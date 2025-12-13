"""
Coupang Account Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

from ..database import Base

# Load .env file before accessing environment variables
backend_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if backend_env_path.exists():
    load_dotenv(backend_env_path)


# 암호화 키 생성 (환경 변수에서 가져오거나 자동 생성)
def get_encryption_key():
    """Get or create encryption key for sensitive data"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # 새로운 키 생성 (프로덕션에서는 환경 변수로 설정해야 함)
        key = Fernet.generate_key().decode()
    return key.encode() if isinstance(key, str) else key


ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    """Encrypt sensitive value"""
    if not value:
        return ""
    encrypted = cipher_suite.encrypt(value.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt sensitive value"""
    if not encrypted_value:
        return ""
    try:
        decoded = base64.b64decode(encrypted_value.encode())
        decrypted = cipher_suite.decrypt(decoded)
        return decrypted.decode()
    except Exception:
        return ""


class CoupangAccount(Base):
    """쿠팡 계정 정보 모델"""
    __tablename__ = "coupang_accounts"

    id = Column(Integer, primary_key=True, index=True)

    # 계정 식별 정보
    name = Column(String(200), nullable=False)  # 사용자 지정 계정 이름

    # 쿠팡 API 인증 정보 (암호화 저장)
    vendor_id = Column(String(500), nullable=False)  # 업체코드
    access_key_encrypted = Column(String(500), nullable=False)  # 액세스키 (암호화)
    secret_key_encrypted = Column(String(500), nullable=False)  # 시크릿키 (암호화)
    wing_username = Column(String(200))  # Wing 사용자명 (선택)
    wing_password_encrypted = Column(String(500))  # Wing 비밀번호 (암호화, 선택)

    # 상태
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def access_key(self) -> str:
        """Decrypt and return access key"""
        return decrypt_value(self.access_key_encrypted)

    @access_key.setter
    def access_key(self, value: str):
        """Encrypt and store access key"""
        self.access_key_encrypted = encrypt_value(value)

    @property
    def secret_key(self) -> str:
        """Decrypt and return secret key"""
        return decrypt_value(self.secret_key_encrypted)

    @secret_key.setter
    def secret_key(self, value: str):
        """Encrypt and store secret key"""
        self.secret_key_encrypted = encrypt_value(value)

    @property
    def wing_password(self) -> str:
        """Decrypt and return wing password"""
        return decrypt_value(self.wing_password_encrypted) if self.wing_password_encrypted else ""

    @wing_password.setter
    def wing_password(self, value: str):
        """Encrypt and store wing password"""
        self.wing_password_encrypted = encrypt_value(value) if value else None

    def to_dict(self, include_keys: bool = True):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "vendor_id": self.vendor_id,
            "wing_username": self.wing_username,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_keys:
            data["access_key"] = self.access_key
            data["secret_key"] = self.secret_key
            data["wing_password"] = self.wing_password

        return data
