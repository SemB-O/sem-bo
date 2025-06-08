from rest_framework.generics import CreateAPIView
from django.contrib.auth import get_user_model
from ..serializers.user_create import UserAccountOnboardingCreateSerializer

User = get_user_model()


class UserAccountOnboardingCreateAPIView(CreateAPIView):
    queryset = User.objects.none() 
    serializer_class = UserAccountOnboardingCreateSerializer
