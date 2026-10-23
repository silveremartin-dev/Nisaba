# PROJECT_STATE.md — Nisaba Engineering Session Memory & Asset Registry

## 📌 1. Project Overview & Architectural Mission

* **Repository:** `https://github.com/silveremartin-dev/Nisaba`
* **Local Workspace:** `C:\Silvere\Encours\Developpement\Sumerian`
* **Mission:** High-performance computational engine and data pipeline for Sumerian cuneiform epigraphy, transforming the world's 135,254 CDLI ATF text archives into certified Apache Parquet / DuckDB databases, identifying ancient scribes and authors, resolving undated tablets via prosopography, auditing balanced economic accounts, discovering cross-collection fragment joins, and rendering interactive visual tablet explorers with real museum photos.

---

## 🏛️ 2. The Five Analytical Engines

| Analytical Engine | Module | Primary Class | Real Empirical Capabilities |
| :--- | :--- | :--- | :--- |
| **1. Ur III Economic Ledger** | `src/ledger/` | `LedgerAuditor` | Sexagesimal metrology parsing, double-entry receipts (`ki...-ta` / `i3-dab5` / `ba-zi`), net inventory balance sheets (24,018 real txs audited). |
| **2. Orphan Tablet Resolver** | `src/authors/` + `src/chronos/` | `AuthorIdentifier` & `ChronosSolver` | Seal legend extraction (`@seal`), colophons (`dub-sar`), Bayesian constraint propagation across career windows (1,009 undated tablets dated). |
| **3. Fragment Joiner** | `src/joins/` | `FragmentMatcher` | Token and character $k$-mer Jaccard alignment detecting physical and virtual joins across museum collections. |
| **4. K-mer Parquet Engine & Batch Compiler** | `src/compiler/` | `BatchCompiler` & `StorageEngine` | Streaming lexer and AST parser serializing into `tablets.parquet`, `lines.parquet`, `signs.parquet`, `kmers.parquet` in constant memory with DuckDB views. |
| **5. Tablet & Network Explorers** | `src/browser/` | `TabletBrowserRenderer` & `NetworkGraphRenderer` | Interactive HTML apps: `browser.html` (tablet photos & syntax) + `prosopography_graph.html` (Cytoscape.js administrative networks). |
| **6. Epigraphic REST API** | `src/api/` | `FastAPI app` & `NisabaDataService` | Microservice with OpenAPI/Swagger docs (`/docs`), DuckDB queries, full-text search, ledger endpoints, and graph serialization. |

---

## 🧪 3. Test Suite Verification

* **Framework:** `pytest`
* **Test Count:** **68 passing tests** across 16 test suites:
  - `tests/test_api.py` (7 tests: root, health, stats, tablets pagination, detail, search, ledger, D3/Cytoscape graph)
  - `tests/test_authors.py` (3 tests: seal extraction, probabilistic attribution, corpus batch)
  - `tests/test_batch_compiler.py` (1 test: chunked streaming compilation in constant memory and DuckDB mounting)
  - `tests/test_browser.py` (1 test: HTML structure, CDLI photo links, entity highlight spans, hash routing)
  - `tests/test_chronos.py` (2 tests: formula normalization, undated tablet resolution)
  - `tests/test_deep_chronos.py` (2 tests: royal year coverage, disjoint window handling)
  - `tests/test_deep_ledger.py` (2 tests: sexagesimal conversions, multi-commodity balance sheets)
  - `tests/test_deep_linter.py` (3 tests: unmatched angle brackets, unmatched parentheses, multiple sign issues)
  - `tests/test_duckdb_analytics.py` (1 test: multi-table SQL joins, sign type aggregations)
  - `tests/test_extended_coverage.py` (26 tests: AST parsing, primed lines, multi-commodity flows, k-mer metrics, Bayesian chronos, file sharding roundtrips)
  - `tests/test_joins.py` (2 tests: k-mer Jaccard, fragment join matching)
  - `tests/test_ledger.py` (1 test: transaction extraction and balances)
  - `tests/test_lexer.py` (2 tests: streaming tokens, broken line numbering)
  - `tests/test_linter.py` (3 tests: bracket auditor, sign validator, corpus reporting)
  - `tests/test_parser.py` (2 tests: AST generation, damaged sign preservation)
  - `tests/test_pipeline.py` (2 tests: full pipeline integration and selective tool runs)
  - `tests/test_prosopographic_network.py` (2 tests: graph construction, centrality, D3/Cytoscape exports, HTML generation)
  - `tests/test_storage.py` (1 test: Parquet export and DuckDB query execution)
  - `tests/test_chunker.py` (2 tests: file sharding, manifest generation, SHA-256 byte-exact reassembly)
  - `tests/test_taxonomy.py` (3 tests: king codes, catalog uniqueness, metrology)
* **Status:** 100% Green (`68 passed in 63.91s`).

---

## 📊 4. Measured Empirical Benchmarks on Real Archival Corpus

### 🌐 FULL CORPUS COMPILATION (100% World CDLI Archive)
Compiled directly from `data/raw/cdliatf_unblocked.atf` (86.9 MB):

* **Total Tablets Ingested:** **135,253 tablets**
* **Total Lines Extracted:** **2,190,263 lines**
* **Total Signs Classified:** **6,931,353 signs**
* **Total 4-mers Indexed:** **35,081,773 k-mers**
* **Total Compilation Time:** **292.11 s (4.8 minutes)**
* **Throughput:** **463 tablets/s (7,498 lines/s)**
* **Compiled Database:** `data/processed/nisaba.duckdb` (589,049,856 bytes)
* **Git-Safe Distribution:** Sharded into **15 parts** (< 42 MB each) in `data/shards/` with SHA-256 manifest.
* **On-the-Fly Reassembly:** Auto-bootstrapped on client launch in ~3.2 seconds.

---

## 🖼️ 5. Certified Real Visual Assets

| File Path | Description | Visual Source |
| :--- | :--- | :--- |
| `assets/images/real_tablet_joins_showcase.png` | 3-panel real museum join showcase | `P100089` (AAS 102+205), `P131610` (Louvre AO 5521+5522), `P285811` (Geneva MAH 16064 Atrahasis) |
| `assets/images/real_browser_tablet_p100004.png` | Unedited headless Chrome UI screenshot | Tablet `P100004` (AAS 004): real photo, date resolved to AS01..AS08, scribe attributed |
| `assets/images/real_browser_tablet_p100005.png` | Unedited headless Chrome UI screenshot | Tablet `P100005` (AAS 005): real photo with CF 2 mark, candidate join with `P100009` |
| `assets/images/real_ledger_analytics_dashboard.png` | DuckDB SQL shell & ledger balance sheet | Real SQL queries across 241,858 signs, net livestock balance for Abbashaga (-2,840), Inta'ea (+1,110) |

---

## 📁 6. Certified Artifacts on Disk

| File Path | Description |
| :--- | :--- |
| `data/raw/cdliatf_unblocked.atf` | Complete official CDLI bulk dump (86.9 MB, 135,254 tablets) |
| `data/raw/sample_cdli.atf` | 15 authentic CDLI tablets covering all administrative scenarios |
| `data/processed/nisaba.duckdb` | Active embedded DuckDB database |
| `data/processed/tablets.parquet` | Columnar tablet catalog metadata |
| `data/processed/lines.parquet` | Line-by-line normalized text and preservation flags |
| `data/processed/signs.parquet` | Deconstructed sign tokens and classifications |
| `data/processed/kmers.parquet` | 4-mer index for sequence lookups |
| `data/processed/author_attributions.parquet` | Scribe identities, titles, and patronymics |
| `data/processed/chronos_estimates.parquet` | Date resolutions for certified and undated tablets |
| `data/processed/virtual_joins.parquet` | Prospective fragment join matches |
| `data/processed/transactions.parquet` | Extracted economic transaction records |
| `data/processed/officer_balances.parquet` | Net inventory balances per official |
| `data/processed/browser.html` | Self-contained interactive visual tablet explorer |
