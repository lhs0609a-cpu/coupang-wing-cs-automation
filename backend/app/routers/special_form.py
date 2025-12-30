"""
특수 양식 처리 API 라우터
고객센터 문의 중 링크 클릭이 필요한 특수 양식 케이스 처리
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from sqlalchemy.orm import Session
import asyncio
import json

from ..database import SessionLocal, get_db
from ..models.coupang_account import CoupangAccount, decrypt_value
from ..services.special_form_automation import (
    SpecialFormAutomation,
    SpecialFormInquiry
)

router = APIRouter(prefix="/api/special-form", tags=["Special Form Automation"])


class ProcessSpecialFormRequest(BaseModel):
    """특수 양식 처리 요청"""
    account_id: int
    inquiry_id: str
    inquiry_content: str
    customer_name: str = "고객"
    special_reply_content: str
    special_link: Optional[str] = None
    ai_response: Optional[str] = None
    manual_response: Optional[str] = None  # 사용자가 직접 입력한 답변
    headless: bool = True


class BatchProcessRequest(BaseModel):
    """일괄 처리 요청"""
    account_id: int
    inquiries: List[dict]
    headless: bool = True


class SpecialFormStatusResponse(BaseModel):
    """상태 응답"""
    account_id: int
    account_name: str
    wing_username: Optional[str]
    has_wing_password: bool
    is_active: bool
    can_process: bool
    message: str


def get_account_with_credentials(db: Session, account_id: int) -> tuple:
    """계정 정보 및 복호화된 비밀번호 가져오기"""
    account = db.query(CoupangAccount).filter(
        CoupangAccount.id == account_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

    if not account.wing_username:
        raise HTTPException(
            status_code=400,
            detail="Wing 아이디가 설정되지 않았습니다. 계정 설정에서 wing_username을 입력해주세요."
        )

    if not account.wing_password:
        raise HTTPException(
            status_code=400,
            detail="Wing 비밀번호가 설정되지 않았습니다. 계정 설정에서 wing_password를 입력해주세요."
        )

    # 비밀번호 복호화
    try:
        decrypted_password = decrypt_value(account.wing_password)
    except Exception as e:
        logger.error(f"비밀번호 복호화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="Wing 비밀번호 복호화 실패"
        )

    return account, decrypted_password


@router.get("/status/{account_id}", response_model=SpecialFormStatusResponse)
async def get_special_form_status(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    특수 양식 자동화 상태 조회

    계정의 Wing 로그인 정보가 설정되어 있는지 확인합니다.
    """
    account = db.query(CoupangAccount).filter(
        CoupangAccount.id == account_id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다")

    has_username = bool(account.wing_username)
    has_password = bool(account.wing_password)
    can_process = has_username and has_password and account.is_active

    if can_process:
        message = "특수 양식 자동화 사용 가능"
    elif not has_username:
        message = "Wing 아이디 설정 필요"
    elif not has_password:
        message = "Wing 비밀번호 설정 필요"
    elif not account.is_active:
        message = "계정이 비활성화 상태"
    else:
        message = "설정 확인 필요"

    return SpecialFormStatusResponse(
        account_id=account.id,
        account_name=account.name,
        wing_username=account.wing_username,
        has_wing_password=has_password,
        is_active=account.is_active,
        can_process=can_process,
        message=message
    )


@router.post("/process")
async def process_special_form(
    request: ProcessSpecialFormRequest,
    db: Session = Depends(get_db)
):
    """
    단건 특수 양식 문의 처리

    coupa.ng 링크가 포함된 특수 양식 문의를 자동으로 처리합니다.
    Playwright를 사용하여 브라우저에서 링크를 클릭하고 답변을 제출합니다.
    """
    try:
        # 계정 정보 가져오기
        account, decrypted_password = get_account_with_credentials(db, request.account_id)

        logger.info(f"특수 양식 처리 시작: account={account.name}, inquiry={request.inquiry_id}")

        # 자동화 인스턴스 생성
        automation = SpecialFormAutomation(
            account_id=account.id,
            wing_username=account.wing_username,
            wing_password=decrypted_password
        )

        try:
            # 초기화 (브라우저 실행 + 로그인)
            if not await automation.initialize(headless=request.headless):
                raise HTTPException(
                    status_code=500,
                    detail="자동화 초기화 실패 - Wing 로그인 확인 필요"
                )

            # 특수 양식 문의 처리
            inquiry = SpecialFormInquiry(
                inquiry_id=request.inquiry_id,
                inquiry_content=request.inquiry_content,
                customer_name=request.customer_name,
                special_reply_content=request.special_reply_content,
                special_link=request.special_link
            )

            # manual_response가 있으면 사용, 없으면 ai_response 사용
            response_text = request.manual_response or request.ai_response

            result = await automation.process_special_inquiry(
                inquiry,
                ai_response=response_text
            )

            logger.info(f"특수 양식 처리 완료: inquiry={request.inquiry_id}, status={result['status']}")

            return {
                "success": result["status"] == "submitted",
                "result": result
            }

        finally:
            await automation.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"특수 양식 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_process_special_forms(
    request: BatchProcessRequest,
    db: Session = Depends(get_db)
):
    """
    일괄 특수 양식 처리

    여러 건의 특수 양식 문의를 순차적으로 처리합니다.
    처리 결과를 한 번에 반환합니다.
    """
    try:
        # 계정 정보 가져오기
        account, decrypted_password = get_account_with_credentials(db, request.account_id)

        if not request.inquiries:
            return {
                "success": True,
                "message": "처리할 문의가 없습니다",
                "results": []
            }

        logger.info(f"일괄 특수 양식 처리 시작: account={account.name}, count={len(request.inquiries)}")

        # 자동화 인스턴스 생성
        automation = SpecialFormAutomation(
            account_id=account.id,
            wing_username=account.wing_username,
            wing_password=decrypted_password
        )

        results = []
        success_count = 0
        failed_count = 0

        try:
            # 초기화
            if not await automation.initialize(headless=request.headless):
                raise HTTPException(
                    status_code=500,
                    detail="자동화 초기화 실패 - Wing 로그인 확인 필요"
                )

            # 문의 리스트 변환 및 처리
            for inq_data in request.inquiries:
                inquiry = SpecialFormInquiry(
                    inquiry_id=str(inq_data.get("inquiry_id", "")),
                    inquiry_content=inq_data.get("inquiry_content", ""),
                    customer_name=inq_data.get("customer_name", "고객"),
                    special_reply_content=inq_data.get("special_reply_content", ""),
                    special_link=inq_data.get("special_link")
                )

                result = await automation.process_special_inquiry(inquiry)
                results.append(result)

                if result["status"] == "submitted":
                    success_count += 1
                else:
                    failed_count += 1

                # 다음 문의 처리 전 대기
                await asyncio.sleep(2)

        finally:
            await automation.close()

        logger.info(f"일괄 처리 완료: 성공={success_count}, 실패={failed_count}")

        return {
            "success": True,
            "message": f"처리 완료: 성공 {success_count}개, 실패 {failed_count}개",
            "total": len(request.inquiries),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"일괄 특수 양식 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/stream")
async def batch_process_stream(
    request: BatchProcessRequest,
    db: Session = Depends(get_db)
):
    """
    일괄 특수 양식 처리 (SSE 스트리밍)

    처리 진행 상황을 실시간으로 스트리밍합니다.
    """
    # 계정 정보 가져오기 (스트리밍 전에 검증)
    account, decrypted_password = get_account_with_credentials(db, request.account_id)

    if not request.inquiries:
        async def empty_generator():
            yield f"data: {json.dumps({'type': 'complete', 'message': '처리할 문의가 없습니다', 'success': 0, 'failed': 0}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            empty_generator(),
            media_type="text/event-stream"
        )

    async def event_generator():
        automation = SpecialFormAutomation(
            account_id=account.id,
            wing_username=account.wing_username,
            wing_password=decrypted_password
        )

        try:
            # 초기화 메시지
            yield f"data: {json.dumps({'type': 'init', 'message': '자동화 초기화 중...'}, ensure_ascii=False)}\n\n"

            if not await automation.initialize(headless=request.headless):
                yield f"data: {json.dumps({'type': 'error', 'message': '자동화 초기화 실패'}, ensure_ascii=False)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'init', 'message': '초기화 완료, 처리 시작'}, ensure_ascii=False)}\n\n"

            # 문의 리스트 변환
            inquiries = [
                SpecialFormInquiry(
                    inquiry_id=str(inq.get("inquiry_id", "")),
                    inquiry_content=inq.get("inquiry_content", ""),
                    customer_name=inq.get("customer_name", "고객"),
                    special_reply_content=inq.get("special_reply_content", ""),
                    special_link=inq.get("special_link")
                )
                for inq in request.inquiries
            ]

            # 일괄 처리 (스트리밍)
            async for result in automation.process_batch(inquiries):
                yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"스트리밍 처리 오류: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        finally:
            await automation.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/extract-link")
async def extract_special_link(content: str):
    """
    텍스트에서 coupa.ng 링크 추출

    테스트용 유틸리티 엔드포인트
    """
    link = SpecialFormAutomation.extract_special_link(content)

    return {
        "found": link is not None,
        "link": link,
        "is_special_case": SpecialFormAutomation.is_special_case(content)
    }
