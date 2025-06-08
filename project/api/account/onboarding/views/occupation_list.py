from rest_framework.generics import ListAPIView
from cbo.models import Occupation
from ..serializers.occupation_list import OccupationAccountOnboardingListSerializer


class OccupationAccountOnboardingListAPIView(ListAPIView):
    queryset = Occupation.objects.all()
    serializer_class = OccupationAccountOnboardingListSerializer
