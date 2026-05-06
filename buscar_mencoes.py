import csv
import os
import time
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações - Sem aspas internas para dar maior volume de resultados
NOME_BUSCA = 'Yuri de Oliveira Luna e Almeida'
PASTA_DADOS = 'data'
CSV_FILE = f'{PASTA_DADOS}/mencoes.csv'
HTML_FILE = 'index.html'

# Garante a criação da pasta data
os.makedirs(PASTA_DADOS, exist_ok=True)

primeira_execucao = not os.path.exists(CSV_FILE)
# Na primeira execução pede mais resultados para formar o histórico
limite_busca = 100 if primeira_execucao else 20

links_existentes = set()
if not primeira_execucao:
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"--- INICIANDO RASTREAMENTO ---")
print(f"Termo de busca: {NOME_BUSCA}")

try:
    # O pause=5.0 é essencial para não tomar bloqueio instantâneo do Google
    resultados = search(
        NOME_BUSCA, 
        num_results=limite_busca, 
        lang="pt", 
        pause=5.0
    )
    
    for url in resultados:
        if url not in links_existentes:
            portal = urlparse(url).netloc.replace('www.', '')
            novas_mencoes.append({
                'Data': data_execucao,
                'Portal': portal,
                'Link': url
            })
            print(f"Novo link catalogado: {url}")
except Exception as e:
    print(f"❌ ERRO NA BUSCA DO GOOGLE: {e}")

# Lógica de salvamento no CSV
if primeira_execucao or novas_mencoes:
    modo = 'w' if primeira_execucao else 'a'
    with open(CSV_FILE, mode=modo, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if primeira_execucao:
            writer.writeheader()
        writer.writerows(novas_mencoes)
    print(f"✅ Arquivo CSV atualizado com {len(novas_mencoes)} links.")
else:
    print("ℹ️ Nenhuma novidade encontrada nesta rodada.")

# Lógica de atualização do HTML
if primeira_execucao or novas_mencoes or not os.path.exists(HTML_FILE):
    dados = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            dados = list(csv.DictReader(f))
            dados.reverse()

    rows = ""
    if dados:
        for item in dados:
            rows += f"""
            <tr>
                <td>{item['Data']}</td>
                <td><span class="portal-tag">{item['Portal']}</span></td>
                <td><a href="{item['Link']}" target="_blank" class="btn-link">Ver Menção ↗</a></td>
            </tr>"""
    else:
        rows = "<tr><td colspan='3' style='text-align: center;'>Nenhum resultado processado ainda.</td></tr>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memorial de Menções | Yuri Almeida</title>
        <style>
            :root {{ --primary: #2563eb; --bg: #f8fafc; --text: #1e293b; }}
            body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #e2e8f0; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; padding-bottom: 1rem; }}
            .counter {{ background: #dbeafe; color: var(--primary); padding: 0.3rem 0.8rem; border-radius: 999px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 0.75rem; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
            td {{ padding: 1rem 0.75rem; border-bottom: 1px solid #f1f5f9; }}
            .portal-tag {{ background: #f1f5f9; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.85rem; border: 1px solid #e2e8f0; }}
            .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 500; }}
            footer {{ margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏛️ Memorial de Menções</h1>
                <span class="counter">{len(dados)} Registros</span>
            </header>
            <table>
                <thead><tr><th>Data de Identificação</th><th>Portal/Origem</th><th>Acesso</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <footer>Última varredura pelo robô: {data_execucao}</footer>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("✅ Painel HTML gerado com sucesso.")
