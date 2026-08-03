#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   YURI-MAIN — API Local em FastAPI                           ║
║   Versão 4.0 — YLuna85 LABs                                  ║
║   Porta Padrão: 8000                                         ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from coletor_engine import executar_varredura, PASTA_DATA, INDEX_GERAL_FILE, PESSOAS_MONITORADAS

app = FastAPI(
    title="yuri-main — API Engine de Menções & Clipping",
    description="API REST assíncrona local para raspagem histórica, sincronização e gestão de menções no YLuna85 LABs.",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

status_execucao = {
    "em_andamento": False,
    "ultima_execucao": None,
    "ultimo_resultado": None
}

def rodar_varredura_background(modo: str, paginas: int):
    global status_execucao
    status_execucao["em_andamento"] = True
    try:
        res = executar_varredura(modo=modo, max_paginas=paginas)
        status_execucao["ultimo_resultado"] = res
    except Exception as e:
        status_execucao["ultimo_resultado"] = {"erro": str(e)}
    finally:
        status_execucao["em_andamento"] = False

@app.get("/")
def read_root():
    return {
        "status": "online",
        "aplicacao": "yuri-main — Clipping Engine",
        "versao": "4.0.0",
        "documentacao": "/docs"
    }

@app.get("/api/status")
def get_status():
    total_mencoes = 0
    if os.path.exists(INDEX_GERAL_FILE):
        try:
            with open(INDEX_GERAL_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                total_mencoes = dados.get("total_mencoes", 0)
        except Exception:
            pass
            
    return {
        "status_servidor": "online",
        "execucao_em_andamento": status_execucao["em_andamento"],
        "ultimo_resultado": status_execucao["ultimo_resultado"],
        "total_mencoes_indexadas": total_mencoes,
        "pessoas_monitoradas": [p["nome_exibicao"] for p in PESSOAS_MONITORADAS]
    }

@app.post("/api/buscar-historico")
def disparar_busca_historica(background_tasks: BackgroundTasks, modo: str = Query("historico", enum=["diario", "historico"]), paginas: int = Query(5, ge=1, le=20)):
    if status_execucao["em_andamento"]:
        raise HTTPException(status_code=400, detail="Já existe uma varredura em andamento.")
        
    background_tasks.add_task(rodar_varredura_background, modo, paginas)
    return {
        "mensagem": f"Varredura no modo '{modo}' iniciada em segundo plano.",
        "paginas": paginas
    }

@app.get("/api/mencoes")
def listar_mencoes():
    if os.path.exists(INDEX_GERAL_FILE):
        try:
            with open(INDEX_GERAL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao ler índice: {e}")
    return {"total_mencoes": 0, "mencoes": []}

@app.post("/api/sincronizar-github")
def sincronizar_github():
    try:
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        cmd_git_add = ["git", "add", "data/"]
        subprocess.run(cmd_git_add, cwd=repo_dir, check=True)
        
        cmd_commit = ["git", "commit", "-m", "🤖 [Auto] Sincronização via API Local FastAPI"]
        subprocess.run(cmd_commit, cwd=repo_dir, capture_output=True)
        
        cmd_push = ["git", "push"]
        res_push = subprocess.run(cmd_push, cwd=repo_dir, capture_output=True, text=True)
        
        return {
            "status": "sucesso",
            "mensagem": "Dados de menções sincronizados com o GitHub com sucesso!",
            "output": res_push.stdout
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na sincronização Git: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_servidor:app", host="127.0.0.1", port=8000, reload=True)
