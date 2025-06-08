from rest_framework import serializers
from django.contrib.auth import get_user_model
from cbo.models import Occupation, UserHasOccupation, Plan

User = get_user_model()


class UserAccountOnboardingCreateSerializer(serializers.ModelSerializer):
    occupation = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Occupation.objects.all(), write_only=True
    )
    plan = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), required=True
    )

    class Meta:
        model = User
        fields = [
            'CPF',
            'email',
            'telephone',
            'date_of_birth',
            'occupational_registration',
            'occupation',
            'plan',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        occupations = data.get('occupation', [])
        plan = data.get('plan')

        if plan and occupations and len(occupations) > plan.max_occupations:
            raise serializers.ValidationError({
                "occupation": f"O plano selecionado permite no máximo {plan.max_occupations} ocupações."
            })

        return data

    def create(self, validated_data):
        occupations = validated_data.pop('occupation')
        user = User.objects.create_user(**validated_data)
        for occupation in occupations:
            UserHasOccupation.objects.create(user=user, occupation=occupation)
        return user
