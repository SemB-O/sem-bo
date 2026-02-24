from cbo.models import Plan, FavoriteProceduresFolder
from cbo.forms.user import UserRegisterForm
from django.http import JsonResponse
from django.views import View
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from cbo.tokens import account_activation_token
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class UserCreate(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body or b'{}')

        selected_plan_id = data.get('selected_plan')
        plan = Plan.objects.filter(id=selected_plan_id).first() if selected_plan_id else None

        if selected_plan_id and not plan:
            return JsonResponse({
                'valid': False,
                'errors': {'selected_plan': ['Plano selecionado inválido.']}
            }, status=400)

        form = UserRegisterForm(data, plan=plan)

        if form.is_valid():
            # Cria o usuário mas mantém inativo até verificar o email
            user = form.save(commit=False)
            user.is_active = False
            user.email_verified = False
            user.save()
            
            # Salva as ocupações (Many-to-Many precisa de save após o user ter ID)
            form.save_m2m()
            
            # Cria a pasta padrão de favoritos
            FavoriteProceduresFolder.objects.get_or_create(
                user=user,
                name="General",
                description="My Favorites"
            )
            
            # Envia email de verificação
            email_sent = self._send_verification_email(request, user)
            
            if not email_sent:
                logger.error(f"Falha ao enviar email de verificação para {user.email}")
            
            return JsonResponse({
                'valid': True,
                'message': 'Usuário registrado com sucesso! Verifique seu email para ativar sua conta.',
                'user_id': user.id,
                'email_sent': email_sent
            })

        return JsonResponse({
            'valid': False,
            'errors': form.errors
        }, status=400)
    
    def _send_verification_email(self, request, user):
        """Envia email de verificação para o usuário"""
        try:
            mail_subject = "Ativação da sua conta Sem B.O"
            message = render_to_string('email/email_verification.html', {
                'user': user.first_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': settings.DOMAIN,
            })
            
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.content_subtype = 'html'
            
            return email.send() > 0
        except Exception as e:
            logger.exception(f"Erro ao enviar email de verificação: {e}")
            return False
