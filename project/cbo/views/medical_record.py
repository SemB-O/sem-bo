from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from ..forms import RecordMedicalForm


class MedicalRecordView(View):
    template_name = 'front/medical_record_home.html'

    def get(self, request):
        occupations = request.user.occupations.all()
        form = RecordMedicalForm()
        context = {
            'form': form
        }
        
        return render(request, self.template_name, context)