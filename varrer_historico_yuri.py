#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   Varredura Histórica Profunda (2014-2026) — Yuri Almeida    ║
║   YLuna85 LABs — Clipping Engine                             ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import csv
import json
import re
import hashlib
from datetime import datetime
import requests
import feedparser

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from coletor_engine import (
    PASTA_DATA, CSV_FIELDNAMES, normalizar_url, extrair_portal,
    gerar_hash_url, extrair_ano, garantir_estrutura_pessoa_ano,
    carregar_hashes_existentes, consolidar_indice_geral, SERPER_API_KEY
)

YURI_OBJ = {
    "id": "yuri_almeida",
    "pasta": "yuri_almeida",
    "nome_busca": "Yuri de Oliveira Luna e Almeida",
    "nome_exibicao": "Yuri Almeida",
    "variacoes": [
        "Yuri de Oliveira Luna e Almeida",
        "Yuri Luna",
        "Yuri Almeida"
    ]
}

def buscar_web_historica_yuri():
    mencoes_coletadas = []
    print("[*] Iniciando busca histórica web (Google / Serper / DOU / Google News) para Yuri Almeida (2014 a 2026)...")
    
    # 1. Google News RSS por variações
    for var in YURI_OBJ["variacoes"]:
        try:
            from urllib.parse import quote
            termo_enc = quote(var)
            url_rss = f"https://news.google.com/rss/search?q={termo_enc}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
            feed = feedparser.parse(url_rss)
            for entry in feed.entries:
                data_pub = entry.get('published', '') or datetime.now().strftime('%Y-%m-%d')
                mencoes_coletadas.append({
                    'Titulo': entry.get('title', ''),
                    'Link': entry.get('link', ''),
                    'Fonte': 'Google News RSS',
                    'Data_Coleta': data_pub
                })
        except Exception as e:
            print(f"[!] Erro RSS: {e}")
            
    # 2. Serper API por Anos (2014 a 2026)
    if SERPER_API_KEY:
        print("[*] SERPER_API_KEY detectada. Executando buscas parametrizadas por ano (2014 a 2026)...")
        for ano in range(2014, 2027):
            for var in ["Yuri de Oliveira Luna e Almeida", "Yuri Luna IF Baiano"]:
                query = f'"{var}" {ano}'
                url_serper = "https://google.serper.dev/search"
                payload = json.dumps({"q": query, "gl": "br", "hl": "pt-br", "num": 10})
                headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
                try:
                    res = requests.post(url_serper, headers=headers, data=payload, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        for item in data.get('organic', []):
                            snippet = item.get('snippet', '')
                            dt_str = f"{ano}-01-01 00:00:00"
                            mencoes_coletadas.append({
                                'Titulo': item.get('title', ''),
                                'Link': item.get('link', ''),
                                'Fonte': f'Google Search ({ano})',
                                'Data_Coleta': dt_str
                            })
                except Exception as e:
                    pass
                    
    return mencoes_coletadas

def escanear_portarias_locais_yuri():
    portarias_mencoes = []
    pasta_rsc = r"G:\Meu Drive\APP\3. Gestão e Atuação Profissional\3.7 TAEs - Carreira e Salarios\Portarias_Yuri\RSC YURI"
    
    if os.path.exists(pasta_rsc):
        print(f"[*] Escaneando acervo de portarias e documentos oficiais em {pasta_rsc}...")
        for file in os.listdir(pasta_rsc):
            if file.endswith(".pdf"):
                # Extrair ano da portaria
                match_ano = re.search(r'20\d{2}|19\d{2}', file)
                if match_ano:
                    ano = match_ano.group(0)
                else:
                    ano = "2014"
                    
                # Formatar nome limpo do título
                titulo_limpo = file.replace("EIXO_", "").replace("_", " ").replace(".pdf", "").strip()
                link_fake = f"file:///{os.path.join(pasta_rsc, file).replace('\\', '/')}"
                
                portarias_mencoes.append({
                    'Titulo': f"Portaria / Documento Oficial: {titulo_limpo}",
                    'Link': link_fake,
                    'Fonte': 'Boletim de Serviço / DOU (IF Baiano)',
                    'Data_Coleta': f"{ano}-06-01 00:00:00"
                })
                
    print(f"[+] Total de documentos oficiais locais de Yuri localizados: {len(portarias_mencoes)}")
    return portarias_mencoes

def salvar_historico_yuri(mencoes: list):
    mencoes_por_ano = {}
    salvas = 0
    
    for item in mencoes:
        link = item.get('Link')
        if not link:
            continue
        hash_id = gerar_hash_url(link)
        ano_str = extrair_ano(item.get('Data_Coleta'))
        
        # Validação do intervalo 2014-2026
        try:
            val_ano = int(ano_str)
            if val_ano < 2014 or val_ano > 2026:
                val_ano = 2014
                ano_str = "2014"
        except Exception:
            ano_str = "2014"
            
        if ano_str not in mencoes_por_ano:
            mencoes_por_ano[ano_str] = {
                'existentes': carregar_hashes_existentes(YURI_OBJ['pasta'], ano_str),
                'itens': []
            }
            
        if hash_id not in mencoes_por_ano[ano_str]['existentes']:
            mencao_dict = {
                'Hash_ID': hash_id,
                'Data_Coleta': item.get('Data_Coleta', f"{ano_str}-01-01 00:00:00"),
                'Ano': ano_str,
                'Pessoa': YURI_OBJ['nome_exibicao'],
                'Fonte': item.get('Fonte', 'Documento Oficial'),
                'Portal': extrair_portal(link) if not link.startswith('file://') else 'Acervo Oficial IF Baiano',
                'Titulo': item.get('Titulo', 'Documento Oficial'),
                'Link': link
            }
            mencoes_por_ano[ano_str]['itens'].append(mencao_dict)
            mencoes_por_ano[ano_str]['existentes'].add(hash_id)
            salvas += 1
            
    for ano, dados in mencoes_por_ano.items():
        if not dados['itens']:
            continue
        csv_file, json_file = garantir_estrutura_pessoa_ano(YURI_OBJ['pasta'], ano)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            for it in dados['itens']:
                writer.writerow(it)
                
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existentes_json = json.load(f)
        except Exception:
            existentes_json = []
            
        existentes_json.extend(dados['itens'])
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(existentes_json, f, ensure_ascii=False, indent=2)
            
    return salvas

if __name__ == "__main__":
    print(f"=== INICIANDO VARREDURA HISTÓRICA PROFUNDA PARA {YURI_OBJ['nome_exibicao'].upper()} (2014 a 2026) ===")
    
    # 1. Coleta web histórica
    mencoes_web = buscar_web_historica_yuri()
    
    # 2. Coleta de portarias oficiais locais (2014 - 2026)
    mencoes_portarias = escanear_portarias_locais_yuri()
    
    # 3. Consolidar e Salvar
    total_coletado = mencoes_web + mencoes_portarias
    novas_salvas = salvar_historico_yuri(total_coletado)
    
    total_indice = consolidar_indice_geral()
    
    print(f"\n==================================================")
    print(f"VARREDURA DE YURI ALMEIDA CONCLUÍDA COM SUCESSO!")
    print(f"Novas Menções/Portarias Registradas: {novas_salvas}")
    print(f"Total de Menções no Índice Geral: {total_indice}")
    print(f"==================================================")
