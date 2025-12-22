"""
Issue Response Service
쿠팡 판매 관련 문제 대응 서비스 - AI 분석 및 답변 생성
"""
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from loguru import logger
from sqlalchemy.orm import Session

from ..models.issue_response import IssueResponse, IssueTemplate
from ..config import settings


class IssueResponseService:
    """
    쿠팡 판매 문제 대응 서비스
    - 문제 분석 및 분류
    - AI 기반 답변 생성
    - 가이드라인 및 템플릿 관리
    """

    # 문제 유형 정의
    ISSUE_TYPES = {
        "ip_infringement": "지재권 침해",
        "reseller": "리셀러/재판매",
        "suspension": "상품 삭제/정지",
        "other": "기타 문제"
    }

    def __init__(self, db: Session):
        self.db = db
        self.guides_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "knowledge_base",
            "issue_guides"
        )
        self._guides_cache: Dict[str, Dict] = {}

        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured for IssueResponseService")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _load_guide(self, issue_type: str) -> Optional[Dict]:
        """가이드라인 JSON 파일 로드"""
        if issue_type in self._guides_cache:
            return self._guides_cache[issue_type]

        file_map = {
            "ip_infringement": "ip_infringement.json",
            "reseller": "reseller.json",
            "suspension": "product_suspension.json",
            "other": "other_issues.json"
        }

        filename = file_map.get(issue_type)
        if not filename:
            return None

        filepath = os.path.join(self.guides_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                guide = json.load(f)
                self._guides_cache[issue_type] = guide
                return guide
        except Exception as e:
            logger.error(f"Error loading guide {filename}: {e}")
            return None

    def get_all_guides(self) -> Dict[str, Dict]:
        """모든 가이드라인 로드"""
        guides = {}
        for issue_type in self.ISSUE_TYPES.keys():
            guide = self._load_guide(issue_type)
            if guide:
                guides[issue_type] = guide
        return guides

    def get_guide(self, issue_type: str) -> Optional[Dict]:
        """특정 문제 유형 가이드라인 조회"""
        return self._load_guide(issue_type)

    def get_templates(self, issue_type: str, subtype: Optional[str] = None) -> List[Dict]:
        """문제 유형별 템플릿 목록 조회"""
        guide = self._load_guide(issue_type)
        if not guide:
            return []

        templates = guide.get("response_templates", [])

        if subtype:
            templates = [t for t in templates if subtype in t.get("for_subtypes", [])]

        return templates

    def analyze_issue(self, content: str, coupang_account_id: Optional[int] = None) -> Dict[str, Any]:
        """
        문제 내용 분석 및 분류

        Args:
            content: 메일/알림 원본 내용
            coupang_account_id: 쿠팡 계정 ID (선택)

        Returns:
            분석 결과 딕셔너리
        """
        # 1. 키워드 기반 1차 분류
        preliminary_type = self._classify_by_keywords(content)

        # 2. AI를 통한 상세 분석
        if self.client:
            ai_analysis = self._analyze_with_ai(content, preliminary_type)
        else:
            ai_analysis = self._fallback_analysis(content, preliminary_type)

        # 3. DB에 저장
        issue_response = IssueResponse(
            coupang_account_id=coupang_account_id,
            issue_type=ai_analysis.get("issue_type", preliminary_type),
            issue_subtype=ai_analysis.get("issue_subtype"),
            original_content=content,
            ai_analysis=ai_analysis,
            severity=ai_analysis.get("severity", "medium"),
            summary=ai_analysis.get("summary", ""),
            deadline=ai_analysis.get("deadline"),
            recommended_actions=ai_analysis.get("recommended_actions", []),
            status="draft"
        )

        self.db.add(issue_response)
        self.db.commit()
        self.db.refresh(issue_response)

        # 4. 가이드라인 정보 추가
        guide = self._load_guide(issue_response.issue_type)
        subtype_info = None
        if guide and issue_response.issue_subtype:
            for st in guide.get("subtypes", []):
                if st.get("id") == issue_response.issue_subtype:
                    subtype_info = st
                    break

        return {
            "id": issue_response.id,
            "issue_type": issue_response.issue_type,
            "issue_type_name": self.ISSUE_TYPES.get(issue_response.issue_type, "기타"),
            "issue_subtype": issue_response.issue_subtype,
            "subtype_info": subtype_info,
            "severity": issue_response.severity,
            "summary": issue_response.summary,
            "deadline": issue_response.deadline,
            "recommended_actions": issue_response.recommended_actions,
            "ai_analysis": ai_analysis,
            "guide": guide
        }

    def _classify_by_keywords(self, content: str) -> str:
        """키워드 기반 문제 유형 1차 분류"""
        content_lower = content.lower()

        # 지재권 관련 키워드
        ip_keywords = ["상표권", "저작권", "지재권", "지식재산", "trademark", "copyright",
                       "특허", "디자인권", "위조", "짝퉁", "정품", "침해"]
        if any(kw in content_lower for kw in ip_keywords):
            return "ip_infringement"

        # 리셀러 관련 키워드
        reseller_keywords = ["리셀러", "reseller", "재판매", "병행수입", "무단", "유통권",
                            "정식유통", "parallel import"]
        if any(kw in content_lower for kw in reseller_keywords):
            return "reseller"

        # 상품 삭제/정지 관련 키워드
        suspension_keywords = ["삭제", "정지", "제재", "차단", "노출제한", "판매중지",
                              "판매불가", "계정정지", "정책위반", "경고"]
        if any(kw in content_lower for kw in suspension_keywords):
            return "suspension"

        return "other"

    def _analyze_with_ai(self, content: str, preliminary_type: str) -> Dict[str, Any]:
        """AI를 사용한 상세 분석"""
        try:
            guide = self._load_guide(preliminary_type)
            subtypes_info = ""
            if guide:
                subtypes = guide.get("subtypes", [])
                subtypes_info = "\n".join([
                    f"- {st['id']}: {st['name']} - {st['description']}"
                    for st in subtypes
                ])

            system_prompt = """당신은 쿠팡 판매자 법무/CS 전문가입니다.
쿠팡에서 발송한 메일/알림 내용을 분석하여 JSON 형식으로 응답해주세요.

분석 시 다음 사항을 고려하세요:
1. 문제의 정확한 유형과 세부 유형 분류
2. 심각도 평가 (판매자에게 미치는 영향 기준)
3. 대응 기한 파악 (있는 경우)
4. 필요한 조치사항 파악"""

            user_prompt = f"""다음 내용을 분석해주세요.

[분석 대상]
{content}

[가능한 세부 유형]
{subtypes_info}

[응답 형식 - 반드시 JSON으로 응답]
{{
  "issue_type": "{preliminary_type}",
  "issue_subtype": "세부 유형 ID (위 목록 중 하나)",
  "severity": "low|medium|high|critical",
  "summary": "한 줄 요약 (50자 이내)",
  "key_points": ["핵심 포인트 목록"],
  "deadline": "대응 기한 (있는 경우, 없으면 null)",
  "recommended_actions": ["권장 조치 목록"],
  "risk_factors": ["위험 요소"],
  "important_notes": "중요 참고사항"
}}"""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI analysis completed: {result.get('summary', '')}")
            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(content, preliminary_type)

    def _fallback_analysis(self, content: str, issue_type: str) -> Dict[str, Any]:
        """AI 없이 기본 분석"""
        guide = self._load_guide(issue_type)
        subtype = None

        if guide:
            # 키워드 매칭으로 세부 유형 찾기
            for st in guide.get("subtypes", []):
                keywords = st.get("keywords", [])
                if any(kw in content for kw in keywords):
                    subtype = st.get("id")
                    break

        return {
            "issue_type": issue_type,
            "issue_subtype": subtype,
            "severity": "medium",
            "summary": f"{self.ISSUE_TYPES.get(issue_type, '기타')} 관련 문제",
            "key_points": ["상세 분석을 위해 AI 설정이 필요합니다"],
            "deadline": None,
            "recommended_actions": ["문제 내용 상세 확인", "관련 가이드라인 참조"],
            "risk_factors": [],
            "important_notes": "AI 분석 미사용 - 기본 분석 결과"
        }

    def generate_response(
        self,
        issue_id: int,
        response_type: str = "appeal",
        additional_context: str = "",
        seller_name: str = ""
    ) -> Dict[str, Any]:
        """
        AI 답변 생성

        Args:
            issue_id: 문제 ID
            response_type: 답변 유형 (appeal: 이의제기, statement: 소명서, report: 신고답변)
            additional_context: 추가 설명
            seller_name: 판매자 이름

        Returns:
            생성된 답변 정보
        """
        # 문제 정보 로드
        issue = self.db.query(IssueResponse).filter(IssueResponse.id == issue_id).first()
        if not issue:
            raise ValueError(f"Issue not found: {issue_id}")

        # 가이드라인 로드
        guide = self._load_guide(issue.issue_type)
        guide_context = self._build_guide_context(guide, issue.issue_subtype, response_type)

        # 템플릿 찾기
        template = self._find_template(guide, issue.issue_subtype, response_type)

        if self.client:
            result = self._generate_with_ai(
                issue=issue,
                response_type=response_type,
                guide_context=guide_context,
                template=template,
                additional_context=additional_context,
                seller_name=seller_name
            )
        else:
            result = self._generate_from_template(
                issue=issue,
                template=template,
                seller_name=seller_name
            )

        # DB 업데이트
        issue.generated_response = result.get("response_text", "")
        issue.response_type = response_type
        issue.confidence = result.get("confidence", 0)
        issue.suggestions = result.get("suggestions", [])
        issue.updated_at = datetime.utcnow()
        self.db.commit()

        return {
            "id": issue.id,
            "generated_response": issue.generated_response,
            "response_type": response_type,
            "confidence": issue.confidence,
            "suggestions": issue.suggestions,
            "template_used": template.get("name") if template else None
        }

    def _build_guide_context(
        self,
        guide: Optional[Dict],
        subtype: Optional[str],
        response_type: str
    ) -> str:
        """가이드라인 컨텍스트 구성"""
        if not guide:
            return ""

        context_parts = [f"[가이드라인: {guide.get('title', '')}]"]

        # 세부 유형 정보
        if subtype:
            for st in guide.get("subtypes", []):
                if st.get("id") == subtype:
                    context_parts.append(f"\n[세부 유형: {st.get('name', '')}]")
                    context_parts.append(f"설명: {st.get('description', '')}")

                    if st.get("checklist"):
                        context_parts.append("\n[체크리스트]")
                        for item in st["checklist"]:
                            context_parts.append(f"- {item}")

                    if st.get("tips"):
                        context_parts.append("\n[대응 팁]")
                        for tip in st["tips"]:
                            context_parts.append(f"- {tip}")

                    if st.get("required_documents"):
                        context_parts.append("\n[필요 서류]")
                        for doc in st["required_documents"]:
                            context_parts.append(f"- {doc}")
                    break

        # 법적 참조
        if guide.get("legal_references"):
            context_parts.append("\n[관련 법규]")
            for ref in guide["legal_references"]:
                context_parts.append(f"- {ref}")

        # 흔한 실수
        if guide.get("common_mistakes"):
            context_parts.append("\n[피해야 할 실수]")
            for mistake in guide["common_mistakes"]:
                context_parts.append(f"- {mistake}")

        return "\n".join(context_parts)

    def _find_template(
        self,
        guide: Optional[Dict],
        subtype: Optional[str],
        response_type: str
    ) -> Optional[Dict]:
        """적합한 템플릿 찾기"""
        if not guide:
            return None

        templates = guide.get("response_templates", [])
        for template in templates:
            if response_type and template.get("response_type") != response_type:
                continue
            if subtype and subtype in template.get("for_subtypes", []):
                return template

        # 세부 유형 매치 없으면 응답 유형만으로 찾기
        for template in templates:
            if template.get("response_type") == response_type:
                return template

        return templates[0] if templates else None

    def _generate_with_ai(
        self,
        issue: IssueResponse,
        response_type: str,
        guide_context: str,
        template: Optional[Dict],
        additional_context: str,
        seller_name: str
    ) -> Dict[str, Any]:
        """AI를 사용한 답변 생성"""
        try:
            response_type_names = {
                "appeal": "이의제기서",
                "statement": "소명서",
                "report": "신고 답변서"
            }

            system_prompt = f"""당신은 쿠팡 판매자를 위한 법무/CS 답변 작성 전문가입니다.
주어진 문제 상황에 대해 전문적이고 효과적인 {response_type_names.get(response_type, '답변')}을 작성해주세요.

작성 지침:
1. 정중하고 전문적인 어투 사용
2. 구체적인 사실 관계 명시
3. 관련 법규/정책 적절히 언급
4. 첨부할 증빙 자료 안내
5. 향후 조치 계획 포함 (필요시)
6. 감정적 표현 자제
7. 마크다운 형식 사용하지 않기"""

            template_text = ""
            if template:
                template_text = f"\n\n[참고 템플릿]\n{template.get('template', '')}"

            user_prompt = f"""다음 문제에 대한 {response_type_names.get(response_type, '답변')}을 작성해주세요.

[문제 유형]: {self.ISSUE_TYPES.get(issue.issue_type, '기타')} - {issue.issue_subtype or '일반'}
[심각도]: {issue.severity}
[요약]: {issue.summary}

[원본 내용]
{issue.original_content}

{guide_context}
{template_text}

[추가 정보]
{additional_context if additional_context else '없음'}

[판매자 이름]: {seller_name if seller_name else '(미입력)'}

위 정보를 바탕으로 답변을 작성해주세요.
답변 마지막에 첨부 권장 서류 목록을 별도로 안내해주세요."""

            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            response_text = response.choices[0].message.content.strip()

            # 마크다운 제거
            response_text = response_text.replace('**', '')
            response_text = response_text.replace('*', '')
            response_text = response_text.replace('_', '')

            # 첨부 서류 추천 추출
            suggestions = self._extract_suggestions(response_text, guide_context)

            # 신뢰도 계산
            confidence = 85
            if response.choices[0].finish_reason == 'stop':
                confidence += 5
            if additional_context:
                confidence += 5

            return {
                "response_text": response_text,
                "confidence": min(100, confidence),
                "suggestions": suggestions
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._generate_from_template(issue, template, seller_name)

    def _generate_from_template(
        self,
        issue: IssueResponse,
        template: Optional[Dict],
        seller_name: str
    ) -> Dict[str, Any]:
        """템플릿 기반 답변 생성"""
        if not template:
            return {
                "response_text": f"""안녕하세요, 쿠팡 판매자 지원팀 담당자님.

{issue.summary or '문제'} 관련하여 연락드립니다.

해당 건에 대해 확인 후 답변드리겠습니다.

감사합니다.
{seller_name or '판매자'} 드림""",
                "confidence": 50,
                "suggestions": ["관련 증빙 자료 첨부 권장"]
            }

        # 템플릿 변수 치환
        response_text = template.get("template", "")
        replacements = {
            "{issue_summary}": issue.summary or "해당 문제",
            "{seller_name}": seller_name or "판매자",
            "{product_name}": "(상품명)",
            "{deletion_reason}": "(삭제 사유)",
            "{appeal_reason}": "(이의제기 사유를 입력해주세요)",
            "{supplier_info}": "(구매처 정보)",
            "{overseas_seller}": "(해외 구매처)",
            "{event_info_if_any}": "(이벤트 정보 - 해당시)",
            "{before_text}": "(수정 전 표현)",
            "{after_text}": "(수정 후 표현)",
            "{complaint_summary}": "(고객 불만 내용)",
            "{cause_analysis}": "(원인 분석)",
            "{resolution}": "(해결 조치)",
            "{prevention}": "(재발 방지 대책)",
            "{violation_acknowledged}": "(위반 사항 인지 내용)",
            "{immediate_action_1}": "(즉시 조치 1)",
            "{immediate_action_2}": "(즉시 조치 2)",
            "{prevention_measure_1}": "(재발 방지 1)",
            "{prevention_measure_2}": "(재발 방지 2)",
            "{timeline}": "(이행 일정)",
            "{violation_content}": "(위반 내용)",
            "{correction_done}": "(조치 완료 내용)",
            "{what_changed}": "(수정 사항)",
            "{creation_date}": "(제작 일시)"
        }

        for key, value in replacements.items():
            response_text = response_text.replace(key, value)

        return {
            "response_text": response_text,
            "confidence": 60,
            "suggestions": ["템플릿 내 {} 부분을 실제 정보로 교체해주세요"]
        }

    def _extract_suggestions(self, response_text: str, guide_context: str) -> List[str]:
        """답변에서 첨부 권장 서류 추출"""
        suggestions = []

        # 가이드 컨텍스트에서 필요 서류 추출
        if "[필요 서류]" in guide_context:
            lines = guide_context.split("\n")
            in_docs = False
            for line in lines:
                if "[필요 서류]" in line:
                    in_docs = True
                    continue
                if in_docs:
                    if line.startswith("- "):
                        suggestions.append(line[2:])
                    elif line.startswith("["):
                        break

        # 응답 텍스트에서 추가 추출
        doc_keywords = ["첨부", "제출", "준비", "증빙"]
        if any(kw in response_text for kw in doc_keywords):
            # 기본 권장 서류 추가
            if not suggestions:
                suggestions = ["관련 증빙 자료", "구매 영수증 또는 세금계산서"]

        return suggestions[:5]  # 최대 5개

    def get_history(
        self,
        coupang_account_id: Optional[int] = None,
        issue_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """이전 대응 이력 조회"""
        query = self.db.query(IssueResponse)

        if coupang_account_id:
            query = query.filter(IssueResponse.coupang_account_id == coupang_account_id)

        if issue_type:
            query = query.filter(IssueResponse.issue_type == issue_type)

        query = query.order_by(IssueResponse.created_at.desc())
        query = query.offset(offset).limit(limit)

        issues = query.all()
        return [issue.to_dict() for issue in issues]

    def get_issue(self, issue_id: int) -> Optional[Dict]:
        """특정 문제 조회"""
        issue = self.db.query(IssueResponse).filter(IssueResponse.id == issue_id).first()
        if not issue:
            return None

        result = issue.to_dict()

        # 가이드라인 정보 추가
        guide = self._load_guide(issue.issue_type)
        if guide:
            result["guide"] = guide
            if issue.issue_subtype:
                for st in guide.get("subtypes", []):
                    if st.get("id") == issue.issue_subtype:
                        result["subtype_info"] = st
                        break

        return result

    def update_issue_status(
        self,
        issue_id: int,
        status: str,
        resolution_notes: Optional[str] = None
    ) -> Optional[Dict]:
        """문제 상태 업데이트"""
        issue = self.db.query(IssueResponse).filter(IssueResponse.id == issue_id).first()
        if not issue:
            return None

        issue.status = status
        if status == "resolved":
            issue.is_resolved = True
            issue.resolved_at = datetime.utcnow()
        if resolution_notes:
            issue.resolution_notes = resolution_notes
        issue.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(issue)

        return issue.to_dict()

    def delete_issue(self, issue_id: int) -> bool:
        """문제 삭제"""
        issue = self.db.query(IssueResponse).filter(IssueResponse.id == issue_id).first()
        if not issue:
            return False

        self.db.delete(issue)
        self.db.commit()
        return True

    def get_statistics(self, coupang_account_id: Optional[int] = None) -> Dict[str, Any]:
        """통계 조회"""
        query = self.db.query(IssueResponse)
        if coupang_account_id:
            query = query.filter(IssueResponse.coupang_account_id == coupang_account_id)

        total = query.count()
        resolved = query.filter(IssueResponse.is_resolved == True).count()

        # 유형별 통계
        type_stats = {}
        for issue_type in self.ISSUE_TYPES.keys():
            count = query.filter(IssueResponse.issue_type == issue_type).count()
            type_stats[issue_type] = {
                "name": self.ISSUE_TYPES[issue_type],
                "count": count
            }

        # 심각도별 통계
        severity_stats = {}
        for severity in ["low", "medium", "high", "critical"]:
            count = query.filter(IssueResponse.severity == severity).count()
            severity_stats[severity] = count

        return {
            "total": total,
            "resolved": resolved,
            "pending": total - resolved,
            "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
            "by_type": type_stats,
            "by_severity": severity_stats
        }
