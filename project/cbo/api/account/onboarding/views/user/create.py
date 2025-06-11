from cbo.models import Plan
from cbo.forms.user import UserRegisterForm
from django.http import JsonResponse
from django.views import View
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


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
            user = form.save()
            
            return JsonResponse({
                'valid': True,
                'message': 'Usuário registrado com sucesso!',
                'user_id': user.id
            })

        return JsonResponse({
            'valid': False,
            'errors': form.errors
        }, status=400)
