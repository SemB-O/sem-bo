import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from cbo.forms.user import UserRegisterForm


@method_decorator(csrf_exempt, name='dispatch')
class ValidatePessoalInfoView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body or b'{}')
        form = UserRegisterForm(data, plan=None)

        fields_to_keep = ['first_name', 'last_name', 'CPF', 'telephone', 'date_of_birth']
        for field in list(form.fields):
            if field not in fields_to_keep:
                form.fields.pop(field)

        if form.is_valid():
            return JsonResponse({'valid': True})
        return JsonResponse({'valid': False, 'errors': form.errors}, status=400)
