import os
import re
import zipfile
import tempfile
import requests
import urllib3
from ftplib import FTP
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from cbo.process_files import DataImporter
from cbo.utils.file_downloader import FileDownloader

# Desabilita warnings de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Command(BaseCommand):
    help = 'Sincroniza dados da SIGTAP automaticamente do DATASUS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o download mesmo que já tenha atualizado recentemente',
        )

    def send_success_email(self, month, date, files_count):
        """Envia email notificando sucesso na sincronização"""
        # Importa models aqui para evitar import circular
        from cbo.models import Procedure, Cid
        
        # Conta registros no banco
        procedure_count = Procedure.objects.count()
        cid_count = Cid.objects.count()
        
        subject = f'✅ SIGTAP Sincronizado com Sucesso - {month}'
        message = f'''Sincronização SIGTAP concluída com sucesso!

📅 Mês: {month}
🕒 Data/Hora: {date}
📁 Arquivos processados: {files_count}

📊 Dados no banco:
   • Procedimentos: {procedure_count:,}
   • CIDs: {cid_count:,}

Sistema: SEM B.O
'''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_FROM,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )

    def update_progress(self, step, message, percentage):
        """Atualiza o progresso no cache para o frontend"""
        cache.set('sigtap_sync_progress', {
            'step': step,
            'message': message,
            'percentage': percentage,
            'timestamp': timezone.now().isoformat()
        }, timeout=3600)  # 1 hora

    def download_ftp_file(self, url, file_path):
        """Baixa arquivo via FTP com progress tracking"""
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        path = parsed_url.path
        filename = os.path.basename(path)
        directory = os.path.dirname(path)
        
        self.stdout.write(f'📡 Conectando ao FTP: {host}')
        
        ftp = FTP(host)
        ftp.login('anonymous', 'anonymous@')
        ftp.cwd(directory)
        
        # Obtém tamanho do arquivo
        file_size = ftp.size(filename)
        self.stdout.write(f'📦 Tamanho: {file_size // 1024 // 1024}MB')
        
        downloaded = 0
        
        def write_callback(chunk):
            nonlocal downloaded
            with open(file_path, 'ab') as f:
                f.write(chunk)
            downloaded += len(chunk)
            if file_size:
                progress = 10 + int((downloaded / file_size) * 30)  # 10-40%
                self.update_progress(3, f'Baixando: {downloaded // 1024 // 1024}MB de {file_size // 1024 // 1024}MB', progress)
        
        # Remove arquivo se existir
        if os.path.exists(file_path):
            os.remove(file_path)
        
        self.stdout.write(f'📥 Baixando via FTP: {filename}')
        ftp.retrbinary(f'RETR {filename}', write_callback)
        ftp.quit()
        
        self.stdout.write(self.style.SUCCESS('✅ Download FTP concluído!'))
        return True

    def handle(self, *args, **options):
        try:
            self.update_progress(1, 'Iniciando sincronização...', 0)
            self.stdout.write(self.style.SUCCESS(f'[{timezone.now()}] Iniciando sincronização SIGTAP...'))

            self.update_progress(2, 'Buscando última versão...', 5)
            downloader = FileDownloader(
                ftp_url='ftp.datasus.gov.br',
                username='anonymous',
                password='',
                file_path_ftp='/dissemin/publicos/SIGTAP/200801_/Tabelas_consolidadas',
                local_save_path=tempfile.gettempdir()
            )

            sigtap_url = downloader.get_last_download_link()
            
            if not sigtap_url:
                self.update_progress(0, 'Erro: Nenhuma URL disponível', 0)
                self.stdout.write(self.style.ERROR('❌ Não foi possível obter o link da SIGTAP'))
                return
            
            # URLs alternativas em caso de falha (versão janeiro/2026)
            alternative_urls = [
                sigtap_url,
                'https://ftp.datasus.gov.br/pub/sistemas/tup/downloads/TabelaUnificada_202601_v2601061123.zip',
                'http://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/TabelaUnificada_202601_v2601061123.zip',
            ]
            
            # Remove duplicadas mantendo ordem
            alternative_urls = list(dict.fromkeys(alternative_urls))
                
            self.update_progress(3, 'Baixando arquivo SIGTAP...', 10)
            self.stdout.write(f'📥 Tentando baixar de: {sigtap_url}')

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "sigtap.zip")

                # Tenta cada URL até conseguir
                download_success = False
                for url_idx, current_url in enumerate(alternative_urls):
                    if url_idx > 0:
                        self.update_progress(3, f'Tentando mirror alternativo...', 10)
                        self.stdout.write(f'🔄 Tentando URL alternativa: {current_url}')
                    
                    # Detecta se é FTP ou HTTP(S)
                    if current_url.startswith('ftp://'):
                        # Download via FTP
                        try:
                            self.update_progress(3, 'Baixando via FTP...', 10)
                            download_success = self.download_ftp_file(current_url, zip_path)
                            break
                        except Exception as e:
                            self.stdout.write(f'❌ Erro no download FTP: {str(e)}')
                            continue
                    else:
                        # Download via HTTP(S)
                        max_retries = 2
                        for attempt in range(max_retries):
                            try:
                                response = requests.get(
                                    current_url, 
                                    timeout=300, 
                                    stream=True,
                                    verify=False
                                )
                                response.raise_for_status()
                                download_success = True
                                break
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    self.update_progress(3, f'Retry {attempt + 2}/{max_retries}...', 10)
                                    self.stdout.write(f'⚠️  Tentativa {attempt + 1} falhou: {str(e)[:50]}')
                                    continue
                                else:
                                    self.stdout.write(f'❌ Falha na URL: {current_url}')
                        
                        if download_success:
                            # Salva o arquivo baixado via HTTP
                            total_size = int(response.headers.get('content-length', 0))
                            downloaded = 0
                            
                            with open(zip_path, "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if total_size:
                                            progress = 10 + int((downloaded / total_size) * 30)  # 10-40%
                                            self.update_progress(3, f'Baixando: {downloaded // 1024 // 1024}MB de {total_size // 1024 // 1024}MB', progress)
                            break
                
                if not download_success:
                    self.update_progress(0, 'Erro: Não foi possível baixar de nenhuma URL', 0)
                    self.stdout.write(self.style.ERROR('❌ Todas as URLs falharam. DATASUS pode estar offline.'))
                    return

                self.update_progress(4, 'Download concluído!', 40)
                self.stdout.write(self.style.SUCCESS('✅ Download concluído'))
                
                self.update_progress(5, 'Descompactando arquivos...', 45)
                self.stdout.write('📦 Descompactando arquivos...')

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                self.update_progress(6, 'Importando dados...', 50)
                self.stdout.write('💾 Importando dados...')
                importer = DataImporter()
                
                # Mapeamento correto baseado nos nomes reais dos arquivos SIGTAP
                file_mapping = {
                    'tb_procedimento': importer.import_procedure_data,
                    'tb_ocupacao': importer.import_occupation_data,
                    'tb_registro': importer.import_record_data,
                    'tb_cid': importer.import_cid_data,
                    'rl_procedimento_cid': importer.import_procedure_has_cid_data,
                    'rl_procedimento_ocupacao': importer.import_procedure_has_occupation_data,
                    'rl_procedimento_registro': importer.import_procedure_has_record_data,
                    'tb_descricao': importer.import_description_data,
                }

                # Filtra arquivos, ignorando .zip e arquivos de layout
                files_to_process = [
                    f for f in os.listdir(tmpdir) 
                    if not f.endswith('.zip') and '_layout' not in f.lower() and '_detalhe' not in f.lower()
                ]
                total_files = len(files_to_process)
                imported_count = 0

                for idx, file_name in enumerate(files_to_process):
                    file_path = os.path.join(tmpdir, file_name)
                    
                    for keyword, import_method in file_mapping.items():
                        if keyword in file_name.lower():
                            progress = 50 + int((idx / total_files) * 45)  # 50-95%
                            self.update_progress(7, f'Processando: {file_name}', progress)
                            self.stdout.write(f'  → Processando: {file_name}')
                            
                            with open(file_path, "rb") as f:
                                import_method(f)
                            imported_count += 1
                            break

                self.update_progress(8, 'Sincronização concluída!', 100)
                self.stdout.write(self.style.SUCCESS(f'✅ Sincronização concluída! {imported_count} arquivos processados'))
                
                # Salva informação da última sincronização
                current_month = timezone.now().strftime('%Y%m')
                current_date = timezone.now().strftime('%d/%m/%Y às %H:%M')
                cache.set('sigtap_last_sync_month', current_month, timeout=None)
                cache.set('sigtap_last_sync_date', timezone.now().isoformat(), timeout=None)
                
                # Envia email de notificação
                try:
                    self.send_success_email(current_month, current_date, imported_count)
                    self.stdout.write(self.style.SUCCESS('📧 Email de notificação enviado!'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  Erro ao enviar email: {str(e)}'))

        except requests.RequestException as e:
            self.update_progress(0, f'Erro no download: {str(e)}', 0)
            self.stdout.write(self.style.ERROR(f'❌ Erro ao baixar: {str(e)}'))
        except Exception as e:
            self.update_progress(0, f'Erro: {str(e)}', 0)
            self.stdout.write(self.style.ERROR(f'❌ Erro durante sincronização: {str(e)}'))
