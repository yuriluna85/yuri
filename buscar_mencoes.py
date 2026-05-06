import csv
import os
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações
NOME_BUSCA = '"Yuri de Oliveira Luna e Almeida"'
CSV_FILE = 'mencoes.csv'
HTML_FILE = 'index.html'

# 1. Verifica o Modo de Execução
primeira_execucao = not os.path.exists(CSV_FILE)
# Se for a primeira vez, busca mais a fundo. Se for diária, busca menos.
limite_busca = 150 if primeira_execucao else 30

# Lê os links existentes para não duplicar
links_existentes = set()
if not primeira_execucao:
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"Iniciando busca para: {NOME_BUSCA}")
print(f"Modo: {'Busca Geral (Primeira Execução)' if primeira_execucao else 'Varredura Diária'}")
print(f"Limite de resultados definidos: {limite_busca}")

try:
    for url in search(NOME_BUSCA, num_results=limite_busca, lang="pt"):
        if url not in links_existentes:
            portal = urlparse(url).netloc.replace('www.', '')
            novas_mencoes.append({
                'Data': data_execucao,
                'Portal': portal,
                'Link': url
            })
except Exception as e:
    print(f"Erro na busca: {e}")

# 2. Atualização Condicional do CSV
if novas_mencoes:
    with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if primeira_execucao:
            writer.writeheader()
        writer.writerows(novas_mencoes)
    print(f"Sucesso: {len(novas_mencoes)} novas menções salvas no CSV.")
else:
    print("Nenhuma menção inédita encontrada. O arquivo CSV foi mantido inalterado.")

# 3. Atualização Condicional do Painel HTML
# Só recria o arquivo HTML se encontramos links novos OU se o HTML sumiu/não existe
precisa_atualizar_html = bool(novas_mencoes) or not os.path.exists(HTML_FILE)

if precisa_atualizar_html and os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        dados = list(csv.DictReader(f))
        dados.reverse() # Coloca os mais recentes no topo da tabela

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
    print("Painel HTML gerado/atualizado com sucesso.")
else:
    print("Painel HTML mantido inalterado, pois não houve novas menções.")
