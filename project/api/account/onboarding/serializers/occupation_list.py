from rest_framework import serializers
from cbo.models import Occupation

class OccupationAccountOnboardingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Occupation
        fields = ['occupation_code', 'name']
