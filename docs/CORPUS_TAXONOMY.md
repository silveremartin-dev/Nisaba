# Ur III Corpus Taxonomy & Linguistic Reference

This reference catalog standardizes entity normalization rules, royal year names, metrological systems, and administrative formulas implemented across Nisaba.

---

## 1. Royal Dynasties of Ur III (ca. 2112–2004 BC)

| King | Conventional Reign | Standard Abbreviation | Attested Administrative Years |
| :--- | :--- | :--- | :--- |
| **Ur-Nammu** | 2112–2095 BC | `UN` | Years 1 to 18 |
| **Shulgi** | 2094–2047 BC | `SH` | Years 1 to 48 (Mass administrative explosion starts ~SH 30) |
| **Amar-Suen** (Amar-Sin) | 2046–2038 BC | `AS` | Years 1 to 9 |
| **Shu-Suen** (Shu-Sin) | 2037–2029 BC | `SS` | Years 1 to 9 |
| **Ibbi-Suen** (Ibbi-Sin) | 2028–2004 BC | `IS` | Years 1 to 24 (Centralized control collapses after IS 3) |

---

## 2. Standard Ur III Administrative Calendar (Reichskalender / Puzrish-Dagan & Umma)

| Month No. | Puzrish-Dagan (Drehem) Standard | Umma Standard | Girsu (Lagash) Standard |
| :---: | :--- | :--- | :--- |
| **1** | `iti masz-da3-gu7` | `iti sze-sag11-ku5` | `iti GAN2-masz` |
| **2** | `iti ses-da-gu7` | `iti sig4-{gesz}i3-szub-ba-gar` | `iti gu4-ra2-bi2-mu2-mu2` |
| **3** | `iti u5-bi2-gu7` | `iti sze-kar-ra-gal2-la` | `iti ezem-{d}li9-si4` |
| **4** | `iti ki-siki-{d}nin-a-zu` | `iti nesag` | `iti szu-numun` |
| **5** | `iti ezem-{d}nin-a-zu` | `iti dal` | `iti munu4-gu7` |
| **6** | `iti a2-ki-ti` | `iti szu-numun` | `iti ezem-{d}dumu-zi` |
| **7** | `iti ezem-{d}szul-gi` | `iti min-esz3` | `iti ezem-{d}szul-gi` |
| **8** | `iti szu-esz5-sza` | `iti e2-iti-6(disz)` | `iti ezem-{d}ba-ba6` |
| **9** | `iti kisziki` | `iti {d}li9-si4` | `iti mu-szu-du7` |
| **10** | `iti ezem-mah` | `iti ezem-{d}szul-gi` | `iti amar-a-a-si` |
| **11** | `iti ezem-an-na` | `iti pa4-u2-e` | `iti sze-sag11-ku5` |
| **12** | `iti ezem-me-ki-gal2` | `iti {d}dumu-zi` | `iti sze-il2-la` |
| **13 (diri)** | `iti diri ...` (intercalary) | `iti diri ...` | `iti diri ...` |

---

## 3. Sexagesimal Metrology & Numerical Tokens

Nisaba parses both integer count systems and capacity/weight systems into canonical decimal floats:

### 3.1. Discrete Counts (Livestock, Humans, Bricks)
- `1(asz)` / `1(disz)` = $1$
- `2(disz)` = $2$
- `1(u)` = $10$
- `2(u)` = $20$
- `1(gesz2)` = $60$
- `1(gesz'u)` = $600$
- `1(szar2)` = $3600$

### 3.2. Capacity System (Dry/Liquid: Grain, Beer, Oil)
- Base unit: `1(sila3)` $\approx 1 \text{ liter}$
- `1(ban2)` = $10 \text{ sila3}$
- `1(barig)` = $60 \text{ sila3}$
- `1(gur)` = $300 \text{ sila3} = 5 \text{ barig}$

---

## 4. Key Commodities

| Sumerian Transliteration | Translation / Category | Domain |
| :--- | :--- | :--- |
| `udu` | sheep | Livestock (Puzrish-Dagan) |
| `udu niga` | fattened sheep | Grain-fed livestock |
| `u8` | ewe | Livestock |
| `sila4` | lamb | Livestock |
| `masz2` | male goat | Livestock |
| `masz2-gal` | full-grown male goat | Livestock |
| `ud5` | female goat | Livestock |
| `gu4` / `gud` | ox / bull | Heavy draught animal |
| `ab2` | cow | Livestock |
| `sze` | barley | Primary cereal currency |
| `dabin` | flour | Rations |
| `kasz` | beer | Beverage |
| `i3-gesz` | sesame oil | Rations |

---

## 5. Core Transaction Verbs & Syntactic Formulas

| Sumerian Formula | Grammatical Role | Economic Semantics |
| :--- | :--- | :--- |
| `ki <Person> -ta` | Ablative phrase | "From [Person]" (Debited party) |
| `i3-dab5` | Finite verb (3sg ergative) | "He took charge of" / "Booked into custody" |
| `ba-zi` | Passive/impersonal verb | "It was expended / disbursed" (Credit side) |
| `mu-kux(DU)` | Nominalized verb | "Delivery / Inward shipment" |
| `kiszib3 <Person>` | Genitive / Seal legend | "Under seal of [Person]" (Official receipt) |
| `giri3 <Person>` | Prepositional phrase | "Via / Under conveying authority of [Person]" |
| `iti <Month>` | Temporal clause | Accounting month |
| `mu <Year>` | Royal year formula | Accounting fiscal year |
