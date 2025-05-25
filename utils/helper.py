import logging
import json
from utils.permission_sets import *
from typing import Dict, List, Optional
logger = logging.getLogger('watchtower')
import copy
from django.contrib.auth.models import Group,Permission
from userauth.models import Employee,Person
from django.db.models import Exists, OuterRef, Q, Value
from django.db.models.functions import Lower, Replace


def process_permissions_data(
    feature_data: Dict,
    existing_permissions: Optional[List[str]] = None,
    selected_categories: Optional[List[str]] = None
) -> Dict:
    """
    Process feature data and mark permissions as selected based on existing group permissions.
    When existing_permissions is None, all features are marked as active by default.
    Preserves the original order of access levels.
    
    Args:
        feature_data (Dict): Raw feature data containing categories, features, actions, and access levels
        existing_permissions (Optional[List[str]]): List of permission codenames from an existing group
        selected_categories (Optional[List[str]]): List of category keys to process. If None, processes all categories
    
    Returns:
        Dict: Processed feature data with selected status marked for each access level and is_active status for features
    """
    try:
        logger.info("Starting permission data processing")
        
        # Make a deep copy of the feature data to avoid modifying the original
        processed_data = copy.deepcopy(feature_data)
        
        permission_set = set(existing_permissions) if existing_permissions else set()
        
        # Get categories to process
        categories = selected_categories or processed_data.keys()
        logger.info(f"Processing categories: {categories}")
        
        # Process each requested category
        for category in categories:
            logger.info(f"Processing category: {category}")
            
            category_data = processed_data.get(category)
            if not category_data or 'features' not in category_data:
                logger.warning(f"Invalid or empty category data for: {category}")
                continue
            
            # Process features
            for feature_name, feature in category_data['features'].items():
                try:
                    # Default is_active to True if no existing permissions are provided
                    feature['is_active'] = existing_permissions is None
                    
                    # Process actions if they exist
                    if 'actions' in feature:
                        for action in feature['actions']:
                            # Process access levels
                            if 'access_levels' in action:
                                found_selected = False
                                
                                # First pass: mark appropriate access levels as selected
                                for access_level in action['access_levels']:
                                    # If no existing_permissions, mark all as selected
                                    if existing_permissions is None:
                                        access_level['selected'] = True
                                        found_selected = True
                                    else:
                                        is_selected = access_level['code'] in permission_set
                                        access_level['selected'] = is_selected
                                        
                                        if is_selected:
                                            found_selected = True
                                            feature['is_active'] = True
                                
                            
                                if not found_selected and existing_permissions is not None:
                               
                                    if action['access_levels']:
                                        action['access_levels'][0]['label'] = "Select an Option"

                    
                except Exception as e:
                    logger.error(f"Error processing feature {feature_name}: {str(e)}")
                    continue
        
        logger.info("Permission data processing completed successfully")
        return processed_data
        
    except Exception as e:
        logger.error(f"Error in process_permissions_data: {str(e)}")
        return {}  # Return empty dict on error


def get_template_context(
    feature_data: Dict,
    template_id: Optional[int] = None,
    existing_permissions: Optional[List[str]] = None
) -> Dict:
    """
    Generate the complete template context with processed permissions data.
    Maintains original order of access levels.
    
    Args:
        feature_data (Dict): Raw feature data containing all categories and features
        template_id (Optional[int]): ID of the template being edited, if any
        existing_permissions (Optional[List[str]]): List of permission codenames from an existing group
        
    Returns:
        Dict: Complete context dictionary for template rendering with is_active status
    """
    try:
        logger.info(f"Generating template context. Template ID: {template_id}")
        processed_data = process_permissions_data(feature_data, existing_permissions)
        
        context = {
            'dashboard': processed_data.get('dashboard'),
            'employee_management': processed_data.get('employee_management'),
            'client_management': processed_data.get('client_management'),
            'department_management': processed_data.get('department_management'),
            'roster_management': processed_data.get('roster_management'),
            'client_incident_report': processed_data.get('client_incident_report'),
            'progress_notes_and_timesheet': processed_data.get('progress_notes_and_timesheet'),
            'admin_control': processed_data.get('admin_control'),
            'settings': processed_data.get('settings'),
            'is_edit_mode': template_id is not None,
            'template_id': template_id
        }
        
        logger.info("Template context generated successfully")
        return context
        
    except Exception as e:
        logger.error(f"Error in get_template_context: {str(e)}")
        return {}  # Return empty context on error
    


PERMISSION_SETS = {
    "employee_profile": EMPLOYEE_PERMISSION_SET,
    "document": DOCUMENT_PERMISSION_SET,
    "client_profile": CLIENT_PERMISSION_SET,
    "risk_assessment": RISK_ASSESSMENT_PERMISSION_SET,
    "client_incident_report": INCIDENT_PERMISSION_SET,
    "department_management": DEPARTMENT_PERMISSION_SET,
    "shift_dashboard": SHIFT_DASHBOARD_PERMISSION_SET,
    "shift_report": SHIFT_REPORT_PERMISSION_SET,
    "progress_notes_and_timesheet": PROGRESS_NOTES_AND_TIMESHEET_PERMISSION_SET,
    "incident_investigation": INCIDENT_INVESTIGATION_PERMISSION_SET,
    "privacy_policy": PRIVACY_POLICY_PERMISSION_SET,
    "terms_and_conditions": TERMS_AND_CONDITIONS_PERMISSION_SET,
    "user_permissions": USER_PERMISSION_SET,
}




def validate_feature_permissions(feature_permissions):
    """
    Validates feature permissions against defined permission sets.
    Ensures action dependencies are followed dynamically, including nested dependencies.
    """

    if not feature_permissions:
        return False, "Template permissions are missing."

    feature_data_dict = json.loads(feature_permissions)

    for feature, permissions in feature_data_dict.items():
        if feature not in PERMISSION_SETS:
            print(f"Feature '{feature}' not found in PERMISSION_SETS.")
            continue

        # Get the permission set for the feature
        permission_set = PERMISSION_SETS[feature]
        parent_feature_code = []
        feature_allowed_permissions = []
        current_post_permissions = []

        for permission in permissions:
            post_data_action = permission.get('action')
            post_data_access_level_code = permission.get('accessLevelCode')

            if post_data_action not in permission_set:
                return False, f"Action '{post_data_action}' is not valid for feature '{feature}'."

            access_level = permission_set[post_data_action].get(post_data_access_level_code)
            
            if access_level is None:
                return False, f"Access Level '{post_data_access_level_code}' is not valid for Action '{post_data_action}' in feature '{feature}'."

            allowed_permissions = access_level
            print(f"Feature: {feature}, Action: {post_data_action}, Access Level: {post_data_access_level_code}, Allowed Permissions: {allowed_permissions}")
            
            allowed_permissions = {k: v for k, v in allowed_permissions.items() if v} 
            
            if not allowed_permissions:
                continue
            
         
            action_permissions = permission_set.get(post_data_action, {})

            action_permissions_for_level = action_permissions.get(post_data_access_level_code, {})
            if not len(parent_feature_code) > 0:
                parent_feature_code.append(post_data_access_level_code)
                if 'create' in action_permissions_for_level:
                    for perm in action_permissions_for_level['create']:
                        feature_allowed_permissions.append(perm['code'])
                    print(f"Allowed create codes for '{post_data_action}': {feature_allowed_permissions}")

                if 'read' in action_permissions_for_level:
                    for perm in action_permissions_for_level['read']:
                        feature_allowed_permissions.append(perm['code'])
                    print(f"Allowed create codes for '{post_data_action}': {feature_allowed_permissions}")
                    
                if 'update' in action_permissions_for_level:
                    for perm in action_permissions_for_level['update']:
                        feature_allowed_permissions.append(perm['code'])
                    print(f"Allowed update codes for '{post_data_action}': {feature_allowed_permissions}")

                if 'delete' in action_permissions_for_level:
                    for perm in action_permissions_for_level['delete']:
                        feature_allowed_permissions.append(perm['code'])
                    print(f"Allowed delete codes for '{post_data_action}': {feature_allowed_permissions}")

                if 'export' in action_permissions_for_level:
                    for perm in action_permissions_for_level['export']:
                        feature_allowed_permissions.append(perm['code'])
                    print(f"Allowed export codes for '{post_data_action}': {feature_allowed_permissions}")

            if post_data_access_level_code not in parent_feature_code:
                current_post_permissions.append(post_data_access_level_code)

        if len(current_post_permissions) > 0: 
            if set(current_post_permissions).issubset(set(feature_allowed_permissions)):  
                continue      
                
            else:
                return False
    return True




def get_employee_permissions():
    return [
        "read_own_reports",
        "create_employee_none",
        "read_own_employees",
        "update_own_employees",
        "read_own_documents",
        "import_own_documents",
        "delete_own_documents",
        "create_client_none",
        "create_risk_assessments_of_their_own",
        "read_risk_assessments_of_their_own",
        "read_own_shift",
        "view_terms_and_conditions_all",
        "view_privacy_policy_all",
        "create_incident_there_own",
        "view_incident_own",
        "update_incident_no_access",
        "export_incident_no_access",
        "create_progress_notes_own",
        "view_progress_notes_own",
        "update_progress_notes_own",
        # "read_incident_investigation_none",
        # "update_incident_investigation_none",
        "risk_assessment_update_none",
        "create_shift_none",
        "update_roster_shift_none",
        "delete_no_shift_access",
        "export_none",
        # "create_templates_none",
        # "read_templates_none",
        "create_department_none",
        "update_none_terms_and_conditions",
        "update_none_privacy_policy",
        "update_templates_none"
    ]



from company_admin.models import CompanyGroup
from django.contrib.auth.models import Group, Permission

def assign_permission_to_group(company, group_name, permission_mapper_role,employee):
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
        
        # "employee": [
        #     "read_own_reports","create_employee_none","read_own_employees","update_own_employees","read_own_documents","import_own_documents","delete_own_documents","create_client_none",
        #     "create_risk_assessments_of_their_own","read_risk_assessments_of_their_own","read_own_shift","view_terms_and_conditions_all","view_privacy_policy_all","create_incident_there_own",
        #     "view_incident_own","update_incident_no_access","export_incident_no_access","create_progress_notes_own","view_progress_notes_own","update_progress_notes_own","read_incident_investigation_none",
        #     "update_incident_investigation_none","risk_assessment_update_none","create_shift_none","update_roster_shift_none","delete_no_shift_access","export_none","create_templates_none","read_templates_none","create_department_none",
        #     "update_none_terms_and_conditions", "update_none_privacy_policy"
        # ]
        "employee": [
            "read_own_reports","create_employee_none","read_own_employees","update_own_employees","read_own_documents","import_own_documents","delete_own_documents","create_client_none",
            "create_risk_assessments_of_their_own","read_risk_assessments_of_their_own","read_own_shift","view_terms_and_conditions_all","view_privacy_policy_all","create_incident_there_own",
            "view_incident_own","update_incident_no_access","export_incident_no_access","create_progress_notes_own","view_progress_notes_own","update_progress_notes_own",
            "risk_assessment_update_none","create_shift_none","update_roster_shift_none","delete_no_shift_access","export_none","create_department_none",
            "update_none_terms_and_conditions", "update_none_privacy_policy"
        ]
    }

    permissions = group_permissions.get(permission_mapper_role, group_permissions["employee"])

    group, _ = CompanyGroup.bells_manager.get_or_create(
        company=company,
        group=Group.objects.get(name=group_name),
    )

    existing_permissions = Permission.objects.filter(codename__in=permissions)
    missing_permissions = set(permissions) - set(existing_permissions.values_list("codename", flat=True))

    if missing_permissions:
        print(f"Missing permissions for group {group_name}: {missing_permissions}")
    
    if group:
        group.group.permissions.set(existing_permissions)






def create_default_group_for_companies(company):
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
        # Create a group specific to this company
        group_full_name = f"{company.company_code} - {group_name}".lower()
        django_group, created = Group.objects.get_or_create(name=group_full_name)
        
        # Create or get CompanyGroup linking the company and group
        company_group, _ = CompanyGroup.objects.get_or_create(
            company=company,
            group=django_group
        )
        
        # Get existing permissions and assign them to the group
        existing_permissions = Permission.objects.filter(codename__in=permissions)
        missing_permissions = set(permissions) - set(existing_permissions.values_list('codename', flat=True))

        if missing_permissions:
            print(f"Missing permissions for group {group_name} in {company.company_code}: {missing_permissions}")
        
        # Set the permissions
        django_group.permissions.set(existing_permissions)
        
    return True



def get_company_templates(company):
    """
    Get company templates divided into user templates and simple templates based on specific criteria.
    
    Args:
        company: The company object to get templates for
        
    Returns:
        tuple: (simple_templates, user_templates)
            - simple_templates: List of templates not ending with 'user' or without associated employees
            - user_templates: List of dictionaries containing templates ending with 'user' that have 
              associated employees, along with their valid emails
    """
    # Get all company templates with annotated middle_name
    all_templates = (
        CompanyGroup.bells_manager
        .filter(company=company)
        .annotate(
            middle_name=Replace(
                'group__name', 
                Value(company.company_code + ' - '),  
                Value('')  
            )
        )
        .annotate(
            has_employee=Exists(
                Employee.objects.filter(template=OuterRef("group"))
            )
        )
        .order_by(Lower('middle_name'))
    )
    
    # Get valid emails for filtering
    valid_emails = set(Person.objects.values_list("email", flat=True))
    
    # Process user templates
    user_templates = []
    for template in all_templates:
        if template.group.name.endswith('user') and template.has_employee:
            # Get list of valid employee emails for this template
            employee_emails = [
                email for email in Employee.bells_manager.filter(
                    template=template.group
                ).values_list("person__email", flat=True)
                if email in valid_emails
            ]
            
            # Only include templates with valid emails
            if employee_emails:
                user_templates.append({
                    "template": template,
                    "emails": employee_emails
                })
    
    # Process simple templates
    simple_templates = [
        template for template in all_templates
        if not (template.group.name.endswith('user') and template.has_employee)
    ]
    
    # Return as a tuple to match existing code
    return simple_templates, user_templates


def format_templates(simple_templates, user_templates):
    """
    Format templates by modifying their display names.

    Args:
        simple_templates (list): List of simple templates.
        user_templates (list): List of user templates (dicts with 'template' and 'emails').

    Returns:
        tuple: (formatted_simple_templates, formatted_user_templates)
    """
    # Process simple templates - remove 'codigomantra - ' prefix
    formatted_simple_templates = []
    for template in simple_templates:
        new_name = template.group.name.replace("codigomantra - ", "")
        template.group.name = new_name
        formatted_simple_templates.append(template)

    # Process user templates - replace name with employee's full name
    formatted_user_templates = []
    for user_template in user_templates:
        template = user_template["template"]
        employees = Employee.bells_manager.filter(template=template.group)

        if employees.exists():
            first_employee = employees.first()
            new_name = f"{first_employee.person.first_name} {first_employee.person.last_name}"
            template.group.name = new_name

        formatted_user_templates.append({
            "template": template,
            "emails": user_template["emails"]
        })

    return formatted_simple_templates, formatted_user_templates




def auth_user_full_name(request):
    first_name = request.user.employee.person.first_name
    last_name = request.user.employee.person.last_name
    return f'{first_name} {last_name}'