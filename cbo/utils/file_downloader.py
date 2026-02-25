from ftplib import FTP
import os
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FileDownloader:
    def __init__(self, ftp_url, username, password, file_path_ftp, local_save_path):
        self.ftp_url = ftp_url
        self.username = username
        self.password = password
        self.file_path_ftp = file_path_ftp
        self.local_save_path = local_save_path

    def download_file_from_ftp(self):
        try:
            ftp = FTP(self.ftp_url)
            ftp.login(self.username, self.password)
            
            ftp.cwd(self.file_path_ftp)
            
            filename = self.file_path_ftp.split("/")[-1]
            
            with open(os.path.join(self.local_save_path, filename), 'wb') as local_file:
                ftp.retrbinary('RETR ' + filename, local_file.write)
            
            ftp.quit()
            logger.info(f"Arquivo baixado com sucesso: {filename}")
            
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo: {e}")

    def get_last_download_link_from_ftp(self):
        """Busca o último arquivo SIGTAP diretamente do FTP"""
        try:
            logger.info("🔍 Conectando ao FTP do DATASUS...")
            ftp = FTP('ftp2.datasus.gov.br')
            ftp.login('anonymous', 'anonymous@')
            
            logger.info("📂 Navegando para /pub/sistemas/tup/downloads...")
            ftp.cwd('/pub/sistemas/tup/downloads')
            
            logger.info("📋 Listando arquivos...")
            files = []
            ftp.dir(files.append)
            
            # Filtra apenas arquivos TabelaUnificada_*.zip
            sigtap_files = []
            for line in files:
                if 'TabelaUnificada_' in line and line.endswith('.zip'):
                    # Extrai nome do arquivo da linha
                    # Formato: -rwxr-xr-x ... TabelaUnificada_202601_v2601061123.zip
                    parts = line.split()
                    filename = parts[-1]
                    sigtap_files.append(filename)
            
            ftp.quit()
            
            if sigtap_files:
                # O último arquivo da lista é o mais recente
                latest_file = sigtap_files[-1]
                logger.info(f"✅ Arquivo mais recente encontrado: {latest_file}")
                
                # Monta URL FTP
                download_url = f'ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/{latest_file}'
                logger.info(f"🔗 URL FTP: {download_url}")
                
                return download_url, latest_file
            else:
                logger.warning("❌ Nenhum arquivo SIGTAP encontrado no FTP")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ Erro ao acessar FTP: {e}")
            return None, None

    def get_last_download_link(self):
        """Busca o último link de download da SIGTAP - tenta FTP primeiro, depois fallback"""
        
        # Tenta FTP primeiro (método mais confiável)
        ftp_url, filename = self.get_last_download_link_from_ftp()
        
        if ftp_url and filename:
            return ftp_url
        
        # Fallback: URL hardcoded (versão janeiro/2026 - mais recente conhecida)
        logger.warning("⚠️  FTP indisponível, usando URL fallback...")
        fallback_url = 'ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/TabelaUnificada_202601_v2601061123.zip'
        logger.info(f"📋 URL fallback: {fallback_url}")
        return fallback_url
