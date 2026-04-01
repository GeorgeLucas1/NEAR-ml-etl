import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from ml.model import AnomalyDetector, UsageRegressor

@pytest.fixture
def dummy_data():
    # Cria os mesmos padrões de features da nossa tabela
    data = {
        "cpu_usage_mean": [10.0, 20.0, 95.0, 15.0, 25.0],
        "ram_usage_mean": [50.0, 52.0, 99.0, 51.0, 50.0],
        "disk_write_delta": [0.0, 1.0, 500.0, 0.0, 2.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def dummy_target():
    return pd.Series([20.0, 95.0, 15.0, 25.0, 10.0])

def test_anomaly_detector_training(dummy_data):
    detector = AnomalyDetector(contamination=0.2)
    detector.fit(dummy_data)
    
    # O modelo deve salvar as features usadas
    assert len(detector.features) == 3
    assert "cpu_usage_mean" in detector.features
    
    # Prever anomalias - Retorna um array do mesmo tamanho do X (-1 ou 1)
    preds = detector.predict(dummy_data)
    assert len(preds) == len(dummy_data)
    assert all(p in [-1, 1] for p in preds)

def test_anomaly_detector_save_load(dummy_data, tmp_path):
    model_path = tmp_path / "model_classifier.joblib"
    
    detector = AnomalyDetector(contamination=0.2)
    detector.fit(dummy_data)
    detector.save(model_path)
    
    # Verificar se o arquivo foi criado
    assert model_path.exists()
    
    # Carregar modelo instanciando novamente
    loaded_detector = AnomalyDetector.load(model_path)
    assert loaded_detector.features == detector.features
    
    # As previsões de ambos devem ser iguais
    preds_original = detector.predict(dummy_data)
    preds_loaded = loaded_detector.predict(dummy_data)
    np.testing.assert_array_equal(preds_original, preds_loaded)

def test_usage_regressor_training(dummy_data, dummy_target):
    regressor = UsageRegressor(random_state=42)
    regressor.fit(dummy_data, dummy_target)
    
    assert len(regressor.features) == 3
    
    # Prever sobre si test_usage_regressormesmo -> O tamanho do output precisa ser o mesmo
    preds = regressor.predict(dummy_data)
    assert len(preds) == len(dummy_data)
    # Tem que retornar um array de floats
    assert isinstance(preds[0], (float, np.floating))

def test_usage_regressor_save_load(dummy_data, dummy_target, tmp_path):
    model_path = tmp_path / "model_regressor.joblib"
    
    regressor = UsageRegressor(random_state=42)
    regressor.fit(dummy_data, dummy_target)
    regressor.save(model_path)
    
    assert model_path.exists()
    
    loaded_regressor = UsageRegressor.load(model_path)
    assert loaded_regressor.features == regressor.features
    
    preds_original = regressor.predict(dummy_data)
    preds_loaded = loaded_regressor.predict(dummy_data)
    np.testing.assert_array_almost_equal(preds_original, preds_loaded)
