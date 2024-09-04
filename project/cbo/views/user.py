import json
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext
from django.utils.encoding import force_bytes, force_str
from cbo.tokens import account_activation_token
from django.conf import settings
from django.urls import reverse_lazy
from ..forms import EmailAuthenticationForm, UserRegisterForm, PasswordResetEmailForm, SetPasswordForm
from ..models import Occupation, Plan, FavoriteFolder, User


class LoginView(LoginView):
    template_name = 'front/login.html'
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        return HttpResponseRedirect(reverse_lazy('home'))

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, 'Credenciais inválidas. Tente novamente.')
        return HttpResponseRedirect(reverse_lazy('login'))


class RegisterView(View):
    template_name = 'create/register_user.html'

    def get(self, request, selected_plan, *args, **kwargs):
        form = UserRegisterForm(initial={'plan': selected_plan}, use_required_attribute=False)
        occupations = Occupation.objects.all()

        plans = Plan.objects.all()
        plans_json = json.dumps(list(plans.values('id', 'name', 'max_occupations', 'description')))

        context = {
            'form': form,
            'occupations': occupations,
            'selected_plan': request.GET.get('selected_plan'),
            'plans_json': plans_json,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = UserRegisterForm(request.POST, use_required_attribute=False)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            selected_occupations = form.cleaned_data['occupation']
            for occupation in selected_occupations:
                user.occupations.add(occupation)
            user.save()

            default_folder, _ = FavoriteFolder.objects.get_or_create(
                user=user,
                name="Geral",
                description="Meus Favoritos"
            )

            self.activateEmail(request, user, form.cleaned_data.get('email'))

            return redirect('login')
        else:
            return render(request, self.template_name, {'form': form})
        
    def activateEmail(self, request, user, to_email):
        mail_subject = "Ativação da sua conta Sem B.O"
        message = render_to_string('email/email_verification.html', {
            'user': user.first_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': settings.DOMAIN,
        })
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.content_subtype = 'html' 
        if email.send():
            messages.success(request, f'Olá {user.first_name}, enviamos um email para {to_email}, por favor verifique-o para validar seu cadastro')
        else:
            messages.error(request, f'Tivemos um problema ao enviar a validação para seu email ({to_email}), por favor cheque se você digitou seu email corretamente!')


class LogoutView(LogoutView):
    next_page = reverse_lazy('login')


class PasswordResetView(View):
    template_name = 'password_reset/email_password_reset.html'

    def get(self, request):
        form = PasswordResetEmailForm()
        return render(
            request=request,
            template_name=self.template_name,
            context={"form": form}
        )

    def post(self, request):
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associetad_user = get_user_model().objects.filter(Q(email=user_email)).first()
            if associetad_user:
                mail_subject = "Redefina sua senha Sem B.O"
                message = render_to_string('email/password_reset_email.html', {
                    'user': associetad_user.first_name,
                    'uid': urlsafe_base64_encode(force_bytes(associetad_user.pk)),
                    'token': account_activation_token.make_token(associetad_user),
                    'protocol': 'https' if request.is_secure() else 'http',
                    'domain': '192.168.0.108:8000'
                })
                email = EmailMessage(mail_subject, message, to=[associetad_user.email])
                email.content_subtype = 'html' 
                if email.send():
                    messages.success(request, f'Olá {associetad_user.first_name}, enviamos um email para {associetad_user.email} com as instruções para redefinir sua senha!')
                else:
                    messages.error(request, 'Seu email não consta no nosso sistema! <b>Por favor, digite um email válido!</b>')

            return redirect('login')


class PasswordResetConfirmView(View):
    template_name = 'password_reset/password_reset.html'

    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            form = SetPasswordForm(user)

            return render(
                request=request,
                template_name=self.template_name,
                context = {
                    "form": form,
                    "uidb64": uidb64,
                    "token": token,
                }
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

    def post(self, request, uidb64, token):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Sua senha foi alterada com sucesso!')
                return redirect('login')
            else:
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                       messages.error(request, gettext(error))
                return redirect('password_reset_confirm', uidb64=uidb64, token=token)
        else:
            messages.error(request, 'Esse link de redefinição de senha é inválido ou expirou.')
        return redirect('login')
    

def activate(request, uidb64, token):
    User =  get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.save()

        email = 'rafaelpinheirodesigner@gmail.com'
        send_info_user_email(to_email=email)

        messages.success(request, 'Obrigado por confirmar seu email, sua conta está ativada!')
    else:
        messages.error(request, 'O link de ativação é inválido!')

    return redirect('login')


def send_info_user_email(to_email):
    mail_subject = "Novo usuário cadastrado!"
    message = render_to_string('email/info_user_email.html', {
        'count': User.objects.count(),
    })

    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html' 
    email.send()