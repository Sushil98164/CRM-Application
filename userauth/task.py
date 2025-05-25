
from celery import shared_task
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string, get_template
from django.utils.encoding import force_bytes
from django.core.mail import message, send_mail, BadHeaderError, EmailMessage
from django.conf import settings



@shared_task(bind=True)
def celery_send_email_message(self,email, domain, uid, user, token, protocol, subject, template_nam):
    try:
        ctx = {
            "email": email,
            "domain": domain,
            'uid': uid,
            "user": user,
            "token": token,
            "protocol": protocol,
        }
        html_msg = get_template(template_nam).render(ctx)
        from_email = settings.EMAIL_HOST_USER
        msg = EmailMessage(subject, html_msg, from_email, [email])
        msg.content_subtype = "html"
        msg.send()
        return True
    except Exception as ex:
        return False
