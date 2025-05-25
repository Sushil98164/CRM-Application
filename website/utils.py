from django.conf import settings

from django.template.loader import  get_template
from django.core.mail import EmailMessage
from django.conf import settings

def send_contact_email(name,subject,message,email,contact_template):
    email_subject='New Contact Form Submission'
    try:
        contact_context = {
            "name": name,
            "email":email,
            "message":message,
            "subject":subject
        }
        fromEmail = email
        to = settings.EMAIL_HOST_USER
        contact_html_msg = get_template(contact_template).render(contact_context)
        contact_html_msg = EmailMessage(email_subject, contact_html_msg, fromEmail, [to])
        contact_html_msg.content_subtype = "html"
        contact_html_msg.send()
        
        return True
    except Exception as ex:
        return False
