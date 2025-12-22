import React, { createContext, useContext, useState, useCallback } from 'react'

const TutorialContext = createContext()

export const useTutorial = () => {
  const context = useContext(TutorialContext)
  if (!context) {
    throw new Error('useTutorial must be used within a TutorialProvider')
  }
  return context
}

// 각 탭별 튜토리얼 스텝 정의
export const TUTORIAL_STEPS = {
  'delivery-sync': [
    {
      target: '.account-select',
      title: '1단계: 쿠팡 계정 선택',
      content: '먼저 송장을 등록할 쿠팡 계정을 선택해주세요. 드롭다운을 클릭해서 계정을 선택하세요.',
      position: 'bottom',
      action: 'select'
    },
    {
      target: '.header-actions .btn-outline, .header-actions .login-status',
      title: '2단계: 네이버 로그인',
      content: '네이버페이에서 배송 정보를 가져오려면 네이버 로그인이 필요합니다. 로그인 버튼을 클릭하세요.',
      position: 'bottom',
      action: 'click'
    },
    {
      target: '.sync-buttons .btn-primary',
      title: '3단계: 수집 및 매칭',
      content: '이 버튼을 클릭하면 네이버페이에서 배송중인 상품의 수취인, 택배사, 송장번호를 자동으로 수집하고, 쿠팡 발주서와 수취인 이름으로 매칭합니다.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.sync-buttons .btn-success',
      title: '4단계: 자동 업로드 (원클릭)',
      content: '이 버튼은 수집 + 매칭 + 송장 업로드까지 한번에 처리합니다. 가장 빠른 방법이에요!',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.stats-grid',
      title: '5단계: 현황 확인',
      content: '여기서 전체 현황을 확인할 수 있어요. 대기중, 매칭됨, 업로드완료, 실패 건수가 표시됩니다.',
      position: 'bottom'
    },
    {
      target: '.tab-navigation',
      title: '6단계: 상세 보기',
      content: '"동기화 현황"에서 각 배송 건의 상세 정보를 확인하고, "네이버 배송"과 "쿠팡 발주서" 탭에서 원본 데이터를 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.delivery-cards, .delivery-list',
      title: '7단계: 수동 매칭/업로드',
      content: '자동 매칭이 안된 건은 카드를 클릭해서 펼치고, "수동 매칭" 버튼으로 직접 매칭할 수 있어요. 매칭된 건은 "송장 업로드" 버튼으로 개별 업로드도 가능합니다.',
      position: 'top'
    }
  ],

  'dashboard': [
    {
      target: '.dashboard-header, .page-header',
      title: '대시보드 소개',
      content: '대시보드에서는 전체 시스템 현황을 한눈에 확인할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.stats-grid, .stat-cards',
      title: '주요 통계',
      content: '오늘의 문의 수, 응답률, 처리 현황 등 핵심 지표를 확인하세요.',
      position: 'bottom'
    }
  ],

  'inquiries': [
    {
      target: '.page-header, h1',
      title: '문의 관리 소개',
      content: '고객 문의를 확인하고 AI가 생성한 답변을 승인/수정/거부할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.inquiry-list, .pending-list, table',
      title: '문의 목록',
      content: '대기 중인 문의 목록입니다. 각 문의를 클릭하면 상세 내용과 AI 답변을 확인할 수 있어요.',
      position: 'top'
    },
    {
      target: '.btn-primary, .approve-btn',
      title: '승인하기',
      content: 'AI 답변이 적절하면 승인 버튼을 클릭하세요. 답변이 자동으로 제출됩니다.',
      position: 'bottom'
    }
  ],

  'returns': [
    {
      target: '.page-header, h1',
      title: '반품 관리 소개',
      content: '고객 반품 요청을 확인하고 처리할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.filter-section, .filters',
      title: '필터 사용',
      content: '날짜, 상태, 반품 사유 등으로 필터링하여 원하는 반품만 볼 수 있어요.',
      position: 'bottom'
    },
    {
      target: '.return-list, table',
      title: '반품 목록',
      content: '반품 요청 목록입니다. 각 항목을 클릭하면 상세 정보를 확인할 수 있습니다.',
      position: 'top'
    }
  ],

  'issue-response': [
    {
      target: '.page-header, h1',
      title: '문제 대응 소개',
      content: '쿠팡에서 받은 지재권 침해, 리셀러 신고, 상품 삭제 등의 문제에 대한 대응 답변을 AI가 작성해드립니다.',
      position: 'bottom'
    },
    {
      target: '.tab-navigation, .tabs',
      title: '탭 구성',
      content: '"새 문제"에서 AI 답변을 생성하고, "가이드라인"에서 대응 방법을, "이력"에서 과거 대응 내역을 확인하세요.',
      position: 'bottom'
    },
    {
      target: '.issue-input, textarea',
      title: '문제 내용 입력',
      content: '쿠팡에서 받은 메일이나 알림 내용을 여기에 붙여넣기 하세요.',
      position: 'bottom'
    },
    {
      target: '.analyze-btn, .btn-primary',
      title: '분석하기',
      content: '이 버튼을 클릭하면 AI가 문제 유형을 분석하고 적절한 답변을 생성합니다.',
      position: 'bottom',
      highlight: true
    }
  ],

  'promotion': [
    {
      target: '.page-header, h1',
      title: '프로모션 관리 소개',
      content: '쿠폰 생성, 할인 설정 등 프로모션 기능을 관리할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.coupon-section, .promotion-list',
      title: '쿠폰 관리',
      content: '현재 진행 중인 쿠폰과 프로모션 목록을 확인하고 관리하세요.',
      position: 'bottom'
    }
  ],

  'naverpay-delivery': [
    {
      target: '.page-header, h1',
      title: '배송 추적 소개',
      content: '네이버페이에서 배송 정보를 수집하고 추적할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.header-actions .btn-primary, .login-status',
      title: '네이버 로그인',
      content: '먼저 네이버에 로그인하세요. 로그인 후 배송 정보 수집이 가능합니다.',
      position: 'bottom'
    },
    {
      target: '.btn-primary:not(.header-actions .btn-primary)',
      title: '배송 정보 수집',
      content: '이 버튼을 클릭하면 네이버페이에서 배송 중인 상품 정보를 자동으로 수집합니다.',
      position: 'bottom',
      highlight: true
    },
    {
      target: '.delivery-table, table',
      title: '배송 목록',
      content: '수집된 배송 정보가 여기에 표시됩니다. 송장번호 복사, 배송 추적 등이 가능해요.',
      position: 'top'
    }
  ],

  'coupang-accounts': [
    {
      target: '.page-header, h1',
      title: '쿠팡 계정 관리',
      content: '쿠팡 Wing API 연동을 위한 계정 정보를 관리합니다.',
      position: 'bottom'
    },
    {
      target: '.btn-primary, .add-account-btn',
      title: '계정 추가',
      content: '새 쿠팡 계정을 추가하려면 이 버튼을 클릭하세요.',
      position: 'bottom'
    },
    {
      target: '.account-list, table',
      title: '계정 목록',
      content: '등록된 쿠팡 계정 목록입니다. Access Key, Secret Key, Vendor ID가 필요합니다.',
      position: 'top'
    }
  ],

  'naver-accounts': [
    {
      target: '.page-header, h1',
      title: '네이버 계정 관리',
      content: '네이버 스마트스토어 연동을 위한 계정 정보를 관리합니다.',
      position: 'bottom'
    },
    {
      target: '.btn-primary, .add-account-btn',
      title: '계정 추가',
      content: '새 네이버 계정을 추가하려면 이 버튼을 클릭하세요.',
      position: 'bottom'
    }
  ],

  'upload-monitoring': [
    {
      target: '.page-header, h1',
      title: '업로드 모니터링',
      content: '상품 업로드 현황과 오류를 모니터링할 수 있습니다.',
      position: 'bottom'
    },
    {
      target: '.stats-grid, .monitoring-stats',
      title: '업로드 통계',
      content: '성공, 실패, 대기 중인 업로드 현황을 확인하세요.',
      position: 'bottom'
    }
  ]
}

export const TutorialProvider = ({ children }) => {
  const [isActive, setIsActive] = useState(false)
  const [currentTab, setCurrentTab] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [completedTabs, setCompletedTabs] = useState(() => {
    const saved = localStorage.getItem('completedTutorials')
    return saved ? JSON.parse(saved) : []
  })

  const startTutorial = useCallback((tabId) => {
    if (TUTORIAL_STEPS[tabId]) {
      setCurrentTab(tabId)
      setCurrentStep(0)
      setIsActive(true)
    }
  }, [])

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
    startTutorial,
    nextStep,
    prevStep,
    endTutorial,
    skipTutorial,
    resetTutorials,
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
