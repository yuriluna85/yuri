import csv
import os
import requests
import json
from datetime import datetime
from urllib.parse import urlparse

# Configurações de Identidade e Caminhos
NOME_ALVO = "Yuri de Oliveira Luna e Almeida"
PASTA_DATA = 'data'
CSV_FILE = os.path.join(PASTA_DATA, 'mencoes.csv')
HTML_FILE = 'index.html'

# Pega a chave da API do Serper.dev nos Secrets do GitHub
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

# Garante que a pasta 'data' exista
os.makedirs(PASTA_DATA, exist_ok=True)

def buscar_na_api():
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": f'"{NOME_ALVO}"',
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

# --- 1. CARREGAMENTO E BUSCA ---
links_existentes = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Usamos o link como chave única para evitar duplicados
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"--- 📡 INICIANDO VARREDURA ---")

try:
    dados_api = buscar_na_api()
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
            print(f"✅ Nova menção encontrada: {link}")

except Exception as e:
    print(f"❌ Erro ao acessar a API: {e}")

# --- 2. ATUALIZAÇÃO DO CSV (INCREMENTAL) ---
# Se for a primeira vez, cria com cabeçalho. Se não, anexa o que for novo.
if novas_mencoes:
    arquivo_existe = os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if not arquivo_existe:
            writer.writeheader()
        writer.writerows(novas_mencoes)
    print(f"📊 CSV atualizado com {len(novas_mencoes)} novos registros.")
elif not os.path.exists(CSV_FILE):
    # Se não achou nada e o arquivo nem existe, cria pelo menos o cabeçalho
    with open(CSV_FILE, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        writer.writeheader()

# --- 3. GERAÇÃO DO HTML (ESTÁTICO) ---
# Aqui o Python "vai atrás" do arquivo data/mencoes.csv para ler TUDO o que já foi salvo
todos_registros = []
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        todos_registros = list(csv.DictReader(f))
        # Inverte para que as menções mais recentes fiquem no topo
        todos_registros.reverse()

print(f"📋 Gerando Dashboard com {len(todos_registros)} registros totais.")

# Constrói as linhas da tabela
rows_html = ""
for item in todos_registros:
    # Garante que os campos existem antes de montar a linha
    data = item.get('Data', 'N/A')
    portal = item.get('Portal', 'Site Desconhecido')
    link = item.get('Link', '#')
    
    rows_html += f"""
    <tr>
        <td>{data}</td>
        <td><span class="portal-tag">{portal}</span></td>
        <td><a href="{link}" target="_blank" class="btn-link">Acessar Menção ↗</a></td>
    </tr>"""

# Template do Dashboard
html_content = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memorial de Menções | Yuri Almeida</title>
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text: #1e293b; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; margin: 0; }}
        .container {{ max-width: 950px; margin: 0 auto; background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
        header {{ border-bottom: 2px solid #f1f5f9; margin-bottom: 2rem; padding-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}
        .counter {{ background: #dbeafe; color: var(--primary); padding: 0.4rem 1rem; border-radius: 999px; font-weight: 700; font-size: 0.875rem; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ padding: 1rem; border-bottom: 2px solid #f1f5f9; font-size: 0.75rem; text-transform: uppercase; color: #64748b; }}
        td {{ padding: 1.25rem 1rem; border-bottom: 1px solid #f8fafc; font-size: 0.95rem; }}
        .portal-tag {{ background: #f1f5f9; padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.8rem; color: #475569; border: 1px solid #e2e8f0; }}
        .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 600; border: 1px solid #dbeafe; padding: 0.4rem 0.8rem; border-radius: 6px; }}
        .btn-link:hover {{ background: var(--primary); color: white; }}
        footer {{ margin-top: 3rem; font-size: 0.8rem; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏛️ Memorial de Menções</h1>
            <span class="counter">{len(todos_registros)} Registros Catalogados</span>
        </header>
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Fonte / Portal</th>
                    <th>Acesso</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else "<tr><td colspan='3' style='text-align:center;'>Aguardando primeira sincronização...</td></tr>"}
            </tbody>
        </table>
        <footer>
            <strong>Monitoramento em tempo real:</strong> {NOME_ALVO}<br>
            Última atualização: {data_execucao}
        </footer>
    </div>
</body>
</html>
"""

# Salva o arquivo HTML final na raiz do repositório
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ Dashboard index.html gerado com sucesso.")
