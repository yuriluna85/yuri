import csv
import os
import time
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações de Identidade e Caminhos
NOME_ALVO = "Yuri de Oliveira Luna e Almeida"
QUERY_BUSCA = "Yuri de Oliveira Luna e Almeida" # Sem aspas para busca ampla

# Definição do Path conforme sua instrução
PASTA_DATA = 'data'
CSV_FILE = os.path.join(PASTA_DATA, 'mencoes.csv')
HTML_FILE = 'index.html'

# Garante que a pasta 'data' exista antes de qualquer operação
os.makedirs(PASTA_DATA, exist_ok=True)

# 1. Carregamento do Histórico para evitar duplicatas
links_existentes = set()
primeira_execucao = not os.path.exists(CSV_FILE)

if not primeira_execucao:
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

lista_para_salvar = [] # Lista que alimentará o CSV final
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')
limite_resultados = 150 if primeira_execucao else 40

print(f"--- 🔎 INICIANDO RASTREAMENTO: {NOME_ALVO} ---")

try:
    # Aumentamos o 'pause' para 10s para reduzir o risco de bloqueio de IP no GitHub
    # advanced=True permite validar Título e Descrição (Snippet)
    resultados = search(QUERY_BUSCA, num_results=limite_resultados, lang="pt", advanced=True, pause=10.0)
    
    for res in resultados:
        # Lógica de Double-Check: O nome deve estar no título, na descrição ou na URL
        texto_completo = f"{res.title} {res.description} {res.url}".lower()
        
        if NOME_ALVO.lower() in texto_completo:
            if res.url not in links_existentes:
                portal = urlparse(res.url).netloc.replace('www.', '')
                lista_para_salvar.append({
                    'Data': data_execucao,
                    'Portal': portal,
                    'Link': res.url
                })
                print(f"✅ VALIDADO: {res.url}")
        else:
            # Log para acompanhamento no Actions de resultados ignorados
            print(f"➖ Ignorado (Homônimo/Parcial): {res.url}")

except Exception as e:
    print(f"❌ ERRO DURANTE A BUSCA: {e}")

# 2. Persistência no Arquivo data/mencoes.csv
if primeira_execucao or lista_para_salvar:
    # Se for a primeira vez, cria com header. Se não, apenas anexa.
    modo = 'w' if primeira_execucao else 'a'
    with open(CSV_FILE, mode=modo, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if primeira_execucao:
            writer.writeheader()
        writer.writerows(lista_para_salvar)
    print(f"📊 Arquivo {CSV_FILE} atualizado com {len(lista_para_salvar)} novos itens.")
else:
    print("ℹ️ Nenhuma nova menção encontrada para atualizar o CSV.")

# 3. Geração do Painel HTML (Recria sempre para refletir o CSV atual)
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        mencoes_totais = list(csv.DictReader(f))
        mencoes_totais.reverse() # Mais recentes no topo

    rows_html = ""
    for item in mencoes_totais:
        rows_html += f"""
        <tr>
            <td>{item['Data']}</td>
            <td><span class="portal-tag">{item['Portal']}</span></td>
            <td><a href="{item['Link']}" target="_blank" class="btn-link">Ver Link ↗</a></td>
        </tr>"""

    html_content = f"""
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
            .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 500; border: 1px solid #dbeafe; padding: 5px 10px; border-radius: 5px; }}
            footer {{ margin-top: 2rem; font-size: 0.8rem; color: #94a3b8; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏛️ Memorial de Menções</h1>
                <span class="counter">{len(mencoes_totais)} Registros</span>
            </header>
            <table>
                <thead><tr><th>Identificação</th><th>Fonte</th><th>Ação</th></tr></thead>
                <tbody>{rows_html if rows_html else "<tr><td colspan='3'>Aguardando dados...</td></tr>"}</tbody>
            </table>
            <footer>Sincronizado em: {data_execucao}</footer>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("✅ Painel index.html atualizado.")
