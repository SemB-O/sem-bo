import pytest
from rest_framework.test import APIRequestFactory
from api.account.onboarding.views.occupation_list import OccupationAccountOnboardingListAPIView
from cbo.models import Occupation


@pytest.mark.django_db
class OccupationAccountOnboardingListTest:
    def setup_method(self):
        self.factory = APIRequestFactory()
        self.view = OccupationAccountOnboardingListAPIView.as_view()
        self.url = '/api/account/onboarding/occupation/list/'

    def test_returns_all_occupations(self):
        Occupation.objects.create(name="Médico", occupation_code="123")
        Occupation.objects.create(name="Arquiteto", occupation_code="456")

        request = self.factory.get(self.url)
        response = self.view(request)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert len(response.data) == 2
        names = [item['name'] for item in response.data]
        assert "Médico" in names
        assert "Arquiteto" in names

    def test_returns_empty_when_no_occupations(self):
        request = self.factory.get(self.url)
        response = self.view(request)

        assert response.status_code == 200
        assert response.data == []
