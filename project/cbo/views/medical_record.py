from django.db.models import Q
from django.views import View
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from ..models import Cid, Procedure
from ..forms import RecordMedicalForm


class MedicalRecordView(View):
    template_name = 'front/medical_record.html'

    def get(self, request):
        form = RecordMedicalForm()

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
    

class ProcedureAutocompleteView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = request.GET.get('page', 1)

        user_occupations = request.user.occupations.all()

        procedures = Procedure.objects.filter(
            Q(procedures_has_occupation__occupation__in=user_occupations) &
            Q(name__icontains=term)
        ).distinct()

        paginator = Paginator(procedures, 30)
        paginated_procedures = paginator.get_page(page)

        results = [
            {'id': procedure.procedure_code, 'text': procedure.name}
            for procedure in paginated_procedures
        ]

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': paginated_procedures.has_next()
            }
        })