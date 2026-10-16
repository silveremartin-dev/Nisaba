# Nisaba System Architecture & Mathematical Specifications

## 1. System Overview

Nisaba is engineered as a modular, high-throughput pipeline designed to ingest, validate, analyze, and query the entire corpus of ancient Sumerian cuneiform inscriptions (over 140,000 texts indexed by the Cuneiform Digital Library Initiative, CDLI).

```
                      Raw CDLI ATF Stream
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Compiler Engine   │
                   │  (Streaming Lexer)  │
                   └──────────┬──────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
    tablets.parquet                     lines.parquet
            │                                   │
            ▼                                   ▼
      DuckDB Engine ◄──────────────────── signs.parquet
            │
            ├───────────────┬───────────────┬───────────────┐
            ▼               ▼               ▼               ▼
      Linter Engine   Chronos-Graph    Joins-Finder   Ledger-Auditor
     (Syntax/Morph)   (Date Solver)    (k-mer Match)  (Double Entry)
            │               │               │               │
            └───────────────┴───────┬───────┴───────────────┘
                                    ▼
                         Tablet Visual Browser
```

---

## 2. Relational Parquet & DuckDB Schema

All compiled texts are persisted in immutable, columnar **Apache Parquet** files, directly mounted into an embedded **DuckDB** instance.

### `tablets` Table
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id_text` | `VARCHAR(16)` | Primary Key (e.g. `P100001`) |
| `designation` | `VARCHAR(128)` | Scholarly designation (e.g. `AAS 001`) |
| `period` | `VARCHAR(64)` | Historical era (e.g. `Ur III (ca. 2100-2000 BC)`) |
| `provenance` | `VARCHAR(64)` | Excavation site (e.g. `Umma`, `Puzris-Dagan`, `Girsu`) |
| `museum_collection` | `VARCHAR(128)` | Museum repository (e.g. `Louvre Museum, Paris`) |
| `line_count` | `INTEGER` | Total parsed lines |
| `has_date` | `BOOLEAN` | Whether an explicit year formula exists |
| `raw_metadata` | `JSON` | Full unparsed CDLI header fields |

### `lines` Table
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id_line` | `VARCHAR(32)` | Composite Key (`{id_text}_{surface}_{line_no}`) |
| `id_text` | `VARCHAR(16)` | Foreign Key -> `tablets.id_text` |
| `surface` | `VARCHAR(16)` | Surface name: `obverse`, `reverse`, `bottom`, `left` |
| `line_number` | `INTEGER` | 1-indexed line position within surface |
| `raw_text` | `VARCHAR` | Exact verbatim line text in ATF format |
| `normalized_text` | `VARCHAR` | Cleaned text with damage flags stripped |
| `is_damaged` | `BOOLEAN` | True if line contains `[...]`, `x`, or `#` |
| `sign_count` | `INTEGER` | Number of individual signs/tokens |

### `signs` Table
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id_sign` | `VARCHAR(48)` | Composite Key (`{id_line}_{sign_index}`) |
| `id_line` | `VARCHAR(32)` | Foreign Key -> `lines.id_line` |
| `sign_index` | `INTEGER` | 0-indexed position within the line |
| `token` | `VARCHAR(64)` | Original transliteration token (e.g. `udu#`) |
| `clean_value` | `VARCHAR(64)` | Clean phonetic or logographic value (`udu`) |
| `sign_type` | `VARCHAR(16)` | `NUMERIC`, `LOGOGRAM`, `SYLLABLE`, `DETERMINATIVE` |
| `damage_flag` | `VARCHAR(8)` | Flags: `#` (damaged), `?` (uncertain), `!` (emended) |
| `is_broken` | `BOOLEAN` | True if enclosed in restoration brackets `[...]` |

---

## 3. Mathematical Specifications

### 3.1. Chronos-Graph: Bayesian Temporal Constraint Propagation

Let $T = \{t_1, t_2, \dots, t_N\}$ be the set of tablets. Let $Y = \{y_1, y_2, \dots, y_M\}$ be the discrete chronological years of the Ur III period ($M \approx 73$ years from Shulgi 20 to Ibbi-Sin 3).

Each tablet $t$ with an intact year formula has a degenerate prior:
$$P(Y_t = y) = \mathbb{I}(y = \text{year}(t))$$

For an undated tablet $t_u$, let $E(t_u) = \{e_1, e_2, \dots, e_k\}$ be the set of co-occurring entities (officials $O$, scribes $S$, seals $L$, and calendar month $m$). The posterior distribution over years is given by:

$$P(Y_{t_u} = y \mid E(t_u)) \propto P(Y_{t_u} = y) \prod_{e \in E(t_u)} P(e \mid Y = y)$$

Where $P(e \mid Y = y)$ is the empirical activity window of entity $e$ computed over the subset of certified dated tablets:
$$P(e \mid Y = y) = \frac{\sum_{t \in T_{\text{dated}}} \mathbb{I}(e \in E(t) \land Y_t = y) + \alpha}{\sum_{t \in T_{\text{dated}}} \mathbb{I}(Y_t = y) + \alpha |E|}$$
With Laplace smoothing parameter $\alpha = 0.05$. The maximum a posteriori (MAP) date and $95\%$ credible interval $[\hat{y}_{\min}, \hat{y}_{\max}]$ are computed deterministically.

---

### 3.2. Sequence Alignment for Fragment Joins ($k$-mer MinHash)

To discover virtual joins across separated fragments without quadratic $O(N^2)$ pairwise line comparisons:
1. Every line $L$ is decomposed into sliding character $k$-grams ($k=4$).
2. A MinHash signature matrix is computed using $h=64$ linear hash functions:
   $$h_i(x) = (a_i x + b_i) \pmod p$$
3. Locality Sensitive Hashing (LSH) with $b$ bands and $r$ rows partitions fragments into candidate buckets where prospective Jaccard similarity exceeds threshold:
   $$\text{Sim}(F_1, F_2) = \frac{|k\text{-mers}(F_1) \cap k\text{-mers}(F_2)|}{|k\text{-mers}(F_1) \cup k\text{-mers}(F_2)|} \ge \tau = 0.65$$
4. Candidate matches along broken edges ($\text{surface} = \text{reverse/obverse}$, edge-adjacent lines) are evaluated for lexical continuity.

---

### 3.3. Ur III Economic Ledger Formulation

A transaction record $X$ is defined as a 5-tuple:
$$X = \langle Q, C, A_{\text{src}}, A_{\text{dst}}, t \rangle$$
Where:
- $Q \in \mathbb{R}^+$: Quantity in sexagesimal decimal conversion (e.g. $1(\text{disz}) = 1$, $1(\text{u}) = 10$, $1(\text{gesz2}) = 60$).
- $C$: Commodity class (e.g. `udu` = sheep, `masz2` = goat, `sze` = barley).
- $A_{\text{src}}$: Debtor / Source official (`ki ... -ta`).
- $A_{\text{dst}}$: Creditor / Receiving official (`i3-dab5` / `kiszib3`).
- $t$: Temporal timestamp (resolved year and month).

Conservation of stock across official $A$ over time window $\Delta t$ satisfies:
$$\text{Balance}(A, C, t_1) + \sum_{X \in \text{In}} Q(X) - \sum_{X \in \text{Out}} Q(X) = \text{Balance}(A, C, t_2) \pm \Delta_{\text{error}}$$
Any persistent non-zero $\Delta_{\text{error}}$ flags a scribal discrepancy or missing intermediary tablet.
