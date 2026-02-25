from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from ..models import Procedure, Cid


class CidAutocomplete(View):
    def get(self, request):
        term = request.GET.get('term', '')
        user = request.user
        occupations = user.occupations.all()

        procedures = Procedure.objects.filter(
            procedures_has_occupation__occupation__in=occupations
        )

        cids = Cid.objects.filter(
            cids_has_procedure__procedure__in=procedures,
            name__icontains=term
        )[:10]

        results = [{'id': cid.cid_code, 'text': cid.name} for cid in cids]
        return JsonResponse({'results': results})