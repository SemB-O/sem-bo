from django.urls import path, include
from cbo.views.profile import UserEditFormValidationView

urlpatterns = [
    path('onboarding/', include('cbo.api.account.onboarding.urls')),
    path('profile/users/validate/', UserEditFormValidationView.as_view(), name='profile-user-validate')
]
