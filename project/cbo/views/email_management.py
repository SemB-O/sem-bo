from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib import messages
from django.conf import settings
from django.views import View
from django.shortcuts import redirect


class EmailManagementView(View):
    def send_email(subject, template_name, context, to_email, file_path=None, file_name=None):
        message = render_to_string(template_name, context)
        email = EmailMessage(subject, message, to=[to_email])
        email.content_subtype = 'html'

        if file_path:
            with open(file_path, 'rb') as pdf_file:
                email.attach(f'{file_name}.pdf', pdf_file.read(), 'application/pdf')

        if email.send():
            return True
        else:
            return False