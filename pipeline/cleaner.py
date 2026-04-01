import sqlite3
import logging
import time
import signal
import sys
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
DB_PATH      = Path(__file__).resolve().parents[1] / "data" / "metrics.db"
LOG_PATH     = Path(__file__).resolve().parents[1] / "logs" / "cleaner.log"
INTERVAL     = 60  # segundos

# Limites de outlier por métrica
OUTLIER_BOUNDS: dict[str, tuple[float, float]] = {
    "cpu_usage":      (0.0,   100.0),
    "cpu_temp":       (0.0,   120.0),  # °C
    "ram_usage":      (0.0,   100.0),
    "disk_usage":     (0.0,   100.0),
    "disk_read":      (0.0,   1e12),   # bytes total
    "disk_write":     (0.0,   1e12),
    "net_sent":       (0.0,   1e13),   # bytes total (acumulado)
    "net_recv":       (0.0,   1e13),
    "gpu_usage":      (0.0,   100.0),
    "gpu_temp":       (0.0,   120.0),
}

# Faixas para normalização min-max por métrica
NORM_RANGES: dict[str, tuple[float, float]] = {
    "cpu_usage":  (0.0, 100.0),
    "cpu_temp":   (0.0, 120.0),
    "ram_usage":  (0.0, 100.0),
    "disk_usage": (0.0, 100.0),
    "disk_read":  (0.0, 1e12),
    "disk_write": (0.0, 1e12),
    "net_sent":   (0.0, 1e13),
    "net_recv":   (0.0, 1e13),
    "gpu_usage":  (0.0, 100.0),
    "gpu_temp":   (0.0, 120.0),
}

METRICS = list(OUTLIER_BOUNDS.keys())

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("cleaner")

# ─────────────────────────────────────────────
# Graceful shutdown
# ─────────────────────────────────────────────
running = True

def _handle_signal(sig, frame):
    global running
    log.info(f"Sinal {sig} recebido — encerrando cleaner...")
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


def fetch_unprocessed(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Busca todos os registros de raw_metrics ainda não processados."""
    return conn.execute(
        "SELECT * FROM raw_metrics WHERE processed = 0 ORDER BY timestamp ASC"
    ).fetchall()


def is_duplicate(conn: sqlite3.Connection, timestamp: str) -> bool:
    """Verifica se já existe um registro com o mesmo timestamp em clean_metrics."""
    row = conn.execute(
        "SELECT 1 FROM clean_metrics WHERE timestamp = ?", (timestamp,)
    ).fetchone()
    return row is not None

# ─────────────────────────────────────────────
# Limpeza
# ─────────────────────────────────────────────
def has_nulls(row: sqlite3.Row) -> bool:
    return any(row[col] is None for col in METRICS)


def has_outlier(row: sqlite3.Row) -> bool:
    for col, (lo, hi) in OUTLIER_BOUNDS.items():
        val = row[col]
        if val is not None and not (lo <= val <= hi):
            return True
    return False


def normalize(value: float, col: str) -> float:
    lo, hi = NORM_RANGES[col]
    if hi == lo:
        return 0.0
    return round((value - lo) / (hi - lo), 6)


def clean_row(row: sqlite3.Row) -> dict | None:
    """
    Aplica todas as etapas de limpeza a um registro.
    Retorna None se o registro deve ser descartado.
    """
    if has_nulls(row):
        log.debug(f"Descartando id={row['id']} — valores nulos")
        return None

    if has_outlier(row):
        log.debug(f"Descartando id={row['id']} — outlier detectado")
        return None

    return {
        "timestamp":   row["timestamp"],
        "cpu_usage":   normalize(row["cpu_usage"],   "cpu_usage"),
        "cpu_temp":    normalize(row["cpu_temp"],     "cpu_temp"),
        "ram_usage":   normalize(row["ram_usage"],    "ram_usage"),
        "disk_usage":  normalize(row["disk_usage"],   "disk_usage"),
        "disk_read":   normalize(row["disk_read"],    "disk_read"),
        "disk_write":  normalize(row["disk_write"],   "disk_write"),
        "net_sent":    normalize(row["net_sent"],     "net_sent"),
        "net_recv":    normalize(row["net_recv"],     "net_recv"),
        "gpu_usage":   normalize(row["gpu_usage"],    "gpu_usage"),
        "gpu_temp":    normalize(row["gpu_temp"],     "gpu_temp"),
    }

# ─────────────────────────────────────────────
# Job principal
# ─────────────────────────────────────────────
def run_cleaning_job():
    log.info("Iniciando job de limpeza...")

    try:
        conn = get_connection()
    except Exception as e:
        log.error(f"Falha ao conectar no banco: {e}")
        return

    try:
        rows = fetch_unprocessed(conn)

        if not rows:
            log.info("Nenhum registro novo para processar.")
            return

        log.info(f"{len(rows)} registro(s) encontrado(s) para limpar.")

        inserted     = 0
        discarded    = 0
        duplicated   = 0
        raw_ids_done = []

        for row in rows:
            # Deduplicação
            if is_duplicate(conn, row["timestamp"]):
                log.debug(f"Duplicata ignorada — timestamp={row['timestamp']}")
                duplicated += 1
                raw_ids_done.append(row["id"])
                continue

            cleaned = clean_row(row)

            if cleaned is None:
                discarded += 1
            else:
                conn.execute(
                    """
                    INSERT INTO clean_metrics (
                        timestamp,
                        cpu_usage, cpu_temp,
                        ram_usage,
                        disk_usage, disk_read, disk_write,
                        net_sent, net_recv,
                        gpu_usage, gpu_temp
                    ) VALUES (
                        :timestamp,
                        :cpu_usage, :cpu_temp,
                        :ram_usage,
                        :disk_usage, :disk_read, :disk_write,
                        :net_sent, :net_recv,
                        :gpu_usage, :gpu_temp
                    )
                    """,
                    cleaned,
                )
                inserted += 1

            raw_ids_done.append(row["id"])

        # Marca todos como processados
        if raw_ids_done:
            conn.executemany(
                "UPDATE raw_metrics SET processed = 1 WHERE id = ?",
                [(rid,) for rid in raw_ids_done],
            )

        conn.commit()

        log.info(
            f"Job concluído — inseridos={inserted} | "
            f"descartados={discarded} | duplicatas={duplicated}"
        )

    except Exception as e:
        log.error(f"Erro durante o job de limpeza: {e}", exc_info=True)
        conn.rollback()

    finally:
        conn.close()

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    log.info(f"Cleaner iniciado — intervalo={INTERVAL}s | db={DB_PATH}")

    while running:
        run_cleaning_job()

        # Aguarda o intervalo respeitando sinais de shutdown
        for _ in range(INTERVAL):
            if not running:
                break
            time.sleep(1)

    log.info("Cleaner encerrado.")


if __name__ == "__main__":
    main()