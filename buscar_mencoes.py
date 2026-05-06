import csv
import os
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações
QUERY = '"Yuri de Oliveira Luna e Almeida"'
CSV_FILE = 'mencoes.csv'
HTML_FILE = 'index.html'

# 1. Busca e Atualização do CSV
links_existentes = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')

try:
    print(f"Buscando: {QUERY}")
    # Aumentei o range para garantir que pegamos tudo na primeira execução
    resultados = search(QUERY, num=30, stop=30, pause=2)
    for url in resultados:
        if url not in links_existentes:
            dominio = urlparse(url).netloc
            novas_mencoes.append({
                'Data_Descoberta': data_hoje,
                'Site_Portal': dominio,
                'Link': url
            })
except Exception as e:
    print(f"Erro na busca: {e}")

if novas_mencoes:
    arquivo_existe = os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data_Descoberta', 'Site_Portal', 'Link'])
        if not arquivo_existe:
            writer.writeheader()
        writer.writerows(novas_mencoes)

# 2. Geração do HTML (Painel de Monitoramento)
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        mencoes = list(csv.DictReader(f))
        mencoes.reverse() # Mais recentes primeiro

    rows_html = ""
    for item in mencoes:
        rows_html += f"""
        <tr>
            <td>{item['Data_Descoberta']}</td>
            <td><span class="badge">{item['Site_Portal']}</span></td>
            <td><a href="{item['Link']}" target="_blank">Abrir Menção &#8599;</a></td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memorial de Menções - Yuri Almeida</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .stats {{ margin-bottom: 20px; font-size: 0.9em; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f9f9f9; }}
            .badge {{ background: #e8f4fd; color: #3498db; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
            a {{ color: #3498db; text-decoration: none; font-weight: 500; }}
            a:hover {{ text-decoration: underline; }}
            footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏛️ Memorial de Menções</h1>
            <div class="stats">
                Monitoramento automatizado para: <strong>{QUERY}</strong><br>
                Total de menções indexadas: <strong>{len(mencoes)}</strong>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Data de Identificação</th>
                        <th>Portal / Origem</th>
                        <th>Acesso</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            <footer>
                Última atualização do robô: {data_hoje}
            </footer>
        </div>
    </body>
    </html>
    """

    with open(HTML_FILE, mode='w', encoding='utf-8') as f:
        f.write(html_content)
    print("Dashboard HTML atualizado!")
