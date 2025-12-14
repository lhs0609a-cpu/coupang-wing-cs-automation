"""
네이버 쇼핑 검색 API 라우터
"""
import httpx
import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import os

router = APIRouter(prefix="/naver-shopping", tags=["네이버 쇼핑"])

# 네이버 API 키 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "4ZmdjnkDVs3ZuvE3SUtv")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "Xdn6gxR0ds")
NAVER_SEARCH_API_URL = "https://openapi.naver.com/v1/search/shop.json"


class ShoppingItem(BaseModel):
    """쇼핑 검색 결과 아이템"""
    title: str
    link: str
    image: Optional[str] = None
    lprice: str  # 최저가
    hprice: str  # 최고가
    mallName: str  # 쇼핑몰 이름
    productId: str
    productType: str  # 1: 일반상품, 2: 일반상품+카탈로그, 3: 카탈로그
    brand: Optional[str] = None
    maker: Optional[str] = None
    category1: Optional[str] = None
    category2: Optional[str] = None
    category3: Optional[str] = None
    category4: Optional[str] = None


class ShoppingSearchResponse(BaseModel):
    """쇼핑 검색 응답"""
    total: int
    start: int
    display: int
    items: List[ShoppingItem]
    query: str


@router.get("/search", response_model=ShoppingSearchResponse)
async def search_shopping(
    query: str = Query(..., description="검색어 (상품명)"),
    display: int = Query(20, ge=1, le=100, description="검색 결과 개수"),
    start: int = Query(1, ge=1, le=1000, description="검색 시작 위치"),
    sort: str = Query("sim", description="정렬 옵션 (sim: 정확도순, date: 날짜순, asc: 가격낮은순, dsc: 가격높은순)")
):
    """
    네이버 쇼핑 검색 API

    - query: 검색할 상품명
    - display: 한 번에 표시할 검색 결과 개수 (최대 100)
    - start: 검색 시작 위치
    - sort: 정렬 옵션
        - sim: 정확도순 (기본값)
        - date: 날짜순
        - asc: 가격 낮은순
        - dsc: 가격 높은순
    """
    try:
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                NAVER_SEARCH_API_URL,
                headers=headers,
                params=params,
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"Naver API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"네이버 API 오류: {response.text}"
                )

            data = response.json()

            # HTML 태그 제거 및 상품명 정제
            items = []
            for item in data.get("items", []):
                # title에서 HTML 태그 제거
                title = item.get("title", "")
                title = title.replace("<b>", "").replace("</b>", "")

                # 상점명 접두사 제거 (예: [쿠오카], (센텀시티점), [쿠오카 공식] 등)
                title = re.sub(r'^(\[[^\]]*\]|\([^)]*\))+\s*', '', title)
                # 앞에 남아있는 불필요한 기호 제거
                title = re.sub(r'^[\s\-_:]+', '', title).strip()

                items.append(ShoppingItem(
                    title=title,
                    link=item.get("link", ""),
                    image=item.get("image"),
                    lprice=item.get("lprice", "0"),
                    hprice=item.get("hprice", "0"),
                    mallName=item.get("mallName", ""),
                    productId=item.get("productId", ""),
                    productType=item.get("productType", "1"),
                    brand=item.get("brand"),
                    maker=item.get("maker"),
                    category1=item.get("category1"),
                    category2=item.get("category2"),
                    category3=item.get("category3"),
                    category4=item.get("category4")
                ))

            return ShoppingSearchResponse(
                total=data.get("total", 0),
                start=data.get("start", 1),
                display=data.get("display", len(items)),
                items=items,
                query=query
            )

    except httpx.TimeoutException:
        logger.error("Naver API timeout")
        raise HTTPException(status_code=504, detail="네이버 API 응답 시간 초과")
    except Exception as e:
        logger.error(f"Naver shopping search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """API 상태 확인"""
    return {
        "status": "healthy",
        "api_configured": bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET)
    }


class ProductNameResponse(BaseModel):
    """상품명 추출 응답"""
    success: bool
    product_name: Optional[str] = None
    source: str  # 추출 소스 (11st, coupang, naver, gmarket, etc)
    error: Optional[str] = None


class ProductImageResponse(BaseModel):
    """상품 이미지 추출 응답"""
    success: bool
    image_url: Optional[str] = None
    source: str
    error: Optional[str] = None


@router.get("/extract-product-name", response_model=ProductNameResponse)
async def extract_product_name(
    url: str = Query(..., description="상품 페이지 URL")
):
    """
    상품 페이지 URL에서 실제 상품명을 추출합니다.

    지원 사이트:
    - 11번가
    - 쿠팡
    - 네이버 쇼핑
    - G마켓
    - 옥션
    - 인터파크
    - 위메프
    - 티몬
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # User-Agent 설정 (봇 차단 우회)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=15.0)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch URL: {url}, status: {response.status_code}")
                return ProductNameResponse(
                    success=False,
                    source=domain,
                    error=f"페이지 로드 실패 (상태 코드: {response.status_code})"
                )

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            product_name = None
            source = "unknown"

            # 11번가
            if "11st.co.kr" in domain:
                source = "11번가"
                # 방법 1: meta og:title
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                # 방법 2: h1.title
                if not product_name:
                    title_el = soup.select_one("h1.title, h2.title, .prd_name")
                    if title_el:
                        product_name = title_el.get_text(strip=True)

            # 쿠팡
            elif "coupang.com" in domain:
                source = "쿠팡"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                if not product_name:
                    title_el = soup.select_one("h1.prod-buy-header__title, h2.prod-buy-header__title")
                    if title_el:
                        product_name = title_el.get_text(strip=True)

            # 네이버 쇼핑
            elif "naver.com" in domain or "shopping.naver" in domain:
                source = "네이버쇼핑"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                if not product_name:
                    title_el = soup.select_one("h3.product_name, .productName, h2._3oDjSvLwcS")
                    if title_el:
                        product_name = title_el.get_text(strip=True)

            # G마켓
            elif "gmarket.co.kr" in domain:
                source = "G마켓"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                if not product_name:
                    title_el = soup.select_one("h1.itemtit, .item_tit")
                    if title_el:
                        product_name = title_el.get_text(strip=True)

            # 옥션
            elif "auction.co.kr" in domain:
                source = "옥션"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                if not product_name:
                    title_el = soup.select_one("h1.itemtit, .item_tit")
                    if title_el:
                        product_name = title_el.get_text(strip=True)

            # 인터파크
            elif "interpark.com" in domain:
                source = "인터파크"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]

            # 위메프
            elif "wemakeprice.com" in domain:
                source = "위메프"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]

            # 티몬
            elif "tmon.co.kr" in domain:
                source = "티몬"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]

            # SSG (신세계몰, 이마트몰)
            elif "ssg.com" in domain:
                source = "SSG"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]

            # 롯데ON
            elif "lotteon.com" in domain:
                source = "롯데ON"
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]

            # 기타 사이트 - 일반적인 방법 시도
            else:
                source = domain
                # og:title 시도
                meta = soup.find("meta", property="og:title")
                if meta and meta.get("content"):
                    product_name = meta["content"]
                # title 태그
                if not product_name:
                    title_el = soup.find("title")
                    if title_el:
                        product_name = title_el.get_text(strip=True)
                # h1 태그
                if not product_name:
                    h1 = soup.find("h1")
                    if h1:
                        product_name = h1.get_text(strip=True)

            # 상품명 정제
            if product_name:
                # 불필요한 문자열 제거
                product_name = product_name.strip()

                # 사이트명 접미사 제거 (예: " - 11번가", " | 쿠팡")
                product_name = re.sub(r'\s*[-|:]\s*(11번가|쿠팡|G마켓|옥션|인터파크|위메프|티몬|SSG|롯데ON|네이버쇼핑).*$', '', product_name, flags=re.IGNORECASE)

                # 상점명 접두사 제거 (예: [쿠오카], (센텀시티점), [쿠오카 공식] 등)
                # 패턴: 대괄호나 소괄호로 둘러싸인 상점명/지점명이 앞에 연속으로 나오는 경우
                product_name = re.sub(r'^(\[[^\]]*\]|\([^)]*\))+\s*', '', product_name)

                # 앞에 남아있는 불필요한 기호 제거
                product_name = re.sub(r'^[\s\-_:]+', '', product_name)

                # 특수문자 정리
                product_name = re.sub(r'\s+', ' ', product_name).strip()

                logger.info(f"Extracted product name from {source}: {product_name[:50]}...")

                return ProductNameResponse(
                    success=True,
                    product_name=product_name,
                    source=source
                )
            else:
                return ProductNameResponse(
                    success=False,
                    source=source,
                    error="상품명을 찾을 수 없습니다"
                )

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching URL: {url}")
        return ProductNameResponse(
            success=False,
            source="unknown",
            error="페이지 로드 시간 초과"
        )
    except Exception as e:
        logger.error(f"Error extracting product name from {url}: {e}")
        return ProductNameResponse(
            success=False,
            source="unknown",
            error=str(e)
        )


@router.get("/extract-product-image", response_model=ProductImageResponse)
async def extract_product_image(
    url: str = Query(..., description="상품 페이지 URL")
):
    """
    상품 페이지 URL에서 대표 이미지 URL을 추출합니다.

    지원 사이트:
    - 11번가
    - 쿠팡
    - 네이버 스마트스토어
    - G마켓
    - 옥션
    - 기타 (og:image 메타태그 사용)
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=15.0)

            if response.status_code != 200:
                return ProductImageResponse(
                    success=False,
                    source=domain,
                    error=f"페이지 로드 실패 (상태 코드: {response.status_code})"
                )

            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            image_url = None
            source = "unknown"

            # 네이버 스마트스토어
            if "smartstore.naver.com" in domain or "shopping.naver.com" in domain or "brand.naver.com" in domain:
                source = "네이버스마트스토어"
                # 대표이미지 찾기
                img = soup.find("img", alt="대표이미지")
                if img and img.get("src"):
                    image_url = img["src"]
                # og:image 메타태그
                if not image_url:
                    meta = soup.find("meta", property="og:image")
                    if meta and meta.get("content"):
                        image_url = meta["content"]
                # 다른 이미지 선택자
                if not image_url:
                    img = soup.select_one("._3X6PiBgKq9 img, .bd_2DO68 img, ._1LY7DqCnwR img")
                    if img and img.get("src"):
                        image_url = img["src"]

            # 11번가
            elif "11st.co.kr" in domain:
                source = "11번가"
                meta = soup.find("meta", property="og:image")
                if meta and meta.get("content"):
                    image_url = meta["content"]
                if not image_url:
                    img = soup.select_one(".img_full img, #prdImg, .c_product_img img")
                    if img and img.get("src"):
                        image_url = img["src"]

            # 쿠팡
            elif "coupang.com" in domain:
                source = "쿠팡"
                meta = soup.find("meta", property="og:image")
                if meta and meta.get("content"):
                    image_url = meta["content"]
                if not image_url:
                    img = soup.select_one(".prod-image__detail img, .prod-image img")
                    if img and img.get("src"):
                        image_url = img["src"]

            # G마켓
            elif "gmarket.co.kr" in domain:
                source = "G마켓"
                meta = soup.find("meta", property="og:image")
                if meta and meta.get("content"):
                    image_url = meta["content"]

            # 옥션
            elif "auction.co.kr" in domain:
                source = "옥션"
                meta = soup.find("meta", property="og:image")
                if meta and meta.get("content"):
                    image_url = meta["content"]

            # 기타 사이트 - og:image 메타태그 사용
            else:
                source = domain
                meta = soup.find("meta", property="og:image")
                if meta and meta.get("content"):
                    image_url = meta["content"]
                # 첫 번째 큰 이미지 찾기
                if not image_url:
                    for img in soup.find_all("img"):
                        src = img.get("src") or img.get("data-src")
                        if src and ("product" in src.lower() or "item" in src.lower() or "goods" in src.lower()):
                            image_url = src
                            break

            if image_url:
                # 상대 경로를 절대 경로로 변환
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = f"https://{domain}{image_url}"

                logger.info(f"Extracted product image from {source}: {image_url[:80]}...")

                return ProductImageResponse(
                    success=True,
                    image_url=image_url,
                    source=source
                )
            else:
                return ProductImageResponse(
                    success=False,
                    source=source,
                    error="이미지를 찾을 수 없습니다"
                )

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching URL: {url}")
        return ProductImageResponse(
            success=False,
            source="unknown",
            error="페이지 로드 시간 초과"
        )
    except Exception as e:
        logger.error(f"Error extracting product image from {url}: {e}")
        return ProductImageResponse(
            success=False,
            source="unknown",
            error=str(e)
        )
