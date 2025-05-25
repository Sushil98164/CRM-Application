from django import forms
from django.forms.models import inlineformset_factory
from company_admin.models import *
from userauth.models import Client
from django.core.exceptions import ValidationError
from datetime import datetime, date,timedelta
from django.core.validators import RegexValidator
from .models import *
import os
from userauth.models import Person
from company_admin.constants import *


TRUE_FALSE_CHOICES = (
    (True, 'Yes'),
    (False, 'No')
)




class MandatoryIncidentForm(forms.ModelForm):
    incident_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    files = forms.FileField(widget=forms.FileInput(), required=False)
    report_type=forms.Select(choices=TYPE_OF_INCIDENT_REPORT)
    sno = forms.IntegerField(widget = forms.HiddenInput())
    class Meta:
        model = Incident
        fields = '__all__'
        widgets = {
            'employee': forms.HiddenInput(),
            'company':forms.HiddenInput(),
            'report_code':forms.HiddenInput(),
            'status':forms.HiddenInput(),
            'report_type':forms.HiddenInput(attrs={'value':"Mandatory Incident"}),
            'is_injured': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'any_witness': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'is_mandatory_aware': forms.CheckboxInput(attrs={'required': True}),
            'pre_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'action_taken': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'inbetween_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'post_incident_details': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
            'incident_severity_level':forms.Select(choices=TYPE_OF_SEVERITY_LEVEL,),
            'specific_severity_level': forms.Select(),

        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)  # Extract the company from kwargs
        super(MandatoryIncidentForm, self).__init__(*args, **kwargs)
        self.fields['incident_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
        self.fields['incident_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        if company:
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


class IncidentForm(forms.ModelForm):
    incident_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    files = forms.FileField(widget=forms.FileInput(), required=False)
    client = forms.ModelChoiceField(queryset=Client.objects.none()) 
    report_type=forms.Select(choices=TYPE_OF_INCIDENT_REPORT)
    # sno = forms.IntegerField(widget = forms.HiddenInput())

    class Meta:
        model = Incident
        fields = '__all__'
        widgets = {
            'employee': forms.HiddenInput(),
            'company':forms.HiddenInput(),
            # 'report_code':forms.HiddenInput(),
            'report_type':forms.HiddenInput(attrs={'value':"Mandatory Incident"}),
            'status':forms.HiddenInput(),
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

        super(IncidentForm, self).__init__(*args, **kwargs)
        self.fields['incident_severity_level'].choices = sorted(TYPE_OF_SEVERITY_LEVEL, key=lambda x: x[1])

        self.fields['incident_category'].choices =[("", "---------")] + sorted(INCIDENT_CATEGORY_CHOICES, key=lambda x: x[1])
        self.fields['incident_classification'].choices =[("", "---------")] + sorted(INCIDENT_CLASSIFICATION_CHOICES, key=lambda x: x[1])

        self.fields['incident_date_time'].widget.attrs['min'] = '1900-01-01T00:00'
        self.fields['incident_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        
        if company:
            self.fields['client'].queryset = Client.bells_manager.filter(company=company)  
        
        if 'employee_client_profile_incident_detail' in request.resolver_match.url_name:
            self.fields['client'].widget.attrs['disabled'] = True
            self.fields['employee'].widget.attrs['disabled'] = True
        
        elif 'incident_edit' in request.resolver_match.url_name:
            self.fields['client'].widget.attrs['disabled'] = True
            self.fields['employee'].widget = forms.HiddenInput()

        else:
            self.fields['client'].widget.attrs['disabled'] = False
            self.fields['employee'].widget.attrs['disabled'] = False
            self.fields['employee'].widget = forms.HiddenInput()

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


def get_formset(Model1, Model2, form, extra=1, can_delete=True):
    """
    This method is used to create a formset
    """
    return inlineformset_factory(
        Model1, Model2,
        form=form, extra=extra, can_delete=can_delete
    )



class DailyShiftNoteForm(forms.ModelForm):
    start_date_time = forms.DateTimeField(required=False,widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_date_time = forms.DateTimeField(required=False,widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
 
    apply_description_validation = False 
    
    class Meta:
        model = DailyShiftCaseNote
        fields = '__all__'
        widgets = {
            'shift': forms.HiddenInput(),
            'company':forms.HiddenInput(),
            # 'sno':forms.HiddenInput(),
            'vehicle_used': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'required': False}),
            'description':forms.Textarea(attrs={'rows': 1, 'cols': 40}),

         

        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        company = kwargs.pop('company', None)
        super(DailyShiftNoteForm, self).__init__(*args, **kwargs)
        self.fields['start_date_time'].widget.attrs['min']='1900-01-01T00:00'
        self.fields['end_date_time'].widget.attrs['min']='1900-01-01T00:00'
        self.fields['start_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        self.fields['end_date_time'].widget.attrs['max'] = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
        if 'client_progress_note_detail' in request.resolver_match.url_name:
            self.fields['client'].widget.attrs['disabled'] = True
            self.fields['employee'].widget.attrs['disabled'] = True

        elif 'dailyshift_add_employee' in request.resolver_match.url_name:

            client_initial = self.initial.get('client', None)
            self.fields['client'].initial = client_initial
            self.fields['client'].queryset = Client.bells_manager.filter(id=client_initial)
            self.fields['employee'].widget = forms.HiddenInput()
            self.fields['start_date_time'].required = True
            self.fields['end_date_time'].required = True
            
            # if has_user_permission(request.user, 'company_admin.update_progress_notes_own_team') or has_user_permission(request.user, 'company_admin.update_progress_notes_all'):
            #     self.fields['description'].required = True
            # else:
            #     self.fields['description'].required = False

        elif request.resolver_match.url_name == 'dailyshift_edit':
            # self.apply_description_validation = True
            client_initial = self.initial.get('client', None)
            self.fields['client'].queryset = Client.bells_manager.filter(id=client_initial)
            self.fields['employee'].widget = forms.HiddenInput()
            print("setting fields to be readonly")
            self.fields['client'].widget.attrs['readonly'] = True
            self.fields['start_date_time'].widget.attrs['readonly'] = True
            self.fields['description'].required = False
            self.fields['end_date_time'].widget.attrs['readonly'] = True
            
        elif 'dailyshift_view' in request.resolver_match.url_name :
            self.apply_description_validation = True
            client_initial = self.initial.get('client', None)
            self.fields['client'].queryset = Client.bells_manager.filter(id=client_initial)
            self.fields['client'].widget.attrs['disabled'] = True
            self.fields['employee'].widget = forms.HiddenInput()
            self.fields['employee'].widget.attrs['readonly'] = True
            self.fields['end_date_time'].widget.attrs['readonly'] = True
            print("setting fields to be readonly")
            self.fields['start_date_time'].widget.attrs['readonly'] = True
            self.fields['description'].widget.attrs['readonly'] = True
            self.fields['vehicle_used'].widget.attrs['disabled'] = 'True'
            self.fields['distance_traveled'].widget.attrs['readonly'] = True



        elif 'dailyshift_edit_employee' in request.resolver_match.url_name :
            
            self.apply_description_validation = True
            client_initial = self.initial.get('client', None)
            self.fields['client'].widget.attrs['readonly'] = True
            self.fields['client'].queryset = Client.bells_manager.filter(id=client_initial)
            self.fields['employee'].widget = forms.HiddenInput()
            self.fields['employee'].widget.attrs['readonly'] = True
            self.fields['end_date_time'].widget.attrs['readonly'] = True
            print("setting fields to be readonly")
            self.fields['start_date_time'].widget.attrs['readonly'] = True

        else:
            self.fields['client'].widget.attrs['disabled'] = False
            self.fields['employee'].widget.attrs['disabled'] = False
            self.fields['employee'].widget = forms.HiddenInput()




    def clean(self):
        cleaned_data = super().clean()
        start_date_time = cleaned_data.get('start_date_time')
        end_date_time = cleaned_data.get('end_date_time')

        if end_date_time and end_date_time <= start_date_time:
            self.add_error('end_date_time', "End date and time cannot be before the start date and time.")
    
        return cleaned_data

   

    
class DailyShiftCaseNoteForm(forms.ModelForm):
    class Meta:
        model = DailyShiftCaseNote
        fields = '__all__'

    widgets = {
        "employee": forms.TextInput(attrs={"required": True}),
        "client": forms.TextInput(attrs={"required": True}),
        "start_date": forms.TextInput(attrs={"required": True}),
        "start_time": forms.TextInput(attrs={"required": True}),
        "end_date": forms.TextInput(attrs={"required": True}),
        "end_time": forms.TextInput(attrs={"required": True}),
        "description": forms.TextInput(attrs={"required": True}),
    }

    def __init__(self, *args, **kwargs):
   
        super(DailyShiftNoteForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.attrs['min']='1900-01-01T00:00'
        self.fields['end_date'].widget.attrs['min']='1900-01-01T00:00'
        self.fields['start_date'].widget.attrs['max'] = date.today()
        self.fields['end_date'].widget.attrs['max'] = date.today()

    def clean_employee(self, user=None):
        if user is not None:
            userdata = Person.objects.filter(email=user.email)
            if userdata.exists():
                employee = user
                return employee
            raise ValidationError("Employee not found")
        raise ValidationError("User not found")

    def clean_client(self, *args, **kwargs):
        try:
            client_id = self.cleaned_data.get("client")
            client_data = client.objects.get(id=client_id)
            client = client_data
            return client
        except:
            raise ValidationError("Please choose the client")

    def clean_start_date(self, *args, **kwargs):
        start_date = self.cleaned_data.get("start_date", '')
        if start_date == "":
            raise ValidationError("Please enter the start date")
        if start_date > date.today():
                self.add_error('start_date', 'Start date-time cannot be in the future.')
        if start_date.year < 1900:
            self.add_error('start_date', 'Start date-time cannot be earlier than the year 1900.')
        return start_date

    def clean_end_date(self, *args, **kwargs):
        end_date = self.cleaned_data.get("end_date", '')
        if end_date == "":
            raise ValidationError("Please enter the end date")
        if end_date > date.today():
            self.add_error('end_date_time', 'End date-time cannot be in the future.')
        if end_date.year < 1900:
            self.add_error('end_date_time', 'End date-time cannot be earlier than the year 1900.')
        return end_date

    def clean_description(self, *args, **kwargs):
        description = self.cleaned_data.get("description")
        if len(description) < 50:
            raise ValidationError(
                "Description should be minimum of 50 alphabets")
        return description

CHOICES_GENDER = (
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
)




class EmployeePersonForm(forms.ModelForm):
   
    phone_number_validator = RegexValidator(
        regex=r'^\d{10,}$',
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
            'is_active': forms.HiddenInput(),
            'gender': forms.Select(attrs={'required': True}),

        }

    def __init__(self, *args, **kwargs):
        super(EmployeePersonForm, self).__init__(*args, **kwargs)
 

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            self.phone_number_validator(phone_number)
        return phone_number
    



class EmployeeProfileForm(forms.ModelForm):
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
            'template': forms.HiddenInput(), 
            'employment_type':forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'date_of_birth': forms.DateInput()  ,
            'role': forms.HiddenInput(),
            'departments': forms.CheckboxSelectMultiple(),
            'address': forms.Textarea(attrs={'rows': 1, 'cols': 40}),
        }
    
    
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].widget.attrs['min'] = '1900-01-01'
        self.fields['date_of_birth'].widget.attrs['max'] = datetime.now().strftime('%Y-%m-%d')
        
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

EmployeeProfileFormset = inlineformset_factory(
    Person, Employee,
    form=EmployeeProfileForm,
    extra=1,
    can_delete=True
)


class IDsAndChecksDocumentsForm(forms.ModelForm):
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    
    class Meta:
        model = IDsAndChecksDocuments
        fields = ['id', 'employee', 'name', 'expiry_date', 'file','status']
        widgets = {
            'employee': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'expiry_date': forms.DateInput(),
            'id': forms.HiddenInput(),
            'status': forms.HiddenInput(),


        }

    def __init__(self, *args, **kwargs):
        predefined_name = kwargs.get('initial', {}).get('name')
        super(IDsAndChecksDocumentsForm, self).__init__(*args, **kwargs)
        self.initial['name'] = predefined_name 
        self.fields['expiry_date'].widget.attrs['min'] = datetime.now().strftime('%Y-%m-%d')
    
    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            valid_extensions = ['.jpg', '.png', '.pdf' , '.jpeg','.heic']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("File must be either a PDF, JPG, JPEG, HEIC, or PNG.")
        return file

class QualificationDocumentsForm(forms.ModelForm):
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
    class Meta:
        model = QualificationDocuments
        fields = ['employee','name','expiry_date','file','status']
        widgets = {
            'employee': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'expiry_date': forms.DateInput(),
            'id': forms.HiddenInput(),
            'status': forms.HiddenInput(),

        }
    def __init__(self, *args, **kwargs):
        qualification_predefined_name = kwargs.get('initial', {}).get('name') 
        super(QualificationDocumentsForm, self).__init__(*args, **kwargs)
        self.initial['name'] = qualification_predefined_name 
        self.fields['expiry_date'].widget.attrs['min'] = datetime.now().strftime('%Y-%m-%d')

    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            valid_extensions = ['.jpg', '.png', '.pdf' , '.jpeg']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("File must be either a PDF, JPG, JPEG, or PNG.")
        return file

class OtherDocumentsForm(forms.ModelForm):
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}),required=False )
    class Meta:
        model = OtherDocuments
        fields = ['employee','name', 'file', 'expiry_date','status']
        widgets = {
            'employee': forms.HiddenInput(),
            'company': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'readonly': 'readonly'}),
            'expiry_date': forms.DateInput(),
            'status': forms.HiddenInput(),

        }
    def __init__(self, *args, **kwargs):
        other_predefined_name = kwargs.get('initial', {}).get('name')
        super(OtherDocumentsForm, self).__init__(*args, **kwargs)
        self.initial['name'] = other_predefined_name 
        self.fields['expiry_date'].widget.attrs['min'] = datetime.now().strftime('%Y-%m-%d')
        
    def clean_file(self):
        file = self.cleaned_data.get('file', False)
        if file:
            valid_extensions = ['.jpg', '.png', '.pdf' , '.jpeg', 'heic']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError("File must be either a PDF, JPG, JPEG, HEIC, or PNG.")
        return file
    



class ClientAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClientAssignment
        fields = ['clients', 'employee']
        widgets = {
            'clients': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
        }

class ClientAssignmentDetailForm(forms.ModelForm):
    class Meta:
        model = ClientAssignmentDetail
        fields = ['client', 'is_deleted']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'is_deleted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class EmployeeClientAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClientAssignment
        fields = ['clients', 'employee']



class EmployeeShiftsForm(forms.ModelForm):
    class Meta:
        model = Shifts
        fields = [
            'employee', 
            'client', 
            'company', 
            'author', 
            'start_date_time', 
            'end_date_time', 
            'shift_type', 
            'status', 
            'total_hour'
        ]
        widgets = {
            'start_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(EmployeeShiftsForm, self).__init__(*args, **kwargs)
    
        # if request and 'dailyshift_edit_employee' in request.resolver_match.url_name or 'dailyshift_view' in request.resolver_match.url_name: 
        #     self.fields['shift_type'].widget.attrs['readonly'] = True
        #     self.fields['shift_type'].widget.attrs['disabled'] = True

        # if has_user_permission(request.user, 'company_admin.update_progress_notes_own'):
        #     self.fields['shift_type'].widget.attrs['readonly'] = True
        #     self.fields['shift_type'].widget.attrs['disabled'] = True

class EmployeeAcknowledgementForm(forms.ModelForm):
    class Meta:
        model = EmployeePolicyAcknowledgment
        fields = '__all__'
        
        widgets = {
            'employee': forms.HiddenInput(),
            'policy': forms.HiddenInput(),
            'is_acknowledged': forms.CheckboxInput(attrs={'required': True}),
        }
