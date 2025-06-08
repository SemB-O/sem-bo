from rest_framework.generics import ListAPIView
from cbo.models import Plan
from ..serializers.plan_list import PlanAccountOnboardingListSerializer


class PlanAccountOnboardingListAPIView(ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanAccountOnboardingListSerializer
