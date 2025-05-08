import logging
import time
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect
from ..process_files import DataImporter
from django.db import transaction

logger = logging.getLogger('upload_files_view')

@method_decorator(login_required(login_url='/login'), name='dispatch')
class UploadFilesView(View):
    template_name = 'create/send_files.html'

    def get(self, request):
        logger.info(f"User {request.user.username} is accessing the file upload page.")
        return render(request, self.template_name)

    @transaction.atomic
    def post(self, request):
        files = request.FILES.getlist('arquivos_txt')

        logger.info("Starting file upload process.")
        start_time = time.time()

        for file in files:
            start_file_time = time.time()

            try:
                logger.info(f"Processing file: {file.name}")

                if 'tb_procedimento' in file.name:
                    DataImporter.import_procedure_data(file)
                elif 'tb_ocupacao' in file.name:
                    DataImporter.import_occupation_data(file)
                elif 'tb_registro' in file.name:
                    DataImporter.import_record_data(file)
                elif 'tb_cid' in file.name:
                    DataImporter.import_cid_data(file)
                elif 'rl_procedimento_cid' in file.name:
                    DataImporter.import_procedure_has_cid_data(file)
                elif 'rl_procedimento_ocupacao' in file.name:
                    DataImporter.import_procedure_has_occupation_data(file)
                elif 'rl_procedimento_registro' in file.name:
                    DataImporter.import_procedure_has_record_data(file)
                elif 'tb_descricao' in file.name:
                    DataImporter.import_description_data(file)

                file_process_time = time.time() - start_file_time
                logger.info(f"File {file.name} processed in {file_process_time:.2f} seconds.")

            except Exception as e:
                logger.error(f"Error processing file {file.name}: {str(e)}")

        total_process_time = time.time() - start_time
        logger.info(f"File upload process completed in {total_process_time:.2f} seconds.")

        return redirect('home')
