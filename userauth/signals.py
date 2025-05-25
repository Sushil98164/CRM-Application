from django.db.models.signals import m2m_changed,post_save
from django.dispatch import receiver
from .models import Department, Employee
from django.contrib.auth.models import Group

EMPLOYEE_ROLE = (
        (1,'Admin'),
        (2,'Manager'),
        (3,'Employee'),
    )

@receiver(post_save, sender=Employee)
def update_employee_permissions_on_save(sender, instance, created, **kwargs):
    """
    Signal to update employee permissions when an Employee is saved.
    """
    pass
    # instance.update_permissions()

@receiver(m2m_changed, sender=Group.permissions.through)
def update_employee_permissions_on_group_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Signal to update employee permissions when Group permissions change.
    """
    pass
    # if action in ["post_add", "post_remove", "post_clear"]:
    #     role_value = next((k for k, v in EMPLOYEE_ROLE if v == instance.name), None)
    #     if role_value is not None:
    #         employees = Employee.objects.filter(role=role_value)
    #         for employee in employees:
    #             employee.update_permissions()


def sync_employee_departments(instance, action, pk_set):
    """
    Synchronizes the Employee-Department relationship.
    Handles both post_add and post_remove actions to ensure
    the manager and employee associations are correctly updated.
    """
    company = instance.company

    if action == "post_add":
        departments = Department.bells_manager.filter(pk__in=pk_set, company=company)
        for dept in departments:
            if instance.role == 2: 
                previous_manager = dept.manager
                if previous_manager:
                    previous_manager.departments.remove(dept)
                    previous_manager.save()
                dept.manager = instance
                dept.save()

            else:
                dept.employees.add(instance)
                dept.save()

    
    if action == "post_remove":
        removed_departments = Department.bells_manager.filter(pk__in=pk_set, company=company)
        
        for dept in removed_departments:
            if instance.role == 2: 
                if dept.manager == instance:
                    dept.manager = None
                dept.employees.remove(instance)
                dept.save()

            else:
                dept.employees.remove(instance)
                dept.save()

                    

# def remove_employee_from_department_when_template_changes(employee_instance,departments_to_add,departments_to_remove):
#     if employee_instance.role == 2:
#         for department_id in departments_to_add:
#             department = Department.bells_manager.filter(id=department_id).first()
#             if department:
#                 department.manager = employee_instance
#                 department.employees.remove(employee_instance)
#                 department.save()
#                 employee_instance.departments.add(department)
#                 employee_instance.save()
#         if departments_to_remove:
#             for department_id in departments_to_remove:
#                 department = Department.bells_manager.filter(id=department_id).first()
#                 if department:
#                     department.employees.remove(employee_instance)
#                     department.save()
#                     employee_instance.remove.add(department)
#                     employee_instance.save()
  
#     elif employee_instance.role == 3:
#         for department_id in departments_to_add:
#             department = Department.bells_manager.filter(id=department_id).first()
#             if department:
#                 department.manager= None
#                 department.employees.add(employee_instance)
#                 department.save()
#                 employee_instance.departments.add(department)
#                 employee_instance.save()

        
#         for department_id in departments_to_remove:
#             department = Department.bells_manager.filter(id=department_id).first()
#             if department:
#                 department.manager= None
#                 department.save()
#                 employee_instance.departments.remove(department)
#                 employee_instance.save()



def remove_employee_from_department_when_template_changes(employee_instance,departments_to_remove):
    for department_id in departments_to_remove:
        department = Department.bells_manager.filter(id=department_id).first()
        if department:
            department.manager = None
            department.save()
      
    

def employeement_assignment_to_department(employee_instance,departments_to_add,departments_to_remove):
    for department_id in departments_to_add:
        department = Department.bells_manager.filter(id=department_id).first()
        if department:
            department.employees.add(employee_instance)
            department.save()
    
    for department_id in departments_to_remove:
        department = Department.bells_manager.filter(id=department_id).first()
        if department:
            department.employees.remove(employee_instance)
            department.save()

    
@receiver(post_save, sender=Department)
def sync_department_manager(sender, instance, **kwargs):
    """
    This signal handler ensures that when a manager is assigned to a department,
    the corresponding relationship is updated in the Employee model. If the manager
    changes, the department is removed from the previous manager's list. pass
    """
    previous_manager = Employee.bells_manager.filter(departments=instance,role=2).first()

    if previous_manager and previous_manager != instance.manager:
        previous_manager.departments.remove(instance)

    if instance.manager:
        instance.manager.departments.add(instance)

  
def employee_soft_delete_remove_department(employee):
    '''
    Remove employee from department when employee is soft deleted
    '''
    try:
        if employee.role == '2':
            managed_departments = Department.bells_manager.filter(manager=employee)
            if managed_departments.exists():
                managed_departments.update(manager=None)
        
        if employee.role == '3':
            employee.assigned_departments.clear()
        employee.departments.clear()
    except Exception as e:
        print(f'Employee department removal error:{e}')
        
        


def update_template_permissions(instance):
    affected_employees = Employee.bells_manager.filter(template=instance)
    for employee in affected_employees:
        employee.person.user_permissions.clear()
        template_permissions = instance.permissions.all()
        employee.person.user_permissions.add(*template_permissions)
        employee.person.save()