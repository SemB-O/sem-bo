from cbo.models import Plan, Payment
from cbo.forms.user import UserRegisterForm
from django.http import JsonResponse
from django.views import View
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from cbo.services.mercado_pago import MercadoPagoService


@method_decorator(csrf_exempt, name='dispatch')
class UserCreate(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body or b'{}')

        selected_plan_id = data.get('selected_plan')
        payment_id = data.get('payment_id')

        plan = Plan.objects.filter(id=selected_plan_id).first() if selected_plan_id else None
        if selected_plan_id and not plan:
            return JsonResponse({
                'valid': False,
                'errors': {'selected_plan': ['Plano selecionado inválido.']}
            }, status=400)

        if not payment_id:
            return JsonResponse({
                'valid': False,
                'errors': {'payment': ['Pagamento não informado.']}
            }, status=400)

        service = MercadoPagoService()
        try:
            payment_data = service.sdk.payment().get(payment_id)["response"]
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'errors': {'payment': ['Erro ao verificar pagamento.', str(e)]}
            }, status=400)

        if payment_data.get("status") != "approved":
            return JsonResponse({
                'valid': False,
                'errors': {'payment': ['Pagamento não aprovado.']}
            }, status=400)

        form = UserRegisterForm(data, plan=plan)
        if form.is_valid():
            user = form.save()

            Payment.objects.create(
                user=user,
                plan=plan,
                status=payment_data.get("status"),
                payment_id=payment_data.get("id"),
                merchant_order_id=payment_data.get("order", {}).get("id"),
                external_reference=payment_data.get("external_reference"),
                payment_type_id=payment_data.get("payment_type_id"),
                net_received_amount=payment_data.get("transaction_details", {}).get("net_received_amount", 0),
                approved_at=payment_data.get("date_approved"),
                payer_email=payment_data.get("payer", {}).get("email"),
            )

            return JsonResponse({
                'valid': True,
                'message': 'Usuário registrado com sucesso!',
                'user_id': user.id
            })

        return JsonResponse({
            'valid': False,
            'errors': form.errors
        }, status=400)
