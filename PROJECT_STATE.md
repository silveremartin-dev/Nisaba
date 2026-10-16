# PROJECT_STATE.md — Nisaba Engineering Session Memory & Asset Registry

## 📌 1. Project Overview & Architectural Mission

* **Repository:** `https://github.com/silveremartin-dev/Nisaba`
* **Local Workspace:** `C:\Silvere\Encours\Developpement\Sumerian`
* **Mission:** High-performance computational engine and data pipeline for Sumerian cuneiform epigraphy, compiling legacy CDLI ATF text archives into certified Apache Parquet / DuckDB databases, auditing morphosyntax, resolving undated tablets via prosopography, and discovering cross-collection fragment joins.

---

## 🚀 2. Current Implementation Status

### Completed Core Engines
1. **Core ATF Streaming Lexer & Parser (`src/compiler/`)**:
   - `lexer.py`: Zero-copy generator tokenizing `&P`, surfaces, lines, comments, and structure markers.
   - `parser.py`: AST model decomposing tablets into lines, metrological signs, damage markers (`#`, `?`, `!`, `[]`), and logograms.
   - `storage.py`: Columnar **Apache Parquet** table generator (`tablets.parquet`, `lines.parquet`, `signs.parquet`) mounted into an embedded **DuckDB** instance (`data/processed/nisaba.duckdb`).
2. **Deterministic Morphosyntactic Linter (`src/linter/`)**:
   - `bracket_auditor.py`: Strict parity and nesting auditor for `[]`, `<>`, `()`, and `{}` semantic determinatives.
   - `sign_validator.py`: Flags illegal subscript notations (`gu_4`), malformed compound signs (`|A.EDIN|`), and merged numbers (`5udu`).
   - `engine.py`: Corpus-wide audit runner producing structured `LinterReport` DataFrames.
3. **Macro-Chronology Solver (`src/chronos/`)**:
   - `year_names.py`: Canonical Ur III royal formula catalog covering Shulgi, Amar-Suen, Shu-Suen, and Ibbi-Suen.
   - `prosopography.py`: Extracts officials (`ki ... -ta`, `i3-dab5`, `kiszib3`), seal legends, and administrative months.
   - `solver.py`: Propagates temporal constraints along entity co-occurrence networks to infer missing dates for undated tablets with confidence scores.
4. **Virtual Fragment Joiner (`src/joins/`)**:
   - `kmer.py`: Character and token $k$-mer sliding window indexer with Jaccard similarity metrics.
   - `matcher.py`: All-against-all sequence alignment discovering complementary broken tablet edges and duplicate scribal series.
5. **Ur III Economic Ledger Auditor (`src/ledger/`)**:
   - `extractor.py`: Extracts double-entry transactions (quantities, commodities, source and receiving officials, action types).
   - `auditor.py`: Computes aggregated inflows, expenditures, and net inventory balances per administrative officer.
6. **Tablet Visual Explorer (`src/browser/`)**:
   - `renderer.py`: Compiles an interactive, standalone HTML web application (`data/processed/browser.html`) with dark-mode UI, live P-number search, color-coded transliteration badges, Linter findings, Chronos dates, and CDLI photo links.
7. **Pipeline Orchestrator (`src/pipeline.py`)**:
   - Unified CLI running the full pipeline end-to-end.

---

## 🧪 3. Test Suite Verification

* **Framework:** `pytest`
* **Test Count:** **16 passing tests** across 8 test suites:
  - `tests/test_lexer.py` (2 tests)
  - `tests/test_parser.py` (2 tests)
  - `tests/test_storage.py` (1 test)
  - `tests/test_linter.py` (3 tests)
  - `tests/test_chronos.py` (2 tests)
  - `tests/test_joins.py` (2 tests)
  - `tests/test_ledger.py` (1 test)
  - `tests/test_browser.py` (1 test)
  - `tests/test_pipeline.py` (1 test)
  - `tests/test_taxonomy.py` (3 tests)
* **Status:** 100% Green (`16 passed in 5.4s`).

---

## 📁 4. Certified Artifacts on Disk

| File Path | Description |
| :--- | :--- |
| `data/raw/sample_cdli.atf` | 7 authentic CDLI tablets covering all administrative scenarios |
| `data/processed/nisaba.duckdb` | Active embedded DuckDB database |
| `data/processed/tablets.parquet` | Columnar tablet catalog metadata |
| `data/processed/lines.parquet` | Line-by-line normalized text and preservation flags |
| `data/processed/signs.parquet` | Deconstructed sign tokens and classifications |
| `data/processed/chronos_estimates.parquet` | Date resolutions for certified and undated tablets |
| `data/processed/transactions.parquet` | Extracted economic transaction records |
| `data/processed/officer_balances.parquet` | Net inventory balances per official |
| `data/processed/browser.html` | Self-contained interactive visual tablet explorer |
