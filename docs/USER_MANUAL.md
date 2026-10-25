# 📖 Nisaba — One-Page User Manual & Quick Reference

## 🏛️ What is Nisaba?
**Nisaba** is a high-performance computational engine and epigraphic intelligence suite for ancient Sumerian cuneiform epigraphy. It transforms the world's complete **135,253 cuneiform tablets** from the Cuneiform Digital Library Initiative (CDLI) into certified columnar relational databases (**DuckDB / Apache Parquet**), recovers lost tablet dates via Bayesian prosopographic networks, identifies ancient scribes, audits double-entry accounting ledgers, and detects cross-museum fragment joins.

---

## ⚡ 1. One-Click Launch

* **Windows**: Double-click `start.bat` (or run `.\start.bat` in PowerShell/CMD).
* **Linux / macOS**: Run `./start.sh`.

The launcher automatically starts the local analytical server and opens your web browser to the **Visual Tablet Explorer** at:
👉 **[http://127.0.0.1:8000/explorer](http://127.0.0.1:8000/explorer)**

---

## 🧭 2. Visual Tablet Explorer (`/explorer`)

The Explorer provides a modern interactive interface to navigate the entire 135,253-tablet world corpus:

1. **Sidebar Navigation & Live Search**:
   * **Corpus Search Bar**: Type any CDLI P-number (e.g. `P100004`), museum inventory mark (e.g. `AO 19761`), or Sumerian keyword (e.g. `udu` for sheep, `kasz` for beer, `gu4` for oxen).
   * **Pagination & Browsing**: Seamlessly browse through 50 tablets per page across all 135,253 tablets.
   * **Direct P-Number Jump**: Type any identifier to load its full epigraphic dossier instantly.

2. **Epigraphic Dossier & Transliteration Panel**:
   * **Full Transliteration**: Displays line-by-line Sumerian text broken down by surface (`@obverse`, `@reverse`, `@left`, `@seal`).
   * **Color-Coded Epigraphic Flags**:
     * 🟡 **Gold**: Numerical values and sexagesimal quantities (`1(disz)`, `3(u)`).
     * 🔵 **Cyan**: Attested administrative officials and personal names.
     * 🔴 **Red**: Damaged signs, physical tablet fractures, and restorations (`[...]`, `#`, `?`).
     * 🟢 **Green**: Administrative verbs and transaction keywords (`i3-dab5`, `ba-zi`, `ki ... -ta`).

3. **High-Resolution Museum Photography**:
   * Displays authentic 2D photographs from international museum collections (Musée du Louvre, British Museum, MAH Geneva, Ashmolean).
   * Tablets without local photographs automatically link to the Berlin CDLI photographic archive mirror.

---

## 🧠 3. Built-In Epigraphic Engines

| Engine | What It Does | Where to See It |
| :--- | :--- | :--- |
| **Chronos Date Solver** | Reconstructs missing dates on broken tablets by calculating the career intersection of attested officials. | **Chronos Box** in Tablet Explorer & `/api/tablets/{id}` |
| **Scribe Attribution** | Identifies ancient scribes by parsing cylinder seal impressions, colophons (`dub-sar`), and patronymics. | **Scribe Attribution Box** in Tablet Explorer |
| **Ur III Economic Ledger** | Audits balanced double-entry accounts ($\Delta \text{Disburser} + \Delta \text{Receiver} = 0$) across 398,000 transactions. | **Ledger Transactions Tab** & `/api/ledger/officials` |
| **Fragment Joiner** | Aligns $k$-mer sequences to identify broken pieces of the same tablet scattered in different museums. | **Candidate Joins Box** in Tablet Explorer |
| **Social Network Graph** | Renders the prosopographic co-occurrence network of Sumerian chancery officials. | **[http://127.0.0.1:8000/api/graph/view](http://127.0.0.1:8000/api/graph/view)** |

---

## 🔍 4. Interactive SQL & API Console (`/docs`)

Visit **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** to run live queries on all **9 columnar DuckDB tables**:
* `GET /api/search?q=udu&limit=20`: Search 7 million signs in < 3 ms.
* `GET /api/ledger/officials`: View net livestock and grain inventories per official (e.g. Abbashaga, Inta'ea, Lukalla).
* `GET /api/tablets/{id_text}`: Fetch complete JSON dossier for any tablet.

---

## 🛠️ 5. Automated Tests & Maintenance

To run the full suite of **72 unit and integration tests**:
```bash
.\start.bat test        # Windows
./start.sh test         # Linux / macOS
# Or directly:
py -m pytest tests/ -v
```
