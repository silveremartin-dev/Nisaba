# AGENTS.md — Developer & AI Agent Collaboration Directives for Nisaba

## 🎯 1. Core Project Identity & Scope

**Nisaba is a high-throughput computational engine and data-engineering suite for ancient Sumerian cuneiform epigraphy, transforming unstructured archival text dumps (CDLI ATF) into certified relational databases, formal linguistic audits, cross-museum virtual joins, and macro-chronological resolutions.**

### The Core Problem:
Assyriology and ancient Near Eastern digital humanities suffer from an **epigraphic data bottleneck**:
1. **The Format Trap**: Over 140,000 Sumerian tablets in the Cuneiform Digital Library Initiative (CDLI) are stored in loose, legacy ASCII Transliteration Format (`.atf`) files written across 30 years with inconsistent dialect flags, unvalidated damage brackets, and irregular sign indexes (`gu4` vs `gud`, `szu` vs `šù`).
2. **Missing Grounded Verification**: General-purpose LLMs severely hallucinate when processing low-resource agglutinative languages like Sumerian, inventing impossible morphological chains and false historical attributions.
3. **The Chronological Void**: Over 30% of Ur III tablets lack explicit year names due to physical tablet edge breakage, even though their transaction networks (officials, seals, commodities, months) contain sufficient mathematical constraints to date them.
4. **Physical & Museum Dispersion**: Thousands of broken clay fragments from the same original tablets or identical administrative series are scattered across museums globally without systematic cross-collection text alignment.

### Nisaba Boundary Principles:
* **IN SCOPE**:
  1. **High-Speed ATF Streaming Compiler**: Parsing CDLI ATF files into strictly typed, columnar **Apache Parquet / DuckDB** schemas (`tablets`, `lines`, `signs`, `entities`).
  2. **Deterministic Morphosyntactic Linter**: Validating sign index validity against canonical Assyriological sign lists (MZL / Borger), checking bracket balancing (`[]`, `<>`, `()`, `#!?`), and detecting morphotactic errors.
  3. **Chronos-Graph (Macro-Chronology Solver)**: Propagating temporal constraints across prosopographic networks (officials, scribal dynasties, seal inscriptions, intercalary months) to assign probabilistic dates to undated tablets.
  4. **Fragment Joiner & Alignment Engine**: Running all-against-all sequence alignment ($k$-mer indexing, MinHash/LSH, break-edge continuity) across the entire corpus to discover virtual joins and duplicate administrative series.
  5. **Ur III Economic Ledger Auditor**: Parsing formulaic transaction triplets ($\langle \text{Quantity/Commodity}, \text{Source } (ki\dots-ta), \text{Destination/Recipient } (i3-dab5 / ba-zi) \rangle$) and verifying balanced accounts.
  6. **Tablet Visual Explorer**: A lightweight, interactive visual navigator displaying tablet metadata, transliterations, highlighted linguistic entities, and direct links to CDLI 2D/3D photo archives.
* **OUT OF SCOPE / STRICTLY REJECTED**:
  - Unconstrained generative LLM hallucination for text completion without formal grammatical verification.
  - Speculative 3D mesh physics reassembly on eroded fractures without textual corroboration.
  - Proprietary or closed binary schemas: all data must remain queryable via standard SQL and Apache Arrow / Parquet.

---

## ⚡ 2. The Computational & Yield Filter

Nisaba operates under the principle that **archival data is vast but noisy**. A rigorous attrition filter must certify ground truth:

$$\text{Certification Score} = \text{ATFSyntaxScore} \times \text{SignIndexValidity} \times \text{ProsopographicConsistency}$$

* **Rule of Zero-Loss Compilation**: When compiling raw ATF to Parquet/DuckDB, all raw text and damage flags (`#`, `?`, `!`, `[]`) must be preserved in dedicated structural columns. No data is silently dropped.
* **The "Primary Grounding" Principle**: Every extracted entity (ruler, scribe, commodity, date, quantity) must point back to its exact tablet identifier (`id_text` P-number) and 1-indexed line number.

---

## 🔄 3. Multi-Engine Architecture

All AI agents and developers implementing features in Nisaba must adhere to the modular architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TIER 1 : Core Ingestion                         │
│  CDLI Bulk ATF Dump (`cdliatf_unblocked.atf` ~150 MB)                  │
│         │                                                              │
│         ▼ (Streaming Lexer & AST Parser)                               │
│  1. Tablets Metadata Table (`tablets.parquet`)                         │
│  2. Lines & Preservations Table (`lines.parquet`)                      │
│  3. Sign-by-Sign Deconstruction (`signs.parquet`)                      │
│  4. Canonical DuckDB Storage (`data/processed/nisaba.duckdb`)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
│ TIER 2: Linter  │        │ TIER 3: Chronos │        │ TIER 4: Joins   │
│ - Bracket audit │        │ - Prosopography │        │ - k-mer index   │
│ - Sign list MZL │        │ - Seal networks │        │ - Break-edge    │
│ - Morphotactics │        │ - Date solver   │        │ - Virtual joins │
└─────────────────┘        └─────────────────┘        └─────────────────┘
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 5 : Ledger & Visual Explorer                    │
│  - Double-Entry Ur III Commodity Balance Sheets (`ledger`)             │
│  - Interactive Visual Browser & CDLI Photo Linker (`browser`)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📄 4. Technical Documentation Standard

* **Strict English Language Requirement**: ALL documentation (`README.md`, `doc/*.md`, `AGENTS.md`), code comments, docstrings, JSON schema definitions, and commit messages MUST be written strictly in English.
* **Traceable Grounding**: All catalog entries must explicitly map to official CDLI P-numbers (e.g. `P100001` to `P520000`).
* **Test-Driven Rigor**: Every module must have comprehensive pytest coverage verifying both synthetic edge cases and real-world CDLI tablet excerpts.

---

## 🤖 5. Specialized Modules & Components

1. **`Compiler` (`src/compiler/`)**:
   - High-throughput streaming lexer and AST builder for CDLI C-ATF format.
   - Parquet and DuckDB serializer with zero data loss.
2. **`Linter` (`src/linter/`)**:
   - Audits bracket parity, damaged sign tokens, deprecated transliteration spellings, and morphological slot violations.
3. **`Chronos` (`src/chronos/`)**:
   - Normalizes Ur III year name formulas; constructs the prosopographic co-occurrence graph; estimates missing tablet dates.
4. **`Joins` (`src/joins/`)**:
   - $k$-mer sequence alignment across damaged tablet edges to detect prospective physical and textual virtual joins.
5. **`Ledger` (`src/ledger/`)**:
   - Extracts balanced transaction records (`i3-dab5`, `ba-zi`, `mu-kux(DU)`) for commodity flow analysis.
6. **`Browser` (`src/browser/`)**:
   - Interactive visual inspection tool rendering tablet transliterations, entity overlays, and links to CDLI image repositories.
