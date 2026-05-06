import csv
import os
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações
NOME_BUSCA = '"Yuri de Oliveira Luna e Almeida"'
CSV_FILE = 'mencoes.csv'
HTML_FILE = 'index.html'

# 1. Gerenciamento de Dados (CSV)
links_existentes = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"Iniciando busca para: {NOME_BUSCA}")

try:
    # Busca os primeiros 30 resultados (ajustável)
    for url in search(NOME_BUSCA, num=30, stop=30, pause=2.0):
        if url not in links_existentes:
            portal = urlparse(url).netloc.replace('www.', '')
            novas_mencoes.append({
                'Data': data_execucao,
                'Portal': portal,
                'Link': url
            })
except Exception as e:
    print(f"Erro na busca: {e}")

if novas_mencoes:
    arquivo_novo = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if arquivo_novo:
            writer.writeheader()
        writer.writerows(novas_mencoes)
    print(f"Sucesso: {len(novas_mencoes)} novas menções encontradas.")
else:
    print("Nenhuma menção inédita encontrada.")

# 2. Geração do Painel HTML
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        dados = list(csv.DictReader(f))
        dados.reverse() # Mais recentes no topo

    rows = ""
    for item in dados:
        rows += f"""
        <tr>
            <td>{item['Data']}</td>
            <td><span class="portal-tag">{item['Portal']}</span></td>
            <td><a href="{item['Link']}" target="_blank" class="btn-link">Ver Menção ↗</a></td>
        </tr>"""

    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memorial de Menções | Yuri Almeida</title>
        <style>
            :root {{ --primary: #2563eb; --bg: #f8fafc; --text: #1e293b; }}
            body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; margin: 0; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            header {{ border-bottom: 2px solid #e2e8f0; margin-bottom: 2rem; padding-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; }}
            h1 {{ margin: 0; font-size: 1.5rem; color: var(--primary); }}
            .counter {{ background: #dbeafe; color: var(--primary); padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: bold; font-size: 0.875rem; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 0.75rem; border-bottom: 2px solid #e2e8f0; font-size: 0.875rem; text-transform: uppercase; color: #64748b; }}
            td {{ padding: 1rem 0.75rem; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }}
            .portal-tag {{ background: #f1f5f9; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.85rem; color: #475569; border: 1px solid #e2e8f0; }}
            .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 500; }}
            .btn-link:hover {{ text-decoration: underline; }}
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
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Fonte/Portal</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <footer>Atualizado automaticamente via GitHub Actions em: {data_execucao}</footer>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
