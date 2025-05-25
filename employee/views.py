from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from employee.forms import *
from company_admin.models import Incident, IncidentAttachment, DailyShiftCaseNote
from userauth.models import Employee, Client
from userauth.decorators import *
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib import messages
from employee.tasks import *
from userauth.forms import *
import json
from django.db.models import Q
from django.forms import formset_factory
from django.http import  JsonResponse
from company_admin.forms import RiskAssessmentDetailForm,RiskDocumentationApprovalForm,RiskMoniterControlForm, RiskAssessmentForm
from django.utils import timezone
from django.db.models.functions import Lower
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from company_admin.helpers import paginate_query
from userauth.utils import has_user_permission  
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@method_decorator(login_required, name='dispatch')
@method_decorator(employee_role_required, name='dispatch')
@method_decorator(employee_can_access_mandatory_incident_report, name='dispatch')
class MandatoryIncidentView(View):
    template_name = 'employee/mandatory-incident-list.html'

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company = employee.company
        assigned_clients = Client.bells_manager.filter(
            client_assignments_detail__client_assignment__employee=employee,
            client_assignments_detail__is_deleted=False,
            client_assignments_detail__client_assignment__is_deleted=False
        ).distinct()
        incidents = Incident.bells_manager.filter(
            employee=employee,
            company=company,
            report_type="Mandatory Incident",
            client__in=assigned_clients,
            client__is_deleted=False
        ).order_by('-created_at')
        # incidents = Incident.bells_manager.filter(employee=employee, company=company,report_type="Mandatory Incident",client__is_deleted=False).order_by('-created_at')
        return render(request, self.template_name, {'incidents': incidents, 'employee': employee})


@method_decorator(login_required, name='dispatch')
@method_decorator(employee_role_required, name='dispatch')
@method_decorator(employee_can_access_mandatory_incident_report, name='dispatch')
class MandatoryIncidentOperationView(View):
    template_name = "employee/mandatory-incident-operations.html"

    def get(self, request, incident_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        employee = request.user.employee
        company = employee.company
        incident_form = MandatoryIncidentForm(initial={'employee': employee, 'company': company,'report_type':"Mandatory Incident", 'status': 'New', 'sno': company.mandatory_next_sno(), 'report_code': company.mandatory_report_code()}, company=company)
        
        client_assignments = ClientAssignment.bells_manager.filter(employee=employee)
        severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)


        incident_form.fields['client'].queryset = Client.bells_manager.filter(
            client_assignments_detail__client_assignment__in=client_assignments,
            client_assignments_detail__is_deleted=False
        ).distinct() 
        context = {
            "incident_form": incident_form,
            'attachment_form': IncidentAttachmentForm(),
            'severity_levels_json':severity_levels_json
        }
        if incident_id and 'mandatory_incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id)
                incident_form = MandatoryIncidentForm(
                    instance=incident, company=company)
                client_assignments = ClientAssignment.bells_manager.filter(employee=employee)

                incident_form.fields['client'].queryset = Client.bells_manager.filter(
                    client_assignments_detail__client_assignment__in=client_assignments,
                    client_assignments_detail__is_deleted=False
                ).distinct() 
                attachments_files = IncidentAttachment.bells_manager.filter(
                    incident=incident)
                initial_data = [
                    attachement for attachement in attachments_files]
                context['attachment_data'] = initial_data
                context['incident_form'] = incident_form
            except:
                return HttpResponseRedirect(reverse('employee:mandatory_incident_list'))

        return render(request, self.template_name, context)

    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, incident_id=None, *args, **kwargs):
        if 'mandatory_incident_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, incident_id)
        employee = request.user.employee
        company = employee.company
        attachment_formset = MandatoryIncidentAttachmentForm(
            request.POST, request.FILES)
        if incident_id and 'mandatory_incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id, )
                incident_form = MandatoryIncidentForm(request.POST, instance=incident, company=company)
                messages.error(request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return HttpResponseRedirect(reverse('employee:mandatory_incident_list'))
            except:
                return HttpResponseRedirect(reverse('employee:mandatory_incident_list'))
        else:
            incident_form = MandatoryIncidentForm(request.POST, {'employee': employee, 'company': company, 'status': 'New', 'sno': company.mandatory_next_sno(
            ), 'report_code': company.mandatory_report_code()}, company=company)

        if incident_form.is_valid() and attachment_formset.is_valid():
            try:
                files = request.FILES
                instance = incident_form.save()
                for file in files.getlist('file'):
                    IncidentAttachment.objects.create(
                        incident=instance, file=file)
                if incident_id and 'mandatory_incident_edit' in request.resolver_match.url_name:
                    delete_attachment_list = request.POST.get(
                        'deleteAttachmentFile', None)
                    if delete_attachment_list is not None:
                        data = [int(file_id) for file_id in delete_attachment_list.split(
                            ',') if file_id.isdigit()]
                        for i in data:
                            IncidentAttachment.objects.filter(
                                id=i).update(is_deleted=True)
                    messages.success(
                        request, 'Mandatory Incident updated successfully!')
                else:
                    messages.success(
                        request, 'Mandatory Incident added successfully!')
                    # incident email
                    company_email = request.user.employee.company.email_for_alerts
                    company_name = request.user.employee.company.name
                    employee_email = request.user.email
                    report_code = str(incident_form.cleaned_data['report_code'])
                    client_first_name = incident_form.cleaned_data['client'].person.first_name
                    client_last_name = incident_form.cleaned_data['client'].person.last_name
                    employee_first_name = request.user.first_name
                    employee_last_name = request.user.last_name
                    incident_type = "Mandatory Incident"
                    incident_date = incident_form.cleaned_data['incident_date_time'].strftime('%Y-%m-%d %H:%M:%S')
                    employee_email_template = 'employee/email/employee-incident-report.html'
                    admin_email_template = 'employee/email/admin-incident-report.html'
                    send_incident_email.apply_async(args=[company_name, company_email, employee_email, employee_first_name,
                            employee_last_name,client_first_name,client_last_name, incident_date, report_code,
                            employee_email_template, admin_email_template,incident_type])
                return HttpResponseRedirect(reverse('employee:mandatory_incident_list'))
            except Exception as e:
                print(request, f"An error occurred: {e}")
                context = {
                    'incident_form': incident_form,
                    'attachment_form': attachment_formset,
                }
                return render(request, self.template_name, context)
        else:
            print("Form is not valid", incident_form.errors,
                  attachment_formset.errors)
            # If forms are not valid
            context = {
                'incident_form': incident_form,
                'attachment_form': attachment_formset,
            }
            return render(request, self.template_name, context)

    def handle_delete(self, request, incident_id):
        @admin_role_required
        def delete_operation(request, incident_id):
            incident = get_object_or_404(Incident, pk=incident_id)
            if incident:
                incident.is_deleted = True
                incident.save()
            messages.success(
                request, 'Mandatory Incident deleted successfully!')
            return HttpResponseRedirect(reverse('employee:mandatory_incident_list'))
        return delete_operation(request, incident_id)


@method_decorator(login_required,name='dispatch')
@method_decorator(employee_role_required,name='dispatch')
def handle_mandatory_attachment_file_delete(request):
    try:
        pk = request.POST.get('file_id')
        incident = IncidentAttachment.objects.filter(id=pk)
        if incident.exists():
            incident.update(is_deleted=True)
        return HttpResponse('Remove Successfully', status=200)
    except Exception as e:
        return HttpResponse(str(e), status=300)


@method_decorator(login_required, name='dispatch')
class IncidentView(View):
    template_name = 'employee/incident-list.html'

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company = employee.company
        assigned_clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name')).distinct()


        # Filter incidents where the client is among those assigned to the employee
        incidents = Incident.bells_manager.filter(
            employee=employee,
            company=company,
            report_type="Incident",
            client__in=assigned_clients,
            client__is_deleted=False
        ).order_by('-created_at')

        # tagged_incidents = Incident.objects.filter(
        #     tagged_incident__tagged_employee=employee,
        #     tagged_incident__incident__company=company,
        #     tagged_incident__incident__client__in=assigned_clients,
        #     tagged_incident__incident__report_type="Incident",
        #     tagged_incident__incident__client__is_deleted=False
        # )

        # incidents = direct_incidents| tagged_incidents

        ordered_incidents = Incident.order_by_status(incidents)

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(ordered_incidents, items_per_page)
        try:
            ordered_incidents_obj = paginator.page(page)
        except PageNotAnInteger:
            ordered_incidents_obj = paginator.page(1)
        except EmptyPage:
            ordered_incidents_obj = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((ordered_incidents_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'employee': employee,
            'incidents': ordered_incidents_obj,
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class IncidentOperationView(View):
    template_name = "employee/incident-operations.html"

    def get(self, request, incident_id=None, *args, **kwargs):
        """
        This Method is used get request
        """
        employee = request.user.employee
        company = employee.company

        # Remove the session variables
        request.session.pop('incident_id', None)
        request.session.pop('employee_id', None)
        request.session.pop('client_id', None)

        # incident_form = IncidentForm(initial={'employee': employee, 'company': company, 'status': 'New', 'sno': company.next_sno(
        # ), 'report_code': company.next_incident_report_code()}, company=company,request=request)

        incident_form = IncidentForm(initial={'employee': employee, 'company': company, 'status': 'New'}, company=company,request=request)

        severity_levels_json = json.dumps(SEVERITY_LEVEL_CHOICES)
        
        incident_form.fields['client'].queryset = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name'))
        context = {
            "incident_form": incident_form,
            'attachment_form': IncidentAttachmentForm(),
            'severity_levels_json':severity_levels_json
        }
        if incident_id and 'incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id)
                employee = incident.employee
                incident_form = IncidentForm(instance=incident,company = company,request=request)
                incident_form.fields['client'].queryset = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name'))
                attachments_files = IncidentAttachment.bells_manager.filter(
                    incident=incident)
                initial_data = [
                    attachement for attachement in attachments_files]
                context['attachment_data'] = initial_data
                context['incident_form'] = incident_form
                context['incident_id'] = incident_id
                incident = Incident.bells_manager.get(pk=incident_id)
                context['client_id'] = incident.client.id
                context['employee'] = employee

                request.session['confirm_modal_flag'] = False

            except:
                return HttpResponseRedirect(reverse('employee:incident_list'))
        return render(request, self.template_name, context)

    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, incident_id=None, *args, **kwargs):
        if 'incident_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, incident_id)
        employee = request.user.employee
        company = employee.company
        attachment_formset = IncidentAttachmentForm(
            request.POST, request.FILES)
        if incident_id and 'incident_edit' in request.resolver_match.url_name:
            try:
                incident = Incident.bells_manager.get(pk=incident_id, )
                incident_form = IncidentForm(
                    request.POST, instance=incident, company=company,request=request)
                messages.error(
                    request, "Unauthorized access attempt. Please respect privacy and security protocols.")
                return HttpResponseRedirect(reverse('employee:incident_list'))
            except:
                return HttpResponseRedirect(reverse('employee:incident_list'))
        else:
            incident_form = IncidentForm(request.POST, {'employee': employee, 'company': company, 'status': 'New'}, company=company,request=request)
        if incident_form.is_valid() and attachment_formset.is_valid():
            try:
                files = request.FILES
                incident_form.instance.sno = company.next_sno()
                incident_form.instance.report_code = company.next_incident_report_code()
                instance = incident_form.save()
                for file in files.getlist('file'):
                    IncidentAttachment.objects.create(
                        incident=instance, file=file)
                if incident_id and 'incident_edit' in request.resolver_match.url_name:
                    delete_attachment_list = request.POST.get(
                        'deleteAttachmentFile')
                    if delete_attachment_list is not None:
                        data = [int(file_id) for file_id in delete_attachment_list.split(
                            ',') if file_id.isdigit()]
                        for i in data:
                            IncidentAttachment.objects.filter(
                                id=i).update(is_deleted=True)
                    messages.success(request, 'Incident updated successfully!')
                else:
                    messages.success(request, 'Incident added successfully!')
                    company_email = request.user.employee.company.email_for_alerts
                    company_name = request.user.employee.company.name
                    employee_email = request.user.email
                    report_code = incident_form.cleaned_data['report_code']
                    client_first_name = incident_form.cleaned_data['client'].person.first_name
                    client_last_name = incident_form.cleaned_data['client'].person.last_name
                    employee_first_name = request.user.first_name
                    employee_last_name = request.user.last_name
                    incident_date = incident_form.cleaned_data['incident_date_time'].strftime('%Y-%m-%d %H:%M:%S')
                    incident_type = "Incident"
                    employee_email_template = 'employee/email/employee-incident-report.html'
                    admin_email_template = 'employee/email/admin-incident-report.html'
                    send_incident_email.apply_async(args=[company_name, company_email, employee_email, employee_first_name,
                            employee_last_name,client_first_name,client_last_name, incident_date, report_code,
                            employee_email_template, admin_email_template,incident_type])

                # return HttpResponseRedirect(reverse('employee:incident_list'))
                incident_id = instance.id if instance.id else incident_id
                current_employee_id = instance.employee.id if instance.employee else None
                current_client_id = instance.client.id if instance.client else None
                
                
                # Store values in session
                request.session['incident_id'] = incident_id
                request.session['employee_id'] = current_employee_id
                request.session['client_id'] = current_client_id
                 
                if 'incident_edit' == request.resolver_match.url_name:
                    request.session['confirm_modal_flag'] = False
                 
                if 'incident_add' ==  request.resolver_match.url_name:
                    request.session['confirm_modal_flag'] = True
                is_invloved =incident_form.cleaned_data['employees_involved']

                if is_invloved == 'yes' and 'incident_add' ==  request.resolver_match.url_name:
                    return redirect('employee:employee_tag_employee')
                return redirect('employee:incident_list')
            
            except Exception as e:
                print(request, f"An error occurred: {e}")
                context = {
                    'incident_form': incident_form,
                    'attachment_form': attachment_formset,
                }
                return render(request, self.template_name, context)
        else:
            print("Form is not valid", incident_form.errors,
                  attachment_formset.errors)
            # If forms are not valid
            context = {
                'incident_form': incident_form,
                'attachment_form': attachment_formset,
            }
            return render(request, self.template_name, context)

    def handle_delete(self, request, incident_id):
        @admin_role_required
        def delete_operation(request, incident_id):
            incident = get_object_or_404(Incident, pk=incident_id)
            if incident:
                incident.is_deleted = True
                incident.save()
            messages.success(request, 'Incident deleted successfully!')
            return HttpResponseRedirect(reverse('employee:incident_list'))
        return delete_operation(request, incident_id)


def handle_incident_attachment_file_delete(request):
    try:
        print('asdf')
        pk = request.POST.get('file_id')

        incident = IncidentAttachment.objects.filter(id=pk)
        print(incident, 'adsf')
        if incident.exists():
            incident.update(is_deleted=True)
            return HttpResponse('Remove Successfully', status=200)
        return HttpResponse('No FIle Found', status=200)
    except Exception as e:
        return HttpResponse(str(e), status=300)



@method_decorator(login_required, name='dispatch')
class ShiftView(View):
    template_name = "employee/shifts/all-shifts-list.html"

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company = employee.company
    
        shifts = DailyShiftCaseNote.bells_manager.filter(
            employee=employee, company=company,client__is_deleted=False).order_by('-created_at')
        return render(request, self.template_name, {'shifts': shifts, 'employee': employee})

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_progress_notes_own',
                                     'company_admin.update_progress_notes_own',
                                     'company_admin.create_progress_notes_own']), name='dispatch')
class ShiftViewOperations(View):
    template_name = "employee/shifts/shift-operations.html"

    def get(self, request, shift_id=None, shift_note_id=None, *args, **kwargs):
        """
        This Method is used for GET request
        """
        employee = request.user.employee
        company = employee.company
        shift_form = None
        request.session['sno'] = None
        if 'dailyshift_add_employee' in request.resolver_match.url_name:
            # shift_form = DailyShiftNoteForm(initial={
            #     'employee': employee, 'company': company, 'sno': company.next_daily_shift_sno()
            # }, company=company, request=request)
            shift_form = DailyShiftNoteForm(initial={
                'employee': employee, 'company': company
            }, company=company, request=request)

            shift_form.fields['client'].queryset = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name'))
            employee_shift_form = EmployeeShiftsForm(request=request)
        if shift_id and ('dailyshift_edit_employee' in request.resolver_match.url_name ):
            # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
            shift_note = DailyShiftCaseNote.bells_manager.get(shift=shift_id)
            
            # Set the end date/time to the current time (i.e., the punch-out time)
            # end_date_time = timezone.now()
            try:
                # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
                # shift = DailyShiftCaseNote.bells_manager.get(pk=shift_note.id)
                shift_form = DailyShiftNoteForm(instance=shift_note, initial={
                    'shift': shift_id, 'employee': employee, 'company': company,
                }, company=company, request=request)
                employee_shift_instance = Shifts.bells_manager.filter(id=shift_id,company=company).first()
                employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance,request=request)

            except:
                return HttpResponseRedirect(reverse('rostering:dailyshift_list_employee'))


        if shift_id and request.resolver_match.url_name == 'dailyshift_edit':
            # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
            shift_note = DailyShiftCaseNote.bells_manager.get(shift=shift_id)
            
            # Set the end date/time to the current time (i.e., the punch-out time)
            end_date_time = timezone.now().replace(second=0, microsecond=0)
            try:
                # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
                # shift = DailyShiftCaseNote.bells_manager.get(pk=shift_note.id)
                shift_form = DailyShiftNoteForm(instance=shift_note, initial={
                    'shift': shift_id, 'employee': employee, 'company': company,'end_date_time':end_date_time,
                }, company=company, request=request)

            except:
                return HttpResponseRedirect(reverse('rostering:employee_shifts_list_view'))
            
        if shift_id and ('dailyshift_view' in request.resolver_match.url_name ):
            # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
            shift_note = DailyShiftCaseNote.bells_manager.get(shift=shift_id)
            
            # Set the end date/time to the current time (i.e., the punch-out time)
            # end_date_time = timezone.now()
            try:
                # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
                # shift = DailyShiftCaseNote.bells_manager.get(pk=shift_note.id)
                shift_form = DailyShiftNoteForm(instance=shift_note, initial={
                    'shift': shift_id, 'employee': employee, 'company': company,
                }, company=company, request=request)
                employee_shift_instance = Shifts.bells_manager.filter(id=shift_id,company=company).first()
                employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance,request=request)

            except:
                return HttpResponseRedirect(reverse('rostering:dailyshift_list_employee'))
        
        
        if 'dailyshift_add_employee' in request.resolver_match.url_name or 'dailyshift_edit_employee' in request.resolver_match.url_name or 'dailyshift_view' in request.resolver_match.url_name:
            context = {'shift_form': shift_form,'employee_shift_form':employee_shift_form}
        else:
            context = {'shift_form': shift_form , 'shift_id': shift_id}
        return render(request, self.template_name, context)

    def get_company(self, request):
        return request.user.employee.company

    def post(self, request, shift_id=None, shift_note_id=None, *args, **kwargs):
        employee = request.user.employee
        company = employee.company
        shift_form = None
        shift_instance = None
        # Check if URL matches dailyshift_add_employee or dailyshift_edit/view
        if 'dailyshift_add_employee' in request.resolver_match.url_name:
            shift_form = DailyShiftNoteForm(request.POST,request.FILES, initial={
                'employee': employee, 'company': company
            }, company=company, request=request)

            shift_form.fields['client'].queryset = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name'))
            
        elif shift_id and (
                        request.resolver_match.url_name == 'dailyshift_edit' or request.resolver_match.url_name == 'dailyshift_edit_employee' or 
                        'dailyshift_view' in request.resolver_match.url_name):
            company=request.user.employee.company
            shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
            if shift:
                shift_client = shift.client

            if request.resolver_match.url_name == 'dailyshift_edit':
                try:
                    # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
                    shift_note = DailyShiftCaseNote.bells_manager.get(shift=shift_id) 
                    shift_form = DailyShiftNoteForm(
                        request.POST,request.FILES, instance=shift_note, initial={
                            'client': shift_note.client.id if shift_note else None,
                            'shift': shift_id,
                            'employee': employee,
                            'company': company,
                        }, company=company, request=request)
                    

                except DailyShiftCaseNote.DoesNotExist:
                    return HttpResponseRedirect(reverse('rostering:employee_shifts_list_view'))
                
            elif request.resolver_match.url_name == 'dailyshift_edit_employee':
                try:
                    # shift_note = DailyShiftCaseNote.objects.filter(shift=shift_id).first()
                    shift_note = DailyShiftCaseNote.bells_manager.get(shift=shift_id) 
                    shift_form = DailyShiftNoteForm(
                        request.POST,request.FILES, instance=shift_note, initial={
                            'client': shift_note.client.id if shift_note else None,
                            'shift': shift_id,
                            'employee': employee,
                            'company': company,
                        }, company=company, request=request)
                    

                    # if shift_form.is_bound:  # Check if form has been bound with POST data
                    #     shift_form.fields['description'].required = False
                    #     shift_form.fields['distance_travel'].required = False
                        
                except DailyShiftCaseNote.DoesNotExist:
                    return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
                    
            

            else:
                shift_form = DailyShiftNoteForm(
                    request.POST,request.FILES, initial={
                        'client': shift_client.id, 
                        'shift': shift_id, 
                        'employee': employee, 
                        'company': company, 
                        # 'sno': company.next_daily_shift_sno()
                    }, company=company, request=request)


        # progress_note=DailyShiftCaseNote.bells_manager.filter(sno=request.session.get('sno')).first()
        # if progress_note:
        #     progress_note.sno == request.session.get('sno')
        #     return redirect('employee:dailyshift_add_employee')


        # progress_note=DailyShiftCaseNote.bells_manager.filter(sno=request.session.get('sno')).exists()
        progress_note=DailyShiftCaseNote.bells_manager.filter(sno=request.session.get('sno')).exists()

        if progress_note:
            messages.info(request,'DailyShiftCaseNote with this Company and Sno already exists.')
            return redirect('employee:dailyshift_add_employee')
        
        if shift_form.is_valid():
            try:
                if 'dailyshift_add_employee' in request.resolver_match.url_name:
                    

                    start_date_time = shift_form.cleaned_data['start_date_time']
                    end_date_time = shift_form.cleaned_data.get('end_date_time')
                   
                    # Check for overlapping shifts created by the employee
                    # overlapping_shifts = Shifts.objects.filter(
                    #     Q(employee=employee) &
                    #     Q(start_date_time__lte=end_date_time) &
                    #     Q(end_date_time__gte=start_date_time)
                    # ).exclude(id=shift_id)

                    # if overlapping_shifts.exists():
                    #     shift_form.add_error(None, "There is already a shift with same date and time")
                    #     context = {'shift_form': shift_form}
                    #     return render(request, self.template_name, context)
                    
                    
                    employee_shift_data = {
                        'employee': employee,
                        'company':company,
                        'client':shift_form.cleaned_data['client'],
                        'start_date_time': start_date_time,
                        'end_date_time': end_date_time,
                        'author':request.user.employee,
                        'shift_type':request.POST.get('shift_type'),
                        'status':'Assigned'
                    }


                    employee_shift_form = EmployeeShiftsForm(employee_shift_data,request=request)
                    if employee_shift_form.is_valid():
                        shift_instance = employee_shift_form.save()
                        shift_form.instance.shift = shift_instance
                        shift_form.instance.sno = company.next_daily_shift_sno() 
                        shift_obj = shift_form.save()
                        
                        progress_note_sno = shift_obj.sno
                        # if progress_note_sno == request.session.get('sno'):
                        #     return redirect('employee:dailyshift_add_employee')
                        # else:
                        request.session['sno'] = progress_note_sno
                company=request.user.employee.company
                shift = Shifts.bells_manager.filter(id=shift_id,company=company).first() if shift_id else shift_instance

                if 'dailyshift_add_employee' in request.resolver_match.url_name or (shift_id and request.resolver_match.url_name == 'dailyshift_edit' ):
                    description = shift_form.cleaned_data.get('description', '').strip()
                    start_date_time = shift_form.cleaned_data['start_date_time']
                    end_date_time = shift_form.cleaned_data['end_date_time'] if 'end_date_time' in shift_form.cleaned_data else None
                    if not description :
                        shift.status = 'Pending'
                    else:
                        shift.status = 'Completed'
                        shift.total_hour = shift.calculate_total_hour(start_date_time, end_date_time)

                    shift.employee = employee
                    shift.company = company
                    shift.client =shift_form.cleaned_data['client']
                    shift.start_date_time=start_date_time
                    shift.end_date_time = end_date_time
                    shift.shift_type = shift.shift_type
                    shift.status = shift.status
                    shift_form.save()
                    # shift_form.instance.shift = shift_instance

                elif 'dailyshift_edit_employee' in request.resolver_match.url_name :
                    description = shift_form.cleaned_data.get('description', '').strip()
                    start_date_time = shift_form.cleaned_data['start_date_time']
                    end_date_time = shift_form.cleaned_data['end_date_time'] if 'end_date_time' in shift_form.cleaned_data else None
                    if not description :
                        shift.status = 'Pending'
                    else:
                        shift.status = 'Completed'
                        shift.total_hour = shift.calculate_total_hour(start_date_time, end_date_time)

                    shift.employee = employee
                    shift.company = company
                    shift.client =shift_form.cleaned_data['client']
                    shift.start_date_time=start_date_time
                    shift.end_date_time = end_date_time
                    shift.shift_type = shift.shift_type
                    shift.status = shift.status
                    shift_form.save()
                else:
                    shift.status = 'Ongoing'

                shift.save()

                if  request.resolver_match.url_name == 'dailyshift_edit':
                    messages.success(request, 'Shift note updated successfully!')
                    return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
                
                elif 'dailyshift_add_employee' in request.resolver_match.url_name:
                    messages.success(request, 'Shift note added successfully!')
                    if request.GET.get('path') == 'dashboard':
                        return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
                    else:
                        return HttpResponseRedirect(reverse('company:daily_shift_note_dashboard'))
                elif 'dailyshift_edit_employee' in request.resolver_match.url_name :
                    messages.success(request, 'Shift note updated successfully!')
                    if shift.status == "Pending":
                        return HttpResponseRedirect(reverse('commpany:daily_shift_note_dashboard'))
                        
                    else:
                        return HttpResponseRedirect(reverse('commpany:daily_shift_note_dashboard'))

                else:
                    return HttpResponseRedirect(reverse('commpany:daily_shift_note_dashboard'))

                
            except Exception as e:
                print(f"An error occurred: {e}")
                employee_shift_form = EmployeeShiftsForm(request=request)

                context = {'shift_form': shift_form,'employee_shift_form':employee_shift_form}
                return render(request, self.template_name, context)
        else:
            print("Form is not valid", shift_form.errors)
            employee_shift_form = EmployeeShiftsForm(request.POST,request=request)

            context = {'shift_form': shift_form,'employee_shift_form':employee_shift_form}
            return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class EmployeeProfile(View):
    template_name = "employee/profile/my-profile.html"

    def get(self, request, *args, **kwargs):
        employee_id =request.user.employee.id
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()
        context = {
            'profile':profile_details,
            'employee_id':employee_id
        }
        return render(request, self.template_name,context)


@method_decorator(login_required, name='dispatch')
class EmployeeDocumentView(View):
    template_name = "employee/profile/my-profile.html"

    def get(self, request, *args, **kwargs):
        
        context = {}
        employee_id = request.user.employee.id
        
        id_checks_predefined_names = [
        "AUSTRALIAN DRIVER LICENSE", 
        "WORKING WITH CHILDREN CHECK OR (WWVP IN OTHER STATES)", 
        "NATIONAL POLICE CHECK",
        "INTERNATIONAL POLICE CHECK", 
        "VEVO CHECK", 
        "TRAVEL PASSPORT", 
        "AUSTRALIAN BIRTH CERTIFICATE", 
        "NDIS WORKER SCREENING CHECK"
         ]
        
        documents_queryset = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id)
        
        documents_dict = {doc.name: doc for doc in documents_queryset}
        documents_info = []
        for name in id_checks_predefined_names:
            document = documents_dict.get(name)
            if document:
                documents_info.append({
                    'id': document.id,
                    'name': document.name,
                    'file': document.file.url if document.file else None,
                    'expiry_date': document.expiry_date,
                    'status': document.status,
                    'employee_id': employee_id,
                })
            else:
                documents_info.append({
                    'id': None,
                    'name': name,
                    'file': None,
                    'expiry_date': None,
                    'status': None,
                    'employee_id': employee_id,
                })
            
        qualification_predefined_names = [
        "CERTIFICATE IN DISABILITY OR AGED CARE", 
        "NDIS WORKER ORIENTATION MODULE/PROGRAM",
        "INFECTION CONTROL TRAINING"
        ]
        qualifications_queryset = QualificationDocuments.bells_manager.filter(employee=employee_id)
        qualifications_dict = {qual.name: qual for qual in qualifications_queryset}
        qualifications_info = []
        for name in qualification_predefined_names:
            qualification = qualifications_dict.get(name)
            if qualification:
                qualifications_info.append({
                    'id': qualification.id,
                    'name': qualification.name,
                    'file': qualification.file.url if qualification.file else None,
                    'expiry_date': qualification.expiry_date,
                    'status': qualification.status,
                    'employee_id': employee_id,
                })
            else:
                qualifications_info.append({
                    'id': None,
                    'name': name,
                    'file': None,
                    'expiry_date': None,
                    'status': None,
                    'employee_id': employee_id,
                })

        
        other_predefined_names = [
        "CAR REGISTRATION", 
        "COMPREHENSIVE CAR INSURANCE",
        "MANUAL HANDLING TRAINING",
        "ASSIST CLIENTS WITH MEDICATION",
        "FIRST AID CERTIFICATE"
        ]
         
        other_documents_queryset = OtherDocuments.bells_manager.filter(employee=employee_id)
        other_documents_dict = {other.name: other for other in other_documents_queryset}
        other_documents_info = []
        for name in other_predefined_names:
            other_document = other_documents_dict.get(name)
            if other_document:
                other_documents_info.append({
                    'id': other_document.id,
                    'name': other_document.name,
                    'file': other_document.file.url if other_document.file else None,
                    'expiry_date': other_document.expiry_date,
                    'status': other_document.status,
                    'employee_id': employee_id,
                })
            else:
                other_documents_info.append({
                    'id': None,
                    'name': name,
                    'file': None,
                    'expiry_date': None,
                    'status': None,
                    'employee_id': employee_id,
                })
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()

        
        if has_user_permission(request.user, 'employee.import_all_documents') or has_user_permission(request.user, 'employee.read_all_documents') or  has_user_permission(request.user, 'employee.import_own_documents') or has_user_permission(request.user, 'employee.read_own_documents') or has_user_permission(request.user, 'employee.read_team_documents') or has_user_permission(request.user, 'employee.import_team_documents'): 
            has_own_import_permission = has_user_permission(request.user, 'employee.import_own_documents')
            has_import_permission = has_user_permission(request.user, 'employee.import_all_documents')
            has_import_team_permission = has_user_permission(request.user, 'employee.import_team_documents')

        context = {
            'other_documents_info': other_documents_info,
            'employee_id':employee_id,
            'profile':profile_details,
            'documents_info':documents_info,
            'qualifications_info': qualifications_info


        }
        if has_user_permission(request.user, 'employee.import_all_documents') or has_user_permission(request.user, 'employee.read_all_documents') or  has_user_permission(request.user, 'employee.import_own_documents') or has_user_permission(request.user, 'employee.read_own_documents') or has_user_permission(request.user, 'employee.read_team_documents') or has_user_permission(request.user, 'employee.import_team_documents'): 
            context['is_edit'] = has_import_permission or  has_own_import_permission or  has_import_team_permission

        return render(request, self.template_name,context)




@method_decorator(login_required, name='dispatch')
class MyClientsView(View):
    template_name = "employee/profile/my-profile.html"

    def get(self, request, *args, **kwargs):
        employee_id =request.user.employee.id
        company=request.user.employee.company
        client_assignments = ClientEmployeeAssignment.bells_manager.filter(employee_id=employee_id)
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()
        client_details_query = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee_id,company_id=company.id).order_by(Lower('person__first_name')).distinct()
        context = {
        'client_assignments': client_assignments,
        'profile':profile_details,
        'client_details': client_details_query,  


         }
        return render(request, self.template_name,context)

@method_decorator(login_required, name='dispatch')
class ClientsDetailView(View):
    template_name = "employee/profile/clients/client_profile.html"

    def get(self, request, client_id=None, *args, **kwargs):
        client_obj = Client.bells_manager.filter(id=client_id).first()
        employee = request.user.employee
        client_assignments = ClientAssignment.bells_manager.filter(employee=employee)
        clients = Client.bells_manager.filter(
        client_assignments_detail__client_assignment__in=client_assignments,
        client_assignments_detail__is_deleted=False
        )
        context ={
            'client_id':client_id,
            'client':client_obj,
            'clients':clients
        }
        return render(request, self.template_name,context)
    
    
@method_decorator(login_required, name='dispatch')
class ClientsRiskassessmentListView(View):
    template_name = "employee/profile/clients/client_profile.html"

    def get(self, request, client_id=None,*args, **kwargs):
        risk_assessment  = RiskAssessment.bells_manager.filter(client=client_id).order_by("-created_at")
        client_obj = Client.bells_manager.filter(id=client_id).first()
        employee = request.user.employee
        clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=employee.company.id).order_by(Lower('person__first_name')).distinct()
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(risk_assessment, items_per_page)
        try:
            risk_assessment_obj = paginator.page(page)
        except PageNotAnInteger:
            risk_assessment_obj = paginator.page(1)
        except EmptyPage:
            risk_assessment_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((risk_assessment_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'risk_assessment':risk_assessment_obj,
            'client':client_obj,
            'clients':clients

        }
        return render(request, self.template_name,context)
    

# @method_decorator(login_required, name='dispatch')
# @method_decorator(check_permissions(['company_admin.read_all_risk_assessments',
#                                      'company_admin.read_risk_assessments_team_own',
#                                      'company_admin.read_risk_assessments_of_their_own',]), name='dispatch')
# class ClientsRiskassessmentDetailView(View):
#     template_name = "employee/profile/clients/client_profile.html"
#     def get(self, request,risk_assessment_id=None,client_id=None, *args, **kwargs):
        company=request.user.employee.company
        risk_assessment = RiskAssessment.bells_manager.get(id=risk_assessment_id)
        risk_assessment_detail_obj  = RiskAssessmentDetail.objects.filter(risk_assessment=risk_assessment,is_deleted=False)              
        RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
        RiskAssessmentDetailFormSet_for_modals = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
        risk_assessment_detail_formset_for_modals = RiskAssessmentDetailFormSet_for_modals(instance=risk_assessment,  prefix='edit_detail',form_kwargs={'request': request},queryset=RiskAssessmentDetail.objects.filter(risk_assessment=risk_assessment, is_deleted=False))

        RiskDocumentationApprovalFormSet = get_formset(RiskAssessment, RiskDocumentationApproval, form=RiskDocumentationApprovalForm,extra =1 if risk_assessment.documentation.first() is None else 0)
        RiskMoniterControlFormSet = get_formset(RiskAssessment, RiskMoniterControl, form=RiskMoniterControlForm, extra=1 if risk_assessment.management_approval.first() is None else 0)

        risk_assessment_form = RiskAssessmentForm(instance=risk_assessment,company=company)
        risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.objects.none(),prefix='detail',form_kwargs={'request': request})
        risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(instance=risk_assessment,prefix='approval')
        risk_moniter_control_formset = RiskMoniterControlFormSet(instance=risk_assessment,  prefix='monitor')
        client_obj = Client.bells_manager.get(pk=client_id)

        return render(
                request,
                self.template_name,
                {
                    'risk_assessment_form': risk_assessment_form,
                    'client_id':client_id,
                    'risk_assessment_detail_formset': risk_assessment_detail_formset,
                    'risk_documentation_approval_formset': risk_documentation_approval_formset,
                    'risk_moniter_control_formset': risk_moniter_control_formset,
                    'risk_assessment_tab':True,
                    'client':client_obj,
                    'risk_assessment_detail_obj':risk_assessment_detail_obj,
                    "risk_assessment_detail_formset_for_modals":risk_assessment_detail_formset_for_modals
                    
                }
            )


class ClientsRiskassessmentOperation(View):
    """
    This view handles the operations related to risk assessment of clients 
    """

    # template_name = 'company_admin/clients/client_profile.html'
    template_name = "employee/profile/clients/client_profile.html"

    def get(self, request,client_id=None,risk_assessment_detail_id=None,risk_assessment_id=None, *args, **kwargs):
        """
        This Method is used to handle get request
        """
        company = self.get_company(request)
        client_obj = Client.bells_manager.get(pk=client_id)
        risk_view = False
        risk_assessment_detail_obj, risk_assessment_detail_formset_for_modals  = None, None
        employee= request.user.employee
        if request.resolver_match.url_name == 'client_risk_assessment_add':
            request.session['is_employee_request'] = False

        if risk_assessment_id and 'client_risk_assessment_edit' in request.resolver_match.url_name:
            try:
                risk_view = request.GET.get('risk_view') == 'True'
                
                risk_assessment = RiskAssessment.bells_manager.get(id=risk_assessment_id)
                risk_assessment_detail_obj  = RiskAssessmentDetail.objects.filter(risk_assessment=risk_assessment,is_deleted=False)              
                RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskAssessmentDetailFormSet_for_modals = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                risk_assessment_detail_formset_for_modals = RiskAssessmentDetailFormSet_for_modals(instance=risk_assessment,  prefix='edit_detail',form_kwargs={'request': request},queryset=RiskAssessmentDetail.bells_manager.filter(risk_assessment=risk_assessment, is_deleted=False))

                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment, RiskDocumentationApproval, form=RiskDocumentationApprovalForm,extra =1 if risk_assessment.documentation.first() is None else 0)
                RiskMoniterControlFormSet = get_formset(RiskAssessment, RiskMoniterControl, form=RiskMoniterControlForm, extra=1 if risk_assessment.management_approval.first() is None else 0)
                risk_assessment_form = RiskAssessmentForm(instance=risk_assessment,company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(instance=risk_assessment,prefix='approval',queryset=RiskDocumentationApproval.bells_manager.order_by('-id'))
                risk_moniter_control_formset = RiskMoniterControlFormSet(instance=risk_assessment,  prefix='monitor',queryset=RiskMoniterControl.bells_manager.order_by('-id'))
                
                request.session['risk_assessment_instance_id'] = risk_assessment.id
                request.session.pop('post_page_request', None)

            except Exception as e:
                print('e')
                return redirect('employee:client_risk_assessment_list_view')

        else:
            risk_assessment_check = request.GET.get('risk_assessment')
            if risk_assessment_check:
                last_risk_assessment_id = request.session.get('risk_assessment_instance_id',None)
                if last_risk_assessment_id and client_id:
                    risk_assessment = RiskAssessment.bells_manager.get(id=request.session['risk_assessment_instance_id'])
                    RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)                
                    RiskAssessmentDetailFormSet_for_modals = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)

                    risk_assessment_form = RiskAssessmentForm(instance=risk_assessment,company=company)
                    risk_assessment_detail_formset_for_modals = RiskAssessmentDetailFormSet_for_modals(instance=risk_assessment,  prefix='edit_detail',form_kwargs={'request': request},queryset=RiskAssessmentDetail.bells_manager.filter(is_deleted=False))
                    risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail',form_kwargs={'request': request})

                    queryset = RiskDocumentationApproval.bells_manager.filter(risk_assessment=risk_assessment).order_by('-id')
                    if not queryset.exists():
                        queryset = RiskDocumentationApproval.objects.none()
                        
                    RiskDocumentationApprovalFormSet = get_formset(
                    RiskAssessment, 
                    RiskDocumentationApproval, 
                    form=RiskDocumentationApprovalForm, 
                    extra=1 if not queryset.exists() else 0 
                        )
                    # RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1 if risk_assessment.documentation.first() is None else 0)
                    # RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1 if risk_assessment.management_approval.first() is None else 0)
                    # RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                    client = Client.bells_manager.get(id=client_id)
                    employee= request.user.employee
                   
                    risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(
                        instance=risk_assessment, 
                        prefix='approval', 
                        queryset=queryset
                    )
                    
                    # Get the queryset with the custom bells_manager, filtering for non-deleted objects
                    moniter_queryset = RiskMoniterControl.bells_manager.filter(risk_assessment=risk_assessment).order_by('-id')

                    # If the queryset is empty, we should return one form in the formset.
                    if not moniter_queryset.exists():
                        moniter_queryset = RiskMoniterControl.objects.none()  # Ensures that the formset can still render.

                    # Create the formset with the queryset and extra logic
                    RiskMoniterControlFormSet = get_formset(
                        RiskAssessment, 
                        RiskMoniterControl, 
                        form=RiskMoniterControlForm, 
                        extra=1 if not moniter_queryset.exists() else 0  
                    )

                    # Instantiate the formset with the given instance and queryset
                    risk_moniter_control_formset = RiskMoniterControlFormSet(
                        instance=risk_assessment, 
                        prefix='monitor', 
                        queryset=moniter_queryset
                    )

                    # risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(instance=risk_assessment,prefix='approval', queryset=RiskDocumentationApproval.bells_manager.order_by('-id'))
                    # risk_moniter_control_formset = RiskMoniterControlFormSet(instance=risk_assessment,  prefix='monitor',queryset=RiskMoniterControl.bells_manager.order_by('-id'))

                    # risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(queryset=RiskDocumentationApproval.objects.none(),  prefix='approval')
                    # risk_moniter_control_formset = RiskMoniterControlFormSet(queryset=RiskMoniterControl.objects.none(),  prefix='monitor')
                    risk_assessment_detail_obj  = RiskAssessmentDetail.bells_manager.filter(risk_assessment=risk_assessment,is_deleted=False)
                    if not risk_assessment_detail_obj:                
                        request.session['risk_assessment_instance_none'] = True
                    else:
                        request.session['risk_assessment_instance_none'] = False



            else:  
                RiskAssessmentDetailFormSet = get_formset(RiskAssessment,RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                client = Client.objects.get(id=client_id)
                employee= request.user.employee
                risk_assessment_form = RiskAssessmentForm(company=company,initial={'client': client, 'prepared_by': employee})
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(queryset=RiskAssessmentDetail.bells_manager.none(),prefix='detail', form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(queryset=RiskDocumentationApproval.bells_manager.none(),prefix='approval',)
                risk_moniter_control_formset = RiskMoniterControlFormSet(queryset=RiskMoniterControl.bells_manager.none(), prefix='monitor')
                request.session['risk_assessment_instance_id'] = None
                request.session.pop('edit_document_request', False)

                if request.resolver_match.url_name == 'client_employee_risk_assessment_add':
                    request.session['is_employee_request'] = True

        risk_assessment_id = request.session['risk_assessment_instance_id']

        show_investigation_for = set()
        all_investigation = has_user_permission(request.user, 'company_admin.authorize_risk_assessment_all')
        team_investigation = has_user_permission(request.user, 'company_admin.authorize_risk_assessment_own_team')
        
        if team_investigation:
            manager_data = DepartmentClientAssignment.get_manager_department_data(manager_id = employee.id,company_id=company.id)
            employee_data = manager_data['employees']
            client_data = manager_data['clients'].values_list('id',flat=True)    
            show_investigation_for.update(client_data)
        elif all_investigation:
            client_data = Client.bells_manager.values_list('id',flat=True)
            show_investigation_for.update(client_data)
        else:
            client_data = Client.bells_manager.none()
            show_investigation_for.update(client_data)
        
        return render(
                request,
                self.template_name,
                {
                    'risk_assessment_form': risk_assessment_form,
                    'client_id':client_id,
                    'risk_assessment_detail_formset': risk_assessment_detail_formset,
                    'risk_documentation_approval_formset': risk_documentation_approval_formset,
                    'risk_moniter_control_formset': risk_moniter_control_formset,
                    'risk_assessment_tab':True,
                    'client':client_obj,
                    'risk_assessment_detail_obj':risk_assessment_detail_obj,
                    "risk_assessment_detail_formset_for_modals":risk_assessment_detail_formset_for_modals,
                    "risk_assessment_id":risk_assessment_id,
                    "show_investigation_for":show_investigation_for,
                    "risk_view":risk_view
                    
                    
                }
            )

    
    def get_company(self, request):
        return request.user.employee.company

    def is_form_empty(self, form):
        for field_name, field in form.fields.items():
            value = form.cleaned_data.get(field_name)
            if value:
                return False
        return True


    def post(self, request,client_id=None, risk_assessment_detail_id=None,risk_assessment_id=None, *args, **kwargs):
        company = self.get_company(request)

        if risk_assessment_id and 'client_risk_assessment_delete' in request.resolver_match.url_name:
            return self.handle_delete(request, client_id,risk_assessment_id)
    
        if risk_assessment_id and 'client_risk_assessment_edit' in request.resolver_match.url_name:
            try:
                risk_assessment = RiskAssessment.bells_manager.get(id=risk_assessment_id)

                RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment, RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment, RiskMoniterControl, form=RiskMoniterControlForm, extra=1)

                risk_assessment_form = RiskAssessmentForm(request.POST,instance=risk_assessment,company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST,instance=risk_assessment,  prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(request.POST,instance=risk_assessment,  prefix='approval')
                risk_moniter_control_formset = RiskMoniterControlFormSet(request.POST,instance=risk_assessment,  prefix='monitor')

            except:
                return HttpResponseRedirect(reverse('company:risk_assessment_list'))
         
        elif 'client_risk_assessment_details_edit' in request.resolver_match.url_name:
            request_data = request.POST
            risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
            risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
            RiskAssessmentDetailFormSet = get_formset(RiskAssessment, RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
            risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST, instance=risk_assessment_instance, prefix='edit_detail', form_kwargs={'request': request})
            form_count = int(request_data.get('form_count')) - 1
            detail_form = risk_assessment_detail_formset.forms[form_count]
            if detail_form.is_valid():
                detail_form.save()
        
            edit_document_request = request.session.get('edit_document_request', False) 
            risk_documentation_approval = RiskDocumentationApproval.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
            risk_management_approval = RiskMoniterControl.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
            
            
            full_name = f"{request.user.first_name} {request.user.last_name}".strip()
            post_page_request = request.session.get('post_page_request')
            if post_page_request:
                edit_document_request = True
            if risk_documentation_approval and not edit_document_request == True:
                
                RiskDocumentationApproval.bells_manager.create(
                    risk_assessment=risk_assessment_instance,
                    completed_by=full_name
                )
                RiskMoniterControl.bells_manager.create(
                    risk_assessment = risk_assessment_instance
                )                
                edit_document_request = request.session['edit_document_request'] = True

            
            is_employee_request = request.session.get('is_employee_request')
            if is_employee_request == True:
                redirect_url = reverse('employee:client_employee_risk_assessment_add', kwargs={'client_id': client_id})
            else:
                post_page_request = request.session.get('post_page_request')
                if post_page_request == True:
                    redirect_url = reverse('employee:client_risk_assessment_add', kwargs={'client_id': client_id})
                else:
                    redirect_url = reverse(
                        'employee:client_risk_assessment_edit', 
                        kwargs={
                            'client_id': client_id, 
                            'risk_assessment_id': risk_assessment_instance_id
                        }
                    )

            query_string = 'risk_assessment=True'
            redirect_url_with_tab = f"{redirect_url}?{query_string}"
            return redirect(redirect_url_with_tab)

        else:

                RiskAssessmentDetailFormSet = get_formset(RiskAssessment,RiskAssessmentDetail, form=RiskAssessmentDetailForm, extra=1)
                RiskDocumentationApprovalFormSet = get_formset(RiskAssessment,RiskDocumentationApproval, form=RiskDocumentationApprovalForm, extra=1)
                RiskMoniterControlFormSet = get_formset(RiskAssessment,RiskMoniterControl, form=RiskMoniterControlForm, extra=1)
                client = Client.bells_manager.get(id=client_id)
                employee= request.user.employee
                risk_assessment_form = RiskAssessmentForm(request.POST,{'client': client, 'prepared_by': employee},company=company)
                risk_assessment_detail_formset = RiskAssessmentDetailFormSet(request.POST, queryset=RiskAssessmentDetail.bells_manager.none(), prefix='detail',form_kwargs={'request': request})
                risk_documentation_approval_formset = RiskDocumentationApprovalFormSet(request.POST, queryset=RiskDocumentationApproval.bells_manager.none(),  prefix='approval')
                risk_moniter_control_formset = RiskMoniterControlFormSet(request.POST, queryset=RiskMoniterControl.bells_manager.none(),  prefix='monitor')

        
        
        if 'client_risk_assessment_details_add' in request.resolver_match.url_name:
            
            if (risk_assessment_form.is_valid() and risk_assessment_detail_formset.is_valid()):
                risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                if risk_assessment_instance_id:
                    risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance.assessment_date=assessment_date
                else:
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance = risk_assessment_form.save(commit=False)
                    risk_assessment_instance.assessment_date=assessment_date
                risk_assessment_instance.save()
                    
                for form in risk_assessment_detail_formset:
                    risk_assessment_detail_instance = form.save(commit=False)
                    risk_assessment_detail_instance.risk_assessment = risk_assessment_instance
                    risk_assessment_detail_instance.save()
                    request.session['risk_assessment_instance_id'] = risk_assessment_instance.id
                    request.session['risk_assessment_detail_instance_id'] = risk_assessment_detail_instance.id
                   
                   
                risk_documentation_approval = RiskDocumentationApproval.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()
                full_name = f"{request.user.first_name} {request.user.last_name}".strip()

                if risk_documentation_approval:
                    risk_documentation_approval.completed_by =full_name
                    risk_documentation_approval.save()
                else:
                    RiskDocumentationApproval.bells_manager.create(
                        risk_assessment=risk_assessment_instance,
                        completed_by=full_name
                    )
                risk_management_approval = RiskMoniterControl.bells_manager.filter(
                    risk_assessment=risk_assessment_instance
                ).first()

                if risk_management_approval:
                    risk_management_approval.risk_assessment =risk_assessment_instance
                    risk_management_approval.save()
                else:
                    RiskMoniterControl.bells_manager.create(
                        risk_assessment=risk_assessment_instance,
                    )
            
            post_page_request = request.session['post_page_request'] = True        
            is_employee_request = request.session.get('is_employee_request')
            if is_employee_request == True:
                # redirect_url = reverse('employee:client_risk_assessment_add', kwargs={'client_id': client_id})
                redirect_url = reverse('employee:client_employee_risk_assessment_add', kwargs={'client_id': client_id})
            else:
                # redirect_url = reverse('employee:client_risk_assessment_add', kwargs={'client_id': client_id})
                redirect_url = reverse('employee:client_employee_risk_assessment_add', kwargs={'client_id': client_id})

            query_string = 'risk_assessment=True'
            redirect_url_with_tab = f"{redirect_url}?{query_string}"
            return redirect(redirect_url_with_tab)
        
        
        elif 'client_employee_risk_assessment_add' in request.resolver_match.url_name or 'client_risk_assessment_edit' in request.resolver_match.url_name:
            is_employee_request = request.session.get('is_employee_request')
            approval_in_post = any(key.startswith('approval-') for key in request.POST)
            monitor_in_post = any(key.startswith('monitor-') for key in request.POST)
            
            # if (risk_assessment_form.is_valid() and risk_documentation_approval_formset.is_valid() and risk_moniter_control_formset.is_valid() and not is_employee_request):
            if (risk_assessment_form.is_valid() and (not approval_in_post or risk_documentation_approval_formset.is_valid()) and (not monitor_in_post or risk_moniter_control_formset.is_valid())): 
                risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                risk_assessment_instance = RiskAssessment.bells_manager.filter(id=risk_assessment_instance_id).first()
                cleaned_data = risk_assessment_form.cleaned_data
                assessment_date = cleaned_data['assessment_date']
                risk_assessment_instance.assessment_date=assessment_date
                risk_assessment_instance.save()
                    
                risk_assessment_instance = RiskAssessment.bells_manager.get(id=risk_assessment_instance_id)
               
                
                for form in risk_documentation_approval_formset:
                    if not self.is_form_empty(form):
                        instance_id = form.cleaned_data.get('id')
                        
                        if instance_id:
                            risk_documentation_approval_instance = RiskDocumentationApproval.bells_manager.get(id=instance_id.id)
                            
                            risk_documentation_approval_instance.completed_by = form.cleaned_data.get('completed_by')
                            risk_documentation_approval_instance.authorized_by = form.cleaned_data.get('authorized_by')
                            risk_documentation_approval_instance.date = form.cleaned_data.get('date')
                            risk_documentation_approval_instance.save()
                        else:
                            form_instance = form.save(commit=False)
                            form_instance.risk_assessment = risk_assessment_instance
                            form_instance.save()

                
                for form in risk_moniter_control_formset:
                    if not self.is_form_empty(form):
                        instance_id = form.cleaned_data.get('id')

                        if instance_id:
                            risk_monitor_control_instance = RiskMoniterControl.bells_manager.get(id=instance_id.id)

                            risk_monitor_control_instance.reviewed_date = form.cleaned_data.get('reviewed_date')
                            risk_monitor_control_instance.reviewed_by = form.cleaned_data.get('reviewed_by')
                            risk_monitor_control_instance.authorized_by = form.cleaned_data.get('authorized_by')
                            risk_monitor_control_instance.save()
                        else:
                            form_instance = form.save(commit=False)
                            form_instance.risk_assessment = risk_assessment_instance
                            form_instance.save()

        
                # for form in risk_moniter_control_formset:
                #     risk_moniter_control_instance = form.save(commit=False)
                #     risk_moniter_control_instance.risk_assessment = risk_assessment_instance
                #     risk_moniter_control_instance.save()
                if risk_assessment_id:
                    messages.success(request, 'Risk assessment updated successfully.')
                else:
                    messages.success(request, 'Risk assessment created successfully.')
                
        
        
                redirect_url = reverse('employee:client_risk_assessment_list_view', kwargs={'client_id': client_id})
                
                redirect_url_with_tab = f"{redirect_url}"
                return redirect(redirect_url_with_tab)
            
            else:
                if risk_assessment_form.is_valid():
                    risk_assessment_instance_id = request.session.get('risk_assessment_instance_id',None)
                    risk_assessment_instance = RiskAssessment.bells_manager.filter(id=risk_assessment_instance_id).first()
                    cleaned_data = risk_assessment_form.cleaned_data
                    assessment_date = cleaned_data['assessment_date']
                    risk_assessment_instance.assessment_date=assessment_date
                    risk_assessment_instance.save()
                    messages.success(request, 'Risk assessment created successfully.')
                    is_employee_request = request.session.get('is_employee_request')
                    if is_employee_request == True:
                        redirect_url = reverse('employee:client_risk_assessment_list_view', kwargs={'client_id': client_id})
                    else:
                        redirect_url = reverse('employee:client_risk_assessment_list_view', kwargs={'client_id': client_id})

                        
                    query_string = 'risk_assessment=True'
                    redirect_url_with_tab = f"{redirect_url}?{query_string}"
                    return redirect(redirect_url_with_tab)
        else:
                return render(
                    request,
                    self.template_name,
                    {
                        'risk_assessment_form': risk_assessment_form,
                        'risk_assessment_detail_formset': risk_assessment_detail_formset,
                        'risk_documentation_approval_formset': risk_documentation_approval_formset,
                        'risk_moniter_control_formset': risk_moniter_control_formset,
                        'client_id':client_id
                    }
                )

    def handle_delete(self, request,client_id=None, risk_assessment_id=None,):
        risk_assessment = get_object_or_404(RiskAssessment, pk=risk_assessment_id)
        if risk_assessment:
            risk_assessment.is_deleted = True
            risk_assessment.save()
            messages.success(request, 'Risk assessment deleted successfully!')
        redirect_url = reverse('employee:client_client_profile_risk_assessment', kwargs={'client_id': client_id})
        redirect_url_with_tab = f"{redirect_url}"
        return redirect(redirect_url_with_tab)
    


@method_decorator(login_required, name='dispatch')
class ClientGetRiskArea(View):
    def get(self, request, *args, **kwargst):
        risk_type_id = request.GET.get('risk_type_id')
        risk_areas = RiskArea.objects.filter(risk_type_id=risk_type_id).values('id', 'name')
        return JsonResponse(list(risk_areas), safe=False)


def ClientDeleteRiskAssessmentDetail(request, client_id=None, risk_assessment_detail_id=None):
    risk_assessment_detail = get_object_or_404(RiskAssessmentDetail, pk=risk_assessment_detail_id)
    risk_assessment_obj=risk_assessment_detail.risk_assessment
    if risk_assessment_detail:
        risk_assessment_detail.is_deleted = True
        risk_assessment_detail.save()
        
        
        document_approval_obj = RiskDocumentationApproval.bells_manager.filter(risk_assessment=risk_assessment_obj).first()
        if document_approval_obj:
            document_approval_obj.is_deleted = True
            document_approval_obj.save()
        management_approval_obj = RiskMoniterControl.bells_manager.filter(risk_assessment=risk_assessment_obj).first()
        if management_approval_obj:
            management_approval_obj.is_deleted = True
            management_approval_obj.save()
    return JsonResponse({'message': 'Deleted successfully'})


def ClientRiskAssessmentDelete(request):
    risk_assessment_id = request.GET.get('risk_assessment_id')
    if risk_assessment_id:
        risk_assessment_obj = get_object_or_404(RiskAssessment, pk=risk_assessment_id)
        active_details = RiskAssessmentDetail.bells_manager.filter(
            risk_assessment=risk_assessment_obj
        )

        if not active_details.exists():
            risk_assessment_obj.is_deleted = True
            risk_assessment_obj.save()
            return JsonResponse({'status': 'success', 'message': 'Risk assessment successfully deleted.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Cannot delete risk assessment. Active details exist.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Risk assessment ID is missing.'})
    
    
@method_decorator(login_required, name='dispatch')
class ClientsProgressListView(View):
    template_name = "employee/profile/clients/client_profile.html"

    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        shifts_note = DailyShiftCaseNote.bells_manager.filter(
             company=company,client=client_id,shift__status="Completed").order_by('-created_at')
        client_obj = Client.bells_manager.filter(id=client_id).first()
        employee = request.user.employee
        clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name')).distinct()

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(shifts_note, items_per_page)
        try:
            shifts_note_obj = paginator.page(page)
        except PageNotAnInteger:
            shifts_note_obj = paginator.page(1)
        except EmptyPage:
            shifts_note_obj = paginator.page(paginator.num_pages)
        
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((shifts_note_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'shifts':shifts_note_obj,
            'client':client_obj,
            'clients':clients

        }
        return render(request, self.template_name, context)



    
@method_decorator(login_required, name='dispatch')
class ClientsProgressDetailView(View):
    template_name = "employee/profile/clients/client_profile.html"
    def get(self, request,shift_id=None,client_id=None, *args, **kwargs):
        company=request.user.employee.company
        shift = DailyShiftCaseNote.bells_manager.get(pk=shift_id,client=client_id)
        shift_form = DailyShiftNoteForm(
            instance=shift, company=company,request=request)
        client_obj = Client.bells_manager.filter(pk=client_id).first()
        employee_shift_instance = Shifts.bells_manager.filter(id=shift.shift.id,company=company).first()
        employee_shift_form = EmployeeShiftsForm(instance=employee_shift_instance,request=request)
        context = {
            'shift_form': shift_form,
            'client_id':client_id,
            'client':client_obj,
            'employee_shift_form':employee_shift_form
        }
        return render(request, self.template_name,context)


@method_decorator(login_required, name='dispatch')
class ClientProfileIncidentlistView(View):
    template_name = 'employee/profile/clients/client_profile.html'
    def get(self, request, client_id=None, *args, **kwargs):
        employee = request.user.employee
        company=employee.company
        incidents = Incident.bells_manager.filter(company = company,employee=employee,client=client_id,report_type='Incident')
        client_obj = Client.bells_manager.filter(id=client_id).first()
        clients = ClientEmployeeAssignment.get_clients_by_employee(employee_id=employee.id,company_id=company.id).order_by(Lower('person__first_name'))        

        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(incidents, items_per_page)
        try:
            incidents_obj = paginator.page(page)
        except PageNotAnInteger:
            incidents_obj = paginator.page(1)
        except EmptyPage:
            incidents_obj = paginator.page(paginator.num_pages)
        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((incidents_obj.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
            'client_id': client_id,
            'incidents':incidents_obj,
            'client':client_obj,
            'clients':clients

        }
        return render(request, self.template_name, context)
    
@method_decorator(login_required, name='dispatch')
class ClientIncidentDetailView(View):
    template_name = 'employee/profile/clients/client_profile.html'
    
    def get(self, request, incident_id=None, client_id=None, *args, **kwargs):
        context = {}
        employee = request.user.employee
        company = employee.company
        client_obj = Client.bells_manager.get(pk=client_id)
        
        specific_severity_description = None
        
        if incident_id and 'employee_client_profile_incident_detail' in request.resolver_match.url_name:
            incident = Incident.bells_manager.filter(pk=incident_id).first()
            if incident:
                incident_form = IncidentForm(
                    instance=incident, company=company, request=request)
                
                # Get the description for the specific severity level
                severity_choices = SEVERITY_LEVEL_CHOICES.get(incident.incident_severity_level, [])
                for value, description in severity_choices:
                    if value == incident.specific_severity_level:
                        specific_severity_description = description
                        break
                
                attachments_files = IncidentAttachment.bells_manager.filter(incident=incident)
                initial_data = [attachment for attachment in attachments_files]
                
                context.update({
                    'attachment_data': initial_data,
                    'incident_form': incident_form,
                    'client_id': client_id,
                    'single_incident_view': True,
                    'client': client_obj,
                    'specific_severity_description': specific_severity_description,
                })
        
        return render(request, self.template_name, context)
    
    
@method_decorator(login_required, name='dispatch')
class EmployeeProfileOperation(View):
    template_name = "employee/profile/employee-profile-operations.html"

    def get(self, request, employee_id=None, *args, **kwargs):
           
        personform = EmployeePersonForm()
        company = self.get_company(request)
        if employee_id and 'employee_profile_edit' in request.resolver_match.url_name:
            try:
                employee = Employee.bells_manager.filter(id=employee_id).first()
                personform = EmployeePersonForm(instance=employee.person,initial={'is_active': True})
                employee_formset = EmployeeProfileFormset(instance=employee.person, prefix="employee_f",initial=[{'company': company,'role':employee.role,'employment_type':employee.employment_type,'template':employee.template}])
            except Exception as e:
                return HttpResponseRedirect(reverse('employee:employee_profile'))
        else:
            return HttpResponseRedirect(reverse('employee:employee_profile'))
        return render(request, self.template_name, {'personform': personform, 'employee_formset': employee_formset,'employee_id':employee_id})

    def get_company(self, request):
        return request.user.employee.company
    
    def post(self, request, employee_id=None, *args, **kwargs):
 
        if employee_id and 'employee_profile_edit' in request.resolver_match.url_name:
            try:
                employee = Employee.bells_manager.filter(pk=employee_id).first()
                personform = EmployeePersonForm(request.POST,request.FILES, instance=employee.person,initial={'is_active': True})
                employee_formset = EmployeeProfileFormset(request.POST ,instance=employee.person, prefix="employee_f", initial=[{'company': self.get_company(request),'role':employee.role,'employment_type':employee.employment_type,'template':employee.template}])
            except:
                return HttpResponseRedirect(reverse('employee:employee_profile'))
        else:
            return HttpResponseRedirect(reverse('employee:employee_profile'))
   
        if personform.is_valid() and employee_formset.is_valid():
            try:
                person_instance=personform.save()
                employee_formset.instance = person_instance
                employee_formset.save()

                messages.success(request, 'Profile Updated successfully!')
                return HttpResponseRedirect(reverse('employee:employee_profile'))
            except Exception as e:
                print(request, f"An error occurred: {e}")
                return render(request, self.template_name, {'personform': personform, 'employee_formset': employee_formset})
        else:
            print("Form is not valid")
            return render(request, self.template_name, {'personform': personform, 'employee_formset': employee_formset})
    


@method_decorator(login_required, name='dispatch')
class EmployeeProfileDocuments(View):
    # template_name = "employee/profile/employee-profile-operations.html"
    template_name = "employee/profile/my-profile.html"

    def get(self, request, employee_id=None,document_id=None, *args, **kwargs):
           
        employee = request.user.employee
        company = self.get_company(request)
     
        #id and checks
        id_checks_predefined_names = ["AUSTRALIAN DRIVER LICENSE", "WORKING WITH CHILDREN CHECK OR (WWVP IN OTHER STATES)", "NATIONAL POLICE CHECK",
                            "INTERNATIONAL POLICE CHECK", "VEVO CHECK", "TRAVEL PASSPORT", "AUSTRALIAN BIRTH CERTIFICATE", "NDIS WORKER SCREENING CHECK"]

        existing_documents = IDsAndChecksDocuments.bells_manager.filter(employee=employee)
        id_checks_initial_data = []
        for name in id_checks_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                id_checks_initial_data.append({
                    'id': existing_document.id,
                    'employee': existing_document.employee.id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status':existing_document.status
                })
            else:
                id_checks_initial_data.append({
                    'employee': employee.id,
                    'company': company.id,
                    'name': name,
                })

        IDsAndChecksDocumentsFormSet = formset_factory(IDsAndChecksDocumentsForm, extra=0)
        idschecksformset = IDsAndChecksDocumentsFormSet(initial=id_checks_initial_data, prefix='idschecks')
        
        # #qualification documents
        qualification_predefined_names = ["CERTIFICATE IN DISABILITY OR AGED CARE", "NDIS WORKER ORIENTATION MODULE/PROGRAM",
                                      "INFECTION CONTROL TRAINING"]
        
        existing_documents = QualificationDocuments.bells_manager.filter(employee=employee)
        qualification_initial_data = []
        for name in qualification_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                qualification_initial_data.append({
                    'id': existing_document.id,
                    'employee': existing_document.employee.id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status':existing_document.status

                })
            else:
                qualification_initial_data.append({
                    'employee': employee.id,
                    'company': company.id,
                    'name': name,
                })
        qualificationDocumentsFormSet = formset_factory(QualificationDocumentsForm, extra=0)
        qualificationFormSet = qualificationDocumentsFormSet(initial=qualification_initial_data, prefix='qualification')
        
        # #Other documents
        other_predefined_names = ["CAR REGISTRATION", "COMPREHENSIVE CAR INSURANCE",
                                      "MANUAL HANDLING TRAINING","ASSIST CLIENTS WITH MEDICATION","FIRST AID CERTIFICATE"]
        
        existing_documents = OtherDocuments.bells_manager.filter(employee=employee)
        other_initial_data = []
        for name in other_predefined_names[:8]:
            existing_document = existing_documents.filter(name=name).first()
            if existing_document:
                other_initial_data.append({
                    'id': existing_document.id,
                    'employee': existing_document.employee.id,
                    'company': company.id,
                    'name': existing_document.name,
                    'expiry_date': existing_document.expiry_date,
                    'file': existing_document.file,
                    'status':existing_document.status

                })
            else:
                other_initial_data.append({
                    'employee': employee.id,
                    'company': company.id,
                    'name': name,
                })
                
        OtherDocumentsFormSet = formset_factory(OtherDocumentsForm, extra=0)
        otherFormSet = OtherDocumentsFormSet(initial=other_initial_data, prefix='other')
        profile_details =  Employee.bells_manager.filter(id=employee_id).first()



        return render(request, self.template_name, {
            'profile': profile_details,
            'idschecksformset': idschecksformset,
            'qualificationFormSet': qualificationFormSet,
            'otherFormSet': otherFormSet,
            'employee_id': employee.id
        })
    def get_company(self, request):
        return request.user.employee.company
    
    def post(self, request, employee_id=None, document_id=None, *args, **kwargs):
        
        if 'delete-employee_document' in request.resolver_match.url_name:
            return self.handle_delete(request,employee_id, document_id)
        employee = request.user.employee
        company = self.get_company(request)
        
        #ids and checks
        id_checks_predefined_names = ["AUSTRALIAN DRIVER LICENSE", "WORKING WITH CHILDREN CHECK OR (WWVP IN OTHER STATES)", "NATIONAL POLICE CHECK",
                            "INTERNATIONAL POLICE CHECK", "VEVO CHECK", "TRAVEL PASSPORT", "AUSTRALIAN BIRTH CERTIFICATE", "NDIS WORKER SCREENING CHECK"]
        IDsAndChecksDocumentsFormSet = formset_factory(IDsAndChecksDocumentsForm, extra=0)
        id_checks_initial_data = [{'employee': employee.id, 'company': company, 'name': name} for name in id_checks_predefined_names[:8]]
    
        idschecksformset = IDsAndChecksDocumentsFormSet(request.POST, request.FILES,initial=id_checks_initial_data, prefix='idschecks')
        
        #qualification 
        qualification_predefined_names = ["CERTIFICATE IN DISABILITY OR AGED CARE", "NDIS WORKER ORIENTATION MODULE/PROGRAM",
                                      "INFECTION CONTROL TRAINING"]
        qualificationDocumentsFormSet = formset_factory(QualificationDocumentsForm, extra=0)
        qualification_initial_data = [{'employee': employee.id, 'company': company, 'name': name} for name in qualification_predefined_names[:3]]        
        qualificationFormSet = qualificationDocumentsFormSet(request.POST, request.FILES, initial=qualification_initial_data, prefix='qualification')
        
        #other 
        other_predefined_names = ["CAR REGISTRATION", "COMPREHENSIVE CAR INSURANCE",
                                      "MANUAL HANDLING TRAINING","ASSIST CLIENTS WITH MEDICATION","FIRST AID CERTIFICATE"]
        OtherDocumentsFormSet = formset_factory(OtherDocumentsForm, extra=0)
        other_initial_data = [{'employee': employee.id, 'company': company, 'name': name} for name in other_predefined_names[:5]]

        otherFormSet = OtherDocumentsFormSet(request.POST, request.FILES,initial=other_initial_data, prefix='other')
        if idschecksformset.is_valid() and qualificationFormSet.is_valid() and otherFormSet.is_valid():

            document_added = False
            
            for form in idschecksformset:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = IDsAndChecksDocuments.bells_manager.filter(name=name, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True

            for form in qualificationFormSet:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = QualificationDocuments.bells_manager.filter(name=name, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True
            
            for form in otherFormSet:
                if form.cleaned_data.get('expiry_date') or form.cleaned_data.get('file'):

                    name = form.cleaned_data.get('name')
                    expiry_date = form.cleaned_data.get('expiry_date')
                    file = form.cleaned_data.get('file')
                    
                    existing_document = OtherDocuments.bells_manager.filter(name=name, employee=form.cleaned_data.get('employee')).first()

                    if existing_document:
                        existing_document.expiry_date = expiry_date
                        if file:
                            existing_document.file = file
                        else:
                            existing_document.file = existing_document.file
                        existing_document.save()
                        document_added = True

                    else:
                        form.save()
                        document_added = True


            
            if document_added:
                messages.success(request, 'Document added successfully!')
            else:
                messages.info(request, 'No document added.')            
            return HttpResponseRedirect(reverse('employee:employee_documents'))
        else:
            messages.error(request, 'The file must be a PDF, JPG, PNG, HEIC, or JPEG.')
            redirect_url = reverse('employee:employee_document', kwargs={'employee_id': employee_id})            
            redirect_url_with_tab = f"{redirect_url}"
            return redirect(redirect_url_with_tab)
              

    def handle_delete(self, request, employee_id,document_id):
        IDsAndChecksDocuments_obj = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        QualificationDocuments_obj = QualificationDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        OtherDocuments_obj=OtherDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
        
        if IDsAndChecksDocuments_obj:
            IDsAndChecksDocuments_obj.is_deleted = True
            IDsAndChecksDocuments_obj.save()
            messages.success(request, 'IDandChecks document deleted successfully!')
        
        elif QualificationDocuments_obj:
            QualificationDocuments_obj.is_deleted = True
            QualificationDocuments_obj.save()
            messages.success(request, 'Qualification document deleted successfully!')
        
        elif OtherDocuments_obj:
            OtherDocuments_obj.is_deleted = True
            OtherDocuments_obj.save()
            messages.success(request, 'Other document document deleted successfully!')
        else:
            messages.success(request, 'No document found!')
            
        return HttpResponseRedirect(reverse('employee:employee_documents'))



@login_required
def EmployeeProfileDocumentDelete(request,employee_id, document_id):
    outer_delete_request = request.POST.get('employee_profile')
    IDsAndChecksDocuments_obj = IDsAndChecksDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    QualificationDocuments_obj = QualificationDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    OtherDocuments_obj=OtherDocuments.bells_manager.filter(employee=employee_id,id=document_id ).first()
    
    if IDsAndChecksDocuments_obj:
        IDsAndChecksDocuments_obj.is_deleted = True
        IDsAndChecksDocuments_obj.save()
        messages.success(request, 'IDandChecks document deleted successfully!')
    
    elif QualificationDocuments_obj:
        QualificationDocuments_obj.is_deleted = True
        QualificationDocuments_obj.save()
        messages.success(request, 'Qualification document deleted successfully!')
    
    elif OtherDocuments_obj:
        OtherDocuments_obj.is_deleted = True
        OtherDocuments_obj.save()
        messages.success(request, 'Other document deleted successfully!')
    else:
        messages.success(request, 'No document found!')
    
    if outer_delete_request:
        return redirect('employee:employee_documents')
    return JsonResponse({'message': 'Deleted successfully'}, status=200)
    # return JsonResponse({'success':True}, status=200)



def user_punch_in_view(request):
    shift_id = request.POST.get('shift_id')
    # shift_form = DailyShiftNoteForm(initial={
    #                                 'client':shift_client.id,'shift':shift_id,'employee': employee, 'company': company, 'sno': company.next_daily_shift_sno()}, company=company, request=request,)
    if shift_id:
        employee = request.user.employee
        company = employee.company
        shift_client =  None
        current_time = timezone.now().replace(second=0, microsecond=0)

        shift = Shifts.bells_manager.filter(id=shift_id,company=company).first()
        if shift:
            try:
                if not DailyShiftCaseNote.bells_manager.filter(shift=shift).exists():
                    DailyShiftCaseNote.bells_manager.get_or_create(
                        shift=shift,
                        employee=employee,
                        company=company,
                        client=shift.client,
                        sno =company.next_daily_shift_sno(),
                        start_date_time=current_time,
                    )
                    shift.status = 'Ongoing'
                    shift.save()
                return JsonResponse({'success': True, 'message': 'Progress note created successfully!'},status=200)
            except Exception as e:
                return JsonResponse({'success': False, 'message': 'An error occurred while creating the progress note.'}, status=500)
    else:
        return JsonResponse({'success':False}, status=400)
    

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_terms_and_conditions_all',
                                     'company_admin.view_privacy_policy_all',]), name='dispatch')
class CompanyPoliciesDocumentsView(View):
    template_name = 'employee/company_policies/documents.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_terms_and_conditions_all',]), name='dispatch')

class EmployeeTermsAndConditionsOperationsView(View):
    template_name = 'employee/company_policies/terms_and_conditions_acknowledgement.html'

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        terms_and_conditions = CompanyTermsAndConditionsPolicy.objects.filter(
            company=employee.company,
            type='terms_and_conditions'
        ).first()

        already_acknowledged = EmployeePolicyAcknowledgment.bells_manager.filter(policy=terms_and_conditions,employee=employee , is_acknowledged= True)

        if terms_and_conditions:
            acknowledgement_form = EmployeeAcknowledgementForm(initial={
                'policy': terms_and_conditions,
                'employee': employee,
            })
        else:
            acknowledgement_form = EmployeeAcknowledgementForm()

        context = {
            'terms_and_conditions': terms_and_conditions,
            'form': acknowledgement_form,
            'already_acknowledged':already_acknowledged
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = EmployeeAcknowledgementForm(request.POST)
        policy = request.POST.get('policy')
        employee = request.user.employee
        already_acknowledged = EmployeePolicyAcknowledgment.bells_manager.filter(policy=policy,employee=employee , is_acknowledged= True)

        if already_acknowledged :
            messages.success(request, "Already acknowledged !!!!!")
            return redirect('employee:employee_company_documents')       
        else :
            if form.is_valid():
                form.save()
                messages.success(request, "Acknowledged Successfully | SHOW_MODAL")
                return redirect('employee:employee_terms_and_conditions')
            else:
                return render(request, self.template_name, {'form': form})

@method_decorator(login_required, name='dispatch')
@method_decorator(check_permissions(['company_admin.view_privacy_policy_all',]), name='dispatch')

class EmployeePrivacyPolicyOperationsView(View):
    template_name = 'employee/company_policies/privacy_policy_acknowlegdement.html'

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        company_privacy_policy = CompanyTermsAndConditionsPolicy.objects.filter(
            company=employee.company,
            type='privacy_policy'
        ).first()

        already_acknowledged = EmployeePolicyAcknowledgment.bells_manager.filter(policy=company_privacy_policy,employee=employee , is_acknowledged= True)

        if company_privacy_policy:
            acknowledgement_form = EmployeeAcknowledgementForm(initial={
                'policy': company_privacy_policy,
                'employee': employee,
            })
        else:
            acknowledgement_form = EmployeeAcknowledgementForm()

        context = {
            'privacy_policy': company_privacy_policy,
            'form': acknowledgement_form,
            'already_acknowledged':already_acknowledged
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = EmployeeAcknowledgementForm(request.POST)
        policy = request.POST.get('policy')
        employee = request.user.employee
        already_acknowledged = EmployeePolicyAcknowledgment.bells_manager.filter(policy=policy,employee=employee , is_acknowledged= True)

        if already_acknowledged :
            messages.success(request, "Already acknowledged !!!!!")
            return redirect('employee:employee_company_documents')       
        else :
            if form.is_valid():
                form.save()
                messages.success(request, "Acknowledged Successfully | SHOW_MODAL")
                return redirect('employee:employee_privacy_policy')
            else:
                return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class TagEmployee(View):
    template_name = 'employee/tag-employee.html'

    def get(self, request, *args, **kwargs):
        try:
            incident_id = request.session.get('incident_id', None) if request.session.get('incident_id', None) else request.GET.get('incident_id')
            current_employee_id = request.session.get('employee_id', None)
            current_client_id = request.session.get('client_id', None) if request.session.get('client_id', None)  else request.GET.get('client_id')
            company = request.user.employee.company
            login_user = request.user.employee
            
            #collecting is any person involved for a incident
            incident_obj = Incident.bells_manager.get(id=incident_id)
            
            if request.resolver_match.url_name == 'employee_tag_employee_view':
                #tagged employee list for tagged incidents
                tagged_employees_for_current_employee_and_client = IncidentTaggedEmployee.bells_manager.filter(
                        incident_id=incident_id,
                        is_removed =False,
                        tagged_to_client_id=current_client_id
                    )
                
                page = request.GET.get('page', 1)
                items_per_page=50
                pagination_result = paginate_query(tagged_employees_for_current_employee_and_client, page, items_per_page)

                context = {
                    'employees_queryset': pagination_result['paginated_data'],
                    'start_entry': pagination_result['start_entry'],
                    'end_entry': pagination_result['end_entry'],
                    'total_entries': pagination_result['total_entries'],
                    'incident_obj':incident_obj,
                    'incident_id': incident_id,
                    'employee_id': current_employee_id,
                    'client_id': current_client_id,
                }
                return render(request, self.template_name,context)
            
            else:
                #showing corresponding emloyees to client
                employees = ClientEmployeeAssignment.get_employees_by_client(client_id=current_client_id,company_id=company.id).exclude(id=current_employee_id).distinct() 
                
                #listing tagged employee in list
                tagged_employees_for_current_employee_and_client=IncidentTaggedEmployee.bells_manager.filter(
                                incident_id=incident_id,
                                tagged_to_client_id = current_client_id,
                                tagged_to_employee_id=current_employee_id,
                                is_removed = False
                                )
                
                #if client and employee changed then setting previous records is_removed true
                if not tagged_employees_for_current_employee_and_client:
                    previous_tagged_incident_record = IncidentTaggedEmployee.bells_manager.filter(
                                incident_id=incident_id,
                                is_removed = False
                    )
                    if previous_tagged_incident_record.exists():
                        previous_tagged_incident_record.update(is_removed=True,untagged_by=login_user)
                        
                
                #tagged employee ids to mark them checked
                tagged_employee_ids_for_current_employee_and_client = list(tagged_employees_for_current_employee_and_client.values_list('tagged_employee_id', flat=True))
                
                incident_obj = get_object_or_404(Incident.bells_manager, id=incident_id)

                page = request.GET.get('page', 1)
                items_per_page = 50
                pagination_result = paginate_query(tagged_employees_for_current_employee_and_client, page, items_per_page)

                context = {
                
                    'employees': employees,
                    'start_entry': pagination_result['start_entry'],
                    'end_entry': pagination_result['end_entry'],
                    'total_entries': pagination_result['total_entries'],
                    'tagged_employees': list(tagged_employee_ids_for_current_employee_and_client),
                    'employees_queryset':pagination_result['paginated_data'],
                    'incident_obj':incident_obj,
                    'incident_id': incident_id,
                    'employee_id': current_employee_id,
                    'client_id': current_client_id,
                }
                return render(request, self.template_name,context)
        except Exception as e:
            print(f'Exception error: {e}')
            return redirect('employee:incident_list')
        
    def post(self, request, *args, **kwargs):
        try:
            incident_id = request.session.get('incident_id', None)
            current_incident_employee_id = request.session.get('employee_id', None)
            current_incident_client_id = request.session.get('client_id', None)
            
            login_user = request.user.employee
            selected_employees = request.POST.get('selected_employees', '').split(',')
            unselected_employees = request.POST.get('unselected_employees', '').split(',')
            
            incident_obj = Incident.bells_manager.filter(id = incident_id).first()

            if incident_obj:
                if selected_employees and '' not in selected_employees:
                    for employee_id in selected_employees:
                        existing_incident_tagged_employee = IncidentTaggedEmployee.bells_manager.filter(
                            incident=incident_obj,
                            tagged_to_client_id = current_incident_client_id,
                            tagged_employee_id=employee_id,
                            is_removed=False
                            )
                        if existing_incident_tagged_employee:
                            existing_incident_tagged_employee.update(is_removed=False)
                        else:
                            IncidentTaggedEmployee.bells_manager.create(
                                incident=incident_obj,
                                tagged_employee_id=employee_id,  
                                tagged_by=login_user,
                                tagged_to_employee_id=current_incident_employee_id,
                                tagged_to_client_id=current_incident_client_id
                            )   
                if unselected_employees and '' not in unselected_employees:
                    for employee_id in unselected_employees:
                        incident_queryset = IncidentTaggedEmployee.bells_manager.filter(
                            incident=incident_obj,
                            tagged_employee_id=employee_id,
                            tagged_to_client_id = current_incident_client_id,
                            is_removed=False,
                            
                            )
                        incident_queryset.update(is_removed=True,untagged_by = login_user)
                return redirect('employee:employee_tag_employee')
            else:
                print('Incident not found with incident id {incident_id}')
                return redirect('employee:incident_list')
        except Exception as e:
            print(f'Exception error: {e}')
            return redirect('employee:incident_list')

            
        




@method_decorator(login_required, name='dispatch')
class TaggedIncidentsView(View):
    template_name = 'employee/tagged-incidents.html'

    def get(self, request, *args, **kwargs):
        employee = request.user.employee
        tagged_incidents_id = IncidentTaggedEmployee.bells_manager.filter(tagged_employee=employee,is_removed=False).values_list('incident', flat=True)
        incidents = Incident.bells_manager.filter(id__in=tagged_incidents_id)
        # Pagination
        items_per_page = 50
        page = request.GET.get('page', 1)
        paginator = Paginator(incidents, items_per_page)
        try:
            incidents_page = paginator.page(page)
        except PageNotAnInteger:
            incidents_page = paginator.page(1)
        except EmptyPage:
            incidents_page = paginator.page(paginator.num_pages)

        total_entries = paginator.count
        if total_entries > 0:
            start_entry = ((incidents_page.number - 1) * items_per_page) + 1
            end_entry = min(start_entry + items_per_page - 1, total_entries)
        else:
            start_entry = 0
            end_entry = 0

        context = {
            'employee': employee,
            'incidents': incidents_page,  
            'start_entry': start_entry,
            'end_entry': end_entry,
            'total_entries': total_entries,
        }
        return render(request, self.template_name, context)
    

    