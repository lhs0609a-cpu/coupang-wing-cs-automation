"""
IP to Name Mapping Model for Upload Monitoring
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database import Base


class IPMapping(Base):
    """IP 주소와 사람 이름 매핑"""
    __tablename__ = "ip_mappings"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<IPMapping(ip={self.ip_address}, name={self.name})>"


class SheetConfig(Base):
    """Google Sheets 설정 저장"""
    __tablename__ = "sheet_configs"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(String(200), nullable=False)
    sheet_name = Column(String(100), default="Sheet1")
    date_column = Column(String(10), default="D")
    email_column = Column(String(10), default="E")
    ip_column = Column(String(10), default="F")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SheetConfig(id={self.sheet_id})>"
