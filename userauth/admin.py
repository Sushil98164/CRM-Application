from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Employee
from django.contrib.auth.models import Group, Permission
from django.db.models.functions import Lower
from django import forms
from company_admin.models import CompanyGroup
from rangefilter.filters import DateRangeFilter

PERSON = get_user_model()


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            groups = Group.objects.filter(
                id__in=CompanyGroup.bells_manager.filter(company=self.instance.company).values_list('group_id', flat=True)
            ).order_by(Lower('name'))

            choices = [
                (group.id, group.name.replace(" - user", "") if " - user" in group.name else group.name)
                for group in groups
            ]   
            self.fields['template'].queryset = groups
            self.fields['template'].choices = choices

@admin.register(PERSON)
class PersonAdmin(UserAdmin):
    """User Admin"""
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2',)
        }),)
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    list_display = (
        "username",
        "first_name",
        "last_name",
        "gender",
        "profile_image",
        "phone_number",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_filter = ('is_staff', 'is_active', 'is_superuser',)

    fieldsets = (
        ("Essentials", {"fields": ("username", "password",
                                   "last_login" ,"date_joined", )}),
        ("Personal Information", {
         "fields": ("first_name", "last_name", "email", "phone_number","profile_image", "gender")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", 'user_permissions')}),

    )

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["date_joined", "last_login", "modified_at"]
        else:
            return []



admin.site.register(Permission)
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    form = EmployeeForm 
    exclude = ['created_by', 'updated_by','role']
    list_display = ['person', 'company','template','created_by', 'updated_by','updated_at','created_at','is_deleted']
    list_filter = (
        'company',
        'is_deleted',
        ('created_at', DateRangeFilter),
    )
    raw_id_fields = ('person', 'company',)
    ordering = ['created_at']

    
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["id", "person", "preferred_name", "date_of_birth", "fix_line", "residential_address", "fund_management_by",'created_at', 'updated_at', 'is_deleted']
    list_filter = ["company", "date_of_birth", "fund_management_by",'is_deleted','created_at']
    search_fields = ["person__first_name", "person__last_name", "preferred_name", "residential_address", "fund_management_by"]
    raw_id_fields = ("person",)


@admin.register(ClientEmergencyDetail)
class ClientEmergencyDetailsAdmin(admin.ModelAdmin):
    list_display = ['client','emergency_name','emergency_fix_line','emergency_phone_number',
                    'emergency_mail','emergency_person_gender','is_authorised_representative',
                    ]
    list_filter = ["client", "emergency_person_gender", "is_authorised_representative"]
    search_fields = ["client__person__first_name", "client__person__last_name", "emergency_name", 
                     "emergency_phone_number", "emergency_mail"]
    raw_id_fields = ('client',)


@admin.register(ClientNDISDetail)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['client','is_individual_ndis_participant','is_any_service_agreements','is_any_consents_obtained','plan_start_date',
                    'plan_end_date','plan_goals_and_objectives','plan_funding_allocation',
                    'participant_number']
    list_filter = ['is_individual_ndis_participant', 'is_any_service_agreements', 
                   'is_any_consents_obtained', 'service_fund_type']
    
    search_fields = ['client__person__first_name', 'client__person__last_name', 
                     'participant_number', 'ndis_services', 'description']
    raw_id_fields = ('client',)

@admin.register(ClientMedicalDetail)
class ClientMedicalDetailsAdmin(admin.ModelAdmin):
    list_display = ['client','is_any_disabilities','primary_disability','secondary_disability','medical_history',
                    'is_any_medication','medication_details','doctor_consent','allergies_and_sensitives','healthcare_provider_info']
    
    list_filter = ['is_any_disabilities', 'is_any_medication', 'doctor_consent']
    
    search_fields = ['client__person__first_name', 'client__person__last_name', 
                     'primary_disability', 'secondary_disability', 'medical_history', 
                     'medication_details', 'allergies_and_sensitives', 'healthcare_provider_info']
    raw_id_fields = ('client',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'manager', 'author', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'company__name', 'manager__person__first_name', 'manager__person__last_name')
    list_filter = ('company', 'manager','is_deleted','created_at')

