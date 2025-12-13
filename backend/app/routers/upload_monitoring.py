"""
Upload Monitoring Router
Google Sheets 데이터 기반 상품 업로드 모니터링
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import httpx
import json
import re
from loguru import logger

from ..database import get_db
from ..models.ip_mapping import IPMapping, SheetConfig

router = APIRouter(prefix="/upload-monitoring", tags=["upload-monitoring"])


# Pydantic Models
class IPMappingCreate(BaseModel):
    ip_address: str
    name: str


class IPMappingUpdate(BaseModel):
    name: str


class SheetConfigCreate(BaseModel):
    sheet_id: str
    sheet_name: Optional[str] = "Sheet1"
    date_column: Optional[str] = "D"
    email_column: Optional[str] = "E"
    ip_column: Optional[str] = "F"


class DateRange(BaseModel):
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
    preset: Optional[str] = None      # today, week, month, 3months


# Helper Functions
def parse_korean_date(date_str: str) -> Optional[datetime]:
    """한국어 날짜 형식 파싱: '2025. 11. 18. 오전 10:37:41'"""
    try:
        # 정규식으로 날짜 파싱
        pattern = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(오전|오후)\s*(\d{1,2}):(\d{2}):(\d{2})'
        match = re.match(pattern, date_str.strip())

        if match:
            year, month, day, am_pm, hour, minute, second = match.groups()
            hour = int(hour)

            # 오후 처리
            if am_pm == '오후' and hour != 12:
                hour += 12
            elif am_pm == '오전' and hour == 12:
                hour = 0

            return datetime(int(year), int(month), int(day), hour, int(minute), int(second))

        # 간단한 형식도 시도: YYYY-MM-DD
        try:
            return datetime.strptime(date_str.strip(), '%Y-%m-%d')
        except:
            pass

        return None
    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        return None


def column_letter_to_index(letter: str) -> int:
    """열 문자를 인덱스로 변환 (A=0, B=1, ...)"""
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


async def fetch_google_sheet_data(sheet_id: str, gid: str = "0") -> List[List]:
    """Google Sheets에서 데이터 가져오기 (공개 시트)"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json&gid={gid}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Google Sheets 접근 실패. 시트가 공개 설정인지 확인하세요.")

        # Google Visualization API 응답 파싱
        text = response.text

        # 응답에서 JSON 부분 추출
        start = text.find('(') + 1
        end = text.rfind(')')
        json_str = text[start:end]

        data = json.loads(json_str)

        rows = []
        if 'table' in data and 'rows' in data['table']:
            for row in data['table']['rows']:
                row_data = []
                if 'c' in row:
                    for cell in row['c']:
                        if cell and 'v' in cell:
                            row_data.append(cell['v'])
                        else:
                            row_data.append(None)
                rows.append(row_data)

        return rows


def get_date_range(preset: str) -> tuple:
    """프리셋에 따른 날짜 범위 반환"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if preset == 'today':
        return today, today + timedelta(days=1)
    elif preset == 'week':
        return today - timedelta(days=7), today + timedelta(days=1)
    elif preset == 'month':
        return today - timedelta(days=30), today + timedelta(days=1)
    elif preset == '3months':
        return today - timedelta(days=90), today + timedelta(days=1)
    else:
        return today - timedelta(days=30), today + timedelta(days=1)


# API Endpoints

@router.get("/data")
async def get_upload_data(
    preset: str = "month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Google Sheets에서 업로드 데이터 조회 및 집계
    """
    # 시트 설정 가져오기
    config = db.query(SheetConfig).first()
    if not config:
        # 기본 시트 ID 사용 (사용자가 제공한 것)
        sheet_id = "1wBxJlm1_p3BJAi16hcgw0XxlnW4Fquk_gfm9dtE4QR0"
        date_col = 3  # D열 (0-indexed)
        email_col = 4  # E열
        ip_col = 5     # F열
    else:
        sheet_id = config.sheet_id
        date_col = column_letter_to_index(config.date_column)
        email_col = column_letter_to_index(config.email_column)
        ip_col = column_letter_to_index(config.ip_column)

    # 날짜 범위 설정
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    else:
        start_dt, end_dt = get_date_range(preset)

    try:
        # Google Sheets 데이터 가져오기
        rows = await fetch_google_sheet_data(sheet_id)

        # IP 매핑 가져오기
        ip_mappings = {m.ip_address: m.name for m in db.query(IPMapping).all()}

        # 데이터 집계
        daily_stats = {}  # {날짜: {IP: count}}
        ip_totals = {}    # {IP: total_count}
        unique_ips = set()

        for row in rows:
            if len(row) <= max(date_col, ip_col):
                continue

            date_val = row[date_col] if date_col < len(row) else None
            ip_val = row[ip_col] if ip_col < len(row) else None

            if not date_val or not ip_val:
                continue

            # 날짜 파싱
            parsed_date = parse_korean_date(str(date_val))
            if not parsed_date:
                continue

            # 날짜 범위 필터
            if parsed_date < start_dt or parsed_date >= end_dt:
                continue

            date_key = parsed_date.strftime('%Y-%m-%d')
            ip_str = str(ip_val).strip()

            unique_ips.add(ip_str)

            # 일별 통계
            if date_key not in daily_stats:
                daily_stats[date_key] = {}
            if ip_str not in daily_stats[date_key]:
                daily_stats[date_key][ip_str] = 0
            daily_stats[date_key][ip_str] += 1

            # IP별 총계
            if ip_str not in ip_totals:
                ip_totals[ip_str] = 0
            ip_totals[ip_str] += 1

        # 차트 데이터 형식으로 변환
        chart_data = []
        sorted_dates = sorted(daily_stats.keys())

        for date in sorted_dates:
            entry = {"date": date}
            for ip in unique_ips:
                # IP를 이름으로 변환
                display_name = ip_mappings.get(ip, ip)
                entry[display_name] = daily_stats[date].get(ip, 0)
            chart_data.append(entry)

        # 개인별 통계
        person_stats = []
        for ip, total in sorted(ip_totals.items(), key=lambda x: -x[1]):
            display_name = ip_mappings.get(ip, ip)

            # 오늘 업로드 수
            today_key = datetime.now().strftime('%Y-%m-%d')
            today_count = daily_stats.get(today_key, {}).get(ip, 0)

            # 어제 업로드 수
            yesterday_key = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            yesterday_count = daily_stats.get(yesterday_key, {}).get(ip, 0)

            # 평균 (기간 내)
            days_with_data = sum(1 for d in daily_stats if ip in daily_stats[d])
            avg = round(total / max(days_with_data, 1), 1)

            person_stats.append({
                "ip": ip,
                "name": display_name,
                "today": today_count,
                "yesterday": yesterday_count,
                "total": total,
                "average": avg
            })

        # 고유 이름 목록 (차트 범례용)
        unique_names = [ip_mappings.get(ip, ip) for ip in unique_ips]

        return {
            "success": True,
            "chart_data": chart_data,
            "person_stats": person_stats,
            "unique_names": unique_names,
            "date_range": {
                "start": start_dt.strftime('%Y-%m-%d'),
                "end": (end_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            },
            "total_records": sum(ip_totals.values())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sheet data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# IP Mapping CRUD

@router.get("/ip-mappings")
async def get_ip_mappings(db: Session = Depends(get_db)):
    """IP-이름 매핑 목록 조회"""
    mappings = db.query(IPMapping).all()
    return {
        "success": True,
        "mappings": [
            {"id": m.id, "ip_address": m.ip_address, "name": m.name}
            for m in mappings
        ]
    }


@router.post("/ip-mappings")
async def create_ip_mapping(mapping: IPMappingCreate, db: Session = Depends(get_db)):
    """IP-이름 매핑 생성"""
    existing = db.query(IPMapping).filter(IPMapping.ip_address == mapping.ip_address).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 IP 주소입니다.")

    new_mapping = IPMapping(
        ip_address=mapping.ip_address,
        name=mapping.name
    )
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    return {
        "success": True,
        "mapping": {
            "id": new_mapping.id,
            "ip_address": new_mapping.ip_address,
            "name": new_mapping.name
        }
    }


@router.put("/ip-mappings/{ip_address}")
async def update_ip_mapping(
    ip_address: str,
    update: IPMappingUpdate,
    db: Session = Depends(get_db)
):
    """IP-이름 매핑 수정"""
    mapping = db.query(IPMapping).filter(IPMapping.ip_address == ip_address).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="IP 매핑을 찾을 수 없습니다.")

    mapping.name = update.name
    db.commit()
    db.refresh(mapping)

    return {
        "success": True,
        "mapping": {
            "id": mapping.id,
            "ip_address": mapping.ip_address,
            "name": mapping.name
        }
    }


@router.delete("/ip-mappings/{ip_address}")
async def delete_ip_mapping(ip_address: str, db: Session = Depends(get_db)):
    """IP-이름 매핑 삭제"""
    mapping = db.query(IPMapping).filter(IPMapping.ip_address == ip_address).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="IP 매핑을 찾을 수 없습니다.")

    db.delete(mapping)
    db.commit()

    return {"success": True, "message": "삭제되었습니다."}


# Sheet Configuration

@router.get("/config")
async def get_sheet_config(db: Session = Depends(get_db)):
    """시트 설정 조회"""
    config = db.query(SheetConfig).first()
    if not config:
        return {
            "success": True,
            "config": {
                "sheet_id": "1wBxJlm1_p3BJAi16hcgw0XxlnW4Fquk_gfm9dtE4QR0",
                "sheet_name": "Sheet1",
                "date_column": "D",
                "email_column": "E",
                "ip_column": "F"
            }
        }

    return {
        "success": True,
        "config": {
            "sheet_id": config.sheet_id,
            "sheet_name": config.sheet_name,
            "date_column": config.date_column,
            "email_column": config.email_column,
            "ip_column": config.ip_column
        }
    }


@router.post("/config")
async def save_sheet_config(config: SheetConfigCreate, db: Session = Depends(get_db)):
    """시트 설정 저장"""
    existing = db.query(SheetConfig).first()

    if existing:
        existing.sheet_id = config.sheet_id
        existing.sheet_name = config.sheet_name
        existing.date_column = config.date_column
        existing.email_column = config.email_column
        existing.ip_column = config.ip_column
    else:
        new_config = SheetConfig(
            sheet_id=config.sheet_id,
            sheet_name=config.sheet_name,
            date_column=config.date_column,
            email_column=config.email_column,
            ip_column=config.ip_column
        )
        db.add(new_config)

    db.commit()

    return {"success": True, "message": "설정이 저장되었습니다."}


@router.get("/test-connection")
async def test_sheet_connection(db: Session = Depends(get_db)):
    """Google Sheets 연결 테스트"""
    config = db.query(SheetConfig).first()
    sheet_id = config.sheet_id if config else "1wBxJlm1_p3BJAi16hcgw0XxlnW4Fquk_gfm9dtE4QR0"

    try:
        rows = await fetch_google_sheet_data(sheet_id)
        return {
            "success": True,
            "message": "연결 성공",
            "row_count": len(rows),
            "sample": rows[:3] if rows else []
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
