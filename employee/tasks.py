from django.template.loader import  get_template
from django.core.mail import EmailMessage
from django.conf import settings
from celery import shared_task


@shared_task(bind=True)
def send_incident_email(self,company_name, company_email, employee_email, employee_first_name,
                        employee_last_name,client_first_name,client_last_name, incident_date, report_code,
                        employee_email_template, admin_email_template,incident_type):
    
    mail_subject=f"New {incident_type} Report Filed: Case ID {report_code}" 

    try:
        employee_ctx = {
            "email": employee_email,
            "employee_first_name": employee_first_name,
            "employee_last_name": employee_last_name,
            "incident_date": incident_date,
            "report_code": report_code,
            "Incident_type":incident_type,
            "client_first_name":client_first_name,
            "client_last_name":client_last_name,
            "mail_subject":mail_subject
        }

        admin_ctx = {
            "email": company_email,
            "incident_date": incident_date,
            "report_code": report_code,
            "employee_first_name": employee_first_name,
            "employee_last_name": employee_last_name,
            "client_first_name":client_first_name,
            "client_last_name":client_last_name,
            "mail_subject":mail_subject,
            "company_name":company_name,
            "Incident_type":incident_type,


        }
        fromEmail = settings.EMAIL_HOST_USER

        employee_html_msg = get_template(employee_email_template).render(employee_ctx)
        print(employee_email)
        employee_msg = EmailMessage(mail_subject, employee_html_msg, fromEmail, [employee_email])
        employee_msg.content_subtype = "html"
        employee_msg.send()

        admin_html_msg = get_template(admin_email_template).render(admin_ctx)
        admin_msg = EmailMessage(mail_subject, admin_html_msg, fromEmail, [company_email])
        admin_msg.content_subtype = "html"
        admin_msg.send()

        return True
    except Exception as ex:
        print(company_name, company_email, employee_email, employee_first_name,
                        employee_last_name,client_first_name,client_last_name, incident_date, report_code,
                        employee_email_template, admin_email_template,incident_type)
        print(ex)
        return False
