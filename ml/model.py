import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest, RandomForestRegressor

# ─────────────────────────────────────────────
# Utils de Segurança Robusta para Produção
# ─────────────────────────────────────────────
def _validate_input(X, expected_features=None):
    """
    APRENDIZADO / SEGURANÇA: Esta é a barreira de validação que protege seu modelo em Produção.
    Sem isso, passar colunas faltantes silenciosamente estouraria o Scikit-Learn e derrubaria a API de Go conectada nas pontas.
    
    Regras estritas (Type Guard / Validations):
    1. Não aceita dados vazios
    2. Exige o tipo DataFrame da biblioteca pandas
    3. Exclui Strings maliciosas - o modelo numérico necessita de float/int
    4. Checa os nomes e ausências das Features, e acima de tudo ORDENA o dataset
       na mesma métrica temporal com as quais foi treinado.
    """
    # 1. Validação de Vazio
    if X is None or (isinstance(X, pd.DataFrame) and X.empty) or len(X) == 0:
        raise ValueError("[Validação ML] -> A matriz de entrada (X) esvaziou! O DataFrame de features passado contém 0 registros.")
        
    # 2. Validação de Tipo
    if not isinstance(X, pd.DataFrame):
        raise TypeError("[Validação ML] -> Formato rejeitado. O X precisa ser um 'pd.DataFrame'.")

    # 3. Conversão de Tipos Rigorosa (Sem permissão pra strings)
    try:
        X_numeric = X.apply(pd.to_numeric)
    except Exception as e:
        raise TypeError(f"[Validação ML] -> A entrada contém campos indesejados (Strings ou Caracteres não-numéricos) em métricas que deveriam ser numéricas: {e}")
        
    # 4. Avaliação de Feature-Mismatch contra o cérebro Original
    if expected_features is not None:
        if not expected_features:
            raise ValueError("[Validação ML] -> Operação Negada! Este modelo de predição está zerado e parece não ter sido treinado com o .fit() ainda.")
            
        missing_cols = set(expected_features) - set(X_numeric.columns)
        if missing_cols:
            raise ValueError(f"[Validação ML] -> Colunas vitais faltando no payload recebido em tempo real de execução: {missing_cols}")
        
        # Garante a ordenação exata
        X_numeric = X_numeric[expected_features]
    
    # 5. Avaliação de Lixo/Nulos gerados em tempo de execução
    if X_numeric.isnull().values.any():
        raise ValueError("[Validação ML] -> NaN Detectado! Uma variável no seu batch continha algo sem valor.")

    return X_numeric


# ─────────────────────────────────────────────
# Modelos 
# ─────────────────────────────────────────────
class AnomalyDetector:
    def __init__(self, contamination=0.05, random_state=42):
        """
        Modelo não-supervisionado para detectar anomalias nas métricas gerais do sistema.
        
        APRENDIZADO: O IsolationForest constrói várias "árvores de decisão" aleatórias (uma floresta). 
        Ele tenta separar os dados. Aqueles que são separados rapidamente (com poucos cortes) 
        são consideradas anomalias (outliers), pois são muito diferentes da "massa" normal.
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1            
        )
        self.features = []

    def fit(self, X):
        """
        APRENDIZADO: A fase de 'fit' é onde o modelo aprende. Neste caso, como é não-supervisionado,
        ele apenas lê X e desenha um limite de decisão. Agora com validação.
        """
        X_val = _validate_input(X, expected_features=None)
        self.features = list(X_val.columns)
        self.model.fit(X_val)

    def predict(self, X):
        """
        APRENDIZADO: A fase de 'predict' testa novos dados. O IsolationForest retorna:
        -1 para anomalias e 1 para inliers (dados normais).
        Passamos o "expected_features" garantindo compatibilidade de tipos e que nenhuma coluna sumiu do nada!
        """
        X_val = _validate_input(X, expected_features=self.features)
        return self.model.predict(X_val)

    def save(self, filepath: Path):
        """
        APRENDIZADO: Converte do Cérebro RAM para uma persistência binária.
        """
        joblib.dump({"model": self.model, "features": self.features}, filepath)

    @classmethod
    def load(cls, filepath: Path):
        """
        APRENDIZADO: Restaura o modelo treinado a partir de um binário joblib salvo anteriomente.
        """
        data = joblib.load(filepath)
        instance = cls() 
        instance.model = data["model"]     
        instance.features = data["features"] 
        return instance


class UsageRegressor:
    def __init__(self, random_state=42):
        """
        Modelo regressor para prever métricas matemáticas futuras (ex: cpu_usage_mean).
        
        APRENDIZADO: O RandomForestRegressor cria dezenas de árvores (n_estimators=100)
        com profundidade limitada, e unifica as suposições da floresta em um valor final preditivo contínuo.
        """
        self.model = RandomForestRegressor(
            n_estimators=100,  
            max_depth=10,      
            random_state=random_state,
            n_jobs=-1
        )
        self.features = []

    def fit(self, X, y):
        """
        APRENDIZADO: Modelo Supervisionado o qual avaliamos o y.
        """
        X_val = _validate_input(X, expected_features=None)
        
        # O target y também carece de validação básica pra bater numéricamente com X
        if y is None or len(y) != len(X_val):
            raise ValueError("[Validação ML] -> O Gabarito temporal 'y' é ausente ou de tamanho desigual ao dataset X.")
            
        self.features = list(X_val.columns)
        self.model.fit(X_val, y)

    def predict(self, X):
        """
        APRENDIZADO: A IA preditora agora é "Blindada" e garantirá que o Back-End em Golang 
        nos entregue com precisão as features de X para ela tentar extrapolar Y no futuro.
        """
        X_val = _validate_input(X, expected_features=self.features)
        return self.model.predict(X_val)

    def save(self, filepath: Path):
        joblib.dump({"model": self.model, "features": self.features}, filepath)

    @classmethod
    def load(cls, filepath: Path):
        data = joblib.load(filepath)
        instance = cls()
        instance.model = data["model"]
        instance.features = data["features"]
        return instance
