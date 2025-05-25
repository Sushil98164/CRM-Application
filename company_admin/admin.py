from django.contrib import admin
from company_admin.models import *
# Register your models here.

@admin.register(IncidentAttachment)
class IncidentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("incident", "file", "created_at", "updated_at")
    list_filter = ("incident", "created_at")
    search_fields = ("incident__id",)
    ordering = ("-created_at",)


# @admin.register(DailyShiftCaseNote)
# class DailyShiftCaseNoteAdmin(admin.ModelAdmin):
#     list_display = ("employee", "client", "company", "shift", "start_date_time", "end_date_time", "vehicle_used", "distance_traveled",'is_deleted','created_at')
#     list_filter = ("company", "employee", "client", "shift", "vehicle_used", "start_date_time", "end_date_time","is_deleted",'created_at')
#     search_fields = ("employee__person__first_name", "employee__person__last_name", "client__person__first_name", "client__person__last_name", "company__name")
#     ordering = ("-start_date_time",)

@admin.register(DailyShiftCaseNote)
class DailyShiftCaseNoteAdmin(admin.ModelAdmin):
    list_display = ("employee", "client", "company", "shift", "start_date_time", "end_date_time", "vehicle_used", "distance_traveled", "is_deleted", "created_at")
    list_filter = ("company", "employee", "client", "shift", "vehicle_used", "start_date_time", "end_date_time", "is_deleted", "created_at")
    search_fields = ("employee__person__first_name", "employee__person__last_name", "client__person__first_name", "client__person__last_name", "company__name")
    ordering = ("-start_date_time",)
    raw_id_fields = ("employee", "client", "company", "shift")
    list_per_page = 50


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'employee', 'client', 'company', 'incident_location', 
        'incident_date_time', 'is_injured', 'any_witness', 
        'report_type', 'report_code', 'status', 'incident_severity_level','employees_involved','is_deleted','created_at','updated_at'
    )

    list_filter = (
        'company', 'is_injured', 'any_witness', 
        'report_type', 'status', 'incident_severity_level',
        'incident_category', 'incident_classification','is_deleted','created_at'
    )

    search_fields = ('incident_location', 'report_code', 'witness_name', 'witness_email')

    ordering = ('-incident_date_time',)
    

@admin.register(RiskType)
class RiskTypeAdmin(admin.ModelAdmin):
    list_display = ['id','name','description']



@admin.register(RiskArea)
class RiskAreaAdmin(admin.ModelAdmin):
    list_display = ['id','name','description']



@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ["id", "client", "get_company", "assessment_date", "reviewed_date", "prepared_by"]
    list_filter = ["client__company", "assessment_date", "reviewed_date", "prepared_by","is_deleted"]
    search_fields = ["client__person__first_name", "client__person__last_name", 
                     "prepared_by__person__first_name", "prepared_by__person__last_name"]
    ordering = ["-assessment_date"]

    def get_company(self, obj):
        return obj.client.company
    get_company.admin_order_field = "client__company"
    get_company.short_description = "Company"


@admin.register(RiskAssessmentDetail)
class RiskAssessmentDetailAdmin(admin.ModelAdmin):
    list_display = [
        "id", "risk_assessment", "risk_type", "choosen_risk_area", 
        "risk_to_self", "risk_to_self_category", "risk_to_staff", 
        "risk_to_staff_category", "risk_to_other", "risk_to_other_category", 
        "source_of_information", "comments"
    ]
    list_filter = [
        "risk_assessment", "risk_type", "risk_to_self_category", 
        "risk_to_staff_category", "risk_to_other_category"
    ]
    search_fields = [
        "risk_assessment__client__person__first_name", 
        "risk_assessment__client__person__last_name", 
        "risk_type__name", "source_of_information"
    ]


@admin.register(RiskDocumentationApproval)
class RiskDocumentationApprovalAdmin(admin.ModelAdmin):
    list_display = ["id", "risk_assessment", "completed_by", "authorized_by", "date"]
    list_filter = ["risk_assessment", "date"]
    search_fields = ["completed_by", "authorized_by", "risk_assessment__client__person__first_name", "risk_assessment__client__person__last_name"]

    
@admin.register(RiskMoniterControl)
class RiskMoniterControlAdmin(admin.ModelAdmin):
    list_display = ["id", "risk_assessment", "reviewed_date", "reviewed_by", "authorized_by"]
    list_filter = ["reviewed_date", "authorized_by"]
    search_fields = ["reviewed_by", "authorized_by", "risk_assessment__client__person__first_name", "risk_assessment__client__person__last_name"]
    ordering = ["-reviewed_date"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'incident', 'report_type', 'content','cause_of_incident','prevention_of_incident')
    list_filter = ('employee', 'incident', 'report_type')


@admin.register(CompanyTermsAndConditionsPolicy)
class CompanyTermsAndConditionsPolicyAdmin(admin.ModelAdmin):
    list_display = ('company', 'type')
    list_filter = ('type','company')
    search_fields = ('company__name', 'type')


@admin.register(EmployeePolicyAcknowledgment)
class EmployeePolicyAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'policy', 'is_acknowledged', 'created_at', 'updated_at')
    list_filter = ('is_acknowledged',)
    search_fields = ('employee__person__first_name', 'policy__type')

@admin.register(IncidentTaggedEmployee)
class IncidentTaggedEmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'incident', 'tagged_employee', 'tagged_by', 
        'untagged_by', 'tagged_to_employee', 'tagged_to_client', 
        'description', 'is_removed', 'created_at', 'updated_at'
    ]
    list_filter = ('incident', 'tagged_employee', 'tagged_by', 'untagged_by', 'is_removed', 'created_at')
    search_fields = [
        'incident__name', 
        'tagged_employee__person__first_name', 
        'tagged_employee__person__last_name',
        'tagged_by__person__first_name', 
        'tagged_by__person__last_name'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('incident', 'tagged_employee', 'description', 'is_removed')
        }),
        ('Tagging Information', {
            'fields': ('tagged_by', 'untagged_by', 'tagged_to_employee', 'tagged_to_client')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ClientEmployeeAssignment)
class ClientEmployeeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'employee', 'created_by', 'created_at', 'is_deleted','updated_by','updated_at')
    list_filter = ('client','employee','is_deleted','created_by','created_at','updated_by','updated_at')
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ('employee__person__first_name', 'employee__person__last_name', 
                     'client__person__first_name', 'client__person__last_name', 
                     'created_by__username')


    
@admin.register(DepartmentClientAssignment)
class DepartmentClientAssignmentAdmin(admin.ModelAdmin):
    list_display = ('department', 'client', 'created_by', 'created_at', 'is_deleted','updated_by','updated_at')
    list_filter = ('department','client','is_deleted','created_by','created_at','updated_by','updated_at')
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    search_fields = ('department__name',
                     'client__person__first_name', 'client__person__last_name', 
                     'created_by__username')

@admin.register(CompanyGroup)
class CompanyGroupAdmin(admin.ModelAdmin):
    list_display = ('company', 'group', 'created_at')  
    search_fields = ('company__company_code', 'group__name')
    list_filter = ('company', 'group')
    

@admin.register(InvestigationHierarchy)
class InvestigationHierarchyAdmin(admin.ModelAdmin):
    list_display = ("company", "hierarchy_timeline_days", "levels", "category", "created_by", "updated_by")
    list_filter = ("company", "category", "levels")


@admin.register(InvestigationStage)
class InvestigationStageAdmin(admin.ModelAdmin):
    list_display = ("hierarchy", "stage_name", "s_no", "version", "stage_timeline_days", "overdue_date","created_at","updated_at", "is_overdue",  "is_active", "created_by", "updated_by")
    list_filter = ("hierarchy", "is_active")
    filter_horizontal = ("permissions",)  


@admin.register(StageOwnerSubstitute)
class StageOwnerSubstituteAdmin(admin.ModelAdmin):
    list_display = ("stage", "owner", "substitute", "substitute_timeline_days", "subsitute_overdue_date", "is_substitute_email_sent", "created_at", "created_by", "updated_by")
    list_filter = ("stage", "owner")


@admin.register(InvestigationQuestion)
class InvestigationQuestionAdmin(admin.ModelAdmin):
    list_display = ("stage", "question", "created_by", "updated_by")
    list_filter = ("stage",)


@admin.register(IncidentStageMapper)
class IncidentStageMapperAdmin(admin.ModelAdmin):
    list_display = ("incident", "stage", "completed_at", "is_overdue", "stage_status", "created_by", "updated_by")
    list_filter = ("stage", "stage_status", "is_overdue")


@admin.register(IncidentStageQuestionMapper)
class IncidentStageQuestionMapperAdmin(admin.ModelAdmin):
    list_display = ("incident_stage", "question", "answer", "created_by", "updated_by")
    list_filter = ("incident_stage",)
