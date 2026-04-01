"""
seed.py — testa o pipeline completo end-to-end

Fluxo:
  1. Inicializa o banco (init_db)
  2. Insere N registros falsos em raw_metrics
  3. Roda cleaner (raw_metrics → clean_metrics)
  4. Roda features (clean_metrics → features)
  5. Imprime resumo do resultado
"""

import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loguru import logger

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parents[1]
DB_PATH  = ROOT / "data" / "metrics.db"
LOG_PATH = ROOT / "logs" / "seed.log"

# adiciona pipeline/ ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).resolve().parent))

from init_db  import init_db
from cleaner  import run_cleaning_job
from features import run_features_job

# ── logging ───────────────────────────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}")
logger.add(LOG_PATH,   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# ── config ────────────────────────────────────────────────────────────────────
N_RECORDS      = 150   # registros a inserir (> WINDOW=100 para testar rolling completo)
N_NULLS        = 5     # registros com valores nulos (devem ser descartados)
N_OUTLIERS     = 5     # registros com outliers (devem ser descartados)
START_TIME     = datetime.now(timezone.utc) - timedelta(minutes=N_RECORDS)

# ── gerador de dados ──────────────────────────────────────────────────────────
def _random_metrics() -> dict:
    return {
        "cpu_usage":  round(random.uniform(5.0,  95.0),  2),
        "cpu_temp":   round(random.uniform(30.0, 90.0),  2),
        "ram_usage":  round(random.uniform(10.0, 90.0),  2),
        "disk_usage": round(random.uniform(10.0, 80.0),  2),
        "disk_read":  round(random.uniform(0.0,  5e7),   2),
        "disk_write": round(random.uniform(0.0,  5e7),   2),
        "net_sent":   round(random.uniform(0.0,  1e6),   2),
        "net_recv":   round(random.uniform(0.0,  1e6),   2),
        "gpu_usage":  round(random.uniform(0.0,  90.0),  2),
        "gpu_temp":   round(random.uniform(30.0, 85.0),  2),
    }


def _null_metrics() -> dict:
    """Registro com alguns campos nulos — deve ser descartado pelo cleaner."""
    m = _random_metrics()
    null_cols = random.sample(list(m.keys()), k=random.randint(1, 3))
    for col in null_cols:
        m[col] = None
    return m


def _outlier_metrics() -> dict:
    """Registro com outlier — deve ser descartado pelo cleaner."""
    m = _random_metrics()
    col = random.choice(["cpu_usage", "cpu_temp", "ram_usage", "gpu_temp"])
    m[col] = 999.9   # fora dos limites definidos em cleaner.py
    return m


# ── seed ──────────────────────────────────────────────────────────────────────
def seed_raw_metrics():
    logger.info(f"Inserindo {N_RECORDS} registros em raw_metrics...")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")

    # índices dos registros que serão nulos ou outliers
    null_indices    = set(random.sample(range(N_RECORDS), N_NULLS))
    outlier_indices = set(random.sample(
        [i for i in range(N_RECORDS) if i not in null_indices],
        N_OUTLIERS,
    ))

    rows = []
    for i in range(N_RECORDS):
        ts = (START_TIME + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if i in null_indices:
            m = _null_metrics()
        elif i in outlier_indices:
            m = _outlier_metrics()
        else:
            m = _random_metrics()

        rows.append((
            ts,
            m["cpu_usage"], m["cpu_temp"],
            m["ram_usage"],
            m["disk_usage"], m["disk_read"], m["disk_write"],
            m["net_sent"],   m["net_recv"],
            m["gpu_usage"],  m["gpu_temp"],
        ))

    conn.executemany(
        """
        INSERT OR IGNORE INTO raw_metrics (
            timestamp,
            cpu_usage, cpu_temp,
            ram_usage,
            disk_usage, disk_read, disk_write,
            net_sent, net_recv,
            gpu_usage, gpu_temp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()

    logger.info(
        f"Seed concluído — total={N_RECORDS} | "
        f"nulos={N_NULLS} | outliers={N_OUTLIERS} | "
        f"válidos esperados≈{N_RECORDS - N_NULLS - N_OUTLIERS}"
    )


# ── resumo ────────────────────────────────────────────────────────────────────
def print_summary():
    conn = sqlite3.connect(DB_PATH)

    def count(table, where="1=1"):
        return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]

    raw_total   = count("raw_metrics")
    raw_pending = count("raw_metrics",   "processed = 0")
    clean_total = count("clean_metrics")
    feat_total  = count("features")

    conn.close()

    logger.info("─" * 50)
    logger.info("RESUMO DO PIPELINE")
    logger.info("─" * 50)
    logger.info(f"raw_metrics   → total={raw_total} | pendentes={raw_pending}")
    logger.info(f"clean_metrics → total={clean_total}")
    logger.info(f"features      → total={feat_total}")
    logger.info("─" * 50)

    # validações básicas
    descartados = N_NULLS + N_OUTLIERS
    esperados   = N_RECORDS - descartados

    ok = True

    if raw_pending != 0:
        logger.warning(f"Ainda há {raw_pending} registros não processados em raw_metrics!")
        ok = False

    if clean_total < esperados:
        logger.warning(
            f"clean_metrics tem {clean_total} registros, esperado ≥ {esperados} "
            f"(descartados={descartados})"
        )
        ok = False

    if feat_total != clean_total:
        logger.warning(
            f"features ({feat_total}) != clean_metrics ({clean_total}) — "
            "nem todos os registros geraram features"
        )
        ok = False

    if ok:
        logger.success("Pipeline OK — todos os registros foram processados corretamente.")
    else:
        logger.error("Pipeline com inconsistências — verifique os logs acima.")


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 50)
    logger.info("SEED — teste end-to-end do pipeline")
    logger.info("=" * 50)

    # 1. banco
    logger.info("[ 1/4 ] Inicializando banco...")
    init_db()

    # 2. dados falsos
    logger.info("[ 2/4 ] Inserindo dados falsos...")
    seed_raw_metrics()

    # 3. cleaner
    logger.info("[ 3/4 ] Rodando cleaner...")
    run_cleaning_job()

    # 4. features
    logger.info("[ 4/4 ] Rodando features...")
    run_features_job()

    # resumo
    print_summary()


if __name__ == "__main__":
    main()