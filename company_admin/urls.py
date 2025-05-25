from django.contrib import admin
from django.urls import path
from .views import *

app_name = 'company'

urlpatterns = [
    #employee
    path('employee/list/',EmployeeView.as_view(),name = "employee_list"),
    path('employee/add/', EmployeeOperationView.as_view(), name='employee_add'),
    path('employee/add/step-2', EmployeeOperationView.as_view(), name='employee_add_step2'),
    
    #adding employee from scratch permissions
    path('employee/scratch/template', EmployeeOperationView.as_view(), name='employee_scratch_template'),
    
    path('employee/existing/template', EmployeeOperationView.as_view(), name='employee_existing_template'),
    path('saved/template/assignment/<int:template_id>/',EmployeeOperationView.as_view(),name = 'saved_template_assignment'),
    path('employee/template/assignment', EmployeeOperationView.as_view(), name='template_employee_assignment'),
    path('employee/edit/<int:employee_id>/', EmployeeOperationView.as_view(), name='employee_edit'),
    path('employee/delete/<int:employee_id>/', EmployeeOperationView.as_view(), name='employee_delete'),
 
    
    
    #add client
    path('client/add/', ClientOperationView.as_view(), name='client_add'),
    path('client/edit/<int:client_id>/', ClientOperationView.as_view(), name='client_edit'),
    path('client/delete/<int:client_id>/', ClientOperationView.as_view(), name='client_delete'),
    path('client/list/',ClientView.as_view(),name = "client_list"),
   
    #add departments
    path('teams/list/',DepartmentListView.as_view(),name = "departments_list"),
    path('teams/add/',DepartmentOperationView.as_view(),name = "departments_add"),
    path('teams/edit/<int:department_id>/',DepartmentOperationView.as_view(),name = "departments_edit"),
    path('teams/delete/<int:department_id>/',DepartmentOperationView.as_view(),name = "department_delete"),
    path('teams/employee/',DepartmentEmployeeAssignmentView.as_view(),name = "department_employee_assignment"),
    path('teams/employee/assignment/',DepartmentEmployeeAssignmentView.as_view(),name = "assign_employees"),

    #department-client assignments
    path('teams/client/',DepartmentClientAssignmentView.as_view(),name = "department_client_assignment"),
    path('teams/client/assignments/',DepartmentClientAssignmentView.as_view(),name = 'assign_client_to_department'),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('profile/',CompanyUserProfileView.as_view(),name = "profile"),
    path('manager/mandatory/incident/',MandatoryIncidentReportDashboard.as_view(),name = "mandatory_incident_reports_dashboard"),
    path('client/incident/',ClientIncidentReportDashboard.as_view(),name = "client_incident_reports_dashboard"),
    path('shifts/notes/',DailyShiftNoteDashboard.as_view(),name = "daily_shift_note_dashboard"),

    
    # path('company/setting/',SettingView.as_view(),name = "setting"),

    path('incident/add/', IncidentOperationView.as_view(), name='admin_incident_add'),
    path('incident/edit/<int:incident_id>/', IncidentOperationView.as_view(), name='admin_incident_edit'),
    path('incident/view/<int:incident_id>/', IncidentOperationView.as_view(), name='admin_incident_view'),

    path('incident/delete/<int:incident_id>/', IncidentOperationView.as_view(), name='admin_incident_delete'),

    path('manager/mandatory/incident/add/',MandatoryIncidentOperationView.as_view(),name="admin_mandatory_incident_add"),
    path('edit/<int:incident_id>/', MandatoryIncidentOperationView.as_view(), name='admin_mandatory_incident_edit'),
    path('manager/mandatory/incident/delete/<int:incident_id>/', MandatoryIncidentOperationView.as_view(), name='admin_mandatory_incident_delete'),

    path('progress-note/edit/<int:shift_note_id>/',ShiftViewOperations.as_view(),name="admin_dailyshift_edit"),
    path('progress-note/view/<int:shift_note_id>/',ShiftViewOperations.as_view(),name="admin_dailyshift_view"),

    path('shift/delete/<int:shift_id>/',ShiftViewOperations.as_view(),name="admin_dailyshift_delete"),

    # Get Employee Details by id
    path('employee/detail/<str:pk>',GetEmployeeDetails,name="get_employee_details"),
    
    #risk management
    path('risk-assessment/add/<int:client_id>/', RiskAssessmentOperationView.as_view(), name='risk_assessment_add'),
    path('risk-assessment/edit/<int:client_id>/<int:risk_assessment_id>/', RiskAssessmentOperationView.as_view(), name='risk_assessment_edit'),
    path('risk-assessment/delete/<int:client_id>/<int:risk_assessment_id>/', RiskAssessmentOperationView.as_view(), name='risk_assessment_delete'),
    path('risk-area', GetRiskArea.as_view(), name='risk_area'),
    path('risk-assessment/details/add/<int:client_id>/', RiskAssessmentOperationView.as_view(), name='risk_assessment_details_add'),
    path('risk-assessment/details/edit/<int:client_id>/', RiskAssessmentOperationView.as_view(), name='risk_assessment_details_edit'),
    path('risk-assessment/details/delete/<int:client_id>/<int:risk_assessment_detail_id>/', DeleteRiskAssessmentDetail, name='risk_assessment_detail_delete'),
    #risk assessment by employee
    path('employee/risk-assessment/add/<int:client_id>/', RiskAssessmentOperationView.as_view(), name='employee_risk_assessment_add'),
    path('risk-assessment-delete/', RiskAssessmentDelete, name='risk_assessment_delete'),

    #client profile urls
    path('client/profile/<int:client_id>/',ClientProfileView.as_view(),name = "client_profile"),
    path('client/profile/risk-assessment/<int:client_id>/',ClientProfileRiskassessmentView.as_view(),name = "client_profile_risk_assessment"),
    path('client/profile/incident/<int:client_id>/',ClientProfileIncidentView.as_view(),name = "client_profile_incident"),
    path('client/profile/mandatory-incident/<int:client_id>/',ClientProfileMandatoryIncidentView.as_view(),name = "client_profile_mandatory_incident"),
    path('client/profile/shift/note/<int:client_id>/',ClientProfileShiftNoteView.as_view(),name = "client_profile_shift_note"),
    path('client/profile/service/delivery/team/<int:client_id>/',ClientServiceDeliveryTeamView.as_view(),name = "client_service_delivery_team"),

    # client-employee assignment urls
    path('client/profile/service-delivery-team/assign/<int:client_id>/', CompanyClientProfileEmployeeAssignmentView.as_view(), name = "client_service_delivery_team_assign"),

    path('client/profile/incident/<int:client_id>/<int:incident_id>/',ClientIncidentOperationView.as_view(),name = "client_profile_incident_detail"),
    path('client/profile/mandatory/incident/<int:client_id>/<int:mandatory_incident_id>/',ClientIncidentOperationView.as_view(),name = "client_profile_mandatory_incident_detail"),
    path('client/profile/shift/note/<int:client_id>/<int:shift_id>/',ClientIncidentOperationView.as_view(),name = "client_profile_shift_note__detail"),
    
    #comment urls for incidents
    path('incident/comment/', CommentOperationView.as_view(), name='admin_incident_comment'),
    path('manager/mandatory/incident/comment/', CommentOperationView.as_view(), name='admin_mandatory_incident_comment'),
    path('incident/question/', QuestionOperationView.as_view(), name='admin_incident_question'),
    path('manager/mandatory/incident/question/', QuestionOperationView.as_view(), name='admin_mandatory_incident_question'),
    
    
    path('download-incident-report/', downloadIncidentReport, name="download_incident_report"),
    # path('download-mandatory-incident/', downloadIncidentReport, name="download_mandatory_incident_report"),
    path('download-shift-report/', downloadShiftReport, name="download_shift_report"),

    #employee profile urls
    path('employee-profile/<int:employee_id>/',CompanyEmployeeProfileView.as_view(),name="employee_profile_view"),
    path('employee-profile/edit/<int:employee_id>/',CompanyEmployeeProfileOperation.as_view(),name="manager_employee_profile_edit"),
    path('employee-profile/clients/<int:employee_id>/',CompanyEmployeeProfileClients.as_view(),name="manager_employee_profile_clients"),

    path('company/client/assignment',CompanyClientAssignment,name="company_client_assignment"),
    path('company/client/assignment/update',CompanyClientAssignment,name="update_company_client_assignment"),

    #employee profile documents urls
    path('employee-documents/<int:employee_id>/',CompanyEmployeeDocumentView.as_view(),name="company_employee_documents"),
    path('employee-profile/document/<int:employee_id>/',CompanyEmployeeProfileDocuments.as_view(),name="company_employee_document"),
    path('employee-profile/document/delete/<int:employee_id>/<int:document_id>/', CompanyEmployeeProfileDocumentDelete, name='company_delete_employee_document'),
    path('employee/profile/document/delete/<int:employee_id>/<int:document_id>/',CompanyEmployeeProfileDocuments.as_view(),name="company_manager_delete_employee_document"),
    path('employee-profile/document/update/', UpdateDocuementStatus, name="update-document_status"),


    path('company/settings/documents',CompanySettingsDocumentView.as_view(),name = 'company_documents'),
 
    path('company/employee/acknowledgements',CompanyEmployeeAcknowledgementView.as_view(),name = 'company_employee_acknowledgement'),
    path('company/terms_and_conditions_edit',TermsAndConditionsOperationsView.as_view(), name='company_terms_and_conditions_edit'),
    path('company/terms_and_conditions_view',TermsAndConditionsOperationsView.as_view(), name='company_terms_and_conditions_view'),
    path('company/privacy_policy_edit',PrivacyPolicyOperationsView.as_view(), name='company_privacy_policy_edit'),
    path('company/privacy_policy_view',PrivacyPolicyOperationsView.as_view(), name='company_privacy_policy_view'),
    
    path('tag/employee/',TagEmployee.as_view(),name='manager_tag_employee'),
    path('incident/employee-present/',IncidentEmployeePresent,name='incident_employee_present'),
    path('employee/incident/employee-present/',IncidentEmployeePresent,name='employee_incident_employee_present'),
        
    #Hierarchy 
    path('company/hierarchy/list',CompanyHeirarchyListView.as_view(), name = 'company_hierarchy_list'),
    path('company/add/investigation',CompanyHeirarchyListView.as_view(), name = 'add_investigation'),
    path('company/heirarchy/stages/<int:hierarchy_id>/',CompanyHeirarchyStagesOperationsView.as_view(),name='hierarchy_stages_list'),
    path('company/heirarchy/add/stages/<int:hierarchy_id>/',CompanyHeirarchyStagesOperationsView.as_view(),name='add_hierarchy_stages'),
    path('company/heirarchy/update/<int:hierarchy_id>/',CompanyHeirarchyStagesOperationsView.as_view(),name='company_hierarchy_update'),
    path('incident/investigation/answer/<int:incident_id>/', InvestigationStageAnswers.as_view(), name='investigation_stage_answers'),
    path('company/heirarchy/view/<int:hierarchy_id>/',CompanyHeirarchyStagesOperationsView.as_view(),name='view_hierarchy'),


    path('company/settings',CompanySettingsView.as_view(),name =  'company_settings'),
    path('company/template/list',CompanyTemplateListView.as_view(),name = 'template_list'),
    path('company/users/template/list',CompanyTemplateListView.as_view(),name = 'users_template_list'),

    path('company/template/add',TemplateOperationsView.as_view(),name = 'add_template'),
    path('company/template/edit/<int:template_id>/',TemplateOperationsView.as_view(),name = 'edit_template'),
    path('company/template/features',TemplateOperationsView.as_view(),name = 'template_feature'),
    path('clone/template/<int:template_id>/',TemplateOperationsView.as_view(),name = 'clone_template'),
    path('company/template/view/<int:template_id>/',TemplateOperationsView.as_view(),name = 'view_template'),

    path('template/permission/is/exist',templatePermissionsIsExist,name = 'template_permissions_is_exist'),
    path('template/is/exist',template_is_exist,name = 'template_is_exist'),
    path('template/is/exist/blur',template_is_exist_on_blur,name = 'template_is_exist_on_blur')
]