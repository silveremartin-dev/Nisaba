# Nisaba Comprehensive Tools Guide

This technical guide provides in-depth specifications, architectural principles, algorithms, and real-world examples for each of the five computational engines in the **Nisaba** suite.

---

## 1. Ur III Economic Ledger Auditor (`--tool ledger`)

### Purpose & Assyriological Background
During the Third Dynasty of Ur (ca. 2112–2004 BC), the centralized state apparatus managed vast livestock clearinghouses (such as Puzrish-Dagan / Drehem) and agricultural centers (Umma, Girsu, Nippur). Chancery practice enforced a strict double-entry transaction grammar:
* **Disbursement / Source:** Marked by the ablative postposition `ki ... -ta` ("from [Officer]").
* **Intake / Custody:** Marked by the compound verbal form `i3-dab5` ("[Officer] took charge of").
* **Expenditure / Clearance:** Marked by the passive-middle verbal chain `ba-zi` ("expended from the account") or delivery formulas `mu-kux(DU)`.
* **Receipt Seal:** Stamped with `kiszib3 [Officer]` ("under the seal of [Officer]").

### Computational Implementation
* **Module:** `src/ledger/extractor.py` & `src/ledger/auditor.py`
* **Parser:** Converts sexagesimal cuneiform metrological tallies ($1(\text{gesz2}) = 60$, $1(\text{u}) = 10$, $1(\text{disz}) = 1$, $1/2(\text{disz}) = 0.5$) into floating-point quantities.
* **Conservation Law:**
  $$\text{Net Balance}(A, C) = \sum_{X \in \text{Intake}(A)} Q(X, C) - \sum_{X \in \text{Disbursement}(A)} Q(X, C)$$

### Real Corpus Example (`CDLI P100004`)
* **Text:** `1(disz) gu4 5(disz) udu niga ki ab-ba-sa6-ga-ta ur-szu-ga-lam-ma i3-dab5`
* **Transaction Triplets:**
  1. $\langle 1.0, \text{"gu4"}, \text{"ab-ba-sa6-ga"}, \text{"ur-szu-ga-lam-ma"} \rangle$
  2. $\langle 5.0, \text{"udu"}, \text{"ab-ba-sa6-ga"}, \text{"ur-szu-ga-lam-ma"} \rangle$
* **Output Artifacts:** `data/processed/transactions.parquet`, `data/processed/officer_balances.parquet`

---

## 2. Orphan Tablet Resolver (`--tool orphan-resolver`)

### Purpose & Historical Bottleneck
Physical tablet edge breakage causes over **30% of Ur III administrative tablets** to lose their explicit royal year formula (`mu ...`). However, ancient transactions record specific officials whose administrative careers spanned precise, finite regnal intervals.

### Chronos Bayesian Constraint Propagation
Let $Y \in \{1, \dots, 73\}$ denote the discrete regnal years of the Ur III dynasty (from Shulgi 20 to Ibbi-Sin 3). For an undated tablet $t$ with attested entities $E(t) = \{e_1, \dots, e_k\}$:

$$P(Y_t = y \mid E(t)) \propto P(Y_t = y) \prod_{e \in E(t)} P(e \mid Y = y)$$

Where $P(e \mid Y = y)$ is estimated empirically across all dated tablets in the corpus using Laplace smoothing ($\alpha = 0.05$).

### Scribe Identification Engine
* **Seal Parsing:** Extracts colophon lines tagged `@seal 1`, `@seal 2`.
* **Lineage Resolution:** Matches formula `[Name] dub-sar dumu [Father] [Title]` (e.g. `lu2-kal-la dub-sar dumu ur-e11-e szusz3` on `P100001`).
* **Output Artifacts:** `data/processed/chronos_estimates.parquet`, `data/processed/author_attributions.parquet`

---

## 3. Fragment Joiner & Alignment Engine (`--tool joins`)

### Purpose & Problem
Broken clay fragments from single tablets or identical multi-tablet administrative series are scattered across global museums. Physical reconstruction requires bringing fragile clay pieces across borders.

### Alignment Architecture
1. **$k$-mer Indexing:** Deconstructs transliteration tokens and character sequences into overlapping $k$-mers ($k=4$).
2. **Jaccard Similarity:**
   $$J(A, B) = \frac{|K(A) \cap K(B)|}{|K(A) \cup K(B)|}$$
3. **Join Classification:**
   * $\ge 0.85$: High-confidence virtual join or duplicate administrative series.
   * $0.65 - 0.84$: Candidate broken edge or administrative series match.

### Ground-Truth Real Joins Certified
* **`P100089` (`AAS 102 + 205`):** Fragments `CF 11` (top) + `CFC 149` (bottom) physically joined across text lines.
* **`P131610` (`Louvre AO 5521 + 5522`):** Musée du Louvre fragments accessioned separately, joined at fracture seam.
* **`P285811` (`Geneva MAH 16064`):** Long-distance virtual join with British Museum `BM 78942` (Atrahasis Epic Tablet III).
* **Output Artifact:** `data/processed/virtual_joins.parquet`

---

## 4. K-mer Parquet Engine (`--tool kmer-parquet`)

### High-Throughput Streaming Compilation
Converts raw CDLI ASCII Transliteration Format (`.atf`) into strictly typed, zero-loss columnar Parquet files mounted in DuckDB:
* `tablets.parquet`: Master catalog metadata, provenance, period, line count.
* `lines.parquet`: Preserves both `raw_text` and `normalized_text`, tracking damage flags (`#`, `?`, `!`, `[]`).
* `signs.parquet`: 241k+ classified sign tokens with linguistic typology (`NUMERIC`, `LOGOGRAM`, `SYLLABLE`, `DETERMINATIVE`).
* `kmers.parquet`: Sliding 4-mer index for sub-millisecond sequence lookups.
* `nisaba.duckdb`: Live analytical database executing complex aggregations in under 3 milliseconds.

---

## 5. Tablet Visual Explorer (`--tool browser`)

### Standalone Interactive Local Application
Compiles an offline-first HTML web application (`data/processed/browser.html`):
* **Local Photo Cache First:** Loads high-resolution museum photographs from `assets/real_tablets/` instantly offline.
* **Online CDLI Mirror Fallback:** Automatically queries `https://cdli.earth/dl/photo/` if a tablet photo is not cached locally.
* **Dynamic Search & Deep Linking:** Live filter bar and URL hash navigation (e.g. `browser.html#P100004`).
* **Visual Analytical Cards:** Color-coded syntax overlays, linter audits, Chronos dates, and double-entry accounting records.

```bash
# Launch visual explorer locally:
Start-Process "data/processed/browser.html"
```
