# api/account/onboarding/validation/login_info.py

import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from cbo.forms.user import UserRegisterForm
from cbo.models import Plan


@method_decorator(csrf_exempt, name='dispatch')
class ValidateLoginInfoView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body or b'{}')

        selected_plan = data.get('selected_plan')
        try:
            plan = Plan.objects.get(id=selected_plan)
        except Plan.DoesNotExist:
            return JsonResponse({'valid': False, 'errors': {'plan': ['Plano inválido.']}}, status=400)

        form = UserRegisterForm(data, plan=plan)

        fields_to_keep = ['email', 'password1', 'password2']
        for field in list(form.fields):
            if field not in fields_to_keep:
                form.fields.pop(field)

        if form.is_valid():
            return JsonResponse({'valid': True})
        return JsonResponse({'valid': False, 'errors': form.errors}, status=400)
