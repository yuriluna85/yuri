# 🏛️ yuri-main — Memorial de Menções & Clipping Engine v4.0

Aplicação de monitoramento contínuo, busca histórica e clipping automatizado para **Yuri Almeida**, **Ana Gabriela** e **Rodrigo Neves**.

Projetada sob a arquitetura **Vibe Design** do YLuna85 LABs: backend assíncrono em Python (FastAPI + Coletor Multimotor) desacoplado de uma interface web SPA responsiva em Vanilla HTML5/CSS3 hospedada no **GitHub Pages**.

---

## 🚀 Novidades da Versão 4.0

1. **Estrutura de Dados Hierárquica (`data/{pessoa}/{ano}/`)**:
   - Organização automática por pessoa e subpastas de ano (`data/yuri_almeida/2026/mencoes_2026.csv`, `.json`).
   - Índice geral consolidado (`data/mencoes_index_geral.json`) indexando 315+ registros.
2. **API Local em FastAPI (`api_servidor.py`)**:
   - Servidor assíncrono na porta `8000` com endpoints REST para raspagem em segundo plano e sincronização automatizada com o GitHub.
3. **Agendamento Diário no GitHub Actions**:
   - Workflow `.github/workflows/rastreador.yml` reconfigurado para rodar **todos os dias às 06:10 AM BRT (09:10 UTC)**.
4. **Multimotores de Raspagem**:
   - Integração com Google Serper API, Google News RSS público, Bing RSS e Imprensa Nacional (DOU).
   - Deduplicação inteligente por Hash MD5 de URL normalizada.
5. **Interface Web Repaginada**:
   - Dark Mode oficial YLuna85 LABs, favicons institucionais, abas de seleção por Pessoa e filtro dinâmico por Ano.

---

## 🛠️ Como Executar Localmente

### 1. Iniciar a API Local FastAPI (Porta 8000)
```bash
python api_servidor.py
```
Acesse a documentação Swagger em: `http://127.0.0.1:8000/docs`

### 2. Executar Varredura Manual pelo Terminal (CLI)
```bash
# Varredura Diária 24h
python buscar_mencoes.py --modo diario

# Varredura Histórica Profunda (Anos Anteriores)
python buscar_mencoes.py --modo historico --paginas 10
```

---

## 📑 Log de Atualizações (Changelog)

- **03/08/2026 (v4.0.0)**:
  - Lançamento da arquitetura híbrida Vibe Design (FastAPI local + Bot GitHub Actions às 06:10 BRT).
  - Implementação da Skill `fastapi-api-builder`.
  - Reestruturação da pasta `data/` por pessoa e por ano.
  - Inclusão dos favicons YLuna85 LABs e visualização com filtros dinâmicos por ano no frontend.