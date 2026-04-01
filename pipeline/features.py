import sqlite3
import signal
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
DB_PATH      = Path(__file__).resolve().parents[1] / "data" / "metrics.db"
LOG_PATH     = Path(__file__).resolve().parents[1] / "logs" / "features.log"
INTERVAL     = 300   # segundos (5 min)
WINDOW       = 100   # tamanho da janela rolling

METRICS = [
    "cpu_usage", "cpu_temp",
    "ram_usage",
    "disk_usage", "disk_read", "disk_write",
    "net_sent", "net_recv",
    "gpu_usage", "gpu_temp",
]

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add(LOG_PATH,   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", rotation="10 MB")

# ─────────────────────────────────────────────
# Graceful shutdown
# ─────────────────────────────────────────────
running = True

def _handle_signal(sig, frame):
    global running
    logger.info(f"Sinal {sig} recebido — encerrando features...")
    running = False

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT,  _handle_signal)

# ─────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def fetch_unprocessed(conn: sqlite3.Connection) -> pd.DataFrame:
    """Busca registros de clean_metrics ainda não processados."""
    rows = conn.execute(
        "SELECT * FROM clean_metrics WHERE processed = 0 ORDER BY timestamp ASC"
    ).fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def fetch_window_context(conn: sqlite3.Connection, oldest_ts: str) -> pd.DataFrame:
    """
    Busca os últimos WINDOW registros anteriores ao oldest_ts para
    garantir janela completa mesmo no primeiro batch.
    """
    rows = conn.execute(
        """
        SELECT * FROM clean_metrics
        WHERE timestamp < ? AND processed = 1
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (oldest_ts, WINDOW),
    ).fetchall()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    return df.iloc[::-1].reset_index(drop=True)  # ordem cronológica

# ─────────────────────────────────────────────
# Feature engineering
# ─────────────────────────────────────────────
def compute_features(df: pd.DataFrame, new_ids: list[int]) -> pd.DataFrame:
    """
    Recebe o DataFrame completo (contexto + novos registros) e
    retorna apenas as features dos registros novos.
    """
    records = []

    for col in METRICS:
        # Rolling sobre a coluna inteira
        df[f"{col}_mean"]  = df[col].rolling(WINDOW, min_periods=1).mean()
        df[f"{col}_std"]   = df[col].rolling(WINDOW, min_periods=1).std().fillna(0.0)
        df[f"{col}_max"]   = df[col].rolling(WINDOW, min_periods=1).max()
        df[f"{col}_min"]   = df[col].rolling(WINDOW, min_periods=1).min()
        df[f"{col}_delta"] = df[col].diff().fillna(0.0)

        # Tendência: slope linear simples da janela
        def _trend(series: pd.Series) -> float:
            if len(series) < 2:
                return 0.0
            x = np.arange(len(series), dtype=float)
            y = series.values.astype(float)
            if np.std(x) == 0:
                return 0.0
            return float(np.polyfit(x, y, 1)[0])

        df[f"{col}_trend"] = (
            df[col]
            .rolling(WINDOW, min_periods=2)
            .apply(_trend, raw=False)
            .fillna(0.0)
        )

    # Filtra apenas os registros novos
    new_df = df[df["id"].isin(new_ids)].copy()

    feature_cols = ["id", "timestamp"] + [
        f"{col}_{feat}"
        for col in METRICS
        for feat in ["mean", "std", "max", "min", "delta", "trend"]
    ]

    return new_df[feature_cols].reset_index(drop=True)


def insert_features(conn: sqlite3.Connection, features_df: pd.DataFrame):
    """Insere as features geradas na tabela features."""
    cols   = [c for c in features_df.columns if c != "id"]
    ph     = ", ".join(["?"] * len(cols))
    fields = ", ".join(cols)

    conn.executemany(
        f"INSERT OR IGNORE INTO features ({fields}) VALUES ({ph})",
        [tuple(row[c] for c in cols) for _, row in features_df.iterrows()],
    )


def mark_processed(conn: sqlite3.Connection, ids: list[int]):
    conn.executemany(
        "UPDATE clean_metrics SET processed = 1 WHERE id = ?",
        [(i,) for i in ids],
    )

# ─────────────────────────────────────────────
# Job principal
# ─────────────────────────────────────────────
def run_features_job():
    logger.info("Iniciando job de features...")

    try:
        conn = get_connection()
    except Exception as e:
        logger.error(f"Falha ao conectar no banco: {e}")
        return

    try:
        new_df = fetch_unprocessed(conn)

        if new_df.empty:
            logger.info("Nenhum registro novo para processar.")
            return

        logger.info(f"{len(new_df)} registro(s) encontrado(s).")

        new_ids    = new_df["id"].tolist()
        oldest_ts  = new_df["timestamp"].iloc[0]

        # Busca contexto anterior para janela completa
        context_df = fetch_window_context(conn, oldest_ts)

        # Concatena contexto + novos
        full_df = (
            pd.concat([context_df, new_df], ignore_index=True)
            if not context_df.empty
            else new_df.copy()
        )

        features_df = compute_features(full_df, new_ids)

        insert_features(conn, features_df)
        mark_processed(conn, new_ids)
        conn.commit()

        logger.info(f"Job concluído — {len(features_df)} feature(s) gerada(s).")

    except Exception as e:
        logger.error(f"Erro durante o job de features: {e}", exc_info=True)
        conn.rollback()

    finally:
        conn.close()

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    logger.info(f"Features iniciado — intervalo={INTERVAL}s | janela={WINDOW} | db={DB_PATH}")

    while running:
        run_features_job()

        for _ in range(INTERVAL):
            if not running:
                break
            time.sleep(1)

    logger.info("Features encerrado.")


if __name__ == "__main__":
    main()