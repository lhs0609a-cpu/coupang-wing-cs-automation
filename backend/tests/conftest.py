"""
Pytest Configuration and Fixtures
pytest 설정 및 픽스처
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test
    각 테스트마다 새로운 테스트 데이터베이스 생성
    """
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    FastAPI test client with test database
    테스트 데이터베이스를 사용하는 FastAPI 테스트 클라이언트
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_inquiry(test_db):
    """Create a sample inquiry for testing"""
    from app.models import Inquiry
    from datetime import datetime

    inquiry = Inquiry(
        coupang_inquiry_id="TEST_INQ_001",
        vendor_id="VENDOR_TEST",
        customer_name="테스트 고객",
        customer_id="CUST_001",
        order_number="ORDER_001",
        product_name="테스트 상품",
        inquiry_text="배송이 언제 오나요?",
        inquiry_category="shipping",
        inquiry_date=datetime.utcnow(),
        status="pending"
    )

    test_db.add(inquiry)
    test_db.commit()
    test_db.refresh(inquiry)

    return inquiry


@pytest.fixture
def sample_response(test_db, sample_inquiry):
    """Create a sample response for testing"""
    from app.models import Response
    from datetime import datetime

    response = Response(
        inquiry_id=sample_inquiry.id,
        response_text="배송은 3일 이내에 도착할 예정입니다.",
        confidence_score=0.85,
        risk_level="low",
        generation_method="ai",
        status="draft"
    )

    test_db.add(response)
    test_db.commit()
    test_db.refresh(response)

    return response


@pytest.fixture
def auth_headers():
    """Authentication headers for testing"""
    return {
        "X-API-Key": "test_api_key_12345"
    }


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test"""
    from app.core.cache import get_cache

    cache = get_cache()
    cache.clear()

    yield

    cache.clear()


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls"""
    class MockOpenAI:
        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                class MockResponse:
                    class Choice:
                        class Message:
                            content = "테스트 응답입니다."

                        message = Message()

                    choices = [Choice()]

                return MockResponse()

        chat = ChatCompletion

    monkeypatch.setattr("openai.OpenAI", lambda *args, **kwargs: MockOpenAI())

    return MockOpenAI


# Pytest configuration
def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests"
    )
