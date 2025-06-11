
from django.urls import path, include

urlpatterns = [
    path('account/', include('cbo.api.account.urls')),
]
