from django.template.loader import  get_template
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from celery import shared_task
from django.db import models

@shared_task(bind=True)
def registration_email(self,fullname,user_email,company_admin_email,
                                    employee_email_template,admin_email_template):
    emp_email_subject="Registration Confirmation"
    admin_email_subject = "New User Registration"
    try:
        employee_context = {
            "full_name": fullname,
        }
        fromEmail = settings.EMAIL_HOST_USER
        employee_html_msg = get_template(employee_email_template).render(employee_context)
        employee_msg = EmailMessage(emp_email_subject, employee_html_msg, fromEmail, [user_email])
        employee_msg.content_subtype = "html"
        employee_msg.send()
        
        admin_context = {
            "full_name": fullname,
            "employee_email":user_email
        }
        admin_html_msg = get_template(admin_email_template).render(admin_context)
        admin_msg = EmailMessage(admin_email_subject, admin_html_msg, fromEmail, [company_admin_email])
        admin_msg.content_subtype = "html"
        admin_msg.send()
        return True
    except Exception as ex:
        return False


def password_reset_email(request, user, subject, template_name):
    protocol = 'http' if not request.is_secure() else 'https'

    try:
        ctx = {
            "email": user.email,
            "domain": request.get_host(),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": protocol,
            
        }
        html_msg = get_template(template_name).render(ctx)
        fromEmail = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, fromEmail, [user.email])
        msg.content_subtype = "html"
        msg.send()
        return True
    except Exception as ex:
        return False
    
    

class BellsManager(models.Manager):
    """Custom manager to return only active objects."""
    # use_for_related_fields = True

    def get_queryset(self):
        """Return only active objects."""
        return super().get_queryset().filter(is_deleted=False)


def has_user_permission(user, permission_codename):
    """
    Checks if the given user has the specified permission.

    Args:
        user (User): The user to check the permission for.
        permission_codename (str): The codename of the permission to check.

    Returns:
        bool: True if the user has the permission, False otherwise.
    """
    return user.has_perm(permission_codename)
