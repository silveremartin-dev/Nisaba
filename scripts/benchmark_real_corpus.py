import os
import sys
import time

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from src.compiler.lexer import ATFLexer
from src.compiler.parser import ATFParser
from src.compiler.storage import StorageEngine
from src.chronos.solver import ChronosSolver
from src.authors.scribe_identifier import AuthorIdentifier
from src.joins.matcher import FragmentMatcher
from src.ledger.extractor import LedgerExtractor
from src.ledger.auditor import LedgerAuditor

def run_real_benchmark(max_tablets: int = 5000):
    dump_path = "data/raw/cdliatf_unblocked.atf"
    if not os.path.exists(dump_path):
        print(f"Dump not found: {dump_path}")
        return

    print("======================================================================")
    print(f"[*] NISABA BENCHMARK: Real CDLI Corpus Ingestion ({max_tablets:,} tablets)")
    print("======================================================================")

    # 1. Parsing Benchmark
    lexer = ATFLexer()
    parser = ATFParser()
    t0 = time.perf_counter()
    tablets = []
    lines_count = 0
    signs_count = 0

    def ur3_lines(file_obj):
        found = False
        for line in file_obj:
            if not found and line.startswith("&P100001"):
                found = True
            if found:
                yield line

    with open(dump_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = lexer.tokenize_stream(ur3_lines(f))
        for tab in parser.parse_stream(tokens):
            tablets.append(tab)
            lines_count += len(tab.lines)
            for l in tab.lines:
                signs_count += len(l.signs)
            if len(tablets) >= max_tablets:
                break

    t_parse = time.perf_counter() - t0
    tabs_sec = len(tablets) / t_parse if t_parse > 0 else 0
    lines_sec = lines_count / t_parse if t_parse > 0 else 0

    print(f"✅ Ingested {len(tablets):,} tablets ({lines_count:,} lines, {signs_count:,} signs)")
    print(f"   ⏱️ Parsing Time : {t_parse:.2f}s ({tabs_sec:,.0f} tablets/sec | {lines_sec:,.0f} lines/sec)")

    # 2. Parquet Export & DuckDB
    t0 = time.perf_counter()
    db_file = "data/processed/benchmark/nisaba.duckdb"
    storage = StorageEngine(db_path=db_file)
    written = storage.export_tables(tablets, output_dir="data/processed/benchmark")
    t_parquet = time.perf_counter() - t0
    print(f"✅ Parquet & DuckDB Export: {t_parquet:.2f}s")
    for tbl, pth in written.items():
        sz = os.path.getsize(pth) / 1024
        print(f"   • {tbl}.parquet: {sz:,.1f} KB")

    # 3. DuckDB Live Query Benchmark
    con = duckdb.connect(db_file)
    t0 = time.perf_counter()
    res = con.execute("SELECT count(*) FROM lines WHERE is_damaged = true").fetchone()
    t_query = (time.perf_counter() - t0) * 1000
    print(f"✅ DuckDB Query (Damaged lines count = {res[0]:,}): {t_query:.2f} ms")

    # 4. Scribe & Author Attribution
    t0 = time.perf_counter()
    author_tool = AuthorIdentifier()
    attributions = author_tool.attribute_corpus(tablets)
    identified = sum(1 for a in attributions if a.identified_scribe)
    t_author = time.perf_counter() - t0
    print(f"✅ Scribe Attributions: {identified:,} / {len(tablets):,} ({t_author:.2f}s)")

    # 5. Chronos Missing Year Resolution
    t0 = time.perf_counter()
    chronos = ChronosSolver()
    estimates = chronos.fit_and_resolve(tablets)
    certified = sum(1 for e in estimates if e.status == "CERTIFIED_DATED")
    estimated = sum(1 for e in estimates if e.status == "ESTIMATED")
    t_chronos = time.perf_counter() - t0
    print(f"✅ Chronos Temporal Resolver: {certified:,} certified, {estimated:,} inferred dates ({t_chronos:.2f}s)")

    # 6. Economic Ledger Auditor
    t0 = time.perf_counter()
    extractor = LedgerExtractor()
    txs = extractor.extract_corpus(tablets)
    auditor = LedgerAuditor()
    balances = auditor.compute_balances(txs)
    t_ledger = time.perf_counter() - t0
    print(f"✅ Ledger Auditor: {len(txs):,} transactions, {len(balances)} officer accounts audited ({t_ledger:.2f}s)")

    print("======================================================================")
    print("ALL BENCHMARKS COMPLETED ON REAL ARCHIVAL DATA")
    print("======================================================================")

if __name__ == "__main__":
    run_real_benchmark(5000)
