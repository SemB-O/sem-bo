from ftplib import FTP
import os
import requests
from bs4 import BeautifulSoup


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
            print(f"Arquivo baixado com sucesso: {filename}")
            
        except Exception as e:
            print(f"Erro ao baixar arquivo: {e}")

    def get_last_download_link(self):
        url = 'http://tabela-unificada.datasus.gov.br/tabela-unificada/app/download.jsp'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = soup.find_all('a', id=lambda x: x and x.endswith(':0:_idJsp195'))
            
            if links:
                ultimo_link = links[-1]['href']
                return ultimo_link
            else:
                return None
        else:
            print("Falha ao fazer a requisição. Código de status:", response.status_code)
            return None

