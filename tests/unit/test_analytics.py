import pytest
import pandas as pd
from app.services.analytics import calculate_assessor_agreement

def test_kappa_calculation():
    # Mock some data
    data = [
        {'task_id': 1, 'assessor_id': 101, 'score': 4},
        {'task_id': 1, 'assessor_id': 102, 'score': 4},
        {'task_id': 2, 'assessor_id': 101, 'score': 3},
        {'task_id': 2, 'assessor_id': 102, 'score': 3},
        {'task_id': 3, 'assessor_id': 101, 'score': 2},
        {'task_id': 3, 'assessor_id': 102, 'score': 1},
    ]
    df = pd.DataFrame(data)
    results = calculate_assessor_agreement(df)
    
    key = "Assessor 101 vs 102"
    assert key in results
    assert results[key]['tasks_compared'] == 3
    assert results[key]['kappa'] > 0 # Should be positive agreement
    
def test_insufficient_data():
    df = pd.DataFrame([
        {'task_id': 1, 'assessor_id': 101, 'score': 4}
    ])
    results = calculate_assessor_agreement(df)
    assert "error" in results
