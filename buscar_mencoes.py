#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   YURI-MAIN — Ponto de Entrada CLI para GitHub Actions        ║
║   Versão 4.0 — YLuna85 LABs                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import argparse
from coletor_engine import executar_varredura

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clipping Engine yuri-main")
    parser.add_argument("--modo", choices=["diario", "historico"], default="diario", help="Modo de varredura")
    parser.add_argument("--paginas", type=int, default=5, help="Quantidade de páginas de busca")
    args = parser.parse_args()

    print(f"[*] Executando clipping yuri-main v4.0 no modo '{args.modo}'...")
    executar_varredura(modo=args.modo, max_paginas=args.paginas)
