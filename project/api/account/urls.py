from django.urls import path, include

urlpatterns = [
    path('onboarding/', include('api.account.onboarding.urls')),
]
