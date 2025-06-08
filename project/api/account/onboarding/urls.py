from django.urls import path
from api.account.onboarding.views import PlanAccountOnboardingListAPIView
from .views.occupation_list import OccupationAccountOnboardingListAPIView
from .views.user_create import UserAccountOnboardingCreateAPIView

urlpatterns = [
    path('plan/list/', PlanAccountOnboardingListAPIView.as_view(), name='account-onboarding-plan-list'),
    path('occupation/list/', OccupationAccountOnboardingListAPIView.as_view(), name='account-onboarding-occupation-list'),
    path('user/create/', UserAccountOnboardingCreateAPIView.as_view(), name='account-onboarding-user-create'),
]
