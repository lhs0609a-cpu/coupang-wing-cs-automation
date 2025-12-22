import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

const TutorialContext = createContext()

export const useTutorial = () => {
  const context = useContext(TutorialContext)
  if (!context) {
    throw new Error('useTutorial must be used within a TutorialProvider')
  }
  return context
}

// 각 탭별 튜토리얼 스텝 정의 (친절하고 쉽게)
export const TUTORIAL_STEPS = {
  // 대시보드
  'dashboard': [
    {
      target: '.dashboard-header, .dashboard-title, h1',
      title: '🏠 대시보드에 오신 것을 환영해요!',
      content: '대시보드는 전체 시스템 현황을 한눈에 볼 수 있는 메인 화면이에요. 여기서 중요한 정보들을 빠르게 확인할 수 있어요!',
      position: 'bottom'
    },
    {
      target: '.stats-grid, .stat-cards, .stat-card',
      title: '📊 핵심 통계 카드',
      content: '오늘의 문의 수, 처리 완료 건수, 대기 중인 작업 등 핵심 지표가 카드 형태로 표시돼요. 숫자를 클릭하면 상세 내역으로 이동할 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.automation-stats, .automation-card, .chart-card',
      title: '⚡ AI 자동화 현황',
      content: 'AI가 얼마나 효율적으로 일하고 있는지 확인해보세요! 자동 승인률, 자동 제출률 등을 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.chatgpt-status, .api-status',
      title: '🤖 ChatGPT 연결 상태',
      content: 'AI 답변 생성에 사용되는 ChatGPT의 연결 상태를 확인할 수 있어요. 초록색이면 정상이에요!',
      position: 'bottom'
    }
  ],

  // 상품 검색
  'product-search': [
    {
      target: '.page-header, h1',
      title: '🔍 상품 검색 기능이에요!',
      content: '쿠팡에 등록된 상품을 검색하고 관리할 수 있는 페이지예요. 상품명, SKU, 바코드 등으로 검색해보세요!',
      position: 'bottom'
    },
    {
      target: '.search-input, .search-box, input[type="text"]',
      title: '✏️ 검색어 입력',
      content: '여기에 찾고 싶은 상품명이나 SKU를 입력하세요. Enter를 누르거나 검색 버튼을 클릭하면 검색돼요!',
      position: 'bottom'
    },
    {
      target: '.search-results, .product-list, table',
      title: '📋 검색 결과',
      content: '검색된 상품들이 여기에 표시돼요. 상품을 클릭하면 상세 정보를 볼 수 있어요.',
      position: 'top'
    }
  ],

  // 반품 관리
  'returns': [
    {
      target: '.page-header, h1',
      title: '📦 반품 관리 시작해볼까요?',
      content: '쿠팡에서 발생한 반품 요청을 확인하고, 네이버에서 자동으로 처리할 수 있는 기능이에요. 이 기능으로 반품 처리 시간을 크게 줄일 수 있어요!',
      position: 'bottom'
    },
    {
      target: '.header-actions button:first-child, .btn-secondary:first-of-type',
      title: '⚙️ 계정 설정',
      content: '먼저 쿠팡과 네이버 계정을 연결해야 해요. 이 버튼을 눌러서 API 키와 로그인 정보를 입력하세요.',
      position: 'bottom'
    },
    {
      target: '.btn-secondary:has(.spinning), button:contains("쿠팡에서 조회")',
      title: '📥 쿠팡 반품 조회',
      content: '이 버튼을 클릭하면 쿠팡에서 최근 30일간의 반품 요청을 가져와요. 처음 사용할 때 꼭 눌러주세요!',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.stats-grid, .stat-card',
      title: '📈 반품 현황',
      content: '전체 반품 수, 대기중, 처리완료, 실패 건수를 한눈에 확인하세요.',
      position: 'bottom'
    },
    {
      target: '.filters, .filter-group',
      title: '🔍 필터 사용하기',
      content: '상태나 네이버 처리 여부로 필터링해서 원하는 반품만 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.btn-primary:has(.spinning), button:contains("자동 처리")',
      title: '🚀 자동 처리 시작!',
      content: '이 버튼이 핵심이에요! 클릭하면 미처리된 반품들을 하나씩 확인하면서 네이버에서 자동 처리할 수 있어요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.returns-table, table',
      title: '📋 반품 목록',
      content: '반품 상세 정보가 표시돼요. 체크박스로 선택해서 일괄 처리하거나, 개별 처리할 수 있어요.',
      position: 'top'
    }
  ],

  // 프로모션
  'promotion': [
    {
      target: '.page-header, h1',
      title: '🎁 프로모션 관리에요!',
      content: '쿠팡의 쿠폰을 자동으로 생성하고 관리할 수 있는 기능이에요. 즉시 할인 쿠폰, 다운로드 쿠폰 등을 쉽게 만들어보세요!',
      position: 'bottom'
    },
    {
      target: '.account-selector, select',
      title: '👤 계정 선택',
      content: '먼저 쿠폰을 생성할 쿠팡 계정을 선택하세요. 여러 계정이 있다면 원하는 계정을 골라주세요!',
      position: 'bottom'
    },
    {
      target: '.config-section, .coupon-config',
      title: '⚙️ 쿠폰 설정',
      content: '할인율, 최소 주문금액, 유효기간 등 쿠폰 조건을 설정하세요. 설정값은 자동으로 저장돼요!',
      position: 'bottom'
    },
    {
      target: '.instant-coupon, .coupon-list',
      title: '⚡ 즉시 할인 쿠폰',
      content: '즉시 할인 쿠폰은 상품에 바로 적용되는 쿠폰이에요. 자동 생성을 켜면 새 상품에 자동으로 쿠폰이 생성돼요!',
      position: 'bottom'
    },
    {
      target: '.download-coupon',
      title: '📥 다운로드 쿠폰',
      content: '고객이 직접 다운받아 사용하는 쿠폰이에요. 마케팅 효과가 좋아요!',
      position: 'bottom'
    },
    {
      target: '.btn-primary, .save-btn',
      title: '💾 저장하기',
      content: '설정을 완료했으면 저장 버튼을 눌러주세요!',
      position: 'bottom',
      highlight: true
    }
  ],

  // 배송 동기화
  'delivery-sync': [
    {
      target: '.page-header, h1',
      title: '🚚 배송 동기화 시작!',
      content: '네이버페이에서 배송 정보를 가져와서 쿠팡에 자동으로 송장을 등록하는 핵심 기능이에요! 이 기능 하나로 송장 입력 시간을 확 줄일 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.account-select, .account-selector, select:first-of-type',
      title: '1️⃣ 쿠팡 계정 선택',
      content: '먼저 송장을 등록할 쿠팡 계정을 선택해주세요. 드롭다운을 클릭해서 계정을 고르세요!',
      position: 'bottom',
      action: 'select'
    },
    {
      target: '.login-status, .naver-login, button:contains("로그인")',
      title: '2️⃣ 네이버 로그인',
      content: '네이버페이에서 배송 정보를 가져오려면 로그인이 필요해요. 로그인 버튼을 클릭하세요!',
      position: 'bottom',
      action: 'click'
    },
    {
      target: '.sync-buttons .btn-primary, button:contains("수집")',
      title: '3️⃣ 배송 정보 수집',
      content: '이 버튼을 누르면 네이버페이에서 배송중인 상품의 수취인, 택배사, 송장번호를 자동으로 수집해요!',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.sync-buttons .btn-success, button:contains("자동 업로드")',
      title: '4️⃣ 원클릭 자동 업로드 ⭐',
      content: '가장 편한 방법! 이 버튼 하나로 수집 → 매칭 → 송장 업로드까지 전부 자동으로 처리돼요. 강력 추천!',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.stats-grid, .sync-stats',
      title: '5️⃣ 현황 확인',
      content: '대기중, 매칭됨, 업로드완료, 실패 건수를 한눈에 확인하세요. 숫자가 실시간으로 업데이트돼요!',
      position: 'bottom'
    },
    {
      target: '.tab-navigation, .tabs',
      title: '6️⃣ 상세 보기',
      content: '"동기화 현황"에서 각 건의 상세 정보를, "네이버 배송"에서 원본 데이터를, "쿠팡 발주서"에서 매칭 대상을 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.delivery-cards, .delivery-list, table',
      title: '7️⃣ 수동 매칭/업로드',
      content: '자동 매칭이 안된 건은 카드를 펼쳐서 "수동 매칭" 버튼으로 직접 매칭하세요. 매칭된 건은 개별 업로드도 가능해요!',
      position: 'top'
    }
  ],

  // 네이버 리뷰
  'naver-review': [
    {
      target: '.page-header, h1',
      title: '⭐ 네이버 리뷰 관리!',
      content: '네이버 스마트스토어의 리뷰를 확인하고 답변을 작성할 수 있어요. AI가 답변을 자동으로 생성해줘요!',
      position: 'bottom'
    },
    {
      target: '.account-select, select',
      title: '👤 계정 선택',
      content: '리뷰를 관리할 네이버 스마트스토어 계정을 선택하세요.',
      position: 'bottom'
    },
    {
      target: '.refresh-btn, button:contains("새로고침")',
      title: '🔄 리뷰 불러오기',
      content: '최신 리뷰를 불러오려면 새로고침 버튼을 클릭하세요.',
      position: 'bottom'
    },
    {
      target: '.review-list, table',
      title: '📝 리뷰 목록',
      content: '고객 리뷰가 여기에 표시돼요. 별점, 내용, 작성일 등을 확인할 수 있어요.',
      position: 'top'
    },
    {
      target: '.reply-btn, button:contains("답변")',
      title: '💬 답변 작성',
      content: '답변 버튼을 클릭하면 AI가 적절한 답변을 추천해줘요. 수정해서 등록할 수도 있어요!',
      position: 'bottom',
      highlight: true
    }
  ],

  // 문의 관리
  'inquiries': [
    {
      target: '.inquiry-header, .page-header, h1',
      title: '💬 문의 관리 시작!',
      content: '고객 문의를 확인하고 AI가 생성한 답변을 검토하는 곳이에요. 승인만 하면 자동으로 답변이 제출돼요!',
      position: 'bottom'
    },
    {
      target: '.sub-tabs, .tab-navigation',
      title: '📑 탭 구성',
      content: '"답변 검토"에서 AI 답변을 승인하고, "답변 기록"에서 과거 내역을, "자동화 기록"에서 처리 로그를, "GPT 설정"에서 AI를 커스터마이징할 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.inquiry-controls, .search-box',
      title: '🔍 검색 & 필터',
      content: '문의 내용이나 상태로 검색하고 필터링할 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.response-list, .response-card',
      title: '📋 답변 목록',
      content: 'AI가 생성한 답변들이 카드 형태로 표시돼요. 카드를 클릭하면 상세 내용을 볼 수 있어요.',
      position: 'top'
    },
    {
      target: '.approve-btn, .action-btn.approve, button:contains("승인")',
      title: '✅ 승인 & 자동 제출',
      content: '답변이 적절하면 승인 버튼을 누르세요! 승인되면 자동으로 고객에게 답변이 제출돼요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.edit-btn, .action-btn.edit, button:contains("수정")',
      title: '✏️ 수정하기',
      content: '답변을 수정하고 싶으면 이 버튼을 누르세요. 수정 후 승인할 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.reject-btn, .action-btn.reject, button:contains("거부")',
      title: '❌ 거부하기',
      content: 'AI 답변이 적절하지 않으면 거부할 수 있어요. 사유를 입력하면 AI가 학습해요!',
      position: 'bottom'
    }
  ],

  // 쿠팡 계정
  'coupang-accounts': [
    {
      target: '.page-header, h1',
      title: '🔑 쿠팡 계정 관리',
      content: '쿠팡 Wing API 연동을 위한 계정 정보를 관리하는 곳이에요. 여러 쿠팡 셀러 계정을 등록할 수 있어요!',
      position: 'bottom'
    },
    {
      target: '.btn-primary, .add-btn, button:contains("추가")',
      title: '➕ 새 계정 추가',
      content: '새 쿠팡 계정을 추가하려면 이 버튼을 클릭하세요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.account-card, .account-list, table',
      title: '📋 등록된 계정',
      content: '등록된 쿠팡 계정들이 표시돼요. 각 계정 카드에서 수정, 삭제가 가능해요.',
      position: 'top'
    },
    {
      target: '.form-group input, .api-key-input',
      title: '📝 필요한 정보',
      content: 'Access Key, Secret Key, Vendor ID가 필요해요. 쿠팡 Wing에서 발급받을 수 있어요. Wing 로그인 정보는 선택사항이에요.',
      position: 'bottom'
    }
  ],

  // 네이버 계정
  'naver-accounts': [
    {
      target: '.page-header, h1',
      title: '🟢 네이버 계정 관리',
      content: '네이버 스마트스토어 연동을 위한 계정 정보를 관리하는 곳이에요.',
      position: 'bottom'
    },
    {
      target: '.btn-primary, .add-btn, button:contains("추가")',
      title: '➕ 새 계정 추가',
      content: '새 네이버 계정을 추가하려면 이 버튼을 클릭하세요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.account-card, .account-list',
      title: '📋 등록된 계정',
      content: '등록된 네이버 계정들이 표시돼요. 기본 계정으로 설정하면 자동으로 해당 계정이 사용돼요.',
      position: 'top'
    },
    {
      target: '.form-group input',
      title: '📝 필요한 정보',
      content: '네이버 아이디와 비밀번호가 필요해요. 정보는 암호화되어 안전하게 저장돼요!',
      position: 'bottom'
    }
  ],

  // 업로드 모니터링
  'upload-monitoring': [
    {
      target: '.page-header, h1',
      title: '📈 업로드 모니터링',
      content: '상품 업로드 현황과 담당자별 실적을 확인할 수 있는 페이지예요!',
      position: 'bottom'
    },
    {
      target: '.date-filter, .calendar-input',
      title: '📅 기간 선택',
      content: '조회하고 싶은 기간을 선택하세요. 일별, 주별, 월별로 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.stats-grid, .monitoring-stats',
      title: '📊 업로드 통계',
      content: '총 업로드 수, 성공률, 실패 건수 등을 한눈에 확인하세요.',
      position: 'bottom'
    },
    {
      target: '.chart-container, .recharts-wrapper',
      title: '📉 차트 분석',
      content: '담당자별 업로드 현황을 그래프로 확인할 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.settings-btn, button:contains("설정")',
      title: '⚙️ 담당자 설정',
      content: '담당자를 추가하거나 관리하려면 설정 버튼을 클릭하세요.',
      position: 'bottom'
    }
  ],

  // 문제 대응
  'issue-response': [
    {
      target: '.page-header, h1',
      title: '⚠️ 문제 대응 센터',
      content: '쿠팡에서 받은 지재권 침해 경고, 리셀러 신고, 상품 삭제 등의 문제에 대해 AI가 대응 답변을 작성해드려요!',
      position: 'bottom'
    },
    {
      target: '.tab-navigation, .tabs',
      title: '📑 탭 구성',
      content: '"새 문제"에서 AI 답변을 받고, "가이드라인"에서 대응 방법을, "이력"에서 과거 대응을, "통계"에서 현황을 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.issue-input, textarea',
      title: '✏️ 문제 내용 붙여넣기',
      content: '쿠팡에서 받은 메일이나 알림 전문을 여기에 붙여넣기 하세요. AI가 문제 유형을 자동으로 분석해요!',
      position: 'bottom'
    },
    {
      target: '.analyze-btn, .btn-primary:contains("분석")',
      title: '🔍 분석하기',
      content: '이 버튼을 클릭하면 AI가 문제 유형을 분석하고 심각도를 평가해요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.analysis-result, .result-card',
      title: '📊 분석 결과',
      content: '문제 유형, 심각도, 권장 조치가 표시돼요. 분석 결과를 확인하세요!',
      position: 'bottom'
    },
    {
      target: '.response-type, .radio-group',
      title: '📝 답변 유형 선택',
      content: '이의제기서, 소명서, 신고 답변 중 원하는 유형을 선택하세요.',
      position: 'bottom'
    },
    {
      target: '.generate-btn, button:contains("답변 생성")',
      title: '✨ 답변 생성',
      content: 'AI가 전문적인 답변을 자동으로 생성해요. 생성된 답변을 복사해서 사용하세요!',
      position: 'bottom',
      highlight: true
    }
  ],

  // 배송 추적 (네이버페이 배송)
  'naverpay-delivery': [
    {
      target: '.page-header, h1',
      title: '🚛 배송 추적',
      content: '네이버페이에서 배송 정보를 수집하고 추적할 수 있어요. 배송 현황을 한눈에 확인하세요!',
      position: 'bottom'
    },
    {
      target: '.login-status, .login-btn',
      title: '🔐 네이버 로그인',
      content: '먼저 네이버에 로그인해야 해요. 로그인 버튼을 클릭하세요!',
      position: 'bottom'
    },
    {
      target: '.scrape-btn, .btn-primary:contains("수집")',
      title: '📥 배송 정보 수집',
      content: '이 버튼을 클릭하면 네이버페이에서 배송 중인 상품 정보를 자동으로 가져와요.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.stats-grid, .delivery-stats',
      title: '📊 배송 현황',
      content: '전체 배송 건수, 택배사별 현황 등을 확인하세요.',
      position: 'bottom'
    },
    {
      target: '.delivery-table, table',
      title: '📋 배송 목록',
      content: '수집된 배송 정보가 여기에 표시돼요. 송장번호를 복사하거나 배송 추적 링크로 이동할 수 있어요.',
      position: 'top'
    },
    {
      target: '.copy-btn, button:contains("복사")',
      title: '📋 송장번호 복사',
      content: '송장번호를 클릭하면 클립보드에 복사돼요. 다른 곳에 붙여넣기 해서 사용하세요!',
      position: 'bottom'
    }
  ],

  // 설정 (추후 구현)
  'settings': [
    {
      target: '.page-header, h1',
      title: '⚙️ 설정',
      content: '시스템 설정을 변경할 수 있는 페이지예요. 알림, 자동화 옵션 등을 설정하세요!',
      position: 'bottom'
    }
  ]
}

export const TutorialProvider = ({ children }) => {
  const [isActive, setIsActive] = useState(false)
  const [currentTab, setCurrentTab] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)

  // 튜토리얼 활성화 여부 (온/오프 설정)
  const [tutorialEnabled, setTutorialEnabled] = useState(() => {
    const saved = localStorage.getItem('tutorialEnabled')
    return saved !== null ? JSON.parse(saved) : true // 기본값: 활성화
  })

  // 자동 튜토리얼 표시 여부 (처음 방문 시 자동 시작)
  const [autoShowTutorial, setAutoShowTutorial] = useState(() => {
    const saved = localStorage.getItem('autoShowTutorial')
    return saved !== null ? JSON.parse(saved) : true // 기본값: 자동 표시
  })

  const [completedTabs, setCompletedTabs] = useState(() => {
    const saved = localStorage.getItem('completedTutorials')
    return saved ? JSON.parse(saved) : []
  })

  // 튜토리얼 활성화 설정 저장
  useEffect(() => {
    localStorage.setItem('tutorialEnabled', JSON.stringify(tutorialEnabled))
  }, [tutorialEnabled])

  // 자동 튜토리얼 설정 저장
  useEffect(() => {
    localStorage.setItem('autoShowTutorial', JSON.stringify(autoShowTutorial))
  }, [autoShowTutorial])

  const startTutorial = useCallback((tabId) => {
    if (!tutorialEnabled) return // 튜토리얼이 비활성화되어 있으면 시작하지 않음

    if (TUTORIAL_STEPS[tabId]) {
      setCurrentTab(tabId)
      setCurrentStep(0)
      setIsActive(true)
    }
  }, [tutorialEnabled])

  const nextStep = useCallback(() => {
    if (!currentTab) return

    const steps = TUTORIAL_STEPS[currentTab]
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      // 튜토리얼 완료
      endTutorial()
    }
  }, [currentTab, currentStep])

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }, [currentStep])

  const endTutorial = useCallback(() => {
    if (currentTab && !completedTabs.includes(currentTab)) {
      const newCompleted = [...completedTabs, currentTab]
      setCompletedTabs(newCompleted)
      localStorage.setItem('completedTutorials', JSON.stringify(newCompleted))
    }
    setIsActive(false)
    setCurrentTab(null)
    setCurrentStep(0)
  }, [currentTab, completedTabs])

  const skipTutorial = useCallback(() => {
    setIsActive(false)
    setCurrentTab(null)
    setCurrentStep(0)
  }, [])

  const resetTutorials = useCallback(() => {
    setCompletedTabs([])
    localStorage.removeItem('completedTutorials')
  }, [])

  // 튜토리얼 온/오프 토글
  const toggleTutorialEnabled = useCallback(() => {
    setTutorialEnabled(prev => !prev)
  }, [])

  // 자동 튜토리얼 토글
  const toggleAutoShowTutorial = useCallback(() => {
    setAutoShowTutorial(prev => !prev)
  }, [])

  // 모든 튜토리얼 완료 여부 확인
  const isTabCompleted = useCallback((tabId) => {
    return completedTabs.includes(tabId)
  }, [completedTabs])

  // 특정 탭의 튜토리얼 완료 표시 제거 (다시 보기용)
  const resetTabTutorial = useCallback((tabId) => {
    const newCompleted = completedTabs.filter(id => id !== tabId)
    setCompletedTabs(newCompleted)
    localStorage.setItem('completedTutorials', JSON.stringify(newCompleted))
  }, [completedTabs])

  const getCurrentStepData = useCallback(() => {
    if (!currentTab || !TUTORIAL_STEPS[currentTab]) return null
    return TUTORIAL_STEPS[currentTab][currentStep]
  }, [currentTab, currentStep])

  const getTotalSteps = useCallback(() => {
    if (!currentTab || !TUTORIAL_STEPS[currentTab]) return 0
    return TUTORIAL_STEPS[currentTab].length
  }, [currentTab])

  const value = {
    isActive,
    currentTab,
    currentStep,
    completedTabs,
    tutorialEnabled,
    autoShowTutorial,
    startTutorial,
    nextStep,
    prevStep,
    endTutorial,
    skipTutorial,
    resetTutorials,
    toggleTutorialEnabled,
    toggleAutoShowTutorial,
    isTabCompleted,
    resetTabTutorial,
    getCurrentStepData,
    getTotalSteps
  }

  return (
    <TutorialContext.Provider value={value}>
      {children}
    </TutorialContext.Provider>
  )
}

export default TutorialContext
