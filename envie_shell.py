#PARA ENVIAR A SHELL PARA O SERVIDOR, EA SSIM COPIAR NA MAQUINA ALVO. 
#By <\ackles>


import requests
import base64
import os 
arquivo_existe= "shell"
if os.path.exists(arquivo_existe):
	arquivo_existe_true = True 
else:
	os.system('')
	
url1 = input("Url: ")
arquivo = input("Nome do arquivo: ")
conteudo = input("Conteúdo a ser enviado: ")
with open(arquivo, 'w', buffering=1024 * 1024) as file:
    file.write(conteudo)
with open(arquivo, 'rb') as file:
    file_content = file.read()
files = {
    'file': (arquivo, file_content, 'application/octet-stream')
}
if arquivo == "shell":
    url = url1 + "/shell"
    response = requests.post(url, files=files)
else:
    url = url1 + "/capture"
    response = requests.post(url, files=files)
print(f"Status Code: {response.status_code}")
