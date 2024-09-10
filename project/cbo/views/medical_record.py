from django.db.models import Q
from django.views import View
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from weasyprint import HTML, CSS
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


class SubmitFormDataView(View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = request.POST.dict()
            form_type = data.get('type')

            html_content = self.render_html_template(data, form_type)
            if not html_content:
                return JsonResponse({'status': 'error', 'message': 'Unknown form type'}, status=400)

            pdf = HTML(string=html_content).write_pdf()

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={form_type}_record.pdf'
            return response

        except (KeyError, ValueError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)

    def render_html_template(self, data, form_type):
        if form_type == 'resumo_alta':
            return render_to_string('prontuarios/resumo_alta.html', data)
        elif form_type == 'laudo_medico':
            return render_to_string('prontuarios/laudo_medico_hospitalar.html', data)
        return None