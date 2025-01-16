from django.db.models import Q
from django.views import View
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from ..models import Cid, Procedure
from ..forms.record_medical import RecordMedicalForm


class MedicalRecordView(View):
    template_name = 'front/medical_record.html'

    def get(self, request):
        user_occupations = request.user.occupations.all()

        procedures_list = Procedure.objects.filter(
            Q(procedures_has_occupation__occupation__in=user_occupations)
        ).distinct()

        procedure_options = [(proc.procedure_code, proc.name) for proc in procedures_list]

        form = RecordMedicalForm(
            procedure_options=procedure_options,
            cid_options=[]
        )

        context = {
            'form': form
        }

        return render(request, self.template_name, context)
    

class CidAutocompleteView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = request.GET.get('page', 1)

        user_occupations = request.user.occupations.all()

        procedures_list = Procedure.objects.filter(
            Q(procedures_has_occupation__occupation__in=user_occupations)
        ).distinct()

        cids = Cid.objects.filter(
            Q(cids_has_procedure__procedure__in=procedures_list) &
            Q(name__icontains=term)
        ).distinct()

        paginator = Paginator(cids, 30)
        paginated_cids = paginator.get_page(page)

        results = [
            {'id': cid.cid_code, 'text': cid.name}
            for cid in paginated_cids
        ]

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': paginated_cids.has_next()
            }
        })