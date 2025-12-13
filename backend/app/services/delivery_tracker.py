"""
택배사 추적 URL 생성 서비스
19개 택배사 지원
"""
from typing import Optional, Dict, List
from urllib.parse import quote


# 택배사 코드 및 정보
COURIER_INFO: Dict[str, Dict] = {
    "04": {
        "name": "CJ대한통운",
        "code": "04",
        "url_template": "https://trace.cjlogistics.com/next/tracking.html?wblNo={tracking}"
    },
    "01": {
        "name": "우체국택배",
        "code": "01",
        "url_template": "https://service.epost.go.kr/trace.RetrieveDomRigi498Trce.comm?sid1={tracking}"
    },
    "05": {
        "name": "한진택배",
        "code": "05",
        "url_template": "https://www.hanjin.com/kor/CMS/DeliveryMgr/WaybillResult.do?mession-open&wblnumText2={tracking}"
    },
    "08": {
        "name": "롯데택배",
        "code": "08",
        "url_template": "https://www.lotteglogis.com/home/reservation/tracking/index?InvNo={tracking}"
    },
    "06": {
        "name": "로젠택배",
        "code": "06",
        "url_template": "https://www.ilogen.com/web/personal/trace/{tracking}"
    },
    "23": {
        "name": "경동택배",
        "code": "23",
        "url_template": "https://kdexp.com/service/shipping/search.do?barcode={tracking}"
    },
    "22": {
        "name": "대신택배",
        "code": "22",
        "url_template": "https://www.ds3211.co.kr/freight/internalFreightSearch.ht?billno={tracking}"
    },
    "11": {
        "name": "일양로지스",
        "code": "11",
        "url_template": "https://www.ilyanglogis.com/functionality/tracking.asp?hawb_no={tracking}"
    },
    "46": {
        "name": "CU편의점",
        "code": "46",
        "url_template": "https://www.cupost.co.kr/postbox/delivery/localResult.cupost?invoice_no={tracking}"
    },
    "24": {
        "name": "GS25",
        "code": "24",
        "url_template": "https://www.cvsnet.co.kr/invoice/tracking.do?invoice_no={tracking}"
    },
    "45": {
        "name": "편의점택배",
        "code": "45",
        "url_template": "https://www.cvsnet.co.kr/invoice/tracking.do?invoice_no={tracking}"
    },
    "17": {
        "name": "천일택배",
        "code": "17",
        "url_template": "https://www.chunil.co.kr/HTrace/HTrace.jsp?wession-open&transNo={tracking}"
    },
    "18": {
        "name": "합동택배",
        "code": "18",
        "url_template": "https://hdexp.co.kr/deliverySearch2.hd?slipno={tracking}"
    },
    "40": {
        "name": "건영택배",
        "code": "40",
        "url_template": "https://www.kunyoung.com/goods/goods_02.php?mulno={tracking}"
    },
    "12": {
        "name": "EMS",
        "code": "12",
        "url_template": "https://service.epost.go.kr/trace.RetrieveEmsRigi498Trce.comm?POST_CODE={tracking}"
    },
    "13": {
        "name": "DHL",
        "code": "13",
        "url_template": "https://www.dhl.com/kr-ko/home/tracking.html?tracking-id={tracking}"
    },
    "14": {
        "name": "FedEx",
        "code": "14",
        "url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking}"
    },
    "21": {
        "name": "UPS",
        "code": "21",
        "url_template": "https://www.ups.com/track?tracknum={tracking}"
    },
    "20": {
        "name": "홈픽",
        "code": "20",
        "url_template": "https://www.homepick.com/tracking?invoiceNo={tracking}"
    }
}

# 택배사 이름으로 코드 매핑
COURIER_NAME_TO_CODE: Dict[str, str] = {
    info["name"]: code for code, info in COURIER_INFO.items()
}

# 추가 별칭 매핑
COURIER_ALIASES: Dict[str, str] = {
    "CJ대한통운": "04",
    "cj대한통운": "04",
    "CJ택배": "04",
    "대한통운": "04",
    "우체국": "01",
    "우체국택배": "01",
    "한진": "05",
    "한진택배": "05",
    "롯데": "08",
    "롯데택배": "08",
    "롯데글로벌로지스": "08",
    "로젠": "06",
    "로젠택배": "06",
    "경동": "23",
    "경동택배": "23",
    "대신": "22",
    "대신택배": "22",
    "일양": "11",
    "일양로지스": "11",
    "CU": "46",
    "CU택배": "46",
    "CU편의점택배": "46",
    "GS": "24",
    "GS택배": "24",
    "GS25택배": "24",
    "편의점": "45",
    "편의점택배": "45",
    "천일": "17",
    "천일택배": "17",
    "합동": "18",
    "합동택배": "18",
    "건영": "40",
    "건영택배": "40",
    "EMS": "12",
    "DHL": "13",
    "FedEx": "14",
    "페덱스": "14",
    "UPS": "21",
    "홈픽": "20"
}


def get_courier_code(courier_name: str) -> Optional[str]:
    """택배사 이름으로 코드 조회"""
    # 정확한 이름 매핑
    if courier_name in COURIER_NAME_TO_CODE:
        return COURIER_NAME_TO_CODE[courier_name]

    # 별칭 매핑
    if courier_name in COURIER_ALIASES:
        return COURIER_ALIASES[courier_name]

    # 부분 매칭 시도
    courier_lower = courier_name.lower()
    for alias, code in COURIER_ALIASES.items():
        if alias.lower() in courier_lower or courier_lower in alias.lower():
            return code

    return None


def get_tracking_url(courier: str, tracking_number: str) -> Optional[str]:
    """
    택배 추적 URL 생성

    Args:
        courier: 택배사 코드 또는 이름
        tracking_number: 송장번호

    Returns:
        추적 URL 또는 None
    """
    # 코드가 직접 전달된 경우
    if courier in COURIER_INFO:
        courier_code = courier
    else:
        # 이름으로 코드 조회
        courier_code = get_courier_code(courier)

    if not courier_code or courier_code not in COURIER_INFO:
        return None

    url_template = COURIER_INFO[courier_code]["url_template"]
    return url_template.format(tracking=quote(tracking_number))


def get_courier_name(courier_code: str) -> Optional[str]:
    """택배사 코드로 이름 조회"""
    if courier_code in COURIER_INFO:
        return COURIER_INFO[courier_code]["name"]
    return None


def get_all_couriers() -> List[Dict]:
    """모든 지원 택배사 목록 반환"""
    return [
        {
            "code": code,
            "name": info["name"]
        }
        for code, info in COURIER_INFO.items()
    ]


def normalize_courier_name(courier_name: str) -> str:
    """택배사 이름 정규화 (표준 이름으로 변환)"""
    code = get_courier_code(courier_name)
    if code and code in COURIER_INFO:
        return COURIER_INFO[code]["name"]
    return courier_name
