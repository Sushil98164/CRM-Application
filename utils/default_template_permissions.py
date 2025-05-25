from django.contrib.auth.models import Group,Permission

def assign_permissions_to_groups(self):
    """
    Assigns predefined permissions to groups related to the company.
    """
    from company_admin.models import CompanyGroup

    group_permissions = {
        "admin": [
                "read_all_reports","create_all_employees","read_all_employees","update_all_employees","read_all_documents","import_all_documents",
                "delete_all_documents","read_all_acknowledgements","create_all_clients","read_all_clients","update_all_clients",
                "create_all_risk_assessments","read_all_risk_assessments","update_all_risk_assessments","create_department_all","read_department_all",
                "update_department_all","delete_custom_department_all","update_clients_to_department","create_shift_all","read_client_shift_all",
                "update_shift_all","delete_shift_all","view_all_shift_reports","export_all_shift_reports","view_terms_and_conditions_all",
                "update_terms_and_conditions_all","update_privacy_policy_all","view_privacy_policy_all","create_templates","read_templates",
                "update_templates","create_incident_all","view_incident_all","update_incident_all","export_incident_report_all","create_progress_notes_own",
                "view_progress_notes_all","update_progress_notes_all","export_progress_notes_all","read_incident_investigation_all","update_incident_investigation_all",
                "authorize_risk_assessment_all","update_employee_approval_all"
                ],
        "manager": [
           "read_team_reports","create_employee_none","read_team_employees","update_team_employees","read_team_documents","import_team_documents",
           "delete_team_documents","read_team_acknowledgements","create_client_none","read_team_clients","update_clients_team_owns","create_risk_assessments_team_own",
           "read_risk_assessments_team_own","update_team_risk_assessments","create_department_all","read_department_own","update_department_own","delete_department_own",
           "update_own_clients_to_department","create_own_team_shift","read_own_team_shift","update_own_team_shift","delete_own_team_shift",
           "view_own_team_shift_reports","export_own_team_shift_reports","view_terms_and_conditions_all","update_none_terms_and_conditions","view_privacy_policy_all",
           "update_none_privacy_policy","create_templates","read_templates","update_templates_none","create_incident_own_team","view_incident_own_team","update_incident_own_team",
           "export_incident_report_own_team","create_progress_notes_own","view_progress_notes_own_team","update_progress_notes_own_team","export_progress_notes_own_team",
           "read_incident_investigation_own_team","update_incident_investigation_own_team","authorize_risk_assessment_own_team","update_employee_approval_none"
        ],
        
        "employee": [
            "read_own_reports","create_employee_none","read_own_employees","update_own_employees","read_own_documents","import_own_documents","delete_own_documents","create_client_none",
            "create_risk_assessments_of_their_own","read_risk_assessments_of_their_own","read_own_shift","view_terms_and_conditions_all","view_privacy_policy_all","create_incident_there_own",
            "view_incident_own","update_incident_no_access","export_incident_no_access","create_progress_notes_own","view_progress_notes_own","update_progress_notes_own","read_incident_investigation_none",
            "update_incident_investigation_none","risk_assessment_update_none","create_shift_none","update_roster_shift_none","delete_no_shift_access","export_none","create_templates_none","read_templates_none","create_department_none", 
            "update_none_terms_and_conditions", "update_none_privacy_policy"

        ]
        
    }


    for group_name, permissions in group_permissions.items():
        group, _ = CompanyGroup.bells_manager.get_or_create(
            company=self,
            group=Group.objects.get_or_create(name=f"{self.company_code} - {group_name}")[0],
        )

        existing_permissions = Permission.objects.filter(codename__in=permissions)
        missing_permissions = set(permissions) - set(existing_permissions.values_list('codename', flat=True))

        if missing_permissions:
            print(f"Missing permissions for group {group_name}: {missing_permissions}")
            continue

        group.group.permissions.set(existing_permissions)