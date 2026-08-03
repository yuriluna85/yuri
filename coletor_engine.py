#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   YURI-MAIN — Multi-Motor & Multi-Pessoa Clipping Engine     ║
║   Versão 4.0 — YLuna85 LABs (Motor de Raspagem Híbrido)      ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import csv
import json
import re
import hashlib
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import requests
import feedparser

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DATA = os.path.join(BASE_DIR, 'data')
INDEX_GERAL_FILE = os.path.join(PASTA_DATA, 'mencoes_index_geral.json')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')

PESSOAS_MONITORADAS = [
    {
        "id": "yuri_almeida",
        "pasta": "yuri_almeida",
        "nome_busca": "Yuri de Oliveira Luna e Almeida",
        "nome_exibicao": "Yuri Almeida",
        "variacoes": ["Yuri de Oliveira Luna e Almeida", "Yuri Luna", "Yuri Almeida"]
    },
    {
        "id": "ana_gabriela",
        "pasta": "ana_gabriela",
        "nome_busca": "Ana Gabriela dos Santos Barbosa",
        "nome_exibicao": "Ana Gabriela",
        "variacoes": ["Ana Gabriela dos Santos Barbosa", "Ana Gabriela dos Santos", "Ana Gabriela Barbosa"]
    },
    {
        "id": "rodrigo_neves",
        "pasta": "rodrigo_neves",
        "nome_busca": "Rodrigo Neves Araújo",
        "nome_exibicao": "Rodrigo Neves",
        "variacoes": ["Rodrigo Neves Araújo", "Rodrigo Neves Araujo", "Rodrigo Neves"]
    }
]

CSV_FIELDNAMES = ['Hash_ID', 'Data_Coleta', 'Ano', 'Pessoa', 'Fonte', 'Portal', 'Titulo', 'Link']
HEADERS_HTTP = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 YLunaClipping/4.0'
}

def normalizar_url(url: str) -> str:
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
    try:
        netloc = urlparse(url).netloc.lower().replace("www.", "")
        return netloc if netloc else "Portal Web"
    except Exception:
        return "Portal Web"

def gerar_hash_url(url: str) -> str:
    url_norm = normalizar_url(url)
    return hashlib.md5(url_norm.encode('utf-8')).hexdigest()

def extrair_ano(data_str: str) -> str:
    if not data_str:
        return str(datetime.now().year)
    match = re.search(r'20\d{2}', str(data_str))
    if match:
        return match.group(0)
    return str(datetime.now().year)

def garantir_estrutura_pessoa_ano(pessoa_pasta: str, ano: str):
    pasta_ano = os.path.join(PASTA_DATA, pessoa_pasta, str(ano))
    os.makedirs(pasta_ano, exist_ok=True)
    csv_file = os.path.join(pasta_ano, f"mencoes_{ano}.csv")
    json_file = os.path.join(pasta_ano, f"mencoes_{ano}.json")
    
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            
    if not os.path.exists(json_file):
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
            
    return csv_file, json_file

def carregar_hashes_existentes(pessoa_pasta: str, ano: str) -> set:
    csv_file, json_file = garantir_estrutura_pessoa_ano(pessoa_pasta, ano)
    hashes = set()
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Hash_ID'):
                        hashes.add(row['Hash_ID'])
        except Exception:
            pass
    return hashes

def validar_homonimo_estrito(pessoa_id: str, titulo: str, link: str) -> bool:
    comb = f"{titulo} {link}".lower()
    
    if pessoa_id == 'ana_gabriela':
        proibidos = ['cantora', 'música', 'álbum', 'turnê', 'lulu santos', 'altas horas', 'bbb', 'ifood', 'cabilhas', 'becker', 'cidinho', 'porto', 'esquartejada', 'palmeirense', 'casamento', 'portugal', 'deputada', 'miss', 'trainee', 'carvalho']
        if any(p in comb for p in proibidos):
            return False
        validos = ['ana gabriela dos santos barbosa', 'ana gabriela dos santos', 'ana gabriela barbosa', 'ifbaiano', 'if baiano', 'uesb', 'gépraxis', 'gepraxis', 'pedagogia', 'educação', 'ensino', 'escola', 'estagio']
        return any(v in comb for v in validos)

    elif pessoa_id == 'rodrigo_neves':
        proibidos = ['niterói', 'niteroi', 'prefeito', 'pdt', 'eleição', 'rio de janeiro', 'preso', 'lava jato', 'lula', 'bope']
        if any(p in comb for p in proibidos):
            return False
        validos = ['rodrigo neves Araújo', 'rodrigo neves araujo', 'ifbaiano', 'if baiano', 'ifba', 'dou', 'diário oficial', 'portaria', 'professor', 'servidor']
        return any(v in comb for v in validos)

    elif pessoa_id == 'yuri_almeida':
        proibidos = ['jogador', 'futebol', 'crime', 'preso', 'homicídio', 'assassinado', 'mc yuri']
        if any(p in comb for p in proibidos):
            return False
        validos = ['yuri de oliveira luna e almeida', 'yuri de oliveira luna', 'yuri luna', 'yuri almeida', 'ifbaiano', 'if baiano', 'computação', 'ti', 'dou', 'portaria', 'observatorio', 'gépraxis', 'gepraxis']
        return any(v in comb for v in validos)

    return True

def salvar_mencoes(pessoa_obj: dict, novas_mencoes: list) -> int:
    salvas_total = 0
    mencoes_por_ano = {}
    
    for mencao in novas_mencoes:
        url_link = mencao.get('Link')
        if not url_link:
            continue
            
        titulo = mencao.get('Titulo', '')
        if not validar_homonimo_estrito(pessoa_obj['id'], titulo, url_link):
            continue

        hash_id = gerar_hash_url(url_link)
        ano = extrair_ano(mencao.get('Data_Coleta'))
        
        if ano not in mencoes_por_ano:
            mencoes_por_ano[ano] = {
                'existentes': carregar_hashes_existentes(pessoa_obj['pasta'], ano),
                'itens': []
            }
            
        if hash_id not in mencoes_por_ano[ano]['existentes']:
            mencao_dict = {
                'Hash_ID': hash_id,
                'Data_Coleta': mencao.get('Data_Coleta', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'Ano': ano,
                'Pessoa': pessoa_obj['nome_exibicao'],
                'Fonte': mencao.get('Fonte', 'Web Search'),
                'Portal': extrair_portal(url_link),
                'Titulo': mencao.get('Titulo', 'Sem Título'),
                'Link': url_link
            }
            mencoes_por_ano[ano]['itens'].append(mencao_dict)
            mencoes_por_ano[ano]['existentes'].add(hash_id)
            salvas_total += 1
            
    for ano, dados in mencoes_por_ano.items():
        if not dados['itens']:
            continue
        csv_file, json_file = garantir_estrutura_pessoa_ano(pessoa_obj['pasta'], ano)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            for item in dados['itens']:
                writer.writerow(item)
                
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                lista_existente = json.load(f)
        except Exception:
            lista_existente = []
            
        lista_existente.extend(dados['itens'])
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(lista_existente, f, ensure_ascii=False, indent=2)
            
    return salvas_total

def consolidar_indice_geral():
    todas_mencoes = []
    
    for pessoa in PESSOAS_MONITORADAS:
        pasta_pessoa = os.path.join(PASTA_DATA, pessoa['pasta'])
        if not os.path.exists(pasta_pessoa):
            continue
        for root, dirs, files in os.walk(pasta_pessoa):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                            if isinstance(dados, list):
                                todas_mencoes.extend(dados)
                    except Exception:
                        pass
                        
    hash_vistos = set()
    unicas = []
    for item in todas_mencoes:
        h = item.get('Hash_ID')
        if h and h not in hash_vistos:
            hash_vistos.add(h)
            unicas.append(item)
            
    unicas.sort(key=lambda x: str(x.get('Data_Coleta', '')), reverse=True)
    
    with open(INDEX_GERAL_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "ultima_atualizacao": datetime.now(timezone.utc).isoformat(),
            "total_mencoes": len(unicas),
            "mencoes": unicas
        }, f, ensure_ascii=False, indent=2)
        
    return len(unicas)

# ── Motores de Busca ──────────────────────────────────────────
def buscar_google_news_rss(termo: str) -> list:
    resultados = []
    try:
        from urllib.parse import quote
        termo_encoded = quote(termo)
        url_rss = f"https://news.google.com/rss/search?q={termo_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        feed = feedparser.parse(url_rss)
        for entry in feed.entries:
            resultados.append({
                'Titulo': entry.get('title', ''),
                'Link': entry.get('link', ''),
                'Fonte': 'Google News RSS',
                'Data_Coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
    except Exception as e:
        print(f"[!] Erro ao buscar Google News RSS para {termo}: {e}")
    return resultados

def buscar_google_serper(termo: str, paginas: int = 2) -> list:
    resultados = []
    if not SERPER_API_KEY:
        return resultados
    url = "https://google.serper.dev/search"
    for page in range(1, paginas + 1):
        payload = json.dumps({"q": f'"{termo}"', "gl": "br", "hl": "pt-br", "page": page})
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        try:
            res = requests.post(url, headers=headers, data=payload, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for item in data.get('organic', []):
                    resultados.append({
                        'Titulo': item.get('title', ''),
                        'Link': item.get('link', ''),
                        'Fonte': 'Google (Serper API)',
                        'Data_Coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
        except Exception:
            pass
    return resultados

def executar_varredura(modo: str = "diario", max_paginas: int = 5) -> dict:
    resumo = {}
    print(f"[*] Iniciando Varredura de Menções (Modo: {modo.upper()})...")
    
    for pessoa in PESSOAS_MONITORADAS:
        print(f"[->] Monitorando: {pessoa['nome_exibicao']}")
        mencoes_coletadas = []
        
        for variacao in pessoa['variacoes']:
            rss_res = buscar_google_news_rss(variacao)
            mencoes_coletadas.extend(rss_res)
            
            if SERPER_API_KEY:
                serper_res = buscar_google_serper(variacao, paginas=max_paginas if modo == "historico" else 2)
                mencoes_coletadas.extend(serper_res)
                
        novas_salvas = salvar_mencoes(pessoa, mencoes_coletadas)
        resumo[pessoa['id']] = novas_salvas
        print(f"    [+] Novas menções salvas para {pessoa['nome_exibicao']}: {novas_salvas}")
        
    total_index = consolidar_indice_geral()
    print(f"[*] Varredura concluída. Total de menções consolidadas no índice: {total_index}")
    return {"resumo_novas": resumo, "total_indice": total_index}

if __name__ == "__main__":
    modo_input = sys.argv[1] if len(sys.argv) > 1 else "diario"
    executar_varredura(modo=modo_input)
