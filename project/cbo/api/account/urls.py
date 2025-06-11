from django.urls import path, include

urlpatterns = [
    path('onboarding/', include('cbo.api.account.onboarding.urls')),
]
