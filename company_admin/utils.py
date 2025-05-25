
from django.template.loader import  get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from celery import shared_task
from django.core.mail import send_mail
from .models import InvestigationStage, StageOwnerSubstitute, IncidentStageMapper, InvestigationHierarchy
from userauth.models import Employee
from django.utils import timezone
from bellscrm_admin.models import Company
from .models import Incident 
from datetime import timedelta
from django.template.loader import render_to_string
from django.template.loader import get_template
from userauth.utils import has_user_permission
from company_admin.models import ClientEmployeeAssignment,DepartmentClientAssignment  
import smtplib
import socket 

import logging
logger = logging.getLogger('watchtower')

@shared_task(bind=True)
def account_status_mail(self,user_email,person_first_name,person_last_name,template_name, protocol, domain):
    
    subject="Account Status"
    try:
        employee_context = {
            "first_name": person_first_name,
            "last_name":person_last_name,
            "protocol":protocol,
            "domain":domain,
        }
        fromEmail = settings.EMAIL_HOST_USER
        employee_html_msg = get_template(template_name).render(employee_context)
        employee_msg = EmailMessage(subject, employee_html_msg, fromEmail, [user_email])
        employee_msg.content_subtype = "html"
        employee_msg.send()
        return True
    except Exception as ex:
        return False
    
@shared_task(bind=True)
def incident_update_email(self,employee_email,employee_first_name,employee_last_name,report_code,incident_date,incident_status,email_template):
    subject ="Incident Update"
    try:
        ctx = {
            "email": employee_email,
            "incident_date": incident_date,
            "report_code": report_code,
            "incident_status": incident_status,
            "employee_first_name": employee_first_name,
            "employee_last_name": employee_last_name
        }
        fromEmail = settings.EMAIL_HOST_USER
        employee_html_msg = get_template(email_template).render(ctx)
        employee_html_msg = EmailMessage(subject, employee_html_msg, fromEmail, [employee_email])
        employee_html_msg.content_subtype = "html"
        employee_html_msg.send()

        return True
    except Exception as ex:
        return False
  
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_default_account_credentials_to_user(self, user_email,password,user_first_name,user_last_name,default_account_registration, company_name, protocol, domain):
    subject ="Account Registration"
    try:
        ctx = {
            "email": user_email,
            "employee_first_name": user_first_name,
            "employee_last_name": user_last_name,
            "password":password,
            "company_name":company_name,
            'protocol':protocol,
            'domain':domain,
        }
        fromEmail = settings.EMAIL_HOST_USER
        employee_html_msg = get_template(default_account_registration).render(ctx)
        employee_html_msg = EmailMessage(subject, employee_html_msg, fromEmail, [user_email])
        employee_html_msg.content_subtype = "html"
        employee_html_msg.send()
        return True
    
    
    except (smtplib.SMTPException, socket.gaierror, socket.timeout) as ex:
        logger.warning(f"Temporary failure sending email to {user_email}. Retrying... Exception: {ex}")
        raise self.retry(exc=ex)
    
    except Exception as ex:
        logger.error(f"Failed to send registration email to {user_email}. Exception: {ex}")
        return False
    

def send_investigation_completion_email(company,incident_id,incident_code,recipients,owner_template,admin_email,admin_template):
    subject = "Investigation Completion"
    subject = f"Investigation Completeted for incident {incident_code}"

    try:
        
        subdomain = company.company_code if company.company_code else None
        parent_host = settings.PARENT_HOST if settings.PARENT_HOST else None
        
        domain = f"{subdomain}.{parent_host}" 
        protocol = settings.HOST_SCHEME
        from_email = settings.EMAIL_HOST_USER
        for recipient in recipients:
            try:
                ctx = {
                    "email": recipient["email"],
                    "employee_first_name": recipient["first_name"],
                    "employee_last_name": recipient["last_name"],
                    "incident_code": incident_code,
                    "incident_id": incident_id,
                    "protocol": protocol,
                    "domain": domain,
                }

                html_content = get_template(owner_template).render(ctx)
                email_msg = EmailMessage(subject, html_content, from_email, [recipient["email"]])
                email_msg.content_subtype = "html"
                email_msg.send()

                logger.info(f"[StageEmail] Successfully sent email to {recipient['email']}")

            except Exception as e:
                logger.error(f"[StageEmail] Failed to send email to {recipient.get('email')}: {str(e)}")
                continue

            try:
                admin_ctx = {
                    "employee_first_name": 'Admin',
                    "incident_code": incident_code,
                    "incident_id": incident_id,
                    "protocol": protocol,
                    "domain": domain,
                }

                admin_html = get_template(admin_template).render(admin_ctx)
                admin_msg = EmailMessage(subject, admin_html, from_email, [admin_email])
                admin_msg.content_subtype = "html"
                admin_msg.send()

                logger.info(f"[StageEmail] Successfully sent admin email to {admin_email}")

            except Exception as e:
                logger.error(f"[StageEmail] Failed to send email to admin {admin_email}: {str(e)}")

            return True

    except Exception as ex:
        logger.exception(f"[StageEmail] General failure in sending stage completion emails: {str(ex)}")
        return False
    
    
    
@shared_task
def remove_expired_substitutes():
    '''
    Removal of subsitute when defined timeline is reached
    '''
    try:
        now = timezone.now()
        expired_subs = StageOwnerSubstitute.objects.filter(
            subsitute_overdue_date__isnull=False,
            subsitute_overdue_date__lt=now
        )

        for sub in expired_subs:
            try:
                sub.removed_stage_subsitute = sub.substitute
                sub.substitute = None
                sub.is_subsitute_time_line_overdue = True
                sub.is_substitute_active = False
                sub.save()
            except Exception as e:
                logger.error(f"Failed to update substitute for StageOwnerSubstitute ID {sub.id}: {e}")
                continue

    except Exception as e:
        logger.error(f"Failed to fetch or process expired substitutes: {e}")

@shared_task
def notify_admin_of_upcoming_substitute_expirations():
    '''
    Finds substitutes expiring within 2 days and queues email alerts to admin.
    '''
    try:
        now = timezone.now()
        upcoming_deadline = now + timedelta(days=2)

        expiring_subs = StageOwnerSubstitute.objects.filter(
            subsitute_overdue_date__isnull=False,
            subsitute_overdue_date__lte=upcoming_deadline,
            # subsitute_overdue_date__gt=now,
            is_substitute_email_sent=False
        )

        for sub in expiring_subs:
            if not sub.substitute:
                continue
            alert_admin_about_expiring_substitutes(sub.id)

    except Exception as e:
        logger.error(f"Failed to fetch or queue email tasks: {e}")



def alert_admin_about_expiring_substitutes(sub_id):
    try:
        sub = StageOwnerSubstitute.objects.get(id=sub_id)

        subject = "Substitute Expiry Alert"
        from_email = settings.EMAIL_HOST_USER
        admin_email = sub.stage.hierarchy.company.email_for_alerts
        owner_name = f'{sub.owner.person.first_name} {sub.owner.person.last_name}'
        substitute_name = f'{sub.substitute.person.first_name} {sub.substitute.person.last_name}' if sub.substitute else 'N/A'
        now = timezone.now().date()
        expiry_date = sub.subsitute_overdue_date.date()
        days_remaining = (expiry_date - now).days
        
        admin_ctx = {
            "stage": sub.stage,
            "subsitute_name":substitute_name,
            "owner_name": owner_name,
            "days_remaining":days_remaining
        }

        admin_html = get_template("company_admin/hierarchy/email/stage_subsitute_timeline_alert_email.html").render(admin_ctx)
        admin_msg = EmailMessage(subject, admin_html, from_email, [admin_email])
        admin_msg.content_subtype = "html" 
        admin_msg.send()
        sub.is_substitute_email_sent = True
        sub.save()

    except StageOwnerSubstitute.DoesNotExist:
        logger.error(f"StageOwnerSubstitute with ID {sub_id} does not exist.")
    except Exception as e:
        logger.error(f"Error sending email for substitute ID {sub_id}: {e}")


@shared_task                        
def process_overdue_stages():
    today = timezone.now()
    companies = Company.bells_manager.all()

    for company in companies:
        investigation_hierarchy_instance = InvestigationHierarchy.bells_manager.filter(company=company).first()
        admin_email = company.email_for_alerts
        logger.info(f"[StageEmail] Processing company: {company.name} ({company.id})")

        try:
            incidents = Incident.bells_manager.filter(
                company=company,
                investigation_hierarchy__isnull=False
            )
        except Exception as e:
            logger.error(f"[StageEmail] Error fetching incidents for company {company.id}: {str(e)}")
            continue

        for incident in incidents:
            try:
                hierarchy = investigation_hierarchy_instance

                for stage in hierarchy.stages.all():
                    overdue = stage.overdue_date and stage.overdue_date < today
                    if overdue:
                        mapper = IncidentStageMapper.bells_manager.filter(
                            incident=incident,
                            stage=stage,
                            is_overdue=False
                        ).first()
                        if mapper:
                            if mapper.stage_status == "completed":
                                continue
                            if not mapper.is_overdue:
                                mapper.is_overdue = True
                                mapper.stage.is_overdue = True
                                mapper.stage.save()
                                mapper.save()

                                recipients = get_stage_recipients(stage, incident, company)
                                owner_names = get_owner_names(stage)
                                send_overdue_email(admin_email, recipients, incident.id, stage.s_no, stage.stage_name, owner_names, company)
                                logger.info(f"[StageEmail] Sent email for overdue stage (started) Stage {stage.id} - Incident {incident.id}")
                        else:
                            if stage.is_active == True and not stage.is_overdue :
                                stage.is_overdue = True
                                stage.save()
                                recipients = get_stage_recipients(stage, incident, company)
                                owner_names = get_owner_names(stage)
                                send_overdue_email(admin_email, recipients, incident.id, stage.s_no, stage.stage_name, owner_names ,company)
                                logger.info(f"[StageEmail] Sent email for overdue stage (unstarted) Stage {stage.id} - Incident {incident.id}")
                            else:
                                continue
            except Exception as e:
                logger.error(f"[StageEmail] Error processing stages for incident {incident.id}: {str(e)}")
                continue


def get_stage_recipients(stage, incident, company):
    recipients = []
    recipient_emails = set()

    owners = StageOwnerSubstitute.bells_manager.filter(stage=stage)
    for owner_data in owners:
        for employee in [owner_data.owner, owner_data.substitute]:
            if not employee:
                continue
            person = employee.person
            email = person.email

            if email in recipient_emails:
                continue

            if has_user_permission(person, 'company_admin.update_incident_investigation_all') or \
               has_user_permission(person, 'company_admin.read_incident_investigation_all'):
                recipients.append({
                    "email": email,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                })
                recipient_emails.add(email)
                continue

            if has_user_permission(person, 'company_admin.update_incident_investigation_own_team') and (
                has_user_permission(person, 'company_admin.read_incident_investigation_own_team') or
                has_user_permission(person, 'company_admin.read_incident_investigation_all')
            ):
                department_data = DepartmentClientAssignment.get_manager_department_data(employee.id, company)
                employee_clients = ClientEmployeeAssignment.get_clients_by_employee(employee.id, company)
                department_clients = department_data.get('clients', Employee.objects.none())
                employees = department_data.get('employees', Employee.objects.none())
                clients = department_clients | employee_clients

                if incident.client in clients and incident.employee in employees:
                    recipients.append({
                        "email": email,
                        "first_name": person.first_name,
                        "last_name": person.last_name,
                    })
                    recipient_emails.add(email)

    return recipients


def get_owner_names(stage):
    owners = StageOwnerSubstitute.bells_manager.filter(stage=stage).values_list(
        'owner__person__first_name', 'owner__person__last_name'
    ).distinct()
    return ", ".join([f"{first.title()} {last.title()}" for first, last in owners if first and last])


def send_overdue_email(admin_email, recipients, incident_id, stage_no, stage_name, owner_names, company):
    subject = f"Overdue Investigation Stage - Level {stage_no}"
    subdomain = company.company_code if company.company_code else None
    parent_host = settings.PARENT_HOST if settings.PARENT_HOST else None
    
    domain = f"{subdomain}.{parent_host}" 
    protocol = settings.HOST_SCHEME
    from_email = settings.EMAIL_HOST_USER
    message = ''
    for recipient in recipients:
        try:
            context = {
                "employee_first_name": recipient["first_name"],
                "employee_last_name": recipient["last_name"],
                "incident_id": incident_id,
                "stage_no": stage_no,
                "stage_name": stage_name,
                "protocol": protocol,
                "domain": domain,
            }
            html_content = get_template("company_admin/hierarchy/email/hierarchy_stage_overdue_mail_owner.html").render(context)
            send_mail(
                subject,
                message,
                from_email,
                [recipient["email"]],
                html_message=html_content
            )
            logger.info(f"[StageEmail] Owner email sent to {recipient['email']} for incident {incident_id}, stage {stage_no}")
        except Exception as e:
            logger.error(f"[StageEmail] Failed to send owner email to {recipient['email']}: {str(e)}")

    try:
        admin_context = {
            "owner_names": owner_names,
            "incident_id": incident_id,
            "stage_no": stage_no,
            "stage_name": stage_name,
            "protocol": protocol,
            "domain": domain,
        }
        html_content = get_template("company_admin/hierarchy/email/hierarchy_stage_overdue_mail_admin.html").render(admin_context)
        send_mail(
            subject,
            message,
            from_email,
            [admin_email],
            html_message=html_content
        )
        logger.info(f"[StageEmail] Admin email sent for incident {incident_id}, stage {stage_no}")
    except Exception as e:
        logger.error(f"[StageEmail] Failed to send admin email to {admin_email}: {str(e)}")




@shared_task(name="send_investigation_completion_email")
def investigationCompletionEmail():
    try:
        companies = Company.bells_manager.all()
    except Exception as e:
        logger.error(f"[StageEmail] Failed to fetch companies: {str(e)}")
        return

    email_template = 'company_admin/hierarchy/email/hierarchy_stage_completion_email.html'

    for company in companies:
        try:
            incidents = Incident.bells_manager.filter(company=company, status='Closed')
        except Exception as e:
            logger.error(f"[StageEmail] Failed to fetch incidents for company ID={company.id}: {str(e)}")
            continue

        for incident in incidents:
            if not incident:
                logger.warning(f"[StageEmail] Skipping null incident for company ID={company.id}")
                continue
            if incident.is_investigation_email_sent:
                continue
            try:
                recipient_data = generate_stage_completion_email_context(company, incident.id)
                if not recipient_data:
                    continue 
                incident_code = incident.report_code
                admin_email = company.email_for_alerts
               
                result = send_investigation_completion_email(
                    company=company,
                    incident_id=incident.id,
                    incident_code=incident_code,
                    recipients=recipient_data,
                    owner_template=email_template,
                    admin_email=admin_email,
                    admin_template=email_template
                )

                if result:
                    incident.is_investigation_email_sent=True
                    incident.save()
                    logger.info(f"[StageEmail] Stage completion email sent for incident ID={incident.id}, company ID={company.id}")
                else:
                    logger.error(f"[StageEmail] Email failed for incident ID={incident.id}, company ID={company.id}")

            except Exception as e:
                logger.exception(f"[StageEmail] Unexpected error for incident ID={incident.id}, company ID={company.id}: {str(e)}")



def generate_stage_completion_email_context(company, incident_id):
    recipients = []

    try:
        incident = Incident.bells_manager.select_related('client', 'employee')\
            .filter(id=incident_id, company=company).first()

        if not incident:
            logger.warning(f"[StageEmail] Incident not found: ID={incident_id}, Company ID={company.id}")
            return recipients

        client = incident.client
        incident_employee = incident.employee

        try:
            stage_ids = IncidentStageMapper.bells_manager.filter(incident_id=incident_id)\
                .values_list('stage_id', flat=True)
        except Exception as e:
            logger.error(f"[StageEmail] Error fetching stage IDs for incident ID={incident_id}: {str(e)}")
            return recipients

        try:
            stage_owners = StageOwnerSubstitute.bells_manager.select_related('owner__person')\
                .filter(stage_id__in=stage_ids)
        except Exception as e:
            logger.error(f"[StageEmail] Error fetching stage owners for incident ID={incident_id}: {str(e)}")
            return recipients

        for owner_sub in stage_owners:
            try:
                employee = owner_sub.owner
                person = employee.person

                # Global permission check
                if has_user_permission(person, 'company_admin.update_incident_investigation_all') or \
                   has_user_permission(person, 'company_admin.read_incident_investigation_all'):
                    recipients.append({
                        "email": person.email,
                        "first_name": person.first_name,
                        "last_name": person.last_name,
                    })
                    continue

                # Team-level permission check
                if has_user_permission(person, 'company_admin.update_incident_investigation_own_team') and (
                    has_user_permission(person, 'company_admin.read_incident_investigation_own_team') or
                    has_user_permission(person, 'company_admin.read_incident_investigation_all')
                ):
                    try:
                        dept_data = DepartmentClientAssignment.get_manager_department_data(employee.id, company)
                        employee_clients = ClientEmployeeAssignment.get_clients_by_employee(employee.id, company)
                        department_clients = dept_data.get('clients', Employee.objects.none())
                        employees = dept_data.get('employees', Employee.objects.none())
                        clients = department_clients | employee_clients

                        if client in clients and incident_employee in employees:
                            recipients.append({
                                "email": person.email,
                                "first_name": person.first_name,
                                "last_name": person.last_name,
                            })
                    except Exception as e:
                        logger.warning(f"[StageEmail] Error checking team-level access for employee ID={employee.id}: {str(e)}")
                        continue

            except Exception as e:
                logger.warning(f"[StageEmail] Error processing stage owner: {str(e)}")
                continue

    except Exception as e:
        logger.exception(f"[StageEmail] Unexpected error during context generation for incident ID={incident_id}: {str(e)}")

    return recipients
