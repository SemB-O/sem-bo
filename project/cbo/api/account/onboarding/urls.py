from django.urls import path
from cbo.api.account.onboarding.views import UserCreate, ValidatePessoalInfoView, ValidateProfissionalInfoView

urlpatterns = [
    path('users/validate/personal-info/', ValidatePessoalInfoView.as_view(), name='onboarding-user-validate-personal-info'),
    path('users/validate/professional-info/', ValidateProfissionalInfoView.as_view(), name='onboarding-user-validate-professional-info'),
    path('/users/', UserCreate.as_view(), name='onboarding-user-create')
]
