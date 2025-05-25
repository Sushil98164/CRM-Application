# SD team feature permissions
CLIENT_EMPLOYEE_ASSIGNMENT_PERMISSIONS = [
    # Update Service Permissions
    ('update_all_services', 'Can update all services'),
    ('update_service_their_team_own', 'Can update services owned by their own team'),
    ('update_service_of_their_own', 'Can update their own services'),
    ('update_none', 'No permission to update services'),

    # Read Service Permissions
    ('read_all_services', 'Can read all services'),
    ('read_service_their_team_own', 'Can read services owned by their own team'),
]

# Company Policy feature
COMPANY_TERMS_AND_CONDITIONS_POLICY_PERMISSIONS = [
    ('create_terms_and_conditions_all', 'Can create terms and conditions'),
    ('create_none_terms_and_conditions', 'No permission to create terms and conditions'),
    ('view_terms_and_conditions_all', 'Can view terms and conditions'),
    ('view_none_terms_and_conditions', 'No permission to view terms and conditions'),
    ('update_terms_and_conditions_all', 'Can Update terms and conditions'),
    ('update_none_terms_and_conditions', 'No permission to update terms and conditions'),
    ('create_privacy_policy_all', 'Can create privacy policy'),
    ('create_none_privacy_policy', 'No permission to create privacy policy'),
    ('view_privacy_policy_all', 'Can view privacy policy'),
    ('view_none_privacy_policy', 'No permission to view privacy policy'),
    ('update_privacy_policy_all', 'Can update privacy policy'),
    ('update_none_privacy_policy', 'No permission to update privacy policy'),

]

# Client profile permissions
CLIENT_PERMISSIONS = [
    ('create_all_clients', 'Can create all clients'),
    ('create_client_none', 'No permission to create clients'),
    ('update_all_clients', 'Can update all clients'),
    ('update_clients_team_owns', 'Can update clients owned by their own team'),
    ('update_clients_of_own', 'Can update their own clients'),
    ('client_update_none', 'No permission to update clients'),
    ('read_all_clients', 'Can read all clients'),
    ('read_team_clients', 'Can read clients owned by their own team'),
]

EMPLOYEE_PERMISSIONS = [
    # Employee profile permissions
    ('create_all_employees', 'Can create all employees'),
    ('create_employee_none', 'Restricted: No create permission'),
    
    ('update_all_employees', 'Can update all employees'),
    ('update_team_employees', 'Can update employees in their team'),
    ('update_own_employees', 'Can update self profile'),
    ('employee_update_none', 'Restricted: No update permission'),

    ('read_all_employees', 'Can read all employees'),
    ('read_team_employees', 'Can read employees in their team'),
    ('read_own_employees', 'Can read self profile'),
    # Employee Approval permission
    ('update_employee_approval_all', 'Can update employee approval status'),
    ('update_employee_approval_none', 'Can not update employee approval status'),

    # Acknowledgement Permissions
    ('read_all_acknowledgements', 'Can read all acknowledgements'),
    ('read_team_acknowledgements', 'Can read acknowledgement their team owns')
]

SHIFT_PERMISSIONS = [
    # Manage employee shifts
    ('create_shift_all', 'Can create all client shifts'),
    ('create_own_team_shift', 'Can create shifts for their own team'),
    ('create_shift_none', 'No access to create shifts'),
    ('update_shift_all', 'Can update all client shifts'),
    ('update_own_team_shift', 'Can update shifts for their own team'),
    ('update_roster_shift_none', 'No access to update roster shifts'),

    ('read_client_shift_all', 'Can read all client shifts'),
    ('read_own_team_shift', 'Can read shifts for their own team'),
    ('read_own_shift', 'Can read their own shifts'),
    ('read_no_shift_access', 'No access to read shifts'),

    # Manage dashboard view
    ('view_dashboard_all_shifts', 'Can view all client shifts on the dashboard'),
    ('view_dashboard_own_team_shifts', 'Can view shifts for their own team on the dashboard'),
    ('view_dashboard_own_shifts', 'Can view their own shifts on the dashboard'),
    ('view_no_dashboard_access', 'No access to view shifts on the dashboard'),

    # Delete shifts
    ('delete_shift_all', 'Can delete all client shifts'),
    ('delete_own_team_shift', 'Can delete shifts for their own team'),
    ('delete_no_shift_access', 'No access to delete shifts'),

    # Shift report permissions
    ('export_all_shift_reports', 'Can export all shift reports'),
    ('export_own_team_shift_reports', 'Can export shift reports for their own team'),
    ('export_shift_reports_none', 'No access to export shift report'),

    ('view_all_shift_reports', 'Can view all shift reports'),
    ('view_own_team_shift_reports', 'Can view shift reports for their own team'),

    # Roster permissions
    # Update employee punch in and punch out
    # ('update_employee_punch_in_out_all_rosters', 'Can update punch-in and punch-out for all rosters'),
    # ('update_employee_punch_in_out_own_team_shifts', 'Can update punch-in and punch-out for shifts within their own team'),
    ('update_employee_punch_in_out_own_shifts', 'Can update punch-in and punch-out for their own shifts'),
    ('update_employee_punch_in_out_no_access', 'No permission to update punch-in and punch-out'),

    # Read view employee punch in and punch out
    # ('view_all_rosters', 'Can view punch-in and punch-out for all rosters'),
    # ('view_own_team_shifts', 'Can view punch-in and punch-out for shifts within their own team'),
    ('view_own_shifts', 'Can view punch-in and punch-out for their own shifts'),
    ('view_no_access', 'No permission to view punch-in and punch-out'),
]

DOCUMENT_PERMISSIONS = [
    # Document permissions
    ('import_all_documents', 'Can import all documents'),
    ('import_team_documents', 'Can import documents in their team'),
    ('import_own_documents', 'Can import documents of their own'),
    ('import_document_none', 'Restricted: No import permission'),

    ('read_all_documents', 'Can read all documents'),
    ('read_team_documents', 'Can read documents in their team'),
    ('read_own_documents', 'Can read documents of their own'),
    ('read_document_none', 'Restricted: No read permission'),

    ('delete_all_documents', 'Can delete all documents'),
    ('delete_team_documents', 'Can delete documents in their team'),
    ('delete_own_documents', 'Can delete documents of their own'),
    ('delete_document_none', 'Restricted: No delete permission'),
]

INCIDENT_PERMISSIONS = [
    # Incident-related permissions
    ('create_incident_all', 'Can create incidents for all teams'),
    ('create_incident_own_team', 'Can create incidents for their own team'),
    ('create_incident_there_own', 'Can create incidents for their own'),
    ('create_no_access_to_incidents','No permission to create incident'),

    ('tag_employee_in_incident_all', 'Can tag employees in incidents for all teams'),
    ('tag_employee_in_incident_own_team', 'Can tag employees in incidents for their own team'),
    ('review_incident_all', 'Can review incidents for all teams'),
    ('review_incident_own_team', 'Can review incidents for their own team'),

    ('view_incident_all', 'Can view incidents for all teams'),
    ('view_incident_own_team', 'Can view incidents for their own team'),
    ('view_incident_own', 'Can view their own incidents'),
    ('view_incident_no_access', 'No permission to view incidents'),

    ('update_tag_employee_in_incident_all', 'Can update employee tags in incidents for all teams'),
    ('update_tag_employee_in_incident_own_team', 'Can update employee tags in incidents for their own team'),

    ('update_incident_all', 'Can update incidents for all teams'),
    ('update_incident_own_team', 'Can update incidents for their own team'),
    ('update_incident_no_access', 'No permission to update incidents'),

    ('delete_incident_report_all', 'Can delete incident reports for all teams'),
    ('delete_incident_report_own_team', 'Can delete incident reports for their own team'),

    ('export_incident_report_all', 'Can export incident reports for all teams'),
    ('export_incident_report_own_team', 'Can export incident reports for their own team'),
    ('export_incident_no_access', 'No permission to export incident reports'),

    ('update_incident_investigation_all', 'Can update incident investigations for all teams'),
    ('update_incident_investigation_own_team', 'Can update incident investigations for their own team'),
    ('update_incident_investigation_self', 'Can update incident investigations for their own assigned client incidents'),
    ('update_incident_investigation_none', 'No access to update incident investigations.'),

    ('read_incident_investigation_all', 'Can read incident investigations for all teams'),
    ('read_incident_investigation_own_team', 'Can read incident investigations for their own team'),
    ('read_incident_investigation_self', 'Can read own incident investigation submissions'),
    ('read_incident_investigation_none', 'No access to read incident investigations.'),

    ('mark_incident_investigation_completed_all', 'Can mark incident investigations as completed for all teams'),
    ('mark_incident_investigation_completed_own_team', 'Can mark incident investigations as completed for their own team'),

    ('can_comment_on_incident_all', 'Can comment on incident investigations for all teams'),
    ('can_comment_on_incident_own_team', 'Can comment on incident investigations for their own team'),
    
    ('read_all_reports','Can read all reporting'),
    ('read_team_reports','Can read reporting for their own team'),
    ('read_own_reports','Can read reporting for their own records'),
    ('read_no_access_to_reports','No permission to read reporting'),
    
    #hierarchy permissions
    ('create_hierarchy_all', 'Can create hierarchy for all teams'),
    ('create_none_hierarchy', 'No permission to create hierarchy'),
    ('update_hierarchy_all', 'Can update hierarchy for all teams'),
    ('update_none_hierarchy', 'No permission to update hierarchy'),
    ('read_hierarchy_all', 'Can read hierarchy for all teams'),
    ('read_none_hierarchy', 'No permission to read hierarchy'),
]

PROGRESS_NOTES_PERMISSIONS = [
    # Create progress notes
    ('create_progress_notes_own', 'Can create progress notes for their own records'),
    ('create_progress_notes_no_access', 'No permission to create progress notes'),

    # Update progress notes
    ('update_progress_notes_all', 'Can update all progress notes'),
    ('update_progress_notes_own_team', 'Can update progress notes for their own team'),
    ('update_progress_notes_own', 'Can update progress notes for their own records'),
    ('update_progress_notes_no_access', 'No permission to update progress notes'),

    # View progress notes
    ('view_progress_notes_all', 'Can view all progress notes'),
    ('view_progress_notes_own_team', 'Can view progress notes for their own team'),
    ('view_progress_notes_own', 'Can view progress notes for their own records'),
    ('view_progress_notes_no_access', 'No permission to view progress notes'),

    # Export progress notes
    ('export_progress_notes_all', 'Can export all progress notes'),
    ('export_progress_notes_own_team', 'Can export progress notes for their own team'),
    ('export_none', 'No permission to export progress notes'),

]

RISK_ASSESSMENT_PERMISSIONS = [
    # Create Risk Assessment Permissions
    ('create_all_risk_assessments', 'Can create all risk assessments'),
    ('create_risk_assessments_team_own', 'Can create risk assessments for their own team'),
    ('create_risk_assessments_of_their_own', 'Can create their own risk assessments'),
    ('create_none', 'No permission to create risk assessments'),

    # Read Risk Assessment Permissions
    ('read_all_risk_assessments', 'Can read all risk assessments'),
    ('read_risk_assessments_team_own', 'Can read risk assessments for their own team'),
    ('read_risk_assessments_of_their_own', 'Can read their own risk assessments'),
    ('read_none', 'No permission to read risk assessments'),

    # Update Risk Assessment Permissions
    ('update_all_risk_assessments', 'Can update all risk assessments'),
    ('update_team_risk_assessments', 'Can update risk assessments for their own team'),
    ('update_own_risk_assessments', 'Can update their own risk assessments'),
    ('risk_assessment_update_none', 'No permission to update risk assessments'),

    # Delete Risk Assessment Permissions
    ('delete_all_risk_assessments', 'Can delete all risk assessments'),
    ('delete_risk_assessments_team_own', 'Can delete risk assessments for their own team'),

    # Risk Assessment Authorization Permissions
    ('authorize_risk_assessment_all', 'Can authorize risk assessments for all teams'),
    ('authorize_risk_assessment_own_team', 'Can authorize risk assessments for their own team'),

    # Risk Assessment Review Permissions
    ('review_risk_assessment_all', 'Can review risk assessments for all teams'),
    ('review_risk_assessment_own_team', 'Can review risk assessments for their own team'),
]


DEPARTMENTS = [
    ('create_department_all', 'Can create all teams'),
    # ('create_department_team_own', 'Can create department for their own team'),
    ('create_department_none', 'No permission to create team'),

    
    ('read_department_all', 'Can read all teams'),
    ('read_department_own', 'Can read team of there own'),
    ('read_department_none', 'No access to read team'),

    ('update_department_all', 'Can update all teams'),
    ('update_department_own', 'Can update team for their own own'),
    ('update_department_none', 'No access to update team'),

    ('delete_custom_department_all', 'Can delete all teams'),
    ('delete_department_own', 'Can delete team for their own team'),
    ('delete_department_none', 'No access to delete team'),

    ('update_assign_manager_to_department', 'Can assign manager to team'),
    ('update_clients_to_department', 'Can assign clients to team'),
    ('update_own_clients_to_department', 'Can assign own clients to team'),

]

USERAUTH_PERMISSIONS = [
    ('create_templates', 'Can create templates'),
    ('create_templates_none', 'No permission to create templates'),
    ('update_templates', 'Can update templates for all users'),
    ('update_templates_none', 'No permission to update templates'),
    ('read_templates', 'Can read templates'),
    ('read_templates_none', 'No permission to read templates'),   
]