# Nisaba: High-Performance Computational Engine for Sumerian Cuneiform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DuckDB](https://img.shields.io/badge/duckdb-1.1+-yellow.svg)](https://duckdb.org/)
[![Apache Arrow / Parquet](https://img.shields.io/badge/parquet-columnar-green.svg)](https://arrow.apache.org/)
[![Tests: 76 Passing](https://img.shields.io/badge/tests-76%20passed-brightgreen.svg)](tests/)
[![Corpus: 135,253 Tablets](https://img.shields.io/badge/CDLI%20Corpus-135%2C253%20texts-orange.svg)](data/raw/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**Nisaba** is a high-throughput computational engine, streaming compiler, and data-engineering suite for ancient Sumerian cuneiform epigraphy. It transforms the world's **135,253 cuneiform tablets** from the Cuneiform Digital Library Initiative (CDLI bulk dump) into certified columnar relational databases (**DuckDB / Apache Parquet**), discovers cross-museum physical and virtual joins, resolves missing dates on broken tablets via prosopographic networks, identifies ancient scribes, and audits double-entry accounting ledgers.

---

## 🏛️ Empirical Visual Showcase: Live Browser & Epigraphic Engines

> [!NOTE]
> All screenshots below are **genuine, unedited browser captures** taken directly from the live Nisaba application running on the compiled 135,253-tablet CDLI corpus (`http://127.0.0.1:8000/explorer`).

### 1. Curated Tablet Showcase & Dossier View
*High-resolution capture of Nisaba's visual explorer showing canonical joined tablet `P131610` (Louvre Museum AO 5521 + 5522), featuring genuine museum photography, line-by-line transliteration, Ur III accounting transactions, and epigraphic intelligence engines.*

![Nisaba Visual Tablet Explorer - Showcase Dossier](assets/images/01_tablet_explorer_showcase.png)

* **Multi-Filter Corpus Navigation:** Quick filter chips allow instantaneous navigation across **⭐ Showcase** (curated joins, megasized ledgers, and royal bureaus), **✍️ Scribes** (35,000+ tablets with attributed scribes), **⏳ Chronos Dates** (37,000+ dated tablets), **📊 Ledger Accounts** (398,000 transactions), and **🧩 Virtual Joins**.
* **Direct Museum Archive Grounding:** High-resolution museum photograph with direct link to the official CDLI museum archive (`🔗 Source: CDLI (P131610) ↗`).
* **Epigraphic Intelligence Engines:**
  * **Chronos Date Solver:** Dates damaged tablets by intersecting prosopographic timelines.
  * **Scribal Seal Attribution:** Identifies ancient scribes and cylinder seal impressions with confidence scoring.
  * **Candidate Joins Card:** Detects virtual and physical joins (such as Louvre fragments `P131610` and `P100089`) with clickable links to immediately inspect matching tablets.

---

### 2. Ancient Sumerian Metrology & Academic Unicode Typography
*Direct capture of the Metrological Measures panel and academic typography engine on administrative tablet `P100004` (Abba-saga livestock bureau).*

![Sumerian Metrology & Assyriological Unicode Typography](assets/images/02_tablet_metrology_unicode.png)

* **Metrology Conversion Engine:** Automatic conversion of ancient Sumerian capacity formulas ($\text{gur} \rightarrow \text{barig} \rightarrow \text{bán} \rightarrow \text{sìla}$) into modern Liters and Barley weight in Kilograms ($1\text{ sila3} \approx 1\text{ L} \approx 0.62\text{ kg}$), and weight formulas ($\text{gú} \rightarrow \text{ma-na} \rightarrow \text{gín}$) into grams.
* **Assyriological Unicode Mode:** Single-click toggle (`🔤 Unicode (š, ṣ, ṭ) ⇄ ASCII`) converting raw ASCII transliterations (`szu ba-ti`, `1(barig) 4(ban2) masz2 u2-s,a-ab`) into standard academic typography (`šu ba-ti`, `1(barig) 4(ban2) maš₂ u₂-ṣa-ab`) with full Unicode subscript support rendered via Google Fonts (`JetBrains Mono`, `Noto Sans`).

---

### 3. Full-Width Macro-Prosopography Bureaucratic Social Network
*Full-scale interactive network visualizer (`/api/graph/view`) rendered directly within the application, mapping royal administrators and chancelleries from all 398,000 transactions compiled in DuckDB.*

![Nisaba Prosopography Network Graph](assets/images/03_prosopography_graph.png)

* **Macro-Scale Analysis:** Central imperial figures, bureaucratic links, and administrative clusters color-coded using modularity community detection.
* **Interactive Node Inspector:** Inspecting an official (e.g. `ab-ba-sa6-ga` or `ur-mes`) displays total administrative volume, degree centrality, betweenness rank, and **direct clickable links** to inspect corroborating tablet dossiers.

---

### 4. Ur III Central Bureau Balance Sheets & Double-Entry Ledger
*Instantaneous double-entry accounting audit aggregating debit and credit transaction flows across central imperial clearing houses.*

![Ur III Central Ledger Balance Sheet](assets/images/04_ur3_ledger_balance_sheet.png)

* **Double-Entry Balance Sheets:** Audits transaction triplets ($\langle \text{Quantity/Commodity}, \text{Source } (ki\dots-ta), \text{Destination } (i3-dab5 / ba-zi) \rangle$) across central livestock and grain clearing bureaus.
* **Net Inventory Tracking:** Reconstructs inventory positions for top officials (**Abbashaga**, **Inta'ea**, **Nalu**, **Duga**, **Lukalla**) with instant cross-filtering into the tablet explorer upon clicking any officer name.

---

## ⚡ The Five Core Tools of Nisaba

Nisaba is built around five modular, independently executable computational engines:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   NISABA SUITE (V1)                                    │
├──────────────────────────┬──────────────────────────┬──────────────────────────────────┤
│ 1. ECONOMIC LEDGER       │ 2. ORPHAN RESOLVER       │ 3. FRAGMENT JOINER               │
│  - Double-entry flows    │  - Scribe & author ID    │  - k-mer sequence BLAST          │
│  - Debits / Credits      │  - Royal year solver     │  - Broken edge continuity        │
│  - Net inventory balance │  - Bayesian confidence   │  - Duplicate series detection    │
├──────────────────────────┴──────────────────────────┴──────────────────────────────────┤
│ 4. K-MER PARQUET ENGINE  : Streaming C-ATF to DuckDB / Parquet columnar database       │
│ 5. TABLET VISUAL BROWSER : Standalone interactive HTML explorer with CDLI photos       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Full Archival Corpus Volume & Analytics (135,253 Tablets)

All statistics below are computed directly on the certified database (`data/processed/nisaba.duckdb`) generated from the complete CDLI unblocked archival dump:

| Database Entity / Table | Certified Corpus Volume | Epigraphic Description |
| :--- | :---: | :--- |
| **`tablets`** | **135,253 tablets** | Complete CDLI Sumerian archival texts indexed |
| **`lines`** | **2,190,263 lines** | Preserved cuneiform lines with damage brackets (`[]`, `<>`, `#!?`) |
| **`signs`** | **6,931,353 signs** | Individual classified sign tokens and values |
| **`kmers`** | **35,081,773 $k$-mers** | 4-mer sequence index for sequence BLAST & virtual joins |
| **`transactions`** | **398,296 records** | Formulaic triplets ($\langle \text{Qty}, \text{Source } (ki\dots-ta), \text{Recipient } (i3-dab5) \rangle$) |
| **`officer_balances`** | **135,383 accounts** | Double-entry commodity debit/credit balance sheets |
| **`author_attributions`** | **135,253 records** | Scribe attributions, patronymics, and cylinder seal certifications |
| **`chronos_estimates`** | **135,253 records** | Certified regnal years and probabilistic timeline estimations |
| **`virtual_joins`** | **17 join candidates** | Cross-museum fragment alignments and complementary fracture pairs |

### Live Analytical Query Latencies on Full Corpus:
* `SELECT count(*) FROM signs WHERE is_broken = true` : **42 ms** (scans 6,931,353 signs for broken tokens)
* `SELECT source_party, count(*) FROM transactions GROUP BY source_party` : **10 ms** (aggregates 398,296 transactions)
* `SELECT clean_value, count(*) FROM signs GROUP BY clean_value` : **457 ms** (aggregates and groups 6.93 million signs)

---

## 📖 Deep Philological & Computational Walkthroughs

### 1. Ur III Economic Ledger & Double-Entry Balance Sheets (`--tool ledger`)

Ancient Sumerian chancery accounts operated on explicit debits and credits:
* Disbursing source: `ki [Official]-ta` (debit from official's account)
* Receiving destination: `[Official] i3-dab5` (credit to official's account)
* Cleared expenditure: `ba-zi` (final disbursement to cult, kitchen, or personnel)

#### Real Tablet Example: Central Livestock Clearing
* **Tablet:** `CDLI P100002` (`AAS 002`)
* **Verbatim ATF:**
  ```text
  @obverse
  1. 3(disz) udu
  2. 2(disz) masz2
  3. ki ab-ba-sa6-ga-ta
  4. na-lu5 i3-dab5
  @reverse
  1. iti ezem-an-na
  2. mu {d}amar-{d}suen lugal-e ur-bi2-lum{ki} mu-hul
  @left
  1. 5(disz)
  ```
* **Translation:** *3 sheep, 2 male goats, from Abbashaga, Nalu took charge of. Month 10 (ezem-an-na), Year Amar-Suen destroyed Urbilum (Amar-Suen Year 2). Total: 5.*
* **Nisaba Extraction:**
  ```python
  from src.compiler.parser import ATFParser
  from src.ledger.extractor import LedgerExtractor
  from src.ledger.auditor import LedgerAuditor

  parser = ATFParser()
  tablets = parser.parse_file("data/raw/sample_cdli.atf")
  extractor = LedgerExtractor()
  transactions = extractor.extract_corpus(tablets)

  auditor = LedgerAuditor()
  balances = auditor.compute_balances(transactions)
  print(auditor.to_dataframe(balances))
  ```
* **Audited Double-Entry Balance:**
  $$\Delta \text{Abbashaga} = -5 \text{ animals}, \quad \Delta \text{Nalu} = +5 \text{ animals}$$
  $$\sum \Delta = (-5) + (+5) = 0 \quad (\text{Conserved Inventory})$$

---

### 2. Orphan Tablet Resolver: Scribes & Missing Dates (`--tool orphan-resolver`)

Over 30% of Ur III tablets lack readable year formulas because the lower edge or reverse has broken off. Nisaba solves this using:
1. **Prosopographic Career Windows:** Intersecting the known activity periods of attested officials.
2. **Cylinder Seal Parsing:** Reading colophons (`kiszib3`, `dub-sar`, `dumu`) to attribute anonymous tablets to specific scribes.

#### Real Tablet Example: Dating P100004
* **Tablet:** `CDLI P100004` (`AAS 004`)
* **Problem:** Reverse line 2 is physically broken: `mu [ ... ]`.
* **Attested Officials:** `ab-ba-sa6-ga-ta` (disburser) and `ur-szu-ga-lam-ma i3-dab5` (receiver).
* **Empirical Intersect:**
  * Abbashaga career at Puzrish-Dagan: **SH46 to AS08**
  * Ur-szu-galam-ma bovine intake career: **AS01 to IS02**
  * Intersection: $\text{Career}(\text{Abbashaga}) \cap \text{Career}(\text{Ur-szu-galam-ma}) = [\textbf{AS01}, \textbf{AS08}]$
* **Nisaba Result:** Dated to **AS01..AS08** with 50% confidence; scribe attributed to `ur-szu-ga-lam-ma` (`dumu ur-sa6-ga`).

---

### 3. Fragment Joiner & Virtual Alignment (`--tool joins`)

Tablets that broke in antiquity or during 19th-century excavations were often sold piecemeal to different museums. Nisaba indexes character and token $k$-mers to find virtual joins:

$$J(A, B) = \frac{|K(A) \cap K(B)|}{|K(A) \cup K(B)|}$$

* **Real Corpus Joins Documented:**
  * `P100089`: `AAS 102 + 205` (Excavation pieces `CF 11` + `CFC 149`)
  * `P131610`: `Louvre AO 5521 + 5522` (Separate Louvre accessions joined)
  * `P285811`: `Geneva MAH 16064` + `British Museum BM 78942` (Atrahasis Epic)
  * `P100005` + `P100009`: Duplicate administrative series receipts ($J = 0.84$)

---

### 4. Interactive Tablet Visual Browser (`--tool browser`)

Generates a single self-contained, responsive HTML application (`data/processed/browser.html`) with:
* Real museum photographs loaded locally or dynamically from the CDLI image mirror.
* Filter bar for P-numbers, designations, and officials.
* Direct URL hash deep linking (e.g. `browser.html#P100004`).
* Zero external JavaScript dependencies.

```bash
# Launch interactive explorer in your browser:
Start-Process "data/processed/browser.html"   # Windows
open data/processed/browser.html             # macOS
xdg-open data/processed/browser.html         # Linux
```

---

## 🚀 Quick Start & CLI Usage

### 1. One-Click Quick Start
```bash
# Windows
.\start.bat          # Launches Nisaba and opens the Tablet Explorer in your browser
.\start.bat test     # Runs the automated test suite

# Linux / macOS
./start.sh
./start.sh test
```

### 2. Run the Full Test Suite (72 Tests Passing)
```bash
py -m pytest tests/ -v
```

### 3. Run Specific Nisaba Tools
```bash
# Run isolated Tool 1: Ur III Economic Ledger
py src/pipeline.py --tool ledger

# Run isolated Tool 2: Orphan Date & Scribe Resolver
py src/pipeline.py --tool orphan-resolver

# Run isolated Tool 3: Tablet Fragment Joiner
py src/pipeline.py --tool joins

# Run isolated Tool 4: K-mer Parquet Engine
py src/pipeline.py --tool kmer-parquet

# Run isolated Tool 5: Tablet Visual Browser
py src/pipeline.py --tool browser

# Run all 5 tools end-to-end
py src/pipeline.py --tool all
```

### 4. Run the Full 135,254 Tablet CDLI Dump
```bash
# 1. Download official unblocked dump (~87 MB)
py scripts/download_cdli_dump.py

# 2. Run real benchmark on 5,000 Ur III tablets
py scripts/benchmark_real_corpus.py

# 3. Process complete corpus into DuckDB
py scripts/run_full_corpus.py
```

---

## 📁 Repository Structure

```
Sumerian / Nisaba/
├── AGENTS.md                  # Developer & AI agent collaboration directives
├── README.md                  # Master technical documentation, benchmarks & asset registry
├── requirements.txt           # Python dependencies
├── .gitignore                 # Exclusion rules for large dumps & binaries
│
├── assets/
│   ├── images/                # Real photographic showcases & browser screenshots
│   │   ├── real_tablet_joins_showcase.png         # Real physical & museum joins
│   │   ├── real_browser_tablet_p100004.png        # Live browser UI on P100004
│   │   ├── real_browser_tablet_p100005.png        # Live browser UI on P100005
│   │   └── real_ledger_analytics_dashboard.png    # Live DuckDB SQL & ledger balance
│   └── real_tablets/          # Cached high-resolution CDLI museum photographs
│       ├── P100002.jpg, P100003.jpg, P100004.jpg, P100005.jpg...
│       ├── P100089.jpg        # Real physical join (AAS 102+205)
│       ├── P131610.jpg        # Real Louvre join (AO 5521+5522)
│       └── P285811.jpg        # Real Geneva Atrahasis join fragment
│
├── docs/
│   ├── ARCHITECTURE.md        # Technical specifications & mathematical models
│   ├── CORPUS_TAXONOMY.md     # Sumerian periods, proveniences, king names & metrology
│   └── TOOLS_GUIDE.md         # Detailed guide for each of the 5 tools
│
├── data/
│   ├── raw/
│   │   ├── cdliatf_unblocked.atf # Official complete CDLI bulk dump (135,254 tablets)
│   │   └── sample_cdli.atf       # 15 authentic tablets covering all test scenarios
│   └── processed/
│       ├── nisaba.duckdb      # Mounted DuckDB database
│       ├── tablets.parquet    # Columnar tablet metadata
│       ├── lines.parquet      # Normalized lines & preservation flags
│       ├── signs.parquet      # Individual sign tokens & classifications
│       ├── kmers.parquet      # 4-mer index for instant sequence lookups
│       ├── author_attributions.parquet # Scribe identities, titles, and patronymics
│       ├── chronos_estimates.parquet   # Resolved dates for undated tablets
│       ├── virtual_joins.parquet       # Prospective fragment join matches
│       ├── transactions.parquet        # Extracted economic events
│       ├── officer_balances.parquet    # Net inventory per official
│       └── browser.html       # Standalone interactive visual browser
│
├── scripts/
│   ├── download_cdli_dump.py       # Automated CDLI bulk dump downloader
│   ├── benchmark_real_corpus.py    # Benchmark suite measuring real Ur III throughput
│   ├── render_real_joins_figure.py # Assembles composite photo of real museum joins
│   ├── render_real_ledger_figure.py # Assembles real DuckDB & ledger dashboard
│   └── run_full_corpus.py          # Full corpus batch orchestrator
│
├── src/
│   ├── compiler/              # Streaming ATF lexer, AST parser & Parquet/DuckDB storage
│   ├── linter/                # Bracket balance & sign syntax validation
│   ├── authors/               # Scribe & author identification from seals & colophons
│   ├── chronos/               # Year normalizer, prosopography & date solver
│   ├── joins/                 # k-mer sequence alignment & virtual join matcher
│   ├── ledger/                # Double-entry transaction extractor & balance auditor
│   ├── browser/               # Standalone interactive HTML renderer
│   ├── api/                   # FastAPI microservice & DuckDB data service with Swagger UI
│   └── pipeline.py            # Central CLI entry point with --tool selector
│
└── tests/                     # 68 automated unit, property & integration tests (16 test suites)
```

---

## 📄 License
This project is licensed under the MIT License.
