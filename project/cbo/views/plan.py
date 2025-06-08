from django.views import View
from django.shortcuts import render, redirect
from ..models import Plan


class PlanView(View):
    def get(self, request):
        plans = Plan.objects.all()
        return render(request, 'create/select_plan.html', {'plans': plans})

    def post(self, request):
        selected_plan_id = request.POST.get('plan_id')
        if selected_plan_id:
            return redirect('register', selected_plan=selected_plan_id)
        else:
            return render(request, 'create/select_plan.html', {'error': 'Plano não selecionado'})
