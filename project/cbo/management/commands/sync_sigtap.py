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
    help = '''Sincroniza dados da SIGTAP automaticamente do DATASUS
    
    ATENÇÃO: Este comando verifica se a competência já existe no banco.
    Se existir, a sincronização será BLOQUEADA para evitar perda de dados.
    
    Opções:
        --force: Força download mesmo que já tenha atualizado recentemente
        --allow-overwrite: PERIGOSO! Permite sobrescrever competência existente
    
    Exemplo de uso seguro:
        python manage.py sync_sigtap
    
    Exemplo de sobrescrita (USE COM CUIDADO):
        python manage.py sync_sigtap --allow-overwrite
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o download mesmo que já tenha atualizado recentemente',
        )
        parser.add_argument(
            '--allow-overwrite',
            action='store_true',
            help='Permite sobrescrever dados de competências já existentes (USE COM CUIDADO!)',
        )
    
    def extract_competence_from_filename(self, filename):
        """
        Extrai código da competência do nome do arquivo ZIP.
        Ex: TabelaUnificada_202601_v2601061123.zip -> 202601
        """
        match = re.search(r'(\d{6})', filename)
        if match:
            return match.group(1)
        return None

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

    def update_progress(self, step, message, percentage, warning=None, error=None, requires_confirmation=False, competence_info=None):
        """Atualiza o progresso no cache para o frontend"""
        progress_data = {
            'step': step,
            'message': message,
            'percentage': percentage,
            'timestamp': timezone.now().isoformat()
        }
        
        if warning:
            progress_data['warning'] = warning
        
        if error:
            progress_data['error'] = error
        
        if requires_confirmation:
            progress_data['requires_confirmation'] = True
            progress_data['competence_info'] = competence_info
        
        cache.set('sigtap_sync_progress', progress_data, timeout=3600)  # 1 hora

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
        from cbo.models import SigtapSyncHistory, Competence, Procedure
        
        # Cria registro de histórico
        sync_history = SigtapSyncHistory.objects.create(
            status='in_progress',
            is_automatic=not options.get('force', False),
            files_total=8,  # 8 arquivos esperados do SIGTAP
        )
        
        try:
            self.update_progress(1, 'Verificando competências existentes...', 0)
            self.stdout.write(self.style.SUCCESS(f'[{timezone.now()}] Iniciando sincronização SIGTAP...'))
            
            # PROTEÇÃO: Verifica competências existentes no banco
            existing_competences = list(
                Competence.objects.filter(is_atemporal=False)
                .order_by('-code')
                .values_list('code', 'formatted_date')[:5]
            )
            
            if existing_competences:
                warning_msg = f'Já existem {len(existing_competences)} competências no banco'
                comp_list = ', '.join([f'{c[1]}' for c in existing_competences[:3]])
                
                self.stdout.write(self.style.WARNING('⚠️  ATENÇÃO: Já existem competências no banco:'))
                for comp_code, comp_date in existing_competences:
                    self.stdout.write(f'   • {comp_date} (código: {comp_code})')
                
                # Atualiza progresso com warning
                self.update_progress(
                    1, 
                    'Competências existentes detectadas',
                    5,
                    warning=f'{warning_msg}: {comp_list}'
                )
                
                # Verifica se não é um --force
                if not options.get('force'):
                    self.stdout.write(self.style.WARNING(
                        '\n⚠️  A sincronização pode sobrepor dados existentes!'
                    ))
                    self.stdout.write(self.style.WARNING(
                        '   Use --force apenas se tiver certeza que deseja atualizar a MESMA competência.'
                    ))
                    
                    # Registra no histórico
                    sync_history.details = {
                        'existing_competences': [c[0] for c in existing_competences],
                        'warning': 'Competências existentes detectadas'
                    }
                    sync_history.save()

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
                    error_msg = 'Não foi possível baixar de nenhuma URL'
                    sync_history.mark_as_completed(status='failed', error_message=error_msg)
                    self.update_progress(0, f'Erro: {error_msg}', 0)
                    self.stdout.write(self.style.ERROR('❌ Todas as URLs falharam. DATASUS pode estar offline.'))
                    return

                self.update_progress(4, 'Download concluído!', 40)
                self.stdout.write(self.style.SUCCESS('✅ Download concluído'))
                
                # PROTEÇÃO: Extrai e verifica competência do arquivo
                filename = os.path.basename(sigtap_url)
                new_competence = self.extract_competence_from_filename(filename)
                
                if new_competence:
                    self.stdout.write(f'📅 Competência detectada no arquivo: {new_competence}')
                    self.update_progress(4, f'Competência detectada: {new_competence}', 42)
                    
                    # Verifica se já existe esta competência
                    existing_comp = Competence.objects.filter(code=new_competence).first()
                    
                    if existing_comp and not existing_comp.is_atemporal:
                        # Competência já existe
                        if not options.get('allow_overwrite'):
                            error_msg = f'❌ Competência {new_competence} ({existing_comp.formatted_date}) já existe no banco!'
                            
                            # Mensagem especial para interface web (pede confirmação)
                            detailed_error = f'A competência {existing_comp.formatted_date} já está no sistema.'
                            
                            sync_history.mark_as_completed(status='failed', error_message=error_msg)
                            sync_history.details = {
                                'error': 'competence_already_exists',
                                'existing_competence': new_competence,
                                'existing_formatted': existing_comp.formatted_date,
                                'requires_confirmation': True  # Flag para frontend
                            }
                            sync_history.save()
                            
                            # Atualiza progresso com erro que pede confirmação
                            self.update_progress(
                                0,
                                'Competência já existe',
                                0,
                                error=detailed_error,
                                requires_confirmation=True,
                                competence_info={
                                    'code': new_competence,
                                    'formatted': existing_comp.formatted_date
                                }
                            )
                            
                            self.stdout.write(self.style.ERROR(
                                f'\n{error_msg}\n'
                                f'   Use --allow-overwrite para forçar a sobrescrita (NÃO RECOMENDADO!)\n'
                                f'   Ou importe manualmente dados de uma competência diferente.'
                            ))
                            return
                        else:
                            warning_msg = f'Sobrescrevendo competência {new_competence} ({existing_comp.formatted_date})'
                            
                            self.stdout.write(self.style.WARNING(f'⚠️  {warning_msg}'))
                            self.update_progress(
                                4,
                                f'Verificando arquivos...',
                                43,
                                warning=warning_msg
                            )
                            
                            sync_history.details = {
                                'warning': 'overwriting_existing_competence',
                                'competence': new_competence
                            }
                            sync_history.save()
                    
                    # Salva competência no histórico
                    sync_history.competence_code = new_competence
                    sync_history.save()
                
                self.update_progress(5, 'Descompactando arquivos...', 45)
                self.stdout.write('📦 Descompactando arquivos...')

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)

                self.update_progress(6, 'Importando dados...', 50)
                self.stdout.write('💾 Importando dados...')
                
                # Cria importer com flag de sobrescrita se permitido
                allow_overwrite = options.get('allow_overwrite', False)
                importer = DataImporter(allow_overwrite=allow_overwrite)
                
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

                self.update_progress(8, 'Sincronizando competências...', 95)
                
                # Sincroniza tabela de competências
                from cbo.process_files import DataImporter
                from cbo.models import Competence
                
                try:
                    comp_stats = DataImporter.sync_competences()
                    sync_history.competences_synced = comp_stats['total']
                    sync_history.files_processed = imported_count
                    
                    # Obtém a última competência real
                    latest_comp = Competence.get_latest_real_competence()
                    if latest_comp:
                        sync_history.competence_code = latest_comp.code
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'📅 Competências sincronizadas: {comp_stats["total"]} total '
                        f'({comp_stats["real_competences"]} reais, {comp_stats["atemporal_competences"]} atemporais)'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  Erro ao sincronizar competências: {str(e)}'))
                
                # Atualiza contadores do histórico
                sync_history.update_counts()
                
                # Marca como concluída com sucesso
                sync_history.mark_as_completed(status='success')
                
                self.update_progress(8, 'Sincronização concluída!', 100)
                self.stdout.write(self.style.SUCCESS(f'✅ Sincronização concluída! {imported_count} arquivos processados'))
                
                # Salva informação da última sincronização (backward compatibility)
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
            error_msg = f'Erro ao baixar: {str(e)}'
            sync_history.mark_as_completed(status='failed', error_message=error_msg)
            self.update_progress(0, f'Erro no download: {str(e)}', 0)
            self.stdout.write(self.style.ERROR(f'❌ {error_msg}'))
        except Exception as e:
            error_msg = f'Erro durante sincronização: {str(e)}'
            sync_history.mark_as_completed(status='failed', error_message=error_msg)
            self.update_progress(0, f'Erro: {str(e)}', 0)
            self.stdout.write(self.style.ERROR(f'❌ {error_msg}'))
