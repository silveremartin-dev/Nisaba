# Nisaba: High-Performance Computational Engine for Sumerian Cuneiform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/duckdb-1.1+-yellow.svg)](https://duckdb.org/)
[![Apache Arrow / Parquet](https://img.shields.io/badge/parquet-columnar-green.svg)](https://arrow.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

High-throughput computational engine, streaming compiler, and data pipeline for ancient Sumerian cuneiform epigraphy. Transforms 140,000+ unstructured archival text dumps (CDLI ATF) into typed relational databases (DuckDB / Apache Parquet), audits morphosyntactic consistency, dates undated tablets via prosopography, and discovers virtual joins across dispersed museum collections.

---

## 🏛️ System Architecture

```
                      Raw CDLI ATF Stream (~150 MB)
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Streaming Lexer   │
                        │     & AST Parser    │
                        └──────────┬──────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
         tablets.parquet                     lines.parquet
                 │                                   │
                 ▼                                   ▼
           DuckDB Engine ◄──────────────────── signs.parquet
                 │
                 ├─────────────────┬─────────────────┬─────────────────┐
                 ▼                 ▼                 ▼                 ▼
          Linter Engine      Chronos-Graph      Joins-Finder     Ledger-Auditor
          (Syntax Audit)     (Date Solver)     (k-mer Match)     (Double Entry)
                 │                 │                 │                 │
                 └─────────────────┴────────┬────────┴─────────────────┘
                                            ▼
                              Tablet Visual Explorer (HTML)
```

---

## ⚡ Key Features

1. **Streaming ATF Compiler to Apache Parquet & DuckDB**:
   - Compiles loose, non-standardized CDLI ASCII Transliteration Format (`.atf`) files into strictly typed, zero-loss columnar tables (`tablets`, `lines`, `signs`).
   - Queryable in microsecond speeds using standard SQL via embedded DuckDB.

2. **Deterministic Morphosyntactic & Bracket Linter**:
   - Mathematical parity verification for square brackets `[]`, angle brackets `<>`, parentheses `()`, and determinative braces `{}`.
   - Orthographic auditor flagging illegal subscript underscores (`gu_4` -> `gu4`), malformed compound signs (`|A.EDIN|`), and unseparated numerals.

3. **Chronos-Graph — Macro-Chronology Solver**:
   - Ur III royal year formula normalizer covering Shulgi, Amar-Suen, Shu-Suen, and Ibbi-Suen.
   - Bayesian temporal constraint propagation across co-occurring officials (`ki...-ta`, `i3-dab5`, `kiszib3`), seal legends, and administrative months to assign probabilistic dates to undated tablets.

4. **Fragment Joiner & Alignment Engine**:
   - Sliding $k$-mer indexer with MinHash / Jaccard similarity metrics.
   - Detects prospective physical joins across broken tablet edges and identifies duplicate administrative series across international museums.

5. **Ur III Economic Ledger Auditor**:
   - Extracts structured transaction records ($\langle \text{Quantity/Commodity}, \text{Source Party}, \text{Receiving Official}, \text{Action Type} \rangle$).
   - Calculates aggregated inflows, expenditures, and net inventory balances per administrative officer.

6. **Interactive Visual Tablet Explorer**:
   - Self-contained, responsive HTML application (`data/processed/browser.html`) with dark-mode theme, live search, color-coded syntax badges, Linter warnings, Chronos date cards, and official CDLI photo archive links.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 2. Run the Full End-to-End Pipeline
```bash
py src/pipeline.py --input data/raw/sample_cdli.atf --output_dir data/processed
```

### 3. Query the Compiled Corpus in DuckDB
```bash
py -c "import duckdb; con = duckdb.connect('data/processed/nisaba.duckdb'); print(con.execute('SELECT id_text, designation, line_count, has_date FROM tablets').df())"
```

### 4. Run Automated Test Suite (16 Tests Passing)
```bash
py -m pytest tests/ -v
```

### 5. Open the Interactive Visual Browser
Open `data/processed/browser.html` directly in any web browser to inspect tablets, transliterations, and analytical overlays.

---

## 📦 Processing the Entire 140,000 Tablet CDLI Corpus

To run Nisaba on the full worldwide corpus of published Sumerian cuneiform:

```bash
# 1. Download official CDLI unblocked dump (~150 MB)
py scripts/download_cdli_dump.py

# 2. Run batch pipeline across all 140,000 tablets
py scripts/run_full_corpus.py
```

---

## 📁 Repository Structure

```
Sumerian / Nisaba/
├── AGENTS.md                  # Developer & AI agent collaboration directives
├── PROJECT_STATE.md           # Engineering session memory & asset registry
├── README.md                  # Project overview, architecture & CLI guide
├── requirements.txt           # Python dependencies
├── .gitignore                 # Exclusion rules for large dumps & binaries
│
├── doc/
│   ├── ARCHITECTURE.md        # Technical specifications & mathematical models
│   └── CORPUS_TAXONOMY.md     # Ur III kings, metrology, calendar & commodities
│
├── data/
│   ├── raw/
│   │   └── sample_cdli.atf    # Representative CDLI ATF dataset
│   └── processed/
│       ├── nisaba.duckdb      # Mounted DuckDB database
│       ├── tablets.parquet    # Columnar tablet metadata
│       ├── lines.parquet      # Normalized lines & preservation flags
│       ├── signs.parquet      # Individual sign tokens & classifications
│       ├── chronos_estimates.parquet # Resolved dates for undated tablets
│       ├── transactions.parquet      # Extracted economic events
│       ├── officer_balances.parquet  # Net inventory per official
│       └── browser.html       # Standalone interactive visual browser
│
├── scripts/
│   ├── download_cdli_dump.py  # Automated CDLI bulk dump downloader
│   └── run_full_corpus.py     # Full corpus batch orchestrator
│
├── src/
│   ├── compiler/              # Streaming ATF lexer, AST parser & Parquet/DuckDB storage
│   ├── linter/                # Bracket balance & sign syntax validation
│   ├── chronos/               # Year normalizer, prosopography & date solver
│   ├── joins/                 # k-mer sequence alignment & virtual join matcher
│   ├── ledger/                # Double-entry transaction extractor & balance auditor
│   ├── browser/               # Standalone interactive HTML renderer
│   └── pipeline.py            # Central CLI entry point
│
└── tests/                     # 16 automated tests covering all modules
```

---

## 📄 License
This project is licensed under the MIT License.
