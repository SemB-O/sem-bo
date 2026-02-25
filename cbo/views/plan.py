from django.views import View
from django.shortcuts import render, redirect
from ..models import Plan


class PlanView(View):
    def get(self, request):
        plans = Plan.objects.filter(is_active=True).prefetch_related(
            'plan_benefits__plan_benefit'
        ).order_by('price')
        
        plans_data = []
        for plan in plans:
            benefit_associations = plan.plan_benefits.select_related('plan_benefit').all()
            plans_data.append({
                'plan': plan,
                'benefit_associations': benefit_associations
            })
        
        return render(request, 'create/select_plan.html', {'plans_data': plans_data})

    def post(self, request):
        selected_plan_id = request.POST.get('plan_id')
        if selected_plan_id:
            return redirect('register', selected_plan=selected_plan_id)
        return render(request, 'create/select_plan.html', {'error': 'Plano não selecionado'})