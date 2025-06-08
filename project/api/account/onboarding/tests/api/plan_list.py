import pytest
from rest_framework.test import APIRequestFactory
from api.account.onboarding.views.plan_list import PlanAccountOnboardingListAPIView
from cbo.models import Plan


@pytest.mark.django_db
class PlanAccountOnboardingListTest:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.view = PlanAccountOnboardingListAPIView.as_view()
        self.url = '/api/account/onboarding/plan/list/'

    def test_returns_all_plans(self):
        Plan.objects.create(name="Basic", max_occupations=1, description="Basic plan", price=19.90)
        Plan.objects.create(name="Premium", max_occupations=5, description="Premium plan", price=99.90)


        request = self.factory.get(self.url)
        response = self.view(request)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 2
        names = [item['name'] for item in response.data]
        assert "Basic" in names
        assert "Premium" in names

    def test_returns_empty_when_no_plans(self):
        request = self.factory.get(self.url)
        response = self.view(request)

        assert response.status_code == 200
        assert response.data == []
