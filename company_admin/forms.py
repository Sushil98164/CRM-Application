from django import forms
from userauth.models import Person, Client, ClientEmergencyDetail, ClientNDISDetail, ClientMedicalDetail, Employee , Department, NDIS_SERVICES_CHOICES, SERVICE_FUND_TYPE_CHOICES, EMPLOYMENT_TYPE_CHOICES
from django.forms.models import inlineformset_factory
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import *
from datetime import datetime, date, timedelta
import re
import ast
from userauth.utils import has_user_permission
from django.forms import BaseInlineFormSet
from django.db.models import Q
from django.db.models.functions import Lower
from employee.models import *
from django.db.models import Exists, OuterRef, Q, Value
from django.db.models.functions import Lower, Replace
from django.forms import modelformset_factory


class CompanyPersonForm(forms.ModelForm):
    """
    CompanyPersonForm
    """
    password = forms.CharField(widget=forms.HiddenInput(), required=False)
    gender = forms.ChoiceField(choices=CHOICES_GENDER, required=False)


    class Meta:
        """
        Meta Class
        """
        model = Person
        fields = ['first_name', 'last_name', 'email',
                  'gender', 'phone_number', 'password', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
            'is_active': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CompanyPersonForm, self).__init__(*args, **kwargs)

        permission_all = has_user_permission(self.request.user, 'userauth.update_employee_approval_all')
        permission_none = has_user_permission(self.request.user, 'userauth.update_employee_approval_none')
        
        # print(f"Permission for 'update_employee_approval_all': {permission_all}")
        # print(f"Permission for 'update_employee_approval_none': {permission_none}")

         # Set the default value for is_active to False (No)
        if not self.initial.get('is_active', None):  # If not already set
            self.initial['is_active'] = False

        # Check permissions and adjust the fields accordingly
        if permission_all:
            self.fields['is_active'].disabled = False
            # self.initial['is_active'] = self.instance.is_active
        elif permission_none:
            self.fields['is_active'].disabled = True
            # self.initial['is_active'] = self.instance.is_active
        else:
            self.fields['is_active'].disabled = True
            # self.initial['is_active'] = self.instance.is_active

 
   
    def save(self, commit=True):
        generated_password = None

        if not self.instance.pk and not self.cleaned_data.get('password'):
            first_name = self.cleaned_data.get('first_name', 'Bells')
            generated_password = f'{first_name}@1234'
            self.instance.set_password(generated_password)

        result = super().save(commit)

        return result, generated_password

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            phone_regex = re.compile(r'^\+?1?\d{10,15}$')
            if not phone_regex.match(phone_number):
                raise forms.ValidationError("Enter a valid phone 10 digit phone number.")
        return phone_number
    
    
   
class ClientPersonForm(forms.ModelForm):
    """
    ClientPersonForm
    """
    password = forms.CharField(widget=forms.HiddenInput(), required=False)
    gender = forms.ChoiceField(choices=CHOICES_GENDER, required=True)
    email = forms.CharField(widget=forms.TextInput(), required=False)

    class Meta:
        """
        Meta Class
        """
        model = Person
        fields = ['first_name', 'last_name','email',
                  'gender', 'phone_number', 'password', 'is_active','profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            # 'email': forms.TextInput(attrs={'required': False}),
            'is_active': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'residential_address': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'created_by': forms.HiddenInput(),

        }

    def __init__(self, *args, **kwargs):
        super(ClientPersonForm, self).__init__(*args, **kwargs)
        self.initial['is_active'] = False
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            self.add_error('phone_number', forms.ValidationError("Please enter a valid 10-digit phone number."))

        return phone_number
    def save(self, commit=True):
        if not self.instance.pk and not self.cleaned_data.get('password'):
            first_name = self.cleaned_data.get('first_name', 'Bells')
            self.instance.set_password(f'{first_name}@1234')
        return super().save(commit)


class ClientForm(forms.ModelForm):
    """
    ClientForm
    """
    fund_management_by = forms.ChoiceField(
        choices=CHOICES_FUND_MANAGEMENT, required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=True )


    class Meta:
        """
        Meta Class
        """
        model = Client
        fields = '__all__'  
        widgets = {
            'id': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'date_of_birth': forms.DateInput(attrs={'required': True}),
            'residential_address': forms.Textarea(attrs={'rows': 1, 'cols': 40}),

            
        }
        
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].widget.attrs['min'] = '1900-01-01'
        print('1900-01-01')
        self.fields['date_of_birth'].widget.attrs['max'] = datetime.now().strftime('%Y-%m-%d')        
        
    def clean_fix_line(self):
        fix_line = self.cleaned_data.get('fix_line')

        if fix_line:
            phone_regex = re.compile(r'^(0[2-8][0-9]{8}|\+61[2-8][0-9]{8})$')
            if not phone_regex.match(fix_line):
                raise forms.ValidationError("Enter a valid Australian fixline number (e.g., 0298765432 or +61298765432).")

        return fix_line
    
    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')

        try:
            forms.DateField().clean(date_of_birth)
        except ValidationError:
            raise ValidationError('Please enter a valid date.')
        if date_of_birth > date.today():
            raise ValidationError('Please select a date from today and back.')
        
        if date_of_birth.year < 1900:
            raise ValidationError('Date of birth cannot be earlier than the year 1900.')
    
        return date_of_birth



class ClientEmergencyDetailForm(forms.ModelForm):
    """
    ClientEmergencyDetailForm
    """
    emergency_name = forms.CharField(required=False)
    class Meta:
        model = ClientEmergencyDetail
        fields = '__all__'
        widgets = {
            'id': forms.HiddenInput(),
            'is_authorised_representative': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
           
            }
    
    
    def clean_emergency_phone_number(self):
        phone_number = self.cleaned_data.get('emergency_phone_number')

        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            self.add_error('emergency_phone_number', forms.ValidationError("Please enter a valid 10-digit phone number."))

        return phone_number


class ClientNDISDetailForm(forms.ModelForm):
    """
    ClientNDISDetailForm
    """
    plan_start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    plan_end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    service_fund_type = forms.ChoiceField(choices=SERVICE_FUND_TYPE_CHOICES, required=True)
    ndis_services = forms.ChoiceField(
        choices=NDIS_SERVICES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':1, 'cols': 40}), required=False)
    hours_requested = forms.IntegerField(required=False)

    class Meta:
        """
        Meta Class
        """
        model = ClientNDISDetail
        fields = '__all__'
        widgets = {
            'id': forms.HiddenInput(),
            'is_individual_ndis_participant': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
            'is_any_service_agreements': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
            'is_any_consents_obtained': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
            'participant_number': forms.TextInput(attrs={'required': False, 'maxlength': 50}),
            'plan_funding_allocation': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'plan_goals_and_objectives': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }
    def __init__(self, *args, **kwargs):
        """
        Initialize the EmployeeForm.
        """
        self.request = kwargs.pop('request', None)
        super(ClientNDISDetailForm, self).__init__(*args, **kwargs)

    def clean_participant_number(self):
        is_individual_ndis_participant = self.cleaned_data.get('is_individual_ndis_participant')
        participant_number = self.cleaned_data.get('participant_number')

        if is_individual_ndis_participant == 1 and not participant_number:
            raise forms.ValidationError('This field is required when you have individual NDIS participant.')

        return participant_number

    def clean_plan_start_date(self):
        is_individual_ndis_participant = self.cleaned_data.get('is_individual_ndis_participant')
        plan_start_date = self.cleaned_data.get('plan_start_date')

        if is_individual_ndis_participant == 1 and not plan_start_date:
            raise forms.ValidationError('This field is required when you have an individual NDIS participant.')

        return plan_start_date

    def clean_plan_end_date(self):
        is_individual_ndis_participant = self.cleaned_data.get('is_individual_ndis_participant')
        plan_end_date = self.cleaned_data.get('plan_end_date')

        if is_individual_ndis_participant == 1 and not plan_end_date:
            raise forms.ValidationError('This field is required when you have an individual NDIS participant.')

        return plan_end_date


class ClientMedicalDetailForm(forms.ModelForm):
    """
    ClientMedicalDetailForm
    """

    class Meta:
        """
        Meta Class
        """
        model = ClientMedicalDetail
        fields = '__all__'
        widgets = {
            'id': forms.HiddenInput(),
            'is_any_disabilities': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
            'is_any_medication': forms.Select(choices=YES_NO_CHOICE, attrs={'required': True}),
            'doctor_consent': forms.Select(choices=YES_NO_CHOICE, attrs={'required': False}),
            'primary_disability': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'secondary_disability': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'medical_history': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'medication_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'allergies_and_sensitives': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'healthcare_provider_info': forms.Textarea(attrs={'rows': 1, 'cols': 40}),


        }

    def clean_primary_disability(self):
        is_any_disabilities = self.cleaned_data.get('is_any_disabilities')
        primary_disability = self.cleaned_data.get('primary_disability')

        if is_any_disabilities == 1 and not primary_disability:
            raise forms.ValidationError('This field is required when you have disabilities.')
        

        return primary_disability
    
    

def get_formset(Model1, Model2, form, extra=1, can_delete=True):
    """
    This method is used to create a formset
    """
    return inlineformset_factory(
        Model1, Model2,
        form=form, extra=extra, can_delete=can_delete
    )

class EmployeeForm(forms.ModelForm):
    """
    EmployeeForm
    """

    class Meta:
        """
        Meta Class
        """
        model = Employee
        fields = '__all__'  
        widgets = {
            'company': forms.HiddenInput(),
            'created_by': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'employment_type' : forms.Select(choices=EMPLOYMENT_TYPE_CHOICES),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the EmployeeForm.
        """
        self.request = kwargs.pop('request', None)
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['employment_type'].choices = sorted(EMPLOYMENT_TYPE_CHOICES, key=lambda x: x[1])
        current_employee = self.request.user.employee
        company = current_employee.company
        self.fields['created_by'].initial = current_employee
        self.fields['company'].initial = company

        # if current_employee.is_admin_role_only():
        #     self.fields['departments'].queryset = Department.bells_manager.filter(company=company).order_by(Lower('name'))
        # elif current_employee.is_manager_role(): 
        #     self.fields['departments'].queryset = Department.bells_manager.filter(company=company,manager=current_employee).order_by(Lower('name'))

       
        # if not self.instance.pk and self.fields['departments'].queryset.exists():
        #     self.fields['departments'].initial = self.fields['departments'].queryset[:1]
        

    # def clean_departments(self):
    #     """
    #     Validate that the selected department(s) are not already assigned.
    #     This validation is only applicable for employees whose role is 'Manager' (role = 2)
    #     and when the URL name is 'employee_add'.
    #     """
    #     selected_departments = self.cleaned_data.get('departments')
        
    #     if (
    #         self.cleaned_data.get('role') == '2' 
    #         and self.request.resolver_match.url_name == 'employee_add'
    #     ):
    #         company = self.request.user.employee.company
    #         for department in selected_departments:
    #             if department.company == company and department.manager and department.manager.pk != self.instance.pk:
    #                 raise ValidationError(f'The department "{department.name}" is already assigned to another manager in the company.')

    #     return selected_departments


class CustomEmployeeFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.fields['employment_type'].choices = sorted(EMPLOYMENT_TYPE_CHOICES, key=lambda x: x[1])

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['request'] = self.request
        return kwargs

EmployeeFormset = inlineformset_factory(
    Person, Employee,
    form=EmployeeForm,
    formset=CustomEmployeeFormSet,
    extra=1,
    can_delete=True
)


class MandatoryIncidentForm(forms.ModelForm):
    incident_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    files = forms.FileField(widget=forms.FileInput(), required=False)
    report_type = forms.Select(choices=TYPE_OF_INCIDENT_REPORT)
    sno = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Incident
        fields = '__all__'
        widgets = {
            'employee': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'report_code': forms.HiddenInput(),
            'report_type': forms.HiddenInput(attrs={'value': "Mandatory Incident"}),
            'is_injured': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'any_witness': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'is_mandatory_aware': forms.CheckboxInput(attrs={'required': True}),
            'pre_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'action_taken': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'inbetween_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'post_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'incident_severity_level': forms.Select(choices=TYPE_OF_SEVERITY_LEVEL),
            'specific_severity_level': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['employee'].widget = forms.Select()
        self.fields['incident_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
        self.fields['incident_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')

        if company:
            if request.user.employee.role == 2:
                manager_departments = request.user.employee.departments.filter(is_deleted=False)
                employees = Employee.bells_manager.filter(
                    Q(company=company) & 
                    (Q(departments__in=manager_departments) | Q(created_by=request.user.employee, departments__in=manager_departments))
                ).distinct().order_by("-created_at")
                self.fields['employee'].queryset = employees

                employees = Employee.bells_manager.filter(departments__in=manager_departments)
                client_assignments = ClientAssignment.bells_manager.filter(employee__in=employees)
                client_queryset = Client.bells_manager.filter(company=company,
                    client_assignments_detail__client_assignment__in=client_assignments,
                    client_assignments_detail__is_deleted=False
                ).distinct().order_by('-created_at')    
                self.fields['client'].queryset = client_queryset  # Filter clients by company
            else:
                self.fields['employee'].queryset = Employee.bells_manager.filter(company=company)
                self.fields['client'].queryset = Client.bells_manager.filter(company=company)  # Filter clients by company

        if self.instance and self.instance.incident_severity_level:
            self.fields['specific_severity_level'].choices = SEVERITY_LEVEL_CHOICES.get(self.instance.incident_severity_level, [])

    def clean(self):
        cleaned_data = super().clean()
        incident_severity_level = cleaned_data.get('incident_severity_level')
        specific_severity_level = cleaned_data.get('specific_severity_level')

        if incident_severity_level == '' or incident_severity_level == 'Not applicable':
            cleaned_data['specific_severity_level'] = ''
        else:
            valid_choices = dict(SEVERITY_LEVEL_CHOICES.get(incident_severity_level, []))
            if specific_severity_level not in valid_choices:
                self.add_error('specific_severity_level', "Select a valid choice. %s is not one of the available choices." % specific_severity_level)

        return cleaned_data


    def clean_injured_person(self):
        is_injured = self.cleaned_data.get('is_injured')
        injured_person = self.cleaned_data.get('injured_person')
        if is_injured and not injured_person:
            raise forms.ValidationError('This field is required.')
        return injured_person

    def clean_witness_name(self):
        any_witness = self.cleaned_data.get('any_witness')
        witness_name = self.cleaned_data.get('witness_name')
        if any_witness and not witness_name:
            raise forms.ValidationError("This field is required.")
        return witness_name

    def clean_report_type(self):
        report_type = self.cleaned_data.get('report_type')
        return report_type

    def clean_incident_date_time(self):
        incident_date_time = self.cleaned_data.get('incident_date_time')
        if isinstance(incident_date_time, datetime):
            incident_date_time = incident_date_time.date()

        try:
            forms.DateField().clean(incident_date_time)
        except ValidationError:
            raise ValidationError('Please enter a valid date.')

        if isinstance(incident_date_time, datetime):
            incident_date_time = incident_date_time.date()

        if incident_date_time > date.today():
            raise ValidationError('Please select a date from today and back.')

        if incident_date_time.year < 1900:
            raise ValidationError('Incident date time cannot be earlier than the year 1900.')

        return incident_date_time



class MandatoryIncidentAttachmentForm(forms.ModelForm):
    class Meta:
        model = IncidentAttachment
        fields = '__all__'
    


# class IncidentForm(forms.ModelForm):
    
#     incident_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
#     files = forms.FileField(widget=forms.FileInput(), required=False)
#     report_type=forms.Select(choices=TYPE_OF_INCIDENT_REPORT)
#     sno = forms.IntegerField(widget = forms.HiddenInput())


#     were_employees_present = forms.BooleanField(
#         required=False,
#         widget=forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False})
#     )




#     class Meta:
#         model = Incident
#         fields = '__all__'
#         exclude = []
#         widgets = {
#             'employee': forms.HiddenInput(),
#             'company':forms.HiddenInput(),
#             'report_code':forms.HiddenInput(),
#             'report_type':forms.HiddenInput(attrs={'value':"Incident"}),
#             'is_injured': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
#             'any_witness': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
#             'pre_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'action_taken': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'inbetween_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'post_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'incident_severity_level':forms.Select(choices=TYPE_OF_SEVERITY_LEVEL,),
#             'specific_severity_level': forms.Select(),
#             'incident_category':forms.Select(choices=INCIDENT_CATEGORY_CHOICES),
#             'define_other_category': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'incident_classification':forms.Select(choices=INCIDENT_CLASSIFICATION_CHOICES),
#             'employees_involved':forms.Select(choices=EMPLOYEE_INVOLVED,),

#         }
    
#     def __init__(self, *args, **kwargs):
#         company = kwargs.pop('company', None)
#         request = kwargs.pop('request', None)

#         super().__init__(*args, **kwargs)

#         self.fields['incident_severity_level'].choices = sorted(TYPE_OF_SEVERITY_LEVEL, key=lambda x: x[1])
#         self.fields['incident_category'].choices = [("", "---------")] +sorted(INCIDENT_CATEGORY_CHOICES, key=lambda x: x[1])
#         self.fields['incident_classification'].choices = [("", "---------")] +sorted(INCIDENT_CLASSIFICATION_CHOICES, key=lambda x: x[1])
#         self.fields['incident_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
#         self.fields['incident_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
#         self.fields['employee'].widget = forms.Select()
#         if company:
#             if request.user.employee.role == 2:
#                 manager_id = request.user.employee.id 
#                 manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager_id,company_id=company.id)
#                 client_queryset = manager_data['clients']
#                 employee_queryset = manager_data['employees']
#                 self.fields['employee'].queryset=employee_queryset
#                 self.fields['client'].queryset = client_queryset  # Filter clients by company
#             else:
#                 self.fields['employee'].queryset = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
#                 self.fields['client'].queryset = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))

#         if self.instance and self.instance.incident_severity_level:
#             self.fields['specific_severity_level'].choices = SEVERITY_LEVEL_CHOICES.get(self.instance.incident_severity_level, [])




#     def clean(self):
#         cleaned_data = super().clean()
#         incident_severity_level = cleaned_data.get('incident_severity_level')
#         specific_severity_level = cleaned_data.get('specific_severity_level')

#         if incident_severity_level == '' or incident_severity_level == 'Not applicable':
#             cleaned_data['specific_severity_level'] = ''
#         else:
#             valid_choices = dict(SEVERITY_LEVEL_CHOICES.get(incident_severity_level, []))
#             if specific_severity_level not in valid_choices:
#                 self.add_error('specific_severity_level', "Select a valid choice. %s is not one of the available choices." % specific_severity_level)

#         return cleaned_data
    
    
#     def clean_injured_person(self):
#         is_injured = self.cleaned_data.get('is_injured')
#         injured_person = self.cleaned_data.get('injured_person')

#         if is_injured and not injured_person:
#             raise forms.ValidationError('This field is required')
#         return injured_person
    
#     def clean_witness_name(self):
#         any_injured = self.cleaned_data.get('any_witness')
#         witness_name = self.cleaned_data.get('witness_name')
#         if any_injured and not witness_name:
#             raise forms.ValidationError("This field is required")
#         return witness_name
    

    
#     def clean_report_type(self):
#         report_type = self.cleaned_data.get('report_type')
#         return report_type
    

    
class IncidentForm(forms.ModelForm):
    
    incident_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    files = forms.FileField(widget=forms.FileInput(), required=False)
    report_type=forms.Select(choices=TYPE_OF_INCIDENT_REPORT)


    were_employees_present = forms.BooleanField(
        required=False,
        widget=forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False})
    )




    class Meta:
        model = Incident
        fields = '__all__'
        exclude = []
        widgets = {
            'employee': forms.HiddenInput(),
            'company':forms.HiddenInput(),
            'sno':forms.HiddenInput(),
            'report_code':forms.HiddenInput(),
            'report_type':forms.HiddenInput(attrs={'value':"Incident"}),
            'is_injured': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'any_witness': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'pre_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'action_taken': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'inbetween_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'post_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'incident_severity_level':forms.Select(choices=TYPE_OF_SEVERITY_LEVEL,),
            'specific_severity_level': forms.Select(),
            'incident_category':forms.Select(choices=INCIDENT_CATEGORY_CHOICES),
            'define_other_category': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'incident_classification':forms.Select(choices=INCIDENT_CLASSIFICATION_CHOICES),
            'employees_involved':forms.Select(choices=EMPLOYEE_INVOLVED,),

        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.fields['incident_severity_level'].choices = sorted(TYPE_OF_SEVERITY_LEVEL, key=lambda x: x[1])
        self.fields['incident_category'].choices = [("", "---------")] +sorted(INCIDENT_CATEGORY_CHOICES, key=lambda x: x[1])
        self.fields['incident_classification'].choices = [("", "---------")] +sorted(INCIDENT_CLASSIFICATION_CHOICES, key=lambda x: x[1])
        self.fields['incident_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
        self.fields['incident_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        self.fields['employee'].widget = forms.Select()
     
        
        if company:
            if has_user_permission(request.user, 'company_admin.create_incident_own_team'):
                manager_id = request.user.employee.id 
                manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id=manager_id,company_id=company.id)
                client_queryset = manager_data['clients']
                employee_clients_data = ClientEmployeeAssignment.get_clients_by_employee(employee_id=manager_id,company_id=company.id) 
                employee_queryset = manager_data['employees']
                self.fields['employee'].queryset=employee_queryset
                self.fields['client'].queryset = client_queryset | employee_clients_data
            
            elif has_user_permission(request.user, 'company_admin.create_incident_all'):
                self.fields['employee'].queryset = Employee.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
                self.fields['client'].queryset = Client.bells_manager.filter(company=company).order_by(Lower('person__first_name'))
            
            elif has_user_permission(request.user, 'company_admin.create_incident_there_own'):
                employee_id = request.user.employee.id 
                self.fields['employee'].queryset = Employee.bells_manager.filter(company=company,id=employee_id).order_by(Lower('person__first_name'))
                assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id = employee_id,company_id=company.id).values_list('id', flat=True)
                self.fields['client'].queryset = Client.bells_manager.filter(company=company, id__in=list(assigned_clients)).order_by(Lower('person__first_name'))

            else:
                self.fields['employee'].queryset = Employee.objects.none()  
                self.fields['client'].queryset = Client.objects.none()  


        if self.instance and self.instance.incident_severity_level:
            self.fields['specific_severity_level'].choices = SEVERITY_LEVEL_CHOICES.get(self.instance.incident_severity_level, [])




    def clean(self):
        cleaned_data = super().clean()
        incident_severity_level = cleaned_data.get('incident_severity_level')
        specific_severity_level = cleaned_data.get('specific_severity_level')

        if incident_severity_level == '' or incident_severity_level == 'Not applicable':
            cleaned_data['specific_severity_level'] = ''
        else:
            valid_choices = dict(SEVERITY_LEVEL_CHOICES.get(incident_severity_level, []))
            if specific_severity_level not in valid_choices:
                self.add_error('specific_severity_level', "Select a valid choice. %s is not one of the available choices." % specific_severity_level)
   
        
        return cleaned_data
    
    
    def clean_injured_person(self):
        is_injured = self.cleaned_data.get('is_injured')
        injured_person = self.cleaned_data.get('injured_person')

        if is_injured and not injured_person:
            raise forms.ValidationError('This field is required')
        return injured_person
    
    def clean_witness_name(self):
        any_injured = self.cleaned_data.get('any_witness')
        witness_name = self.cleaned_data.get('witness_name')
        if any_injured and not witness_name:
            raise forms.ValidationError("This field is required")
        return witness_name
        
    def clean_report_type(self):
        report_type = self.cleaned_data.get('report_type')
        return report_type
    

    


class IncidentAttachmentForm(forms.ModelForm):
    class Meta:
        model = IncidentAttachment
        fields = '__all__'


from rostering.constants import CHOICES_SHIFT_TYPE

class DailyShiftNoteForm(forms.ModelForm):
    start_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    shift_type = forms.ChoiceField(choices=CHOICES_SHIFT_TYPE)

    class Meta:
        model = DailyShiftCaseNote
        fields = '__all__'
        widgets = {
            'employee': forms.HiddenInput(),
            'company':forms.HiddenInput(),
            'sno':forms.HiddenInput(),
            'vehicle_used': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'description':forms.Textarea(attrs={'rows': 1, 'cols': 40}),

        }
    
    def __init__(self,*args, **kwargs):
        request = kwargs.pop('request', None)
        company = kwargs.pop('company',None)
        super().__init__(*args, **kwargs)
        
        self.fields['start_date_time'].widget.attrs['min']='1900-01-01T00:00'
        self.fields['end_date_time'].widget.attrs['min']='1900-01-01T00:00'
        if has_user_permission(request.user, 'company_admin.update_progress_notes_own'):
            self.fields['start_date_time'].widget.attrs['readonly'] = True
            self.fields['end_date_time'].widget.attrs['readonly'] = True

        assigned_clients = kwargs.get('initial', {}).get('client', None)
        if assigned_clients is not None:
            self.fields['client'].queryset = assigned_clients
            print(assigned_clients,'assigned_clients')
            
        if request and request.resolver_match.url_name == 'admin_dailyshift_view':
            for field in self.fields.values():
                field.disabled = True

    
    def clean(self):
        cleaned_data = super().clean()
        start_date_time = cleaned_data.get('start_date_time')
        end_date_time = cleaned_data.get('end_date_time')

        if start_date_time and end_date_time:
            if end_date_time <= start_date_time:
                raise ValidationError({
                    'end_date_time': 'End time must be after start time.'
                })
            
  
        if start_date_time.year < 1900:
            self.add_error('start_date_time', 'Start date-time cannot be earlier than the year 1900.')
        if end_date_time.year < 1900:
            self.add_error('end_date_time', 'End date-time cannot be earlier than the year 1900.')

    
        return cleaned_data

CHOICES_INCIDENT_REOPORTS = (
    ('','-------'),
    ('New','New'),
    ('InProgress','InProgress'),
    ('Closed','Closed'),
)


class FilterQuerySetForm(forms.Form):
    client = forms.ModelChoiceField(queryset=None,required=False)
    employee = forms.ModelChoiceField(queryset = None,required=False)
    status = forms.ChoiceField(required=False, choices=CHOICES_INCIDENT_REOPORTS)
    incident_category = forms.ChoiceField(required=False,choices=INCIDENT_CATEGORY_CHOICES)
    incident_classification = forms.ChoiceField(required=False,choices=INCIDENT_CLASSIFICATION_CHOICES)
    class Meta:
        model = DailyShiftCaseNote
        fields = ['client','employee','status','incident_category','incident_classification']

    def __init__(self,*args, **kwargs):
        super(FilterQuerySetForm,self).__init__(*args, **kwargs)

        self.fields['incident_category'].choices = [("", "---------")] +sorted(INCIDENT_CATEGORY_CHOICES, key=lambda x: x[1])
        self.fields['incident_classification'].choices = [("", "---------")] +sorted(INCIDENT_CLASSIFICATION_CHOICES, key=lambda x: x[1])
        
         
        
class RiskAssessmentForm(forms.ModelForm):
    assessment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
    reviewed_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )

    class Meta:
        model = RiskAssessment
        fields = ['client', 'assessment_date', 'reviewed_date', 'prepared_by']
        widgets = {
            'prepared_by': forms.HiddenInput(),
            'client':forms.HiddenInput(),
            'id': forms.HiddenInput(),

        }
       
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)

        super(RiskAssessmentForm, self).__init__(*args, **kwargs)
        self.fields['assessment_date'].widget.attrs['max'] = (datetime.now()).strftime('%Y-%m-%d')
        self.fields['reviewed_date'].widget.attrs['max'] = (datetime.now()).strftime('%Y-%m-%d')

      
    def clean(self):
        cleaned_data = super(RiskAssessmentForm, self).clean()
        assessment_date = cleaned_data.get('assessment_date')
        reviewed_date = cleaned_data.get('reviewed_date')

        if assessment_date and reviewed_date and assessment_date >= reviewed_date:
            self.add_error('reviewed_date', "Review date must be later than assessment date.")

        return cleaned_data
    


RISK_LEVEL_CHOICES = [(str(i), str(i)) for i in range(1, 11)]
   
class RiskAssessmentDetailForm(forms.ModelForm):
    choosen_risk_area = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'class': 'multiselect'}))
    risk_to_self = forms.ChoiceField(
        required=False,
        choices=[('', '-------')] + RISK_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    risk_to_staff = forms.ChoiceField(
        required=False,
        choices=[('', '-------')] + RISK_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    risk_to_other = forms.ChoiceField(
        required=False,
        choices=[('', '-------')] +RISK_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


    class Meta:
        model = RiskAssessmentDetail
        fields = '__all__'
        widgets = {
            'id': forms.HiddenInput(),
            }
    def __init__(self,*args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
   
        if self.request and  'risk_assessment_add' in self.request.resolver_match.url_name and self.request.method == 'GET':
            if self.request.GET.get('risk_assessment') == 'True':
                instance = kwargs.get('instance')
                try:

                    choosen_risk_area_dict_str = instance.choosen_risk_area
                    choosen_risk_area_dict = ast.literal_eval(choosen_risk_area_dict_str)
                    selected_risk_area_ids = choosen_risk_area_dict.keys()
                    selected_risk_areas = RiskArea.objects.filter(id__in=selected_risk_area_ids)
                    
                    first_risk_area = selected_risk_areas.first()
                    ids = [item['id'] for item in first_risk_area.risk_type.risk_areas.all().values('id')]
                    selected_risk_areas = RiskArea.objects.filter(id__in=ids)
                    self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in selected_risk_areas]
                    self.initial['choosen_risk_area'] = list(selected_risk_area_ids)
                
                except:
                    self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in RiskArea.objects.none()]
            else:
                self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in RiskArea.objects.none()]
        
        elif self.request and self.request.resolver_match.url_name == 'risk_assessment_edit' or self.request.resolver_match.url_name == 'client_risk_assessment_edit' and self.request.method == 'GET':
            instance = kwargs.get('instance')
            try:
                choosen_risk_area_dict_str = instance.choosen_risk_area
                choosen_risk_area_dict = ast.literal_eval(choosen_risk_area_dict_str)
                selected_risk_area_ids = choosen_risk_area_dict.keys()
                selected_risk_areas = RiskArea.objects.filter(id__in=selected_risk_area_ids)
                
                first_risk_area = selected_risk_areas.first()
                ids = [item['id'] for item in first_risk_area.risk_type.risk_areas.all().values('id')]
                selected_risk_areas = RiskArea.objects.filter(id__in=ids)
                self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in selected_risk_areas]
                self.initial['choosen_risk_area'] = list(selected_risk_area_ids)
            except:
                    self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in RiskArea.objects.none()]
             
       
        
        else:
            self.fields['choosen_risk_area'].choices = [(area.id, area.name) for area in RiskArea.objects.all()]
        
 
   
    def clean_choosen_risk_area(self):
        choosen_risk_areas = self.cleaned_data.get('choosen_risk_area')
        choices = self.fields['choosen_risk_area'].choices
        risk_areas_dict = {}
        for id, name in choices:
            if str(id) in choosen_risk_areas:
                risk_areas_dict[id] = name
        return risk_areas_dict

class RiskDocumentationApprovalForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )

    class Meta:
        model = RiskDocumentationApproval
        fields = '__all__'
        widgets = {
            'id': forms.HiddenInput(),
            'completed_by': forms.TextInput(attrs={'readonly': 'readonly'}),

            }
        
    def __init__(self, *args, **kwargs):
        super(RiskDocumentationApprovalForm, self).__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['max'] = (datetime.now()).strftime('%Y-%m-%d')
        
    def clean_date(self):
        date = self.cleaned_data['date']
        return date

class RiskMoniterControlForm(forms.ModelForm):
    reviewed_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
    class Meta:
        model = RiskMoniterControl
        fields = '__all__'

        widgets = {
            'id': forms.HiddenInput(),
            }
        
    def __init__(self, *args, **kwargs):
        super(RiskMoniterControlForm, self).__init__(*args, **kwargs)
        self.fields['reviewed_date'].widget.attrs['max'] = (datetime.now()).strftime('%Y-%m-%d')

class RiskMoniterControlFormSet(forms.BaseModelFormSet):
    def clean(self):
        super().clean()
        non_empty_forms = [form for form in self.forms if any(form.cleaned_data.values()) and not form.cleaned_data.get('DELETE', False)]
        self.forms = non_empty_forms


class RiskAssessmentDetailFormSet(forms.BaseModelFormSet):
    def clean(self):
        super().clean()
        non_empty_forms = [form for form in self.forms if any(form.cleaned_data.values()) and not form.cleaned_data.get('DELETE', False)]
        self.forms = non_empty_forms

class RiskDocumentationApprovalFormSet(forms.BaseModelFormSet):
    def clean(self):
        super().clean()

        non_empty_forms = [form for form in self.forms if any(form.cleaned_data.values()) and not form.cleaned_data.get('DELETE', False)]
        self.forms = non_empty_forms
        
    
class IncidentCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['employee', 'incident', 'report_type', 'content']    
        widgets = {
            'id': forms.HiddenInput(),
            'content': forms.Textarea(attrs={'rows': 1, 'cols': 40}),

        }

class IncidentQuestionForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['employee', 'incident', 'report_type', 'cause_of_incident','prevention_of_incident']    
        widgets = {
            'id': forms.HiddenInput(),
            'cause_of_incident': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'prevention_of_incident': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }
        


class CompanyEmployeePersonForm(forms.ModelForm):
   
    phone_number_validator = RegexValidator(
        regex=r'^\d{10,15}$',
        message='Phone number must be numeric and have a length 10.'
    )

    class Meta:
        """
        Meta Class
        """
        model = Person
        fields = ['first_name', 'last_name', 'email',
                  'phone_number', 'is_active','profile_image', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True, 'readonly': True}),
            'is_active': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),

        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CompanyEmployeePersonForm, self).__init__(*args, **kwargs)
        user = self.request.user

        # Log the permission checks
        permission_all = has_user_permission(user, 'userauth.update_employee_approval_all')
        permission_none = has_user_permission(user, 'userauth.update_employee_approval_none')
        
        # print(f"Permission for 'update_employee_approval_all': {permission_all}")
        # print(f"Permission for 'update_employee_approval_none': {permission_none}")

        # Check permissions and adjust the fields accordingly
        if permission_all:
            self.fields['is_active'].disabled = False
            self.initial['is_active'] = self.instance.is_active
        elif permission_none:
            self.fields['is_active'].disabled = True
            self.initial['is_active'] = self.instance.is_active
        else:
            self.fields['is_active'].disabled = True
            self.initial['is_active'] = self.instance.is_active


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            self.phone_number_validator(phone_number)
        return phone_number
    


# class CompanyEmployeeProfileForm(forms.ModelForm):
#     """
#     EmployeeForm
#     """
#     date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
 
#     class Meta:
#         """
#         Meta Class
#         """
#         model = Employee
#         fields = '__all__'  
#         widgets = {
#             'company': forms.HiddenInput(),
#             'id': forms.HiddenInput(),
#             'date_of_birth': forms.DateInput()  ,
#             'address': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
#             'created_by':forms.HiddenInput(),
#         }
    
    
#     def __init__(self,*args, **kwargs):
#         self.request = kwargs.pop('request', None)
#         super().__init__(*args, **kwargs)
#         if self.request and hasattr(self.request.user, 'employee'):
#             employee = self.request.user.employee
#             company = employee.company

#             self.fields['template'].queryset = Group.objects.filter(
#                 id__in=CompanyGroup.objects.filter(company=company).values_list('group_id', flat=True)
#             ).order_by(Lower('name'))

#         if self.instance and self.instance.pk and self.instance.template:
#             self.fields['template'].initial = self.instance.template

#         self.fields['template'].label_from_instance = lambda obj: obj.name.split(" - ")[1] if " - " in obj.name else obj.name
                
#         self.fields['date_of_birth'].widget.attrs['min'] = '1900-01-01'
#         print('1900-01-01')
#         self.fields['date_of_birth'].widget.attrs['max'] = datetime.now().strftime('%Y-%m-%d')
#         company = self.request.user.employee.company
#         current_employee = self.request.user.employee
#         if company:
#             self.fields['created_by'].initial = self.instance.created_by
#             if Employee.objects.filter(company=company, role=1).exists():
#                 self.fields['role'].choices = [choice for choice in CHOICE_ROLES if choice[0] != 1]

#         if current_employee.is_admin_role_only():
#             self.fields['departments'].queryset = Department.bells_manager.filter(company=company).order_by(Lower('name'))
#         elif current_employee.is_manager_role():
#             self.fields['departments'].queryset = current_employee.managed_departments.filter(is_deleted=False).order_by(Lower('name'))

#         if not self.instance.pk and self.fields['departments'].queryset.exists():
#             self.fields['departments'].initial = self.fields['departments'].queryset[:1]

#         # permissions_to_check = [
#         # 'userauth.add_role',
#         # 'userauth.edit_role',
#         # 'userauth.add_is_active',
#         # 'userauth.edit_is_active',
        
#         # ]
    
#         # user_permissions = has_user_permission(self.request, permissions_to_check)
#         # if not user_permissions['edit_role']:
#         #     self.fields['role'].widget.attrs['disabled'] = True
#         #     self.fields['role'].required = False
#     def template_label(self, obj):
#         """ Generate label based on template name after filtering. """
#         name_part = obj.name.split(" - ")[1] if " - " in obj.name else obj.name
#         return name_part   
#     def clean_date_of_birth(self):
#         date_of_birth = self.cleaned_data.get('date_of_birth')

#         if not date_of_birth:
#             return date_of_birth

#         try:
#             forms.DateField().clean(date_of_birth)
#         except ValidationError:
#             raise ValidationError('Please enter a valid date.')
        
#         if date_of_birth > date.today():
#             raise ValidationError('Please select a date from today and back.')
        
#         if date_of_birth.year < 1900:
#             raise ValidationError('Date of birth cannot be earlier than the year 1900.')
    
#         return date_of_birth
        
class CompanyEmployeeProfileForm(forms.ModelForm):
    """
    EmployeeForm
    """
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
 
    class Meta:
        """
        Meta Class
        """
        model = Employee
        fields = '__all__'  
        widgets = {
            'company': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'date_of_birth': forms.DateInput()  ,
            'address': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'created_by':forms.HiddenInput(),
        }
    
    
    def __init__(self,*args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
            company = employee.company
            # self.fields['template'].queryset = Group.objects.filter(
            #     id__in=CompanyGroup.objects.filter(company=company)
            #     .annotate(
            #         has_non_deleted_employee=Exists(
            #             Employee.objects.filter(
            #                 template_id=OuterRef('group_id'), 
            #                 is_deleted=False,
            #                 company=company
            #             )
            #         )
            #     )
            #     .filter(has_non_deleted_employee=True)
            #     .values_list('group_id', flat=True)
            # ).order_by(Lower('name'))
            
            

            company_groups = CompanyGroup.objects.filter(company=company)
            company_groups = company_groups.annotate(
                has_non_deleted_employee=Exists(
                    Employee.objects.filter(
                        template_id=OuterRef('group_id'),
                        is_deleted=False,
                        company=company
                    )
                ),
                has_any_employee=Exists(
                    Employee.objects.filter(
                        template_id=OuterRef('group_id'),
                        company=company
                    )
                )
            )
            company_groups = company_groups.filter(
                Q(has_non_deleted_employee=True) | Q(has_any_employee=False)
            )
            group_ids = company_groups.values_list('group_id', flat=True)

            employee_groups = Group.objects.filter(id__in=group_ids).order_by(Lower('name'))        
            self.fields['template'].queryset = employee_groups
            self.fields['template'].required = True
   

            def custom_template_label(obj):
                emp = Employee.objects.filter(template=obj).first()
                
                if " - user" in obj.name and emp:
                    if emp.is_deleted == False:
                        return f"{emp.person.first_name} {emp.person.last_name}"
                    else:
                        return None
                parts = obj.name.split(" - ")
                return parts[1].strip() if len(parts) > 1 else obj.name

            self.fields['template'].label_from_instance = custom_template_label

        if self.instance and self.instance.pk and self.instance.template:
            self.fields['template'].initial = self.instance.template

        # self.fields['template'].label_from_instance = lambda obj: obj.name.split(" - ")[1] if " - " in obj.name else obj.name
                
        self.fields['date_of_birth'].widget.attrs['min'] = '1900-01-01'
        self.fields['date_of_birth'].widget.attrs['max'] = datetime.now().strftime('%Y-%m-%d')
        company = self.request.user.employee.company
        current_employee = self.request.user.employee
        if company:
            self.fields['created_by'].initial = self.instance.created_by
            if Employee.objects.filter(company=company, role=1).exists():
                self.fields['role'].choices = [choice for choice in CHOICE_ROLES if choice[0] != 1]

        # if current_employee.is_admin_role_only():
        #     self.fields['departments'].queryset = Department.bells_manager.filter(company=company).order_by(Lower('name'))
        # elif current_employee.is_manager_role():
        #     self.fields['departments'].queryset = current_employee.managed_departments.filter(is_deleted=False).order_by(Lower('name'))

        # if not self.instance.pk and self.fields['departments'].queryset.exists():
        #     self.fields['departments'].initial = self.fields['departments'].queryset[:1]

    # def template_label(self, obj):
    #     """ Generate label based on template name after filtering. """
    #     name_part = obj.name.split(" - ")[1] if " - " in obj.name else obj.name
    #     return name_part   
    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')

        if not date_of_birth:
            return date_of_birth

        try:
            forms.DateField().clean(date_of_birth)
        except ValidationError:
            raise ValidationError('Please enter a valid date.')
        
        if date_of_birth > date.today():
            raise ValidationError('Please select a date from today and back.')
        
        if date_of_birth.year < 1900:
            raise ValidationError('Date of birth cannot be earlier than the year 1900.')
    
        return date_of_birth



CompanyEmployeeProfileFormset = inlineformset_factory(
    Person, Employee,
    form=CompanyEmployeeProfileForm,
    formset=CustomEmployeeFormSet,

    extra=1,
    can_delete=True
)


class MangerDepartmentForm(forms.ModelForm):
    """
    ManagerDepartmentForm
    """

    class Meta:
        """
        Meta Class
        """
        model = Department
        fields = '__all__'
        
        widgets = {
            'company': forms.HiddenInput(),
            'author': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }
        
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        request = kwargs.pop('request', None)
        author = kwargs.pop('author', None)
        manager = kwargs.pop('manager', None)  

        super().__init__(*args, **kwargs)
        if request.resolver_match.url_name == 'departments_add':
            self.fields['company'].initial = company
            self.fields['author'].initial = author

            user_permissions = request.user.get_all_permissions()

            if 'userauth.read_department_all' or 'userauth.read_department_own' or 'userauth.create_department_all' in user_permissions:
                permission_codenames = ['read_department_all', 'read_department_own','create_department_all']
                permissions = Permission.objects.filter(codename__in=permission_codenames)

                employees_with_permission = Employee.bells_manager.filter(
                    company=company
                ).filter(
                    Q(person__user_permissions__in=permissions) |
                    Q(person__groups__permissions__in=permissions)
                ).distinct().order_by(Lower('person__first_name'))

                self.fields['manager'].queryset = employees_with_permission

            elif 'userauth.read_department_own' or 'userauth.create_department_all' in user_permissions:

                self.fields['manager'].queryset = Employee.bells_manager.filter(id=request.user.employee.id)
             
        elif request and request.resolver_match.url_name == 'departments_edit':
            self.fields['manager'].initial = manager
            
            user_permissions = request.user.get_all_permissions()

            if 'userauth.update_department_all'  in user_permissions:
                permission_codenames = ['update_department_all', 'update_department_own']
                permissions = Permission.objects.filter(codename__in=permission_codenames)

                employees_with_permission = Employee.bells_manager.filter(
                    company=company
                ).filter(
                    Q(person__user_permissions__in=permissions) |
                    Q(person__groups__permissions__in=permissions)
                ).distinct().order_by(Lower('person__first_name'))

                self.fields['manager'].queryset = employees_with_permission
            
            elif 'userauth.update_department_own' in user_permissions:
                self.fields['manager'].queryset = Employee.bells_manager.filter(id=manager.id) if manager else Employee.objects.none()
                self.fields['manager'].disabled = True
            else:
                self.fields['manager'].queryset = Employee.bells_manager.none()

        



class CompanyTermsAndConditionsPolicyForm(forms.ModelForm):
    class Meta:
        model = CompanyTermsAndConditionsPolicy
        fields = '__all__'
        
        widgets = {
            'type': forms.HiddenInput(),
            'company': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk is None:  
            if CompanyTermsAndConditionsPolicy.objects.filter(
                company=cleaned_data['company'], 
                type=cleaned_data['type']
            ).exists():
                raise forms.ValidationError("A policy for this company and type already exists.")
        return cleaned_data
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            self.add_error('description',"This field cannot be empty")
        return description
    

class ClientEmployeeAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClientEmployeeAssignment
        fields = ['client', 'employee']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
        }


class DepartmentClientAssignmentForm(forms.ModelForm):
    class Meta:
        model = DepartmentClientAssignment
        fields = ['department', 'client']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
        }
        

class CompanyInvestigationHierarchyForm(forms.ModelForm):
    class Meta:
        model = InvestigationHierarchy
        fields = ['company', 'category', 'hierarchy_timeline_days', 'levels']
        widgets = {
            'hierarchy_timeline_days': forms.NumberInput(attrs={'class': 'form-control','min': '1'}),
            'levels': forms.NumberInput(attrs={'class': 'form-control','min': '1'}),
        }     


    def clean(self):
        cleaned_data = super().clean()
        hierarchy_timeline_days = cleaned_data.get('hierarchy_timeline_days')
        hierarchy_levels = cleaned_data.get('levels')

        if hierarchy_levels is not None and hierarchy_levels <= 0:
            self.add_error('levels', "Level number must be greater than 0.")
        
        if hierarchy_timeline_days is not None and hierarchy_timeline_days <= 0:
            self.add_error('hierarchy_timeline_days', "Timeline days must be greater than 0.")
        
        return cleaned_data
    
class InvestigationStageForm(forms.ModelForm):
    class Meta:
        model = InvestigationStage
        fields = [
            'hierarchy', 
            'stage_name', 
            's_no', 
            'version', 
            'stage_timeline_days', 
            'is_active', 
            'permissions'
        ]
        widgets = {
            'stage_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter stage name'}),
            's_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'version': forms.NumberInput(attrs={'class': 'form-control'}),
            'stage_timeline_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permissions': forms.CheckboxSelectMultiple(),
        }
        
class StageOwnerSubstituteForm(forms.ModelForm):
    class Meta:
        model = StageOwnerSubstitute
        fields = ['owner', 'substitute', 'substitute_timeline_days']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'substitute': forms.Select(attrs={'class': 'form-control'}),
            'substitute_timeline_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Timeline for the substitute owner'})
        }

     
class IncidentStageQuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = IncidentStageQuestionMapper
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 1, 'cols': 40})
        }
        
IncidentStageQuestionAnswerFormSet = modelformset_factory(
    IncidentStageQuestionMapper,
    form=IncidentStageQuestionAnswerForm,
    extra=0
)

class InvestigationQuestionForm(forms.ModelForm):
    answer = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 40})
    )

    class Meta:
        model = InvestigationQuestion
        fields = ['question']
        widgets = {
            'question': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial') or {}
        super().__init__(*args, **kwargs)
        self.fields['answer'].initial = initial.get('answer', '')
