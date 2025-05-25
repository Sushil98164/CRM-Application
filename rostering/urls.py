from django.urls import path
from .views import *

app_name = 'rostering'

urlpatterns = [
    
    #admin urls
    path('rostering/dashboard',ManagerRosteringDashboard.as_view(), name='manager_rostering_dashboard'),
    path('shift/reports',ManagerShiftReportView.as_view(), name='manager_shift_report_view'),
    path('filter-employees/', FilterEmployeesByClientView.as_view(), name='filter_employees_by_client'),
    path('create/shift/', CreateEmployeeShift.as_view(), name='create_employee_shift'),
    path('un-assigned/clients-employees/list', UnassignedShiftsClientsEmployeeList.as_view(), name='unassigned_clients_employees_list'),
    path('fetch/shifts/calendar', ShiftsCalendar.as_view(), name='fetch_shifts_to_calendar'),
    path('shift/details/', ShiftDetails.as_view(), name='shift_details'),
    path('edit/shift/details/', EditShiftDetailsView.as_view(), name='edit_shift_details'),
    path('edit-filter-employees/', EditFilterEmployeesByClient.as_view(), name='edit_filter_employees_by_client'),
    path('edit/shift/', EditEmployeeShift.as_view(), name='edit_employee_shift'),
    path('delete-shift/', DeleteShift.as_view(), name='delete_shift'),
    path('download-shifts-report/', downloadShiftsReport, name='download_shifts_report'),
    path('get-employee-client/', GetEmployeeClient, name='get_employee_client'),





    #employee urls
    path('employee/shifts/dashboard',EmployeeShiftsDashboard.as_view(), name='employee_shifts_dashboard'),
    path('employee/shift/details/', EmployeeShiftDetails.as_view(), name='employee_shift_details'),
    path('fetch/employee/shifts/calendar',FetchEmployeeShiftsToCalendar.as_view(), name='fetch_employee_shifts_to_calendar'),

    path('employee/shifts/list',EmployeeShiftsListView.as_view(), name='employee_shifts_list_view'),
    # path('employee/previous/shifts/list',EmployeeShiftsListView.as_view(), name='employee_previous_shifts_list_view'),
    path('employee/ongoing/shifts/list',EmployeeShiftsListView.as_view(), name='employee_ongoing_shifts_list_view'),


    path('shift/employee/list/',EmployeeShiftsListView.as_view(),name='dailyshift_list_employee')


    


]