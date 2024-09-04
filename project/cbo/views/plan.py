from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from ..models import Plan


class PlanView(View):
    def get(self, request):
        order = ['Plano Essencial', 'Plano Essencial +', 'Plano Codificador/Faturista']
        plans = Plan.objects.all().order_by('name')
        plans_ordered = sorted(plans, key=lambda x: order.index(x.name) if x.name in order else len(order))

        return render(request, 'create/select_plan.html', {'plans': plans_ordered})

    def post(self, request):
        selected_plan_id = request.POST.get('selected_plan_id')
        redirect_url = reverse('register', kwargs={'selected_plan': selected_plan_id})
        return JsonResponse({'redirect_url': redirect_url})
