from employee.models import *
from company_admin.models import *

# script for creating client employee assignments and department client assignments
def generate_client_dept_assignments(company_id):
    """
    Generate client-employee and department-client assignments for a given company.
    """
    print('Starting client and department assignment generation...')
    
    employees = Employee.bells_manager.filter(company__id=company_id)
    print(f"Employees found for company {company_id}: {employees}")

    client_assignment_details = ClientAssignmentDetail.bells_manager.filter(client_assignment__employee__in=employees)
    print(f"ClientAssignmentDetails found: {client_assignment_details}")

    new_client_employee_assignments = [
        ClientEmployeeAssignment(
            client=detail.client,
            employee=detail.client_assignment.employee,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
            created_by=detail.client_assignment.created_by,
        )
        for detail in client_assignment_details
    ]
    ClientEmployeeAssignment.bells_manager.bulk_create(new_client_employee_assignments)

    new_department_client_assignments = []
    for employee in employees:
        if employee.role == 3:  # Assuming role 3 refers to department heads or admins
            departments = employee.departments.filter(is_deleted=False)
            print(f"Departments for employee {employee.id}: {departments}")

            assigned_clients = Client.bells_manager.filter(
                client_assignments_detail__client_assignment__employee=employee,
                client_assignments_detail__is_deleted=False,
            ).distinct()
            print(f"Assigned clients for employee {employee.id}: {assigned_clients}")

            for department in departments:
                for client in assigned_clients:
                    new_department_client_assignments.append(
                        DepartmentClientAssignment(
                            department=department,
                            client=client,
                            created_at=department.created_at,
                            updated_at=department.updated_at,
                            created_by=department.author,
                        )
                    )
    DepartmentClientAssignment.bells_manager.bulk_create(new_department_client_assignments)
    print(f"Migration completed successfully for company ID: {company_id}")

companies = Company.objects.all()

for company in companies:
    generate_client_dept_assignments(company.id)
