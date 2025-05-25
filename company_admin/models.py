from django.db import models
from userauth.models import *
from bellscrm_admin.models import Company
from django.core.validators import MaxValueValidator
from rostering.models import Shifts
from django.db.models import Case, When, Value, IntegerField
from ckeditor.fields import RichTextField
from django.db.models import Q
from django.db.models.functions import Lower
from utils.model_permissions import INCIDENT_PERMISSIONS, PROGRESS_NOTES_PERMISSIONS, RISK_ASSESSMENT_PERMISSIONS, COMPANY_TERMS_AND_CONDITIONS_POLICY_PERMISSIONS,CLIENT_EMPLOYEE_ASSIGNMENT_PERMISSIONS
from .constants import *

class MandatoryIncident(TimestampModel):
    """Mandatory Incident Model"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = "mandatory_incidents")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name = "mandatory_incidents")
    company= models.ForeignKey(Company, on_delete=models.CASCADE, related_name = "mandatory_incidents")
    sno = models.IntegerField(default = 1)
    report_code = models.CharField(max_length=20)
    incident_location = models.CharField(max_length=150)
    incident_date_time = models.DateTimeField(null=True,blank=True)
    is_injured = models.BooleanField(default = False)
    injured_person = models.TextField(null=True,blank=True)
    action_taken = models.TextField(blank=True)
    any_witness = models.BooleanField(default = False)
    witness_name = models.CharField(max_length=100,null=True,blank=True)
    witness_phone_number  = models.CharField(max_length=50,null=True,blank=True)
    witness_email = models.EmailField(max_length=250,null=True,blank=True)
    status = models.CharField(max_length = 100, choices=CHOICES_INCIDENT_REOPORTS, default="New")
    story_of_incident = models.TextField()
    is_mandatory_aware = models.BooleanField(default = False)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    
    class Meta:
        """Meta Class"""
        verbose_name = 'MandatoryIncident'
        verbose_name_plural = 'MandatoryIncidents'

        unique_together = ('company', 'sno')

    def __str__(self):
        return f"{self.id} {self.report_code}"


class MandatoryIncidentAttachment(TimestampModel):
    incident = models.ForeignKey(MandatoryIncident, on_delete=models.CASCADE,null=True,blank=True, related_name = "mandatory_incident_attachments")
    file = models.FileField(upload_to='mandatory_incident_attachments/',null=True,blank=True, max_length=255)
    objects = models.Manager()
    bells_manager = BellsManager()

    class Meta:
        verbose_name = 'MandatoryIncidentAttachment'
        verbose_name_plural = 'MandatoryIncidentAttachments'

    def __str__(self):
        return f"{self.incident}"

class Incident(TimestampModel):
    """Incident Model"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = "incidents")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name = "incidents")
    company= models.ForeignKey(Company, on_delete=models.CASCADE, related_name = "incidents")
    investigation_hierarchy = models.ForeignKey('InvestigationHierarchy', on_delete=models.SET_NULL, null=True, blank=True, related_name = "incidents")
    incident_location = models.CharField(max_length=150)
    incident_date_time = models.DateTimeField(null=True,blank=True)
    is_injured = models.BooleanField(default = False)
    injured_person = models.CharField(max_length=150,null=True,blank=True)
    action_taken = models.TextField(blank=True)
    any_witness = models.BooleanField(default = False)
    witness_name = models.CharField(max_length=100,null=True,blank=True)
    witness_phone_number  = models.CharField(max_length=50,null=True,blank=True)
    witness_email = models.EmailField(max_length=250,null=True,blank=True)
    pre_incident_details = models.TextField(null=True,blank=True)
    is_mandatory_aware = models.BooleanField(default = False)
    report_type = models.CharField(max_length = 100, choices=TYPE_OF_INCIDENT_REPORT,default="Incident")
    report_code = models.CharField(max_length=20,null=True, blank=True)
    sno = models.IntegerField(default = 1, null=True, blank=True)
    status = models.CharField(max_length = 100, choices=CHOICES_INCIDENT_REOPORTS, default="New")
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    inbetween_incident_details = models.TextField(blank=True, null=True)
    post_incident_details = models.TextField(blank=True, null=True)
    incident_severity_level= models.CharField(max_length=255, choices=TYPE_OF_SEVERITY_LEVEL)
    specific_severity_level = models.CharField(max_length=255, blank=True, null=True)
    incident_category = models.CharField(max_length=255,choices=INCIDENT_CATEGORY_CHOICES, null=True,blank=True)
    define_other_category = models.TextField(null=True,blank=True)
    incident_classification = models.CharField(max_length=255,choices=INCIDENT_CLASSIFICATION_CHOICES,null=True,blank=True)
    employees_involved = models.CharField(max_length=255, choices=EMPLOYEE_INVOLVED ,default='no')
    is_investigation_email_sent = models.BooleanField(default=True)


    class Meta:
        """Meta Class"""
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'

        # unique_together = ('company', 'sno','report_type')
        
        permissions = INCIDENT_PERMISSIONS


    def __str__(self):
        return f"{self.id} {self.report_code}"

    
    @classmethod
    def order_by_status(cls, queryset):
        """Custom method to order incidents by status (New, In-progress, Closed) and then by created_at."""
        status_order = Case(
            When(status="New", then=Value(1)),
            When(status="InProgress", then=Value(2)),
            When(status="Closed", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
        return queryset.annotate(status_order=status_order).order_by('status_order')


class IncidentAttachment(TimestampModel):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE,null=True,blank=True, related_name = "incident_attachments")

    file = models.FileField(upload_to='incident_attachments/',null=True,blank=True, max_length=255)
    objects = models.Manager()
    bells_manager = BellsManager()

    class Meta:
        verbose_name = 'IncidentAttachment'
        verbose_name_plural = 'IncidentAttachments'

    def __str__(self):
        return f"{self.incident}"

class DailyShiftCaseNote(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = "daily_shift_case_notes")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name = "daily_shift_case_notes")
    company= models.ForeignKey(Company, on_delete=models.CASCADE, related_name = "daily_shift_case_notes")
    shift = models.ForeignKey(Shifts, on_delete=models.SET_NULL, related_name="daily_shift_case_notes", null=True, blank=True)
    sno = models.IntegerField(default=1, null= True, blank = True)
    start_date_time = models.DateTimeField(blank=True,null=True)
    end_date_time = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    vehicle_used = models.BooleanField(default=False)
    distance_traveled = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(200)])
    file = models.FileField(upload_to='progress_notes_attachments/',null=True,blank=True, max_length=255)

    class Meta:
        verbose_name = 'DailyShiftCaseNote'
        verbose_name_plural = 'DailyShiftCaseNotes'
        # unique_together = ('company', 'sno')
        permissions =PROGRESS_NOTES_PERMISSIONS



    def __str__(self):
        return f"{self.id} {self.company}-{self.sno}"
    

     

class RiskType(TimestampModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Risk Type'
        verbose_name_plural = 'Risk Types'

    def __str__(self):
        return self.name

class RiskArea(TimestampModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    risk_type = models.ForeignKey(RiskType, on_delete=models.CASCADE, related_name="risk_areas")

    class Meta:
        verbose_name = 'Risk Area'
        verbose_name_plural = 'Risk Areas'

    def __str__(self):
        return self.name

class RiskAssessment(TimestampModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="risk_assessment")
    assessment_date = models.DateField(null=True, blank=True)
    reviewed_date = models.DateField(null=True, blank=True)
    prepared_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="prepared_by")
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()
    
    class Meta:
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'
        
        permissions = RISK_ASSESSMENT_PERMISSIONS


    def __str__(self):
        return f"Risk Assessment for {self.client}"



class RiskAssessmentDetail(TimestampModel):
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE,related_name="assessment_details")
    risk_type = models.ForeignKey(RiskType, on_delete=models.CASCADE,null=True, blank=True)
    choosen_risk_area = models.TextField(null=True, blank=True)
    risk_to_self =  models.CharField(max_length=5, null=True, blank=True)
    risk_to_self_category =  models.CharField(max_length = 100, choices=RISK_CATEGORY,  null=True, blank=True)
    risk_to_staff =  models.CharField(max_length=5, null=True, blank=True)
    risk_to_staff_category =  models.CharField(max_length = 100, choices=RISK_CATEGORY,  null=True, blank=True)
    risk_to_other =  models.CharField(max_length=5, null=True, blank=True)
    risk_to_other_category =  models.CharField(max_length = 100, choices=RISK_CATEGORY,  null=True, blank=True)
    source_of_information = models.CharField(max_length=255, null=True, blank=True)
    comments =  models.CharField(max_length=255, null=True, blank=True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()

    class Meta:
        verbose_name = 'Risk Assessment Detail'
        verbose_name_plural = 'Risk Assessment Details'

  
    def __str__(self):
        return f"Documentation for {self.risk_assessment.client}"

class RiskDocumentationApproval(TimestampModel):
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, related_name="documentation")
    completed_by = models.CharField(max_length=255, null=True, blank=True)
    authorized_by = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()
    class Meta:
        verbose_name = 'Risk Documentation'
        verbose_name_plural = 'Risk Documentations'

    def __str__(self):
        return f"Documentation for {self.risk_assessment.client}"


class RiskMoniterControl(TimestampModel):
    risk_assessment =models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, related_name="management_approval")
    reviewed_date = models.DateField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=255, null=True, blank=True)
    authorized_by = models.CharField(max_length=255, null=True, blank=True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()

    class Meta:
        verbose_name = 'Risk Management Approval'
        verbose_name_plural = 'Risk Management Approvals'

    def __str__(self):
        return f"Management Approval for {self.risk_assessment.client}"
    
    

class Comment(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="admin_comments")
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=100, choices=TYPE_OF_INCIDENT_REPORT, default="Incident")
    content = models.TextField(null=True,blank=True)
    cause_of_incident = models.TextField(null=True,blank=True)
    prevention_of_incident = models.TextField(null=True,blank=True)

    def __str__(self):
        return f'Comment by {self.employee.person.first_name}'

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        

class IncidentTaggedEmployee(TimestampModel):
    incident = models.ForeignKey(Incident,on_delete=models.CASCADE,related_name='tagged_incident')
    tagged_employee = models.ForeignKey(Employee,on_delete=models.CASCADE,related_name='tagged_employee')
    description = models.TextField(null=True,blank=True)
    tagged_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='tagged_by_user')
    untagged_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='untagged_by_user')
    tagged_to_employee = models.ForeignKey(Employee,on_delete=models.CASCADE,related_name='tagged_to_employee')
    tagged_to_client  = models.ForeignKey(Client,on_delete=models.CASCADE,related_name='tagged_to_client')
    is_removed = models.BooleanField(default=False)
    objects = models.Manager()  
    bells_manager = BellsManager()

    def __str__(self):
        return f'Tagged employee :{self.tagged_employee.person.first_name}  in Incident : {self.incident.id} on {self.created_at.strftime("%Y-%m-%d")}'

    class Meta:
        verbose_name = 'Incident Tag'
        verbose_name_plural = 'Incident Tags'

class CompanyTermsAndConditionsPolicy(TimestampModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='terms_and_conditions_policy')
    type = models.CharField(max_length = 255 , choices = POLICY_CHOICES)
    description = RichTextField(blank=True,null=True)
    objects = models.Manager()  
    bells_manager = BellsManager()

    class Meta:
        verbose_name = 'Company Terms and Conditions Policy'
        verbose_name_plural = 'Company Terms and Conditions Policies'
        unique_together = ('company', 'type')
        
        permissions = COMPANY_TERMS_AND_CONDITIONS_POLICY_PERMISSIONS

    
        
    def __str__(self):
        return f"{self.company.name} - {self.get_type_display()}"
    
    


class EmployeePolicyAcknowledgment(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='policy_acknowledgments',null=True,blank=True)
    policy = models.ForeignKey(CompanyTermsAndConditionsPolicy, on_delete=models.CASCADE, related_name='acknowledgments')
    is_acknowledged = models.BooleanField(default=False)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()


    class Meta:
        verbose_name = 'Employee Policy Acknowledgment'
        verbose_name_plural = 'Employee Policy Acknowledgments'

    def __str__(self):
        return f"{self.employee} - {self.policy.get_type_display()} - Acknowledged: {'Yes' if self.is_acknowledged else 'No'}"
  
class ClientEmployeeAssignment(TimestampModel):
    client = models.ForeignKey(Client, on_delete = models.CASCADE, related_name = 'client_employee_assignments', null=True, blank = True)
    employee =  models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = 'client_employee_assignments', null=True, blank= True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()

    class Meta: 
        verbose_name = 'Client Employee Assignment'
        verbose_name_plural = 'Client Employee Assignments'
        permissions = CLIENT_EMPLOYEE_ASSIGNMENT_PERMISSIONS  
    def __str__(self):
        return f"{self.employee.person.first_name} assigned to {self.client.person.first_name} by {self.created_by}"

    @classmethod
    def get_clients_by_employee(cls, employee_id, company_id):
        """
        Fetch all clients assigned to a specific employee within the company
        Returns queryset of Client objects
        """
        return Client.bells_manager.filter(
            client_employee_assignments__employee_id=employee_id,
            client_employee_assignments__is_deleted=False,
            company_id=company_id
        ).distinct().order_by(Lower('person__first_name'))

    @classmethod
    def get_employees_by_client(cls, client_id, company_id):
        """
        Fetch all employees assigned to a specific client within the company
        Returns queryset of Employee objects
        """
        return Employee.bells_manager.filter(
            client_employee_assignments__client_id=client_id,
            client_employee_assignments__is_deleted=False,
            company_id=company_id
        ).distinct().order_by(Lower('person__first_name'))

class DepartmentClientAssignment(TimestampModel):
    department = models.ForeignKey(Department, on_delete = models.CASCADE, related_name = 'department_client_assignments', null=True, blank = True)
    client =  models.ForeignKey(Client, on_delete=models.CASCADE, related_name = 'department_client_assignments', null=True, blank= True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()

    class Meta: 
        verbose_name = 'Department Client Assignment'
        verbose_name_plural = 'Department Client Assignments'

    def __str__(self):
        return f"{self.client.person.first_name} assigned to {self.department.name} by {self.created_by}"
    
    @classmethod
    def get_manager_department_data(cls, manager_id, company_id):
        """
        Fetch clients and related employees for a manager's departments within the company
        """
        # Get base departments managed by the manager in the company
        departments = Department.bells_manager.filter(
            manager_id=manager_id,
            company_id=company_id
        )
        
        # Get clients from these departments in the company
        clients = Client.bells_manager.filter(
            department_client_assignments__department__in=departments,
            department_client_assignments__is_deleted=False,
            company_id=company_id
        ).distinct().order_by(Lower('person__first_name'))

        # Get employees through client relationships in the company
        employees = Employee.bells_manager.filter(
            Q(client_employee_assignments__client__in=clients,
              client_employee_assignments__is_deleted=False) |
            Q(id=manager_id),
            company_id=company_id
        ).distinct().order_by(Lower('person__first_name'))

        return {
            'departments': departments,
            'clients': clients,
            'employees': employees
        }




class CompanyGroup(TimestampModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="company_groups")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_groups")
    objects = models.Manager()
    bells_manager = BellsManager()

    class Meta:
        unique_together = ('group', 'company') 

    def __str__(self):
        return f"{self.company.name} - {self.group.name}"
    


class IncidentHierarchyTimeStamp(models.Model):
    created_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name="created_%(class)s_set"
    )
    updated_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name="updated_%(class)s_set"
    )
    class Meta:
        abstract = True
        

class InvestigationHierarchy(IncidentHierarchyTimeStamp,TimestampModel):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="investigation_hierarchy"
    )
    hierarchy_timeline_days = models.PositiveIntegerField()
    levels = models.PositiveIntegerField()
    category = models.CharField(
        max_length=100, 
        choices=CHOICES_INVESTIGATION_HIERARCHY, 
        default="incident_investigation_hierarchy"
    )
    objects = models.Manager()
    bells_manager = BellsManager()
    
    class Meta:
        verbose_name = "Investigation Hierarchy"
        verbose_name_plural = "Investigation Hierarchies"

    def __str__(self):
        return f"{self.company.name}"

        
class InvestigationStage(IncidentHierarchyTimeStamp, TimestampModel):
    hierarchy = models.ForeignKey(
        InvestigationHierarchy, 
        on_delete=models.CASCADE, 
        related_name="stages" 
    )
    stage_name = models.CharField(max_length=255)  
    s_no = models.PositiveIntegerField(default=1)
    version = models.PositiveIntegerField(default=1)
    stage_timeline_days = models.PositiveIntegerField()
    overdue_date = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        Permission, related_name="investigation_stages"  
    )
    objects = models.Manager()
    bells_manager = BellsManager()
    
    
    class Meta:
        verbose_name = "Investigation Stage"
        verbose_name_plural = "Investigation Stages"
        
        permissions = [
            ("can_change_to_inprogress_not_closed", "Can change incident status to InProgress but not Closed"),
            ("can_mark_inprogress_and_closed", "Can change the incident report status to In Progress and can mark it as Closed"),
            ("can_view_incident_investigation_details", "View the incident and investigation details")

        ]
        
    def __str__(self):
        return f"Stage-{self.stage_name} Version-{self.version}"
    
    @staticmethod
    def generate_sno(hierarchy):
        max_s_no = InvestigationStage.objects.filter(hierarchy=hierarchy, is_active = True).aggregate(models.Max('s_no'))['s_no__max']        
        if max_s_no is None:
            return 1
        return max_s_no + 1
    
class StageOwnerSubstitute(IncidentHierarchyTimeStamp, TimestampModel):
    stage = models.ForeignKey(
        InvestigationStage, 
        on_delete=models.CASCADE, 
        related_name="stage_owners"  
    )
    owner = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="stage_owner"
    )
    substitute = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="stage_substitute", 
        null=True, 
        blank=True
    )
    substitute_timeline_days = models.PositiveIntegerField()
    subsitute_overdue_date = models.DateTimeField(null=True, blank=True)
    is_subsitute_time_line_overdue = models.BooleanField(default=False)
    is_substitute_active = models.BooleanField(null=True, blank=True, default=None)
    is_substitute_email_sent = models.BooleanField(default=False)
    removed_stage_subsitute = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name="removed_stage_substitute", 
        null=True, 
        blank=True
    )
    objects = models.Manager()
    bells_manager = BellsManager()
    
    
    class Meta:
        verbose_name = "Stage Owner Substitute"
        verbose_name_plural = "Stage Owner Substitutes"
        unique_together = ("stage", "owner", "substitute")

    def __str__(self):
        return f"Stage {self.stage.stage_name} - Owner: {self.owner}"


    
class InvestigationQuestion(IncidentHierarchyTimeStamp, TimestampModel):
    stage = models.ForeignKey(
        InvestigationStage, 
        on_delete=models.CASCADE, 
        related_name="investigation_questions" 
    )
    question = models.TextField()

    objects = models.Manager()
    bells_manager = BellsManager()
    
    
    class Meta:
        verbose_name = "Investigation Question"
        verbose_name_plural = "Investigation Questions"
    
    def __str__(self):
        return f"Question for Stage {self.stage.s_no}"



class IncidentStageMapper(IncidentHierarchyTimeStamp, TimestampModel):
    incident = models.ForeignKey(
        Incident, 
        on_delete=models.CASCADE, 
        related_name="incident_stage_mappings"  
    )
    stage = models.ForeignKey(
        InvestigationStage, 
        on_delete=models.CASCADE, 
        related_name="stage_mappings"  
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    stage_status = models.CharField(
            max_length=20, 
            choices=STAGE_STATUS_CHOICES, 
            default="pending"
        )
    objects = models.Manager()
    bells_manager = BellsManager()
    
    
    class Meta:
        verbose_name = "Incident Stage Mapper"
        verbose_name_plural = "Incident Stage Mappers"

    def __str__(self):
        return f"Incident {self.incident} - Stage {self.stage.s_no}"


class IncidentStageQuestionMapper(IncidentHierarchyTimeStamp, TimestampModel):
    incident_stage = models.ForeignKey(IncidentStageMapper, on_delete=models.CASCADE)
    question = models.ForeignKey(InvestigationQuestion, on_delete=models.CASCADE)
    answer = models.TextField(blank=True, null=True)
    objects = models.Manager()
    bells_manager = BellsManager()
    
    
    class Meta:
        verbose_name = "Incident Stage Question Mapper"
        verbose_name_plural = "Incident Stage Question Mappers"

    def __str__(self):
        return f"Question {self.question} for Incident Stage {self.incident_stage}"


