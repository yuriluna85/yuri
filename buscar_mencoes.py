import csv
import os
import requests
import json
from datetime import datetime
from urllib.parse import urlparse

# Configurações
NOME_ALVO = "Yuri de Oliveira Luna e Almeida"
PASTA_DATA = 'data'
CSV_FILE = os.path.join(PASTA_DATA, 'mencoes.csv')
HTML_FILE = 'index.html'

# Pega a chave da API das variáveis de ambiente do GitHub
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

os.makedirs(PASTA_DATA, exist_ok=True)

def buscar_na_api():
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f'"{NOME_ALVO}"', # Aqui usamos aspas para ser exato na API
        "gl": "br",
        "hl": "pt-br",
        "autocorrect": False
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

# 1. Carrega histórico
links_existentes = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"--- 📡 INICIANDO BUSCA VIA API (SERPER) ---")

try:
    dados_api = buscar_na_api()
    # A API retorna os resultados em 'organic'
    resultados = dados_api.get('organic', [])
    
    for item in resultados:
        link = item.get('link')
        if link and link not in links_existentes:
            portal = urlparse(link).netloc.replace('www.', '')
            novas_mencoes.append({
                'Data': data_execucao,
                'Portal': portal,
                'Link': link
            })
            print(f"✅ Novo link validado: {link}")

except Exception as e:
    print(f"❌ Erro na API: {e}")

# 2. Salva no CSV
if novas_mencoes or not os.path.exists(CSV_FILE):
    modo = 'w' if not os.path.exists(CSV_FILE) else 'a'
    with open(CSV_FILE, mode=modo, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if modo == 'w': writer.writeheader()
        writer.writerows(novas_mencoes)

# 3. Gera HTML (Sempre atualiza para refletir o total)
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        todos = list(csv.DictReader(f))
        todos.reverse()

    rows = "".join([f"<tr><td>{i['Data']}</td><td><span class='portal-tag'>{i['Portal']}</span></td><td><a href='{i['Link']}' target='_blank' class='btn-link'>Ver ↗</a></td></tr>" for i in todos])

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Memorial de Menções | Yuri Almeida</title>
        <style>
            :root {{ --primary: #2563eb; --bg: #f8fafc; --text: #1e293b; }}
            body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #e2e8f0; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; padding-bottom: 1rem; }}
            .counter {{ background: #dbeafe; color: var(--primary); padding: 0.3rem 0.8rem; border-radius: 999px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 0.75rem; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
            td {{ padding: 1rem 0.75rem; border-bottom: 1px solid #f1f5f9; }}
            .portal-tag {{ background: #f1f5f9; padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid #e2e8f0; font-size: 0.85rem; }}
            .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header><h1>🏛️ Memorial de Menções</h1><span class="counter">{len(todos)} Registros</span></header>
            <table><thead><tr><th>Data</th><th>Fonte</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table>
            <footer style="margin-top:20px; text-align:center; font-size:12px; color:gray;">Sincronizado via API em: {data_execucao}</footer>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
