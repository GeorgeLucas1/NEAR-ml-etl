import sqlite3
import sys
from pathlib import Path

from loguru import logger

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
DB_PATH  = Path(__file__).resolve().parents[1] / "data" / "metrics.db"
LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "init_db.log"

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(LOG_PATH,   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# ─────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────
DDL = [
    # coletar atraves de rust por conta da perfomance
    # ── raw_metrics ───────────────────────────────────────────────────────────
    # Escrita pelo collector (Rust). Dados brutos, sem normalização.
    """
    CREATE TABLE IF NOT EXISTS raw_metrics (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL UNIQUE,

        cpu_usage   REAL,   -- %
        cpu_temp    REAL,   -- °C
        ram_usage   REAL,   -- %
        disk_usage  REAL,   -- %
        disk_read   REAL,   -- bytes/s
        disk_write  REAL,   -- bytes/s
        net_sent    REAL,   -- bytes/s
        net_recv    REAL,   -- bytes/s
        gpu_usage   REAL,   -- %
        gpu_temp    REAL,   -- °C

        processed   INTEGER NOT NULL DEFAULT 0,  -- 0=pendente | 1=limpo
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
    """,

    # ── clean_metrics ─────────────────────────────────────────────────────────
    # Escrita pelo cleaner.py. Valores normalizados [0, 1], sem nulos/outliers.
    """
    CREATE TABLE IF NOT EXISTS clean_metrics (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL UNIQUE,

        cpu_usage   REAL    NOT NULL,
        cpu_temp    REAL    NOT NULL,
        ram_usage   REAL    NOT NULL,
        disk_usage  REAL    NOT NULL,
        disk_read   REAL    NOT NULL,
        disk_write  REAL    NOT NULL,
        net_sent    REAL    NOT NULL,
        net_recv    REAL    NOT NULL,
        gpu_usage   REAL    NOT NULL,
        gpu_temp    REAL    NOT NULL,

        processed   INTEGER NOT NULL DEFAULT 0,  -- 0=pendente | 1=features geradas
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
    """,

    # ── features ─────────────────────────────────────────────────────────────
    # Escrita pelo features.py. 60 colunas (10 métricas × 6 features).
    """
    CREATE TABLE IF NOT EXISTS features (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL UNIQUE,

        -- CPU usage
        cpu_usage_mean   REAL NOT NULL,
        cpu_usage_std    REAL NOT NULL,
        cpu_usage_max    REAL NOT NULL,
        cpu_usage_min    REAL NOT NULL,
        cpu_usage_delta  REAL NOT NULL,
        cpu_usage_trend  REAL NOT NULL,

        -- CPU temperature
        cpu_temp_mean    REAL NOT NULL,
        cpu_temp_std     REAL NOT NULL,
        cpu_temp_max     REAL NOT NULL,
        cpu_temp_min     REAL NOT NULL,
        cpu_temp_delta   REAL NOT NULL,
        cpu_temp_trend   REAL NOT NULL,

        -- RAM
        ram_usage_mean   REAL NOT NULL,
        ram_usage_std    REAL NOT NULL,
        ram_usage_max    REAL NOT NULL,
        ram_usage_min    REAL NOT NULL,
        ram_usage_delta  REAL NOT NULL,
        ram_usage_trend  REAL NOT NULL,

        -- Disk usage
        disk_usage_mean  REAL NOT NULL,
        disk_usage_std   REAL NOT NULL,
        disk_usage_max   REAL NOT NULL,
        disk_usage_min   REAL NOT NULL,
        disk_usage_delta REAL NOT NULL,
        disk_usage_trend REAL NOT NULL,

        -- Disk read
        disk_read_mean   REAL NOT NULL,
        disk_read_std    REAL NOT NULL,
        disk_read_max    REAL NOT NULL,
        disk_read_min    REAL NOT NULL,
        disk_read_delta  REAL NOT NULL,
        disk_read_trend  REAL NOT NULL,

        -- Disk write
        disk_write_mean  REAL NOT NULL,
        disk_write_std   REAL NOT NULL,
        disk_write_max   REAL NOT NULL,
        disk_write_min   REAL NOT NULL,
        disk_write_delta REAL NOT NULL,
        disk_write_trend REAL NOT NULL,

        -- Network sent
        net_sent_mean    REAL NOT NULL,
        net_sent_std     REAL NOT NULL,
        net_sent_max     REAL NOT NULL,
        net_sent_min     REAL NOT NULL,
        net_sent_delta   REAL NOT NULL,
        net_sent_trend   REAL NOT NULL,

        -- Network recv
        net_recv_mean    REAL NOT NULL,
        net_recv_std     REAL NOT NULL,
        net_recv_max     REAL NOT NULL,
        net_recv_min     REAL NOT NULL,
        net_recv_delta   REAL NOT NULL,
        net_recv_trend   REAL NOT NULL,

        -- GPU usage
        gpu_usage_mean   REAL NOT NULL,
        gpu_usage_std    REAL NOT NULL,
        gpu_usage_max    REAL NOT NULL,
        gpu_usage_min    REAL NOT NULL,
        gpu_usage_delta  REAL NOT NULL,
        gpu_usage_trend  REAL NOT NULL,

        -- GPU temperature
        gpu_temp_mean    REAL NOT NULL,
        gpu_temp_std     REAL NOT NULL,
        gpu_temp_max     REAL NOT NULL,
        gpu_temp_min     REAL NOT NULL,
        gpu_temp_delta   REAL NOT NULL,
        gpu_temp_trend   REAL NOT NULL,

        created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
    """,

    # ── anomalies ─────────────────────────────────────────────────────────────
    # Detecção de anomalias pelo modelo ML
    """
    CREATE TABLE IF NOT EXISTS anomalies (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT    NOT NULL,
        metric      TEXT    NOT NULL,
        value       REAL    NOT NULL,
        threshold   REAL    NOT NULL,
        severity    TEXT    NOT NULL,  -- low, medium, high
        type        TEXT    NOT NULL,  -- spike, drop, anomaly
        created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
    """,

    # ─────────────────────────────────────────────────────────────────────────
    # Índices
    # ─────────────────────────────────────────────────────────────────────────
    "CREATE INDEX IF NOT EXISTS idx_raw_processed   ON raw_metrics   (processed)",
    "CREATE INDEX IF NOT EXISTS idx_raw_timestamp   ON raw_metrics   (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_clean_processed ON clean_metrics (processed)",
    "CREATE INDEX IF NOT EXISTS idx_clean_timestamp ON clean_metrics (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_feat_timestamp  ON features      (timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomalies   (timestamp)",
]

# ─────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────
def init_db():
    logger.info(f"Inicializando banco em {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")

        for statement in DDL:
            conn.execute(statement)

        conn.commit()
        conn.close()

        logger.info("Banco inicializado com sucesso — tabelas: raw_metrics, clean_metrics, features")

    except Exception as e:
        logger.error(f"Falha ao inicializar banco: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    init_db()