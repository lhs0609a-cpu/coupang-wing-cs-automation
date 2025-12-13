"""
Naver Account Model
네이버 API 계정 설정 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64

from ..database import Base


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


class NaverAccount(Base):
    """네이버 API 계정 설정 모델"""
    __tablename__ = "naver_accounts"

    id = Column(Integer, primary_key=True, index=True)

    # 계정 식별 정보
    name = Column(String(200), nullable=False, comment="사용자 지정 계정 이름")
    description = Column(Text, nullable=True, comment="계정 설명")

    # 네이버 API 인증 정보 (암호화 저장)
    client_id = Column(String(500), nullable=False, comment="네이버 Client ID")
    client_secret_encrypted = Column(String(500), nullable=False, comment="네이버 Client Secret (암호화)")

    # OAuth 설정
    callback_url = Column(String(500), nullable=True, comment="OAuth 콜백 URL")

    # 네이버 로그인 정보 (선택, Selenium 자동화용)
    naver_username = Column(String(200), nullable=True, comment="네이버 아이디 (선택)")
    naver_password_encrypted = Column(String(500), nullable=True, comment="네이버 비밀번호 (암호화, 선택)")

    # OAuth 토큰 (자동 저장)
    access_token_encrypted = Column(Text, nullable=True, comment="Access Token (암호화)")
    refresh_token_encrypted = Column(Text, nullable=True, comment="Refresh Token (암호화)")
    token_expires_at = Column(DateTime, nullable=True, comment="토큰 만료 시간")

    # 상태
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    is_default = Column(Boolean, default=False, comment="기본 계정 여부")
    last_used_at = Column(DateTime, nullable=True, comment="마지막 사용 시간")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성 시간")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정 시간")

    # === Property: Client Secret ===
    @property
    def client_secret(self) -> str:
        """Decrypt and return client secret"""
        return decrypt_value(self.client_secret_encrypted)

    @client_secret.setter
    def client_secret(self, value: str):
        """Encrypt and store client secret"""
        self.client_secret_encrypted = encrypt_value(value)

    # === Property: Naver Password ===
    @property
    def naver_password(self) -> str:
        """Decrypt and return naver password"""
        return decrypt_value(self.naver_password_encrypted) if self.naver_password_encrypted else ""

    @naver_password.setter
    def naver_password(self, value: str):
        """Encrypt and store naver password"""
        self.naver_password_encrypted = encrypt_value(value) if value else None

    # === Property: Access Token ===
    @property
    def access_token(self) -> str:
        """Decrypt and return access token"""
        return decrypt_value(self.access_token_encrypted) if self.access_token_encrypted else ""

    @access_token.setter
    def access_token(self, value: str):
        """Encrypt and store access token"""
        self.access_token_encrypted = encrypt_value(value) if value else None

    # === Property: Refresh Token ===
    @property
    def refresh_token(self) -> str:
        """Decrypt and return refresh token"""
        return decrypt_value(self.refresh_token_encrypted) if self.refresh_token_encrypted else ""

    @refresh_token.setter
    def refresh_token(self, value: str):
        """Encrypt and store refresh token"""
        self.refresh_token_encrypted = encrypt_value(value) if value else None

    def to_dict(self, include_secrets: bool = False, include_tokens: bool = False):
        """
        Convert to dictionary

        Args:
            include_secrets: Client Secret 포함 여부
            include_tokens: Access/Refresh Token 포함 여부
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "client_id": self.client_id,
            "callback_url": self.callback_url,
            "naver_username": self.naver_username,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_secrets:
            data["client_secret"] = self.client_secret
            data["naver_password"] = self.naver_password

        if include_tokens:
            data["access_token"] = self.access_token
            data["refresh_token"] = self.refresh_token

        return data

    def __repr__(self):
        return f"<NaverAccount(id={self.id}, name={self.name}, is_active={self.is_active})>"
