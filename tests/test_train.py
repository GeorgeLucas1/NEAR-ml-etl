import pytest
import pandas as pd
from ml.train import prepare_data

@pytest.fixture
def sample_db_data():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "timestamp": ["2026-03-27T20:00:00Z", "2026-03-27T20:05:00Z", "2026-03-27T20:10:00Z"],
        "cpu_usage_mean": [10.0, 20.0, 30.0],
        "ram_usage_mean": [15.0, 25.0, 35.0],
        "created_at": ["T", "T", "T"]
    })

def test_prepare_data_drops_non_features(sample_db_data):
    X, X_reg, y_reg = prepare_data(sample_db_data)
    
    # As colunas irrelevantes devem ser dropadas
    assert "id" not in X.columns
    assert "timestamp" not in X.columns
    assert "created_at" not in X.columns
    
    # Mas as features devem ser mantidas
    assert "cpu_usage_mean" in X.columns
    assert "ram_usage_mean" in X.columns

def test_prepare_data_targets_shift(sample_db_data):
    X, X_reg, y_reg = prepare_data(sample_db_data)
    
    # y_reg deve corresponder à próxima leitura de cpu_usage_mean
    # O df de entrada tem cpu_usage_mean = [10.0, 20.0, 30.0]
    # O y_reg deve ser [20.0, 30.0]
    assert len(y_reg) == 2
    assert y_reg.iloc[0] == 20.0
    assert y_reg.iloc[1] == 30.0
    
    # X_reg deve ser sincronizado com y_reg
    # logo o primeiro X_reg deve ter cpu_usage_mean = 10.0
    assert len(X_reg) == 2
    assert X_reg.iloc[0]["cpu_usage_mean"] == 10.0
