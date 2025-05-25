from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import login
from .forms import LoginForm, PersonForm, PasswordResttingForm, ForgotPasswordSetForm
from django.db import IntegrityError
from .models import Company, Client, Employee, Person
from bellscrm_admin.models import CompanyDetail
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.mail import send_mail
from userauth.forms import ChangePasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.core.mail import message, BadHeaderError, EmailMessage
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from  userauth.utils import *
from django.contrib.auth.models import Group
from company_admin.models import CompanyGroup
from utils.helper import assign_permission_to_group

import logging
logger = logging.getLogger('watchtower')


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


    
class LoginView(View):
    template_name = 'userauth/login.html'
    login_form = LoginForm

    def get_company_obj(self, request):
        company_code = request.get_host().split('.')[0]
        return Company.bells_manager.filter(company_code__iexact=company_code).first()

    def get(self, request):
        company_obj = self.get_company_obj(request)

        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("company:dashboard"))
        login_form = self.login_form()
        return render(request, self.template_name, {'form': login_form, 'company_obj': company_obj})

    def post(self, request):
        company_obj = self.get_company_obj(request)
        login_form = self.login_form(data=request.POST)
        msg = "Invalid Credentials!"

        if login_form.is_valid():
            email = login_form.cleaned_data['email']
            password = login_form.cleaned_data['password']
            # if company_obj is not None:
            #     employee_company_obj = Employee.objects.filter(company__company_code__iexact=company_obj.company_code, person__email=email).first() 
            #     if employee_company_obj:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('company:dashboard')
        return render(request, self.template_name, {'form': login_form, 'msg': msg, 'company_obj': company_obj})
    

class RegisterView(View):
    template_name = 'userauth/sign_up.html'
    template_name2 = 'userauth/page-404.html'

    def get(self, request):
        company_code = request.get_host().split('.')[0]
        company_obj = Company.bells_manager.filter(company_code__iexact=company_code)
        if company_obj.count() > 0:
            form = PersonForm()
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, self.template_name2)

    def post(self, request):
        company_code = request.get_host().split('.')[0]
        company_obj = Company.bells_manager.filter(company_code__iexact=company_code)
        if company_obj.count() > 0:
            form = PersonForm(request.POST)
            if form.is_valid():
                try:
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password'])
                    user.is_active = False
                    user.save()
                    company_obj = company_obj.first()
                    employee_obj = Employee.objects.create(company=company_obj,person=user)
                    if employee_obj:
                        template_name = f"{company_obj.company_code.strip().lower()} - {user.first_name}-{user.last_name}-{employee_obj.id} - user"
                        template, created = Group.objects.get_or_create(name=template_name)
                        if created:
                            permission_mapper_role = 'employee'
                            print(f"Created new user template '{template_name}' for employee '{employee_obj.person.first_name}', id '{employee_obj.id}'")
                            CompanyGroup.objects.get_or_create(group=template, company=company_obj)
                            print(f"Created CompanyGroup for company '{company_obj.company_code}' and template '{template}'")
                            #assigning permission to group and user
                            assign_permission_to_group(company_obj, template, permission_mapper_role,employee_obj)
                            employee_obj.template = template
                            employee_obj.save()

                    else:
                        print(f"Updated employee {employee_obj.id} with existing template '{template_name}'")
                        
                    # registration email
                    fullname = f'{user.first_name} {user.last_name}'
                    user_email = user.email
                    company_admin_email = company_obj.email_for_alerts 
                    employee_email_template = 'userauth/email/registration-mail-to-user.html'
                    admin_email_template ='userauth/email/registration-mail-to-admin.html'
                    registration_email.apply_async(args=[fullname,user_email,company_admin_email,
                                    employee_email_template,admin_email_template])
                    return render(request, 'userauth/Thank_you.html')
                except IntegrityError:
                    form.add_error('email', 'A user with this email already exists.')
                    return render(request, self.template_name, {'form': form})
            else:
                return render(request, self.template_name, {'form': form})
        else:
            return render(request, self.template_name2)


    
@method_decorator(login_required,name='get')
class Logout(View):
    def get(self,request,*args, **kwargs):
        if request.user.is_authenticated:
            # company_code = request.user.employee.company.company_code
            logout(request)
            request.session.flush()
            return redirect('user_auth:login')
            # return redirect('user_auth:login', company_code=company_code)
        else:
            return HttpResponseRedirect(reverse("user_auth:login"))


class ForgetPasswordViewView(View):
    template_name = 'userauth/forget_password.html'

    def get(self, request, *args, **kwargs):
        company_code = request.get_host().split('.')[0]
        company_obj = Company.bells_manager.filter(company_code__iexact=company_code)
        return render(request, self.template_name)





class RestPasswordEmailView(View):
    template_name = 'userauth/forget_password.html'

    def get_company_obj(self, request):
        company_code = request.get_host().split('.')[0]
        return Company.bells_manager.filter(company_code__iexact=company_code).first()

    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("company:dashboard"))
        else:
            form = PasswordResttingForm()
            return render(request, self.template_name, {'reset_form': form})

    def post(self, request, *args, **kwargs):
        company_obj = self.get_company_obj(request)
        form = PasswordResttingForm(request.POST)
        context = {'reset_form': form}

        if form.is_valid():
            email = form.cleaned_data.get("email")
            if company_obj:
                employee_company_obj = Employee.objects.filter(
                    company__company_code__iexact=company_obj.company_code, person__email=email
                ).first()

                if employee_company_obj:
                    try:
                        person = Person.objects.get(email=email)
                        subject = "Account Password Reset"
                        status = password_reset_email(
                            request, person, subject, 'userauth/email/password_reset_email.html'
                        )

                        if status:
                            msg = "The password reset instructions have been sent to your email. Please check your inbox and follow the provided link to reset your password"
                        else:
                            msg = "Please try again later"

                        return render(request, self.template_name, {'reset_form': PasswordResttingForm(), 'message': msg if status else None, 'error_message': msg if not status else None})
                    except Person.DoesNotExist:
                        pass

                msg = "The password reset instructions have been sent to your email. Please check your inbox and follow the provided link to reset your password"
                return render(request, self.template_name, {'reset_form': PasswordResttingForm(), 'message': msg})
            else:
                msg = "The password reset instructions have been sent to your email. Please check your inbox and follow the provided link to reset your password"
                return render(request, self.template_name, {'reset_form': PasswordResttingForm(), 'message': msg})
        else:
            return render(request, self.template_name, context)
        
@method_decorator(login_required, name='dispatch')     
class ChangePasswordView(LoginRequiredMixin, View):
    template_name = "company_admin/profile/change_password.html"

    def get(self, request, *args, **kwargs):
        passwordform = ChangePasswordForm(user = request.user)
        return render(request, self.template_name, {'changepasswordform': passwordform})

    def post(self, request, *args, **kwargs):
        changepasswordform = ChangePasswordForm(request.POST, user=request.user)
        if changepasswordform.is_valid():
            user = request.user
            new_password = changepasswordform.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password Updated successfully!')
            return redirect('user_auth:change_password')
        else:
            return render(request, self.template_name, {'changepasswordform': changepasswordform})




class NewPasswordView(PasswordResetConfirmView):
    """This is set password view."""
    form_class = ForgotPasswordSetForm
    success_url = reverse_lazy('user_auth:landing_website_password_reset_complete')

    def form_invalid(self, form):
        
        additional_context = {
            'form_errors' : form.errors,

        }
        context = self.get_context_data(form=form)
        context.update(additional_context)
        return self.render_to_response(context)


            

class RestPasswordDoneView(PasswordContextMixin, View):
    
    template_name = "userauth/form/password_reset_done.html"
    def get(self, request):
        context = {}
        return render(self.request, self.template_name, context)



def page_not_found_404_view(request, exception):
    context = {}
    context['current_page'] = '404'
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("company:dashboard"))
    else:
        return render(request, "userauth/page-404.html", context, status=404)
    


def custom_500_view(request, exception):
    context = {}
    context['current_page'] = '500'
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("company:dashboard"))
    else:
        return render(request, "userauth/page-404.html", context, status=500)