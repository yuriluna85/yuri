#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   YURI-MAIN — Multi-Motor & Multi-Pessoa Clipping Engine     ║
║   Versão 3.0 — YLuna85 LABs                                  ║
║   Busca no Google (Serper), Bing e DOU (Imprensa Nacional)   ║
║   Deduplicação Canônica Cross-Engine + Exportação CSV/JSON   ║
╚══════════════════════════════════════════════════════════════╝
"""

import csv
import json
import os
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse, urlunparse

import requests

# ── Configurações de Pessoas e Caminhos ───────────────────────
PASTA_DATA = 'data'
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

PESSOAS_MONITORADAS = [
    {
        "id": "yuri_luna",
        "nome_busca": "Yuri de Oliveira Luna e Almeida",
        "nome_exibicao": "Yuri Luna",
        "csv_path": os.path.join(PASTA_DATA, 'mencoes_yuri_luna.csv')
    },
    {
        "id": "ana_gabriela",
        "nome_busca": "Ana Gabriela dos Santos Barbosa",
        "nome_exibicao": "Ana Gabriela",
        "csv_path": os.path.join(PASTA_DATA, 'mencoes_ana_gabriela.csv')
    },
    {
        "id": "rodrigo_neves",
        "nome_busca": "Rodrigo Neves Araújo",
        "nome_exibicao": "Rodrigo Neves",
        "csv_path": os.path.join(PASTA_DATA, 'mencoes_rodrigo_neves.csv')
    }
]

JSON_CONSOLIDADO = os.path.join(PASTA_DATA, 'mencoes_consolidado.json')
CSV_FIELDNAMES = ['Data_Coleta', 'Pessoa', 'Fonte', 'Portal', 'Titulo', 'Link']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

os.makedirs(PASTA_DATA, exist_ok=True)


# ── Utilitários de Normalização e Deduplicação ───────────────
def normalizar_url(url: str) -> str:
    """Normaliza URL para comparação canônica unificada."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        scheme = "https"
        netloc = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        return f"{scheme}://{netloc}{path}"
    except Exception:
        return url.strip().lower()


def extrair_portal(url: str) -> str:
    """Extrai o nome amigável do portal da URL."""
    try:
        netloc = urlparse(url).netloc.lower().replace("www.", "")
        return netloc if netloc else "Portal Web"
    except Exception:
        return "Portal Web"


# ── Motores de Varredura ──────────────────────────────────────
def buscar_google_serper(nome: str, max_pages: int = 3) -> list:
    """Busca no Google via Serper.dev com paginação histórica."""
    resultados = []
    if not SERPER_API_KEY:
        print("[!] SERPER_API_KEY nao configurada no ambiente. Pulando Google.")
        return resultados

    url = "https://google.serper.dev/search"
    for page in range(1, max_pages + 1):
        payload = json.dumps({
            "q": f'"{nome}"',
            "gl": "br",
            "hl": "pt-br",
            "autocorrect": False,
            "page": page
        })
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        try:
            r = requests.post(url, headers=headers, data=payload, timeout=20)
            if r.status_code == 200:
                data = r.json()
                for item in data.get('organic', []):
                    link = item.get('link')
                    title = item.get('title', 'Menção em artigo/página web')
                    if link:
                        resultados.append({
                            'fonte': 'Google',
                            'titulo': title,
                            'link': link
                        })
            else:
                break
        except Exception as e:
            print(f"❌ Erro busca Google (Pág {page}): {e}")
            break
    return resultados


def buscar_dou_oficial(nome: str) -> list:
    """Busca nativa no Diário Oficial da União (in.gov.br)."""
    resultados = []
    url = f'https://www.in.gov.br/consulta/-/buscar/dou?q="{requests.utils.quote(nome)}"&s=todos&exactDate=all&sortType=0'
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code == 200:
            marker = '_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params'
            idx = r.text.find(marker)
            if idx != -1:
                start_json = r.text.find('{', idx)
                end_json = r.text.find('</script>', start_json)
                json_str = r.text[start_json:end_json].strip()
                data = json.loads(json_str)
                for item in data.get('jsonArray', []):
                    title = item.get('title', 'Publicação no Diário Oficial da União')
                    url_title = item.get('urlTitle', '')
                    pub_date = item.get('pubDate', '')
                    full_link = f"https://www.in.gov.br/web/dou/-/{url_title}" if url_title else ""
                    if full_link:
                        resultados.append({
                            'fonte': 'DOU',
                            'titulo': f"{title} ({pub_date})" if pub_date else title,
                            'link': full_link
                        })
    except Exception as e:
        print(f"❌ Erro busca DOU para {nome}: {e}")
    return resultados


def buscar_bing_search(nome: str) -> list:
    """Busca complementar no Bing Search."""
    resultados = []
    url = f"https://www.bing.com/search?q=%22{requests.utils.quote(nome)}%22"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            links = re.findall(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', r.text)
            for link, raw_title in links:
                if 'bing.com' not in link and 'microsoft.com' not in link:
                    clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                    resultados.append({
                        'fonte': 'Bing',
                        'titulo': clean_title if clean_title else 'Publicação na Web (Bing)',
                        'link': link
                    })
    except Exception as e:
        print(f"[-] Erro busca Bing para {nome}: {e}")
    return resultados


# ── Processamento Principal ───────────────────────────────────
def processar_varredura():
    data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')
    print(f"\n==================================================")
    print(f" [!] INICIANDO VARREDURA MULTI-MOTOR -- {data_hoje}")
    print(f"==================================================\n")

    todos_registros_consolidados = []

    for pessoa in PESSOAS_MONITORADAS:
        nome_busca = pessoa['nome_busca']
        nome_exib = pessoa['nome_exibicao']
        csv_file = pessoa['csv_path']

        print(f"Processando: {nome_exib} ({nome_busca})...")

        # 1. Carrega links já existentes para a pessoa
        links_existentes_norm = set()
        registros_pessoa = []

        if os.path.exists(csv_file):
            with open(csv_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    registros_pessoa.append(r)
                    url_norm = normalizar_url(r.get('Link', ''))
                    if url_norm:
                        links_existentes_norm.add(url_norm)

        # 2. Executa a varredura nas 3 fontes
        res_dou = buscar_dou_oficial(nome_busca)
        res_google = buscar_google_serper(nome_busca, max_pages=3)
        res_bing = buscar_bing_search(nome_busca)

        # Combina mantendo prioridade: DOU > Google > Bing
        todos_novos_candidatos = res_dou + res_google + res_bing
        novos_adicionados = 0

        for item in todos_novos_candidatos:
            link = item['link']
            url_norm = normalizar_url(link)

            if url_norm and url_norm not in links_existentes_norm:
                links_existentes_norm.add(url_norm)
                novo_reg = {
                    'Data_Coleta': data_hoje,
                    'Pessoa': nome_exib,
                    'Fonte': item['fonte'],
                    'Portal': extrair_portal(link),
                    'Titulo': item['titulo'],
                    'Link': link
                }
                registros_pessoa.append(novo_reg)
                novos_adicionados += 1
                print(f"  + Novo [{item['fonte']}]: {link[:80]}...")

        # 3. Salva CSV individual atualizado
        with open(csv_file, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(registros_pessoa)

        print(f"  [OK] {nome_exib}: {len(registros_pessoa)} registros totais (+{novos_adicionados} novos).\n")
        todos_registros_consolidados.extend(registros_pessoa)

    # 4. Gera JSON consolidado para renderização estática ultra-rápida
    # Ordena do mais recente para o mais antigo
    todos_registros_consolidados.sort(key=lambda x: x.get('Data_Coleta', ''), reverse=True)

    with open(JSON_CONSOLIDADO, mode='w', encoding='utf-8') as f:
        json.dump({
            "ultima_atualizacao": data_hoje,
            "total_registros": len(todos_registros_consolidados),
            "registros": todos_registros_consolidados
        }, f, ensure_ascii=False, indent=2)

    print(f"==================================================")
    print(f" [OK] VARREDURA CONCLUIDA")
    print(f" [OK] JSON Consolidado salvo com {len(todos_registros_consolidados)} registros.")
    print(f"==================================================\n")

if __name__ == "__main__":
    processar_varredura()
