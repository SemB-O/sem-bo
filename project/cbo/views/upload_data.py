from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect
from ..process_files import DataImporter


@method_decorator(login_required(login_url='/login'), name='dispatch')
class UploadDataView(View):
    template_name = 'create/send_files.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        arquivos = request.FILES.getlist('arquivos_txt')

        for arquivo in arquivos:
            if 'tb_procedimento' in arquivo.name:
                DataImporter.import_procedure_data(arquivo)
            elif 'tb_ocupacao' in arquivo.name:
                DataImporter.import_occupation_data(arquivo)
            elif 'tb_registro' in arquivo.name:
                DataImporter.import_record_data(arquivo)
            elif 'tb_cid' in arquivo.name:
                DataImporter.import_cid_data(arquivo)
            elif 'rl_procedimento_cid' in arquivo.name:
                DataImporter.import_procedure_has_cid_data(arquivo)
            elif 'rl_procedimento_ocupacao' in arquivo.name:
                DataImporter.import_procedure_has_occupation_data(arquivo)
            elif 'rl_procedimento_registro' in arquivo.name:
                DataImporter.import_procedure_has_record_data(arquivo)

        return redirect('home')
