from django.contrib import admin
from django.urls import path
from .views import *

app_name = 'employee'

urlpatterns = [
    #incident
    path('employee/incident/add/', IncidentOperationView.as_view(), name='incident_add'),
    path('employee/incident/edit/<int:incident_id>/', IncidentOperationView.as_view(), name='incident_edit'),
    path('employee/incident/delete/<int:incident_id>/', IncidentOperationView.as_view(), name='incident_delete'),
    path('incident/attachment/delete/',handle_incident_attachment_file_delete, name='incident_attachment_delete'),
    path('incident/list/',IncidentView.as_view(),name = "incident_list"),

    path('mandatory/incident/add/', MandatoryIncidentOperationView.as_view(), name='mandatory_incident_add'),
    path('mandatory/incident/edit/<int:incident_id>/', MandatoryIncidentOperationView.as_view(), name='mandatory_incident_edit'),
    path('mandatory/incident/delete/<int:incident_id>/', MandatoryIncidentOperationView.as_view(), name='mandatory_incident_delete'),
    path('mandatory/incident/attachment/delete/',handle_mandatory_attachment_file_delete, name='mandatory_incident_attachment_delete'),
    path('mandatory/incident/list/',MandatoryIncidentView.as_view(),name = "mandatory_incident_list"),
   
    
    #shift note
    # path('shift/add/',ShiftViewOperations.as_view(),name="dailyshift_add"),
    # path('shift/edit/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_edit"),
    # path('shift/delete/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_delete"),
    path('shift/list/',ShiftView.as_view(),name="dailyshift_list"),

    #employee profile urls
    path('my-profile/',EmployeeProfile.as_view(),name="employee_profile"),
    path('my-profile/edit/<int:employee_id>/',EmployeeProfileOperation.as_view(),name="employee_profile_edit"),

    #employee documents urls
    path('my-documents/',EmployeeDocumentView.as_view(),name="employee_documents"),
    path('employee/document/<int:employee_id>/',EmployeeProfileDocuments.as_view(),name="employee_document"),
    path('my-profile/document/delete/<int:employee_id>/<int:document_id>/', EmployeeProfileDocumentDelete, name='delete_employee_document'),
    path('my-profile/document/delete/<int:employee_id>/<int:document_id>/',EmployeeProfileDocuments.as_view(),name="delete-employee_document"), 
    
    #Myclients urls
    path('employee/clients/list/',MyClientsView.as_view(),name="my_clients"),
    path('employee/client-details/<int:client_id>/',ClientsDetailView.as_view(),name="client_detail_view"),
    path('employee/client/risk-assessment-list/<int:client_id>/',ClientsRiskassessmentListView.as_view(),name="client_risk_assessment_list_view"),
    # path('employee/client/risk-assessment-detail/<int:client_id>/<int:risk_assessment_id>/',ClientsRiskassessmentDetailView.as_view(),name="client_risk_assessment_detail_view"),
    # path('employee/client/risk-assessment/edit/<int:client_id>/<int:risk_assessment_id>/',ClientsRiskassessmentDetailView.as_view(),name="client_risk_assessment_edit"),

    
    path('client/risk-assessment/add/<int:client_id>/', ClientsRiskassessmentOperation.as_view(), name='client_risk_assessment_add'),
    path('client/risk-assessment/edit/<int:client_id>/<int:risk_assessment_id>/', ClientsRiskassessmentOperation.as_view(), name='client_risk_assessment_edit'),
    path('client/risk-assessment/delete/<int:client_id>/<int:risk_assessment_id>/', ClientsRiskassessmentOperation.as_view(), name='client_risk_assessment_delete'),
    path('client/risk-area', ClientGetRiskArea.as_view(), name='risk_area'),
    path('client/risk-assessment/details/add/<int:client_id>/', ClientsRiskassessmentOperation.as_view(), name='client_risk_assessment_details_add'),
    path('client/risk-assessment/details/edit/<int:client_id>/', ClientsRiskassessmentOperation.as_view(), name='client_risk_assessment_details_edit'),
    path('client/risk-assessment/details/delete/<int:client_id>/<int:risk_assessment_detail_id>/', ClientDeleteRiskAssessmentDetail, name='client_risk_assessment_detail_delete'),
    #risk assessment by employee
    path('client/employee/risk-assessment/add/<int:client_id>/', ClientsRiskassessmentOperation.as_view(), name='client_employee_risk_assessment_add'),
    path('client/risk-assessment-delete/', ClientRiskAssessmentDelete, name='client_risk_assessment_delete'),
    
    
    path('employee/client/progress-notes-list/<int:client_id>/',ClientsProgressListView.as_view(),name="client_progress_note_list_view"),
    path('employee/client/progress-notes-detail/<int:client_id>/<int:shift_id>/',ClientsProgressDetailView.as_view(),name="client_progress_note_detail"),
    path('employee/client/profile/incident-list/<int:client_id>/',ClientProfileIncidentlistView.as_view(),name = "client_profile_incident_list"),
    path('employee/client/profile/incident-detail/<int:client_id>/<int:incident_id>/',ClientIncidentDetailView.as_view(),name = "employee_client_profile_incident_detail"),
    path('employee/client/profile/mandatory/incident-detail/<int:client_id>/<int:mandatory_incident_id>/',ClientIncidentDetailView.as_view(),name = "employee_client_profile_mandatory_incident_detail"),


    #rostering urls
    path('shift/list/',ShiftView.as_view(),name="dailyshift_list"),
    path('shift/add/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_add"),
    path('shift/edit/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_edit"),
    path('shift/detail/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_view"),



    #rostering independent adding progress notes
    path('shift/employee/add/',ShiftViewOperations.as_view(),name="dailyshift_add_employee"),
    path('shift/employee/edit/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_edit_employee"),
    path('employee/shifts/create-progress-note/', user_punch_in_view, name='create_progress_note_by_employee'),

    # path('shift/add/<int:shift_id>/',ShiftViewOperations.as_view(),name="dailyshift_add"),

    path('employee/company_policies/documents',CompanyPoliciesDocumentsView.as_view(),name = 'employee_company_documents'),
    path('acknowledge/terms_and_conditions',EmployeeTermsAndConditionsOperationsView.as_view(), name='employee_terms_and_conditions'),
    path('acknowledge/privacy_policy',EmployeePrivacyPolicyOperationsView.as_view(), name='employee_privacy_policy'),

    path('employee/tag/employee/',TagEmployee.as_view(),name='employee_tag_employee'),
    path('employee/tag/employee/view/',TagEmployee.as_view(),name='employee_tag_employee_view'),
    path('tagged/incidents/',TaggedIncidentsView.as_view(),name='tagged_incidents'),

]