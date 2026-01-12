from django.urls import path
from .views.weebhook import SyncSIGTAPView

urlpatterns = [
    path('sync/', SyncSIGTAPView.as_view(), name='sigtap-sync'),
]
