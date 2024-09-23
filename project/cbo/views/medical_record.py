import os
from django.db.models import Q
from django.views import View
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from weasyprint import HTML, CSS
from ..models import Cid, Procedure
from ..models.patient import Patient
from ..models.medical_record import MedicalRecord
from ..forms import RecordMedicalForm
from ..views.email_management import EmailManagementView


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

            if form_type.lower().replace(' ', '_') == 'resumo_de_alta':
                html_content = self.handle_resumo_alta(data)
            else:
                return JsonResponse({'status': 'error', 'message': 'Unknown form type'}, status=400)

            pdf = HTML(string=html_content).write_pdf(
                stylesheets=[],
                presentational_hints=True,
                **{'format': 'A4'}
            )

            patient_name = data.get('patientName')
            user = request.user
            patient = self.get_or_create_patient(patient_name, user)
            record_id = self.save_pdf_to_medical_record(patient, form_type, pdf)

            return redirect('view_single_medical_record', record_id=record_id)

        except (KeyError, ValueError) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred'}, status=500)

    def handle_resumo_alta(self, data):
        html_content = self.render_html_template(data, 'resumo_alta')
        
        medicacoes_recomendacoes_select = data.get('medicacoes_recomendacoes_select', '')
        cid_10 = data.get('cid_10', '')
        procedure = data.get('procedure', '')
        condicao_alta = data.get('condicao_alta', '')

        html_content = self.check_recommendations(html_content, medicacoes_recomendacoes_select)
        html_content = self.check_condition(html_content, condicao_alta)
        html_content = self.update_cid_sections(html_content, cid_10)
        html_content = self.update_procedure_sections(html_content, procedure)

        return html_content

    def render_html_template(self, data, form_type):
        if form_type == 'resumo_alta':
            return render_to_string('prontuarios/resumo_alta.html', {
                'clinica': data.get('clinica', ''),
                'nome': data.get('nome', ''),
                'prontuario': data.get('prontuario', ''),
                'idade': data.get('idade', ''),
                'motivo_internacao': data.get('motivo_internacao', ''),
                'resumo_internacao': data.get('resumo_internacao', ''),
                'cirurgia': data.get('cirurgia', ''),
                'resultados_exames': data.get('resultados_exames', ''),
                'medicacoes_recomendacoes': data.get('medicacoes_recomendacoes', ''),
                'medicacoes_recomendacoes_select': data.get('medicacoes_recomendacoes_select', ''),
                'diagnostico_alta': data.get('diagnostico_alta', ''),
                'condicao_alta': data.get('condicao_alta', ''),
                'encaminhamento': data.get('encaminhamento', ''),
                'cid_10': data.get('cid_10', ''),
                'procedure': data.get('procedure', ''),
                'data_alta': data.get('data_alta', ''),
            })
        elif form_type == 'laudo_medico':
            return render_to_string('prontuarios/laudo_medico_hospitalar.html', data)
        return None
    
    def check_recommendations(self, html_content, recommendation):
        soup = BeautifulSoup(html_content, 'html.parser')

        divs = soup.select('.medicacoes_recomendacoes_select div div')

        for div in divs:
            if recommendation in div.text:
                div.string = div.text.replace("(  )", "(X)")

        return str(soup)
    
    def check_condition(self, html_content, condition):
        soup = BeautifulSoup(html_content, 'html.parser')

        condition_divs = soup.select('.checkbox-group > div > div')

        for div in condition_divs:
            if condition in div.text:
                div.string = div.text.replace("(  )", "(X)")

        return str(soup)
    
    def update_cid_sections(self, html_content, cids):
        soup = BeautifulSoup(html_content, 'html.parser')

        for i, cid in enumerate(cids, start=1):
            for j, char in enumerate(cids, start=1):
                cid_id = f"cid-{i}-{j}"
                element = soup.find(id=cid_id)
                if element:
                    element.string = char

        return str(soup)

    def update_procedure_sections(self, html_content, procedures):
        soup = BeautifulSoup(html_content, 'html.parser')

        for i, procedure in enumerate(procedures, start=1):
            for j, char in enumerate(procedures, start=1):
                procedure_id = f"procedure-{i}-{j}"
                element = soup.find(id=procedure_id)
                if element:
                    element.string = char

        return str(soup)

    def get_or_create_patient(self, patient_name, user):
        patient, created = Patient.objects.get_or_create(name=patient_name, user=user)
        return patient

    def save_pdf_to_medical_record(self, patient, form_type, pdf):
        date_str = datetime.now().strftime("%Y_%m_%d")
        patient_name = patient.name.lower().replace(" ", "_")
        record_name = f"{patient_name}_{date_str}"
    
        pdf_filename = f"{record_name}.pdf"
            
        pdf_directory = Path('medical_records/')

        if not pdf_directory.exists():
            os.makedirs(pdf_directory)

        pdf_path = Path(f'medical_records/{pdf_filename}')

        medical_record = MedicalRecord.objects.create(
            patient=patient,
            record_name=record_name,
            record_type=form_type
        )

        with pdf_path.open('wb') as f:
            f.write(pdf)

        medical_record.pdf.name = str(pdf_path)
        medical_record.save()

        return medical_record.id
    

class ManageMedicalRecordsView(View):
    def get(self, request, *args, **kwargs):
        records = MedicalRecord.objects.all()
        return render(request, 'medical_records/manage_records.html', {'records': records})


class ViewSingleMedicalRecord(View):
    def get(self, request, record_id, *args, **kwargs):
        record = get_object_or_404(MedicalRecord, id=record_id)

        context = {
            'record': record,
        }

        return render(request, 'front/single_record_view.html', context)

    def post(self, request, record_id, *args, **kwargs):
        record = get_object_or_404(MedicalRecord, id=record_id)
        recipient_email = request.POST.get('recipient_email')

        if not record.pdf:
            return JsonResponse({'status': 'error', 'message': 'PDF não encontrado.'}, status=404)

        try:
            subject = f"{record.record_type} - {record.patient.name}"
            context = {
                'patient_name': record.patient.name,
                'record_name': record.record_name,
                'user': request.user,
                'type': record.record_type
            }
            template_name = 'email/medical_record_email.html'
            record_type = record.record_type.lower().replace(' ', '_')
            file_name = f'{record_type}_{record.record_name}'
            email_sent = EmailManagementView.send_email(subject, template_name, context, recipient_email, record.pdf.path, file_name)

            if email_sent:
                return JsonResponse({'status': 'success', 'message': 'E-mail enviado com sucesso!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Falha ao enviar o e-mail.'}, status=500)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class ViewMedicalRecordPDF(View):
    def get(self, request, record_id, *args, **kwargs):
        record = get_object_or_404(MedicalRecord, id=record_id)
        record_type = record.record_type.lower().replace(' ', '_')

        if not record.pdf:
            raise Http404("PDF não encontrado.")

        download = request.GET.get('download')

        if download:
            response = FileResponse(record.pdf.open(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{record_type}_{record.record_name}.pdf"'
        else:
            response = FileResponse(record.pdf.open(), content_type='application/pdf')

        return response