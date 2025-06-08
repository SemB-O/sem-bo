from rest_framework import serializers
from cbo.models import Plan  


class PlanAccountOnboardingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price']
