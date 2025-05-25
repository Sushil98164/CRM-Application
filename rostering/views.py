from django.shortcuts import render
from django.views import View
from userauth.decorators import *
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rostering.forms import ShiftsForm
from django.db.models import Q
from .models import *
from django.http import JsonResponse
import dateutil.parser
from django.http import HttpResponse
from django.db.models.functions import TruncDate
import json
from django.db.models import Subquery, OuterRef
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from datetime import datetime, timedelta
from company_admin.forms import FilterQuerySetForm
from io import BytesIO
import pytz
import pandas as pd
from django.conf import settings
from userauth.models import *
from employee.models import *   
from django.db.models.functions import Lower
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from userauth.utils import has_user_permission  

    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.read_client_shift_all',
                                     'rostering.read_own_team_shift',
                                     'rostering.read_own_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',
                                     'rostering.create_shift_all',
                                     'rostering.create_own_team_shift']), name='dispatch')
class ManagerRosteringDashboard(View):
    template_name = 'rostering/admin/dashboard/rostering-dashboard.html'
    def get(self, request, *args, **kwargs):
        
        
        author = request.user.employee
        company = author.company
        shift_form = ShiftsForm(initial={
            'author': author,
            'company': company,
            'shift_category': 'Regular shift',
            'status':'Assigned',

        },company=company,request=request)
        context = {
                    'shift_form': shift_form,
                }
        if has_user_permission(request.user,'rostering.create_shift_none'):
           is_create_access = False
           context['is_create_access']=is_create_access
        return render(request, self.template_name,context)
   
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.view_all_shift_reports',
                                     'rostering.view_own_team_shift_reports',
                                     'rostering.export_all_shift_reports',
                                     'rostering.export_own_team_shift_reports',]), name='dispatch')
class ManagerShiftReportView(View):
    template_name = 'rostering/admin/shift-reports.html'

    def parse_total_hour(self, total_hour_str):
        if total_hour_str is None:
            return 0.0
        match = re.match(r"(\d+)\s*hours?\s*(?:and)?\s*(\d+)?\s*minutes?", total_hour_str.strip())
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours + minutes / 60.0
        return 0.0

    def format_hours_minutes(self, total_hours):
        hours_int = int(total_hours)
        minutes = round((total_hours - hours_int) * 60)
        if minutes >= 60:
            hours_int += 1
            minutes -= 60
        return f"{hours_int} hour {minutes} min"

    def get(self, request, *args, **kwargs):
        company = request.user.employee.company
        all_shifts = has_user_permission(request.user, 'rostering.view_all_shift_reports')
        team_shifts = has_user_permission(request.user, 'rostering.view_own_team_shift_reports')
        if team_shifts:
            manager = request.user.employee
            # Get department and client data
            department_data = DepartmentClientAssignment.get_manager_department_data(
                manager_id=manager.id,
                company_id=company.id
            )
            client_data = department_data['clients']
            managed_employees = department_data['employees']
            # Filter shifts for managed employees and clients
            shifts = Shifts.bells_manager.filter(
                company=company,
                status='Completed',
                employee__in=managed_employees,
                client__in=client_data
            ).values(
                'id',
                'employee__id', 'client__id',
                'employee__person__first_name', 'employee__person__last_name',
                'client__person__first_name', 'client__person__last_name',
                'shift_type', 'total_hour', 'start_date_time', 'end_date_time'
            )
        elif all_shifts:
            shifts = Shifts.bells_manager.filter(company=company, status='Completed').values(
                'id',
                'employee__id', 'client__id',
                'employee__person__first_name', 'employee__person__last_name',
                'client__person__first_name', 'client__person__last_name',
                'shift_type', 'total_hour', 'start_date_time', 'end_date_time'
            )
        else:
            shifts = Shifts.bells_manager.none()
            
        shifts = filter_shifts_queryset(queryset=shifts, request=request)

        reset_filter = False
        if request.GET:
            reset_filter = True

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        employee_client_name = request.GET.get('employee_client')
        all_employees = request.GET.get('all_employees')
        all_clients = request.GET.get('all_clients')

        context = {}

        if all_employees or employee_client_name == 'employee' or not employee_client_name:
            aggregated_data = {}
            for shift in shifts:
                shift_id = shift['id']
                employee_id = shift['employee__id']
                employee_name = f"{shift['employee__person__first_name']} {shift['employee__person__last_name']}"
                shift_type = shift['shift_type']
                total_hour_str = shift['total_hour']
                if employee_id not in aggregated_data:
                    aggregated_data[employee_id] = {
                        'shift_ids': [],
                        'employee_name': employee_name,
                        'morning_hours': 0.0,
                        'evening_hours': 0.0,
                        'night_hours': 0.0,
                        'open_shift_hours': 0.0,
                        'total_hours': 0.0
                    }
                aggregated_data[employee_id]['shift_ids'].append(shift_id)
                total_hours = self.parse_total_hour(total_hour_str)
                if shift_type == 'Morning':
                    aggregated_data[employee_id]['morning_hours'] += total_hours
                elif shift_type == 'Evening':
                    aggregated_data[employee_id]['evening_hours'] += total_hours
                elif shift_type == 'Night':
                    aggregated_data[employee_id]['night_hours'] += total_hours
                elif shift_type == 'Open shift':
                    aggregated_data[employee_id]['open_shift_hours'] += total_hours
                aggregated_data[employee_id]['total_hours'] += total_hours
            formatted_data = [
                {
                    'shift_ids': data['shift_ids'],
                    'employee_name': data['employee_name'],
                    'morning_hours': self.format_hours_minutes(data['morning_hours']),
                    'evening_hours': self.format_hours_minutes(data['evening_hours']),
                    'night_hours': self.format_hours_minutes(data['night_hours']),
                    'open_shift_hours': self.format_hours_minutes(data['open_shift_hours']),
                    'total_hours': self.format_hours_minutes(data['total_hours'])
                } for data in aggregated_data.values()
            ]
            context = {
                'data': formatted_data,
                'start_date': start_date,
                'end_date': end_date,
                'is_employee': True,
                'reset_filter': reset_filter
            }
        elif all_clients or employee_client_name == 'client':
            client_aggregated_data = {}
            for shift in shifts:
                shift_id = shift['id']
                client_id = shift['client__id']
                client_name = f"{shift['client__person__first_name']} {shift['client__person__last_name']}"
                shift_type = shift['shift_type']
                total_hour_str = shift['total_hour']
                if client_id not in client_aggregated_data:
                    client_aggregated_data[client_id] = {
                        'shift_ids': [],
                        'client_name': client_name,
                        'morning_hours': 0.0,
                        'evening_hours': 0.0,
                        'night_hours': 0.0,
                        'open_shift_hours': 0.0,
                        'total_hours': 0.0
                    }
                client_aggregated_data[client_id]['shift_ids'].append(shift_id)
                total_hours = self.parse_total_hour(total_hour_str)
                if shift_type == 'Morning':
                    client_aggregated_data[client_id]['morning_hours'] += total_hours
                elif shift_type == 'Evening':
                    client_aggregated_data[client_id]['evening_hours'] += total_hours
                elif shift_type == 'Night':
                    client_aggregated_data[client_id]['night_hours'] += total_hours
                elif shift_type == 'Open shift':
                    client_aggregated_data[client_id]['open_shift_hours'] += total_hours
                client_aggregated_data[client_id]['total_hours'] += total_hours
            formatted_data = [
                {
                    'shift_ids': data['shift_ids'],
                    'client_name': data['client_name'],
                    'morning_hours': self.format_hours_minutes(data['morning_hours']),
                    'evening_hours': self.format_hours_minutes(data['evening_hours']),
                    'night_hours': self.format_hours_minutes(data['night_hours']),
                    'open_shift_hours': self.format_hours_minutes(data['open_shift_hours']),
                    'total_hours': self.format_hours_minutes(data['total_hours'])
                } for data in client_aggregated_data.values()
            ]
            context = {
                'data': formatted_data,
                'start_date': start_date,
                'end_date': end_date,
                'is_employee': False,
                'reset_filter': reset_filter
            }

        return render(request, self.template_name, context)


def filter_shifts_queryset(queryset=None, request=None):
    if queryset is None or request is None:
        return queryset

    employee_client_name = request.GET.get('employee_client')
    employee_client_id = request.GET.get('name_select')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    filter_conditions = Q()

    if employee_client_name == 'employee':
        if employee_client_id:
            filter_conditions &= Q(employee__id=employee_client_id)
        else:
            pass
    elif employee_client_name == 'client':
        if employee_client_id:
            filter_conditions &= Q(client__id=employee_client_id)
        else:
            pass

    if start_date:
        start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        filter_conditions &= Q(start_date_time__gte=start_date)
    if end_date:
        end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1))
        filter_conditions &= Q(end_date_time__lte=end_date)

    queryset = queryset.filter(filter_conditions)

    return queryset

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.create_shift_all',
                                     'rostering.create_own_team_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class FilterEmployeesByClientView(View):
    def get(self, request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        company = request.user.employee.company
        
        
        has_team = has_user_permission(request.user,'rostering.create_own_team_shift')
               
        if has_team:
            employee_id = request.user.employee.id
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee_id,company_id=company.id)
            employees = department_data['employees'].filter(
                client_employee_assignments__client_id = client_id
            ).distinct().order_by(Lower('person__first_name'))

        else:
            employees = ClientEmployeeAssignment.get_employees_by_client(client_id=client_id,company_id=company.id).order_by(Lower('person__first_name')).distinct() 


        employees_data = [{'id': employee.id, 'name': f"{employee.person.first_name} {employee.person.last_name}"} for employee in employees]
        return JsonResponse({'employees': employees_data}, safe=False)






@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.read_client_shift_all',
                                     'rostering.read_own_team_shift',
                                     'rostering.read_own_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class ShiftDetails(View):
    def get(self, request, *args, **kwargs):
        status = request.GET.get('status')
        company = request.user.employee.company
        start_date_str = request.GET.get('start_date')

        # Initialize update button permissions
        show_update_button_for = set()
        show_eye_button_for = set()
        update_all_shifts = has_user_permission(request.user,'rostering.update_shift_all')     
        update_team_shifts = has_user_permission(request.user,'rostering.update_own_team_shift')
        own_shifts = has_user_permission(request.user,'rostering.read_own_shift')     
        team_shifts = has_user_permission(request.user,'rostering.read_own_team_shift')
        delete_shift_all = has_user_permission(request.user,'rostering.delete_shift_all')
        delete_team_shift = has_user_permission(request.user,'rostering.delete_own_team_shift')
                                           
        if start_date_str:
            try:
                start_date = dateutil.parser.isoparse(start_date_str)
                if own_shifts:
                    shifts = Shifts.bells_manager.filter(
                        Q(status=status),
                        Q(start_date_time__date=start_date.date()),
                        company=company,
                        employee = request.user.employee
                    ).values(
                        'id',
                        'client__person__first_name',
                        'client__person__last_name',
                        'start_date_time',
                        'end_date_time',
                        'client__residential_address',
                    )
                elif team_shifts:
                    department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
                    clients = department_data['clients']
                    employee = department_data['employees']
                    
                    client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=request.user.employee.id, company_id=company.id)
                    all_clients = clients | client_data                     
                    shifts = Shifts.bells_manager.filter(
                        Q(status=status),
                        Q(start_date_time__date=start_date.date()),
                        company=company,
                        client__in = all_clients,
                        employee__in=employee
                    ).values(
                        'id',
                        'client__person__first_name',
                        'client__person__last_name',
                        'start_date_time',
                        'end_date_time',
                        'client__residential_address',
                    )
                else:
                    shifts = Shifts.bells_manager.filter(
                        Q(status=status),
                        Q(start_date_time__date=start_date.date()),
                        company=company,
                    ).values(
                        'id',
                        'client__person__first_name',
                        'client__person__last_name',
                        'start_date_time',
                        'end_date_time',
                        'client__residential_address',
                    )

                # Calculate which shifts should show update button
                if update_all_shifts or delete_shift_all:
                    filter_shifts = Shifts.bells_manager.filter(
                        company=company
                    ).values_list('id', flat=True)
                    show_update_button_for.update(filter_shifts)
                    show_eye_button_for.update(filter_shifts)
                
                elif update_team_shifts or delete_team_shift:
                    manager = request.user.employee
                    department_data = DepartmentClientAssignment.get_manager_department_data(
                        manager_id=manager.id,
                        company_id=company.id
                    )
                    client_data = department_data['clients']
                    managed_employees = department_data['employees']
                    filter_shifts = Shifts.bells_manager.filter(
                        employee__in=managed_employees,     
                        client__in=client_data,
                        company=company, 
                        is_deleted=False
                    ).values_list('id', flat=True)
                    show_update_button_for.update(filter_shifts)
                    show_eye_button_for.update(filter_shifts)
                    
                               
                shift_details = []
                for shift in shifts:
                    client_first_name = shift['client__person__first_name']
                    client_last_name = shift['client__person__last_name']
                    client_full_name = f"{client_first_name} {client_last_name}"
                    shift_id = shift['id']
                    address = shift['client__residential_address']
                    
                    start_datetime = timezone.localtime(shift['start_date_time'])
                    end_datetime = timezone.localtime(shift['end_date_time'])
                    shift_details.append({
                        'clientName': client_full_name,
                        'shift_id': shift_id,
                        'startDateTime': start_datetime.strftime('%B %d, %Y, %I:%M %p'),
                        'endDateTime': end_datetime.strftime('%B %d, %Y, %I:%M %p'),
                        'address': address,
                        'can_update': shift_id in show_update_button_for,
                        'can_see' : shift_id in show_eye_button_for,
                    })
                return JsonResponse({
                    'shifts': shift_details,
                }, safe=False)
            except ValueError:
                return JsonResponse({'error': 'Invalid start date format'}, status=400)

        return JsonResponse({'error': 'Invalid start date'}, status=400)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.read_client_shift_all',
                                     'rostering.read_own_team_shift',
                                     'rostering.read_own_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class EditShiftDetailsView(View):
    def get(self, request, *args, **kwargs):
        author = request.user.employee
        company = author.company
        shift_id = request.GET.get('shiftId')
        existing_shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
        update_all_shifts = has_user_permission(request.user,'rostering.update_shift_all')
        update_team_shifts = has_user_permission(request.user,'rostering.update_own_team_shift')
        delete_shift_all = has_user_permission(request.user,'rostering.delete_shift_all')     
        delete_team_shift = has_user_permission(request.user,'rostering.delete_own_team_shift') 
        
        show_delete_button_for = set()
        show_update_button_for = set()

        if delete_shift_all or update_all_shifts:
            shifts_ids = Shifts.bells_manager.filter(company=company).values_list('id', flat=True)
            if delete_shift_all:
                show_delete_button_for = set(shifts_ids) 
            if update_all_shifts:
                show_update_button_for = set(shifts_ids)  
        
        if delete_team_shift or update_team_shifts:
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            client_ids =  department_data['clients'].values_list('id', flat = True)
            employee_ids  = department_data['employees'].values_list('id', flat = True)
            if client_ids:
                shifts_ids = Shifts.bells_manager.filter(client__in = client_ids, employee__in = employee_ids, company=company).values_list('id', flat=True)
                # show_delete_button_for = set(shifts_ids)                
                if update_team_shifts:
                    show_update_button_for = set(shifts_ids) 
                if delete_team_shift:
                    show_delete_button_for = set(shifts_ids) 
        
        shift_form = ShiftsForm(instance=existing_shift,initial={
            'author': author,
            'company': company,
            'shift_category': 'Regular shift',
            'shift_id':shift_id,
            'status':existing_shift.status,
        },company=company,request=request)

        shift_form.fields['employee'].queryset = ClientEmployeeAssignment.get_employees_by_client(client_id=existing_shift.client.id,company_id=company.id).order_by(Lower('person__first_name')).distinct() 

        form_html = render(request, 'rostering/admin/dashboard/edit-shift-form.html', {'shift_form': shift_form,'show_delete_button_for':show_delete_button_for,'show_update_button_for':show_update_button_for,'shift_id':int(shift_id)})
        return HttpResponse(form_html)
    
    
# @method_decorator(login_required, name='dispatch')
# class ShiftsCalendar(View):
#     def get(self, request, *args, **kwargs):     
#         month = request.GET.get('month')
#         company=request.user.employee.company
#         current_view = request.GET.get('calendar_view')
        
#         all_shifts = has_user_permission(request.user,'rostering.read_client_shift_all')     
#         team_shifts = has_user_permission(request.user,'rostering.read_own_team_shift')     
#         own_shifts = has_user_permission(request.user,'rostering.read_own_team_shift')     
        
#         update_all_shifts = has_user_permission(request.user,'rostering.update_shift_all')     
#         update_team_shifts = has_user_permission(request.user,'rostering.update_own_team_shift')     

#         if all_shifts:
#             shifts = Shifts.bells_manager.filter(company=company)
            
#         elif team_shifts:
#             manager = request.user.employee
#             department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = manager.id,company_id=company.id)
#             client_data =  department_data['clients']
#             managed_employees = department_data['employees']
#             shifts = Shifts.bells_manager.filter(
#                 employee__in=managed_employees,     
#                 client__in=client_data,
#                 company=company, 
#                 is_deleted=False
#             )
            
        
#         elif own_shifts:
#             # return redirect('rostering:employee_shifts_dashboard')
#             employee = request.user.employee
#             company=employee.company            
#             client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by('-created_at')
#             shifts = Shifts.bells_manager.filter(
#                 employee=employee, 
#                 client__in=client_data,
#                 company=company, 
#                 is_deleted=False
#             )

#         else:
#             shifts = Shifts.bells_manager.none()
            
#         show_update_button_for = set()
        
#         if update_all_shifts:
#             filter_shifts = Shifts.bells_manager.filter(company=company).values_list('id',flat=True)
#             show_update_button_for.update(filter_shifts)
        
#         elif update_team_shifts:
#             manager = request.user.employee
#             department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = manager.id,company_id=company.id)
#             client_data =  department_data['clients']
#             managed_employees = department_data['employees']
#             filter_shifts = Shifts.bells_manager.filter(
#                 employee__in=managed_employees,     
#                 client__in=client_data,
#                 company=company, 
#                 is_deleted=False
#             ).values_list('id',flat=True)
#             show_update_button_for.update(filter_shifts)
#         else:
#             filter_shifts = Shifts.bells_manager.none()
#             show_update_button_for.update(filter_shifts)


#         if month:
#             shifts=shifts.filter(start_date_time__month=month)
#         else:
#             shifts=shifts
#         assigned_obj = shifts.filter(status='Assigned')
#         ongoing_obj = shifts.filter(status='Ongoing')
#         pending_obj = shifts.filter(status='Pending')
#         completed_obj = shifts.filter(status='Completed')
        
#         shifts_data = {
#             'assigned_shifts': {},
#             'ongoing_shifts': {},
#             'completed_shifts': {},
#             'pending_shifts': {},
#             'current_view':current_view,
#             'show_update_button_for':list(show_update_button_for)
#         }
#         if assigned_obj.count() > 0:
#             shifts_queryset = self.queryset_data(assigned_obj)
#             self.populate_shifts_data(shifts_queryset, 'assigned_shifts', shifts_data)

#         if ongoing_obj.count() > 0:
#             ongoing_queryset = self.queryset_data(ongoing_obj)
#             self.populate_shifts_data(ongoing_queryset, 'ongoing_shifts', shifts_data)
        
#         if pending_obj.count() > 0:
#             pending_queryset = self.queryset_data(pending_obj)
#             self.populate_shifts_data(pending_queryset, 'pending_shifts', shifts_data)

#         if completed_obj.count() > 0:
#             completed_queryset = self.queryset_data(completed_obj)
#             self.populate_shifts_data(completed_queryset, 'completed_shifts', shifts_data)

#         json_data = json.dumps(shifts_data)
#         return JsonResponse(json_data, safe=False)

#     def queryset_data(self, objs):
      
#         shifts_queryset = objs.order_by('start_date_time')

#         return shifts_queryset

 
#     def populate_shifts_data(self, status_obj, status_name, shifts_data):
#         for index, shift in enumerate(status_obj):
#             start_time_local = timezone.localtime(shift.start_date_time)
#             end_time_local = timezone.localtime(shift.end_date_time)

#             shift_info = {
#                 'start_date_time': start_time_local.isoformat(),
#                 'end_date_time': end_time_local.isoformat(),
#                 'title': shift.status,
                
#             }
#             shifts_data[status_name][index] = shift_info
            


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.read_client_shift_all',
                                     'rostering.read_own_team_shift',
                                     'rostering.read_own_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',
                                    ]), name='dispatch')
class ShiftsCalendar(View):
    def get(self, request, *args, **kwargs):   
          
        month = request.GET.get('month')
        company=request.user.employee.company
        current_view = request.GET.get('calendar_view')
        
        all_shifts = has_user_permission(request.user,'rostering.read_client_shift_all')     
        team_shifts = has_user_permission(request.user,'rostering.read_own_team_shift')     
        own_shifts = has_user_permission(request.user,'rostering.read_own_shift')     
        
   

        if all_shifts:
            shifts = Shifts.bells_manager.filter(company=company)
            
        elif team_shifts:
            manager = request.user.employee
            # department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = manager.id,company_id=company.id)
            # client_data =  department_data['clients']
            # client_ids_1 = client_data.values_list('id', flat=True)
            
            # client_data_2 = ClientEmployeeAssignment.get_clients_by_employee(employee_id=manager.id, company_id=company.id)
            # client_ids_2 = set(client_data_2.values_list('id', flat=True))
            # all_client_ids = client_ids_1 | client_ids_2  
            # client_ids = list(all_client_ids)
            # Get clients assigned through department
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager.id, company_id=company.id)
            client_data = department_data['clients']
            employee_data = department_data['employees']
            # client_ids_1 = set(client_data.values_list('id', flat=True))  
            print(employee_data,"heloooo")
            client_data_2 = ClientEmployeeAssignment.get_clients_by_employee(employee_id=manager.id, company_id=company.id)
            # client_ids_2 = set(client_data_2.values_list('id', flat=True)) 

            # client_ids = list(client_ids_1 | client_ids_2)  
            # employee_query_set = Employee.bells_manager.filter(id=request.user.employee.id)
            # employee_data = employee_data.union(employee_query_set)
            # managed_employees = Employee.bells_manager.filter(
            #                         Q(client_employee_assignments__client_id__in=client_ids),
            #                         client_employee_assignments__is_deleted=False
            #                     ).distinct().order_by(Lower('person__first_name'))
            all_clients = client_data | client_data_2 
    
            shifts = Shifts.bells_manager.filter(
                employee__in=employee_data,     
                client__in=all_clients,
                company=company, 
                is_deleted=False
            )
            
        
        elif own_shifts:
            # return redirect('rostering:employee_shifts_dashboard')
            employee = request.user.employee
            company=employee.company            
            client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by('-created_at')
            shifts = Shifts.bells_manager.filter(
                employee=employee, 
                client__in=client_data,
                company=company, 
                is_deleted=False
            )

        else:
            shifts = Shifts.bells_manager.none()
            
        

        if month:
            shifts=shifts.filter(start_date_time__month=month)
        else:
            shifts=shifts
        assigned_obj = shifts.filter(status='Assigned')
        ongoing_obj = shifts.filter(status='Ongoing')
        pending_obj = shifts.filter(status='Pending')
        completed_obj = shifts.filter(status='Completed')
        
        shifts_data = {
            'assigned_shifts': {},
            'ongoing_shifts': {},
            'completed_shifts': {},
            'pending_shifts': {},
            'current_view':current_view,
        }
        if assigned_obj.count() > 0:
            shifts_queryset = self.queryset_data(assigned_obj)
            self.populate_shifts_data(shifts_queryset, 'assigned_shifts', shifts_data)

        if ongoing_obj.count() > 0:
            ongoing_queryset = self.queryset_data(ongoing_obj)
            self.populate_shifts_data(ongoing_queryset, 'ongoing_shifts', shifts_data)
        
        if pending_obj.count() > 0:
            pending_queryset = self.queryset_data(pending_obj)
            self.populate_shifts_data(pending_queryset, 'pending_shifts', shifts_data)

        if completed_obj.count() > 0:
            completed_queryset = self.queryset_data(completed_obj)
            self.populate_shifts_data(completed_queryset, 'completed_shifts', shifts_data)
        
 

        json_data = json.dumps(shifts_data)
        return JsonResponse(json_data, safe=False)

    def queryset_data(self, objs):
      
        shifts_queryset = objs.order_by('start_date_time')

        return shifts_queryset

 
    def populate_shifts_data(self, status_obj, status_name, shifts_data):
        for index, shift in enumerate(status_obj):
            start_time_local = timezone.localtime(shift.start_date_time)
            end_time_local = timezone.localtime(shift.end_date_time)

            shift_info = {
                'start_date_time': start_time_local.isoformat(),
                'end_date_time': end_time_local.isoformat(),
                'title': shift.status,

                
            }
            shifts_data[status_name][index] = shift_info
            


    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.create_shift_all',
                                     'rostering.create_own_team_shift',]), name='dispatch')
class CreateEmployeeShift(View):
    def post(self, request, *args, **kwargs):
        shift_form = ShiftsForm(request.POST,request=request)
      
        if shift_form.is_valid():
            try:
                shift_form.save()
                return JsonResponse({'success': True}, status=200)
            except ValidationError as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
        else:
            errors = shift_form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors}, status=400)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.create_shift_all',
                                     'rostering.create_own_team_shift',
                                     'rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class UnassignedShiftsClientsEmployeeList(View):
    def get(self, request, *args, **kwargs):
        if request.method == 'GET':
            date = request.GET.get('date')
            month = request.GET.get('month')
            selection = request.GET.get('selection')
            company = request.user.employee.company
            if date and month:
                if selection == 'employee':
                    employee_obj = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))

                    employees_with_shifts = employee_obj.filter(
                        Q(shifts__status='Ongoing') | Q(shifts__status='Assigned'),
                        shifts__start_date_time__date=date,
                        shifts__start_date_time__month=month,
                        shifts__is_deleted=False
                    ).distinct()

                    employees_without_shifts = employee_obj.exclude(
                        id__in=employees_with_shifts.values_list('id', flat=True)
                    )
                    data = list(employees_without_shifts.values('id', 'person__first_name', 'person__last_name'))
                elif selection == 'client':
                    client_obj = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
                    clients_with_shifts = client_obj.filter(
                        shifts__start_date_time__date=date,
                        shifts__start_date_time__month=month,
                        shifts__is_deleted = False

                    ).distinct()

                    clients_without_shifts = client_obj.exclude(
                        id__in=clients_with_shifts.values_list('id', flat=True)
                    )
                    data = list(clients_without_shifts.values('id', 'person__first_name', 'person__last_name'))
                else:
                    return JsonResponse({'error': 'Invalid selection'}, status=400)
            else:
                if selection == 'employee':
                    employees_without_shifts = Employee.bells_manager.filter(company=company, shifts__isnull=True, shifts__is_deleted = False)
                    data = list(employees_without_shifts.values('id', 'person__first_name', 'person__last_name'))
                elif selection == 'client':
                    client_without_shifts = Client.bells_manager.filter(company=company, shifts__isnull=True, shifts__is_deleted = False)
                    data = list(client_without_shifts.values('id', 'person__first_name', 'person__last_name'))
                else:
                    return JsonResponse({'error': 'Invalid selection'}, status=400)

            return JsonResponse({'data': data})

        return JsonResponse({'error': 'Method Not Allowed'}, status=405)

    
    
@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class EditFilterEmployeesByClient(View):
    def get(self, request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        company = request.user.employee.company
        
        if request.user.employee.role == 1:
            employees = ClientEmployeeAssignment.get_employees_by_client(client_id=client_id,company_id=company.id).order_by(Lower('person__first_name')).distinct() 
        elif request.user.employee.role == 2:
            manager_employee = request.user.employee
            department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager_employee.id,company_id=company.id)
            department_employees = department_data['employees']
            employees = ClientEmployeeAssignment.get_employees_by_client(client_id=client_id,company_id=company.id).filter(
                employee__in=department_employees
            ).order_by(Lower('person__first_name')).distinct()
            
        employees_data = [{'id': employee.id, 'name': f"{employee.person.first_name} {employee.person.last_name}"} for employee in employees]
        return JsonResponse({'employees': employees_data}, safe=False)


@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.update_shift_all',
                                     'rostering.update_own_team_shift',]), name='dispatch')
class EditEmployeeShift(View):
    def post(self, request, *args, **kwargs):
        shift_id = request.POST.get('shift_id')
        company=request.user.employee.company
        existing_shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
        
        if existing_shift:
            shift_form = ShiftsForm(request.POST, instance=existing_shift,request=request)
            
            if shift_form.is_valid():
                try:
                    shift_instance = shift_form.save(commit=False)
                    progress_note = DailyShiftCaseNote.bells_manager.filter(shift=shift_instance.id).first()
                    if progress_note:
                        progress_note.client = shift_instance.client
                        progress_note.employee = shift_instance.employee
                        progress_note.start_date_time = shift_instance.start_date_time
                        progress_note.end_date_time = shift_instance.end_date_time
                        progress_note.save()
                        total_hour = shift_instance.calculate_total_hour(progress_note.start_date_time,progress_note.end_date_time)
                        shift_instance.total_hour= total_hour
                    shift_instance.save()

                    return JsonResponse({'success': True})
                except ValidationError as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
            else:
                errors = shift_form.errors.as_json()
                return JsonResponse({'success': False, 'errors': errors}, safe=False, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Shift not found'}, status=404)



@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['rostering.delete_shift_all',
                                     'rostering.delete_own_team_shift',]), name='dispatch')
class DeleteShift(View):
    def get(self, request, *args, **kwargs):
        shift_id = request.GET.get('shift_id')
        company=request.user.employee.company
        shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
        if shift:
            if shift.status == 'Ongoing':
                message = 'You cannot delete an ongoing shift.'
                return JsonResponse({'success': False, 'error': message}, status=400)
            else:
                shift.is_deleted =True
                shift.save()
                DailyShiftCaseNote.objects.filter(shift=shift).update(is_deleted=True)

                return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Shift not found'}, status=404)


#Employee functions start from here   
@method_decorator(login_required, name='dispatch')
class EmployeeShiftsDashboard(View):
    template_name = 'rostering/employee/dashboard/shift-dashboard.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    


@method_decorator(login_required, name='dispatch')
# @method_decorator(check_permissions(['company_admin.view_progress_notes_own','company_admin.update_progress_notes_own']), name='dispatch')
class EmployeeShiftsListView(View):
    template_name = "company_admin/dashboard/daily-shift-note-dashboard.html"
    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by('-created_at')
             
        shifts = Shifts.bells_manager.filter(
            employee=employee, 
            client__in=client_data,
            company=company
        )
        
        if 'dailyshift_list_employee' in request.resolver_match.url_name:

            shifts = shifts.filter(Q(status='Completed')|Q(status='Pending'), employee=employee).order_by('-created_at')
        else:
            shifts = shifts.filter(Q(status='Ongoing') | Q(status='Assigned') , employee=employee).order_by('-status', '-updated_at')
        
        items_per_page = 10
        page = request.GET.get('page', 1)
        paginator = Paginator(shifts, items_per_page)
        try:
            shifts = paginator.page(page)
        except PageNotAnInteger:
            shifts = paginator.page(1)
        except EmptyPage:
            shifts = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((shifts.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'shifts': shifts,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
        }
        return render(request, self.template_name,context)




@method_decorator(login_required, name='dispatch')
class FetchEmployeeShiftsToCalendar(View):
    def get(self, request):
        employee = request.user.employee
        company=employee.company
        calendar_view = request.GET.get('calendar_view')
        
        client_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by('-created_at')
                
        shifts = Shifts.bells_manager.filter(
            employee=employee, 
            client__in=client_data,
            company=company, 
            is_deleted=False
        ).values(
            'client__person__first_name',
            'client__person__last_name',
            'start_date_time',
            'end_date_time',
            'id'
        )

        shifts_data = []
   
        for shift in shifts:
            start_datetime = timezone.localtime(shift['start_date_time'])
            end_datetime = timezone.localtime(shift['end_date_time'])
            full_name = f"{shift['client__person__first_name']} {shift['client__person__last_name']}"
            shift_data = {
                'start_date_time':start_datetime.isoformat(),
                'end_date_time': end_datetime.isoformat(),
                'title': full_name,
                'shift_id': shift['id'],
                
            }
            shift_data['calendar_view'] = calendar_view

            shifts_data.append(shift_data)
            
        return JsonResponse(shifts_data, safe=False)
    


@method_decorator(login_required, name='dispatch')
class EmployeeShiftDetails(View):
    def get(self, request, *args, **kwargs):
        shift_id = request.GET.get('shift')
        company=request.user.employee.company

        if shift_id:
            try:
                shifts = Shifts.bells_manager.filter(id=shift_id,company=company).values(
                    'client__person__first_name',
                    'client__person__last_name',
                    'start_date_time',
                    'end_date_time',
                    'client__residential_address',
                )

                shift_details = []

                for shift in shifts:
                    start_datetime = timezone.localtime(shift['start_date_time'])
                    end_datetime = timezone.localtime(shift['end_date_time'])

                    client_first_name = shift['client__person__first_name']
                    client_last_name = shift['client__person__last_name']
                    client_full_name = f"{client_first_name} {client_last_name}"
                    address = shift['client__residential_address']

                    shift_details.append({
                        'clientName': client_full_name,
                        'address': address,
                        'startDateTime': start_datetime.strftime('%B %d, %Y, %I:%M %p'),
                        'endDateTime': end_datetime.strftime('%B %d, %Y, %I:%M %p'),
                    })

                return JsonResponse({'shifts': shift_details}, safe=False)
            except Shifts.DoesNotExist:
                return JsonResponse({'error': 'Shift ID does not exist'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)

        return JsonResponse({'error': 'Invalid shift ID'}, status=400)



                                                 
def GetEmployeeClient(request):
    if request.method == 'GET':
        employee = request.user.employee
        company = employee.company
        employee_type = request.GET.get('employee')
        
        view_all_perm = has_user_permission(request.user, 'rostering.view_all_shift_reports')
        view_team_perm = has_user_permission(request.user, 'rostering.view_own_team_shift_reports')
        
        all_employees = None
        all_clients = None

        if employee_type == 'employee':
            if view_all_perm:
                all_employees = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            elif view_team_perm:
                department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
                all_employees = department_data.get('employees', Employee.bells_manager.none())
            else:
                all_employees = Employee.bells_manager.filter(id=employee.id)
            serialized_employees = [{'id': employee.pk, 'name': f"{employee.person.first_name} {employee.person.last_name}"} for employee in all_employees]
            return JsonResponse({'employees': serialized_employees})
        elif employee_type == 'client':
            if view_all_perm:
                all_clients = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            elif view_team_perm:
                department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=employee.id, company_id=company.id)
                team_clients = department_data.get('clients', Client.bells_manager.none())
                own_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id, company_id=company.id)
                all_clients = team_clients | own_clients
            else:
                all_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id, company_id=company.id)
            serialized_clients = [{'id': client.pk, 'name': f"{client.person.first_name} {client.person.last_name}"} for client in all_clients]
            return JsonResponse({'clients': serialized_clients})
        else:
            return JsonResponse({'error': 'Invalid employee type'})
    else:
        return JsonResponse({'error': 'Invalid request method'})



@login_required
@check_permissions(['rostering.export_all_shift_reports', 'rostering.export_own_team_shift_reports'])
def downloadShiftsReport(request):
    file_type = request.GET.get('file_type')
    shift_ids_str = request.GET.get('shiftIdElements_ids')
    is_employee_str = request.GET.get('is_employee')  

    is_employee = is_employee_str.lower() == 'true'
    if not shift_ids_str:
        return HttpResponse(status=400, content="Shift IDs are required")

    shift_ids_str = shift_ids_str.replace('[', '').replace(']', '')
    try:
        shift_ids = [int(id.strip()) for id in shift_ids_str.split(',')]
    except ValueError as e:
        return HttpResponse(status=400, content=f"Invalid shift ID format: {e}")

    company = request.user.employee.company
    
    has_team = has_user_permission(request.user, 'rostering.export_own_team_shift_reports')
    has_all = has_user_permission(request.user, 'rostering.export_all_shift_reports')
    
    if has_team:
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = request.user.employee.id,company_id=company.id)
            employee_data = manager_data['employees']
            client_data = manager_data['clients']   
            shifts = Shifts.bells_manager.filter(client__in = client_data, employee__in = employee_data ,status="Completed")
    elif has_all:
        shifts = Shifts.bells_manager.filter(id__in=shift_ids, company=company)
    
    else:
        shifts = Shifts.bells_manager.none()

    if is_employee:
        aggregated_data = {}
        sno=1
        for shift in shifts.values(
            'id',
            'employee__id',
            'employee__person__first_name',
            'employee__person__last_name',
            'shift_type',
            'total_hour'
        ):
            employee_id = shift['employee__id']
            employee_name = f"{shift['employee__person__first_name']} {shift['employee__person__last_name']}"
            shift_type = shift['shift_type']
            total_hour_str = shift['total_hour']
            if employee_id not in aggregated_data:
                aggregated_data[employee_id] = {
                    'sno': sno,
                    'shift_ids': [],
                    'employee_name': employee_name,
                    'morning_hours': 0.0,
                    'evening_hours': 0.0,
                    'night_hours': 0.0,
                    'open_shift_hours': 0.0,
                    'total_hours': 0.0
                }
                sno+=1
            aggregated_data[employee_id]['shift_ids'].append(shift['id'])
            total_hours = parse_total_hour(total_hour_str)
            if shift_type == 'Morning':
                aggregated_data[employee_id]['morning_hours'] += total_hours
            elif shift_type == 'Evening':
                aggregated_data[employee_id]['evening_hours'] += total_hours
            elif shift_type == 'Night':
                aggregated_data[employee_id]['night_hours'] += total_hours
            elif shift_type == 'Open shift':
                    aggregated_data[employee_id]['open_shift_hours'] += total_hours   
            aggregated_data[employee_id]['total_hours'] += total_hours

        employee_df = pd.DataFrame(aggregated_data.values())
        if not employee_df.empty:
            employee_df = employee_df[[
                'sno','employee_name', 'morning_hours', 'evening_hours', 'night_hours', 'open_shift_hours' ,'total_hours'
            ]]

            employee_df['morning_hours'] = employee_df['morning_hours'].apply(format_hours_minutes)
            employee_df['evening_hours'] = employee_df['evening_hours'].apply(format_hours_minutes)
            employee_df['night_hours'] = employee_df['night_hours'].apply(format_hours_minutes)
            employee_df['open_shift_hours'] = employee_df['open_shift_hours'].apply(format_hours_minutes)
            employee_df['total_hours'] = employee_df['total_hours'].apply(format_hours_minutes)

            employee_df.columns = [
            'S.no', 'Employee name', 'Morning hours', 'Evening hours', 'Night hours','Open shift hours' ,'Total hours'
            ]
        else:
            employee_df = pd.DataFrame(columns=['S.no', 'Employee name', 'Morning hours', 'Evening hours', 'Night hours','Open shift hours' ,'Total hours'])
            
            
        if file_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
            filename = f'employee_shifts_report_{timestamp}.csv'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-File-Type'] = file_type

            employee_df.to_csv(response, index=False, header=True)
            return response

        elif file_type == 'excel':
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')

            employee_df.to_excel(writer, index=False, sheet_name='Employees', startrow=1)

            workbook = writer.book
            employee_worksheet = writer.sheets['Employees']

            cell_format = workbook.add_format({
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter'
            })

            for idx, col in enumerate(employee_df.columns):
                max_len = max((employee_df[col].astype(str).str.len().max(), len(col))) + 2
                employee_worksheet.set_column(idx, idx, max_len, cell_format)

            for row in range(len(employee_df)):
                max_content_length = max(len(str(employee_df[col].iloc[row])) for col in employee_df.columns)
                employee_worksheet.set_row(row + 2, max_content_length // 2 + 10)  # Adjust row height

            writer.close()
            output.seek(0)

            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
            filename = f'employee_shifts_report_{timestamp}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-File-Type'] = file_type
            return response

        else:
            return HttpResponse(status=400, content="Invalid file type")
        
    else:
        client_aggregated_data = {}
        sno=1
        for shift in shifts.values(
            'id',
            'client__id',
            'client__person__first_name',
            'client__person__last_name',
            'shift_type',
            'total_hour'
        ):
            client_id = shift['client__id']
            client_name = f"{shift['client__person__first_name']} {shift['client__person__last_name']}"
            shift_type = shift['shift_type']
            total_hour_str = shift['total_hour']
            if client_id not in client_aggregated_data:
                client_aggregated_data[client_id] = {
                    'sno': sno,
                    'shift_ids': [],
                    'client_name': client_name,
                    'morning_hours': 0.0,
                    'evening_hours': 0.0,
                    'night_hours': 0.0,
                    'open_shift_hours': 0.0,
                    'total_hours': 0.0
                }
                sno+=1
            client_aggregated_data[client_id]['shift_ids'].append(shift['id'])
            total_hours = parse_total_hour(total_hour_str)
            if shift_type == 'Morning':
                client_aggregated_data[client_id]['morning_hours'] += total_hours
            elif shift_type == 'Evening':
                client_aggregated_data[client_id]['evening_hours'] += total_hours
            elif shift_type == 'Night':
                client_aggregated_data[client_id]['night_hours'] += total_hours
            elif shift_type == 'Open shift':
                client_aggregated_data[client_id]['open_shift_hours'] += total_hours

            client_aggregated_data[client_id]['total_hours'] += total_hours

        client_df = pd.DataFrame(client_aggregated_data.values())
        client_df = client_df[[
            'sno','client_name', 'morning_hours', 'evening_hours', 'night_hours', 'open_shift_hours','total_hours'
        ]]

        client_df['morning_hours'] = client_df['morning_hours'].apply(format_hours_minutes)
        client_df['evening_hours'] = client_df['evening_hours'].apply(format_hours_minutes)
        client_df['night_hours'] = client_df['night_hours'].apply(format_hours_minutes)
        client_df['open_shift_hours'] = client_df['open_shift_hours'].apply(format_hours_minutes)
        client_df['total_hours'] = client_df['total_hours'].apply(format_hours_minutes)

        client_df.columns = [
          'S.no','Client name', 'Morning hours', 'Evening hours', 'Night hours', 'Open shift hours','Total hours'
        ]

        if file_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
            filename = f'client_shifts_report_{timestamp}.csv'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-File-Type'] = file_type

            client_df.to_csv(response, index=False, header=True)
            return response

        elif file_type == 'excel':
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')

            client_df.to_excel(writer, index=False, sheet_name='Clients', startrow=1)

            workbook = writer.book
            client_worksheet = writer.sheets['Clients']

            cell_format = workbook.add_format({
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter'
            })

            for idx, col in enumerate(client_df.columns):
                max_len = max((client_df[col].astype(str).str.len().max(), len(col))) + 2
                client_worksheet.set_column(idx, idx, max_len, cell_format)

            for row in range(len(client_df)):
                max_content_length = max(len(str(client_df[col].iloc[row])) for col in client_df.columns)
                client_worksheet.set_row(row + 2, max_content_length // 2 + 10)  # Adjust row height

            writer.close()
            output.seek(0)

            response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            timestamp = timezone.now().strftime('%d-%b-%Y-%I.%M%p').lower()
            filename = f'client_shifts_report_{timestamp}.xlsx'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-File-Type'] = file_type
            return response

        else:
            return HttpResponse(status=400, content="Invalid file type")
        

def parse_total_hour(total_hour_str):
    if total_hour_str is None:
        return 0.0
    match = re.match(r"(\d+)\s*hours?\s*(?:and)?\s*(\d+)?\s*minutes?", total_hour_str.strip())
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        return hours + minutes / 60.0
    return 0.0

def format_hours_minutes(total_hours):
    hours_int = int(total_hours)
    minutes = round((total_hours - hours_int) * 60)
    if minutes >= 60:
        hours_int += 1
        minutes -= 60
    return f"{hours_int} hour {minutes} min"