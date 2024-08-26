from django.urls import path
from . import views

urlpatterns = [
    path('run_migrations/', views.run_migrations, name='run_migrations'),
    path('run_collectstatic/', views.run_collectstatic, name='run_collectstatic'),
    path('create_superuser/', views.create_superuser, name='create_superuser'),
]