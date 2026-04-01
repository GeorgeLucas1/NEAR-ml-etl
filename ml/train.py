import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import sys
# Adicionar o diretório atual ao path para poder importar a classe recém-criada
sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import AnomalyDetector, UsageRegressor

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "metrics.db"
ML_DIR = ROOT_DIR / "ml"
CLASSIFIER_PATH = ML_DIR / "model_classifier.joblib"
REGRESSOR_PATH = ML_DIR / "model_regressor.joblib"

# Métrica alvo para Regressão (nosso objetivo final é prever essa métrica futura)
TARGET_METRIC = "cpu_usage_mean"

# ─────────────────────────────────────────────
# Funções de Banco e Preparação de Dados
# ─────────────────────────────────────────────
def get_features_df() -> pd.DataFrame:
    """Busca os dados gerados na tabela de features usando pandas e o SQL."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # APRENDIZADO: Carregar direto o SQL para dentro do DataFrame do pandas
        # é eficiente e muito usado em manipulação de Data Science. Ordenamos
        # por timestamp pra garantir que a viagem no tempo de regressão (shift) fique correta!
        df = pd.read_sql_query("SELECT * FROM features ORDER BY timestamp ASC", conn)
    finally:
        conn.close()
    return df

def prepare_data(df: pd.DataFrame):
    """
    Remove colunas que não são features (como id, timestamp, etc) 
    e pra regressão, cria a coluna de 'gabarito' alvo no futuro (target_cpu).
    """
    df_sorted = df.copy().sort_values("timestamp").reset_index(drop=True)
    
    # APRENDIZADO: Por que drop_cols? 
    # O modelo não deve prever métricas com base no "ID", ele é apenas um número 
    # de banco de dados, se não tirarmos, o modelo pode ficar associando números sequenciais vazios
    # como justificativas numéricas. 
    drop_cols = ["id", "timestamp", "created_at"]
    X = df_sorted.drop(columns=[col for col in drop_cols if col in df_sorted.columns]).copy()
    
    # APRENDIZADO: O Fillna(0.0) garante que, se em alguma limpeza houve valor ausente, 
    # não passamos nulos, o Scikit-Learn explode ao ver Null em suas matrizes numéricas!
    X = X.fillna(0.0)
    
    # === A MÁGICA TEMPORAL DA REGRESSÃO ===
    # APRENDIZADO: O comando .shift(-1) pega todos os valores de cpu_usage_mean e
    # desloca 1 posição pra cima. Exemplo prático: a linha 1 da coluna alvo vai copiar a carga
    # exata que aconteceu na linha 2. Dessa forma treinamos a máquina a correlacionar:
    # "Dadas as features do Tempo 1 (X) => Elas resultaram que uso de CPU no Tempo 2 será Y"
    target = X[TARGET_METRIC].shift(-1)
    
    # Ao mexer -1, a última linha de 'target' fica vazia (NaN, porque não existe linha +1)
    # Por segurança, sempre quebramos fora a última linha para o bloco de treino da regressão
    X_reg = X.iloc[:-1].copy()
    y_reg = target.iloc[:-1].copy()
    
    # X_unsupervised: Para o IsolationForest (detector de anomalia), não existe "futuro", 
    # então mandamos toda a base original (X), ele entende apenas o "agora" normal ou não.
    return X, X_reg, y_reg


# ─────────────────────────────────────────────
# Pipeline Principal de Treinamento
# ─────────────────────────────────────────────
def train_pipeline():
    logger.info(f"Conectando ao banco de dados: {DB_PATH}")
    df = get_features_df()
    
    if df.empty:
        logger.error("Nenhum dado encontrado na tabela de features. Execute o dataSeeding.py primeiro.")
        return
        
    logger.info(f"Total de registros na tabela 'features': {len(df)}")
    
    # ── Preparação
    X_unsupervised, X_reg, y_reg = prepare_data(df)
    
    # ── 1. Pipeline Classificador (Detector de Anomalia)
    logger.info("Iniciando treinamento do Detector de Anomalias (IsolationForest)...")
    clf = AnomalyDetector(contamination=0.05, random_state=42)
    clf.fit(X_unsupervised)
    clf.save(CLASSIFIER_PATH)
    logger.success(f"Modelo Classificador treinado e exportado em binário: {CLASSIFIER_PATH.name}")
    
    # ── 2. Pipeline Regressor (Bola de Cristal do Sistema)
    logger.info(f"Iniciando treinamento do Regressor para o alvo: '{TARGET_METRIC}'...")
    
    # APRENDIZADO: Separamos o dataset em "Treino e Teste" (70/30) temporais para verificação de erro. 
    # Não devemos embaralhar dados (train_test_split sem shuffle) pois senão o modelo perde a coerência
    # de tempo antes/depois ("data leak"). Testamos se o modelo acerta o final da série como "futuro real".
    split_idx = int(len(X_reg) * 0.70)
    X_train, y_train = X_reg.iloc[:split_idx], y_reg.iloc[:split_idx]
    X_test, y_test   = X_reg.iloc[split_idx:], y_reg.iloc[split_idx:]
    
    # Criamos o modelo matemático e ensinamos ele usando o treino (70%).
    reg = UsageRegressor(random_state=42)
    reg.fit(X_train, y_train)
    
    # APRENDIZADO: AVALIAÇÃO DA INTELIGÊNCIA (Validation phase)
    # Passamos o Y_Test e geramos a predição. O quão próximo o 'y_pred' está de adivinhar o 'y_test'?
    y_pred = reg.predict(X_test)
    mse = mean_squared_error(y_test, y_pred) # Quadrado do Erro - Ajuda a punir severamente erros grandes!
    mae = mean_absolute_error(y_test, y_pred) # Erro Absoluto Médio - Média "honesta" da diferença bruta em uso (%)
    r2 = r2_score(y_test, y_pred)            # Coeficiente R2 - Nível de perfeição de 0 a 1 em relação à média geral.
    
    logger.info(f"[Avaliação do Regressor] - MSE: {mse:.4f} | MAE: {mae:.4f} | R²: {r2:.4f}")
    
    # Retreinamos para exportação usando a base de Conhecimento toda agora para ir em produção.
    reg.save(REGRESSOR_PATH)
    logger.success(f"Modelo Regressor treinado e exportado em binário: {REGRESSOR_PATH.name}")
    
    logger.info("Parabéns! O Pipeline de Treinamento da sua ML terminou de rodar.")


if __name__ == "__main__":
    train_pipeline()
