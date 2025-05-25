from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from userauth.forms import PersonForm
from userauth.models import Client, Employee
from django.core.mail import send_mail
from userauth.decorators import *
from .forms import *
from django.urls import reverse
from .models import *
from django.contrib import messages
from userauth.forms import ProfileSetting 
from django.db.models import Q
from company_admin.utils import *
from datetime import datetime
from django.http import JsonResponse, HttpResponseRedirect
from employee.models import *
from django.forms import formset_factory
import json
import csv
from django.http import HttpResponse
from django.utils import timezone
import xlsxwriter
from io import BytesIO
from django.conf import settings
import pytz
from employee.forms import IDsAndChecksDocumentsForm, QualificationDocumentsForm, OtherDocumentsForm,ClientAssignmentForm,ClientAssignmentDetailForm,EmployeeClientAssignmentForm,EmployeeShiftsForm
from django.db.models import OuterRef, Subquery, Window, F
from django.db.models.functions import RowNumber
import pandas as pd
from userauth.models import *
from django.db.models import Q
from django.db.models.functions import Lower, Replace
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
import json
from userauth.signals import remove_employee_from_department_when_template_changes,sync_employee_departments,employeement_assignment_to_department,employee_soft_delete_remove_department,update_template_permissions
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Exists, OuterRef, Subquery
from django.db.models import Case, When, Value, IntegerField
from .helpers import paginate_query
from utils.features import get_all_features_data
from django.template.loader import render_to_string
from django.contrib.auth.models import Permission
from utils.helper import get_template_context
from userauth.utils import has_user_permission  
from company_admin.constants import *
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.core.files import File
from utils.permission_sets import *
from utils.helper import *
from employee.tasks import send_incident_email
from django.urls import resolve
from urllib.parse import urlparse
import logging
logger = logging.getLogger('watchtower')

class ForgetPasswordViewView(View):
    template_name = 'userauth/forget_password.html'
    add_employee  = PersonForm()
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    def post(self,request):
        email = request.POST.get("email")
        sendmail = send_mail("Forget_password","Title of forget password","devopsgarg@gmail.com",["himanshu.codigomantra@gmail.com"])



@method_decorator(login_required,name='dispatch')
class DashboardView(View):
    template_name = 'company_admin/index.html'
    def get(self, request, *args, **kwargs):
        from django.db.models import Count, F, Value as V
        try:
            employee = request.user.employee
        except:
            return redirect('user_auth:login')
        company = employee.company
        incidents = Incident.bells_manager.filter(company = company,report_type="Incident")

        
        INCIDENT_PERMISSIONS = [
            "company_admin.create_incident_all",
            "company_admin.create_incident_own_team",
            "company_admin.create_incident_there_own",
            "company_admin.view_incident_all",
            "company_admin.view_incident_own_team",
            "company_admin.view_incident_own",
            "company_admin.update_incident_all",
            "company_admin.update_incident_own_team",
            "company_admin.export_incident_report_all",
            "company_admin.export_incident_report_own_team",
        ]
        
        has_incident_permission = any(has_user_permission(request.user, perm) for perm in INCIDENT_PERMISSIONS)

        if has_incident_permission and has_user_permission(request.user, 'company_admin.read_all_reports'):
            incidents = incidents
        
        elif has_incident_permission and has_user_permission(request.user, 'company_admin.read_team_reports'):
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee.id,company_id=company.id)
            employee_clients_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id = employee.id,company_id=company.id)
            assigned_clients = department_data['clients'] | employee_clients_data
            assigned_employees  = department_data['employees']

            incidents = incidents.filter(client__in=assigned_clients, employee__in=assigned_employees)
        elif has_incident_permission and (has_user_permission(request.user, 'company_admin.read_own_reports') or has_user_permission(request.user, 'company_admin.read_no_access_to_reports') ):
            assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id = employee.id,company_id=company.id)

            incidents = incidents.filter(
                employee=employee,
                client__in=assigned_clients,
            )
        elif not has_incident_permission:
            incidents = incidents.none()
            
        else:
            incidents = incidents.none()
            
 
        counts = incidents.filter(
            company=company,
            report_type="Incident"
        ).aggregate(
            total_count=Count('id'),
            new_count=Count('id', filter=Q(status="New")),
            in_progress_count=Count('id', filter=Q(status="InProgress")),
            completed_count=Count('id', filter=Q(status="Closed")),
        )
        context = {
            'total_count': counts['total_count'],
            'new_count': counts['new_count'],
            'in_progress_count': counts['in_progress_count'],
            'completed_count': counts['completed_count'],
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.create_all_employees',
                                     'userauth.read_all_employees',
                                     'userauth.read_team_employees',
                                     'userauth.update_all_employees',
                                     'userauth.update_team_employees',
                                     'userauth.read_own_employees',
                                     ]), name='dispatch')   
class EmployeeView(View):
    template_name = 'company_admin/employee/employee-list.html'
    
    def get(self, request, *args, **kwargs):
        company = request.user.employee.company
        user = request.user
        acknowledgement_exist = False

        logger.info(f"User: {user.email} | Company: {company.name}")

        # Fetch Read & Update Permissions
        can_read_all = has_user_permission(user, 'userauth.read_all_employees')
        can_read_team = has_user_permission(user, 'userauth.read_team_employees')
        can_read_own = has_user_permission(user, 'userauth.read_own_employees')

        can_update_all = has_user_permission(user, 'userauth.update_all_employees')
        can_update_team = has_user_permission(user, 'userauth.update_team_employees')
        can_update_own = has_user_permission(user, 'userauth.update_own_employees')

        logger.info(f"Permissions - Read All: {can_read_all}, Read Team: {can_read_team}, "
                    f"Update All: {can_update_all}, Update Team: {can_update_team}, Update Own: {can_update_own}")

        manager = user.employee if (can_read_team or can_update_team) else None

        if can_read_all:
            employees = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            logger.info(f"User has read_all permission. Total Employees fetched: {employees.count()}")
        elif can_read_team:
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager.id, company_id=company.id)
            employees = department_data['employees']
            logger.info(f"User has read_team permission. Team Employees fetched: {len(employees)}")
        elif can_read_own:
            employees =  Employee.bells_manager.filter(company=company,id=request.user.employee.id).order_by(Lower('person__first_name'))

        else:
            employees = Employee.bells_manager.none()
            logger.info("User has no read permission. No employees fetched.")

        # Acknowledgement Check
        if employees.filter(policy_acknowledgments__isnull=False).exists():
            acknowledgement_exist = True
            logger.info("Acknowledgement exists for some employees.")

        # show_eye_button_for = set()

        # if  can_update_all:
        #     show_eye_button_for = set(employees)
        #     logger.info("User has both read_all and update_all permissions. Eye button will be shown for all employees.")
        # elif can_update_team:
        #     department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager.id, company_id=company.id)
        #     show_eye_button_for = set(department_data.get('employees', []))
        #     logger.info(f"User has read_all but update_team. Eye button will be shown for team employees only: {len(show_eye_button_for)} employees.")
        # elif can_update_own:
        #     employees = Employee.bells_manager.filter(id=request.user.employee.id)
        #     show_eye_button_for = set(employees)
        #     logger.info("User has read_team and update_own. No eye button will be shown.")
            

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(employees, items_per_page)
        
        try:
            employees_obj = paginator.page(page)
        except PageNotAnInteger:
            employees_obj = paginator.page(1)
        except EmptyPage:
            employees_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        start_entry = ((employees_obj.number - 1) * items_per_page + 1) if total_entries > 0 else 0
        end_entry = min(start_entry + items_per_page - 1, total_entries) if total_entries > 0 else 0

        logger.info(f"Pagination - Showing {start_entry} to {end_entry} of {total_entries} employees.")

        context = {
            'employees': employees_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'acknowledgement_exist': acknowledgement_exist,
            # 'show_eye_button_for': show_eye_button_for
        }
        return render(request, self.template_name, context)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.create_all_employees',
                                     'create_employee_none']), name='dispatch')   
class EmployeeOperationView(View):
    """
    This view handles the operations related to employees 
    """

    template_name_step1 = 'company_admin/employee/employee-operations.html'
    template_name_step2 = 'company_admin/employee/employee-operations-step2.html'

    def get(self, request,template_id=None, employee_id=None, *args, **kwargs):
        
        """
        This Method is used get request
        """
        context = {}
        company = self.get_company(request)
        used_template_name = None  

        if 'employee_add' == request.resolver_match.url_name:
            if not request.GET.get("back"):
                request.session.pop('person_data', None)
                request.session.pop('employee_data', None)
                
            personform = CompanyPersonForm(request=request, initial=request.session.get('person_data', {}))
            employee = request.user.employee
            employee_formset = EmployeeFormset(
                prefix="employee_f", request=request,
                initial=request.session.get('employee_data', [{'company': company, 'created_by': employee}])
            )
            return render(request, self.template_name_step1, {'personform': personform, 'employee_formset': employee_formset})
          
        
        if template_id and 'saved_template_assignment' == request.resolver_match.url_name or 'employee_scratch_template' == request.resolver_match.url_name or 'employee_existing_template' == request.resolver_match.url_name or  'employee_add_step2' == request.resolver_match.url_name  or 'employee_existing_template' == request.resolver_match.url_name:
            context ={}
            existing_permissions = None
            used_template_name = None
            if 'saved_template_assignment' == request.resolver_match.url_name:
                if template_id:
                    try:
                        group = Group.objects.get(id=template_id)
                        existing_permissions = list(group.permissions.values_list('codename', flat=True))
                        if " - user" in group.name:
                            employee = Employee.bells_manager.filter(template__name = group).first()
                            if employee:
                                user_template = f'{employee.person.first_name} {employee.person.last_name}'
                                used_template_name = user_template
                            else:
                                used_template_name = None
                        else:
                            used_template_name = group.name.split('-')[-1].strip()
                    except Group.DoesNotExist:
                        logger.warning(f"Group with id {template_id} not found")
                        return redirect('company:employee_existing_template')
                context['template_id']=template_id
            elif 'employee_scratch_template' == request.resolver_match.url_name:
                existing_permissions = get_employee_permissions()
            feature_data = get_all_features_data()
            context = get_template_context(
                feature_data=feature_data,
                template_id=template_id,
                existing_permissions=existing_permissions,
            )
            if 'employee_scratch_template' == request.resolver_match.url_name:
                context['user_permission']= 'Start from scratch'
            if 'employee_existing_template' == request.resolver_match.url_name or 'saved_template_assignment' == request.resolver_match.url_name:
                # company_templates =  CompanyGroup.bells_manager.filter(company = company)
                company_templates = (
                                CompanyGroup.bells_manager
                                .filter(company=company)
                                .annotate(
                                    middle_name=Replace(
                                        'group__name', 
                                        Value(company.company_code + ' - '),  # Pass company prefix dynamically
                                        Value('')  # Replace with empty string
                                    )
                                )
                                .order_by(Lower('middle_name'))
                            )
               
                simple_templates, user_templates = get_company_templates(company)
                context['simple_templates']=simple_templates
                context['user_templates']=user_templates
                context['used_template_name'] = used_template_name
                context['existing_user_permission']= 'Choose a role based or permission set'
            if 'saved_template_assignment' == request.resolver_match.url_name:
                context['saved_template_name']=used_template_name
            return render(request, self.template_name_step2,context)
            
  

    def get_company(self, request):
        return request.user.employee.company
    
    
    def post(self, request, template_id = None, employee_id=None, *args, **kwargs):
        if 'employee_delete' in request.resolver_match.url_name:
            logger.info(f"Deleting employee with ID: {employee_id}")
            return self.handle_delete(request, employee_id)  
        
        personform = CompanyPersonForm(request.POST,request=request)
        employee_formset = EmployeeFormset(request.POST, request=request,prefix="employee_f", initial=[{'company': self.get_company(request)}])
        
        if personform.is_valid() and employee_formset.is_valid():
            
            # Store person form data in session (excluding models/files)
            person_cleaned_data = {
                field: value 
                for field, value in personform.cleaned_data.items()
                if not isinstance(value, (Model, File)) 
            }
            request.session['person_data'] = person_cleaned_data
            employee_formset_data = [{
                'employment_type': form.cleaned_data.get('employment_type'),
                'company_id': form.cleaned_data.get('company').id,
                'created_by_id': form.cleaned_data.get('created_by').id,
            } for form in employee_formset if form.cleaned_data]
            
            request.session['employee_data'] = employee_formset_data
            logger.info("Redirecting to employee step 2.")
            return redirect('company:employee_add_step2')
  
        elif 'template_employee_assignment' == request.resolver_match.url_name:
            logger.info("Processing employee template assignment.")
            company = request.user.employee.company
            template_id = request.POST.get('template_id')
            feature_permissions = request.POST.get('final_feature_data')
            template_name = request.POST.get('template_name_hidden')

            if not feature_permissions:
                logger.warning("Feature permissions missing. Redirecting to template creation.")
                return redirect('company:employee_add_step2')

            
            # feature_data_dict = json.loads(feature_permissions)
            # permission_codes = [
            #     entry["accessLevelCode"]
            #     for features in feature_data_dict.values()
            #     for entry in features
            #     if entry.get("is_active", True) 
            # ]
            
            try:
                feature_data_dict = json.loads(feature_permissions)
                permission_codes = [
                    entry["accessLevelCode"]
                    for features in feature_data_dict.values()
                    for entry in features
                    if entry.get("is_active", True) 
                ]
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error parsing feature permissions: {e}")
                messages.error(request, "Error processing permission data. Please try again.")
                return redirect('company:employee_add_step2')
            
            if not permission_codes:
                logger.warning("No active permission codes found. Redirecting to template creation.")
                return redirect('company:employee_add_step2')
            
            # Retrieve person data from session
            person_data = request.session.get('person_data')
            if not person_data:
                logger.error("Person data missing from session")
                messages.error(request, "Session data expired. Please start again.")
                return redirect('company:employee_add')
                        
            user_email = person_data['email']
            user_first_name =  person_data['first_name']
            user_last_name =  person_data['last_name']
            is_active =  person_data['is_active']
            existing_person_object = Person.objects.filter(email= user_email).first()
            person_instance = None
            try:
                person_instance = Person(
                    email=user_email,
                    username=user_email,  
                    first_name=user_first_name,
                    last_name=user_last_name,
                    is_active=is_active
                    
                )
                generated_password = self.generate_default_password(user_first_name)
                person_instance.set_password(generated_password)  
                person_instance.save()
                logger.info(f"Created new person: {person_instance.id}")
            except Exception as e:
                    logger.error(f"Error creating person: {str(e)}")
                    return redirect('company:employee_add')

            if not person_instance:
                logger.error("Person instance is None after creation attempt")
                return redirect('company:employee_add')
            
            # generated_password = person_instance.password  

            # template_id = request.POST.get('template_id')
            # if template_id and template_id!='None':
            #     group=Group.objects.get(id=template_id)
            #     company_group_obj = CompanyGroup.bells_manager.get(group=group, company=company)
            #     group_name = group.name.split('-')[-1].strip()

            # else:
            employee_formset_data = request.session.get('employee_data', [])
            if not employee_formset_data:
                logger.error("Employee data missing from session")
                person_instance.delete()
                messages.info(request, 'Something went wrong, Please try again')
                return redirect('company:employee_add')
            
            employee_id = None
            employees = []
            
            for emp_data in employee_formset_data:
                employee = Employee(
                    person=person_instance,
                    employment_type=emp_data.get('employment_type'),
                    company_id=emp_data.get('company_id'),
                    created_by_id=emp_data.get('created_by_id'),
                )
                employee.save()
                employees.append(employee) 
                employee_id = employee.id       
            
            user_template_name = f"{company.company_code.strip().lower()} - {person_instance.first_name}-{person_instance.last_name}-{employee_id} - user"

            # group_name = (
            #     f"{company.company_code} - {template_name}"
            #     if template_name 
            #     else f"{user_template_name}"
            # )
            group_name = f"{company.company_code} - {user_template_name}"
            
            if not group_name:
                person_instance.delete()
                for employee in employees:
                    employee.delete()
                    logger.info(f"Group name not found for {employee.id}.")
                messages.info(request, 'Something went wrong, Please try again')
                return redirect('company:employee_add')
            # Create new group and assign permissions
            try:
                group = Group.objects.create(name=group_name)
            except Exception as e:
                logger.error(f"Error creating group: {str(e)}")
                person_instance.delete()
                for employee in employees:
                    employee.delete()
                    logger.info(f"Deleted employee {employee.id} due to group/permission setup failure")
                messages.info(request, 'Something went wrong, Please try again')
                return redirect('company:employee_add')
            try:
                company_group_obj = CompanyGroup.bells_manager.create(group=group, company=company)
            except:
                logger.error(f"Error creating company group: {str(e)}")
                person_instance.delete()
                for employee in employees:
                    employee.delete()
                    logger.info(f"Deleted employee {employee.id} due to group/permission setup failure")
                messages.info(request, 'Something went wrong, Please try again')
                return redirect('company:employee_add')

                
            if company_group_obj:
                try:
                    permissions = Permission.objects.filter(codename__in=permission_codes)
                    group.permissions.add(*permissions)
                    # Log any missing permissions
                    existing_permission_codes = permissions.values_list('codename', flat=True)
                    missing_permissions = set(permission_codes) - set(existing_permission_codes)
                    if missing_permissions:
                        for permission_code in missing_permissions:
                            logger.warning(f"Permission with code {permission_code} does not exist.")
                            print(f"Permission with code {permission_code} does not exist.")
                except Exception as e:
                    logger.error(f"Error assigning permissions: {str(e)}")
                    person_instance.delete()
                    for employee in employees:
                        employee.delete()
                        logger.info(f"Deleted employee {employee.id} due to group/permission setup failure")
                    messages.info(request, 'Something went wrong, Please try again')
                    return redirect('company:employee_add')

                    
            for employee in employees:
                employee.template = group
                employee.save(update_fields=["template"])
        
            
            request.session.pop('employee_data', None)
            request.session.pop('person_data', None)
        
            
            active_template_name = 'company_admin/employee/email/active-account.html'
            inactive_template_name = 'company_admin/employee/email/in-active-account.html'

            #new registration mail
            password =  generated_password
            default_account_registration_email = 'company_admin/employee/email/new-account-registration.html'
            protocol = 'http' if not request.is_secure() else 'https'
            domain = request.get_host()
            if employee_id and 'employee_edit' in request.resolver_match.url_name:
                if existing_person_object is not None:
                    if person_instance.is_active != existing_person_object.is_active:
                        if person_instance.is_active == True:
                            account_status_mail.apply_async(args = [user_email,user_first_name,user_last_name,active_template_name, protocol, domain ])
                        else:
                            account_status_mail.apply_async(args = [user_email,user_first_name,user_last_name,inactive_template_name, protocol, domain])
                messages.success(request, 'Employee updated successfully!')
            else:
                send_default_account_credentials_to_user.apply_async(args = [user_email,password,user_first_name,user_last_name,default_account_registration_email, self.get_company(request).name, protocol, domain])
            messages.success(request, 'Employee added successfully!')
            return redirect('company:employee_list')

        else:
            print("Form is not valid")
            return render(request, self.template_name_step1, {'personform': personform, 'employee_formset': employee_formset})
    
    def generate_default_password(self,first_name):
        """Generate a default password using the first name."""
        first_name = first_name 
        return f"{first_name}@1234"


    def handle_delete(self, request, employee_id):
        employee = get_object_or_404(Employee, pk=employee_id)
        if employee:
            employee.is_deleted = True
            employee.updated_by = request.user.first_name + ' ' + request.user.last_name
            employee.updated_at = timezone.now()
            employee.person.is_active = False
            employee.person.save()
            employee.save()
            employee_soft_delete_remove_department(employee)
            messages.success(request, 'Employee deleted successfully!')

        return HttpResponseRedirect(reverse('company:employee_list'))

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.read_all_clients',
                                     'userauth.read_team_clients',
                                     'userauth.update_all_clients',
                                     'userauth.update_clients_team_owns',
                                     'userauth.create_all_clients','userauth.create_client_none']), name='dispatch') 
class ClientView(View):
    template_name = 'company_admin/clients/all_clients.html'

    def can_update_client(self, client, update_all_clients, update_team_clients, department_clients):
        """
        Determine if a client can be updated based on user permissions.
        """
        if update_all_clients:
            return True
        return update_team_clients and client in department_clients  

    @method_decorator(login_required, name='dispatch')
    def get(self, request, *args, **kwargs):
        user_employee = request.user.employee
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')
        update_all_clients = has_user_permission(request.user, 'userauth.update_all_clients')
        update_team_clients = has_user_permission(request.user, 'userauth.update_clients_team_owns')

        department_clients = set()
        if read_team_clients or update_team_clients:
            department_data = DepartmentClientAssignment.get_manager_department_data(
                manager_id=user_employee.id, company_id=user_employee.company.id
            )
            department_clients = set(department_data['clients']) 

        if read_all_clients:
            clients_queryset = Client.bells_manager.filter(company=user_employee.company).order_by('person__first_name')
        elif read_team_clients:
            clients_queryset = list(department_clients)  
        else:
            clients_queryset = [] 
        
        employee_clients = ClientEmployeeAssignment.get_clients_by_employee(user_employee.id, user_employee.company.id)
        clients_queryset = list(set(clients_queryset) | set(employee_clients))
        clients_queryset = sorted(clients_queryset, key=lambda c: c.person.first_name.lower())

        clients_list = [{'client': client, 'can_update': self.can_update_client(
            client, update_all_clients, update_team_clients, department_clients
        )} for client in clients_queryset]

        # Pagination
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(clients_list, items_per_page)
        try:
            clients_obj = paginator.page(page)
        except PageNotAnInteger:
            clients_obj = paginator.page(1)
        except EmptyPage:
            clients_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        start_entry = ((clients_obj.number - 1) * items_per_page) + 1 if total_entries else 0
        end_entry = min(start_entry + items_per_page - 1, total_entries) if total_entries else 0

        context = {
            'clients': clients_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['userauth.create_client_none','userauth.client_update_none','userauth.read_all_clients', 'userauth.read_team_clients','userauth.update_all_clients', 'userauth.update_clients_team_owns']), name='dispatch')   
class ClientProfileView(View):
    template_name = 'company_admin/clients/client_profile.html'
    def get(self, request, client_id=None, *args, **kwargs):
        
        show_update_button_for = set()
        company = request.user.employee.company
        client_obj = Client.bells_manager.get(pk=client_id)
        update_all_clients = has_user_permission(request.user, 'userauth.update_all_clients')
        update_team_clients = has_user_permission(request.user, 'userauth.update_clients_team_owns')
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')
        
        
        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=request.user.employee.id, company_id=company.id
        )
        
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))
        
        if update_all_clients:
            show_update_button_for = {client_obj.id}
        if update_team_clients:
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            client_ids = department_data['clients'].values_list('id',flat=True)
            show_update_button_for = set(client_ids)
            
        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False
            
        context = {
            'client_id': client_id,
            'client':client_obj,
            'show_update_button_for':show_update_button_for,
            'show_service_delivery_team': show_service_delivery_team
        }
        return render(request, self.template_name, context)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions([
    'company_admin.create_all_risk_assessments',
    'company_admin.create_risk_assessments_team_own',
    'company_admin.update_all_risk_assessments',
    'company_admin.update_team_risk_assessments',
    'company_admin.read_all_risk_assessments',
    'company_admin.read_risk_assessments_team_own',
    'company_admin.create_risk_assessments_of_their_own',
]), name='dispatch')
class ClientProfileRiskassessmentView(View):
    template_name = 'company_admin/clients/client_profile.html'

    def get(self, request, client_id=None, *args, **kwargs):
        client_obj = Client.bells_manager.get(pk=client_id)
        company = request.user.employee.company
        employee_id = request.user.employee.id

        # Fetch user permissions
        read_all_risk_assessment = has_user_permission(request.user, 'company_admin.read_all_risk_assessments')
        read_team_risk_assessment = has_user_permission(request.user, 'company_admin.read_risk_assessments_team_own')
        read_own_risk_assessment = has_user_permission(request.user, 'company_admin.read_risk_assessments_of_their_own')
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')

        # Get department data once
        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=employee_id, company_id=company.id
        )
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))

        # Determine visibility of service delivery team
        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False

        # Risk assessment retrieval logic
        if read_all_risk_assessment or read_own_risk_assessment:
            risk_assessment = RiskAssessment.bells_manager.filter(client=client_id).order_by("-created_at")

        elif read_team_risk_assessment:
            own_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id, company.id)
            own_client_ids = set(client.id for client in own_clients)

            # Combine team and own client IDs
            combined_client_ids = team_client_ids.union(own_client_ids)
            # if client_id in team_client_ids:
            if client_id in combined_client_ids:
                risk_assessment = RiskAssessment.bells_manager.filter(client=client_id).order_by("-created_at")
            else:
                risk_assessment = RiskAssessment.bells_manager.none()

        else:
            risk_assessment = RiskAssessment.bells_manager.none()

        # Pagination
        items_per_page = 50
        paginator = Paginator(risk_assessment, items_per_page)
        page = request.GET.get('page', 1)
        try:
            risk_assessment_obj = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            risk_assessment_obj = paginator.page(1)

        total_entries = paginator.count
        start_entry = ((risk_assessment_obj.number - 1) * items_per_page) + 1 if total_entries else 0
        end_entry = min(start_entry + items_per_page - 1, total_entries) if total_entries else 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'risk_assessment': risk_assessment_obj,
            'client': client_obj,
            'show_service_delivery_team': show_service_delivery_team
        }

        # Cleanup session variables
        request.session.pop('edit_document_request', None)
        request.session.pop('is_employee_request', None)

        return render(request, self.template_name, context)

    

@method_decorator(login_required,name='dispatch')
# @method_decorator(check_permissions(['company_admin.view_incident_all',
#                                      'company_admin.view_incident_own_team',]), name='dispatch') 
class ClientProfileIncidentView(View):
    template_name = 'company_admin/clients/client_profile.html'
    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        incidents = Incident.bells_manager.filter(company = company,client=client_id,report_type='Incident')
        incidents = Incident.order_by_status(incidents)
        client_obj = Client.bells_manager.get(pk=client_id)
        
        
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')
        
        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=request.user.employee.id, company_id=company.id
        )
        
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))
        
        
        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(incidents, items_per_page)
        try:
            incidents_obj = paginator.page(page)
        except PageNotAnInteger:
            incidents_obj = paginator.page(1)
        except EmptyPage:
            incidents_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((incidents_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'incidents':incidents_obj,
            'client':client_obj,
            'show_service_delivery_team':show_service_delivery_team

        }
        return render(request, self.template_name, context)
    
    
    
@method_decorator(login_required,name='dispatch')
@method_decorator(admin_role_required,name='dispatch')
@method_decorator(user_can_access_client, name='dispatch')
class ClientProfileMandatoryIncidentView(View):
    template_name = 'company_admin/clients/client_profile.html'
    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        mandatory_incidents = Incident.bells_manager.filter(company = company,client=client_id,report_type='Mandatory Incident')
        client_obj = Client.bells_manager.get(pk=client_id)

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(mandatory_incidents, items_per_page)
        try:
            mandatory_incidents_obj = paginator.page(page)
        except PageNotAnInteger:
            mandatory_incidents_obj = paginator.page(1)
        except EmptyPage:
            mandatory_incidents_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((mandatory_incidents_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'mandatory_incidents':mandatory_incidents_obj,
            'client':client_obj

        }
        return render(request, self.template_name, context)
    

@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['company_admin.view_progress_notes_all',
                                     'company_admin.view_progress_notes_own_team',
                                     'company_admin.view_progress_notes_own']), name='dispatch') 
class ClientProfileShiftNoteView(View):
    template_name = 'company_admin/clients/client_profile.html'
    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        shifts_note = DailyShiftCaseNote.bells_manager.filter(
             company=company,client=client_id,shift__status="Completed").order_by('-created_at')
        client_obj = Client.bells_manager.filter(id=client_id).first()
        
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')
        
        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=request.user.employee.id, company_id=company.id
        )
        
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))
        
        
        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(shifts_note, items_per_page)
        try:
            shifts_obj = paginator.page(page)
        except PageNotAnInteger:
            shifts_obj = paginator.page(1)
        except EmptyPage:
            shifts_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((shifts_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0
        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'shifts':shifts_obj,
            'client':client_obj,
            'show_service_delivery_team':show_service_delivery_team

        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions([
    'userauth.read_team_clients',
    'userauth.update_clients_team_owns',
    'userauth.read_all_clients',
    'userauth.update_all_clients'
]), name='dispatch')
class ClientServiceDeliveryTeamView(View):
    template_name = 'company_admin/clients/client_profile.html'

    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company = employee.company
        client_obj = get_object_or_404(Client, pk=client_id)

        update_all_clients = has_user_permission(request.user, 'userauth.update_all_clients')
        update_team_clients = has_user_permission(request.user, 'userauth.update_clients_team_owns')
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')

        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=employee.id, company_id=company.id
        )
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))
        employees = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
        
        show_service_delivery_team = False
        associated_employees = Employee.objects.none()  
        if read_all_clients:
            show_service_delivery_team = True 
            employees = employees
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True 
            employees = department_data['employees'] 
        else :
            employees = employees.filter(id=employee.id,company=company)
            
        if show_service_delivery_team == True: 
            associated_employees = ClientEmployeeAssignment.get_employees_by_client(client_id=client_id, company_id=company.id)

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(associated_employees, items_per_page)

        try:
            associated_employees_obj = paginator.page(page)
        except PageNotAnInteger:
            associated_employees_obj = paginator.page(1)
        except EmptyPage:
            associated_employees_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        start_entry = ((associated_employees_obj.number - 1) * items_per_page) + 1 if total_entries > 0 else 0
        end_entry = min(start_entry + items_per_page - 1, total_entries)

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'client': client_obj,
            'associated_employees': associated_employees_obj,
            'associated_employee_ids': list(associated_employees.values_list('id', flat=True)),
            'employees': employees.order_by(Lower('person__first_name')),
            'show_service_delivery_team': show_service_delivery_team
        }
        return render(request, self.template_name, context)

    
    
    
@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['company_admin.view_incident_all',
                                     'company_admin.view_incident_own_team',
                                     'company_admin.view_incident_own',
                                     'company_admin.view_progress_notes_all',
                                     'company_admin.view_progress_notes_own_team',
                                     'company_admin.view_progress_notes_own']), name='dispatch') 
class ClientIncidentOperationView(View):
    template_name = 'company_admin/clients/client_profile.html'

    def get(self, request, incident_id=None, shift_id=None, mandatory_incident_id=None, client_id=None, *args, **kwargs):
        context = {}
        try:
            employee = request.user.employee
            company = employee.company
            client_obj = Client.bells_manager.get(pk=client_id)
        except Client.DoesNotExist:
            context['error'] = "Client not found"
            return render(request, self.template_name, context)

        specific_severity_description = None
        
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')

        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=request.user.employee.id, company_id=company.id
        )

        team_client_ids = set(department_data['clients'].values_list('id', flat=True))

        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False

        # Add it to context
        context["show_service_delivery_team"] = show_service_delivery_team

        # Handling the incident view
        if incident_id and 'client_profile_incident_detail' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id)
                incident_form = IncidentForm(instance=incident, company=company,request=request)

                # Get the description for the specific severity level
                severity_choices = SEVERITY_LEVEL_CHOICES.get(incident.incident_severity_level, [])
                for value, description in severity_choices:
                    if value == incident.specific_severity_level:
                        specific_severity_description = description
                        break

                attachments_files = IncidentAttachment.bells_manager.filter(incident=incident)
                initial_data = [attachment for attachment in attachments_files]

                context.update({
                    'attachment_data': initial_data,
                    'incident_form': incident_form,
                    'client_id': client_id,
                    'single_incident_view': True,
                    'client': client_obj,
                    'incident_id': incident_id,
                    'specific_severity_description': specific_severity_description,
                })
            except Incident.DoesNotExist:
                context['error'] = "Incident not found"

        # Handling the mandatory incident view
        if mandatory_incident_id and 'client_profile_mandatory_incident_detail' in request.resolver_match.url_name:
            try:
                mandatory_incident = Incident.bells_manager.get(pk=mandatory_incident_id)
                mandatory_incident_form = MandatoryIncidentForm(instance=mandatory_incident, company=company,request=request)

                # Get the description for the specific severity level
                severity_choices = SEVERITY_LEVEL_CHOICES.get(mandatory_incident.incident_severity_level, [])
                for value, description in severity_choices:
                    if value == mandatory_incident.specific_severity_level:
                        specific_severity_description = description
                        break

                attachments_files = IncidentAttachment.bells_manager.filter(incident=mandatory_incident)
                initial_data = [attachment for attachment in attachments_files]

                context.update({
                    'attachment_data': initial_data,
                    'incident_form': mandatory_incident_form,
                    'client_id': client_id,
                    'single_mandatory_incident_view': True,
                    'client': client_obj,
                    'incident_id': mandatory_incident_id,
                    'specific_severity_description': specific_severity_description,
                })
            except Incident.DoesNotExist:
                context['error'] = "Mandatory incident not found"

        # Handling the daily shift note view
        if shift_id and 'client_profile_shift_note__detail' in request.resolver_match.url_name:
            try:
                shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id)
                shift_form = DailyShiftNoteForm(instance=shift, company=company, request=request)
                employee_shift_instance = Shifts.bells_manager.filter(id=shift.shift.id,company=company).first()
                employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance,request=request)
                context.update({
                    'shift_form': shift_form,
                    'client_id': client_id,
                    'single_shift_note_view': True,
                    'client': client_obj,
                    'shift_id': shift_id,
                    'employee_shift_form' :employee_shift_form,
                })
            except DailyShiftCaseNote.DoesNotExist:
                context['error'] = "Shift note not found"

        return render(request, self.template_name, context)

        
        
        
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.create_all_clients',
                                     'userauth.update_all_clients',
                                     'userauth.update_clients_team_owns']), name='dispatch')
class ClientOperationView(View):
    """
    This view handles the operations related to client 
    """

    template_name = 'company_admin/clients/client-operations.html'
    def get(self, request, client_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        
        personform = ClientPersonForm()
        company = self.get_company(request)
        if client_id and 'client_edit' in request.resolver_match.url_name:
            try:
                client = Client.bells_manager.get(pk=client_id)
                ClientFormset = get_formset(Person,Client,ClientForm,extra=0)
                ClientEmergencyDetailFormset = get_formset(Client, ClientEmergencyDetail, ClientEmergencyDetailForm, extra=1 if client.emergency_contact_details.first() is None else 0)
                ClientNDISDetailFormset = get_formset(Client, ClientNDISDetail, ClientNDISDetailForm, extra=1 if client.ndis_details.first() is None else 0)
                ClientMedicalDetailFormset = get_formset(Client, ClientMedicalDetail, ClientMedicalDetailForm, extra=1 if client.medical_details.first() is None else 0)
                personform = ClientPersonForm(instance=client.person)
                client_formset = ClientFormset(instance=client.person, prefix="client")
                emergency_formset = ClientEmergencyDetailFormset(instance=client,prefix='emergency')
                ndis_formset = ClientNDISDetailFormset(instance=client,prefix='ndis')
                medical_formset = ClientMedicalDetailFormset(instance=client,prefix='medical')
  
            except:
                return HttpResponseRedirect(reverse('company:client_list'))
        else:
            ClientFormset = get_formset(Person,Client,ClientForm,extra=1)
            ClientEmergencyDetailFormset = get_formset(Client,ClientEmergencyDetail,ClientEmergencyDetailForm,extra=1)
            ClientNDISDetailFormset = get_formset(Client, ClientNDISDetail,ClientNDISDetailForm,extra=1)
            ClientMedicalDetailFormset = get_formset(Client, ClientMedicalDetail,ClientMedicalDetailForm,extra=1)
            client_formset = ClientFormset(prefix="client", initial=[{'company': company}])
            emergency_formset = ClientEmergencyDetailFormset(prefix='emergency')
            ndis_formset = ClientNDISDetailFormset(prefix='ndis')
            medical_formset = ClientMedicalDetailFormset(prefix='medical')
        
        context = {
            'personform': personform,
            'client_formset': client_formset,
            'emergency_formset':emergency_formset,
            'ndis_formset':ndis_formset,
            'medical_formset':medical_formset,
            'client_id':client_id
        }

        return render(request, self.template_name, context)

    
    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, client_id=None, *args, **kwargs):
        if 'client_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, client_id)
        
        if client_id and 'client_edit' in request.resolver_match.url_name:
            try:
                ClientFormset = get_formset(Person,Client,ClientForm,extra=0)
                ClientEmergencyDetailFormset = get_formset(Client,ClientEmergencyDetail,ClientEmergencyDetailForm,extra=0)
                ClientNDISDetailFormset = get_formset(Client, ClientNDISDetail,ClientNDISDetailForm,extra=0)
                ClientMedicalDetailFormset = get_formset(Client, ClientMedicalDetail,ClientMedicalDetailForm,extra=0)
                client = Client.bells_manager.get(pk=client_id)
                personform = ClientPersonForm(request.POST,request.FILES, instance=client.person)
                client_formset = ClientFormset(request.POST, instance=client.person, prefix="client")
                emergency_formset = ClientEmergencyDetailFormset(request.POST, instance=client,prefix='emergency')
                ndis_formset = ClientNDISDetailFormset(request.POST, instance=client,prefix='ndis')
                medical_formset = ClientMedicalDetailFormset(request.POST, instance=client,prefix='medical')
            except:
                return HttpResponseRedirect(reverse('company:client_list'))
        else:
            ClientFormset = get_formset(Person,Client,ClientForm,extra=0)
            ClientEmergencyDetailFormset = get_formset(Client,ClientEmergencyDetail,ClientEmergencyDetailForm,extra=0)
            ClientNDISDetailFormset = get_formset(Client, ClientNDISDetail,ClientNDISDetailForm,extra=0)
            ClientMedicalDetailFormset = get_formset(Client, ClientMedicalDetail,ClientMedicalDetailForm,extra=0)
            personform = ClientPersonForm(request.POST,request.FILES)
            print("Profile Image in request.FILES:", request.FILES.get('profile_image'))
            client_formset = ClientFormset(request.POST, prefix="client", initial=[{'company': self.get_company(request)}])
            emergency_formset = ClientEmergencyDetailFormset(request.POST, prefix='emergency')
            ndis_formset = ClientNDISDetailFormset(request.POST, prefix='ndis')
            medical_formset = ClientMedicalDetailFormset(request.POST, prefix='medical')
        if personform.is_valid() and client_formset.is_valid() and emergency_formset.is_valid() and ndis_formset.is_valid() and medical_formset.is_valid():
            try:
                user_email = personform.cleaned_data.get('email')
                person_instance = personform.save(commit=False)

                if not user_email:
                    timestamp_int = int(datetime.now().timestamp())
                    unique_id = timestamp_int
                    default_email = f"{''.join(filter(str.isalpha, person_instance.first_name.lower()))}_{request.user.employee.company.company_code.lower()}_{unique_id}@bellscrm.com.au" 
                    user_email = default_email
                person_instance.username = user_email
                person_instance.email = user_email
                person_instance.save()
                client_formset.instance = person_instance
                client_formset.save()
                          
                client_obj = client_formset[0].instance
                for form in ndis_formset:
                    if form.cleaned_data.get('service_fund_type') != 'NDIS':
                        form.cleaned_data['ndis_services'] = None
                emergency_formset.instance = client_obj
                emergency_formset.save()
                ndis_formset.instance = client_obj
                ndis_formset.save()
                medical_formset.instance = client_obj
                medical_formset.save()
                
                #assigning client to employee
                
                if has_user_permission(request.user,'userauth.create_all_clients'):
                    form_data = {
                        'clients':[client_obj],
                        'employee':request.user.employee
                    }
                    existing_assignment = ClientAssignment.bells_manager.filter(employee=request.user.employee).first()
                    if existing_assignment:
                        # existing_assignment.clients.add(client_obj)
                        assignment_detail_form = ClientAssignmentDetailForm({
                            'client': client_id or client_obj.id,
                            'is_deleted': False,
                        })
                        if assignment_detail_form.is_valid():
                            assignment_detail = assignment_detail_form.save(commit=False)
                            assignment_detail.client_assignment = existing_assignment
                            assignment_detail.save()
                    
                    else:
                        assignment_form = EmployeeClientAssignmentForm(form_data)
                        if assignment_form.is_valid():
                            assignment = assignment_form.save(commit=False)
                            assignment.save()
                            
                            assignment_detail_form = ClientAssignmentDetailForm({
                                'client': client_id or client_obj.id,
                                'is_deleted': False,
                            })
                            if assignment_detail_form.is_valid():
                                assignment_detail = assignment_detail_form.save(commit=False)
                                assignment_detail.client_assignment = assignment
                                assignment_detail.save()
                    
                if client_id:
                    messages.success(request, 'Client updated successfully!')
                else:
                    messages.success(request, 'Client added successfully!')

                return HttpResponseRedirect(reverse('company:client_list'))
            except Exception as e:
                print(request, f"An error occurred: {e}")
                context = {
                    'personform': personform,
                    'client_formset': client_formset,
                    'emergency_formset':emergency_formset,
                    'ndis_formset':ndis_formset,
                    'medical_formset':medical_formset,
                }
                return render(request, self.template_name, context)
        else:
            print("Form is not valid")
            # If forms are not valid
            context = {
                'client_id':client_id,
                'personform': personform,
                'client_formset': client_formset,
                'emergency_formset':emergency_formset,
                'ndis_formset':ndis_formset,
                'medical_formset':medical_formset,
                'personform_errors': personform.errors,
                'emergency_formset_errors': emergency_formset.errors,

            }
            return render(request, self.template_name, context)
    
    def handle_delete(self, request, client_id):
        client = get_object_or_404(Client, pk=client_id)
        if client:
            client.is_deleted = True
            client.person.is_active = False
            client.person.save()
            client.save()
            messages.success(request, 'Client deleted successfully!')
        return HttpResponseRedirect(reverse('company:client_list'))

    
# @method_decorator(login_required, name='get')
# class CompanyUserProfileView(View):
#     template_name = "company_admin/profile/setting.html"

#     def get(self, request, *args, **kwargs):
#         user = get_object_or_404(Person, pk=request.user.pk)
#         profileform = ProfileSetting(instance=user)
#         return render(request, self.template_name, {'profilesettingform': profileform})


@method_decorator(login_required,name='dispatch')
@method_decorator(admin_role_required,name='dispatch')
@method_decorator(user_can_access_mandatory_incident_report,name='dispatch')
class MandatoryIncidentReportDashboard(View):
    template_name = "company_admin/dashboard/mandatory-incident-report.html"
    
    def get(self,request,*args, **kwargs):
        employee = request.user.employee
        company = employee.company
        if employee.role == 2:
            manager_departments = employee.departments.filter(is_deleted=False)
            employee_data = Employee.bells_manager.filter(departments__in=manager_departments, company=company, is_deleted=False).distinct()
            client_assignments = ClientAssignment.bells_manager.filter(employee__in=employee_data,employee__company=company,
                is_deleted=False)
            client_data = Client.bells_manager.filter(company=company,
                        client_assignments_detail__client_assignment__in=client_assignments,
                        client_assignments_detail__is_deleted=False
                    ).distinct().order_by('-created_at') 
                    
        else:
            client_data = Client.bells_manager.filter(company = company)
            employee_data = Employee.bells_manager.filter(company = company)

        client_form = FilterQuerySetForm(request.GET or None)

        incidents = Incident.bells_manager.filter(company = company,report_type = "Mandatory Incident",client__in=client_data).order_by('-created_at')
 
        client_form.fields['employee'].queryset = employee_data
        client_form.fields['client'].queryset = client_data
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        incidents = filter_queryset(queryset=incidents,request=request)

        total_count = len(incidents)
        new_count = len(incidents.filter(status='New'))
        in_progress_count = len(incidents.filter(status='InProgress'))
        completed_count = len(incidents.filter(status='Closed'))
        context = {
            'incidents':incidents,
            'total_count': total_count,
            'new_count': new_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'employee_data':employee_data,
            'client_data':client_data,
            'client_form':client_form,
            'start_date': start_date,
            'end_date': end_date,
        }
        return render(request,self.template_name, context)

# @method_decorator(login_required,name='dispatch')
# class ClientIncidentReportDashboard(View):
#     template_name = "company_admin/dashboard/client-incident-report-dashboard.html"
    
#     def get(self,request,*args, **kwargs):
#         employee = request.user.employee
#         company = employee.company
#         if has_user_permission(request.user,'company_admin.view_incident_own_team'):
#             manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee.id,company_id=company.id)
#             employee_data = manager_data['employees']
#             client_data = manager_data['clients']
                    
#         if has_user_permission(request.user,'company_admin.view_incident_all'):
#             client_data = Client.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
#             employee_data = Employee.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
        
#         else:
#             assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id = employee.id,company_id=company.id)

#             incidents = incidents.filter(
#                 employee=employee,
#                 client__in=assigned_clients,
#                 client__is_deleted=False
#             )
        
#         # client_data = Client.bells_manager.filter(company = company)
#         incident_form = FilterQuerySetForm(request.GET or None)

#         total_incidents = Incident.bells_manager.filter(company = company,report_type="Incident",client__in=client_data, employee__in=employee_data).order_by('-created_at')
#         # employee_data = Employee.bells_manager.filter(company = company)
        
#         start_date = request.GET.get('start_date')
#         end_date = request.GET.get('end_date')
#         incident_form.fields['employee'].queryset = employee_data
#         incident_form.fields['client'].queryset = client_data
#         incidents = filter_queryset(queryset=total_incidents,request=request)
#         incidents = Incident.order_by_status(incidents)
#         total_count = len(total_incidents)
#         new_count = len(total_incidents.filter(status='New'))
#         in_progress_count = len(total_incidents.filter(status='InProgress'))
#         completed_count = len(total_incidents.filter(status='Closed'))

#         items_per_page = 50
#         page = request.GET.get('page', 1)
#         paginator = Paginator(incidents, items_per_page)
#         try:
#             incidents_obj = paginator.page(page)
#         except PageNotAnInteger:
#             incidents_obj = paginator.page(1)
#         except EmptyPage:
#             incidents_obj = paginator.page(paginator.num_pages)

#         total_entries = paginator.count
#         if total_entries > 0:
#             start_entry = ((incidents_obj.number - 1) * items_per_page) + 1
#             end_entry = min(start_entry + items_per_page - 1, total_entries)
#         else:
#             start_entry = 0
#             end_entry = 0
        
#         context = {
#             'incidents': incidents_obj,
#             'start_entry': start_entry,
#             'end_entry': end_entry,
#             'total_entries': total_entries,
#             # 'incidents':incidents,
#             'total_count': total_count,
#             'new_count': new_count,
#             'in_progress_count': in_progress_count,
#             'completed_count': completed_count,
#             'employee_data':employee_data,
#             'client_data':client_data,
#             'incident_form':incident_form,
#             'start_date': start_date,
#             'end_date': end_date,
#             # ... other context variables ...
#         }
#         return render(request,self.template_name, context)
    


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.create_incident_all',
                                     'company_admin.update_incident_all',
                                     'company_admin.create_incident_own_team',
                                     'company_admin.create_incident_there_own',
                                     'company_admin.update_incident_own_team',
                                     'company_admin.update_progress_notes_own',
                                     'company_admin.view_incident_all',
                                     'company_admin.view_incident_own_team',
                                     'company_admin.view_incident_own']), name='dispatch')
class ClientIncidentReportDashboard(View):
    template_name = "company_admin/dashboard/client-incident-report-dashboard.html"

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company = employee.company

        client_data = Client.bells_manager.none()
        employee_data = Employee.bells_manager.none()

        read_all_incident = has_user_permission(request.user, 'company_admin.view_incident_all')
        read_team_incident = has_user_permission(request.user, 'company_admin.view_incident_own_team')
        read_own_incident = has_user_permission(request.user, 'company_admin.view_incident_own')
        update_all_incident = has_user_permission(request.user, 'company_admin.update_incident_all')
        update_own_team_incident = has_user_permission(request.user, 'company_admin.update_incident_own_team')

        if read_all_incident:
            total_incidents = Incident.bells_manager.filter(company=company)
        elif read_team_incident :
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
            employee_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id) 
            employee_data = manager_data.get('employees', Employee.bells_manager.none())
            client_data = manager_data.get('clients', Client.bells_manager.none()) | employee_clients

        elif read_own_incident:
            assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id, company_id=company.id)
            client_data = assigned_clients
            employee_data = Employee.bells_manager.filter(id=employee.id)  

        else:
            client_data = Client.bells_manager.none()
            employee_data = Employee.bells_manager.none()
        
        show_update_button_for = set()
        if update_all_incident:
            filter_client_data = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            filter_employee_data = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            filter_total_incidents = Incident.bells_manager.filter(
                company=company,
                report_type="Incident",
                client__in=filter_client_data,
            ).order_by('-created_at').values_list('id', flat=True)

            show_update_button_for.update(filter_total_incidents) 

        elif update_own_team_incident:
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
            filter_employee_data = manager_data.get('employees', Employee.bells_manager.none())
            filter_client_data = manager_data.get('clients', Client.bells_manager.none())
            
            filter_total_incidents = Incident.bells_manager.filter(
                company=company,
                report_type="Incident",
                client__in=filter_client_data
            ).order_by('-created_at').values_list('id', flat=True)

            show_update_button_for.update(filter_total_incidents) 
                    
            
        # Initialize the incident form
        incident_form = FilterQuerySetForm(request.GET or None)
        incident_form.fields['employee'].queryset = employee_data
        incident_form.fields['client'].queryset = client_data

        # Get all incidents for the selected clients and employees
        if read_all_incident:
            total_incidents = total_incidents
        else:
            total_incidents = Incident.bells_manager.filter(
                Q(company=company,
                report_type="Incident",
                client__in=client_data,
                employee__in=employee_data)|Q(employee=employee)
            ).order_by('-created_at')

        # Filter incidents based on request parameters
        incidents = filter_queryset(queryset=total_incidents, request=request)
        incidents = Incident.order_by_status(incidents)

        # Count incidents by status
        total_count = total_incidents.count()
        new_count = total_incidents.filter(status='New').count()
        in_progress_count = total_incidents.filter(status='InProgress').count()
        completed_count = total_incidents.filter(status='Closed').count()

        # Pagination
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(incidents, items_per_page)

        try:
            incidents_obj = paginator.page(page)
        except PageNotAnInteger:
            incidents_obj = paginator.page(1)
        except (EmptyPage, ValueError):
            incidents_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        start_entry = ((incidents_obj.number - 1) * items_per_page) + 1 if total_entries > 0 else 0
        end_entry = min(start_entry + items_per_page - 1, total_entries) if total_entries > 0 else 0

        context = {
            'incidents': incidents_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'total_count': total_count,
            'new_count': new_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'employee_data': employee_data,
            'client_data': client_data,
            'incident_form': incident_form,
            'start_date': request.GET.get('start_date'),
            'end_date': request.GET.get('end_date'),
            'show_update_button_for':show_update_button_for
        }
        return render(request, self.template_name, context)
    
def filter_queryset(queryset=None,request=None):
    employee = request.GET.get('employee')
    client = request.GET.get('client')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    incident_category = request.GET.get('incident_category')
    incident_classification = request.GET.get('incident_classification')
    
    model = queryset.model
    model_name = model.__name__.lower()
    
    if model_name == 'incident':
        filters = Q()
        if employee:
            filters &= Q(employee=employee)
        if client:
            filters &= Q(client=client)
        if status:
            filters &= Q(status=status)
        if incident_category:
            filters &= Q(incident_category=incident_category)
        if incident_classification:
            filters &= Q(incident_classification=incident_classification)
        if start_date and end_date:
            filters &= Q(incident_date_time__date__range=(start_date, end_date))
        elif start_date:
            filters &= Q(incident_date_time__date=start_date)
        elif end_date:
            filters &= Q(incident_date_time__date=end_date)
        return_data = queryset.filter(filters) if filters != Q() else queryset
    else:
        if employee and client and status:
            return_data = queryset.filter(Q(employee=employee)& Q(client=client)& Q(status = status))
        elif employee and client:
            return_data = queryset.filter(Q(employee=employee)& Q(client=client))
        elif employee and status:
            return_data = queryset.filter(Q(employee=employee)& Q(status= status))
        elif client and status:
            return_data = queryset.filter(Q(client=client)& Q(status= status))
        elif employee:
            return_data = queryset.filter(Q(employee=employee))
        elif client:
            return_data = queryset.filter(Q(client=client))
        elif status:
            return_data = queryset.filter(Q(status=status))
        else:
            return_data = queryset

        if start_date and end_date:
                return_data = return_data.filter(
                    Q(start_date_time__date__gte=start_date, end_date_time__date__lte=end_date)
                    
                )
        elif start_date:
                return_data = return_data.filter(start_date_time__date=start_date)
        elif end_date:
                return_data = return_data.filter(end_date_time__date=end_date)

    return return_data

    
@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['company_admin.create_progress_notes_own',
                                     'company_admin.view_progress_notes_all',
                                     'company_admin.view_progress_notes_own_team',
                                     'company_admin.view_progress_notes_own',
                                     'company_admin.update_progress_notes_all',
                                     'company_admin.update_progress_notes_own_team',
                                     'company_admin.update_progress_notes_own']), name='dispatch')
class DailyShiftNoteDashboard(View):
    template_name = "company_admin/dashboard/daily-shift-note-dashboard.html"
    def get(self,request,*args, **kwargs):
        employee = request.user.employee
        company = employee.company
        context={}   
        read_all_shifts = has_user_permission(request.user,'company_admin.view_progress_notes_all')
        read_team_shifts = has_user_permission(request.user,'company_admin.view_progress_notes_own_team')
        read_own_shifts = has_user_permission(request.user,'company_admin.view_progress_notes_own')
        update_all_shifts = has_user_permission(request.user,'company_admin.update_progress_notes_all')
        update_team_shifts = has_user_permission(request.user,'company_admin.update_progress_notes_own_team')
        
        if read_all_shifts:
            client_data = Client.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
            employee_data = Employee.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
        
        elif read_team_shifts:
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee.id,company_id=company.id)
            employee_data = manager_data['employees']
            employee_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id) 
            client_data = manager_data.get('clients', Client.bells_manager.none()) | employee_clients
            print(client_data,'client data...............   ')
                    
        elif read_own_shifts:
            client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id)
            filter_total_shifts = DailyShiftCaseNote.bells_manager.filter(
                company=company,
                client__in=client_data,
                employee=employee
            ).exclude(shift__status="Ongoing").order_by('-created_at').values_list('id', flat=True)
            show_update_button_for = set(filter_total_shifts)
           
        else:
            client_data = Client.bells_manager.none()
            employee_data = Employee.bells_manager.none()
            context['default_view']=True
            
        client_form = FilterQuerySetForm(request.GET or None)
        if read_own_shifts:
            # total_shifts = DailyShiftCaseNote.bells_manager.filter(company = company,client__in=client_data ,employee = employee).order_by('-created_at')
            total_shifts = DailyShiftCaseNote.bells_manager.filter(
                company=company,
                client__in=client_data,
                employee=employee
            ).exclude(shift__status="Ongoing").order_by('-created_at')

            employee_data = Employee.bells_manager.none()

        else:
            total_shifts = DailyShiftCaseNote.bells_manager.filter(company = company,client__in=client_data ,employee__in = employee_data).exclude(shift__status="Ongoing").order_by('-created_at')

        show_update_button_for = set()
        if update_all_shifts:
            filter_client_data = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            filter_total_shifts = DailyShiftCaseNote.bells_manager.filter(company=company, client__in=filter_client_data).order_by('-created_at').values_list('id', flat=True)
            show_update_button_for = set(filter_total_shifts)  
            
        elif update_team_shifts:
            filter_manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
            filter_client_data = filter_manager_data['clients'] 
            filter_employee_data = filter_manager_data['employees']      
            filter_total_shifts = DailyShiftCaseNote.bells_manager.filter(company=company, client__in=filter_client_data,employee__in=filter_employee_data).order_by('-created_at').values_list('id', flat=True)
            show_update_button_for = set(filter_total_shifts)  
        
        elif has_user_permission(request.user, 'company_admin.update_progress_notes_own'):
            client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id, company_id=company.id)
            filter_total_shifts = DailyShiftCaseNote.bells_manager.filter(
                company=company,
                client__in=client_data,
                employee=employee
            ).exclude(shift__status="Ongoing").order_by('-created_at').values_list('id', flat=True)
            show_update_button_for = set(filter_total_shifts)

        else:
            show_update_button_for = set() 
            filter_total_shifts = DailyShiftCaseNote.bells_manager.none()
            
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        client_form.fields['employee'].queryset = Employee.bells_manager.filter(id__in=[emp.id for emp in employee_data]) if employee_data else Employee.bells_manager.none()
        client_form.fields['client'].queryset = Client.bells_manager.filter(id__in=[cli.id for cli in client_data]) if client_data else Client.bells_manager.none()

        shifts = filter_queryset(queryset=total_shifts,request=request)

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(shifts, items_per_page)
        try:
            shifts_obj = paginator.page(page)
        except PageNotAnInteger:
            shifts_obj = paginator.page(1)
        except EmptyPage:
            shifts_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((shifts_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        
        context.update ({
            'shifts': shifts_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'total_count': total_shifts.count(),
            'employee': employee,
            'employee_data': employee_data,
            'client_data': client_data,
            'client_form': client_form,
            'start_date' :start_date,
            'end_date' :end_date,
            'show_update_button_for':show_update_button_for
        })
        return render(request,self.template_name, context)
    



# @method_decorator(login_required,name='dispatch')
# @method_decorator(check_permissions(['company_admin.update_incident_all',
#                                      'company_admin.update_incident_own_team',
#                                      'company_admin.create_incident_there_own',
#                                      'company_admin.create_incident_all',
#                                      'company_admin.create_incident_own_team']), name='dispatch')
# class IncidentOperationView(View):
#     template_name = "company_admin/dashboard/incidents/incident-operations.html"
    
#     def get(self, request, incident_id=None, *args, **kwargs):
#         """
#         This Method is used get request
#         """
#         employee = request.user.employee
#         company = employee.company
        
#         # Remove the session variables
#         request.session.pop('incident_id', None)
#         request.session.pop('employee_id', None)
#         request.session.pop('client_id', None)
#         incident = None
#         status_permission = []
#         incident_form = IncidentForm(initial={'company':company,'status':'New'},company=company,request=request)
#         severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)
        
#         incident = Incident.bells_manager.filter(pk=incident_id,report_type="Incident").first()
#         comment_instance = Comment.objects.filter(incident=incident).first()
        
#         context = {
#             "incident_form": incident_form,
#             'attachment_form': IncidentAttachmentForm(),
#             'contact_form': IncidentCommentForm(),
#             'question_form': IncidentQuestionForm(instance=comment_instance),
#             'severity_levels_json': severity_levels_json,
#             'question_updated_by': comment_instance.employee if comment_instance else ''
#         }
        
#         if incident_id and ('admin_incident_edit' in request.resolver_match.url_name or 'admin_incident_view' in request.resolver_match.url_name):
#             try:
#                 incident = Incident.bells_manager.get(pk=incident_id, report_type="Incident")
#                 incident_hierarchy = incident.investigation_hierarchy
#                 context['incident_hierarchy'] = incident_hierarchy
#                 context['incident'] = incident

#                 if incident_hierarchy:
#                     incident_stage_instance = None
#                     all_stages_completed = False
#                     available_stages = InvestigationStage.bells_manager.filter(
#                         hierarchy=incident_hierarchy,
#                         hierarchy__company = company,
#                         is_active=True,
#                         stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
#                             Q(owner=request.user.employee) | Q(substitute=request.user.employee)
#                         )
#                     ).order_by('s_no').distinct()
                    
#                     mapped_stages = IncidentStageMapper.bells_manager.filter(
#                         incident=incident,
#                         incident__company = request.user.employee.company
#                     ).select_related('stage').order_by('stage__s_no')

#                     ## Showing investigation details data to incident
#                     completed_stages_data = self.get_completed_stages_data(request, mapped_stages)
#                     context['completed_stages_data'] = completed_stages_data
                    
#                     current_stage_mapper = mapped_stages.filter(stage_status='pending').order_by('-stage__s_no').first()
#                     if current_stage_mapper:
#                         incident_stage_instance = current_stage_mapper.stage
#                         is_owner_or_substitute = StageOwnerSubstitute.bells_manager.filter(
#                             Q(owner=request.user.employee) | Q(substitute=request.user.employee), stage=incident_stage_instance
#                         ).exists()

                        
#                     if current_stage_mapper and is_owner_or_substitute:
#                         # incident_stage_instance = current_stage_mapper.stage
#                         # is_owner_or_substitute = StageOwnerSubstitute.bells_manager.filter(
#                         #     Q(owner=request.user.employee) | Q(substitute=request.user.employee), stage=incident_stage_instance
#                         # ).exists()

#                         # if is_owner_or_substitute:
#                         questions = InvestigationQuestion.bells_manager.filter(stage=incident_stage_instance)
#                         question_mappers = IncidentStageQuestionMapper.bells_manager.filter(
#                             incident_stage=current_stage_mapper
#                         )
#                         existing_answers = {qm.question_id: qm.answer for qm in question_mappers}
                        
#                         QuestionFormSet = modelformset_factory(
#                             InvestigationQuestion,
#                             form=InvestigationQuestionForm,
#                             extra=0,
#                             fields=['question']
#                         )
                        
#                         initial_data = [{'answer': existing_answers.get(q.id, '')} for q in questions]
                    
#                         StageQuestionformset = []
#                         for i, (question, init) in enumerate(zip(questions, initial_data)):
#                             form = InvestigationQuestionForm(
#                                 instance=question,
#                                 initial=init,
#                                 prefix=f'form-{i}' 
#                             )
#                             StageQuestionformset.append(form)
#                         permission_codename = get_user_incident_status_permission(incident_stage_instance)
#                         context['status_permission'] = permission_codename
#                         context['StageQuestionformset'] = StageQuestionformset
#                         context['incident_stage_instance'] = incident_stage_instance
#                         context['current_stage_mapper'] = current_stage_mapper

#                     else:
#                         highest_completed_sno = 0
#                         if mapped_stages.filter(stage_status='completed').exists():
#                             highest_completed_sno = mapped_stages.filter(
#                                 stage_status='completed'
#                             ).order_by('-stage__s_no').first().stage.s_no
                        
#                         next_stages = available_stages.filter(s_no=highest_completed_sno + 1)
#                         next_stage = next_stages.filter(
#                             stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
#                                 Q(owner=request.user.employee) | Q(substitute=request.user.employee)
#                             )
#                         ).first()
                        
#                         if next_stage and incident.status != 'Closed' :
#                             questions = InvestigationQuestion.bells_manager.filter(stage=next_stage)
#                             QuestionFormSet = modelformset_factory(
#                                 InvestigationQuestion,
#                                 form=InvestigationQuestionForm,
#                                 extra=0,
                                
#                             )
#                             permission_codename = get_user_incident_status_permission(next_stage)
#                             context['can_edit_status'] = permission_codename is not None
#                             # context['status_permission'] = permission_codename
#                             request.session['status_permission'] = list(permission_codename)
#                             context['status_permission'] = request.session.get('status_permission', [])

#                             StageQuestionformset = QuestionFormSet(queryset=questions)
#                             context['StageQuestionformset'] = StageQuestionformset
#                             context['incident_stage_instance'] = next_stage
#                             context['current_stage_mapper'] = None 
#                             all_stages_completed = False

#                         else:
#                             mapped_stage_s_nos = IncidentStageMapper.bells_manager.filter(
#                                 incident=incident,
#                                 incident__company = request.user.employee.company
#                             ).values_list('stage__s_no', flat=True)

#                             # Get available stages excluding already mapped ones
#                             next_available_stages = InvestigationStage.bells_manager.filter(
#                                 hierarchy=incident_hierarchy,
#                                 hierarchy__company=company,
#                                 is_active=True,
#                                 stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
#                                     Q(owner=request.user.employee) | Q(substitute=request.user.employee)
#                                 )
#                             ).exclude(s_no__in=Subquery(mapped_stage_s_nos)).order_by('s_no').distinct().exists()

#                             if next_available_stages and incident.status != 'Closed':
#                                 all_stages_completed = False
#                             elif not available_stages:
#                                 context['incident_stage_instance'] = incident_stage_instance
#                             else:
#                                 context['status_permission'] = request.session.get('status_permission', [])
#                                 all_stages_completed = True
#                     context['all_stages_completed'] = all_stages_completed
                    
#                 incident_form = IncidentForm(instance=incident, company=company, request=request)
#                 attachments_files = IncidentAttachment.bells_manager.filter(incident=incident)
#                 initial_data = [attachement for attachement in attachments_files]
#                 comments = Comment.objects.filter(incident=incident_id, content__isnull=False)
#                 context['attachment_data'] = initial_data
#                 context['incident_form'] = incident_form
#                 context['comments'] = comments
#                 context['incident_id'] = incident_id
#                 request.session['incident_id'] = incident_id
#                 request.session['client_id'] = incident.client.id
#                 request.session['employee_id'] = incident.employee.id
#                 request.session['confirm_modal_flag'] = False
#                 context['initial_value'] = {
#                     'initial_employee_name': incident.employee,
#                     'initial_phone_number': incident.employee.person.phone_number,
#                     'initial_email': incident.employee.person.email,
#                 }
                
#                 read_all_investigation = has_user_permission(request.user, 'company_admin.read_incident_investigation_all')
#                 read_team_investigation = has_user_permission(request.user, 'company_admin.read_incident_investigation_own_team')
#                 update_all_investigation = has_user_permission(request.user, 'company_admin.update_incident_investigation_all')
#                 update_team_investigation = has_user_permission(request.user, 'company_admin.update_incident_investigation_own_team')
                
#                 show_incident_investigation_for = set()
#                 show_update_incident_investigation_for = set()
#                 filter_total_incidents = Incident.bells_manager.none()
#                 if read_all_investigation or update_all_investigation:
#                     filter_client_data = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
#                     filter_employee_data = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
#                     filter_total_incidents = Incident.bells_manager.filter(
#                         company=company,
#                         report_type="Incident",
#                         client__in=filter_client_data,
#                     ).order_by('-created_at').values_list('id', flat=True)
#                     show_incident_investigation_for.update(filter_total_incidents)
#                     if update_all_investigation:
#                         show_update_incident_investigation_for.update(filter_total_incidents)
#                 if read_team_investigation or update_team_investigation:
#                     manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
#                     filter_employee_data = manager_data.get('employees', Employee.bells_manager.none())
#                     filter_client_data = manager_data.get('clients', Client.bells_manager.none())
                    
#                     filter_total_incidents = Incident.bells_manager.filter(
#                         company=company,
#                         report_type="Incident",
#                         employee__in=filter_employee_data,
#                         client__in=filter_client_data
#                     ).order_by('-created_at').values_list('id', flat=True)
#                     if read_team_investigation:
#                         show_incident_investigation_for.update(filter_total_incidents)
#                     if update_team_investigation:
#                         show_update_incident_investigation_for.update(filter_total_incidents)
                
#                 context['show_incident_investigation_for'] = show_incident_investigation_for
#                 context['show_update_incident_investigation_for'] = show_update_incident_investigation_for
                
#             except Exception as e:
#                 return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
        
#         return render(request, self.template_name, context)
   

#     # def get_completed_stages_data(self,request, mapped_stages):
#     #     """Get completed stages with questions/answers that the employee can view"""
#     #     completed_stages_data = []

#     #     current_employee = request.user.employee

#     #     valid_stage_ids = StageOwnerSubstitute.bells_manager.filter(
#     #         Q(owner=current_employee) | Q(substitute=current_employee)
#     #     ).values_list('stage_id', flat=True)

#     #     permission = Permission.objects.filter(codename='can_view_incident_investigation_details').first()

#     #     for stage_mapper in mapped_stages.filter(
#     #         stage_status='completed',
#     #         stage__id__in=valid_stage_ids
#     #     ):
#     #         stage = stage_mapper.stage

#     #         if permission and permission in stage.permissions.all():
#     #             question_answers = IncidentStageQuestionMapper.bells_manager.filter(
#     #                 incident_stage=stage_mapper
#     #             )

#     #             completed_stages_data.append({
#     #                 'stage': stage,
#     #                 'stage_mapper': stage_mapper,
#     #                 'question_answers': question_answers,
#     #                 'completed_on': stage_mapper.completed_at.strftime('%d %b %Y, %I:%M %p') if stage_mapper.completed_at else "Not recorded"

#     #             })

#     #     return completed_stages_data

#     def get_completed_stages_data(self, request, mapped_stages):
#         """Get completed stages with questions/answers that the employee can view"""
#         completed_stages_data = []

#         current_employee = request.user.employee

#         valid_stage_ids = StageOwnerSubstitute.bells_manager.filter(
#             Q(owner=current_employee) | Q(substitute=current_employee)
#         ).values_list('stage_id', flat=True)

#         permission = Permission.objects.filter(codename='can_view_incident_investigation_details').first()

#         for stage_mapper in mapped_stages.filter(
#             stage_status='completed',
#             stage__id__in=valid_stage_ids
#         ):
#             stage = stage_mapper.stage

#             if permission and permission in stage.permissions.all():
#                 question_answers = IncidentStageQuestionMapper.bells_manager.filter(
#                     incident_stage=stage_mapper
#                 ).select_related('question', 'created_by')

#                 # Include 'created_by' (question completed by) in the response
#                 question_answers_data = []
#                 for qa in question_answers:
#                     question_answers_data.append({
#                         'question': qa.question,
#                         'answer': qa.answer,
#                         'completed_by_name': f"{qa.created_by.person.get_full_name()}" if qa.created_by and qa.created_by.person else "N/A"
#                     })

#                 completed_stages_data.append({
#                     'stage': stage,
#                     'stage_mapper': stage_mapper,
#                     'question_answers': question_answers_data,
#                     'completed_on': stage_mapper.completed_at.strftime('%d %b %Y, %I:%M %p') if stage_mapper.completed_at else "Not recorded"
#                 })

#         return completed_stages_data



#     def get_company(self, request):
#         return request.user.employee.company

#     def post(self, request, incident_id=None, *args, **kwargs):
#         if 'incident_delete' in request.resolver_match.url_name:
#             return self.handle_delete(request, incident_id)
#         employee = request.user.employee
#         company = employee.company
#         company_hierarchy = InvestigationHierarchy.bells_manager.filter(company=company).first()

#         attachment_formset = IncidentAttachmentForm(request.POST, request.FILES)

#         if incident_id and 'admin_incident_edit' in request.resolver_match.url_name:
#             try:
#                 incident = Incident.bells_manager.get(pk=incident_id,report_type="Incident" )
#                 incident_form = IncidentForm(request.POST,instance=incident,company=company,request=request)
#             except:
#                 return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
#         else:
#             incident_form = IncidentForm(request.POST, {'company':company,'status':'New', 'sno':company.next_sno(), 'report_code':company.next_incident_report_code()},company=company,request=request)
#         if incident_form.is_valid()  and attachment_formset.is_valid():
#             try:
#                 files = request.FILES
#                 incident_form.instance.sno = company.next_sno()
#                 incident_form.instance.report_code = company.next_incident_report_code()
#                 instance = incident_form.save()
#                 if instance: 
#                     instance.investigation_hierarchy = company_hierarchy
#                     instance.save()
#                     client_assignments = ClientEmployeeAssignment.get_clients_by_employee(employee_id=instance.employee.id,company_id=company.id)
    
#                     if client_assignments.exists():
#                         if not client_assignments.filter(id=instance.client.id).exists():
#                             ClientEmployeeAssignment.bells_manager.create(
#                                 employee=instance.employee,
#                                 client=instance.client
#                             )
#                     else:
#                         ClientEmployeeAssignment.bells_manager.create(
#                         employee=instance.employee,
#                         client=instance.client
#                     )

#                 employee=incident_form.cleaned_data['employee']
               
#                 for file in files.getlist('file'):    
#                     IncidentAttachment.objects.create(incident=instance,file=file)
#                 if incident_id:
#                     delete_attachment_list = request.POST.get('deleteAttachmentFile',None)
#                     if delete_attachment_list is not None:
#                         data = [int(file_id) for file_id in delete_attachment_list.split(',') if file_id.isdigit()]
#                         for i in data:
#                             IncidentAttachment.objects.filter(id=i).update(is_deleted = True)
#                     messages.success(request, 'Incident updated successfully!')
#                 else:
#                     messages.success(request, 'Incident added successfully!')
#                     if has_user_permission(request.user, 'company_admin.create_incident_there_own'):
#                         company_email = request.user.employee.company.email_for_alerts
#                         company_name = request.user.employee.company.name
#                         employee_email = request.user.email
#                         report_code = incident_form.cleaned_data['report_code']
#                         client_first_name = incident_form.cleaned_data['client'].person.first_name
#                         client_last_name = incident_form.cleaned_data['client'].person.last_name
#                         employee_first_name = request.user.first_name
#                         employee_last_name = request.user.last_name
#                         incident_date = incident_form.cleaned_data['incident_date_time'].strftime('%Y-%m-%d %H:%M:%S')
#                         incident_type = "Incident"
#                         employee_email_template = 'employee/email/employee-incident-report.html'
#                         admin_email_template = 'employee/email/admin-incident-report.html'
#                         result = send_incident_email.apply_async(args=[company_name, company_email, employee_email, employee_first_name,
#                                 employee_last_name,client_first_name,client_last_name, incident_date, report_code,
#                                 employee_email_template, admin_email_template,incident_type])
                        
                    
#                 employee_email = incident_form.cleaned_data['employee'].person.email
#                 employee_first_name =  incident_form.cleaned_data['employee'].person.first_name
#                 employee_last_name= incident_form.cleaned_data['employee'].person.last_name
#                 report_code = incident_form.cleaned_data['report_code']
#                 incident_date = incident_form.cleaned_data['incident_date_time']
#                 incident_status = incident_form.cleaned_data['status']
#                 email_template = 'company_admin/employee/email/incident-status-update.html'

#                 # return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
#                 incident_id = instance.id if instance.id else incident_id
#                 current_employee_id = instance.employee.id if instance.employee else None
#                 current_client_id = instance.client.id if instance.client else None
                
                
#                 # Store values in session
#                 request.session['incident_id'] = incident_id
#                 request.session['employee_id'] = current_employee_id
#                 request.session['client_id'] = current_client_id
#                 request.session['confirm_modal_flag'] = True
#                 request.session['confirm_modal_flag_post'] = True

#                 if 'admin_incident_edit' == request.resolver_match.url_name:
#                     request.session['confirm_modal_flag'] = False
                 
#                 if 'admin_incident_add' ==  request.resolver_match.url_name:
#                     request.session['confirm_modal_flag'] = True
#                 is_invloved =incident_form.cleaned_data['employees_involved']
                
#                 if is_invloved == 'yes' and 'admin_incident_add' ==  request.resolver_match.url_name:
#                     return redirect('company:manager_tag_employee')
#                 return redirect('company:client_incident_reports_dashboard')    
            
#             except Exception as e:
#                 print(request, f"An error occurred: {e}")
#                 context = {
#                     'incident_form': incident_form,
#                     'attachment_form':attachment_formset,
#                 }
#                 return render(request, self.template_name, context)
#         else:
#             print("Form is not valid",request.POST, incident_form.errors,attachment_formset.errors)
#             incident = None
#             severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)
#             incident = Incident.bells_manager.filter(pk=incident_id,report_type="Incident").first()
#             comment_instance = Comment.objects.filter(incident=incident ).first()
#             contact_form = IncidentCommentForm(request.POST)
#             # If forms are not valid
#             context = {
#                     'incident_form': incident_form,
#                     'attachment_form':attachment_formset,
#                     'contact_form' : contact_form ,
#                     'question_form' : IncidentQuestionForm(instance=comment_instance),
#                     'severity_levels_json': severity_levels_json,
#                     'question_updated_by':comment_instance.employee if comment_instance else ''
#                 }
#             return render(request, self.template_name, context)
    
#     def handle_delete(self, request, incident_id):
#         def delete_operation(request, incident_id):
#             incident = get_object_or_404(Incident, pk=incident_id)
#             if incident:
#                 incident.is_deleted = True
#                 incident.save()
#             messages.success(request, 'Incident deleted successfully!')
#             return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
#         return delete_operation(request, incident_id)



@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['company_admin.update_incident_all',
                                     'company_admin.update_incident_own_team',
                                     'company_admin.create_incident_there_own',
                                     'company_admin.create_incident_all',
                                     'company_admin.create_incident_own_team']), name='dispatch')
class IncidentOperationView(View):
    template_name = "company_admin/dashboard/incidents/incident-operations.html"
    
    def get(self, request, incident_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        employee = request.user.employee
        company = employee.company
        # Remove the session variables
        request.session.pop('incident_id', None)
        request.session.pop('employee_id', None)
        request.session.pop('client_id', None)
        request.session.pop('status_permission', None)
        incident = None
        permission_is_applicable = False
        
        incident_form = IncidentForm(initial={'company':company,'status':'New'},company=company,request=request)
        severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)
        
        incident = Incident.bells_manager.filter(pk=incident_id,report_type="Incident").first()
        comment_instance = Comment.objects.filter(incident=incident).first()
        
        context = {
            "incident_form": incident_form,
            'attachment_form': IncidentAttachmentForm(),
            'contact_form': IncidentCommentForm(),
            'question_form': IncidentQuestionForm(instance=comment_instance),
            'severity_levels_json': severity_levels_json,
            'question_updated_by': comment_instance.employee if comment_instance else ''
        }
        
        if incident_id and ('admin_incident_edit' in request.resolver_match.url_name or 'admin_incident_view' in request.resolver_match.url_name):
            try:
                incident = Incident.bells_manager.get(pk=incident_id, report_type="Incident")
                incident_hierarchy = incident.investigation_hierarchy
                context['incident_hierarchy'] = incident_hierarchy
                context['incident'] = incident

                if incident_hierarchy:
                    incident_stage_instance = None
                    all_stages_completed = False
                    available_stages = InvestigationStage.bells_manager.filter(
                        hierarchy=incident_hierarchy,
                        hierarchy__company = company,
                        is_active=True,
                        stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
                            Q(owner=request.user.employee) | Q(substitute=request.user.employee)
                        )
                    ).order_by('s_no').distinct()
                    
                    mapped_stages = IncidentStageMapper.bells_manager.filter(
                        incident=incident,
                        incident__company = request.user.employee.company
                    ).select_related('stage').order_by('stage__s_no')


                    # if available_stages:
                    #     next_available_stages = available_stages.first()

                    #     next_sno = next_available_stages.s_no

                    #     if next_sno > 1:
                    #         last_stage_mapper = mapped_stages.last() 
                            
                    #         if last_stage_mapper and last_stage_mapper.stage.s_no < next_sno:
                    #             if last_stage_mapper.stage_status == 'completed':  
                    #                 permission_is_applicable = True
                    #     else:
                    #         permission_is_applicable = True
                                    
                    ## Showing investigation details data to incident
                    completed_stages_data = self.get_completed_stages_data(request, mapped_stages)
                    context['completed_stages_data'] = completed_stages_data
                    
                    current_stage_mapper = mapped_stages.filter(stage_status='pending').order_by('-stage__s_no').first()
                    if current_stage_mapper:
                        incident_stage_instance = current_stage_mapper.stage
                        is_owner_or_substitute = StageOwnerSubstitute.bells_manager.filter(
                            Q(owner=request.user.employee) | Q(substitute=request.user.employee), stage=incident_stage_instance
                        ).exists()

                        
                    if current_stage_mapper and is_owner_or_substitute:
                        questions = InvestigationQuestion.bells_manager.filter(stage=incident_stage_instance)
                        question_mappers = IncidentStageQuestionMapper.bells_manager.filter(
                            incident_stage=current_stage_mapper
                        )
                        existing_answers = {qm.question_id: qm.answer for qm in question_mappers}
                        
                        QuestionFormSet = modelformset_factory(
                            InvestigationQuestion,
                            form=InvestigationQuestionForm,
                            extra=0,
                            fields=['question']
                        )
                        
                        initial_data = [{'answer': existing_answers.get(q.id, '')} for q in questions]
                    
                        StageQuestionformset = []
                        for i, (question, init) in enumerate(zip(questions, initial_data)):
                            form = InvestigationQuestionForm(
                                instance=question,
                                initial=init,
                                prefix=f'form-{i}' 
                            )
                            StageQuestionformset.append(form)
                        permission_codename = get_user_incident_status_permission(incident_stage_instance)
                        context['status_permission'] = permission_codename
                        context['StageQuestionformset'] = StageQuestionformset
                        context['incident_stage_instance'] = incident_stage_instance
                        context['current_stage_mapper'] = current_stage_mapper

                    else:
                        highest_completed_sno = 0
                        if mapped_stages.filter(stage_status='completed').exists():
                            highest_completed_sno = mapped_stages.filter(
                                stage_status='completed'
                            ).order_by('-stage__s_no').first().stage.s_no
                        
                        next_stages = available_stages.filter(s_no=highest_completed_sno + 1)
                            
                        next_stage = next_stages.filter(
                            stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
                                Q(owner=request.user.employee) | Q(substitute=request.user.employee)
                            )
                        ).first()
                        if next_stage:
                            request.session['current_stage_id'] = next_stage.id
                        if next_stage and incident.status != 'Closed' :
                            questions = InvestigationQuestion.bells_manager.filter(stage=next_stage)
                            QuestionFormSet = modelformset_factory(
                                InvestigationQuestion,
                                form=InvestigationQuestionForm,
                                extra=0,
                                
                            )
                            permission_codename = get_user_incident_status_permission(next_stage)
                            context['can_edit_status'] = permission_codename is not None
                            # context['status_permission'] = permission_codename
                            request.session['status_permission'] = list(permission_codename)
                            context['status_permission'] = request.session.get('status_permission', [])

                            StageQuestionformset = QuestionFormSet(queryset=questions)
                            context['StageQuestionformset'] = StageQuestionformset
                            context['incident_stage_instance'] = next_stage
                            context['current_stage_mapper'] = None 
                            all_stages_completed = False

                        else:
                            mapped_stage_s_nos = IncidentStageMapper.bells_manager.filter(
                                incident=incident,
                                incident__company = request.user.employee.company
                            ).values_list('stage__s_no', flat=True)

                            # Get available stages excluding already mapped ones
                            next_available_stages = InvestigationStage.bells_manager.filter(
                                hierarchy=incident_hierarchy,
                                hierarchy__company=company,
                                is_active=True,
                                stage_owners__in=StageOwnerSubstitute.bells_manager.filter(
                                    Q(owner=request.user.employee) | Q(substitute=request.user.employee)
                                )
                            ).exclude(s_no__in=Subquery(mapped_stage_s_nos)).order_by('s_no').distinct().exists()

                            if next_available_stages and incident.status != 'Closed':
                                all_stages_completed = False
                            elif not available_stages:
                                context['incident_stage_instance'] = incident_stage_instance
                            else:
                                if next_stage:
                                    permission_codename = get_user_incident_status_permission(next_stage)
                                    context['status_permission'] = permission_codename

                                else:
                                    current_stage_id = request.session.get('current_stage_id')
                                    is_owner_or_substitute = StageOwnerSubstitute.bells_manager.filter(
                                        Q(owner=request.user.employee) | Q(substitute=request.user.employee), stage=current_stage_id
                                    ).exists()
                                    if is_owner_or_substitute:
                                        stage_instance=InvestigationStage.bells_manager.filter(id=current_stage_id).first()
                                        if stage_instance:
                                            permission_codename = get_user_incident_status_permission(stage_instance)
                                            context['status_permission'] = permission_codename
                                        
                                    # context['status_permission'] = request.session.get('status_permission', [])
                                all_stages_completed = True
                        

                    context['all_stages_completed'] = all_stages_completed
                    
                incident_form = IncidentForm(instance=incident, company=company, request=request)
                attachments_files = IncidentAttachment.bells_manager.filter(incident=incident)
                initial_data = [attachement for attachement in attachments_files]
                comments = Comment.objects.filter(incident=incident_id, content__isnull=False)
                context['attachment_data'] = initial_data
                context['incident_form'] = incident_form
                context['comments'] = comments
                context['incident_id'] = incident_id
                request.session['incident_id'] = incident_id
                request.session['client_id'] = incident.client.id
                request.session['employee_id'] = incident.employee.id
                request.session['confirm_modal_flag'] = False
                context['initial_value'] = {
                    'initial_employee_name': incident.employee,
                    'initial_phone_number': incident.employee.person.phone_number,
                    'initial_email': incident.employee.person.email,
                }
                
                read_all_investigation = has_user_permission(request.user, 'company_admin.read_incident_investigation_all')
                read_team_investigation = has_user_permission(request.user, 'company_admin.read_incident_investigation_own_team')
                read_self_investigation = has_user_permission(request.user, 'company_admin.read_incident_investigation_self')

                update_all_investigation = has_user_permission(request.user, 'company_admin.update_incident_investigation_all')
                update_team_investigation = has_user_permission(request.user, 'company_admin.update_incident_investigation_own_team')
                update_self_investigation = has_user_permission(request.user, 'company_admin.update_incident_investigation_self')

                show_investigation_details_for = set()
                show_update_incident_investigation_for = set()
                filter_total_incidents = Incident.bells_manager.none()
                if read_all_investigation or update_all_investigation:
                    filter_total_incidents = Incident.bells_manager.filter(
                        company=company,
                        report_type="Incident",
                        id=incident_id,
                    ).order_by('-created_at').values_list('id', flat=True)
                    if read_all_investigation:
                        show_investigation_details_for.update(filter_total_incidents)
                    if update_all_investigation:
                        show_update_incident_investigation_for.update(filter_total_incidents)

                if read_team_investigation or update_team_investigation:
                    manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
                    filter_employee_data = manager_data.get('employees', Employee.bells_manager.none())
                    filter_client_data = manager_data.get('clients', Client.bells_manager.none())
                    
                    filter_total_incidents = Incident.bells_manager.filter(
                        company=company,
                        report_type="Incident",
                        employee__in=filter_employee_data,
                        client__in=filter_client_data
                    ).order_by('-created_at').values_list('id', flat=True)
                    if read_team_investigation:
                        show_investigation_details_for.update(filter_total_incidents)
                    if update_team_investigation:
                        show_update_incident_investigation_for.update(filter_total_incidents)
                
                if read_self_investigation or update_self_investigation:
                    filter_client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id = employee.id,company_id=company.id)
                    filter_total_incidents = Incident.bells_manager.filter(
                        company=company,
                        report_type="Incident",
                        client__in=filter_client_data
                    ).order_by('-created_at').values_list('id', flat=True)
                    if read_self_investigation:
                        show_investigation_details_for.update(filter_total_incidents)
                    if update_self_investigation:
                        show_update_incident_investigation_for.update(filter_total_incidents)
                        if not incident_id in show_update_incident_investigation_for: 
                            context['status_permission'] = None
                context['show_investigation_details_for'] = show_investigation_details_for
                context['show_update_incident_investigation_for'] = show_update_incident_investigation_for
                # if not show_update_incident_investigation_for or incident.status == 'Closed':
                #     context['status_permission'] = '' or None
                
                # if (not show_update_incident_investigation_for or incident.status == 'Closed') and not permission_is_applicable:
                #     context['status_permission'] = None
                if not show_update_incident_investigation_for or not incident_id in show_update_incident_investigation_for:
                        context['status_permission'] = None
            except Exception as e:
                return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
        return render(request, self.template_name, context)
   

    def get_completed_stages_data(self, request, mapped_stages):
        """Get completed stages with questions/answers that the employee can view"""
        completed_stages_data = []

        current_employee = request.user.employee

        valid_stage_ids = StageOwnerSubstitute.bells_manager.filter(
            Q(owner=current_employee) | Q(substitute=current_employee)
        ).values_list('stage_id', flat=True)

        for stage_mapper in mapped_stages.filter(
            stage_status='completed',
            # stage__id__in=valid_stage_ids
        ):
            stage = stage_mapper.stage

            question_answers = IncidentStageQuestionMapper.bells_manager.filter(
                incident_stage=stage_mapper
            ).select_related('question', 'created_by')

            question_answers_data = []
            for qa in question_answers:
                question_answers_data.append({
                    'question': qa.question,
                    'answer': qa.answer,
                    'completed_by_name': f"{qa.created_by.person.get_full_name()}" if qa.created_by and qa.created_by.person else "N/A"
                })

            completed_stages_data.append({
                'stage': stage,
                'stage_mapper': stage_mapper,
                'question_answers': question_answers_data,
                'completed_on': stage_mapper.completed_at.strftime('%d %b %Y, %I:%M %p') if stage_mapper.completed_at else "Not recorded"
            })

        return completed_stages_data


    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, incident_id=None, *args, **kwargs):
        if 'incident_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, incident_id)
        employee = request.user.employee
        company = employee.company
        company_hierarchy = InvestigationHierarchy.bells_manager.filter(company=company).first()

        attachment_formset = IncidentAttachmentForm(request.POST, request.FILES)

        if incident_id and 'admin_incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id,report_type="Incident" )
                incident_form = IncidentForm(request.POST,instance=incident,company=company,request=request)
            except:
                return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
        else:
            incident_form = IncidentForm(request.POST, {'company':company,'status':'New', 'sno':company.next_sno(), 'report_code':company.next_incident_report_code()},company=company,request=request)
        if incident_form.is_valid()  and attachment_formset.is_valid():
            try:
                files = request.FILES
                if request.resolver_match.url_name != 'admin_incident_edit':
                    incident_form.instance.sno = company.next_sno()
                    incident_form.instance.report_code = company.next_incident_report_code()
                    
                instance = incident_form.save()
                if instance: 
                    instance.investigation_hierarchy = company_hierarchy
                    instance.save()
                    client_assignments = ClientEmployeeAssignment.get_clients_by_employee(employee_id=instance.employee.id,company_id=company.id)
    
                    if client_assignments.exists():
                        if not client_assignments.filter(id=instance.client.id).exists():
                            ClientEmployeeAssignment.bells_manager.create(
                                employee=instance.employee,
                                client=instance.client
                            )
                    else:
                        ClientEmployeeAssignment.bells_manager.create(
                        employee=instance.employee,
                        client=instance.client
                    )

                employee=incident_form.cleaned_data['employee']
               
                for file in files.getlist('file'):    
                    IncidentAttachment.objects.create(incident=instance,file=file)
                if incident_id:
                    delete_attachment_list = request.POST.get('deleteAttachmentFile',None)
                    if delete_attachment_list is not None:
                        data = [int(file_id) for file_id in delete_attachment_list.split(',') if file_id.isdigit()]
                        for i in data:
                            IncidentAttachment.objects.filter(id=i).update(is_deleted = True)
                    messages.success(request, 'Incident updated successfully!')
                else:
                    messages.success(request, 'Incident added successfully!')
                    if has_user_permission(request.user, 'company_admin.create_incident_there_own'):
                        company_email = request.user.employee.company.email_for_alerts
                        company_name = request.user.employee.company.name
                        employee_email = request.user.email
                        report_code = incident_form.cleaned_data['report_code']
                        client_first_name = incident_form.cleaned_data['client'].person.first_name
                        client_last_name = incident_form.cleaned_data['client'].person.last_name
                        employee_first_name = request.user.first_name
                        employee_last_name = request.user.last_name
                        incident_date = incident_form.cleaned_data['incident_date_time'].strftime('%Y-%m-%d %H:%M:%S')
                        incident_type = "Incident"
                        employee_email_template = 'employee/email/employee-incident-report.html'
                        admin_email_template = 'employee/email/admin-incident-report.html'
                        result = send_incident_email.apply_async(args=[company_name, company_email, employee_email, employee_first_name,
                                employee_last_name,client_first_name,client_last_name, incident_date, report_code,
                                employee_email_template, admin_email_template,incident_type])
                        
                    
                employee_email = incident_form.cleaned_data['employee'].person.email
                employee_first_name =  incident_form.cleaned_data['employee'].person.first_name
                employee_last_name= incident_form.cleaned_data['employee'].person.last_name
                report_code = incident_form.cleaned_data['report_code']
                incident_date = incident_form.cleaned_data['incident_date_time']
                incident_status = incident_form.cleaned_data['status']
                email_template = 'company_admin/employee/email/incident-status-update.html'

                # return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
                incident_id = instance.id if instance.id else incident_id
                current_employee_id = instance.employee.id if instance.employee else None
                current_client_id = instance.client.id if instance.client else None
                
                
                # Store values in session
                request.session['incident_id'] = incident_id
                request.session['employee_id'] = current_employee_id
                request.session['client_id'] = current_client_id
                request.session['confirm_modal_flag'] = True
                request.session['confirm_modal_flag_post'] = True

                if 'admin_incident_edit' == request.resolver_match.url_name:
                    request.session['confirm_modal_flag'] = False
                 
                if 'admin_incident_add' ==  request.resolver_match.url_name:
                    request.session['confirm_modal_flag'] = True
                is_invloved =incident_form.cleaned_data['employees_involved']
                
                if is_invloved == 'yes' and 'admin_incident_add' ==  request.resolver_match.url_name:
                    return redirect('company:manager_tag_employee')
                return redirect('company:client_incident_reports_dashboard')    
            
            except Exception as e:
                print(request, f"An error occurred: {e}")
                context = {
                    'incident_form': incident_form,
                    'attachment_form':attachment_formset,
                }
                return render(request, self.template_name, context)
        else:
            print("Form is not valid",request.POST, incident_form.errors,attachment_formset.errors)
            incident = None
            severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)
            incident = Incident.bells_manager.filter(pk=incident_id,report_type="Incident").first()
            comment_instance = Comment.objects.filter(incident=incident ).first()
            contact_form = IncidentCommentForm(request.POST)
            # If forms are not valid
            context = {
                    'incident_form': incident_form,
                    'attachment_form':attachment_formset,
                    'contact_form' : contact_form ,
                    'question_form' : IncidentQuestionForm(instance=comment_instance),
                    'severity_levels_json': severity_levels_json,
                    'question_updated_by':comment_instance.employee if comment_instance else ''
                }
            return render(request, self.template_name, context)
    
    def handle_delete(self, request, incident_id):
        def delete_operation(request, incident_id):
            incident = get_object_or_404(Incident, pk=incident_id)
            if incident:
                incident.is_deleted = True
                incident.save()
            messages.success(request, 'Incident deleted successfully!')
            return HttpResponseRedirect(reverse('company:client_incident_reports_dashboard'))
        return delete_operation(request, incident_id)


@method_decorator(login_required,name='dispatch')
@method_decorator(employee_role_required,name='dispatch')
@method_decorator(user_can_access_mandatory_incident_report,name='dispatch')
class MandatoryIncidentOperationView(View):
    
    template_name = "company_admin/dashboard/mandatory_incidents/mandatory-incident-operations.html"
    
    def get(self, request, incident_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        employee = request.user.employee
        company = employee.company
        incident = None
        incident_form = MandatoryIncidentForm(initial={'company':company,'status':'New','report_type':'Mandatory Incident', 'sno':company.mandatory_next_sno(), 'report_code':company.mandatory_report_code()},company=company,request=request)

        severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)

        context = {
            "incident_form":incident_form,
            'attachment_form':MandatoryIncidentAttachmentForm(),
            'contact_form' : IncidentCommentForm(),
            'question_form' : IncidentQuestionForm(),
            'severity_levels_json':severity_levels_json

        }
        if incident_id and 'admin_mandatory_incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id,report_type="Mandatory Incident")
                incident_form = MandatoryIncidentForm(instance=incident,company=company,request=request)
                attachments_files = IncidentAttachment.bells_manager.filter(incident = incident)
                initial_data  = [attachement for attachement in attachments_files]
                comments = Comment.objects.filter(incident=incident_id)
                context['attachment_data'] = initial_data
                context['incident_form'] = incident_form
                context['comments'] = comments
                context['incident_id'] = incident_id

                context['initial_value'] = {'initial_employee_name':incident.employee,'initial_phone_number':incident.employee.person.phone_number,'initial_email':incident.employee.person.email}
            except Exception as e:
                print(e)
                return HttpResponseRedirect(reverse('company:mandatory_incident_reports_dashboard'))
        return render(request, self.template_name, context)

    
    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, incident_id=None, *args, **kwargs):
        if 'mandatory_incident_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, incident_id)
        employee = request.user.employee
        company = employee.company
        attachment_formset = MandatoryIncidentAttachmentForm(request.POST, request.FILES)
        if incident_id and 'admin_mandatory_incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id,report_type="Mandatory Incident")
                incident_form = MandatoryIncidentForm(request.POST, instance=incident,company=company,request=request)
            except:
                return HttpResponseRedirect(reverse('company:mandatory_incident_reports_dashboard'))
        else:
            incident_form = MandatoryIncidentForm(request.POST, {'company':company,'status':'New','report_type':'Mandatory Incident', 'sno':company.mandatory_next_sno(), 'report_code':company.mandatory_report_code()},company=company,request=request)
        if incident_form.is_valid() and attachment_formset.is_valid():
            try:
                files = request.FILES
                instance = incident_form.save()
                employee= incident_form.cleaned_data['employee']
                # if request.POST.get('content'):
                #     comment_data = {
                #         'employee': employee,
                #         'incident': instance,
                #         'report_type': 'Mandatory Incident',
                #         'content':request.POST.get('content')
                #     }
                #     comment_form = IncidentCommentForm(comment_data)
                #     if comment_form.is_valid():
                #         comment_form.save()

                for file in files.getlist('file'):    
                    IncidentAttachment.objects.create(incident=instance,file=file)
                if incident_id:
                    delete_attachment_list = request.POST.get('deleteAttachmentFile')
                    if delete_attachment_list is not None:
                        data = [int(file_id) for file_id in delete_attachment_list.split(',') if file_id.isdigit()]
                        for i in data:
                            IncidentAttachment.objects.filter(id=i).update(is_deleted = True)
                    messages.success(request, 'Mandatory Incident updated successfully!')
                else:
                    messages.success(request, 'Mandatory Incident added successfully!')
                employee_email = incident_form.cleaned_data['employee'].person.email
                employee_first_name = incident_form.cleaned_data['employee'].person.first_name
                employee_last_name=incident_form.cleaned_data['employee'].person.last_name
                report_code = incident_form.cleaned_data['report_code']
                incident_date = incident_form.cleaned_data['incident_date_time']
                incident_status = incident_form.cleaned_data['status']
                email_template = 'company_admin/employee/email/incident-status-update.html'
                # incident_update_email.apply_async(args=[employee_email,employee_first_name,employee_last_name,report_code,incident_date,incident_status,email_template])
                return HttpResponseRedirect(reverse('company:mandatory_incident_reports_dashboard'))
            except Exception as e:
                print(request, f"An error occurred: {e}")
                context = {
                    'incident_form': incident_form,
                    'attachment_form':attachment_formset,
                }
                return render(request, self.template_name, context)
        else:
            print("Form is not valid",incident_form.errors)
            # If forms are not valid
            context = {
                    'incident_id':incident_id,
                    'incident_form': incident_form,
                    'attachment_form':attachment_formset,
                }
            return render(request, self.template_name, context)
    
    def handle_delete(self, request, incident_id):
        @admin_role_required
        def delete_operation(request, incident_id):
            incident = get_object_or_404(Incident, pk=incident_id)
            if incident:
                incident.is_deleted = True
                incident.save()
            messages.success(request, 'Mandatory Incident deleted successfully!')
            return HttpResponseRedirect(reverse('company:mandatory_incident_reports_dashboard'))
        return delete_operation(request, incident_id)



@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['company_admin.create_progress_notes_own',
                                     'company_admin.view_progress_notes_all',
                                     'company_admin.view_progress_notes_own_team',
                                     'company_admin.update_progress_notes_all',
                                     'company_admin.update_progress_notes_own_team',
                                     ]), name='dispatch')
class ShiftViewOperations(View):
    template_name = "company_admin/dashboard/daily_shift/shift-operations.html"
    
    def get(self, request, shift_note_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        employee = request.user.employee
        company = employee.company
        shift_note = None
        shiftid = None
        employee_shift_form = None
        
        assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(
            employee_id=employee.id, company_id=company.id
        ).values_list('id', flat=True)

        update_all_shift_notes = has_user_permission(request.user, 'company_admin.update_progress_notes_all')
        update_team_shift_notes = has_user_permission(request.user, 'company_admin.update_progress_notes_own_team')

        if update_all_shift_notes:
            clients = Client.bells_manager.filter(company=company)
        elif update_team_shift_notes:
            department_data = DepartmentClientAssignment.get_manager_department_data(
                manager_id=employee.id, company_id=company.id
            )
            team_client_ids = set(department_data['clients'].values_list('id', flat=True))
            clients = Client.bells_manager.filter(id__in=team_client_ids)
            print(clients)
        else:
            clients = Client.bells_manager.filter(id__in=assigned_clients)
        # shift_form = DailyShiftNoteForm(initial={'employee': employee, 'company': company, 'sno': company.next_daily_shift_sno()}, company=company)
        shift_form = DailyShiftNoteForm(initial={
            'employee': employee, 
            'company': company, 
            'sno': company.next_daily_shift_sno(),
            'client': clients
        },
        request=request, 
        company=company,
        )
        
        if shift_note_id:
            if request.resolver_match.url_name == 'admin_dailyshift_edit' :
                try:
                    shift_note = DailyShiftCaseNote.bells_manager.get(pk=shift_note_id)
                    shiftid = shift_note.shift.id
                    shift_form = DailyShiftNoteForm(instance=shift_note, company=company, request=request)
                    employee_shift_instance = Shifts.bells_manager.filter(id=shift_note.shift.id, company=company).first()
                    employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance, request=request)
                except Exception as e:
                    return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
                
            if request.resolver_match.url_name == 'admin_dailyshift_view':
                try:
                    shift_note = DailyShiftCaseNote.bells_manager.get(pk=shift_note_id)
                    shiftid = shift_note.shift.id
                    shift_form = DailyShiftNoteForm(instance=shift_note, company=company, request=request)
                    employee_shift_instance = Shifts.bells_manager.filter(id=shift_note.shift.id, company=company).first()
                    employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance, request=request)
                except Exception as e:
                    return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
        
        context = {
            'shift_form': shift_form,
            'shift': shift_note,
            'shift_note_id':shift_note_id,
            'shiftid': shiftid,
            'employee_shift_form': employee_shift_form
        }
        return render(request, self.template_name, context)

    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, shift_note_id=None, *args, **kwargs):
        if 'shift_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, shift_note_id)
        
        employee = request.user.employee
        company = employee.company
        
        if shift_note_id and 'admin_dailyshift_edit' in request.resolver_match.url_name:
            try:
                shift_note = DailyShiftCaseNote.bells_manager.get(pk=shift_note_id)
                shift_form = DailyShiftNoteForm(request.POST,request.FILES, instance=shift_note, company=company,request=request)
            except Exception as e:
                return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
        else:
            shift_form = DailyShiftNoteForm(request.POST, {'employee': employee, 'company': company, 'sno': company.next_daily_shift_sno()}, company=company)
        
        if shift_form.is_valid():
            try:
                progress_note = shift_form.save(commit=False)
                shift_id = shift_form.cleaned_data['shift'].id
                if shift_id:
                    shift_obj = Shifts.bells_manager.filter(id=shift_id, company=company).first()
                    if shift_obj:
                        description = shift_form.cleaned_data.get('description', '').strip()
                        start_date_time = shift_form.cleaned_data['start_date_time']
                        end_date_time = shift_form.cleaned_data['end_date_time'] if 'end_date_time' in shift_form.cleaned_data else None
                        if not description :
                            shift_obj.status = 'Pending'
                        else:
                            shift_obj.status = 'Completed'
                            shift_obj.total_hour = shift_obj.calculate_total_hour(start_date_time, end_date_time)


                        progress_note.shift = shift_obj
                        # start_date_time = shift_form.cleaned_data['start_date_time']
                        # end_date_time = shift_form.cleaned_data['end_date_time'] if 'end_date_time' in shift_form.cleaned_data else None
                        shift_obj.start_date_time = start_date_time
                        shift_obj.end_date_time = end_date_time
                        shift_obj.shift_type = request.POST.get('shift_type')
                        # shift_obj.total_hour = shift_obj.calculate_total_hour(start_date_time, end_date_time)
                        shift_obj.save()    
                progress_note.save()

                messages.success(request, 'Shift note updated successfully!' if shift_id else 'Shift note added successfully!')
                return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
            except Exception as e:
                employee_shift_instance = Shifts.bells_manager.filter(id=shift_id, company=company).first() 
                employee_shift_form = EmployeeShiftsForm(request.POST,instance=employee_shift_instance, company=company,request=request)

                context = {
                    'shift_form': shift_form,
                    'employee_shift_form': employee_shift_form,
                }
                return render(request, self.template_name, context)
        else:
            shift_note = DailyShiftCaseNote.bells_manager.filter(id=shift_note_id).first()
    
            employee_shift_instance = Shifts.bells_manager.filter(id=shift_note.shift.id, company=company).first() 
            employee_shift_form = EmployeeShiftsForm(request.POST, instance=employee_shift_instance, request=request)

            context = {
                'shift':shift_note,
                'shift_form': shift_form,
                'employee_shift_form': employee_shift_form,
                'shift_type' : employee_shift_instance.shift_type,
                'shift_note_id':shift_note_id,
                'shiftid':shift_note.shift.id
            }
            return render(request, self.template_name, context)
    
    def handle_delete(self, request, shift_id):
        def delete_operation(request, shift_id):
            shift = get_object_or_404(DailyShiftCaseNote, pk=shift_id)
            if shift:
                shift.is_deleted = True
                shift.save()
                messages.success(request, 'Shift note deleted successfully!')
            return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
        return delete_operation(request, shift_id)



    
        
@login_required
def GetEmployeeDetails(request,pk):
        try:
            employee_details = Employee.bells_manager.filter(id=pk).first()
            data = {'first_name':employee_details.person.first_name,
                    'phone_number':employee_details.person.phone_number,
                    'email':employee_details.person.email}
            return JsonResponse(data,safe=False,status=200)
        except Exception as e:
            return JsonResponse({'error':str(e)},safe=False, status=400)


# @method_decorator(login_required,name='dispatch')
# @method_decorator(admin_role_required,name='dispatch')
# @method_decorator(user_can_access_employee, name='dispatch')
# class RiskAssessmentView(View):
#     template_name = 'company_admin/clients/client_profile.html'

#     def get(self,request,*args, **kwargs):
#         risk_assessment  = RiskAssessment.bells_manager.all().order_by("-created_at")
#         return render(request,self.template_name,{'risk_assessment':risk_assessment})


@method_decorator(login_required, name='dispatch')
class GetRiskArea(View):
    def get(self, request, *args, **kwargst):
        risk_type_id = request.GET.get('risk_type_id')
        risk_areas = RiskArea.objects.filter(risk_type_id=risk_type_id).values('id', 'name')
        return JsonResponse(list(risk_areas), safe=False)



 

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.create_all_risk_assessments',
                                     'company_admin.create_risk_assessments_team_own',
                                     'company_admin.update_all_risk_assessments',
                                     'company_admin.update_team_risk_assessments',
                                     'company_admin.create_risk_assessments_of_their_own',
                                     'company_admin.read_risk_assessments_of_their_own',
                                     'company_admin.risk_assessment_update_none'

                                    ]), name='dispatch')
class RiskAssessmentOperationView(View):
    """
    This view handles the operations related to risk assessment of clients 
    """

    template_name = 'company_admin/clients/client_profile.html'
    def get(self, request,client_id=None,risk_assessment_detail_id=None,risk_assessment_id=None, *args, **kwargs):
        """
        This Method is used to handle get request
        """
        company = self.get_company(request)
        client_obj = Client.bells_manager.get(pk=client_id)
        risk_assessment_detail_obj, risk_assessment_detail_formset_for_modals  = None, None
        employee= request.user.employee
        if request.resolver_match.url_name == 'risk_assessment_add':
            request.session['is_employee_request'] = False

        if risk_assessment_id and 'risk_assessment_edit' in request.resolver_match.url_name:
            try:
                risk_assessment = RiskAssessment.bells_manager.get(id=risk_assessment_id)
                risk_assessment_detail_obj  = RiskAssessmentDetail.objects.filter(risk_assessment=risk_assessment,is_deleted=False)              
                RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskAssessmentDetailFormSet_for_modals = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                risk_assessment_detail_formset_for_modals = RiskAssessmentDetailFormSet_for_modals(instance=risk_assessment,  prefix='edit_detail',form_kwargs={'request': request},queryset=RiskAssessmentDetail.bells_manager.filter(risk_assessment=risk_assessment, is_deleted=False))

                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment, RiskDocumentationApproval, form=RiskDocumentationApprovalForm,extra =1 if risk_assessment.documentation.first() is None else 0)
                RiskMoniterControlFormSet = get_formset(RiskAssessment, RiskMoniterControl, form=RiskMoniterControlForm, extra=1 if risk_assessment.management_approval.first() is None else 0)
                risk_assessment_form = RiskAssessmentForm(instance=risk_assessment,company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(instance=risk_assessment,prefix='approval',queryset=RiskDocumentationApproval.bells_manager.order_by('-id'))
                risk_moniter_control_formset = RiskMoniterControlFormSet(instance=risk_assessment,  prefix='monitor',queryset=RiskMoniterControl.bells_manager.order_by('-id'))
                
                request.session['risk_assessment_instance_id'] = risk_assessment.id
                request.session.pop('post_page_request', None)

            except Exception as e:
                print('e')
                return HttpResponseRedirect(reverse('company:client_profile'))

        else:
            risk_assessment_check = request.GET.get('risk_assessment')
            if risk_assessment_check:
                last_risk_assessment_id = request.session.get('risk_assessment_instance_id',None)
                if last_risk_assessment_id and client_id:
                    risk_assessment = RiskAssessment.bells_manager.get(id=request.session['risk_assessment_instance_id'])
                    RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)                
                    RiskAssessmentDetailFormSet_for_modals = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)

                    risk_assessment_form = RiskAssessmentForm(instance=risk_assessment,company=company)
                    risk_assessment_detail_formset_for_modals = RiskAssessmentDetailFormSet_for_modals(instance=risk_assessment,  prefix='edit_detail',form_kwargs={'request': request},queryset=RiskAssessmentDetail.bells_manager.filter(is_deleted=False))
                    risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail',form_kwargs={'request': request})

                    queryset = RiskDocumentationApproval.bells_manager.filter(risk_assessment=risk_assessment).order_by('-id')
                    if not queryset.exists():
                        queryset = RiskDocumentationApproval.objects.none()
                        
                    RiskDocumentationApprovalFormSet = get_formset(
                    RiskAssessment, 
                    RiskDocumentationApproval, 
                    form=RiskDocumentationApprovalForm, 
                    extra=1 if not queryset.exists() else 0 
                        )
                    # RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1 if risk_assessment.documentation.first() is None else 0)
                    # RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1 if risk_assessment.management_approval.first() is None else 0)
                    # RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                    client = Client.bells_manager.get(id=client_id)
                    employee= request.user.employee
                   
                    risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(
                        instance=risk_assessment, 
                        prefix='approval', 
                        queryset=queryset
                    )
                    
                    # Get the queryset with the custom bells_manager, filtering for non-deleted objects
                    moniter_queryset = RiskMoniterControl.bells_manager.filter(risk_assessment=risk_assessment).order_by('-id')

                    # If the queryset is empty, we should return one form in the formset.
                    if not moniter_queryset.exists():
                        moniter_queryset = RiskMoniterControl.objects.none()  # Ensures that the formset can still render.

                    # Create the formset with the queryset and extra logic
                    RiskMoniterControlFormSet = get_formset(
                        RiskAssessment, 
                        RiskMoniterControl, 
                        form=RiskMoniterControlForm, 
                        extra=1 if not moniter_queryset.exists() else 0  
                    )

                    # Instantiate the formset with the given instance and queryset
                    risk_moniter_control_formset = RiskMoniterControlFormSet(
                        instance=risk_assessment, 
                        prefix='monitor', 
                        queryset=moniter_queryset
                    )

                    # risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(instance=risk_assessment,prefix='approval', queryset=RiskDocumentationApproval.bells_manager.order_by('-id'))
                    # risk_moniter_control_formset = RiskMoniterControlFormSet(instance=risk_assessment,  prefix='monitor',queryset=RiskMoniterControl.bells_manager.order_by('-id'))

                    # risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(queryset=RiskDocumentationApproval.objects.none(),  prefix='approval')
                    # risk_moniter_control_formset = RiskMoniterControlFormSet(queryset=RiskMoniterControl.objects.none(),  prefix='monitor')
                    risk_assessment_detail_obj  = RiskAssessmentDetail.bells_manager.filter(risk_assessment=risk_assessment,is_deleted=False)
                    if not risk_assessment_detail_obj:                
                        request.session['risk_assessment_instance_none'] = True
                    else:
                        request.session['risk_assessment_instance_none'] = False



            else:  
                RiskAssessmentDetailFormSet = get_formset(RiskAssessment,RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                client = Client.objects.get(id=client_id)
                employee= request.user.employee
                risk_assessment_form = RiskAssessmentForm(company=company,initial={'client': client, 'prepared_by': employee})
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail', form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(queryset=RiskDocumentationApproval.bells_manager.none(),prefix='approval',)
                risk_moniter_control_formset = RiskMoniterControlFormSet(queryset=RiskMoniterControl.bells_manager.none(), prefix='monitor')
                request.session['risk_assessment_instance_id'] = None
                request.session.pop('edit_document_request', False)

                if request.resolver_match.url_name == 'employee_risk_assessment_add':
                    request.session['is_employee_request'] = True

        risk_assessment_id = request.session['risk_assessment_instance_id']

        show_investigation_for = set()
        all_investigation = has_user_permission(request.user, 'company_admin.authorize_risk_assessment_all')
        team_investigation = has_user_permission(request.user, 'company_admin.authorize_risk_assessment_own_team')
        read_team_clients = has_user_permission(request.user, 'userauth.read_team_clients')
        read_all_clients = has_user_permission(request.user, 'userauth.read_all_clients')

        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=employee.id, company_id=company.id
        )
        
        team_client_ids = set(department_data['clients'].values_list('id', flat=True))

        if read_all_clients:
            show_service_delivery_team = True
        elif read_team_clients and client_id in team_client_ids:
            show_service_delivery_team = True
        else:
            show_service_delivery_team = False
        
        if team_investigation:
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee.id,company_id=company.id)
            employee_data = manager_data['employees']
            client_data = manager_data['clients'].values_list('id',flat=True)    
            show_investigation_for.update(client_data)
        elif all_investigation:
            client_data = Client.bells_manager.values_list('id',flat=True)
            show_investigation_for.update(client_data)
        else:
            client_data = Client.bells_manager.none()
            show_investigation_for.update(client_data)
        
        return render(
                request,
                self.template_name,
                {
                    'risk_assessment_form': risk_assessment_form,
                    'client_id':client_id,
                    'risk_assessment_detail_formset': risk_assessment_detail_formset,
                    'risk_documentation_approval_formset': risk_documentation_approval_formset,
                    'risk_moniter_control_formset': risk_moniter_control_formset,
                    'risk_assessment_tab':True,
                    'client':client_obj,
                    'risk_assessment_detail_obj':risk_assessment_detail_obj,
                    "risk_assessment_detail_formset_for_modals":risk_assessment_detail_formset_for_modals,
                    "risk_assessment_id":risk_assessment_id,
                    "show_investigation_for":show_investigation_for,
                    'show_service_delivery_team':show_service_delivery_team
                    
                }
            )

    
    def get_company(self, request):
        return request.user.employee.company

    def is_form_empty(self, form):
        for field_name, field in form.fields.items():
            value = form.cleaned_data.get(field_name)
            if value:
                return False
        return True


    def post(self, request,client_id=None, risk_assessment_detail_id=None,risk_assessment_id=None, *args, **kwargs):
        company = self.get_company(request)

        if risk_assessment_id and 'risk_assessment_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, client_id,risk_assessment_id)
    
        if risk_assessment_id and 'risk_assessment_edit' in request.resolver_match.url_name:
            try:
                risk_assessment = RiskAssessment.bells_manager.get(id=risk_assessment_id)

                RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment, RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment, RiskMoniterControl, form=RiskMoniterControlForm, extra=1)

                risk_assessment_form = RiskAssessmentForm(request.POST,instance=risk_assessment,company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST,instance=risk_assessment,  prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(request.POST,instance=risk_assessment,  prefix='approval')
                risk_moniter_control_formset = RiskMoniterControlFormSet(request.POST,instance=risk_assessment,  prefix='monitor')

            except:
                return HttpResponseRedirect(reverse('company:risk_assessment_list'))
         
        elif 'risk_assessment_details_edit' in request.resolver_match.url_name:
            request_data = request.POST
            risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
            risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
            RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
            risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST, instance=risk_assessment_instance, prefix='edit_detail', form_kwargs={'request': request})
            form_count = int(request_data.get('form_count')) - 1
            detail_form = risk_assessment_detail_formset.forms[form_count]
            if detail_form.is_valid():
                detail_form.save()
        
            edit_document_request = request.session.get('edit_document_request', False) 
            risk_documentation_approval = RiskDocumentationApproval.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
            risk_management_approval = RiskMoniterControl.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
            
            
            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            post_page_request = request.session.get('post_page_request')
            if post_page_request:
                edit_document_request = True
            if risk_documentation_approval and not edit_document_request == True:
                
                RiskDocumentationApproval.bells_manager.create(
                    risk_assessment=risk_assessment_instance,
                    completed_by=full_name
                )
                RiskMoniterControl.bells_manager.create(
                    risk_assessment = risk_assessment_instance
                )                
                edit_document_request = request.session['edit_document_request'] = True

            
            is_employee_request = request.session.get('is_employee_request')
            if is_employee_request == True:
                redirect_url = reverse('company:employee_risk_assessment_add', kwargs={'client_id': client_id})
            else:
                post_page_request = request.session.get('post_page_request')
                if post_page_request == True:
                    redirect_url = reverse('company:risk_assessment_add', kwargs={'client_id': client_id})
                else:
                    redirect_url = reverse(
                        'company:risk_assessment_edit', 
                        kwargs={
                            'client_id': client_id, 
                            'risk_assessment_id': risk_assessment_instance_id
                        }
                    )

            query_string = 'risk_assessment=True'
            redirect_url_with_tab = f"{redirect_url}?{query_string}"
            return redirect(redirect_url_with_tab)

        else:

                RiskAssessmentDetailFormSet = get_formset(RiskAssessment,RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                client = Client.bells_manager.get(id=client_id)
                employee= request.user.employee
                risk_assessment_form = RiskAssessmentForm(request.POST,{'client': client, 'prepared_by': employee},company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST, queryset=RiskAssessmentDetail.bells_manager.none(), prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(request.POST, queryset=RiskDocumentationApproval.bells_manager.none(),  prefix='approval')
                risk_moniter_control_formset = RiskMoniterControlFormSet(request.POST, queryset=RiskMoniterControl.bells_manager.none(),  prefix='monitor')

        
        
        if 'risk_assessment_details_add' in request.resolver_match.url_name:
            
            if (risk_assessment_form.is_valid() and risk_assessment_detail_formset.is_valid()):
                risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                if risk_assessment_instance_id:
                    risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance.assessment_date=assessment_date
                else:
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance = risk_assessment_form.save(commit=False)
                    risk_assessment_instance.assessment_date=assessment_date
                risk_assessment_instance.save()
                    
                for form in risk_assessment_detail_formset:
                    risk_assessment_detail_instance = form.save(commit=False)
                    risk_assessment_detail_instance.risk_assessment = risk_assessment_instance
                    risk_assessment_detail_instance.save()
                    request.session['risk_assessment_instance_id'] = risk_assessment_instance.id
                    request.session['risk_assessment_detail_instance_id'] = risk_assessment_detail_instance.id
                   
                   
                risk_documentation_approval = RiskDocumentationApproval.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
                full_name = f"{request.user.first_name} {request.user.last_name}".strip()

                if risk_documentation_approval:
                    risk_documentation_approval.completed_by =full_name
                    risk_documentation_approval.save()
                else:
                    RiskDocumentationApproval.bells_manager.create(
                        risk_assessment=risk_assessment_instance,
                        completed_by=full_name
                    )
                risk_management_approval = RiskMoniterControl.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()

                if risk_management_approval:
                    risk_management_approval.risk_assessment =risk_assessment_instance
                    risk_management_approval.save()
                else:
                    RiskMoniterControl.bells_manager.create(
                        risk_assessment=risk_assessment_instance,
                    )
            
            post_page_request = request.session['post_page_request'] = True        
            is_employee_request = request.session.get('is_employee_request')
            if is_employee_request == True:
                redirect_url = reverse('company:employee_risk_assessment_add', kwargs={'client_id': client_id})
            else:
                redirect_url = reverse('company:risk_assessment_add', kwargs={'client_id': client_id})

            query_string = 'risk_assessment=True'
            redirect_url_with_tab = f"{redirect_url}?{query_string}"
            return redirect(redirect_url_with_tab)
        
        
        elif 'risk_assessment_add' in request.resolver_match.url_name or 'risk_assessment_edit' in request.resolver_match.url_name:
            is_employee_request = request.session.get('is_employee_request')
            if (risk_assessment_form.is_valid() and risk_documentation_approval_formset.is_valid() and risk_moniter_control_formset.is_valid() and not is_employee_request):
               
                risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                risk_assessment_instance = RiskAssessment.bells_manager.filter(id=risk_assessment_instance_id).first()
                cleaned_data = risk_assessment_form.cleaned_data
                assessment_date = cleaned_data['assessment_date']
                risk_assessment_instance.assessment_date=assessment_date
                risk_assessment_instance.save()
                    
                risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
               
                
                for form in risk_documentation_approval_formset:
                    if not self.is_form_empty(form):
                        instance_id = form.cleaned_data.get('id')
                        
                        if instance_id:
                            risk_documentation_approval_instance = RiskDocumentationApproval.bells_manager.get(id=instance_id.id)
                            
                            risk_documentation_approval_instance.completed_by = form.cleaned_data.get('completed_by')
                            risk_documentation_approval_instance.authorized_by = form.cleaned_data.get('authorized_by')
                            risk_documentation_approval_instance.date = form.cleaned_data.get('date')
                            risk_documentation_approval_instance.save()
                        else:
                            form_instance = form.save(commit=False)
                            form_instance.risk_assessment = risk_assessment_instance
                            form_instance.save()

                
                for form in risk_moniter_control_formset:
                    if not self.is_form_empty(form):
                        instance_id = form.cleaned_data.get('id')

                        if instance_id:
                            risk_monitor_control_instance = RiskMoniterControl.bells_manager.get(id=instance_id.id)

                            risk_monitor_control_instance.reviewed_date = form.cleaned_data.get('reviewed_date')
                            risk_monitor_control_instance.reviewed_by = form.cleaned_data.get('reviewed_by')
                            risk_monitor_control_instance.authorized_by = form.cleaned_data.get('authorized_by')
                            risk_monitor_control_instance.save()
                        else:
                            form_instance = form.save(commit=False)
                            form_instance.risk_assessment = risk_assessment_instance
                            form_instance.save()

        
                # for form in risk_moniter_control_formset:
                #     risk_moniter_control_instance = form.save(commit=False)
                #     risk_moniter_control_instance.risk_assessment = risk_assessment_instance
                #     risk_moniter_control_instance.save()
                if risk_assessment_id:
                    messages.success(request, 'Risk assessment updated successfully.')
                else:
                    messages.success(request, 'Risk assessment created successfully.')
                
        
        
                redirect_url = reverse('company:client_profile_risk_assessment', kwargs={'client_id': client_id})
                
                redirect_url_with_tab = f"{redirect_url}"
                return redirect(redirect_url_with_tab)
            
            else:
                if risk_assessment_form.is_valid():
                    risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                    risk_assessment_instance = RiskAssessment.bells_manager.filter(id=risk_assessment_instance_id).first()
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance.assessment_date=assessment_date
                    risk_assessment_instance.save()
                    messages.success(request, 'Risk assessment created successfully.')
                    is_employee_request = request.session.get('is_employee_request')
                    if is_employee_request == True:
                        redirect_url = reverse('employee:client_risk_assessment_list_view', kwargs={'client_id': client_id})
                    else:
                        redirect_url = reverse('company:client_profile_risk_assessment', kwargs={'client_id': client_id})

                        
                    query_string = 'risk_assessment=True'
                    redirect_url_with_tab = f"{redirect_url}?{query_string}"
                    return redirect(redirect_url_with_tab)
        else:
                return render(
                    request,
                    self.template_name,
                    {
                        'risk_assessment_form': risk_assessment_form,
                        'risk_assessment_detail_formset': risk_assessment_detail_formset,
                        'risk_documentation_approval_formset': risk_documentation_approval_formset,
                        'risk_moniter_control_formset': risk_moniter_control_formset,
                        'client_id':client_id
                    }
                )

    def handle_delete(self, request,client_id=None, risk_assessment_id=None,):
        risk_assessment = get_object_or_404(RiskAssessment, pk=risk_assessment_id)
        if risk_assessment:
            risk_assessment.is_deleted = True
            risk_assessment.save()
            messages.success(request, 'Risk assessment deleted successfully!')
        redirect_url = reverse('company:client_profile_risk_assessment', kwargs={'client_id': client_id})
        redirect_url_with_tab = f"{redirect_url}"
        return redirect(redirect_url_with_tab)
    
    



def DeleteRiskAssessmentDetail(request, client_id=None, risk_assessment_detail_id=None):
    risk_assessment_detail = get_object_or_404(RiskAssessmentDetail, pk=risk_assessment_detail_id)
    risk_assessment_obj=risk_assessment_detail.risk_assessment
    if risk_assessment_detail:
        risk_assessment_detail.is_deleted = True
        risk_assessment_detail.save()
        
        
        document_approval_obj = RiskDocumentationApproval.bells_manager.filter(risk_assessment=risk_assessment_obj).first()
        if document_approval_obj:
            document_approval_obj.is_deleted = True
            document_approval_obj.save()
        management_approval_obj = RiskMoniterControl.bells_manager.filter(risk_assessment=risk_assessment_obj).first()
        if management_approval_obj:
            management_approval_obj.is_deleted = True
            management_approval_obj.save()
    return JsonResponse({'message': 'Deleted successfully'})


def RiskAssessmentDelete(request):
    risk_assessment_id = request.GET.get('risk_assessment_id')
    if risk_assessment_id:
        risk_assessment_obj = get_object_or_404(RiskAssessment, pk=risk_assessment_id)
        active_details = RiskAssessmentDetail.bells_manager.filter(
            risk_assessment=risk_assessment_obj
        )

        if not active_details.exists():
            risk_assessment_obj.is_deleted = True
            risk_assessment_obj.save()
            return JsonResponse({'status': 'success', 'message': 'Risk assessment successfully deleted.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Cannot delete risk assessment. Active details exist.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Risk assessment ID is missing.'})


@method_decorator(login_required, name='dispatch')
class CommentOperationView(View):
    def post(self, request):
        if request.resolver_match.url_name == 'admin_mandatory_incident_comment':
              comment_data = {
                'employee': request.user.employee,
                'incident': request.POST.get('incident_id'), 
                'report_type': 'Mandatory Incident',
                'content': request.POST.get('content')
            }
        else:
            comment_data = {
                    'employee': request.user.employee,
                    'incident': request.POST.get('incident_id'), 
                    'report_type': 'Incident',
                    'content': request.POST.get('content')
                }
        form = IncidentCommentForm(comment_data)
        if form.is_valid():
            comment=form.save()
            if comment.content:
                saved_comment_data = {
                    'employee': request.user.first_name,
                    'content': comment.content,
                    'date': comment.created_at.strftime("%B %d, %Y")
                }
                return JsonResponse({'comment': saved_comment_data})
            else:
                return JsonResponse({'comment': 'Content is None'}, status=400)

        else:
            return JsonResponse({'errors': form.errors}, status=400)

@method_decorator(login_required, name='dispatch')
class QuestionOperationView(View):
    def post(self, request):
        employee = request.user.employee
        incident_id = request.POST.get('incident_id')

        question_data = {
            'employee': employee,
            'incident': incident_id,
            'report_type': 'Incident',
            'cause_of_incident': request.POST.get('cause_of_incident'),
            'prevention_of_incident': request.POST.get('prevention_of_incident')
        }

        comment_instance = Comment.objects.filter(incident=incident_id).first()

        if comment_instance:
            form = IncidentQuestionForm(question_data, instance=comment_instance)
        else:
            form = IncidentQuestionForm(question_data)

        if form.is_valid():
            form.save()
            messages.success(request,'Remarks updated sucessfully')
            redirect_url = reverse('company:admin_incident_edit', kwargs={'incident_id': incident_id})
            return HttpResponseRedirect(redirect_url)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error} in remarks.")

            redirect_url = reverse('company:admin_incident_edit', kwargs={'incident_id': incident_id})
            return HttpResponseRedirect(redirect_url)

severity_description_map = {
    'Harmful to self': {
        'L1': 'No first aid/treatment required',
        'L2': 'Minor injury, requiring some first aid (e.g. creams, band aids etc.)',
        'L3': 'Resulting in no obvious serious injury but may cause long lasting injury. E.g. head banging, serious anal picking etc.',
        'L4': 'Treatment by Dr or ambulance required'
    },
    'Harmful to property': {
        'L1': 'Damage to property less than $50',
        'L2': 'Damage $50-$100',
        'L3': 'Damage > $150'
    },
    'Harmful to others': {
        'L1': 'Shouts/swears up to 20 mins / verbal or physical threat',
        'L2': 'Hit/kick/pushing - not causing bruising or other injury / shouts more than 20 mins',
        'L3': 'Hit/kick/pushing - causing minor first aid',
        'L4': 'Treatment by Dr of ambulance required for either client or staff / staff refuse to work with client or are removed from shift cycle'
    }
}

def get_severity_description(row):
    severity_level = row['incident_severity_level']
    specific_level = row['specific_severity_level']
    return severity_description_map.get(severity_level, {}).get(specific_level, specific_level)


@login_required
def downloadIncidentReport(request):
    company = request.user.employee.company
    file_type = request.POST.get('file_type')
    incident_ids_str = request.POST.get('incident_ids')
    incident_ids = [int(id) for id in incident_ids_str.split(',')]

    if request.resolver_match.url_name == 'download_incident_report':
        if file_type == 'all-csv' or file_type == 'all-excel':
            #filters for all-csv and all-excel downloads
            client_id = request.POST.get('id_client')
            employee_id = request.POST.get('id_employee') 
            start_date = request.POST.get('start_date') 
            end_date = request.POST.get('end_date') 
        
            filters = Q(company=company)
            if client_id:
                filters &= Q(client_id=client_id)
            if employee_id:
                filters &= Q(employee_id=employee_id)
            if start_date and end_date:
                filters &= Q(incident_date_time__date__gte=start_date, incident_date_time__date__lte=end_date)
            elif start_date:
                filters &= Q(incident_date_time__date=start_date)
            elif end_date:
                filters &= Q(incident_date_time__date=end_date)
                
            if has_user_permission(request.user, 'company_admin.export_incident_report_own_team'):
                manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=request.user.employee.id, company_id=company.id)
                client_data = manager_data.get('clients', Client.bells_manager.none())
                employee_data = manager_data.get('employees', Employee.bells_manager.none())
            else:
                client_data = Client.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
                employee_data = Employee.bells_manager.filter(company = company).order_by(Lower('person__first_name'))

            incidents = Incident.bells_manager.filter(filters,client__in=client_data,employee__in = employee_data,report_type="Incident")
            print(incidents.query)
        else:    
            incidents = Incident.bells_manager.filter(id__in=incident_ids, company=company, report_type="Incident")
    
    elif request.resolver_match.url_name == 'download_mandatory_incident_report':
        incidents = Incident.bells_manager.filter(id__in=incident_ids, company=company, report_type="Mandatory Incident")
    else:
        incidents = Incident.bells_manager.none()

    incidents_values = incidents.values(
        'id',
        'report_code',
        'employee__person__first_name',
        'employee__person__last_name', 
        'employee__person__phone_number',
        'employee__person__email',
        'client__person__first_name',
        'client__person__last_name',
        'incident_location',
        'incident_date_time',
        'is_injured',
        'injured_person',
        'action_taken',
        'any_witness',
        'witness_name',
        'witness_phone_number',
        'witness_email',
        'pre_incident_details',
        'status',
        'inbetween_incident_details',
        'post_incident_details',
        'incident_severity_level',
        'specific_severity_level',
        'incident_category',
        'define_other_category',
        'incident_classification',
    )

    df = pd.DataFrame(list(incidents_values))
    
    if not df.empty :

        comments = Comment.objects.filter(
        incident_id__in=incident_ids
        ).values(
            'incident_id',
            'content',
            'cause_of_incident',
            'prevention_of_incident',
            'employee__person__first_name',
            'employee__person__last_name',
            'created_at'
        ).order_by('incident_id', '-created_at')

        incident_comments = {}
        for incident_id in incident_ids:
            incident_comments[incident_id] = {
                'comments': [],
                'causes': [],
                'preventions': []
            }

        for comment in comments:
            incident_id = comment['incident_id']
            commenter_name = f"{comment['employee__person__first_name']} {comment['employee__person__last_name']}"
            created_at = comment['created_at'].strftime('%d-%m-%Y %I:%M %p')  
            
            if comment['content']:
                formatted_comment = f"[{created_at}] : {commenter_name}: {comment['content']}"
                incident_comments[incident_id]['comments'].append(formatted_comment)
            
            if comment['cause_of_incident']:
                formatted_cause = f"[{created_at}] : {commenter_name}: {comment['cause_of_incident']}"
                incident_comments[incident_id]['causes'].append(formatted_cause)
            
            if comment['prevention_of_incident']:
                formatted_prevention = f"[{created_at}] : {commenter_name} : {comment['prevention_of_incident']}"
                incident_comments[incident_id]['preventions'].append(formatted_prevention)


        df['all_comments'] = df['id'].apply(
        lambda x: '\n\n'.join(incident_comments.get(x, {}).get('comments', [])) or '-'
        )
        df['all_causes'] = df['id'].apply(
            lambda x: '\n\n'.join(incident_comments.get(x, {}).get('causes', [])) or '-'
        )
        df['all_preventions'] = df['id'].apply(
            lambda x: '\n\n'.join(incident_comments.get(x, {}).get('preventions', [])) or '-'
        )

        df['employee_name'] = df['employee__person__first_name'] + ' ' + df['employee__person__last_name']

        df = df.drop(columns=['employee__person__first_name', 'employee__person__last_name'])

        df['client_name'] = df['client__person__first_name'] + ' ' + df['client__person__last_name']

        df = df.drop(columns=['client__person__first_name', 'client__person__last_name'])

        df['incident_date_time'] = df['incident_date_time'].dt.tz_convert(settings.TIME_ZONE)
        df['incident_date_time_ampm'] = df['incident_date_time'].dt.strftime('%I:%M %p')

        df['incident_date'] = df['incident_date_time'].apply(lambda x: x.strftime('%d-%m-%Y') if x else '-')
        df['incident_time'] = df['incident_date_time_ampm']

        df = df.fillna('-')
        df['is_injured'] = df['is_injured'].map({True: 'Yes', False: 'No', '-': '-'})
        df['any_witness'] = df['any_witness'].map({True: 'Yes', False: 'No', '-': '-'})
        # df['is_mandatory_aware'] = df['is_mandatory_aware'].map({True: 'Yes', False: 'No', '-': '-'})
        df['specific_severity_level'] = df.apply(get_severity_description, axis=1)

        df = df[[
            'report_code', 'employee_name', 'employee__person__phone_number', 'employee__person__email', 
            'client_name', 'incident_location', 'incident_date', 'incident_time','is_injured', 
            'injured_person', 'action_taken', 'any_witness', 'witness_name', 'witness_phone_number', 
            'witness_email', 'pre_incident_details','inbetween_incident_details','post_incident_details','incident_severity_level',
            'specific_severity_level','incident_category','define_other_category','incident_classification', 'status','all_causes', 'all_preventions', 'all_comments',
        ]]

        df.insert(0, 'S.no', range(1, len(df) + 1))

        df.columns = [
            'S.no', 'Report number', 'Employee name', 'Employee phone number', 'Employee email', 'Client name',
            'Place of incident occurred', 'Date of incident', 'Time of incident', 'Is anyone injured in the incident?',
            'Name of the injured person',
            'What actions were taken after the injury was noticed?', 'Is there a witness?', 'Witness name', 'Witness phone number',
            'Witness email', 'What happened before the incident and what actions did you take?',
            'What happened during the incident and what actions did you take?',
            'What happened after the incident and what actions did you take?',
            'According to your observation- please define incident severity level',
            'Select severity',
            'Incident category','Define the category','Incident classification','Status of the incident','What is the root cause of this incident?', 
            'What actions are in place to prevent this incident occurring in future?', 'Comments'

        ]
    
    else:
        df = pd.DataFrame(columns=[
            'S.no', 'Report number', 'Employee name', 'Employee phone number', 'Employee email', 'Client name',
            'Place of incident occurred', 'Date of incident', 'Time of incident', 'Is anyone injured in the incident?',
            'Name of the injured person', 'What actions were taken after the injury was noticed?', 
            'Is there a witness?', 'Witness name', 'Witness phone number', 'Witness email', 
            'What happened before the incident and what actions did you take?', 
            'What happened during the incident and what actions did you take?', 
            'What happened after the incident and what actions did you take?', 
            'According to your observation- please define incident severity level', 'Select severity', 
            'Incident category', 'Define the category', 'Incident classification', 'Status of the incident',
            'What is the root cause of this incident?', 'What actions are in place to prevent this incident occurring in future?', 
            'Comments'
        ])


    if file_type == 'csv' or file_type == 'all-csv':
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
        filename = f'incidents_report_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-File-Type'] = file_type
        
        df.to_csv(response, index=False)
        return response

    elif file_type == 'excel' or file_type == 'all-excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        df.to_excel(writer, index=False, sheet_name='Incidents')

        workbook = writer.book
        worksheet = writer.sheets['Incidents']

        cell_format = workbook.add_format({
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter'
        })

        for idx, col in enumerate(df.columns):
            max_len = max((df[col].astype(str).str.len().max(), len(col))) + 2
            worksheet.set_column(idx, idx, max_len, cell_format)

        for row in range(len(df)):
            max_content_length = max(len(str(df[col].iloc[row])) for col in df.columns)
            worksheet.set_row(row + 1, max_content_length // 2 + 10)  # Adjust row height

        writer.close()
        output.seek(0)

        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
        filename = f'incidents_report_{timestamp}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-File-Type'] = file_type
        return response


@login_required
def downloadShiftReport(request):
    company = request.user.employee.company
    file_type = request.POST.get('file_type')
    shift_ids_str = request.POST.get('shift_ids')
    
    shift_ids = [int(id) for id in shift_ids_str.split(',')]
    if file_type == 'all-csv' or file_type == 'all-excel':
        #filters for all-csv and all-excel downloads
        client_id = request.POST.get('id_client')
        employee_id = request.POST.get('id_employee') 
        start_date = request.POST.get('start_date') 
        end_date = request.POST.get('end_date') 
    
        filters = Q(company=company)
        # Add conditions only if filters are provided
        if client_id:
                filters &= Q(client_id=client_id)
        if employee_id:
            filters &= Q(employee_id=employee_id)
        if start_date and end_date:
            filters &= Q(start_date_time__date__gte=start_date, end_date_time__date__lte=end_date)
        elif start_date:
            filters &= Q(start_date_time__date=start_date)
        elif end_date:
            filters &= Q(end_date_time__date=end_date)
            
        client_data = Client.bells_manager.filter(company = company).order_by(Lower('person__first_name'))
        if has_user_permission(request.user, 'company_admin.export_progress_notes_own_team'):
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            employee_data = manager_data['employees']
            client_data = manager_data['clients']   
            shifts = DailyShiftCaseNote.bells_manager.filter(filters, client__in = client_data, employee__in = employee_data, shift__status="Completed")
        else:
            shifts = DailyShiftCaseNote.bells_manager.filter(filters, client__in = client_data, shift__status="Completed")
    else:
        shifts = DailyShiftCaseNote.bells_manager.filter(id__in=shift_ids, company=company)

    local_timezone = pytz.timezone(settings.TIME_ZONE)

    shifts_values = shifts.values(
        'employee__person__first_name',
        'employee__person__last_name',
        'client__person__first_name',
        'client__person__last_name',
        'start_date_time',
        'end_date_time',
        'vehicle_used',
        'distance_traveled',
        'description'
    )

    df = pd.DataFrame(list(shifts_values))
    if not df.empty :
        df = df.fillna('-')
        df['employee_name'] = df['employee__person__first_name'] + ' ' + df['employee__person__last_name']

        df = df.drop(columns=['employee__person__first_name', 'employee__person__last_name'])

        df['client_name'] = df['client__person__first_name'] + ' ' + df['client__person__last_name']

        df = df.drop(columns=['client__person__first_name', 'client__person__last_name'])
    
        # df['start_date_time'] = df['start_date_time'].dt.tz_convert(settings.TIME_ZONE)
        # df['end_date_time'] = df['end_date_time'].dt.tz_convert(settings.TIME_ZONE)
        # Convert to datetime with UTC awareness
        df['start_date_time'] = pd.to_datetime(df['start_date_time'], errors='coerce', utc=True)
        df['end_date_time'] = pd.to_datetime(df['end_date_time'], errors='coerce', utc=True)

        # Convert to local timezone only where values are valid (not NaT)
        df.loc[df['start_date_time'].notna(), 'start_date_time'] = df.loc[df['start_date_time'].notna(), 'start_date_time'].dt.tz_convert(settings.TIME_ZONE)
        df.loc[df['end_date_time'].notna(), 'end_date_time'] = df.loc[df['end_date_time'].notna(), 'end_date_time'].dt.tz_convert(settings.TIME_ZONE)

        df['start_date_time'] = df['start_date_time'].dt.strftime('%Y-%m-%d %I:%M %p')
        df['end_date_time'] = df['end_date_time'].dt.strftime('%Y-%m-%d %I:%M %p')
        df['vehicle_used'] = df['vehicle_used'].map({True: 'Yes', False: 'No', None: '-'})



        df['distance_traveled'] = df['distance_traveled'].apply(lambda x: str(x) if x else '-')
        df['description'] = df['description'].apply(lambda x: x if x else '-')

        df = df.fillna('-')
        df = df[[
            'employee_name',
            'client_name',
            'start_date_time',
            'end_date_time',
            'vehicle_used',
            'distance_traveled',
            'description'
        ]]
        
        df.insert(0, 'S.no', range(1, len(df) + 1))
        
        df = df.rename(columns={
            'S.no': 'S.no',
            'employee_name': 'Employee name',
            'client_name': 'Client name',
            'start_date_time': 'Start date and Time',
            'end_date_time': 'End date and time',
            'vehicle_used': 'Whether a vehicle was used Used',
            'distance_traveled': 'Distance traveled',
            'description': 'Description of the notes'
        })
    
    else :
        df = pd.DataFrame(columns=[
            'S.no', 'Employee name', 'Client name', 'Start date and Time', 
            'End date and time', 'Whether a vehicle was used', 'Distance traveled', 'Description of the notes'
        ])
        

    if file_type == 'csv' or file_type == 'all-csv':
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
        filename = f'shifts_report_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-File-Type'] = file_type
        df.to_csv(response, index=False, date_format='%Y-%m-%d %I:%M %p')

        # df.to_csv(response, index=False)
        return response

    elif file_type == 'excel' or file_type == 'all-excel':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        df.to_excel(writer, index=False, sheet_name='Shifts')

        workbook = writer.book
        worksheet = writer.sheets['Shifts']

        cell_format = workbook.add_format({
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter'
        })

        for idx, col in enumerate(df.columns):
            max_len = max((df[col].astype(str).str.len().max(), len(col))) + 2
            worksheet.set_column(idx, idx, max_len, cell_format)

        for row in range(len(df)):
            max_content_length = max(len(str(df[col].iloc[row])) for col in df.columns)
            worksheet.set_row(row + 1, max_content_length // 2 + 10)  # Adjust row height

        writer.close()
        output.seek(0)

        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
        filename = f'shifts_report_{timestamp}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-File-Type'] = file_type
        return response
    
    
    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions([
                                     'userauth.update_all_employees',
                                     'userauth.update_team_employees',
                                     'userauth.update_own_employees',
                                     'userauth.read_own_employees',
                                    'userauth.employee_update_none'

                                     ]), name='dispatch')     
class CompanyEmployeeProfileView(View):
    template_name = "company_admin/employee/employee-profile.html"

    def get(self, request,employee_id=None, *args, **kwargs):
        company = request.user.employee.company
        user = request.user
        can_update_all = has_user_permission(user, 'userauth.update_all_employees')
        can_update_team = has_user_permission(user, 'userauth.update_team_employees')
        can_update_own = has_user_permission(user, 'userauth.update_own_employees')
        employee_list = Employee.bells_manager.filter(company=company).order_by('person__first_name')
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()
     
        client_assignments = ClientAssignment.bells_manager.filter(employee=employee_id).order_by('clients__person__first_name')

        clients = Client.bells_manager.filter(
            client_assignments_detail__client_assignment__in=client_assignments,
            client_assignments_detail__is_deleted=False
        ).order_by('person__first_name').distinct()
        
         
        show_eye_button_for = set()

        if  can_update_all:
            show_eye_button_for = set(employee_list.values_list('id', flat=True))
            logger.info("User has both read_all and update_all permissions. Eye button will be shown for all employees.")
        elif can_update_team:
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company.id)
            show_eye_button_for = set(department_data.get('employees', []).values_list('id', flat=True))
            logger.info(f"User has read_all but update_team. Eye button will be shown for team employees only: {len(show_eye_button_for)} employees.")
        elif can_update_own and employee_id == request.user.employee.id:
            employees = Employee.bells_manager.filter(id=request.user.employee.id)
            show_eye_button_for = set(employees.values_list('id', flat=True))
            logger.info("User has read_team and update_own. No eye button will be shown.")
        
        # else:
        #     employees = Employee.bells_manager.filter(company=company,id=user.employee.id).order_by('person__first_name')
        #     show_eye_button_for = set(employees.values_list('id', flat=True))

        context = {
            'profile':profile_details,
            'employee_id':employee_id,
            'employees':employee_list,
            'clients': clients,
            'show_eye_button_for':show_eye_button_for

        }
        return render(request, self.template_name,context)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.update_all_employees',
                                     'userauth.update_team_employees',
                                     'userauth.update_own_employees',
                                     'userauth.employee_update_none',
                                     ]), name='dispatch')   
class CompanyEmployeeProfileOperation(View):
    template_name = "company_admin/employee/edit-employee-profile.html"

    def get(self, request, employee_id=None, *args, **kwargs):
        context = {}
           
        personform = CompanyEmployeePersonForm(request=request)
        company = self.get_company(request)
        if employee_id and 'manager_employee_profile_edit' in request.resolver_match.url_name:
            try:
                employee = Employee.bells_manager.filter(pk=employee_id).first()
                personform = CompanyEmployeePersonForm(instance=employee.person, request=request)
                employee_formset = CompanyEmployeeProfileFormset(instance=employee.person, request=request, prefix="employee_f",initial=[{'company': company,'role':employee.role,'created_by':employee.created_by}])

            except Exception as e:
                print(f'Error:{e}')
                redirect_url = reverse('company:employee_profile_view', kwargs={'employee_id': employee_id})            
                redirect_url_with_tab = f"{redirect_url}"
                return redirect(redirect_url_with_tab)
        else:
            employee_formset = CompanyEmployeeProfileFormset(prefix="employee_f", initial=[{'company': company}])
            
        context = {
            'personform': personform,
            'employee_formset': employee_formset,
            'employee_id': employee_id,
        }

        return render(request, self.template_name, context)

    def get_company(self, request):
        return request.user.employee.company
    
    def post(self, request, employee_id=None, *args, **kwargs):
        existing_template = None
        existing_departments = None
        
        if employee_id and 'manager_employee_profile_edit' in request.resolver_match.url_name:
            try:
                employee = Employee.bells_manager.get(pk=employee_id)
               
                personform = CompanyEmployeePersonForm(request.POST,request.FILES, request=request,instance=employee.person)
                employee_formset = CompanyEmployeeProfileFormset(request.POST ,request=request,instance=employee.person, prefix="employee_f", initial=[{'company': self.get_company(request),'role':employee.role}])

            except:
                redirect_url = reverse('company:manager_employee_profile_edit', kwargs={'employee_id': employee_id})            
                redirect_url_with_tab = f"{redirect_url}"
                return redirect(redirect_url_with_tab)
        else:
            redirect_url = reverse('company:manager_employee_profile_edit', kwargs={'employee_id': employee_id})            
            redirect_url_with_tab = f"{redirect_url}"
            return redirect(redirect_url_with_tab)
        
        
        if personform.is_valid() and employee_formset.is_valid():
            try:
                
                person_instance = personform.save()
                employee_formset.instance = person_instance
                template_name = employee_formset.cleaned_data[0]['template']
                group = Group.objects.get(name=template_name)
                post_existing_permissions = list(group.permissions.values_list('codename', flat=True))

                # Get the employee instance correctly
                employee_instance = Employee.bells_manager.filter(id=employee_formset.cleaned_data[0]['id'].id).first()

                if employee_instance:
                    # Update the existing template with new permissions
                    template_instance = Group.objects.get(id=employee_instance.template.id)
                    template_instance.permissions.clear()
                    new_permissions = Permission.objects.filter(codename__in=post_existing_permissions)
                    template_instance.permissions.add(*new_permissions)
                    full_name = auth_user_full_name(request)
                    # Process each form in the formset
                    for form in employee_formset:
                        employee_obj = form.save(commit=False)  
                        employee_obj.template = template_instance 
                        employee_obj.updated_by = full_name
                        employee_obj.save() 
                        

                employee_person_instance = employee.person
                read_team_departments = has_user_permission(employee_person_instance, 'userauth.read_department_own')
                update_team_departments = has_user_permission(employee_person_instance, 'userauth.update_department_own')

                if not read_team_departments or update_team_departments:
                    department_to_remove = set(Department.bells_manager.filter(manager=employee).values_list('id', flat=True))


                # new_departments = set(person_instance.employee.departments.values_list('id', flat=True))
                form_cleaned_data = employee_formset.cleaned_data[0]
                # departments = form_cleaned_data.get('departments')
                # new_departments = [department.id for department in departments]
                # new_departments_set = set(new_departments)

                # departments_to_add = new_departments_set
                # departments_to_remove = existing_departments - new_departments_set
                
                current_template = person_instance.employee.template
                employee_instance = Employee.bells_manager.filter(person=person_instance).first()
                # if existing_template != current_template:
                #     remove_employee_from_department_when_role_changes(employee_instance,departments_to_add,departments_to_remove)
                # else:
                #     employeement_assignment_to_department(employee_instance,departments_to_add,departments_to_remove)
                # if existing_template != current_template:
                if not read_team_departments or update_team_departments:
                    remove_employee_from_department_when_template_changes(employee_instance,department_to_remove)
               

                messages.success(request, 'Profile Updated successfully!')
                redirect_url = reverse('company:employee_profile_view', kwargs={'employee_id': employee_id})            
                redirect_url_with_tab = f"{redirect_url}"
                return redirect(redirect_url_with_tab)
            except Exception as e:
                print(request, f"An error occurred: {e}")
                return render(request, self.template_name, {'personform': personform, 'employee_formset': employee_formset, 'employee_id':employee_id})
        else:
            print("Form is not valid")
            return render(request, self.template_name, {'personform': personform, 'employee_formset': employee_formset,'employee_id':employee_id})
    
    

@method_decorator(login_required, name='dispatch')
class CompanyEmployeeProfileClients(View):
    template_name = "company_admin/employee/employee-profile.html"

    def get(self, request, employee_id=None, *args, **kwargs):
        employee = Employee.bells_manager.filter(pk=employee_id).first()

        company=employee.company
        related_clients = None

        # if request.user.employee.role == 1:
        client_queryset = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
        related_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee_id,company_id=company.id).order_by(Lower('person__first_name'))
        # elif request.user.employee.role == 2:
        #     manager_employee = request.user.employee
        #     manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = manager_employee.id,company_id=company.id)
        #     client_data = manager_data['clients']
        #     client_queryset = ClientEmployeeAssignment.get_clients_by_employee(
        #                         employee_id=employee.id,company_id=company.id
        #                     ).filter(id__in=client_data.values_list('id', flat=True))
        #     related_clients = client_queryset
        new_client_queryset = client_queryset.exclude(id__in=related_clients.values_list('id', flat=True))
        
        context = {
        'employee_id':employee_id,
        'clients': new_client_queryset,
        'related_clients': related_clients,
        'profile':employee
        }
        return render(request, self.template_name,context)


@login_required
def CompanyClientAssignment(request):
    if request.method == 'POST':
        assignment_form = ClientAssignmentForm(request.POST)
        clients = request.POST.getlist('clients')
        employee_id = request.POST.get('employee')
        employee = Employee.bells_manager.filter(id=employee_id).first()
        
        if request.resolver_match.url_name == "company_client_assignment":
            if assignment_form.is_valid():
                client_assignment, created = ClientAssignment.bells_manager.get_or_create(employee=employee)
                
                for client in clients:
                    assignment_detail_form = ClientAssignmentDetailForm({
                        'client': client,
                        'is_deleted': False,
                    })
                    if assignment_detail_form.is_valid():
                        assignment_detail = assignment_detail_form.save(commit=False)
                        assignment_detail.client_assignment = client_assignment
                        assignment_detail.save()

        if request.resolver_match.url_name == "update_company_client_assignment":
            clients = request.POST.getlist('clients')
            unchecked_clients = request.POST.getlist('unchecked_clients')
            client_assignment_obj, _ = ClientAssignment.bells_manager.get_or_create(employee=employee)
            
            existing_clients = client_assignment_obj.client_assignment_details.filter(is_deleted=False)
            existing_client_ids = [str(detail.client_id) for detail in existing_clients]
            
            for detail in existing_clients:
                client_id = str(detail.client_id)
                if client_id in unchecked_clients:
                    detail.is_deleted = True
                    detail.save()
                    unchecked_clients.remove(client_id) 

            for client_id in unchecked_clients:
                if client_id not in existing_client_ids:
                    client_assignment_obj.client_assignment_details.create(
                        client_id=client_id,
                        is_deleted=False
                    )

            for client_id in clients:
                if client_id not in unchecked_clients and client_id not in existing_client_ids:
                    client_assignment_obj.client_assignment_details.create(
                        client_id=client_id,
                        is_deleted=False
                    )

            client_assignment_obj.save()

    return JsonResponse({'success': True})



# @method_decorator(check_permissions(['employee.read_all_documents',
#                                      'employee.read_team_documents',
#                                     'employee.import_all_documents',
#                                     'employee.import_team_documents',
#                                     'employee.import_document_none',
#                                     'employee.delete_all_documents',
#                                     'employee.delete_team_documents',
#                                     'employee.delete_document_none',
#                                     'employee.read_own_documents',
#                                      ]), name='dispatch')
@method_decorator(login_required, name='dispatch')
class CompanyEmployeeDocumentView(View):
    template_name = "company_admin/employee/employee-profile.html"

    def get(self, request, employee_id = None, *args, **kwargs):
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()
        company = request.user.employee.company
        employee_list = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
        IDsAndChecksDocuments_queryset= IDsAndChecksDocuments.bells_manager.filter(employee=employee_id, is_deleted=False).order_by('-created_at')
        QualificationDocuments_query_set = QualificationDocuments.bells_manager.filter(employee=employee_id, is_deleted=False).order_by('-created_at')
        OtherDocuments_query_set=OtherDocuments.bells_manager.filter(employee=employee_id, is_deleted=False).order_by('-created_at')
        context = {}
        show_delete_button_for = set()
        try:
            if has_user_permission(request.user, 'employee.import_team_documents') or has_user_permission(request.user, 'employee.read_team_documents'):
                department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
                if department_data['departments'] and  department_data['clients'] and  department_data['employees']:
                    department_employee_ids = set(employee.id for employee in department_data['employees'])
                    if employee_id in department_employee_ids:
                        has_import_permission = has_user_permission(request.user, 'employee.import_team_documents')
                        has_read_permission = has_user_permission(request.user, 'employee.read_team_documents')

                        context = {
                            'IDsAndChecksDocuments':IDsAndChecksDocuments_queryset,
                            'QualificationDocuments':QualificationDocuments_query_set,
                            'OtherDocuments':OtherDocuments_query_set,
                            'employee_id':employee_id,
                            'profile':profile_details,
                            'employees':employee_list,
                        }
                        context['is_edit'] = has_import_permission or has_import_permission and has_read_permission
                        context['can_approve_document'] = True

                        return render(request, self.template_name,context)
                    else:
                        context['employee_id']=employee_id
                        context['is_edit'] = False
                        return render(request, self.template_name,context)
                else:
                    context['employee_id']=employee_id
                    context['is_edit'] = False
                    context['can_approve_document'] = True

                
            if has_user_permission(request.user, 'employee.delete_team_documents'):
                department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
                if department_data['departments'] and  department_data['clients'] or  department_data['employees']:
                    department_employee_ids = set(employee.id for employee in department_data['employees'])
                    show_delete_button_for = set(department_employee_ids)
                    context['show_delete_button_for'] = show_delete_button_for
            if has_user_permission(request.user, 'employee.delete_all_documents'):
                show_delete_button_for = set(Employee.bells_manager.all().values_list('id',flat=True))
                context['show_delete_button_for'] = show_delete_button_for

            if has_user_permission(request.user, 'employee.delete_own_documents'):
                show_delete_button_for =set(Employee.bells_manager.filter(id=request.user.employee.id).values_list('id',flat=True))
                context['show_delete_button_for'] = show_delete_button_for

            if has_user_permission(request.user, 'employee.import_all_documents') or has_user_permission(request.user, 'employee.read_all_documents'): 
                has_import_permission = has_user_permission(request.user, 'employee.import_all_documents')
                has_read_permission = has_user_permission(request.user, 'employee.read_all_documents')
                        
                context = {
                    'IDsAndChecksDocuments':IDsAndChecksDocuments_queryset,
                    'QualificationDocuments':QualificationDocuments_query_set,
                    'OtherDocuments':OtherDocuments_query_set,
                    'employee_id':employee_id,
                    'profile':profile_details,
                    'employees':employee_list,
                    'show_delete_button_for':show_delete_button_for

                }
                context['is_edit'] = has_import_permission or has_import_permission and has_read_permission
                context['can_approve_document'] = True

            if has_user_permission(request.user, 'employee.read_own_documents') or has_user_permission(request.user, 'employee.read_team_documents') or has_user_permission(request.user, 'userauth.read_own_employees') or has_user_permission(request.user, 'userauth.read_all_employees') or  has_user_permission(request.user, 'userauth.read_team_employees'):
                if employee_id == request.user.employee.id:
                    context = {
                            'IDsAndChecksDocuments':IDsAndChecksDocuments_queryset,
                            'QualificationDocuments':QualificationDocuments_query_set,
                            'OtherDocuments':OtherDocuments_query_set,
                            'employee_id':employee_id,
                            'profile':profile_details,
                            'employees':employee_list,
                        }
                    context['is_edit'] = has_user_permission(request.user, 'employee.import_own_documents')
                    read_own_documents = has_user_permission(request.user, 'employee.read_own_documents')
                    import_own_documents = has_user_permission(request.user, 'employee.import_own_documents')    
                    if import_own_documents or read_own_documents:
                        context['can_approve_document'] = False
                    else:
                        context['can_approve_document'] = True

                context['show_delete_button_for'] = show_delete_button_for
            context['employee_id']=employee_id
            
            has_own_import_permission = has_user_permission(request.user, 'employee.import_own_documents')
            has_import_permission = has_user_permission(request.user, 'employee.import_all_documents')
            has_import_team_permission = has_user_permission(request.user, 'employee.import_team_documents')
            if has_own_import_permission or has_import_permission or has_import_team_permission:
                if employee_id == request.user.employee.id:
                    context['is_edit'] = True
            return render(request, self.template_name,context)
        except Exception as e:
            print('Exception :', e)
            employee_id = employee_id
            return redirect(reverse('company:employee_profile_view', kwargs={'employee_id': employee_id}))
        


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['employee.read_all_documents',
                                     'employee.read_team_documents',
                                     'employee.import_all_documents',
                                     'employee.import_team_documents',
                                    'employee.import_own_documents',
                                     'employee.delete_all_documents',
                                     'employee.delete_team_documents',
                                     ]), name='dispatch')
class CompanyEmployeeProfileDocuments(View):
    template_name = "company_admin/employee/employee-profile.html"

    def get(self, request, employee_id=None,document_id=None, *args, **kwargs):
           
        company = self.get_company(request)
        
        #id and checks
        id_checks_predefined_names = ["AUSTRALIAN DRIVER LICENSE", "WORKING WITH CHILDREN CHECK OR (WWVP IN OTHER STATES)", "NATIONAL POLICE CHECK",
                            "INTERNATIONAL POLICE CHECK", "VEVO CHECK", "TRAVEL PASSPORT", "AUSTRALIAN BIRTH CERTIFICATE", "NDIS WORKER SCREENING CHECK"]

        existing_documents = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id, is_deleted=False)
        id_checks_initial_data = []
        for name in id_checks_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                id_checks_initial_data.append({
                    'id': existing_document.id,
                    'employee':employee_id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status': existing_document.status,

                })
            else:
                id_checks_initial_data.append({
                    'employee': employee_id,
                    'company': company.id,
                    'name': name,
                })

        IDsAndChecksDocumentsFormSet = formset_factory(IDsAndChecksDocumentsForm, extra=0)
        idschecksformset = IDsAndChecksDocumentsFormSet(initial=id_checks_initial_data, prefix='idschecks')
        
        # #qualification documents
        qualification_predefined_names = ["CERTIFICATE IN DISABILITY OR AGED CARE", "NDIS WORKER ORIENTATION MODULE/PROGRAM",
                                      "INFECTION CONTROL TRAINING"]
        
        existing_documents = QualificationDocuments.bells_manager.filter(employee=employee_id, is_deleted=False)
        qualification_initial_data = []
        for name in qualification_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                qualification_initial_data.append({
                    'id': existing_document.id,
                    'employee': employee_id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status': existing_document.status,

                })
            else:
                qualification_initial_data.append({
                    'employee': employee_id,
                    'company': company.id,
                    'name': name,
                })
        qualificationDocumentsFormSet = formset_factory(QualificationDocumentsForm, extra=0)
        qualificationFormSet = qualificationDocumentsFormSet(initial=qualification_initial_data, prefix='qualification')
        
        # #Other documents
        other_predefined_names = ["CAR REGISTRATION", "COMPREHENSIVE CAR INSURANCE",
                                      "MANUAL HANDLING TRAINING","ASSIST CLIENTS WITH MEDICATION","FIRST AID CERTIFICATE"]
        
        existing_documents = OtherDocuments.bells_manager.filter(employee=employee_id, is_deleted=False)
        other_initial_data = []
        for name in other_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                other_initial_data.append({
                    'id': existing_document.id,
                    'employee': employee_id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status': existing_document.status,

                })
            else:
                other_initial_data.append({
                    'employee':employee_id,
                    'company': company.id,
                    'name': name,
                })
                
        OtherDocumentsFormSet = formset_factory(OtherDocumentsForm, extra=0)
        otherFormSet = OtherDocumentsFormSet(initial=other_initial_data, prefix='other')
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()

        return render(request,self.template_name, {
                'idschecksformset': idschecksformset,
                'qualificationFormSet': qualificationFormSet,
                'otherFormSet': otherFormSet,
                'employee_id': employee_id,
                'profile':profile_details
            })
    def get_company(self, request):
        return request.user.employee.company
    
    def post(self, request, employee_id=None, document_id=None, *args, **kwargs):
        if 'company_manager_delete_employee_document' in request.resolver_match.url_name:
            return self.handle_delete(request, employee_id,document_id )
        company = self.get_company(request)
        
        #ids and checks
        id_checks_predefined_names = ["AUSTRALIAN DRIVER LICENSE", "WORKING WITH CHILDREN CHECK OR (WWVP IN OTHER STATES)", "NATIONAL POLICE CHECK",
                            "INTERNATIONAL POLICE CHECK", "VEVO CHECK", "TRAVEL PASSPORT", "AUSTRALIAN BIRTH CERTIFICATE", "NDIS WORKER SCREENING CHECK"]
        IDsAndChecksDocumentsFormSet = formset_factory(IDsAndChecksDocumentsForm, extra=0)
        id_checks_initial_data = [{'employee': employee_id, 'company': company, 'name': name} for name in id_checks_predefined_names[:8]]
    
        idschecksformset = IDsAndChecksDocumentsFormSet(request.POST, request.FILES,initial=id_checks_initial_data, prefix='idschecks')
        
        #qualification 
        qualification_predefined_names = ["CERTIFICATE IN DISABILITY OR AGED CARE", "NDIS WORKER ORIENTATION MODULE/PROGRAM",
                                      "INFECTION CONTROL TRAINING"]
        qualificationDocumentsFormSet = formset_factory(QualificationDocumentsForm, extra=0)
        qualification_initial_data = [{'employee': employee_id, 'company': company, 'name': name} for name in qualification_predefined_names[:3]]        
        qualificationFormSet = qualificationDocumentsFormSet(request.POST, request.FILES, initial=qualification_initial_data, prefix='qualification')
        
        #other 
        other_predefined_names = ["CAR REGISTRATION", "COMPREHENSIVE CAR INSURANCE",
                                      "MANUAL HANDLING TRAINING","ASSIST CLIENTS WITH MEDICATION","FIRST AID CERTIFICATE"]
        OtherDocumentsFormSet = formset_factory(OtherDocumentsForm, extra=0)
        other_initial_data = [{'employee': employee_id, 'company': company, 'name': name} for name in other_predefined_names[:5]]

        otherFormSet = OtherDocumentsFormSet(request.POST, request.FILES,initial=other_initial_data, prefix='other')
        if idschecksformset.is_valid() and qualificationFormSet.is_valid() and otherFormSet.is_valid():

            document_added = False
            
            for form in idschecksformset:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = IDsAndChecksDocuments.bells_manager.filter(name=name,is_deleted = False, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True

            for form in qualificationFormSet:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = QualificationDocuments.bells_manager.filter(name=name, is_deleted = False, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True
            
            for form in otherFormSet:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = OtherDocuments.bells_manager.filter(name=name,is_deleted = False, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True

            if document_added:
                messages.success(request, 'Document added successfully!')
            else:
                messages.info(request, 'No document added.')            
            redirect_url = reverse('company:company_employee_documents', kwargs={'employee_id': employee_id})            
            redirect_url_with_tab = f"{redirect_url}"
            return redirect(redirect_url_with_tab)
        else:
            messages.error(request, 'The file must be a PDF, JPG, PNG, HEIC, or JPEG.')
            redirect_url = reverse('company:company_employee_documents', kwargs={'employee_id': employee_id})            
            redirect_url_with_tab = f"{redirect_url}"
            return redirect(redirect_url_with_tab)
              
    
    def handle_delete(self, request, employee_id,document_id):
        IDsAndChecksDocuments_obj = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        QualificationDocuments_obj = QualificationDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        OtherDocuments_obj=OtherDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        
        if IDsAndChecksDocuments_obj:
            IDsAndChecksDocuments_obj.is_deleted = True
            IDsAndChecksDocuments_obj.save()
            messages.success(request, 'IDandChecks document deleted successfully!')
        
        elif QualificationDocuments_obj:
            QualificationDocuments_obj.is_deleted = True
            QualificationDocuments_obj.save()
            messages.success(request, 'Qualification document deleted successfully!')
        
        elif OtherDocuments_obj:
            OtherDocuments_obj.is_deleted = True
            OtherDocuments_obj.save()
            messages.success(request, 'Other document document deleted successfully!')
        else:
            messages.success(request, 'No document found!')

        
        redirect_url = reverse('company:company_employee_documents', kwargs={'employee_id': employee_id})            
        redirect_url_with_tab = f"{redirect_url}"
        return redirect(redirect_url_with_tab)

    


@login_required
def CompanyEmployeeProfileDocumentDelete(request,employee_id, document_id):
    IDsAndChecksDocuments_obj = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    QualificationDocuments_obj = QualificationDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    OtherDocuments_obj=OtherDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    
    if IDsAndChecksDocuments_obj:
        IDsAndChecksDocuments_obj.is_deleted = True
        IDsAndChecksDocuments_obj.save()
        messages.success(request, 'IDandChecks document deleted successfully!')
    
    elif QualificationDocuments_obj:
        QualificationDocuments_obj.is_deleted = True
        QualificationDocuments_obj.save()
        messages.success(request, 'Qualification document deleted successfully!')
    
    elif OtherDocuments_obj:
        OtherDocuments_obj.is_deleted = True
        OtherDocuments_obj.save()
        messages.success(request, 'Other document deleted successfully!')
    else:
        messages.success(request, 'No document found!')
        
    return JsonResponse({'message': 'Deleted successfully'})


@login_required
def UpdateDocuementStatus(request):
    data = json.loads(request.body)
    document_id = data.get('document_id')
    new_status = data.get('status')
    
    IDsAndChecksDocuments_obj = IDsAndChecksDocuments.bells_manager.filter(id=document_id ).first()
    QualificationDocuments_obj = QualificationDocuments.bells_manager.filter(id=document_id ).first()
    OtherDocuments_obj=OtherDocuments.bells_manager.filter(id=document_id ).first()
    
    if IDsAndChecksDocuments_obj:
        IDsAndChecksDocuments_obj.status = new_status
        IDsAndChecksDocuments_obj.save()
        messages.success(request, 'IDandChecks document status updated successfully!')
    
    elif QualificationDocuments_obj:
        QualificationDocuments_obj.status = new_status
        QualificationDocuments_obj.save()
        messages.success(request, 'Qualification document status updated successfully!')
    
    elif OtherDocuments_obj:
        OtherDocuments_obj.status = new_status
        OtherDocuments_obj.save()
        messages.success(request, 'Other document status updated successfully!')
    else:
        messages.success(request, 'No document found!')
        
    return JsonResponse({'message': 'Status updated successfully'})



@method_decorator(login_required,name='dispatch')
@method_decorator(check_permissions(['userauth.update_department_all',
                                     'userauth.update_department_own',
                                     'userauth.read_department_all',
                                     'userauth.read_department_own',
                                      'userauth.create_department_all'
                                     ]), name='dispatch') 


class DepartmentListView(View):
    template_name = 'company_admin/department/departments-list.html'
    def get(self,request,*args, **kwargs):
        company = request.user.employee.company
        author = request.user.employee
        read_all_department = has_user_permission(request.user, 'userauth.read_department_all')
        read_own_department =  has_user_permission(request.user, 'userauth.read_department_own')
        update_all_department = has_user_permission(request.user, 'userauth.update_department_all')
        update_own_department = has_user_permission(request.user, 'userauth.update_department_own')

        delete_all_department = has_user_permission(request.user, 'userauth.delete_custom_department_all')
        delete_own_department = has_user_permission(request.user, 'userauth.delete_department_own')



        if read_all_department :
             departments  = Department.bells_manager.filter(company=company).order_by(Lower("name"))
        
        elif read_own_department:
            departments = Department.bells_manager.filter(
                    Q(company=company, manager=author) |
                    Q(company=company, author=author, manager=author)
                ).order_by("name")
        else:
            departments=Department.bells_manager.none()
            
        show_update_button_for = set()
        if update_all_department:
            show_update_button_for = set(departments.values_list('id', flat=True))
        elif update_own_department:
            show_update_button_for = set(
                Department.bells_manager.filter(
                    Q(company=company, manager=author) |
                    Q(company=company, author=author, manager=author)
                ).values_list('id', flat=True)
            )
        
        
        show_delete_button_for = set()
        if delete_all_department:
            show_delete_button_for = set(departments.values_list('id', flat=True))
        elif delete_own_department:
            show_delete_button_for = set(
                Department.bells_manager.filter(
                    Q(company=company, manager=author) |
                    Q(company=company, author=author, manager=author)
                ).values_list('id', flat=True)
            )
            
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(departments, items_per_page)
        try:
            departments_obj = paginator.page(page)
        except PageNotAnInteger:
            departments_obj = paginator.page(1)
        except EmptyPage:
            departments_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count

        if total_entries > 0:
            start_entry = ((departments_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
           'departments': departments_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'show_update_button_for':show_update_button_for,
            'show_delete_button_for':show_delete_button_for
        }
        return render(request,self.template_name,context)
    
    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.create_department_all',
                                     'userauth.create_department_team_own',
                                     'userauth.update_department_all',
                                     'userauth.update_department_own',
                                     'userauth.delete_custom_department_all',
                                     'userauth.delete_department_own']), name='dispatch') 
class DepartmentOperationView(View):
    """
    This view handles the operations related to departments 
    """

    template_name = 'company_admin/department/department-operations.html'
    def get(self, request, department_id=None, *args, **kwargs):
        
        """
        This Method is used get request
        """
        context ={}
        company = self.get_company(request)
        department_form = MangerDepartmentForm(company=company, request =request, author = request.user.employee )
        if department_id and 'departments_edit' == request.resolver_match.url_name:
            try:
                permission_codenames = ['read_department_all', 'read_department_own']
                permissions = Permission.objects.filter(codename__in=permission_codenames)

                department_obj = Department.bells_manager.get(pk=department_id)
                department_form = MangerDepartmentForm(instance=department_obj,company=company,request =request, manager =department_obj.manager,  author = department_obj.author)
                employees = Employee.bells_manager.filter(
                    company=company
                ).filter(
                    Q(person__user_permissions__in=permissions) |
                    Q(person__groups__permissions__in=permissions)
                ).distinct().order_by(Lower('person__first_name'))
                # department = get_object_or_404(Department, id=department_id, company=company)
                # selected_employees = Employee.bells_manager.filter(
                #     departments=department
                # ).filter(
                #     Q(person__user_permissions__in=permissions) |
                #     Q(person__groups__permissions__in=permissions)
                # ).values_list('id', flat=True).distinct()

                # assigned_employees = Employee.bells_manager.filter(
                #     departments=department
                # ).filter(
                #     Q(person__user_permissions__in=permissions) |
                #     Q(person__groups__permissions__in=permissions)
                # ).distinct()
            except Exception as e:
                return HttpResponseRedirect(reverse('company:departments_list'))
     
        context = {
            'form': department_form
        }
     
        if department_id:
            context['employees'] = employees
            context['department_id'] = department_id
            # context['selected_employee_ids'] =  list(selected_employees),
            # context['assigned_employees'] = assigned_employees


        return render(request, self.template_name,context)

    
    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, department_id=None, *args, **kwargs):
        company = self.get_company(request)

        if 'department_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, department_id)
        
        if department_id and 'departments_edit' in request.resolver_match.url_name:
            try:
                department_obj = Department.bells_manager.get(pk=department_id)
                department_form = MangerDepartmentForm(request.POST, company=company,manager= department_obj.manager ,request =request,instance=department_obj)
            except:
                return HttpResponseRedirect(reverse('company:departments_list'))
        else:
            department_form = MangerDepartmentForm(request.POST, request=request,company=company)
        
        
        if department_form.is_valid():
            department_instance = department_form.save()

            if 'departments_edit' in request.resolver_match.url_name:
                messages.success(request, 'Team updated successfully!')
            
            if 'departments_edit' in request.resolver_match.url_name:
                return redirect('company:departments_list')
            else:
                dept_id = department_instance.id
                if has_user_permission(request.user, 'userauth.update_clients_to_department') or has_user_permission(request.user, 'userauth.update_own_clients_to_department') :
                    url = f"{reverse('company:department_client_assignment')}?dept_id={dept_id}"
                else:
                    messages.success(request, 'Team added successfully!')
                    url = f"{reverse('company:departments_list')}?dept_id={dept_id}"

                return HttpResponseRedirect(url)

        else:
            print("Form is not valid")
            return render(request, self.template_name, {'form': department_form})
    
    def handle_delete(self, request, department_id):
        department = get_object_or_404(Department, pk=department_id)
        if department:
            department.is_deleted = True
            department.save()
            messages.success(request, 'Team deleted successfully!')

        return HttpResponseRedirect(reverse('company:departments_list'))





@method_decorator(login_required, name='dispatch')
class DepartmentEmployeeAssignmentView(View):
    template_name = 'company_admin/department/department-operations.html'

    def get(self, request, *args, **kwargs):
        dept_id = request.GET.get('dept_id')
        company = request.user.employee.company
        department = Department.bells_manager.filter(id = dept_id,company=company).first()
        employees = None
        if request.user.employee.role == 1:
            employees = Employee.bells_manager.filter(company=company).exclude(role__in=[1, 2]).order_by(Lower('person__first_name'))
        if request.user.employee.role == 2:
            manager = request.user.employee
            employees_id = Department.bells_manager.filter(manager=manager).values_list('employees',flat=True)
            employees = Employee.bells_manager.filter(id__in=employees_id).exclude(role__in=[1, 2]).distinct().order_by(Lower('person__first_name'))

        if department:    
            assigned_employees_to_department_queryset = department.employees.all().order_by(Lower('person__first_name'))
            assigned_employee_ids = department.employees.values_list('id', flat=True)
        else:
            print(f'Department not found for id {dept_id}')
            return redirect('company:departments_list')
       
        
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(assigned_employees_to_department_queryset, items_per_page)
        try:
            assigned_employees_obj = paginator.page(page)
        except PageNotAnInteger:
            assigned_employees_obj = paginator.page(1)
        except EmptyPage:
            assigned_employees_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((assigned_employees_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'employees': employees,
            'dept_id': dept_id,
            'selected_employee_ids': list(assigned_employee_ids),
            'assigned_employees': assigned_employees_obj,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.resolver_match.url_name == 'assign_employees':
            try:
                data = json.loads(request.body)
                selected_employees = data.get('selected_employees', [])
                #not using unselected_employees variable
                unselected_employees = data.get('unselected_employees', [])
                dept_id = data.get('dept_id')

                if dept_id:
                    department = Department.bells_manager.filter(id=dept_id).first()
                    if department:
                        employees_to_assign = Employee.bells_manager.filter(id__in=selected_employees)
                        department.employees.set(employees_to_assign)
                        department.save()
                        for employee in employees_to_assign:
                            employee.departments.add(department)
                        
                        employees_to_unassign = Employee.bells_manager.filter(id__in=unselected_employees)
                        for employee in employees_to_unassign:
                            employee.departments.remove(department)

                        response_data = {
                            "message": "Employees assigned successfully",
                            "selected_employees": selected_employees,
                            "unselected_employees": unselected_employees,
                        }
                        return JsonResponse(response_data, status=200)
                    else:
                        return JsonResponse({"error": "Team ID not provided"}, status=400)

                else:
                    return JsonResponse({"error": "Team ID not provided"}, status=400)

            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON data"}, status=400)

        return JsonResponse({"error": "Invalid request"}, status=400)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_terms_and_conditions_all',
                                     'company_admin.update_terms_and_conditions_all',
                                     'company_admin.view_privacy_policy_all',
                                     'company_admin.update_privacy_policy_all',]), name='dispatch') 
class CompanySettingsDocumentView(View):
    template_name = 'company_admin/documents/documents.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_terms_and_conditions_all',
                                     'company_admin.update_terms_and_conditions_all',
                                     'company_admin.view_privacy_policy_all',
                                     'company_admin.update_privacy_policy_all',
                                     'userauth.create_templates',
                                     'userauth.update_templates',
                                     'userauth.read_templates',]), name='dispatch')   
class CompanySettingsView(View):
    template_name = 'company_admin/settings.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.update_templates',
                                     'userauth.read_templates',
                                     'userauth.create_templates']), name='dispatch') 
class CompanyTemplateListView(View):
    template_name = 'company_admin/template/template-list.html'

    def get(self, request, *args, **kwargs):
        company= request.user.employee.company
        read_templates = has_user_permission(request.user, 'userauth.read_templates')
        url_name = request.resolver_match.url_name
        employee_emails ={}
        if read_templates:
            if url_name == 'users_template_list':
                #users templates
                templates = (
                    CompanyGroup.bells_manager
                    .filter(company=company)
                    .filter(group__name__endswith='user') 
                    .annotate(
                        middle_name=Replace(
                            'group__name',
                            Value(company.company_code + ' - '),
                            Value('')
                        )
                    )
                    .order_by(Lower('middle_name'))
                )
             
                valid_emails = set(Person.objects.values_list("email", flat=True))

                employee_emails = {
                    template.group.id: [
                        email for email in Employee.bells_manager.filter(template=template.group).values_list("person__email", flat=True)
                        if email in valid_emails
                    ]
                    for template in templates
                }
                employee_emails = {k: v for k, v in employee_emails.items() if v}
                templates = [template for template in templates if template.group.id in employee_emails]
                user_template_request = True
            if url_name == 'template_list':
          
                templates = (
                CompanyGroup.bells_manager
                .filter(company=company)
                .annotate(
                    middle_name=Replace(
                        'group__name',
                        Value(company.company_code + ' - '),
                        Value('')
                    )
                )
                .annotate(
                    has_employee=Exists(
                        Employee.objects.filter(template=OuterRef("group"))
                    )
                )
                .filter(~(Q(group__name__endswith='user') & Q(has_employee=True)))  
                .order_by(Lower('middle_name'))
                )
                
                
        else:
            templates =  CompanyGroup.bells_manager.none()

        context = {
            'templates':templates,
            'employee_emails': employee_emails,
            }
        return render(request, self.template_name,context)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions([
                                     'userauth.read_all_acknowledgements',
                                     'userauth.read_team_acknowledgements',
                                     ]), name='dispatch')   
class CompanyEmployeeAcknowledgementView(View):
    template_name = 'company_admin/employee/employee-list.html'

    def get(self, request, *args, **kwargs):
        company = request.user.employee.company
        current_policy_type = request.GET.get('type', 'terms_and_conditions')

        if has_user_permission(request.user, 'userauth.read_all_acknowledgements'):
            employees = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
        else:
            manager = request.user.employee
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager.id,company_id=company.id)
            employees= department_data['employees']


        total_employees_count = employees.count()
        terms_and_conditions_policy = CompanyTermsAndConditionsPolicy.bells_manager.filter(
            company=company)
        
        tc_policy = terms_and_conditions_policy.filter(
            type='terms_and_conditions'
        ).first()
        
        privacy_policy = terms_and_conditions_policy.filter(
            type='privacy_policy'
        ).first()

        tc_acknowledged_count = employees.filter(
            policy_acknowledgments__policy__type='terms_and_conditions',
            policy_acknowledgments__is_acknowledged=True,
            policy_acknowledgments__is_deleted=False
        ).count() if tc_policy else 0
        
        tc_pending_count = total_employees_count - tc_acknowledged_count
        tc_pending_percentage = (tc_pending_count / total_employees_count * 100) if total_employees_count > 0 else 0
        tc_acknowledged_percentage = (tc_acknowledged_count / total_employees_count * 100) if total_employees_count > 0 else 0

        privacy_acknowledged_count = employees.filter(
            policy_acknowledgments__policy__type='privacy_policy',
            policy_acknowledgments__is_acknowledged=True,
            policy_acknowledgments__is_deleted=False
        ).count() if privacy_policy else 0
        
        privacy_pending_count = total_employees_count - privacy_acknowledged_count
        privacy_pending_percentage = (privacy_pending_count / total_employees_count * 100) if total_employees_count > 0 else 0
        privacy_acknowledged_percentage = (privacy_acknowledged_count / total_employees_count * 100) if total_employees_count > 0 else 0

        current_policy = tc_policy if current_policy_type == 'terms_and_conditions' else privacy_policy
        
        employee_status = []
        if current_policy:
            policy = current_policy
            employee_status = employees.annotate(
                is_acknowledged=Exists(
                    EmployeePolicyAcknowledgment.bells_manager.filter(
                        policy=policy,
                        employee=OuterRef('pk'),
                        is_acknowledged=True
                    )
                ),
                acknowledgment_date=Subquery(
                    EmployeePolicyAcknowledgment.bells_manager.filter(
                        policy=policy,
                        employee=OuterRef('pk'),
                        is_acknowledged=True
                    ).values('created_at')[:1]
                ),
                status_order=Case(
                    When(is_acknowledged=False, then=Value(1)), 
                    default=Value(2),  
                    output_field=IntegerField()
                )
            ).order_by('status_order', Lower('person__first_name'))
            print('employee_status', employee_status.first().acknowledgment_date)
            
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(employee_status, items_per_page)
        
        try:
            employees_obj = paginator.page(page)
        except PageNotAnInteger:
            employees_obj = paginator.page(1)
        except EmptyPage:
            employees_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((employees_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'employee_status': employees_obj,
            'policy_type': current_policy_type,
            'policy': current_policy,
            
            'tc_acknowledged_count': tc_acknowledged_count,
            'tc_pending_count': tc_pending_count,
            'tc_total_employees': total_employees_count,
            'tc_pending_percentage': tc_pending_percentage,
            'tc_acknowledged_percentage': tc_acknowledged_percentage,
            'tc_policy_exists': tc_policy is not None,
            
            'privacy_acknowledged_count': privacy_acknowledged_count,
            'privacy_pending_count': privacy_pending_count,
            'privacy_total_employees': total_employees_count,
            'privacy_pending_percentage': privacy_pending_percentage,
            'privacy_acknowledged_percentage': privacy_acknowledged_percentage,
            'privacy_policy_exists': privacy_policy is not None,
            
            'no_data': current_policy is None,
        }        
        return render(request, self.template_name, context)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_terms_and_conditions_all',
                                     'company_admin.update_terms_and_conditions_all',]), name='dispatch') 
class TermsAndConditionsOperationsView(View):
    template_name = 'company_admin/documents/terms_and_conditions_operations.html'

    def get(self, request, *args, **kwargs):
        logger.info(f"Accessing terms and conditions GET method - URL: {request.resolver_match.url_name}")
        url_name = request.resolver_match.url_name
        company = request.user.employee.company
        context ={}
        try :
            company_policy = CompanyTermsAndConditionsPolicy.bells_manager.get(
                company= company, 
                type='terms_and_conditions'
            )
        except CompanyTermsAndConditionsPolicy.DoesNotExist:
            logger.info(f"No existing terms and conditions found for company {company.id}")
            company_policy = None

        except Exception as e:
            logger.error(f"Error retrieving company policy: {str(e)}", exc_info=True)
            messages.error(request, "Failed to retrieve company policy.")
            return redirect('company:company_documents')
        
        try:
            if url_name == 'company_terms_and_conditions_edit':
                logger.info("Rendering terms and conditions form")
                if company_policy:
                    form = CompanyTermsAndConditionsPolicyForm(instance=company_policy)                      
                else:
                    form = CompanyTermsAndConditionsPolicyForm(initial={
                        'type': 'terms_and_conditions',
                        'company': company})
                context['form'] = form

            elif url_name == 'company_terms_and_conditions_view':
                logger.info("Rendering terms and conditions view ")
                if company_policy:
                    form = None  
                    description = company_policy.description
                else:
                    description = None

                context={
                    'description':description
                }              
            return render(request, self.template_name ,context)
        
        except Exception as e:
            logger.error(f"Error processing terms and conditions view: {str(e)}", exc_info=True)
            messages.error(request, "Something went wrong while processing your request.")
            return redirect('company:company_documents')
        
    def post(self, request, *args, **kwargs):
        logger.info("Processing terms and conditions form submission")
        company = request.user.employee.company
        try:
            company_terms_conditions = CompanyTermsAndConditionsPolicy.bells_manager.filter(
                company=company, 
                type='terms_and_conditions'
            ).first()

            if company_terms_conditions:
                logger.info("Updating existing terms and conditions")
                previous_description = company_terms_conditions.description
                form = CompanyTermsAndConditionsPolicyForm(request.POST, instance=company_terms_conditions)
                terms_created_by = company_terms_conditions.created_by
            else:
                logger.info("Creating new terms and conditions")
                form = CompanyTermsAndConditionsPolicyForm(request.POST)

            if form.is_valid():
                terms_and_conditions = form.save(commit=False)
                terms_and_conditions.company = company
                terms_and_conditions.type = 'terms_and_conditions'
                if company_terms_conditions:
                    terms_and_conditions.created_by = terms_created_by
                    terms_and_conditions.updated_by = request.user.first_name
                    terms_and_conditions.updated_at = timezone.now()
                    if previous_description != terms_and_conditions.description:
                        logger.info("Terms description changed, updating acknowledgments")
                        try:
                            acknowledgments = EmployeePolicyAcknowledgment.bells_manager.filter(policy=terms_and_conditions,is_acknowledged=True)
                            acknowledgments.update(is_acknowledged=False,is_deleted=True,updated_at=timezone.now(),updated_by=request.user.first_name)
                            logger.info(f"Updated {acknowledgments.count()} acknowledgments")
                        except Exception as e:
                            logger.error(f"Error updating acknowledgments: {str(e)}", exc_info=True)
                            messages.warning(request, "Terms saved but there was an error updating acknowledgments.")
                            return redirect('company:company_documents')
                else:
                    terms_and_conditions.created_by = request.user.first_name
                    terms_and_conditions.created_at = timezone.now()

                terms_and_conditions.save()
                logger.info(f"Successfully saved terms and conditions for company {company.id}")
                messages.success(request, "Terms and Conditions have been saved successfully!")
                return redirect('company:company_documents')       
            else:
                logger.warning(f"Form validation failed: {form.errors}")
                context = {
                    'form': form
                }
                return render(request, self.template_name, context)
        except Exception as e:
            logger.error(f"Error saving terms and conditions: {str(e)}", exc_info=True)
            messages.error(request, "Failed to save Terms and Conditions. Please try again.")
            return redirect('company:company_documents')

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_privacy_policy_all',
                                     'company_admin.update_privacy_policy_all',]), name='dispatch') 
class PrivacyPolicyOperationsView(View):
    template_name = 'company_admin/documents/privacy_policy_operations.html'

    def get(self, request, *args, **kwargs):
        logger.info(f"Accessing Privacy policy GET method - URL: {request.resolver_match.url_name}")
        context = {}
        company = request.user.employee.company
        url_name = request.resolver_match.url_name
        try :
            company_policy = CompanyTermsAndConditionsPolicy.bells_manager.get(
                company= company, 
                type='privacy_policy'
            )
        except CompanyTermsAndConditionsPolicy.DoesNotExist:
            logger.info(f"No existing terms and conditions found for company {company.id}")
            company_policy = None

        except Exception as e:
            logger.error(f"Error retrieving company policy: {str(e)}", exc_info=True)
            messages.error(request, "Failed to retrieve company policy.")
            return redirect('company:company_documents')
            
        try:
            if url_name == 'company_privacy_policy_edit':
                logger.info("Rendering Privacy policy form")
                if company_policy:
                    form = CompanyTermsAndConditionsPolicyForm(instance=company_policy)
                else:
                    form = CompanyTermsAndConditionsPolicyForm(initial={
                        'type': 'privacy_policy',
                        'company': company})
                context['form'] = form

        
            elif url_name == 'company_privacy_policy_view':
                logger.info("Rendering Privacy policy view ")
                if company_policy:
                    form = None  
                    description = company_policy.description
                else:
                    description = None

                context={
                    'description':description
                }
            return render(request, self.template_name ,context)

        except Exception as e:
            logger.error(f"Error processing privacy policy view: {str(e)}", exc_info=True)
            messages.error(request, "Something went wrong while processing your request.")
            return redirect('company:company_documents')
    
    def post(self, request, *args, **kwargs):
        logger.info("Processing privacy poicy form submission")
        company = request.user.employee.company
        try:
            company_privacy_policy = CompanyTermsAndConditionsPolicy.bells_manager.filter(
                company=company, 
                type='privacy_policy'
            ).first()

            if company_privacy_policy:
                logger.info("Updating existing privacy policy")
                previous_description = company_privacy_policy.description
                form = CompanyTermsAndConditionsPolicyForm(request.POST, instance=company_privacy_policy)
                privacy_policy_created_by = company_privacy_policy.created_by 
            else:
                logger.info("Creating new Privacy policy")
                form = CompanyTermsAndConditionsPolicyForm(request.POST)

            if form.is_valid():
                privacy_policy = form.save(commit=False)
                privacy_policy.company = company
                privacy_policy.type = 'privacy_policy'
                if company_privacy_policy:  
                    privacy_policy.created_by = privacy_policy_created_by
                    privacy_policy.updated_by = request.user.first_name
                    privacy_policy.updated_at = timezone.now()
                    if previous_description != company_privacy_policy.description:
                        logger.info("Privacy policy changed, updating acknowledgments")         
                        try:
                            acknowledgments = EmployeePolicyAcknowledgment.bells_manager.filter(policy=privacy_policy,is_acknowledged=True)
                            acknowledgments.update(is_acknowledged=False,is_deleted=True,updated_at=timezone.now(),updated_by=request.user.first_name)
                            logger.info(f"Updated {acknowledgments.count()} acknowledgments")
                        except Exception as e:
                            logger.error(f"Error updating acknowledgments: {str(e)}", exc_info=True)
                            messages.warning(request, "Privacy policy saved but there was an error updating acknowledgments.")
                            return redirect('company:company_documents')
                else:
                    privacy_policy.created_by = request.user.first_name
                    privacy_policy.created_at = timezone.now()
                                
                privacy_policy.save()
                logger.info(f"Successfully saved privacy policy for company {company.id}") 
                messages.success(request, "Privacy Policy have been saved successfully!")
                return redirect('company:company_documents')
            
            else:
                logger.warning(f"Form validation failed: {form.errors}")
                context = {
                    'form': form
                }
                return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error saving privacy policy: {str(e)}", exc_info=True)
            messages.error(request, "Failed to save Privacy policy. Please try again.")
            return redirect('company:company_documents')
        
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.update_incident_all',
                                     'company_admin.update_incident_own_team',
                                     'company_admin.create_incident_all',
                                     'company_admin.create_incident_own_team',
                                     'company_admin.create_incident_there_own']), name='dispatch')
class TagEmployee(View):
    template_name = 'company_admin/dashboard/incidents/tag-employee.html'

    def get(self, request, *args, **kwargs):
        
        try:
            incident_id = request.session.get('incident_id') if request.session.get('incident_id', None) else  request.GET.get('incident_id')
            current_employee_id = request.session.get('employee_id') if request.session.get('employee_id', None) else  request.GET.get('employee_id')
            current_client_id = request.session.get('client_id') if request.session.get('client_id', None) else  request.GET.get('client_id')
            company = request.user.employee.company
            login_user = request.user.employee
            incident_view = request.GET.get('incident_view') if request.GET.get('incident_view') else False
            
            employees = ClientEmployeeAssignment.get_employees_by_client(client_id=current_client_id,company_id=company.id).exclude(id=current_employee_id).distinct() 
            
            #listing tagged employee in list
            tagged_employees_for_current_employee_and_client=IncidentTaggedEmployee.bells_manager.filter(
                            incident_id=incident_id,
                            tagged_to_client_id = current_client_id,
                            tagged_to_employee_id=current_employee_id,
                            is_removed = False
                            )
            #if client and employee changed then setting previous records is_removed true
            if not tagged_employees_for_current_employee_and_client:
                previous_tagged_incident_record = IncidentTaggedEmployee.bells_manager.filter(
                            incident_id=incident_id,
                            is_removed = False
                )
                if previous_tagged_incident_record.exists():
                    previous_tagged_incident_record.update(is_removed=True,untagged_by=login_user)

            #tagged employee ids to mark them checked
            tagged_employee_ids_for_current_employee_and_client = list(tagged_employees_for_current_employee_and_client.values_list('tagged_employee_id', flat=True))

            #collecting is any person involved for a incident
            incident_obj = Incident.bells_manager.get(id=incident_id)

            page = request.GET.get('page', 1)
            items_per_page=50
            pagination_result = paginate_query(tagged_employees_for_current_employee_and_client, page, items_per_page)

            context = {
                
                'employees': employees,
                'start_entry': pagination_result['start_entry'],
                'end_entry': pagination_result['end_entry'],
                'total_entries': pagination_result['total_entries'],
                'tagged_employee_ids':tagged_employee_ids_for_current_employee_and_client,
                'employees_queryset':pagination_result['paginated_data'],
                'incident_id': incident_id,
                'employee_id': current_employee_id,
                'client_id': current_client_id,
                'incident_obj':incident_obj,
                'incident_view':incident_view
            }
            return render(request, self.template_name, context)
        except Exception as e:
            print(f'Exception error: {e}')
            return redirect('company:client_incident_reports_dashboard')

    def post(self, request, *args, **kwargs):
        try:
            incident_id = request.session.get('incident_id', None)
            current_incident_employee_id = request.session.get('employee_id', None)
            current_incident_client_id = request.session.get('client_id', None)

            login_user = request.user.employee
            selected_employees = request.POST.get('selected_employees', '').split(',')
            unselected_employees = request.POST.get('unselected_employees', '').split(',')
            
            incident_obj = Incident.bells_manager.filter(id = incident_id).first()
            if incident_obj:
                if selected_employees and '' not in selected_employees:
                    for employee_id in selected_employees:
                        existing_incident_tagged_employee = IncidentTaggedEmployee.bells_manager.filter(
                            incident=incident_obj,
                            tagged_to_client_id = current_incident_client_id,
                            tagged_employee_id=employee_id,
                            is_removed=False
                            )
                        if existing_incident_tagged_employee:
                            existing_incident_tagged_employee.update(is_removed=False)
                        else:
                            IncidentTaggedEmployee.bells_manager.create(
                                incident=incident_obj,
                                tagged_employee_id=employee_id,  
                                tagged_by=login_user,
                                tagged_to_employee_id=current_incident_employee_id,
                                tagged_to_client_id=current_incident_client_id
                            )   
                if unselected_employees and '' not in unselected_employees:
                    for employee_id in unselected_employees:
                        incident_queryset = IncidentTaggedEmployee.bells_manager.filter(
                            incident=incident_obj,
                            tagged_employee_id=employee_id,
                            tagged_to_client_id = current_incident_client_id,
                            is_removed=False,
                            
                            )
                        incident_queryset.update(is_removed=True,untagged_by = login_user)
                
                return redirect('company:manager_tag_employee')

            else:
                print('Incident not found with incident id {incident_id}')
                return redirect('company:client_incident_reports_dashboard')
        except Exception as e:
            print(f'Exception error: {e}')
            return redirect('company:client_incident_reports_dashboard')


@login_required
def IncidentEmployeePresent(request):
    if request.method == 'POST':
        try:
            incident_id = request.POST.get('incident_id')
            employee_present = request.POST.get('employee_present')
            login_user = request.user.employee
            incident = get_object_or_404(Incident.bells_manager, id=incident_id)

            if incident:
                incident.employees_involved = employee_present
                incident.save()
                incident_queryset = IncidentTaggedEmployee.bells_manager.filter(
                        incident=incident,
                        is_removed=False
                        )
                if incident_queryset:
                    incident_queryset.update(is_removed=True,untagged_by=login_user)
            
            else:
                print("Incident not found.")
        except Exception as e:
            print(f"Error: {e}")
    request.session['confirm_modal_flag'] = False
    if request.resolver_match.url_name == 'employee_incident_employee_present':
        return redirect('employee:employee_tag_employee')
    return redirect('company:manager_tag_employee')

@method_decorator(login_required, name='dispatch')
# @method_decorator(check_permissions(['company_admin.update_all_services',
#                                      'company_admin.update_service_their_team_own',]), name='dispatch') 
class CompanyClientProfileEmployeeAssignmentView(View):
    def post(self, request, client_id):
        """
        Assign or update employees assigned to a client.
        - Adds new employees to the service delivery team for the client.
        - Marks unselected employees as deleted.
        """
        try:
            selected_employee_ids = set(map(int, request.POST.getlist('selected-employees[]')))
            unselected_employee_ids = set(map(int, request.POST.getlist('unselected-employees[]')))

            existing_assignments = ClientEmployeeAssignment.bells_manager.filter(client_id=client_id)
            existing_employee_ids = set(existing_assignments.values_list('employee_id', flat=True))

            if unselected_employee_ids:
                ClientEmployeeAssignment.bells_manager.filter(
                    client_id=client_id,
                    employee_id__in=unselected_employee_ids,
                    is_deleted=False
                ).update(is_deleted=True,
                         updated_at=timezone.now(),
                         updated_by=f"{request.user.first_name}  {request.user.last_name}"
                         )

            new_employee_ids = selected_employee_ids - existing_employee_ids
            employees_to_assign = Employee.bells_manager.filter(id__in=new_employee_ids)

            assignments_to_create = [
                ClientEmployeeAssignment(client_id=client_id, employee=employee, created_by = request.user,created_at = timezone.now())
                for employee in employees_to_assign
            ]
            
            if assignments_to_create:
                ClientEmployeeAssignment.bells_manager.bulk_create(assignments_to_create)

            logger.info(f'Client assignments updated for client {client_id}')
            return JsonResponse({'success': True})

        except Exception as e:
            print(e)
            logger.error(f'Error assigning employees to client {client_id}: {str(e)}')
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred'}, status=500)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.update_clients_to_department',
                                     'userauth.update_own_clients_to_department'
                                   ]), name='dispatch') 
class DepartmentClientAssignmentView(View):
    template_name = 'company_admin/department/department-operations.html'

    def get(self, request, *args, **kwargs):
        dept_id = request.GET.get('dept_id')
        company = request.user.employee.company
        department = Department.bells_manager.filter(id=dept_id, company=company).first()

        if not department:
            messages.error(request, "Team not found.")
            return redirect('company:departments_list')


        clients_assigned_to_department = Client.bells_manager.filter(company=company,
            department_client_assignments__department=department,
            department_client_assignments__is_deleted=False,
        ).distinct().order_by(Lower('person__first_name'))

        assigned_client_ids = list(clients_assigned_to_department.values_list('id', flat=True))
        
        can_view_clients = set()
        if has_user_permission(request.user, 'userauth.read_all_clients'):
            can_view_clients = set(assigned_client_ids)
        if has_user_permission(request.user, 'userauth.read_team_clients'):
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            clients_ids = list(department_data['clients'].values_list('id', flat=True))
            can_view_clients = set(clients_ids).intersection(assigned_client_ids)

                
        if has_user_permission(request.user, 'userauth.update_clients_to_department'):
            clients = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
        elif has_user_permission(request.user, 'userauth.update_own_clients_to_department'):  
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            clients = department_data['clients']
        else:
            clients = Client.bells_manager.none()
        items_per_page = 50
        page = request.GET.get('page', 1)
        pagination_result = paginate_query(clients_assigned_to_department, page, items_per_page)

        context = {
            'start_entry':pagination_result['start_entry'] ,
            'end_entry': pagination_result['end_entry'],
            'total_entries': pagination_result['total_entries'],
            'clients': clients,
            'department_id': dept_id,
            'assigned_client_ids': list(assigned_client_ids),
            'assigned_clients': pagination_result['paginated_data'],
            'can_view_clients':can_view_clients
        }

        return render(request, self.template_name, context)
    
    def post(self, request , *args, **kwargs):
        """
        Assign or update clients assigned to a department.
        - Adds new clients to the department.
        - Marks unselected clients as deleted.
        """
        try:
            department_id = request.POST.get('dept_id')
            selected_client_ids = set(map(int, request.POST.getlist('selected-clients[]')))
            unselected_client_ids = set(map(int, request.POST.getlist('unselected-clients[]')))

            department = Department.bells_manager.filter(id=department_id).first()
            if not department:
                return JsonResponse({'success': False, 'error': 'Team not found'}, status=404)

            existing_assignments = DepartmentClientAssignment.bells_manager.filter(department=department)
            existing_client_ids = set(existing_assignments.values_list('client_id', flat=True))

            if unselected_client_ids:
                existing_assignments.filter(
                    client_id__in=unselected_client_ids,
                    is_deleted=False
                ).update(
                    is_deleted=True,
                    updated_at=timezone.now(),
                    updated_by=f"{request.user.first_name} {request.user.last_name}"
                )

            # Create new assignments for selected clients
            new_client_ids = selected_client_ids - existing_client_ids
            if new_client_ids:
                clients_to_assign = Client.bells_manager.filter(id__in=new_client_ids)
                assignments_to_create = [
                    DepartmentClientAssignment(
                        department=department,
                        client=client,
                        created_by=request.user,
                        created_at=timezone.now(),
                    )
                    for client in clients_to_assign
                ]
                DepartmentClientAssignment.bells_manager.bulk_create(assignments_to_create)

            logger.info(f"Client assignments updated for department {department_id}")
            return JsonResponse({'success': True})

        except Exception as e:
            logger.error(f"Error assigning clients to Team {department_id}: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred'}, status=500)
        
@method_decorator(login_required, name='dispatch')
class CompanyHeirarchyListView(View):
    template_name = 'company_admin/hierarchy/hierarchy_list.html'
    def get(self, request,*args, **kwargs):
        company = request.user.employee.company        
        investigation_hierarchy = InvestigationHierarchy.bells_manager.filter(company=company).first()
        hierarchy_form = CompanyInvestigationHierarchyForm()
        context ={
            'investigation_hierarchy':investigation_hierarchy,
            'hierarchy_form' : hierarchy_form,
            'company':company,
            'category': 'incident_investigation_hierarchy',
        }
        
        return render(request, self.template_name,context) 

    def post(self, request,*args, **kwargs):
        employee = request.user.employee
        company = employee.company

        hierarchy_form = CompanyInvestigationHierarchyForm(request.POST)
        
        if hierarchy_form.is_valid():
            hierarchy = hierarchy_form.save(commit=False)
            hierarchy.created_by = employee
            hierarchy.save()
            messages.success(request, "Company investigation hierarchy saved successfully!")
            request.session['hierarchy_id'] = hierarchy.id
            request.session['hierarchy_levels'] = hierarchy_form.cleaned_data['levels']
            request.session['hierarchy_days'] = hierarchy_form.cleaned_data['hierarchy_timeline_days']
            self.map_investigation_to_new_existing_inidents(company)
            return redirect('company:hierarchy_stages_list', hierarchy_id=hierarchy.id)
        else:
            investigation_hierarchy = InvestigationHierarchy.bells_manager.first()
            context = {
                'investigation_hierarchy': investigation_hierarchy,
                'hierarchy_form': hierarchy_form,
                'company': company,
                'category': 'incident_investigation_hierarchy',
            }
            for field, errors in hierarchy_form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return render(request, self.template_name, context)
    
    def map_investigation_to_new_existing_inidents(self,company):
        try:
            company = Company.bells_manager.get(id=company.id)
        except Company.DoesNotExist:
            logger.warning(f'Company not found with ID {company.id} for investigation backfill.')
            return

        try:
            investigation_hierarchy = InvestigationHierarchy.bells_manager.get(company=company)
        except InvestigationHierarchy.DoesNotExist:
            logger.warning(f'No InvestigationHierarchy found for company {company.id}.')
            return

        new_existing_incidents = Incident.bells_manager.filter(status='New', company=company, investigation_hierarchy__isnull=True)
        
        if not new_existing_incidents.exists():
            logger.info(f'No new incidents found for company {company.id}.')
            return

        for incident in new_existing_incidents:
            incident.investigation_hierarchy = investigation_hierarchy
            incident.save()
            logger.info(f'Backfilled Incident ID {incident.id} with InvestigationHierarchy ID {investigation_hierarchy.id}.')

class CompanyHeirarchyOperationsView(View):
    template_name = 'company_admin/hierarchy/hierarchy_operations.html'
    def get(self, request,*args, **kwargs):
        return render(request, self.template_name)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['userauth.update_templates','userauth.create_templates','userauth.read_templates']), name='dispatch') 
class TemplateOperationsView(View):
    template_name = 'company_admin/template/template_operations.html'

    def get(self, request, template_id=None,*args, **kwargs):
        company = request.user.employee.company
        user_template_request = request.GET.get('user_template_request')
        url_name = request.resolver_match.url_name
        input_value_template_name = request.GET.get('template_name')
        if url_name == 'add_template' and not request.user.has_perm('userauth.create_templates'):
            messages.error(request, "Unauthorized access attempted.You do not have permission to add a template.")
            return redirect('company:template_list')
        if url_name == 'edit_template' and not request.user.has_perm('userauth.update_templates'):
            messages.error(request, "Unauthorized access attempted.You do not have permission to edit a template.")
            return redirect('company:template_list')
        
        company_templates = CompanyGroup.bells_manager.filter(company=company)
        company_templates = (
                CompanyGroup.bells_manager
                .filter(company=company)
                .annotate(
                    middle_name=Replace(
                        'group__name', 
                        Value(company.company_code + ' - '),  
                        Value('')  
                    )
                )
                .order_by(Lower('middle_name'))
            )
        # simple_templates = []
        # user_templates = []

        # for company_template in company_templates:
        #     group_name = company_template.group.name
        #     is_exit=Employee.bells_manager.filter(template__name = group_name).exists()
        #     if " - user" in group_name and is_exit:
        #         # user_templates.append(company_template)
        #             employee_emails = Employee.bells_manager.filter(template_id=company_template.group.id).values_list("person__email", flat=True)
        #             user_templates.append({
        #             "template": company_template,
        #             "emails": list(employee_emails)
        #         })
        #     else:
        #         simple_templates.append(company_template)
        
        # Get both template types as a tuple
        simple_templates, user_templates = get_company_templates(company)

        # Now you can use simple_templates and user_templates directly              
        try:
            feature_data = get_all_features_data()
            existing_permissions = None
            template_display_name = None
            actual_template_name =  None
            company_templates_data = []
            for group in company_templates:
                group_permissions = list(group.group.permissions.values_list('codename', flat=True))
                company_templates_data.append({
                    # 'id':group.group.id,
                    # 'name': group.group.name.split('-')[-1].strip() if " - user" not in group.group.name else group.group.name.split('-')[-2].strip(),
                    'permissions': group_permissions,
                })
            
            existing_permissions = get_employee_permissions()

            if template_id and (request.resolver_match.url_name == 'edit_template' or request.resolver_match.url_name == 'clone_template' or request.resolver_match.url_name == 'view_template'):
                try:
                    group = Group.objects.get(id=template_id)
                    existing_permissions = list(group.permissions.values_list('codename', flat=True))
                    if " - user" in group.name:
                        # template_display_name = group.name.split('-')[-2].strip()
                        employee = Employee.bells_manager.filter(template__name = group).first()
                        if employee:
                            user_template = f'{employee.person.first_name} {employee.person.last_name}'
                            template_display_name = user_template
                            actual_template_name = employee.template.name
                        else:
                            template_display_name = None
                            actual_template_name = None
                    else:
                        template_display_name = group.name.split('-')[-1].strip()
                        actual_template_name =  group.name
                 
                except Group.DoesNotExist:
                    logger.warning(f"Group with id {template_id} not found")
                    return redirect('company:template_list')
                        
            context = get_template_context(
                feature_data=feature_data,
                template_id=template_id,
                existing_permissions=existing_permissions,
            )
            
            if template_display_name and not request.resolver_match.url_name == 'clone_template':
                context['template_name'] = template_display_name
                context['actual_template_name'] = actual_template_name

            context['simple_templates'] = simple_templates
            context['company_templates_data'] = json.dumps(company_templates_data, cls=DjangoJSONEncoder) 
            context['clone_template_name'] = template_display_name
            context['user_templates'] = user_templates
            
            if not request.session.get('redirected_from_post'):
                request.session['template_exists'] = False
            request.session['redirected_from_post'] = False
            if request.resolver_match.url_name == 'edit_template':
                context['existing_template'] = template_display_name
                context['actual_existing_template_name'] = actual_template_name
            
            if request.resolver_match.url_name == 'clone_template':
                context['clone_template_name'] = template_display_name
                context['actual_template_name'] = actual_template_name
                context['template_name'] = input_value_template_name

            context['user_template_request'] = user_template_request
            return render(request, self.template_name, context)

        except Exception as e:
            logger.error(f"Error in TemplateOperationsView.get: {str(e)}")
            return redirect('company:template_list')

    
    def post(self, request, template_id=None, *args, **kwargs):
        company = request.user.employee.company
        template_id = request.POST.get('template_id')
        feature_permissions = request.POST.get('final_feature_data')
        template_name = request.POST.get('template_name_hidden')
        url_name = request.resolver_match.url_name        
                
        is_valid = validate_feature_permissions(feature_permissions)
        if not is_valid:
            messages.error(request,'Something went wrong!')
            if url_name == 'template_feature' and template_id:
                return redirect(reverse('company:edit_template', args=[template_id]))
            
            if url_name == 'template_feature' and not template_id:
                return redirect('company:add_template')
           


        if not feature_permissions:
            messages.info(request,'Template permissions are missing')
            return redirect('company:add_template')

        try:
            feature_data_dict = json.loads(feature_permissions)
            permission_codes = [
                entry["accessLevelCode"]
                for features in feature_data_dict.values()
                for entry in features
                if entry.get("is_active", True) 
            ]
            
            if not permission_codes:
                messages.info(request,'Template permissions are missing')
                return redirect('company:add_template')

            group_name = f"{company.company_code.strip()} - {template_name.strip()}".lower()
            user_group_name = f"{company.company_code.strip()} - {template_name.strip()} - user".lower()

            if template_id and not request.resolver_match.url_name == 'clone_template':
                # Update existing template
                try:
                    group = Group.objects.get(id=template_id)
                    is_user_template = group.name.lower().endswith('- user')

                    if is_user_template:
                        new_group_name = user_group_name
                    else:
                        new_group_name = group_name

                    if Group.objects.filter(name=new_group_name).exclude(id=template_id).exists():
                        messages.error(request, "A group with this name already exists.")
                        return redirect('company:add_template')

                    if group.name.lower() != new_group_name:
                        group.name = new_group_name
                        group.save()
                        logger.info(f"Permission set name updated to {new_group_name}")
                        # messages.info(request, 'Template Updated successfully!')

                    else:
                        logger.info(f"No name change required for template: {group.name}")


                    # Update permissions
                    group.permissions.clear()  # Remove existing permissions
                    permissions = Permission.objects.filter(codename__in=permission_codes)
                    group.permissions.add(*permissions)
                    update_template_permissions(group)
                    # Log any missing permissions
                    existing_permission_codes = permissions.values_list('codename', flat=True)
                    missing_permissions = set(permission_codes) - set(existing_permission_codes)
                    if missing_permissions:
                        for permission_code in missing_permissions:
                            logger.warning(f"Permission with code {permission_code} does not exist.")

                    logger.info(f"Successfully updated template {group_name}")
                    messages.info(request, 'Template Updated successfully!')
                    if url_name == 'template_feature' and not is_user_template:
                        return redirect('company:template_list')
                    else:
                        return redirect('company:users_template_list')

                    
                except Exception:
                    logger.error(f"Group with id {template_id} not found during update")
                    return redirect('company:template_list')
            else:
                if not template_name:
                    messages.info(request,'Template name required')
                    return redirect('company:add_template')

                existing_groups = Group.objects.filter(company_groups__company=company)
                    
                # Check if template with same name exists
                if existing_groups.filter(name=group_name).exists() or existing_groups.filter(name=user_group_name).exists():
                    logger.warning(f"Group '{group_name}' already exists.")
                    request.session['template_exists'] = True
                    request.session['permissions_exists'] = False  
                    request.session['redirected_from_post'] = True
                    request.session['template_name'] = template_name
                    messages.info(request, 'Template with this name already exist')
                    return redirect('company:add_template')
                
                else:
                    for existing_group in existing_groups:
                        existing_permissions = set(existing_group.permissions.values_list('codename', flat=True))
                        new_permissions = set(permission_codes)
                    
                        if existing_permissions == new_permissions:
                            logger.warning(f"A template with the same permissions already exists: {existing_group.name}")
                            request.session['template_exists'] = True  
                            request.session['redirected_from_post'] = True
                            request.session['template_name'] = template_name
                            messages.info(request, 'Template with these permission set already exists!')
                            return redirect('company:add_template')
                # Create new group and assign permissions
                group = Group.objects.create(name=group_name.lower())
                company_group_obj = CompanyGroup.bells_manager.create(group=group, company=company)

                if company_group_obj:
                    permissions = Permission.objects.filter(codename__in=permission_codes)
                    group.permissions.add(*permissions)

                    # Log any missing permissions
                    existing_permission_codes = permissions.values_list('codename', flat=True)
                    missing_permissions = set(permission_codes) - set(existing_permission_codes)
                    if missing_permissions:
                        for permission_code in missing_permissions:
                            logger.warning(f"Permission with code {permission_code} does not exist.")
                            print(f"Permission with code {permission_code} does not exist.")
                    logger.info(f"Successfully created new template {group_name}")
                    messages.info(request, 'Template added successfully!')
                    return redirect('company:template_list')

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return redirect('company:add_template')
        


@login_required
def templatePermissionsIsExist(request):
    try:
        if request.method == 'POST':
            company = request.user.employee.company
            feature_permissions = request.POST.get('final_feature_data')
            is_add_request = request.POST.get('is_add_request').strip()
            current_existing_template = request.POST.get('existing_template').strip()
            template_name = request.POST.get('template_name')
          
            group_name = f"{company.company_code.strip()} - {template_name.strip()}".lower()
            user_group_name = f"{company.company_code.strip()} - {template_name.strip()} - user".lower()
            current_existing_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()}".lower()
            current_existing_user_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()} - user".lower()
            
            feature_data_dict = json.loads(feature_permissions)
            permission_codes = [
                entry["accessLevelCode"]
                for features in feature_data_dict.values()
                for entry in features
                if entry.get("is_active", True)
            ]
            
            if not permission_codes:
                messages.info(request, 'Template permissions are missing')
                return JsonResponse({'exists': False}, status=200)

            new_permissions = set(permission_codes)

            existing_groups = Group.objects.filter(company_groups__company=company)

            for existing_group in existing_groups:
                existing_permissions = set(existing_group.permissions.values_list('codename', flat=True))

                if new_permissions == existing_permissions: 
                    if request.resolver_match.url_name == 'edit_template' and (
                            current_existing_group_name != group_name or current_existing_user_group_name != user_group_name):
                        return JsonResponse({'exists': True}, status=200)
                    
                    if is_add_request == 'true':
                        logger.warning(f"A template with the same permissions already exists: {existing_group.name}")
                        return JsonResponse({'exists': True}, status=200)

            return JsonResponse({'exists': False}, status=200)

    except Exception as e:
        logger.error(f"Error in templatePermissionsIsExist: {str(e)}")
        return JsonResponse({'exists': False}, status=500)


@login_required
def template_is_exist(request):
    try:
        if request.method == 'POST':
            company = request.user.employee.company
            template_name = request.POST.get('template_name')
            is_add_request = request.POST.get('is_add_request').strip()
            current_existing_template = request.POST.get('existing_template').strip()

            if not template_name:
                messages.info(request, 'Template name is missing')
                return JsonResponse({'exists': False}, status=200)
            
            group_name = f"{company.company_code.strip()} - {template_name.strip()}".lower()
            user_group_name = f"{company.company_code.strip()} - {template_name.strip()} - user".lower()
            current_existing_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()}".lower()
            current_existing_user_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()} - user".lower()
            
            existing_groups = Group.objects.filter(company_groups__company=company)
            if existing_groups.filter(name=group_name).exists() or existing_groups.filter(name=user_group_name).exists():
                if is_add_request == 'true' and current_existing_group_name!= group_name or current_existing_user_group_name!= user_group_name :
                    logger.warning(f"Group '{group_name}' already exists.")
                    return JsonResponse({'exists': True}, status=200)
            return JsonResponse({'exists': False}, status=200)

    except Exception as e:
        return JsonResponse({'exists': False}, status=500) 




@login_required
def template_is_exist_on_blur(request):
    try:
        if request.method == 'POST':
            company = request.user.employee.company
            template_name = request.POST.get('template_name')
            is_add_request = request.POST.get('is_add_request').strip()
            current_existing_template = request.POST.get('existing_template').strip()

            if not template_name:
                return JsonResponse({'exists': False}, status=200)
            
            group_name = f"{company.company_code.strip()} - {template_name.strip()}".lower()
            user_group_name = f"{company.company_code.strip()} - {template_name.strip()} - user".lower()
            current_existing_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()}".lower()
            current_existing_user_group_name = f"{company.company_code.strip()} - {current_existing_template.strip()} - user".lower()
            
            existing_groups = Group.objects.filter(company_groups__company=company)
            if existing_groups.filter(name=group_name).exists() or existing_groups.filter(name=user_group_name).exists():
                if is_add_request == 'true' and current_existing_group_name!= group_name or current_existing_user_group_name!= user_group_name :
                    logger.warning(f"Group '{group_name}' already exists.")
                    return JsonResponse({'exists': True}, status=200)
            return JsonResponse({'exists': False}, status=200)

    except Exception as e:
        return JsonResponse({'exists': False}, status=500) 
 


@login_required    
def user_punch_in_view(request):
    shift_id = request.POST.get('shift_id')
    # shift_form = DailyShiftNoteForm(initial={
    #                                 'client':shift_client.id,'shift':shift_id,'employee': employee, 'company': company, 'sno': company.next_daily_shift_sno()}, company=company, request=request,)
    if shift_id:
        employee = request.user.employee
        company = employee.company
        shift_client =  None
        current_time = timezone.now().replace(second=0, microsecond=0)

        shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
        if shift:
            try:
                shift_note = DailyShiftCaseNote.objects.create(
                    shift=shift,
                    employee=employee,
                    company=company,
                    client=shift.client,
                    sno =company.next_daily_shift_sno(),
                    start_date_time=current_time,
                )
                shift.status = 'Ongoing'
                shift.save()
                return JsonResponse({'success': True, 'message': 'Progress note created successfully!'},status=200)
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'An error occurred while creating the progress note.'}, status=500)
    else:
        return JsonResponse({'success':False}, status=400)


from utils.helper import assign_permission_to_group

def backfill_employee_templates():
    print("Starting backfill_employee_templates() function...") 
    
    role_to_template = {
        1: 'admin',
        2: 'manager',
        3: 'employee',
    }

    # for employee in Employee.objects.all():
    for employee in Employee.objects.filter(id = 301, company = 1):

        print(f"Processing employee {employee.company} {employee.id}...") 
        
        role = employee.role
        permission_mapper_role = role_to_template[role]
        company = employee.company
        first_name = employee.person.first_name.strip().lower()
        last_name = employee.person.last_name.strip().lower()
        if role in role_to_template:
            template_name = f"{company.company_code.strip().lower()} - {first_name}-{last_name}-{employee.id} - user"
            template, created = Group.objects.get_or_create(name=template_name)

            if created:
                print(f"Created new user template '{template_name}' for employee '{employee.person.first_name}', id '{employee.id}'")
                CompanyGroup.objects.get_or_create(group=template, company=company)
                print(f"Created CompanyGroup for company '{company.company_code}' and template '{template}'")
                
                #assigning permission to group and user
                assign_permission_to_group(company, template, permission_mapper_role,employee)
                employee.template = template
                employee.save()
                    
            else:
                print(f"Updated employee {employee.id} with existing template '{template_name}'")
            
    print('Assignment Completed successfully')    
    



def create_groups_for_all_companies():
    companies = Company.objects.all()
    for company in companies:
        create_default_group_for_companies(company)
        print(f"Created default groups for company: {company.company_code}")
        
        


@method_decorator(login_required, name='dispatch')
class CompanyHeirarchyStagesOperationsView(View):
    template_name = 'company_admin/hierarchy/hierarchy_operations.html'   
    def get(self, request, hierarchy_id=None, *args, **kwargs):
        # hierarchy_id = request.session.get('hierarchy_id') if request.session.get('hierarchy_id') else hierarchy_id
        company =request.user.employee.company
        investigation_hierarchy_instance = InvestigationHierarchy.bells_manager.filter(id=hierarchy_id,company=company).first()
        if investigation_hierarchy_instance:
            hierarchy_levels = investigation_hierarchy_instance.levels
            hierarchy_timeline_days = investigation_hierarchy_instance.hierarchy_timeline_days
        else:
            hierarchy_levels = None
            hierarchy_timeline_days = None
            messages.warning(request, 'The investigation hierarchy does not exist or could not be found.')
            return redirect('company:company_hierarchy_list')

        stages = InvestigationStage.bells_manager.filter(
            hierarchy=investigation_hierarchy_instance,
            is_active=True
        ).order_by('-s_no')


        PERMISSIONS = [
            'company_admin.update_incident_investigation_all',
            'company_admin.update_incident_investigation_own_team',
            'company_admin.update_incident_investigation_self'
        ]

        def has_required_permission(person):
            return any(has_user_permission(person, perm) for perm in PERMISSIONS)

        owner_employees = Employee.bells_manager.filter(company=company)
        owner_employees = [emp for emp in owner_employees if hasattr(emp, 'person') and has_required_permission(emp.person)]
        owner_options = [
            {"id": emp.id, "name": f"{emp.person.first_name} {emp.person.last_name}"}
            for emp in owner_employees
        ]

        substitute_employees = Employee.bells_manager.filter(company=company)
        substitute_employees = [emp for emp in substitute_employees if hasattr(emp, 'person') and has_required_permission(emp.person)]
        substitute_options = [
            {"id": emp.id, "name": f"{emp.person.first_name} {emp.person.last_name}"}
            for emp in substitute_employees
        ]

        stage_data = []
        for stage in stages:
            stage_data.append({
                "id": stage.s_no,
                "level": stage.s_no,
                "name": stage.stage_name,
                "timeline": stage.stage_timeline_days,
                "owners": [
                    {   "id": stage_owner.id,
                        "owner": stage_owner.owner_id,
                        "substitute": stage_owner.substitute_id,
                        "timeline": stage_owner.substitute_timeline_days,
                        "owner_name": stage_owner.owner.person.first_name if stage_owner.owner else None,
                        "substitute_name": stage_owner.substitute.person.first_name if stage_owner.substitute else None
            
                    }
                    for stage_owner in stage.stage_owners.all()
                ],
                "questions": [
                    {
                        "id": question.id,
                        "question": question.question
                    }
                    for question in stage.investigation_questions.all()
                ],
                "permissions": [
                    {"value": permission.codename, "checked": True}
                    for permission in stage.permissions.all()
                ]
            })

        
        context = {
            'hierarchy_levels': hierarchy_levels,
            'hierarchy_timeline_days': hierarchy_timeline_days,
            'hierarchy_id': hierarchy_id,
            'stages_json': json.dumps(stage_data) ,
            'owner_options': json.dumps(owner_options),
            'substitute_options': json.dumps(substitute_options),
         
        }
        return render(request, self.template_name, context)    
    
    def post(self, request, hierarchy_id=None, *args, **kwargs):
        
        employee = request.user.employee
        company = employee.company
        stage_id = None
        stage_new_version = False
        is_new_stage = False
        is_hierarchy_timeline_changed = False
        self.version_upgrade_stage_list = []
        try:
            hierarchy_levels = int(request.POST.get('hierarchy_levels') or 1)
            hierarchy_timeline = request.POST.get('hierarchy_timeline')

            if not hierarchy_timeline or not hierarchy_timeline.isdigit() or int(hierarchy_timeline) < 1:
                return JsonResponse({
                    'status': 'fail',
                    'error_type': 'invalid_hierarchy_timeline',
                    'message': 'Hierarchy timeline must be a number greater than or equal to 1.'
                })

            hierarchy_timeline = int(hierarchy_timeline)
            response = self.validate_total_stage_timeline_against_hierarchy(request, hierarchy_levels)
            status = response['status']
            message = response['message']
            time_line_status = response['time_line_status']
            if status == False:
                return JsonResponse({
                    'message': message,
                    'status':'fail',
                    'time_line_status':time_line_status
                })
                
            validation_response = self.validate_unique_stage_names(request, company, hierarchy_id, hierarchy_levels)
            if request.resolver_match.url_name == 'add_hierarchy_stages':
                # current_url = reverse('company:hierarchy_stages_list')
                # return redirect('company:hierarchy_stages_list', hierarchy_id=hierarchy_id)
                current_url = reverse('company:company_hierarchy_list')

            elif request.resolver_match.url_name == 'company_hierarchy_update':
                current_url = reverse('company:company_hierarchy_update', kwargs={'hierarchy_id': hierarchy_id})
            else:
                current_url = reverse('company:company_hierarchy_list')

            if not validation_response['status']:
                return JsonResponse({
                    'status':validation_response,
                    'redirect_url': current_url
                })

                
            hierarchy_id = hierarchy_id if hierarchy_id else request.POST.get('hierarchy_id')
            hierarchy_instance = InvestigationHierarchy.bells_manager.filter(id=hierarchy_id,company = company).first()
            if not hierarchy_instance:
                    return JsonResponse({'status': 'error', 'message': 'Hierarchy not found'})
                
            hierarchy_instance.levels = hierarchy_levels
            hierarchy_instance.hierarchy_timeline_days = hierarchy_timeline
            is_hierarchy_timeline_changed = int(hierarchy_instance.hierarchy_timeline_days) !=int(hierarchy_timeline)

            hierarchy_instance.save()
            
            if hierarchy_id and request.resolver_match.url_name == 'company_hierarchy_update': 
               self.remove_extra_stages(request, hierarchy_instance, hierarchy_levels)
            
            for stage_level in range(1, hierarchy_levels + 1):                
                if hierarchy_id and request.resolver_match.url_name == 'company_hierarchy_update':
                    stage_sno = stage_level
                    company=request.user.employee.company
                    
                    try:
                        stage_instance = InvestigationStage.bells_manager.filter(s_no=stage_sno, is_active = True, hierarchy__company = company).first()
                    except IndexError:
                        stage_instance = None  
                    
                    if stage_instance:
                        stage_id = stage_instance.id
                        self.update_investigation_stage(request,stage_id, hierarchy_id, stage_level, is_new_stage, is_hierarchy_timeline_changed)   
                    else:
                        is_new_stage = True    
                        next_s_no = InvestigationStage.generate_sno(hierarchy_instance)
                        stage_instance = self.create_stage(request, hierarchy_instance, employee, next_s_no, stage_level, stage_new_version, stage_id, is_new_stage )
                        self.createOwnersubsitute(request, stage_instance, stage_level)
                        self.createQuestion(request, stage_instance, stage_level)
                        self.version_upgrade_stage_list.append(stage_instance.id)
                   
                if request.resolver_match.url_name == 'add_hierarchy_stages':
                    is_new_stage = True
                    next_s_no = InvestigationStage.generate_sno(hierarchy_instance)
                    stage_instance = self.create_stage(request, hierarchy_instance, employee, next_s_no, stage_level, stage_new_version, stage_id, is_new_stage )
                    self.createOwnersubsitute(request, stage_instance, stage_level)
                    self.createQuestion(request, stage_instance, stage_level)
                    self.update_stage_overdue_date(request, hierarchy_instance)
                    

                        
            if request.resolver_match.url_name == 'company_hierarchy_update':
                status = self.upgradePendingstageversion(request, self.version_upgrade_stage_list, is_new_stage  )
                if status:
                    # if status is true
                    self.update_stage_overdue_date(request, hierarchy_instance)
                messages.info(request, 'Hierarchy updated successfully!')
            else:
                messages.info(request, 'Hierarchy created successfully!')    
            logger.info("Hierarchy saved with stages, owners, and questions.")
            return JsonResponse({
                'status': 'success',
                'message': 'Hierarchy updated successfully',
                'redirect_url': reverse('company:company_hierarchy_list')
            })
                          
        except Exception as e:
            logger.exception("Error occurred while saving hierarchy.")
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'})
        
    def createOwnersubsitute(self,request, stage_instance, stage_level):
        employee = request.user.employee
        owner_index = 1
        while True:
            owner_key = f'owner-{stage_level}-{owner_index}'
            sub_key = f'substitute-{stage_level}-{owner_index}'
            sub_time_key = f'timeline-{stage_level}-{owner_index}'
            if owner_key not in request.POST:
                break

            try:
                owner_id = request.POST.get(owner_key)
                substitute_id = request.POST.get(sub_key)
                substitute_timeline = request.POST.get(sub_time_key)

                owner = Employee.bells_manager.get(id=owner_id)
                substitute = Employee.bells_manager.get(id=substitute_id) if substitute_id else None

                instance = StageOwnerSubstitute.bells_manager.create(
                    stage=stage_instance,
                    owner=owner,
                    substitute=substitute,
                    substitute_timeline_days=substitute_timeline or 0,
                    created_by = employee,
                )
                if instance.created_at and instance.substitute and instance.substitute_timeline_days:
                    instance.subsitute_overdue_date = instance.created_at + timedelta(days=int(instance.substitute_timeline_days))
                    instance.save()

                if instance.substitute:
                    instance.is_substitute_active = True
                    instance.save()
                    
            except Exception as e:
                print('Error in creating owner/Subsitute :{e}')
                logger.info(f"Owner or substitute not found for stage {stage_level}, index {owner_index}: {e}")

            owner_index += 1
        return True
         
    def createQuestion(self,request, stage_instance, stage_level):
        employee = request.user.employee
        question_index = 1
        while True:
            question_key = f'question-{stage_level}-{question_index}'
            if question_key not in request.POST:
                break

            try:
                question_text = request.POST.get(question_key)
                if question_text:
                    InvestigationQuestion.bells_manager.create(
                        stage=stage_instance,
                        question=question_text,
                        created_by = employee

                    )
            except Exception as e:
                logger.error(f"Error while creating question for stage level {stage_level} at index {question_index}: {str(e)}")
                print('Error:{e}')
            question_index += 1

        return True
    
    def validate_total_stage_timeline_against_hierarchy(self, request, hierarchy_levels):
        total_stage_timeline_days = 0
        for i in range(1, hierarchy_levels + 1):    
            try:
                stage_timeline_str = request.POST.get(f'stage-timeline-{i}')
                total_stage_timeline_days += float(stage_timeline_str)
            except:
                logger.info(f'Invalid stage timelne value for levels  {i}')
        
        hierarchy_timeline_str = request.POST.get('hierarchy_timeline', '0')
        total_hierarchy_timeline = float(hierarchy_timeline_str)
        if total_stage_timeline_days < total_hierarchy_timeline:
            response = {
                'status': False,
                'message': 'Stage timeline is less than the total hierarchy timeline',
                'time_line_status': 'lesser'
            }
            return response
        elif total_stage_timeline_days > total_hierarchy_timeline:
            response = {
                'status': False,
                'message': 'Stage timeline is more than the total hierarchy timeline',
                'time_line_status': 'greator'

            }
            return response
        
        else:
            response = {
                'status': True,
                'message': 'Stage timeline is equal to the total hierarchy timeline',
                'time_line_status': 'equal'
            }
            return response
    
    
    def validate_unique_stage_names(self, request, company, hierarchy_id, hierarchy_levels):
        stage_names_seen = set()
        
        for i in range(1, hierarchy_levels + 1):
            stage_name = request.POST.get(f'stage-name-{i}', '').strip()
            if not stage_name:
                continue 

            if stage_name.lower() in stage_names_seen:
                return {
                    'status': False,
                    # 'message': f'Duplicate stage name "{stage_name}" found in the submitted form.',
                    'message': 'Stage name must not be unique.',
                    'error_type': 'duplicate_in_form'
                }
            stage_names_seen.add(stage_name.lower())

            # exists = InvestigationStage.bells_manager.filter(
            #     hierarchy_id=hierarchy_id,
            #     stage_name__iexact=stage_name,
            #     hierarchy__company = company
            # ).exists()
            # if exists:
            #     return {
            #         'status': False,
            #         'message': f'Stage name {stage_name} already exists for this hierarchy.',
            #         'error_type': 'duplicate_in_form'

            #     }

        return {
            'status': True,
            'message': 'All stage names are unique for the hierarchy.',
            'error_type': None
        }
            
    def update_investigation_stage(self, request, stage_id, hierarchy_id, stage_level, is_new_stage, is_hierarchy_timeline_changed):
        employee = request.user.employee
        is_stage_updated = self.is_stage_updated(request, stage_id, stage_level, is_hierarchy_timeline_changed)
        is_owner_updated = self.is_owner_updated(request, stage_id, stage_level)
        is_question_updated = self.is_question_updated(request, stage_id, stage_level)
        
        if is_stage_updated or is_owner_updated or is_question_updated:
            stage_new_version = True
            stage_instance = InvestigationStage.bells_manager.filter(id=stage_id).first()
            stage_instance.is_active = False
            stage_instance.updated_by = employee
            stage_instance.updated_at = timezone.now()
            stage_instance.save()
            hierarchy_id = hierarchy_id if hierarchy_id else request.POST.get('hierarchy_id')
            hierarchy_instance = InvestigationHierarchy.bells_manager.filter(id=hierarchy_id).first()
            next_s_no = stage_instance.s_no
            new_stage_instance = self.create_stage(request, hierarchy_instance, employee, next_s_no , stage_level, stage_new_version, stage_id, is_new_stage )
            self.createOwnersubsitute(request, new_stage_instance, stage_level)
            self.createQuestion(request, new_stage_instance, stage_level)
            self.version_upgrade_stage_list.append(new_stage_instance.id)


        else:
            #update the same stage
            investigate_instance = InvestigationStage.bells_manager.filter(id=stage_id).first()
            investigate_instance.updated_by = employee
            investigate_instance.save()
            
            # Update related StageOwnerSubstitute entries
            owner_subs = StageOwnerSubstitute.bells_manager.filter(stage=investigate_instance)
            for owner_sub in owner_subs:
                owner_sub.updated_by = employee
                owner_sub.save()

            # Update related InvestigationQuestion entries
            questions = InvestigationQuestion.bells_manager.filter(stage=investigate_instance)
            for question in questions:
                question.updated_by = employee
                question.save()
        
        return True
            
    def is_stage_updated(self,request, stage_id, stage_level, is_hierarchy_timeline_changed):
        stage_name = request.POST.get(f'stage-name-{stage_level}','').strip()
        stage_timeline = request.POST.get(f'stage-timeline-{stage_level}','').strip()
        can_change_to_inprogress_not_closed = request.POST.get(f'can-change-to-inprogress-not-closed-{stage_level}','').strip()
        can_mark_inprogress_and_closed = request.POST.get(f'can-mark-inprogress-and-closed-{stage_level}','').strip()
        can_view_incident_investigation_details = request.POST.get(f'can-view-incident-investigation-details-{stage_level}','').strip()
        stage_instance = InvestigationStage.bells_manager.filter(id = stage_id ).first()
        
        if stage_instance:
            try:
                stage_timeline_val = int(float(stage_timeline))
            except (TypeError, ValueError):
                logger.error(ValueError)
                stage_timeline_val = None
            is_stage_name_changed = stage_instance.stage_name.strip() !=stage_name
            is_stage_timeline_changed = stage_instance.stage_timeline_days != stage_timeline_val
    
            current_permission_ids = set(stage_instance.permissions.values_list('codename', flat=True))
            posted_permissions = set(filter(None, [
                can_change_to_inprogress_not_closed,
                can_mark_inprogress_and_closed,
                can_view_incident_investigation_details
            ]))
            is_permissions_changed = current_permission_ids != posted_permissions
            return is_stage_name_changed or is_stage_timeline_changed or is_permissions_changed or is_hierarchy_timeline_changed
        return False
    
    def is_owner_updated(self, request, stage_id, stage_level):
        owner_index = 1
        existing_entries = StageOwnerSubstitute.bells_manager.filter(stage_id=stage_id).order_by('id')
        posted_entries = []

        while True:
            owner_key = f'owner-{stage_level}-{owner_index}'
            sub_key = f'substitute-{stage_level}-{owner_index}'
            sub_time_key = f'timeline-{stage_level}-{owner_index}'

            if owner_key not in request.POST:
                break

            owner_id = request.POST.get(owner_key)
            substitute_id = request.POST.get(sub_key)
            substitute_timeline = request.POST.get(sub_time_key) or "0"

            posted_entries.append({
                "owner_id": int(owner_id) if owner_id else None,
                "substitute_id": int(substitute_id) if substitute_id else None,
                "substitute_timeline_days": int(float(substitute_timeline.strip())) if substitute_timeline else 0
            })

            owner_index += 1

        if len(posted_entries) != existing_entries.count():
            return True

        for existing, posted in zip(existing_entries, posted_entries):
            if (
                existing.owner_id != posted["owner_id"] or
                (existing.substitute_id or None) != posted["substitute_id"] or
                existing.substitute_timeline_days != posted["substitute_timeline_days"]
            ):
                return True

        return False

    def is_question_updated(self, request, stage_id, stage_level):
        stage = InvestigationStage.bells_manager.filter(id=stage_id).first()
        existing_questions = list(stage.investigation_questions.values_list('question', flat=True))  
        existing_questions = [q.strip() for q in existing_questions]
        posted_questions = []
        question_index = 1
        while True:
            question_key = f'question-{stage_level}-{question_index}'

            if question_key not in request.POST:
                break
            question_text = request.POST.get(question_key, '').strip()
            if question_text:
                posted_questions.append(question_text)
            question_index += 1

        return sorted(existing_questions) != sorted(posted_questions)

    def create_stage(self,request, hierarchy_instance, employee, next_s_no , stage_level, stage_new_version, stage_id, is_new_stage):
        try:
            stage_name = request.POST.get(f'stage-name-{stage_level}')
            stage_timeline = request.POST.get(f'stage-timeline-{stage_level}')
            can_change_to_inprogress_not_closed = request.POST.get(f'can-change-to-inprogress-not-closed-{stage_level}')
            can_mark_inprogress_and_closed = request.POST.get(f'can-mark-inprogress-and-closed-{stage_level}')
            can_view_incident_investigation_details = request.POST.get(f'can-view-incident-investigation-details-{stage_level}')
                
            stage_instance = InvestigationStage.bells_manager.create(
                        hierarchy=hierarchy_instance,
                        stage_name=stage_name,
                        stage_timeline_days=stage_timeline,
                        created_by = employee,
                    
                    )
            if stage_new_version:
                previous_stage_instance = InvestigationStage.bells_manager.filter(id=stage_id).first()
                previous_stage_instance.updated_at = timezone.now()
                next_version = previous_stage_instance.version + 1
                stage_instance.version = next_version
                stage_instance.s_no = next_s_no
                stage_instance.save()

            if is_new_stage:
                stage_instance.s_no = next_s_no
                stage_instance.save()
                
            permission_codenames = []
            if can_change_to_inprogress_not_closed:
                permission_codenames.append(can_change_to_inprogress_not_closed)
            if can_mark_inprogress_and_closed:
                permission_codenames.append(can_mark_inprogress_and_closed)
            if can_view_incident_investigation_details:
                permission_codenames.append(can_view_incident_investigation_details)

            if permission_codenames:
                permissions = Permission.objects.filter(codename__in=permission_codenames)
                stage_instance.permissions.set(permissions)
            
            return stage_instance
        except Exception as e:
            logger.error(f'Error while creating stage: {e}')            
            return None


    def remove_extra_stages(self, request, hierarchy_instance, hierarchy_levels):
        company = request.user.employee.company
        updated_by_employee = request.user.employee

        extra_stages = InvestigationStage.bells_manager.filter(
            hierarchy=hierarchy_instance,
            s_no__gt=hierarchy_levels,
            is_active = True,
            hierarchy__company=company
        )
        
        if extra_stages.exists():
            print(f"Deleting stages with s_no greater than {hierarchy_levels}")
            for stage in extra_stages:
                print(f"Deleting stage s_no: {stage.s_no}")
            extra_stages.update(is_active=False, updated_by=request.user.employee.id)
        else:
            print("No extra stages to delete.")
    
    def update_stage_overdue_date(self, request, hierarchy_instance):
        investigation_stages = InvestigationStage.bells_manager.filter(
        hierarchy=hierarchy_instance, is_active = True
        ).order_by('s_no')

        previous_due_date = None

        for stage in investigation_stages:
            if stage.s_no == 1:
                if request.resolver_match.url_name == 'add_hierarchy_stages':
                    due_date = stage.created_at + timedelta(days=int(stage.stage_timeline_days))
                else:
                    due_date = stage.updated_at + timedelta(days=int(stage.stage_timeline_days))

            else:
                due_date = previous_due_date + timedelta(days=int(stage.stage_timeline_days))
            stage.overdue_date = due_date
            stage.save()
            previous_due_date = due_date
        
        return 

    def upgradePendingstageversion(self, request, version_upgrade_stage_list, is_new_stage):
        if version_upgrade_stage_list:
            company = request.user.employee.company
            is_new_stage = False
            employee = request.user.employee
            stage_new_version = True
            hierarchy_id =  request.POST.get('hierarchy_id')
            hierarchy_instance = InvestigationHierarchy.bells_manager.filter(id=hierarchy_id,company=company).first()
            stage_instance =  InvestigationStage.bells_manager.filter(hierarchy=hierarchy_instance).exclude(id__in=version_upgrade_stage_list).order_by('s_no')
            stage_instance = stage_instance.filter(is_active = True)
            for stage in stage_instance:
                stage_level = stage.s_no
                stage.is_active = False
                stage.updated_by = employee
                stage.updated_at = timezone.now()
                stage.created_at = timezone.now()
                stage.save()
                next_s_no = stage.s_no
                new_stage_instance = self.create_stage(request, hierarchy_instance, employee, next_s_no , stage_level, stage_new_version, stage.id, is_new_stage )
                self.createOwnersubsitute(request, new_stage_instance, stage_level)
                self.createQuestion(request, new_stage_instance, stage_level)
            return True
        return False

@method_decorator(login_required, name='dispatch')    
class InvestigationStageAnswers(View):
    def post(self, request, incident_id=None, *args, **kwargs):
        stage_id = request.POST.get('stage_id')
        employee = request.user.employee
        company = employee.company
        if stage_id:
            
            total_forms = int(request.POST.get('form-TOTAL_FORMS', 0))
            answered_count = 0
            for i in range(total_forms):
                answer = request.POST.get(f'form-{i}-answer', '').strip()
                if answer:
                    answered_count += 1

            if answered_count == 0:
                messages.warning(request, "No questions were answered. Please provide at least one answer.")
                return HttpResponseRedirect(reverse('company:admin_incident_edit', kwargs={'incident_id': incident_id}))
            
            incident_stage_mapper_instance, created = IncidentStageMapper.bells_manager.update_or_create(
                incident_id=incident_id,
                stage_id=stage_id,
            )
            if created:
                incident_stage_mapper_instance.created_by = employee
            else:
                incident_stage_mapper_instance.updated_by = employee

            incident_stage_mapper_instance.save()
            
            self.save_answers_to_mapper(request, incident_stage_mapper_instance, employee)
            
            stage_status = self.determine_stage_status(request)
            incident_stage_mapper_instance.stage_status = stage_status
            incident_stage_mapper_instance.save()

            if stage_status == 'completed':
                incident_stage_mapper_instance.completed_at = timezone.now()
                incident_stage_mapper_instance.save()
        
        previous_url_name = resolve(urlparse(request.META.get('HTTP_REFERER', '')).path).url_name if request.META.get('HTTP_REFERER') else None
        if previous_url_name == 'admin_incident_view':
            return HttpResponseRedirect(reverse('company:admin_incident_view', kwargs={'incident_id': incident_id}))
        return HttpResponseRedirect(reverse('company:admin_incident_edit', kwargs={'incident_id': incident_id}))

    def determine_stage_status(self, request):
        """Determine if all questions have been answered"""
        stage_id = request.POST.get('stage_id')
        stage_mapper = IncidentStageMapper.bells_manager.filter(
            stage_id=stage_id
        ).first()

        total_questions = InvestigationQuestion.bells_manager.filter(
            stage_id=stage_id
        ).count()

        answered_questions = IncidentStageQuestionMapper.bells_manager.filter(
            incident_stage=stage_mapper
        ).exclude(Q(answer__isnull=True) | Q(answer__exact='')).count()

        if total_questions == answered_questions and total_questions != 0:
            return 'completed'
        else:
            return 'pending'

    def save_answers_to_mapper(self, request, incident_stage_mapper_instance, employee):
        """Save answers to the incident stage question mapper only if answer is present.
        Prevent duplicate entries for the same question."""
        total_forms = int(request.POST.get('form-TOTAL_FORMS', 0))
        saved_count = 0

        for i in range(total_forms):
            answer = request.POST.get(f'form-{i}-answer', '').strip()
            question_id = request.POST.get(f'form-{i}-question_id')

            if answer and question_id:
                obj, created = IncidentStageQuestionMapper.bells_manager.update_or_create(
                    incident_stage=incident_stage_mapper_instance,
                    question_id=question_id,
                    defaults={
                        'answer': answer,
                        'created_by': employee,
                    }
                )
                if created:
                    saved_count += 1

        return saved_count
        
    def generate_stage_completion_email_context(self, request, stage_id, incident_id):
        recipients = []

        try:
            company = request.user.employee.company.id
        except Exception as e:
            logger.error(f"[StageEmail] Failed to get company from user: {str(e)}")
            return recipients

        try:
            stage_owners = StageOwnerSubstitute.objects.select_related('owner__person').filter(stage_id=stage_id)
        except Exception as e:
            logger.error(f"[StageEmail] Failed to fetch stage owners for stage_id={stage_id}: {str(e)}")
            return recipients

        try:
            incident = Incident.bells_manager.select_related('client', 'employee').filter(id=incident_id).first()
            client = incident.client if incident else None
            incident_employee = incident.employee if incident else None
        except Exception as e:
            logger.error(f"[StageEmail] Failed to fetch incident or related data for incident_id={incident_id}: {str(e)}")
            client = None
            incident_employee = None

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
                        department_data = DepartmentClientAssignment.get_manager_department_data(employee.id, company)
                        employee_clients = ClientEmployeeAssignment.get_clients_by_employee(employee.id, company)
                        department_clients = department_data.get('clients', Employee.objects.none())
                        employees = department_data.get('employees', Employee.objects.none())
                        clients = department_clients | employee_clients

                        if client in clients and incident_employee in employees:
                            recipients.append({
                                "email": person.email,
                                "first_name": person.first_name,
                                "last_name": person.last_name,
                            })
                    except Exception as e:
                        logger.warning(f"[StageEmail] Failed to fetch department/client data for employee_id={employee.id}: {str(e)}")
                        continue

            except Exception as e:
                logger.warning(f"[StageEmail] Error processing stage owner employee_id={getattr(owner_sub.owner, 'id', 'N/A')}: {str(e)}")
                continue

        return recipients


                    

def get_user_incident_status_permission(mapper_or_stage):
    """
    Returns set of permissions the user has for a stage.
    Accepts either an IncidentStageMapper or a Stage object.
    """
    if not mapper_or_stage:
        return set()

    stage = mapper_or_stage.stage if hasattr(mapper_or_stage, 'stage') else mapper_or_stage
    
    return set(stage.permissions.values_list("codename", flat=True))

