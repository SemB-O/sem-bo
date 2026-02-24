from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import os
import re
import zipfile
import tempfile
import requests

from cbo.process_files import DataImporter


@method_decorator(csrf_exempt, name='dispatch')
class SyncSIGTAPView(View):
    def post(self, request):
        email_body = request.POST.get("body")

        if not email_body:
            return JsonResponse({"error": "Corpo do e-mail não recebido."}, status=400)

        match = re.search(r"https?://\S+\.zip", email_body)
        if not match:
            return JsonResponse({"error": "Link da SIGTAP não encontrado no e-mail."}, status=400)

        sigtap_url = match.group(0)

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "sigtap.zip")

                response = requests.get(sigtap_url)
                response.raise_for_status()

                with open(zip_path, "wb") as f:
                    f.write(response.content)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                importer = DataImporter()

                for file_name in os.listdir(tmpdir):
                    file_path = os.path.join(tmpdir, file_name)

                    if "procedure" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_procedure_data(f)
                    elif "occupation" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_occupation_data(f)
                    elif "record" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_record_data(f)
                    elif "cid" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_cid_data(f)
                    elif "proc_cid" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_procedure_has_cid_data(f)
                    elif "proc_ocup" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_procedure_has_occupation_data(f)
                    elif "proc_registro" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_procedure_has_record_data(f)
                    elif "descricao" in file_name.lower():
                        with open(file_path, "rb") as f:
                            importer.import_description_data(f)

            return JsonResponse({"status": "Dados da SIGTAP sincronizados com sucesso."})

        except Exception as e:
            return JsonResponse({"error": f"Erro durante a sincronização: {str(e)}"}, status=500)
