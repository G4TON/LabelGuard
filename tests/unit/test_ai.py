import pytest
from app.services.ai import ai_service
from app.config import config

def test_demo_ai_qp_suggestion():
    worker_data = {"trade": "Plumbing", "experience": 5, "declaration": "I am a plumber"}
    available_qps = [{"id": "QP-DEMO-001"}]
    
    # Ensure demo mode for test
    ai_service.is_demo = True
    result = ai_service.suggest_qualification_pack(worker_data, available_qps)
    
    assert result["suggested_qp_id"] == "QP-DEMO-001"
    assert "confidence" in result
    
def test_demo_ai_evidence_review():
    ai_service.is_demo = True
    result = ai_service.review_evidence("Test task", {}, "Some text evidence")
    
    assert result["suggested_score"] == 3
    assert result["requires_human"] == True
