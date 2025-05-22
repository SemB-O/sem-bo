import json
from django.contrib.auth.views import LogoutView
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login
from django.views import View
from django.views.generic import TemplateView
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
from django.db.models import Q
from ..forms.user import LoginAuthenticationForm, UserRegisterForm, PasswordResetEmailForm, SetPasswordForm
from ..models import Occupation, Plan, FavoriteFolder, User


class LoginView(FormView):
    template_name = 'front/login.html'
    form_class = LoginAuthenticationForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect('home')
        else:
            messages.error(self.request, 'Credenciais inválidas. Tente novamente.')
            return redirect('login')

    def form_invalid(self, form):
        messages.error(self.request, 'Erro no formulário. Verifique os dados.')
        return redirect('login')


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
            'selected_plan': selected_plan,
            'plans_json': plans_json,
        }

        return render(request, self.template_name, context)

    def post(self, request, selected_plan, *args, **kwargs):
        form = UserRegisterForm(request.POST, use_required_attribute=False)

        if form.is_valid():
            try:
                user = self._create_user(form)
                self._assign_occupations(user, form.cleaned_data['occupation'])
                self._create_default_folder(user)
                self.activateEmail(request, user, form.cleaned_data.get('email'))
                return redirect('login')
            except Exception as e:
                return render(request, self.template_name, {
                    'form': form,
                    'form_error': f"An unexpected error occurred: {str(e)}"
                })
        else:
            return render(request, self.template_name, {
                'form': form,
                'selected_plan': selected_plan,
            })


    def _create_user(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        return user

    def _assign_occupations(self, user, occupations):
        for occupation in occupations:
            user.occupations.add(occupation)
        user.save()

    def _create_default_folder(self, user):
        FavoriteFolder.objects.get_or_create(
            user=user,
            name="General",
            description="My Favorites"
        )

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


class PasswordResetView(TemplateView):
    template_name = 'password_reset/password_reset.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PasswordResetEmailForm()
        return context

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
                    'domain': settings.DOMAIN
                })
                email = EmailMessage(mail_subject, message, to=[associetad_user.email])
                email.content_subtype = 'html' 
                if email.send():
                    messages.success(request, f'Olá {associetad_user.first_name}, enviamos um email para {associetad_user.email} com as instruções para redefinir sua senha!')
                else:
                    messages.error(request, 'Seu email não consta no nosso sistema! <b>Por favor, digite um email válido!</b>')

            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('password_reset')


class PasswordResetConfirmView(TemplateView):
    template_name = 'password_reset/email_password_reset.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uidb64 = self.kwargs.get('uidb64')
        token = self.kwargs.get('token')
        form = SetPasswordForm()

        context.update({
            'form': form,
            'uidb64': uidb64,
            'token': token
        })
        
        return context

    def get_user_from_uid(self, uidb64):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            return None

    def post(self, request, uidb64, token):
        user = self.get_user_from_uid(uidb64)

        if user is not None and account_activation_token.check_token(user, token):
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                form.save(user)
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