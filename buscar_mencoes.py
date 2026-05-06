import csv
import os
import time
from datetime import datetime
from googlesearch import search
from urllib.parse import urlparse

# Configurações de Identidade
NOME_ALVO = "Yuri de Oliveira Luna e Almeida"
# Busca ampla para o Google (sem aspas) para evitar bloqueios e aumentar alcance
QUERY_BUSCA = "Yuri de Oliveira Luna e Almeida"

# Caminhos de Arquivos
PASTA_DADOS = 'data'
CSV_FILE = f'{PASTA_DADOS}/mencoes.csv'
HTML_FILE = 'index.html'

# Garante que a estrutura de pastas exista
os.makedirs(PASTA_DADOS, exist_ok=True)

# 1. Gerenciamento de Histórico e Modo de Operação
primeira_execucao = not os.path.exists(CSV_FILE)
limite_resultados = 150 if primeira_execucao else 40

links_existentes = set()
if not primeira_execucao:
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links_existentes.add(row['Link'])

novas_mencoes = []
data_execucao = datetime.now().strftime('%d/%m/%Y %H:%M')

print(f"--- INICIANDO RASTREAMENTO COM DOUBLE-CHECK ---")
print(f"Termo na busca (Amplo): {QUERY_BUSCA}")
print(f"Filtro de Validação (Rigoroso): {NOME_ALVO}")

try:
    # advanced=True permite acessar .title e .description de cada resultado
    # pause=5.0 evita que o Google identifique o bot rapidamente
    resultados = search(
        QUERY_BUSCA, 
        num_results=limite_resultados, 
        lang="pt", 
        advanced=True, 
        pause=5.0
    )
    
    for res in resultados:
        # Prepara o texto para o Double-Check (Título + Descrição + URL)
        # Convertemos tudo para minúsculo para uma comparação justa
        texto_para_validar = f"{res.title} {res.description} {res.url}".lower()
        termo_obrigatorio = NOME_ALVO.lower()
        
        # O FILTRO: Só prossegue se o nome completo exato estiver presente
        if termo_obrigatorio in texto_para_validar:
            if res.url not in links_existentes:
                portal = urlparse(res.url).netloc.replace('www.', '')
                novas_mencoes.append({
                    'Data': data_execucao,
                    'Portal': portal,
                    'Link': res.url
                })
                print(f"✅ VALIDADO E CATALOGADO: {res.url}")
        else:
            # Opcional: log para debug no Actions (pode remover se preferir logs limpos)
            print(f"--- Descartado (Homônimo ou Parcial): {res.url}")

except Exception as e:
    print(f"❌ ERRO DURANTE A BUSCA: {e}")

# 2. Persistência de Dados (CSV)
if primeira_execucao or novas_mencoes:
    modo = 'w' if primeira_execucao else 'a'
    with open(CSV_FILE, mode=modo, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Data', 'Portal', 'Link'])
        if primeira_execucao:
            writer.writeheader()
        writer.writerows(novas_mencoes)
    print(f"✅ Processo concluído: {len(novas_mencoes)} novos registros validados.")
else:
    print("ℹ️ Nenhuma nova menção validada nesta varredura.")

# 3. Atualização do Painel Visual (HTML)
# Recria o dashboard se for a 1ª vez, se houver novidades ou se o arquivo sumiu
if primeira_execucao or novas_mencoes or not os.path.exists(HTML_FILE):
    historico_completo = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            historico_completo = list(csv.DictReader(f))
            historico_completo.reverse() # Mais recentes no topo

    rows_html = ""
    if historico_completo:
        for item in historico_completo:
            rows_html += f"""
            <tr>
                <td>{item['Data']}</td>
                <td><span class="portal-tag">{item['Portal']}</span></td>
                <td><a href="{item['Link']}" target="_blank" class="btn-link">Ver Menção ↗</a></td>
            </tr>"""
    else:
        rows_html = "<tr><td colspan='3' style='text-align: center; color: #94a3b8;'>Aguardando primeira detecção válida...</td></tr>"

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
            .container {{ max-width: 950px; margin: 0 auto; background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
            header {{ border-bottom: 2px solid #f1f5f9; margin-bottom: 2rem; padding-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; }}
            h1 {{ margin: 0; font-size: 1.75rem; color: var(--primary); letter-spacing: -0.025em; }}
            .counter {{ background: #dbeafe; color: var(--primary); padding: 0.4rem 1rem; border-radius: 999px; font-weight: 700; font-size: 0.875rem; }}
            table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            th {{ padding: 1rem; border-bottom: 2px solid #f1f5f9; font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; }}
            td {{ padding: 1.25rem 1rem; border-bottom: 1px solid #f8fafc; font-size: 0.95rem; }}
            .portal-tag {{ background: #f1f5f9; padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.8rem; color: #475569; border: 1px solid #e2e8f0; font-weight: 500; }}
            .btn-link {{ color: var(--primary); text-decoration: none; font-weight: 600; border: 1px solid #dbeafe; padding: 0.4rem 0.8rem; border-radius: 6px; transition: all 0.2s; }}
            .btn-link:hover {{ background: var(--primary); color: white; }}
            footer {{ margin-top: 3rem; font-size: 0.85rem; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 1.5rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏛️ Memorial de Menções</h1>
                <span class="counter">{len(historico_completo)} Menções Validadas</span>
            </header>
            <table>
                <thead>
                    <tr>
                        <th>Data da Identificação</th>
                        <th>Fonte / Portal</th>
                        <th>Link de Acesso</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            <footer>
                <strong>Monitoramento Ativo:</strong> {NOME_ALVO}<br>
                Última sincronização do robô: {data_execucao}
            </footer>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("✅ Painel HTML atualizado.")
