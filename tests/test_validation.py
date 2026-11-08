import pytest
from app.services.spam import spam_service
from app.services.validation import validation_service
from app.services.reference import reference_service

def test_device_hash_reproducibility():
    h1 = spam_service.compute_device_hash("192.168.1.10", "Mozilla/5.0")
    h2 = spam_service.compute_device_hash("192.168.1.10", "Mozilla/5.0")
    h3 = spam_service.compute_device_hash("192.168.1.11", "Mozilla/5.0")
    
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 length

def test_honeypot_detection():
    assert spam_service.check_honeypot(None) is True
    assert spam_service.check_honeypot("") is True
    assert spam_service.check_honeypot("http://spam-link.com") is False

def test_rate_limiter():
    test_hash = "test_device_rate_limit_hash"
    # Clean previous state
    spam_service.submissions[test_hash] = []

    # First 5 submissions allowed
    for _ in range(5):
        assert spam_service.check_rate_limit(test_hash) is True
    
    # 6th submission blocked
    assert spam_service.check_rate_limit(test_hash) is False

def test_category_validation():
    reference_service.load()
    assert validation_service.validate_category("Late/not arrived") is True
    assert validation_service.validate_category("Invalid_Fake_Category") is False
