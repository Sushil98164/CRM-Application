from django import template
import ast
from userauth.utils import has_user_permission
from company_admin.models import DepartmentClientAssignment
from userauth.models import Employee
import os

register = template.Library()


@register.filter
def get_dict_value(value):
    try:
        dict_value = ast.literal_eval(value)
        return ', '.join(dict_value.values())
    except (ValueError, SyntaxError):
        return value
        
# @register.filter(name='split_string')
# def split_string(value, delimiter=" - "):
#     """
#     Splits a string by a delimiter and returns the second part or adjusts for user templates.
#     If the delimiter is not found, the original value is returned.
#     """
#     if value:
#         is_exit=Employee.bells_manager.filter(template__name = value).exists()
#         if " - user" in value and is_exit:
#             parts = value.split(delimiter)
#             return parts[-2].strip() if len(parts) > 1 else value  # For user templates, use the second-to-last part

#         else:
#             parts = value.split(delimiter)
#             return parts[1].strip() if len(parts) > 1 else value  # For non-user templates, use the second part
#     return value



@register.filter(name='split_string')
def split_string(value, delimiter=" - "):
    """
    Splits a string by a delimiter and returns the second part or adjusts for user templates.
    If the delimiter is not found, the original value is returned.
    """
    if value:
        is_exit=Employee.bells_manager.filter(template__name = value).exists()
        if " - user" in value and is_exit:
            # parts = value.split(delimiter)
            # # return parts[-2].strip() if len(parts) > 1 else value 
            # name_parts = parts[1].rsplit("-", 1)[0].split("-")  # Extract and split by "-"
            # first_name = name_parts[0].strip() if len(name_parts) > 0 else ""
            # last_name = name_parts[1].strip() if len(name_parts) > 1 else ""

            # # Handle cases where first_name or last_name is missing
            # if first_name and last_name:
            #     parts = f"{first_name} {last_name}"
            # elif last_name:  # If only last_name exists
            #     parts = last_name
            # else:
            #     parts = ""  # Both are missing, return empty string
            employee = Employee.bells_manager.filter(template__name = value).first()
            full_name = f'{employee.person.first_name} {employee.person.last_name}'
            parts = full_name
            return parts
        else:
            parts = value.split(delimiter)
            return parts[1].strip() if len(parts) > 1 else value  # For non-user templates, use the second part
    return value



@register.filter
def has_permission(user, permission_code):
    return user.has_perm(permission_code)



@register.simple_tag
def can_access_team_data(user, employee_id, company_id):
    """
    Checks if the user has permissions to access team data based on department.
    Returns True if the user has 'read_all_documents' permission or if the user can read team documents based on department.
    """
    has_read_all_permission = has_user_permission(user, 'employee.read_all_documents')
    has_read_all_employees = has_user_permission(user, 'userauth.read_all_employees')
    has_team_employees = has_user_permission(user, 'userauth.read_team_employees')
    has_self_permission = has_user_permission(user, 'userauth.read_own_employees')

    

    if has_read_all_permission:
        return True
    
    # if has_read_all_employees or has_team_employees or has_self_permission:
    if (has_read_all_employees or has_team_employees or has_self_permission) and not has_user_permission(user, 'employee.read_team_documents'):

        if employee_id == user.employee.id:
            return True
        return False
    if  has_user_permission(user, 'employee.read_team_documents'):
        department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company_id)
        department_data['departments'] and department_data['clients'] and department_data['employees']
        department_employee_ids = set(employee.id for employee in department_data['employees'])
        if employee_id in department_employee_ids:
            has_read_permission = has_user_permission(user, 'employee.read_team_documents')
            return has_read_permission
    if has_user_permission(user, 'employee.read_own_documents') and user.employee.id == employee_id:
            has_read_self_permission =  has_read_self_permission = has_user_permission(user, 'employee.read_own_documents')
            return  has_read_self_permission
  
    return False

@register.simple_tag
def can_access_own_data(user, employee_id, company_id):
    """
    Checks if the user has permissions to access team data based on department.
    Returns True if the user has 'read_all_documents' permission or if the user can read team documents based on department.
    """
    has_read_all_permission = has_user_permission(user, 'employee.read_all_documents')
    has_read_own_permission = has_user_permission(user, 'employee.read_own_documents')

    if has_read_all_permission or has_read_own_permission:
        return True

    department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company_id)

    if department_data['departments'] and department_data['clients'] and department_data['employees']:
        department_employee_ids = set(employee.id for employee in department_data['employees'])
        if employee_id in department_employee_ids:
            has_read_permission = has_user_permission(user, 'employee.read_team_documents')
            return has_read_permission
    return False



from company_admin.models import ClientEmployeeAssignment

@register.simple_tag
def can_access_risk_assessment_data(user, client_id, company_id):
 
    has_create_all_permission = has_user_permission(user, 'company_admin.create_all_risk_assessments')

    if has_create_all_permission:
        return True
    # if has_user_permission(user, 'company_admin.create_risk_assessments_team_own'):
    #     department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company_id)
    #     department_data['departments'] and department_data['clients'] and department_data['employees']
    #     department_client_ids = set(client.id for client in department_data['clients'])
    #     if client_id in department_client_ids:
    #         has_create_team_permission = has_user_permission(user, 'company_admin.create_risk_assessments_team_own')
    #         return has_create_team_permission
    
    if has_user_permission(user, 'company_admin.create_risk_assessments_team_own'):
        department_data = DepartmentClientAssignment.get_manager_department_data(
            manager_id=user.employee.id,
            company_id=company_id
        )
        team_client_ids = {client.id for client in department_data.get('clients', [])}
        
        # Also include user's own clients
        own_clients = ClientEmployeeAssignment.get_clients_by_employee(user.employee.id, company_id)
        own_client_ids = {client.id for client in own_clients}

        combined_client_ids = team_client_ids.union(own_client_ids)
        return client_id in combined_client_ids
        
    if has_user_permission(user, 'company_admin.create_risk_assessments_of_their_own'):
        clients = ClientEmployeeAssignment.get_clients_by_employee(user.employee.id,company_id)
        if client_id in [client.id for client in clients]:
            has_read_self_permission =  has_read_self_permission = has_user_permission(user, 'company_admin.create_risk_assessments_of_their_own')
            return  has_read_self_permission
    return False



@register.simple_tag
def can_access_self_risk_assessment_data(user, client_id, company_id):
 
    has_create_all_permission = has_user_permission(user, 'company_admin.create_all_risk_assessments')
    has_create_own_permission = has_user_permission(user, 'company_admin.create_risk_assessments_of_their_own')

    if has_create_all_permission:
        return True
    if has_create_own_permission:
        return True

    department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company_id)

    if department_data['departments'] and department_data['clients'] and department_data['employees']:
        department_client_ids = set(client.id for client in department_data['clients'])
        if client_id in department_client_ids:
            has_create_team_permission = has_user_permission(user, 'company_admin.create_risk_assessments_team_own')
            return has_create_team_permission
    return False


@register.simple_tag
def can_update_risk_assessment_data(user, client_id, company_id):
 
    has_update_all_permission = has_user_permission(user, 'company_admin.update_all_risk_assessments')

    if has_update_all_permission:
        return True
    
    department_data = DepartmentClientAssignment.get_manager_department_data(manager_id=user.employee.id, company_id=company_id)

    if department_data['departments'] and department_data['clients'] and department_data['employees']:
        department_client_ids = set(client.id for client in department_data['clients'])
        if client_id in department_client_ids:
            has_create_team_permission = has_user_permission(user, 'company_admin.update_team_risk_assessments')
            return has_create_team_permission
    return False



@register.filter
def risk_get_dict_value(dictionary, key):
    """Get the value from a dictionary using the provided key."""
    return dictionary.get(key, [])

@register.filter
def group_get_dict_value(dictionary, key):
    """Get the value from a dictionary using the provided key."""
    return dictionary.get(key, [])


@register.simple_tag(takes_context=True)
def counter(context):
    if 'global_counter' not in context:
        context['global_counter'] = 1
    else:
        context['global_counter'] += 1
    return context['global_counter']



@register.filter
def basename(value):
    """Return the base name of a file path or URL"""
    return os.path.basename(value)