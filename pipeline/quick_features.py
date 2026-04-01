import sqlite3
from pathlib import Path
from datetime import datetime
import sys

# Ajustar path para rodar de qualquer diretório
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'metrics.db'

def generate_features():
    conn = sqlite3.connect(DB_PATH)
    
    # Buscar últimas 20 métricas
    rows = conn.execute("""
        SELECT cpu_usage, cpu_temp, ram_usage, disk_usage, disk_read, disk_write,
               net_sent, net_recv, gpu_usage, gpu_temp
        FROM raw_metrics 
        ORDER BY timestamp DESC
        LIMIT 20
    """).fetchall()
    
    if len(rows) < 5:
        print(f"Poucos dados: {len(rows)} registros")
        return
    
    import numpy as np
    
    # Calcular estatísticas
    data = np.array(rows)
    metrics_names = ['cpu_usage', 'cpu_temp', 'ram_usage', 'disk_usage', 
                     'disk_read', 'disk_write', 'net_sent', 'net_recv', 
                     'gpu_usage', 'gpu_temp']
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    
    features = {'timestamp': timestamp}
    
    for i, metric in enumerate(metrics_names):
        col = data[:, i]
        features[f'{metric}_mean'] = float(np.mean(col))
        features[f'{metric}_std'] = float(np.std(col))
        features[f'{metric}_max'] = float(np.max(col))
        features[f'{metric}_min'] = float(np.min(col))
        features[f'{metric}_delta'] = float(col[0] - col[-1]) if len(col) > 1 else 0
        features[f'{metric}_trend'] = float(np.polyfit(range(len(col)), col, 1)[0]) if len(col) > 1 else 0
    
    # Inserir no banco
    cols = ', '.join(features.keys())
    placeholders = ', '.join(['?' for _ in features])
    
    conn.execute(f"INSERT INTO features ({cols}) VALUES ({placeholders})", 
                 list(features.values()))
    conn.commit()
    conn.close()
    
    print(f"Features geradas com sucesso para {timestamp}")

if __name__ == "__main__":
    generate_features()
