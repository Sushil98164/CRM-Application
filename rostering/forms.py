from django import forms
from rostering.models import Shifts
from employee.models import *
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.core.exceptions import ValidationError
from userauth.models import Department
from django.db.models.functions import Lower
from company_admin.models import *
from userauth.utils import has_user_permission  


   
class ShiftsForm(forms.ModelForm):
    class Meta:
        model = Shifts
        fields = [
            'id',
            'employee',
            'client',
            'company',
            'author',
            'start_date_time',
            'end_date_time',
            'shift_category',
            'shift_type',
            'status',
            'total_hour',
        ]
        widgets = {
            'start_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'author': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'shift_category': forms.HiddenInput(),
            'status': forms.HiddenInput(),

        }
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None) 
        request = kwargs.pop('request',None)
        super().__init__(*args, **kwargs)
        self.fields['start_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
        self.fields['end_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
     
        if company:
            all_shifts = has_user_permission(request.user, 'rostering.create_shift_all')
            team_shifts = has_user_permission(request.user, 'rostering.create_own_team_shift')  
            if team_shifts:
                manager_employee = request.user.employee
                department_data = DepartmentClientAssignment.get_manager_department_data(manager_id = manager_employee.id,company_id=company.id)
                client_queryset =  department_data['clients']
                client_ids = client_queryset.values_list('id', flat=True)
                employees = department_data['employees']
                assigned_employees = Employee.bells_manager.filter(
                                        Q(client_employee_assignments__client_id__in=client_ids),
                                        client_employee_assignments__is_deleted=False
                                    ).distinct().order_by(Lower('person__first_name'))
                employees_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id = manager_employee.id,company_id = company.id)
                self.fields['client'].queryset = client_queryset | employees_clients
                self.fields['employee'].queryset = employees
            elif all_shifts:
                self.fields['client'].queryset = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name')) 
                self.fields['employee'].queryset = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name')) 

            else:
                self.fields['client'].queryset = Client.bells_manager.none()
                self.fields['employee'].queryset = Employee.bells_manager.none()

    def clean(self):
        cleaned_data = super().clean()
        start_date_time = cleaned_data.get('start_date_time')
        end_date_time = cleaned_data.get('end_date_time')
    
        if end_date_time <= start_date_time:
            raise ValidationError("End date and time cannot be before the start date and time.")
        
        if start_date_time.year < 1900:
            self.add_error('start_date_time', 'Start date-time cannot be earlier than the year 1900.')
        if end_date_time.year < 1900:
            self.add_error('end_date_time', 'End date-time cannot be earlier than the year 1900.')

        return cleaned_data