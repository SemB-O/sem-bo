import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from cbo.models import Occupation, Plan, User


@pytest.mark.django_db
class UserAccountOnboardingCreateTest:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("account-onboarding-user-create")

        self.plan = Plan.objects.create(
            name="Pro",
            max_occupations=3,
            description="Plano profissional",
            price=99.99
        )
        self.occupation1 = Occupation.objects.create(name="Dev", occupation_code="111")
        self.occupation2 = Occupation.objects.create(name="Designer", occupation_code="222")

    def test_create_user_with_valid_data(self):
        data = {
            "password": "securePassword123",
            "email": "test@example.com",
            "CPF": "366.270.980-59",
            "telephone": "11999999999",
            "date_of_birth": "2000-01-01",
            "plan": self.plan.id,
            "occupation": [self.occupation1.occupation_code, self.occupation2.occupation_code]
        }

        response = self.client.post(self.url, data, format="json")

        assert response.status_code == 201
        assert User.objects.filter(email="test@example.com").exists()

    def test_fails_with_missing_fields(self):
        response = self.client.post(self.url, {}, format="json")

        assert response.status_code == 400
        required_fields = ["email", "CPF", "telephone", "date_of_birth", "plan", "occupation"]
        for field in required_fields:
            assert field in response.data

    def test_fails_if_plan_limit_exceeded(self):
        limited_plan = Plan.objects.create(
            name="Basic",
            max_occupations=1,
            description="Plano básico",
            price=19.90

        )

        data = {
            "password": "Pass123!",
            "email": "limit@example.com",
            "CPF": "642.134.220-54",
            "telephone": "11777777777",
            "date_of_birth": "1990-10-10",
            "plan": limited_plan.id,
            "occupation": [self.occupation1.occupation_code, self.occupation2.occupation_code],
        }

        response = self.client.post(self.url, data, format="json")

        assert response.status_code == 400
        assert "occupation" in response.data or "non_field_errors" in response.data
