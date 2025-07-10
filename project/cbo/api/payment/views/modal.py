# cbo/api/payment/views.py
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from cbo.models import Plan
from cbo.services.mercado_pago import MercadoPagoService


@method_decorator(csrf_exempt, name='dispatch')
class PaymentCheckoutModalView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        selected_plan_id = data.get("selected_plan")
        if not selected_plan_id:
            return JsonResponse({"error": "Campo 'selected_plan' é obrigatório."}, status=400)

        plan = Plan.objects.filter(id=selected_plan_id).first()
        if not plan:
            return JsonResponse({"error": "Plano inválido."}, status=400)

        try:
            service = MercadoPagoService()
            preference_id = service.create_checkout_preference(plan, data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": f"Erro ao gerar preferência: {str(e)}"}, status=500)

        return JsonResponse({"preference_id": preference_id})
