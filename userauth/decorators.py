from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Employee, Client
from company_admin.models import *
from django.http import HttpResponseForbidden
from django.db.models import Q
from userauth.utils import has_user_permission  


def admin_role_required(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        # Assuming the user's ID is stored in the request object
        user_id = request.user.id
        try:
            employee = Employee.bells_manager.get(person_id=user_id)
            if employee.role in [1,2]:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:dashboard')  # Replace 'home' with the name of your home page view
        except Employee.DoesNotExist:
            messages.error(request, "User is not an employee.")
            return redirect('company:dashboard')
    return wrapper_func

def user_can_access_employee(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('employee_id',None)
        if employee_id:
            try:
                employee = Employee.bells_manager.get(pk=employee_id)
                if employee.company != request.user.employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('company:employee_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:employee_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_can_access_client(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        client_id = kwargs.get('client_id')
        if client_id:
            try:
                client = Client.bells_manager.get(pk=client_id)
                if client.company != request.user.employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('company:client_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:client_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_role_required(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        # Assuming the user's ID is stored in the request object
        user_id = request.user.id
        try:
            employee = Employee.bells_manager.get(person_id=user_id)
            if employee.role in [1,2,3]:  # 1 represents Admin in your EMPLOYEE_ROLE
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:dashboard')  # Replace 'home' with the name of your home page view
        except Employee.DoesNotExist:
            messages.error(request, "User is not an employee.")
            return redirect('company:dashboard')
    return wrapper_func

def user_can_access_incident_report(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        incident_id = kwargs.get('incident_id')
        if incident_id:
            try:
                incident = Incident.bells_manager.get(pk=incident_id)
                if incident.company != request.user.employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('company:client_incident_reports_dashboard')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:client_incident_reports_dashboard')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_can_access_daily_shift_notes(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        shift_id = kwargs.get('shift_id')
        if shift_id:
            try:
                shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id)
                if shift.company != request.user.employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('company:daily_shift_note_dashboard')
            except:
                return redirect('company:daily_shift_note_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def user_can_access_mandatory_incident_report(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        mandatory_incident_id = kwargs.get('incident_id')
        if mandatory_incident_id:
            try:
                incident = Incident.bells_manager.get(pk=mandatory_incident_id,report_type = "Mandatory Incident")
                if incident.company != request.user.employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('company:mandatory_incident_reports_dashboard')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:mandatory_incident_reports_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_can_access_mandatory_incident_report(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        mandatory_incident_id = kwargs.get('incident_id')
        if mandatory_incident_id:
            try:
                incident = Incident.bells_manager.get(pk=mandatory_incident_id,report_type="Mandatory Incident")
                employee = request.user.employee
                if incident.company != employee.company or incident.employee != employee:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('employee:mandatory_incident_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('employee:mandatory_incident_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def employee_can_access_daily_shift_notes(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        shift_id = kwargs.get('shift_id')
        if shift_id:
            try:
                shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id)
                employee = request.user.employee
                if shift.company != employee.company or shift.employee != employee:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('employee:dailyshift_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('employee:dailyshift_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_can_access_other_employee_daily_shift_notes(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        shift_id = kwargs.get('shift_id')
        if shift_id:
            try:
                shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id)
                employee = request.user.employee
                if shift.company != employee.company:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('employee:dailyshift_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('employee:dailyshift_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
def employee_can_access_daily_shift_notes(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        shift_id = kwargs.get('shift_id')
        if shift_id:
            try:
                shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id)
                employee = request.user.employee
                if shift.company != employee.company or shift.employee != employee:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    # return HttpResponseForbidden("Unauthorized access attempt. Please respect privacy and security protocols. ")
                    return redirect('employee:dailyshift_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('employee:dailyshift_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_can_access_incident_report(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        incident_id = kwargs.get('incident_id')
        if incident_id:
            try:
                employee = request.user.employee
                incident_exists = Incident.bells_manager.filter(
                    Q(pk=incident_id),
                    Q(company=employee.company),
                    Q(employee=employee) | Q(tagged_incident__tagged_employee=employee)
                ).exists()
                
                if not incident_exists:
                    messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                    return redirect('employee:incident_list')
            except:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('employee:incident_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def check_permissions(required_permissions):
    """Decorator to check if the user has any of the required permissions."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper_func(request, *args, **kwargs):
            user = request.user

            if any(has_user_permission(user, perm) for perm in required_permissions):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return redirect('company:dashboard')
        return wrapper_func
    return decorator