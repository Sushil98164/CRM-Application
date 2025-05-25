from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from bellscrm_admin.models import Company
from django.contrib.auth.models import Group
from userauth.constants import *
from utils.base_models import TimestampModel
from utils.model_permissions import COMPANY_TERMS_AND_CONDITIONS_POLICY_PERMISSIONS, CLIENT_PERMISSIONS, EMPLOYEE_PERMISSIONS, DEPARTMENTS,USERAUTH_PERMISSIONS
from userauth.utils import BellsManager
from django.contrib.auth.models import Permission

class Person(AbstractUser, TimestampModel):
    phone_number=models.CharField(max_length=15,null=True,blank=True)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    last_visited = models.DateTimeField(default=timezone.now)
    gender = models.CharField(max_length=20, choices=CHOICES_GENDER,null=True,blank=True)
    is_account_approved_by_admin = models.BooleanField(default=False)
    email = models.EmailField(unique=True, error_messages={'unique': 'This email address is already associated with an account.'})
    is_active = models.BooleanField(default=True, db_index=True)
    profile_image=models.ImageField(upload_to='profile_images', blank=True)
    

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'
        permissions = USERAUTH_PERMISSIONS

    def __str__(self):
        return f"{self.first_name} {self.last_name}"




class Employee(TimestampModel):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name="employee")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees")
    template = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="employees", null=True, blank=True)
    role = models.IntegerField(choices=EMPLOYEE_ROLE, default=3, null=True, blank=True)
    departments = models.ManyToManyField('Department', related_name="department_employees", blank=True)
    objects = models.Manager()
    bells_manager = BellsManager()
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_phone_number = models.CharField(max_length=50, null=True, blank=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="created_employees")
    employment_type = models.CharField(max_length=255, choices = EMPLOYMENT_TYPE_CHOICES , default="Permanent staff")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_role = self.role


    def is_admin_role(self):
        return self.role in [1, 2]
    
    def is_admin_role_only(self):
        return self.role in [1]
    
    def is_manager_role(self):
        return self.role in [2]
    
    def has_perm(self, perm, obj=None):
        return self.person.has_perm(perm, obj)

    def has_module_perms(self, app_label):
        return self.person.has_module_perms(app_label)
    
    
    
    
    def save(self, *args, **kwargs):
        # print(f"Saving Employee instance: {self}")
        
        # Fetch existing employee instance before saving
        employee_instance = Employee.bells_manager.filter(pk=self.pk).first()
        existing_template = employee_instance.template if employee_instance else None

        super().save(*args, **kwargs)

        # print(f"New template (before reassigning): {self.template}")

        # Ensure template does not change when updated from Django Admin
        if existing_template and existing_template != self.template:
            # print(f"Restoring existing template: {existing_template}")
            requested_template = self.template
            self.template = existing_template
            super().save(update_fields=["template"])  
        else:
            requested_template = None
            
        # Apply permissions based on the existing or assigned template
        if existing_template:
            # print(f"Using existing template permissions: {existing_template}")
            template_permissions = (
                requested_template.permissions.all() if requested_template and requested_template.permissions.exists()
                else existing_template.permissions.all()
            )
            self.person.user_permissions.clear()
            for permission in template_permissions:
                # print(f"Adding permission: {permission}")
                self.person.user_permissions.add(permission)
        elif self.template:
            # print(f"Using new template permissions: {self.template}")
            template_permissions = self.template.permissions.all()
            self.person.user_permissions.clear()
            for permission in template_permissions:
                # print(f"Adding permission: {permission}")
                self.person.user_permissions.add(permission)
        else:
            # print("No template assigned, clearing permissions.")
            self.person.user_permissions.clear()

        self.person.save()
        # print(f"Finished saving employee: {self}")

        
        
    # def save(self, *args, **kwargs):
    #     # Check if this is a new instance or template has changed
    #     is_new = not self.pk
    #     template_changed = False
        
    #     if not is_new:
    #         old_instance = Employee.objects.get(pk=self.pk)
    #         template_changed = old_instance.template != self.template

    #     super().save(*args, **kwargs)

    #     if is_new or template_changed:
    #         if self.template:
    #             # Get all permissions associated with the template group
    #             template_permissions = self.template.permissions.all()
                
    #             # Clear existing permissions if template has changed
    #             if template_changed:
    #                 self.person.user_permissions.clear()
                
    #             # Assign new permissions to the person
    #             for permission in template_permissions:
    #                 self.person.user_permissions.add(permission)
    #         else:
    #             # If no template is assigned, clear all permissions
    #             self.person.user_permissions.clear()
            
    #         # Save the person instance to ensure permissions are updated
    #         self.person.save()
    
    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        permissions = EMPLOYEE_PERMISSIONS

    def __str__(self):
        return str(self.person) if self.person_id else "Unknown person"



class Department(TimestampModel):
    name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    # manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_departments", limit_choices_to={'role': 2})
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_departments")
    description = models.TextField(null=True, blank=True)
    # employees = models.ManyToManyField(Employee, related_name="assigned_departments", blank=True,limit_choices_to=~models.Q(role__in=[1, 2]))
    employees = models.ManyToManyField(Employee, related_name="assigned_departments", blank=True)
    author = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments_created')
    objects = models.Manager()
    bells_manager = BellsManager()
    
    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        
        permissions = DEPARTMENTS  


    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Client(TimestampModel):
    person= models.OneToOneField(Person, on_delete=models.CASCADE,related_name="clients")
    company = models.ForeignKey(Company, related_name="client_company", on_delete=models.CASCADE)
    preferred_name = models.CharField(max_length=100,null=True,blank=True)
    date_of_birth = models.DateField(blank=False)
    fix_line = models.CharField(max_length=20,null=True,blank=True)
    residential_address = models.TextField(null=True,blank=True)
    fund_management_by = models.CharField(max_length=50,null=True,blank=True)
    objects = models.Manager()  
    bells_manager = BellsManager()  

    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        
        permissions = CLIENT_PERMISSIONS  

    def __str__(self):
        if self.preferred_name is None:
            return f"{self.person}"
        return f"{self.person}"

   
    

class ClientEmergencyDetail(TimestampModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="emergency_contact_details")
    emergency_name = models.CharField(max_length=50,null=True,blank=True)
    emergency_fix_line = models.CharField(max_length=50,null=True,blank=True)
    emergency_phone_number = models.CharField(max_length=50,null=True,blank=True)
    emergency_mail = models.EmailField(max_length=254,null=True,blank=True)
    emergency_person_gender = models.IntegerField(choices = CHOICES_GENDER,null=True,blank=True)
    is_authorised_representative = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )

    class Meta:
        verbose_name = 'ClientEmergencyDetail'
        verbose_name_plural = 'ClientEmergencyDetails'

    def __str__(self):
        return f"{self.client}"

class ClientNDISDetail(TimestampModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="ndis_details")
    
    is_individual_ndis_participant = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )
    is_any_service_agreements = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )
    is_any_consents_obtained = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )

    plan_start_date = models.DateField(null=True,blank=True)
    plan_end_date = models.DateField(null=True,blank=True)
    plan_goals_and_objectives = models.TextField(null=True,blank=True)
    plan_funding_allocation = models.TextField(null=True,blank=True)
    participant_number = models.CharField(max_length=50,null=True,blank=True)
    service_fund_type = models.CharField(
        max_length=100,
        choices=SERVICE_FUND_TYPE_CHOICES,
        default='NDIS',
    )
    ndis_services = models.CharField(
        max_length=200,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)
    hours_requested = models.IntegerField(null=True, blank=True)
    class Meta:
        verbose_name = 'ClientNDISDetail'
        verbose_name_plural = 'ClientNDISDetails'

    def __str__(self):
        return f"{self.client}"

class ClientMedicalDetail(TimestampModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="medical_details")
    is_any_disabilities = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )
    primary_disability = models.TextField(null=True,blank=True)
    secondary_disability = models.TextField(null=True,blank=True)
    medical_history = models.TextField(null=True,blank=True)
    is_any_medication = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )
    medication_details = models.TextField(null=True,blank=True)
    doctor_consent = models.IntegerField(
        choices=RADIO_CHOICE,
        default=0,
    )
    allergies_and_sensitives = models.TextField(null=True,blank=True)
    healthcare_provider_info = models.TextField(null=True,blank=True)

    class Meta:
        verbose_name = 'ClientMedicalDetail'
        verbose_name_plural = 'ClientMedicalDetails'

    def __str__(self):
        return f"{self.client}"
    

