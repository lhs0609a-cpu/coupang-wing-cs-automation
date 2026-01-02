import React, { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Ticket,
  RefreshCw,
  Settings,
  Play,
  Pause,
  AlertCircle,
  CheckCircle,
  Clock,
  Package,
  TrendingUp,
  Download,
  Zap,
  ChevronDown,
  ChevronUp,
  Search,
  Calendar,
  FileText,
  BarChart2,
  Info,
  Percent,
  DollarSign,
  Save,
  XCircle,
  StopCircle
} from 'lucide-react'
import TutorialButton from './TutorialButton'
import '../styles/PromotionManagement.css'

const PromotionManagement = ({ apiBaseUrl, showNotification }) => {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [config, setConfig] = useState(null)
  const [instantCoupons, setInstantCoupons] = useState([])
  const [downloadCoupons, setDownloadCoupons] = useState([])
  const [contracts, setContracts] = useState([])  // 계약서 목록
  const [trackingList, setTrackingList] = useState([])
  const [applyLogs, setApplyLogs] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [activeSection, setActiveSection] = useState('config')
  const [syncInProgress, setSyncInProgress] = useState(false)
  const [bulkApplyInProgress, setBulkApplyInProgress] = useState(false)
  const [bulkApplyProgress, setBulkApplyProgress] = useState(null)
  const [copiedPolicies, setCopiedPolicies] = useState(null)  // 복사한 쿠폰 정책
  const [policySourceAccount, setPolicySourceAccount] = useState(null)  // 정책 복사할 원본 계정

  // AbortController ref - 계정 변경 시 이전 요청 취소용
  const abortControllerRef = useRef(null)

  // 쿠폰 설정 폼 상태
  const [couponForm, setCouponForm] = useState({
    // 기본 설정
    is_enabled: false,
    apply_delay_days: 0,  // 항상 즉시 적용
    contract_id: '',  // 계약서 ID (쿠폰 생성에 필요)

    // 즉시할인쿠폰 설정
    instant_coupon_enabled: false,
    instant_coupon_id: '',
    instant_coupon_name: '',

    // 즉시할인쿠폰 자동 생성 설정 (NEW)
    instant_coupon_auto_create: true,  // 자동 생성 모드 (기본: 활성화)
    instant_coupon_title_template: '',  // 쿠폰명 템플릿
    instant_coupon_duration_days: 30,  // 쿠폰 유효기간 (일)
    instant_coupon_discount: '',  // 할인율 또는 할인금액
    instant_coupon_discount_type: 'RATE',  // RATE, PRICE, FIXED_WITH_QUANTITY
    instant_coupon_max_discount_price: 10000,  // 최대할인금액

    // 다운로드쿠폰 설정
    download_coupon_enabled: false,
    download_coupon_id: '',
    download_coupon_name: '',

    // 다운로드쿠폰 자동 생성 설정 (NEW)
    download_coupon_auto_create: true,  // 자동 생성 모드 (기본: 활성화)
    download_coupon_title_template: '',  // 쿠폰명 템플릿
    download_coupon_duration_days: 30,  // 쿠폰 유효기간 (일)

    // 자동 적용 옵션
    auto_apply_to_all: true,  // 설정 저장 시 전체 상품에 자동 적용
  })

  // 단계별 완료 상태 추적
  const [setupProgress, setSetupProgress] = useState({
    step1_account: false,
    step2_couponType: false,
    step3_couponId: false,
    step4_options: true,  // 기본값이 있으므로 true
  })

  // Load accounts on mount
  useEffect(() => {
    loadAccounts()
  }, [])

  // Load config when account changes
  useEffect(() => {
    if (selectedAccount) {
      // 이전 요청 취소
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      // 새 AbortController 생성
      abortControllerRef.current = new AbortController()
      const signal = abortControllerRef.current.signal

      // 계정 변경 시 모든 상태 초기화
      setCopiedPolicies(null)
      setConfig(null)
      setStatistics(null)
      setTrackingList([])
      setApplyLogs([])
      setBulkApplyProgress(null)
      setCouponForm({
        is_enabled: false,
        apply_delay_days: 0,
        contract_id: '',
        instant_coupon_enabled: false,
        instant_coupon_id: '',
        instant_coupon_name: '',
        instant_coupon_auto_create: true,
        instant_coupon_title_template: '',
        instant_coupon_duration_days: 30,
        instant_coupon_discount: '',
        instant_coupon_discount_type: 'RATE',
        instant_coupon_max_discount_price: 10000,
        download_coupon_enabled: false,
        download_coupon_id: '',
        download_coupon_name: '',
        download_coupon_auto_create: true,
        download_coupon_title_template: '',
        download_coupon_duration_days: 30,
        auto_apply_to_all: true,
      })
      setContracts([])
      setInstantCoupons([])
      setDownloadCoupons([])

      // 현재 선택된 계정 ID를 캡처해서 API 호출에 전달
      const accountId = selectedAccount

      // 새 계정 데이터 로드 (계정 ID와 signal 전달)
      loadConfig(accountId, signal)
      loadStatistics(accountId, signal)
      loadBulkApplyProgress(accountId, signal)
      loadContracts(accountId, signal)
      loadInstantCoupons('APPLIED', accountId, signal)
      loadDownloadCoupons('IN_PROGRESS', accountId, signal)
    }

    // Cleanup: 컴포넌트 언마운트 또는 계정 변경 시 요청 취소
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [selectedAccount])

  // 진행 상태 업데이트
  useEffect(() => {
    setSetupProgress({
      step1_account: !!selectedAccount,
      step2_couponType: couponForm.instant_coupon_enabled || couponForm.download_coupon_enabled,
      step3_couponId: (
        (couponForm.instant_coupon_enabled && couponForm.instant_coupon_id && parseInt(couponForm.instant_coupon_id) > 0) ||
        (couponForm.download_coupon_enabled && couponForm.download_coupon_id && parseInt(couponForm.download_coupon_id) > 0)
      ),
      step4_options: true, // 기본값이 있으므로 항상 true
    })
  }, [selectedAccount, couponForm])

  // 진행 상황 폴링 (진행 중일 때만)
  useEffect(() => {
    let interval = null
    if (selectedAccount && bulkApplyProgress && (bulkApplyProgress.status === 'collecting' || bulkApplyProgress.status === 'applying')) {
      const currentAccountId = selectedAccount
      interval = setInterval(() => {
        // 폴링 시에도 현재 계정 ID를 전달
        loadBulkApplyProgress(currentAccountId)
      }, 5000) // 5초마다 업데이트
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [bulkApplyProgress?.status, selectedAccount])

  // 설정이 로드되면 폼 업데이트
  useEffect(() => {
    if (config) {
      setCouponForm({
        is_enabled: config.is_enabled || false,
        apply_delay_days: 0,  // 항상 즉시 적용
        contract_id: config.contract_id || '',
        instant_coupon_enabled: config.instant_coupon_enabled || false,
        instant_coupon_id: config.instant_coupon_id || '',
        instant_coupon_name: config.instant_coupon_name || '',
        instant_coupon_auto_create: config.instant_coupon_auto_create !== false,  // 기본 true
        instant_coupon_title_template: config.instant_coupon_title_template || '',
        instant_coupon_duration_days: config.instant_coupon_duration_days || 30,
        instant_coupon_discount: config.instant_coupon_discount || '',
        instant_coupon_discount_type: config.instant_coupon_discount_type || 'RATE',
        instant_coupon_max_discount_price: config.instant_coupon_max_discount_price || 10000,
        download_coupon_enabled: config.download_coupon_enabled || false,
        download_coupon_id: config.download_coupon_id || '',
        download_coupon_name: config.download_coupon_name || '',
        download_coupon_auto_create: config.download_coupon_auto_create !== false,  // 기본 true
        download_coupon_title_template: config.download_coupon_title_template || '',
        download_coupon_duration_days: config.download_coupon_duration_days || 30,
        auto_apply_to_all: true,
      })
      // 저장된 정책이 있으면 로드, 없으면 초기화
      if (config.download_coupon_policies) {
        setCopiedPolicies(config.download_coupon_policies)
      } else {
        setCopiedPolicies(null)
      }
    }
  }, [config])

  const loadAccounts = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/coupang-accounts`)
      setAccounts(response.data)
      if (response.data.length > 0 && !selectedAccount) {
        setSelectedAccount(response.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load accounts:', error)
      showNotification('계정 목록을 불러오는데 실패했습니다', 'error')
    }
  }

  const loadConfig = async (accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    setLoading(true)
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/config/${targetAccount}`, { signal })
      setConfig(response.data.config)
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') {
        console.log('Request cancelled:', targetAccount)
        return
      }
      console.error('Failed to load config:', error)
      setConfig(null)
    } finally {
      setLoading(false)
    }
  }

  // 계약서 목록 로드
  const loadContracts = async (accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/contracts/${targetAccount}`, { signal })
      if (response.data.success) {
        setContracts(response.data.contracts || [])
      }
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') return
      console.error('Failed to load contracts:', error)
      setContracts([])
    }
  }

  const loadBulkApplyProgress = async (accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/progress/${targetAccount}`, { signal })
      if (response.data.success && response.data.progress) {
        setBulkApplyProgress(response.data.progress)
        const status = response.data.progress.status
        setBulkApplyInProgress(status === 'collecting' || status === 'applying')
      } else {
        setBulkApplyProgress(null)
        setBulkApplyInProgress(false)
      }
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') return
      console.error('Failed to load bulk apply progress:', error)
    }
  }

  const loadInstantCoupons = async (status = 'APPLIED', accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/coupons/instant/${targetAccount}?status=${status}`, { signal })
      if (response.data.success) {
        setInstantCoupons(response.data.coupons || [])
      }
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') return
      console.error('Failed to load instant coupons:', error)
    }
  }

  const loadDownloadCoupons = async (status = 'IN_PROGRESS', accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/coupons/download/${targetAccount}?status=${status}`, { signal })
      if (response.data.success) {
        setDownloadCoupons(response.data.coupons || [])
      } else {
        setDownloadCoupons([])
      }
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') return
      console.error('Failed to load download coupons:', error)
      setDownloadCoupons([])
    }
  }

  // 다운로드쿠폰 단건 조회 및 정책 복사 (쿠폰 ID로 직접 조회)
  const fetchDownloadCouponById = async (copyPolicies = false) => {
    // 정책 복사 시에는 원본 계정 사용, 그 외에는 현재 선택된 계정 사용
    const accountToUse = copyPolicies ? (policySourceAccount || selectedAccount) : selectedAccount

    if (!accountToUse || !couponForm.download_coupon_id) {
      showNotification(copyPolicies ? '원본 계정과 쿠폰 ID를 입력해주세요' : '쿠폰 ID를 입력해주세요', 'error')
      return
    }

    try {
      const response = await axios.get(
        `${apiBaseUrl}/promotion/coupons/download/${accountToUse}/${couponForm.download_coupon_id}`
      )

      if (response.data.success && response.data.coupon) {
        const coupon = response.data.coupon

        // 정책 복사 옵션이 활성화된 경우
        if (copyPolicies && coupon.policies && coupon.policies.length > 0) {
          setCopiedPolicies(coupon.policies)
          // 쿠폰명 템플릿도 기존 쿠폰명에서 자동 설정
          const templateName = coupon.couponName?.replace(/\s*#\d+$/, '') || '신규상품 할인쿠폰'
          setCouponForm(prev => ({
            ...prev,
            download_coupon_title_template: templateName
          }))
          const sourceAccountName = accounts.find(a => a.id === accountToUse)?.name || ''
          showNotification(`${sourceAccountName} 계정에서 쿠폰 정책 ${coupon.policies.length}개가 복사되었습니다`, 'success')
        } else if (copyPolicies) {
          showNotification('이 쿠폰에는 복사할 정책이 없습니다', 'warning')
        } else {
          setCouponForm(prev => ({
            ...prev,
            download_coupon_name: coupon.couponName || `쿠폰 #${coupon.couponId}`
          }))
          showNotification(`쿠폰 조회 성공: ${coupon.couponName}`, 'success')
        }
      } else {
        showNotification(response.data.message || '쿠폰을 찾을 수 없습니다', 'error')
      }
    } catch (error) {
      console.error('Failed to fetch download coupon:', error)
      const accountName = accounts.find(a => a.id === accountToUse)?.name || ''
      showNotification(`${accountName} 계정에서 쿠폰 조회에 실패했습니다. 해당 계정의 쿠폰 ID인지 확인해주세요.`, 'error')
    }
  }

  const loadTrackingList = async (status = null) => {
    if (!selectedAccount) return
    try {
      const url = status
        ? `${apiBaseUrl}/promotion/tracking/${selectedAccount}?status=${status}`
        : `${apiBaseUrl}/promotion/tracking/${selectedAccount}`
      const response = await axios.get(url)
      setTrackingList(response.data.trackings || [])
    } catch (error) {
      console.error('Failed to load tracking list:', error)
    }
  }

  const loadApplyLogs = async () => {
    if (!selectedAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/logs/${selectedAccount}`)
      setApplyLogs(response.data.logs || [])
    } catch (error) {
      console.error('Failed to load apply logs:', error)
    }
  }

  const loadStatistics = async (accountId = null, signal = null) => {
    const targetAccount = accountId || selectedAccount
    if (!targetAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/statistics/${targetAccount}`, { signal })
      setStatistics(response.data.statistics || response.data)
    } catch (error) {
      if (axios.isCancel(error) || error.name === 'AbortError') return
      console.error('Failed to load statistics:', error)
      setStatistics(null)
    }
  }

  // 진행 중인 작업 취소
  const cancelBulkApply = async () => {
    if (!selectedAccount) return

    if (!window.confirm('진행 중인 작업을 취소하시겠습니까?')) {
      return
    }

    try {
      const response = await axios.delete(`${apiBaseUrl}/promotion/progress/${selectedAccount}`)
      if (response.data.success) {
        showNotification(response.data.message, 'success')
        setBulkApplyProgress(null)
        setBulkApplyInProgress(false)
        // 진행 상황 새로고침
        await loadBulkApplyProgress()
      }
    } catch (error) {
      console.error('Failed to cancel bulk apply:', error)
      showNotification('작업 취소에 실패했습니다', 'error')
    }
  }

  // 쿠폰 일괄 적용 재시작 (취소 후 새로 시작)
  const restartBulkApply = async (skipApplied = true) => {
    if (!selectedAccount) return

    const confirmMsg = skipApplied
      ? '기존 작업을 취소하고 새로 시작하시겠습니까?\n(이미 적용된 상품은 제외됩니다)'
      : '기존 작업을 취소하고 전체 상품에 새로 적용하시겠습니까?'

    if (!window.confirm(confirmMsg)) {
      return
    }

    try {
      const response = await axios.post(`${apiBaseUrl}/promotion/sync/${selectedAccount}/restart`, {
        skip_applied: skipApplied
      })
      if (response.data.success) {
        showNotification(response.data.message, 'success')
        setBulkApplyInProgress(true)
        // 진행 상황 폴링 시작
        setTimeout(() => loadBulkApplyProgress(), 2000)
      }
    } catch (error) {
      console.error('Failed to restart bulk apply:', error)
      showNotification('재시작에 실패했습니다', 'error')
    }
  }

  // 쿠폰 설정 저장 및 전체 적용
  const saveAndApplyConfig = async () => {
    if (!selectedAccount) return

    // 즉시할인쿠폰 유효성 검사 (자동 생성 모드 vs 기존 쿠폰 사용 모드)
    if (couponForm.instant_coupon_enabled) {
      if (couponForm.instant_coupon_auto_create) {
        // 자동 생성 모드: 계약서 ID와 할인 설정이 필요
        if (!couponForm.contract_id) {
          showNotification('즉시할인쿠폰 자동 생성을 위해 계약서를 선택해주세요', 'error')
          return
        }
        if (!couponForm.instant_coupon_discount) {
          showNotification('즉시할인쿠폰 할인율/할인금액을 입력해주세요', 'error')
          return
        }
      } else {
        // 기존 쿠폰 사용 모드: 쿠폰 ID 필요
        if (!couponForm.instant_coupon_id) {
          showNotification('즉시할인쿠폰 ID를 입력해주세요', 'error')
          return
        }
      }
    }

    // 다운로드쿠폰 유효성 검사 (자동 생성 모드 vs 기존 쿠폰 사용 모드)
    if (couponForm.download_coupon_enabled) {
      if (couponForm.download_coupon_auto_create) {
        // 자동 생성 모드: 계약서 ID와 정책이 필요
        if (!couponForm.contract_id) {
          showNotification('다운로드쿠폰 자동 생성을 위해 계약서를 선택해주세요', 'error')
          return
        }
        if (!copiedPolicies || copiedPolicies.length === 0) {
          showNotification('다운로드쿠폰 자동 생성을 위해 기존 쿠폰에서 정책을 복사해주세요', 'error')
          return
        }
      } else {
        // 기존 쿠폰 사용 모드: 쿠폰 ID 필요
        if (!couponForm.download_coupon_id) {
          showNotification('다운로드쿠폰 ID를 입력해주세요', 'error')
          return
        }
      }
    }

    if (!couponForm.instant_coupon_enabled && !couponForm.download_coupon_enabled) {
      showNotification('최소 하나의 쿠폰을 활성화해주세요', 'error')
      return
    }

    setSaving(true)
    try {
      // 1. 설정 저장
      const configData = {
        is_enabled: true, // 저장하면 자동으로 활성화
        apply_delay_days: couponForm.apply_delay_days,
        contract_id: couponForm.contract_id ? parseInt(couponForm.contract_id) : null,
        instant_coupon_enabled: couponForm.instant_coupon_enabled,
        instant_coupon_id: couponForm.instant_coupon_id ? parseInt(couponForm.instant_coupon_id) : null,
        instant_coupon_name: couponForm.instant_coupon_name,
        // 즉시할인쿠폰 자동 생성 모드 설정
        instant_coupon_auto_create: couponForm.instant_coupon_auto_create,
        instant_coupon_title_template: couponForm.instant_coupon_title_template,
        instant_coupon_duration_days: couponForm.instant_coupon_duration_days,
        instant_coupon_discount: couponForm.instant_coupon_discount ? parseInt(couponForm.instant_coupon_discount) : null,
        instant_coupon_discount_type: couponForm.instant_coupon_discount_type,
        instant_coupon_max_discount_price: couponForm.instant_coupon_max_discount_price ? parseInt(couponForm.instant_coupon_max_discount_price) : 10000,
        download_coupon_enabled: couponForm.download_coupon_enabled,
        download_coupon_id: couponForm.download_coupon_id ? parseInt(couponForm.download_coupon_id) : null,
        download_coupon_name: couponForm.download_coupon_name,
        // 다운로드쿠폰 자동 생성 모드 설정
        download_coupon_auto_create: couponForm.download_coupon_auto_create,
        download_coupon_title_template: couponForm.download_coupon_title_template,
        download_coupon_duration_days: couponForm.download_coupon_duration_days,
        download_coupon_policies: copiedPolicies,
      }

      const saveResponse = await axios.post(`${apiBaseUrl}/promotion/config/${selectedAccount}`, configData)

      if (saveResponse.data.success) {
        setConfig(saveResponse.data.config)
        showNotification('설정이 저장되었습니다', 'success')

        // 2. 전체 상품에 일괄 적용 (auto_apply_to_all이 true일 때)
        if (couponForm.auto_apply_to_all) {
          showNotification('승인된 전체 상품에 쿠폰 적용을 시작합니다...', 'success')

          const bulkResponse = await axios.post(`${apiBaseUrl}/promotion/sync/${selectedAccount}/bulk-apply`, {
            days_back: 30
          })

          if (bulkResponse.data.success) {
            showNotification(bulkResponse.data.message, 'success')
          }
        }

        // 통계 새로고침
        setTimeout(() => {
          loadStatistics()
          loadApplyLogs()
        }, 3000)
      }
    } catch (error) {
      console.error('Failed to save config:', error)
      showNotification('설정 저장에 실패했습니다', 'error')
    } finally {
      setSaving(false)
    }
  }

  const toggleConfig = async (enabled) => {
    if (!selectedAccount) return
    try {
      const response = await axios.post(`${apiBaseUrl}/promotion/config/${selectedAccount}/toggle`, { enabled })
      if (response.data.success) {
        setConfig(response.data.config)
        setCouponForm(prev => ({ ...prev, is_enabled: enabled }))
        showNotification(response.data.message, 'success')
      }
    } catch (error) {
      console.error('Failed to toggle config:', error)
      showNotification('설정 변경에 실패했습니다', 'error')
    }
  }

  // 진행률 표시 컴포넌트
  const renderProgressSection = () => {
    if (!bulkApplyProgress) return null

    const { status, collecting_progress, applying_progress, current_date,
            total_products, total_items, total_days, processed_days,
            instant_total, instant_success, instant_failed,
            download_total, download_success, download_failed,
            started_at, completed_at, error_message } = bulkApplyProgress

    const isInProgress = status === 'collecting' || status === 'applying'
    const isCompleted = status === 'completed'
    const isFailed = status === 'failed'

    const getStatusText = () => {
      switch (status) {
        case 'collecting': return '상품 정보 수집 중...'
        case 'applying': return '쿠폰 적용 중...'
        case 'completed': return '완료'
        case 'failed': return '실패'
        default: return status
      }
    }

    const getStatusColor = () => {
      switch (status) {
        case 'collecting': return '#3b82f6'
        case 'applying': return '#8b5cf6'
        case 'completed': return '#10b981'
        case 'failed': return '#ef4444'
        default: return '#6b7280'
      }
    }

    return (
      <motion.div
        className={`progress-section ${isInProgress ? 'in-progress' : ''}`}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="progress-header">
          <div className="progress-title">
            {isInProgress && <RefreshCw className="spinning" size={18} />}
            {isCompleted && <CheckCircle size={18} style={{ color: '#10b981' }} />}
            {isFailed && <AlertCircle size={18} style={{ color: '#ef4444' }} />}
            <span>쿠폰 일괄 적용 {getStatusText()}</span>
          </div>
          <span className="progress-status" style={{ color: getStatusColor() }}>
            {getStatusText()}
          </span>
        </div>

        {/* 수집 단계 */}
        {(status === 'collecting' || status === 'applying' || isCompleted) && (
          <div className="progress-stage">
            <div className="stage-header">
              <span className="stage-label">1단계: 상품 정보 수집</span>
              <span className="stage-stats">
                {processed_days}/{total_days}일 처리 | {total_products}개 상품 | {total_items}개 옵션
              </span>
            </div>
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{
                  width: `${collecting_progress}%`,
                  backgroundColor: status === 'collecting' ? '#3b82f6' : '#10b981'
                }}
              />
            </div>
            {status === 'collecting' && current_date && (
              <p className="progress-detail">현재 처리 중: {current_date}</p>
            )}
          </div>
        )}

        {/* 적용 단계 */}
        {(status === 'applying' || isCompleted) && (instant_total > 0 || download_total > 0) && (
          <div className="progress-stage">
            <div className="stage-header">
              <span className="stage-label">2단계: 쿠폰 적용</span>
              <span className="stage-stats">
                성공: {instant_success + download_success} | 실패: {instant_failed + download_failed}
              </span>
            </div>
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{
                  width: `${applying_progress}%`,
                  backgroundColor: status === 'applying' ? '#8b5cf6' : '#10b981'
                }}
              />
            </div>
            {instant_total > 0 && (
              <p className="progress-detail">
                즉시할인쿠폰: {instant_success}/{instant_total} 적용 완료
                {instant_failed > 0 && <span className="failed"> ({instant_failed}개 실패)</span>}
              </p>
            )}
            {download_total > 0 && (
              <p className="progress-detail">
                다운로드쿠폰: {download_success}/{download_total} 적용 완료
                {download_failed > 0 && <span className="failed"> ({download_failed}개 실패)</span>}
              </p>
            )}
          </div>
        )}

        {/* 완료/실패 메시지 */}
        {isCompleted && (
          <div className="progress-complete">
            <CheckCircle size={16} />
            <span>총 {total_products}개 상품({total_items}개 옵션)에 쿠폰 적용이 완료되었습니다.</span>
          </div>
        )}

        {isFailed && error_message && (
          <div className="progress-error">
            <AlertCircle size={16} />
            <span>{error_message}</span>
          </div>
        )}

        {/* 시작/완료 시간 */}
        <div className="progress-time">
          {started_at && <span>시작: {new Date(started_at).toLocaleString()}</span>}
          {completed_at && <span>완료: {new Date(completed_at).toLocaleString()}</span>}
        </div>

        {/* 액션 버튼들 */}
        <div className="progress-actions">
          {/* 진행 중일 때: 취소 버튼만 */}
          {isInProgress && (
            <button
              className="cancel-button"
              onClick={cancelBulkApply}
            >
              <StopCircle size={16} />
              <span>작업 취소</span>
            </button>
          )}

          {/* 완료/취소/실패 상태일 때: 재시작 버튼들 */}
          {(isCompleted || isFailed || status === 'cancelled') && (
            <>
              <button
                className="restart-button"
                onClick={() => restartBulkApply(true)}
              >
                <RefreshCw size={16} />
                <span>신규 상품만 적용</span>
              </button>
              <button
                className="restart-button full"
                onClick={() => restartBulkApply(false)}
              >
                <Zap size={16} />
                <span>전체 재적용</span>
              </button>
            </>
          )}
        </div>
      </motion.div>
    )
  }

  // 단계별 진행 가이드 컴포넌트
  const renderSetupGuide = () => {
    const totalSteps = 4
    const completedSteps = Object.values(setupProgress).filter(Boolean).length
    const progressPercent = (completedSteps / totalSteps) * 100

    const steps = [
      {
        number: 1,
        title: '계정 선택',
        completed: setupProgress.step1_account,
        description: '쿠폰을 적용할 쿠팡 계정을 선택하세요',
        icon: '🎯'
      },
      {
        number: 2,
        title: '쿠폰 종류 선택',
        completed: setupProgress.step2_couponType,
        description: '즉시할인 또는 다운로드쿠폰을 활성화하세요',
        icon: '🎫'
      },
      {
        number: 3,
        title: '쿠폰 선택',
        completed: setupProgress.step3_couponId,
        description: '적용할 쿠폰 ID를 입력하세요 (0이 아닌 값)',
        icon: '✨'
      },
      {
        number: 4,
        title: '옵션 설정',
        completed: setupProgress.step4_options,
        description: '적용 옵션을 확인하세요',
        icon: '⚙️'
      }
    ]

    return (
      <div className="setup-guide">
        <div className="guide-header">
          <h3>🎮 설정 가이드 ({completedSteps}/{totalSteps} 완료)</h3>
          <div className="guide-progress-bar">
            <div
              className="guide-progress-fill"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
        <div className="guide-steps">
          {steps.map((step, index) => (
            <div
              key={step.number}
              className={`guide-step ${step.completed ? 'completed' : ''} ${!step.completed && (index === 0 || steps[index - 1].completed) ? 'current' : ''}`}
            >
              <div className="step-indicator">
                {step.completed ? (
                  <CheckCircle size={24} style={{ color: '#10b981' }} />
                ) : (
                  <div className="step-number">{step.number}</div>
                )}
              </div>
              <div className="step-content">
                <div className="step-title">
                  <span className="step-icon">{step.icon}</span>
                  <span>{step.title}</span>
                </div>
                <div className="step-description">{step.description}</div>
              </div>
            </div>
          ))}
        </div>
        {completedSteps === totalSteps && (
          <div className="guide-complete">
            <CheckCircle size={20} style={{ color: '#10b981' }} />
            <span>모든 설정이 완료되었습니다! 아래 "설정 저장 및 적용" 버튼을 클릭하세요 🎉</span>
          </div>
        )}
      </div>
    )
  }

  // 쿠폰 설정 UI (쿠팡윙 스타일)
  const renderCouponConfigSection = () => (
    <div className="coupon-config-container">
      {/* 단계별 가이드 */}
      {renderSetupGuide()}

      {/* 진행률 표시 */}
      {renderProgressSection()}

      {/* 헤더 */}
      <div className="coupon-config-header">
        <div className="header-info">
          <Info size={20} />
          <div>
            <p>즉시할인쿠폰과 다운로드쿠폰으로 매출을 10배 늘려보세요!</p>
            <p className="sub-info">설정을 저장하면 기존 상품과 신규 상품 모두에 자동으로 쿠폰이 적용됩니다.</p>
          </div>
        </div>
        {config?.is_enabled && (
          <div className="status-badge active">
            <CheckCircle size={16} />
            자동연동 활성화됨
          </div>
        )}
      </div>

      {/* STEP 1: 쿠폰 정보 입력 */}
      <div className="config-step">
        <div className="step-header">
          <span className="step-number">STEP 1</span>
          <span className="step-title">쿠폰 정보를 입력하십시오</span>
        </div>

        <div className="coupon-type-section">
          {/* 즉시할인쿠폰 */}
          <div className={`coupon-card ${couponForm.instant_coupon_enabled ? 'active' : ''}`}>
            <div className="coupon-card-header">
              <label className="coupon-toggle">
                <input
                  type="checkbox"
                  checked={couponForm.instant_coupon_enabled}
                  onChange={(e) => setCouponForm(prev => ({
                    ...prev,
                    instant_coupon_enabled: e.target.checked
                  }))}
                />
                <span className="toggle-slider"></span>
              </label>
              <div className="coupon-type-info">
                <Zap size={20} />
                <span>즉시할인쿠폰</span>
              </div>
            </div>

            {couponForm.instant_coupon_enabled && (
              <div className="coupon-card-body">
                {/* 자동 생성 모드 토글 */}
                <div className="form-row mode-toggle">
                  <label className="checkbox-label mode-switch">
                    <input
                      type="checkbox"
                      checked={couponForm.instant_coupon_auto_create}
                      onChange={(e) => setCouponForm(prev => ({
                        ...prev,
                        instant_coupon_auto_create: e.target.checked
                      }))}
                    />
                    <span className="checkmark"></span>
                    <span className="mode-label">
                      <Zap size={16} />
                      자동 생성 모드 (권장)
                    </span>
                  </label>
                  <p className="help-text">
                    {couponForm.instant_coupon_auto_create
                      ? '1만개 상품마다 새 쿠폰이 자동 생성됩니다 (쿠폰 1개당 최대 1만개 상품 제한)'
                      : '기존 쿠폰에 상품을 추가합니다 (이미 등록된 상품 1만개 이상이면 실패)'}
                  </p>
                </div>

                {/* 자동 생성 모드일 때의 설정 */}
                {couponForm.instant_coupon_auto_create && (
                  <>
                    {/* 계약서 선택 (다운로드쿠폰과 공유) */}
                    {!couponForm.download_coupon_enabled && (
                      <div className="form-row required">
                        <label>계약서 선택 <span className="required-mark">*</span></label>
                        <div className="select-with-button">
                          <select
                            value={couponForm.contract_id}
                            onChange={(e) => setCouponForm(prev => ({
                              ...prev,
                              contract_id: e.target.value
                            }))}
                          >
                            <option value="">계약서를 선택하세요</option>
                            {contracts.map(contract => (
                              <option key={contract.contractId} value={contract.contractId}>
                                [{contract.contractId}] {contract.type} ({contract.start?.split(' ')[0]} ~ {contract.end?.split(' ')[0]})
                              </option>
                            ))}
                          </select>
                          <button
                            className="load-coupons-btn"
                            onClick={loadContracts}
                          >
                            <RefreshCw size={14} />
                            새로고침
                          </button>
                        </div>
                        <p className="help-text">쿠폰 생성에 필요한 계약서를 선택하세요</p>
                      </div>
                    )}

                    {/* 다운로드쿠폰에서 계약서 선택 시 안내 메시지 */}
                    {couponForm.download_coupon_enabled && couponForm.contract_id && (
                      <div className="form-row info-row">
                        <div className="info-message">
                          <CheckCircle size={16} style={{ color: '#10b981' }} />
                          <span>계약서: {contracts.find(c => c.contractId === parseInt(couponForm.contract_id))?.type || couponForm.contract_id} (다운로드쿠폰과 공유)</span>
                        </div>
                      </div>
                    )}

                    {/* 할인 타입 선택 */}
                    <div className="form-row required">
                      <label>할인 타입 <span className="required-mark">*</span></label>
                      <select
                        value={couponForm.instant_coupon_discount_type}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          instant_coupon_discount_type: e.target.value
                        }))}
                      >
                        <option value="RATE">정률 할인 (%)</option>
                        <option value="PRICE">정액 할인 (원)</option>
                        <option value="FIXED_WITH_QUANTITY">수량할인 (원)</option>
                      </select>
                      <p className="help-text">
                        {couponForm.instant_coupon_discount_type === 'RATE' && '상품 가격의 일정 비율을 할인합니다'}
                        {couponForm.instant_coupon_discount_type === 'PRICE' && '고정 금액을 할인합니다'}
                        {couponForm.instant_coupon_discount_type === 'FIXED_WITH_QUANTITY' && '수량에 따른 고정 금액 할인입니다'}
                      </p>
                    </div>

                    {/* 할인율/할인금액 입력 */}
                    <div className="form-row required">
                      <label>
                        {couponForm.instant_coupon_discount_type === 'RATE' ? '할인율 (%)' : '할인금액 (원)'}
                        <span className="required-mark">*</span>
                      </label>
                      <div className="input-with-unit">
                        <input
                          type="number"
                          min="1"
                          max={couponForm.instant_coupon_discount_type === 'RATE' ? 100 : undefined}
                          placeholder={couponForm.instant_coupon_discount_type === 'RATE' ? '예) 10' : '예) 1000'}
                          value={couponForm.instant_coupon_discount}
                          onChange={(e) => setCouponForm(prev => ({
                            ...prev,
                            instant_coupon_discount: e.target.value
                          }))}
                        />
                        <span className="unit">
                          {couponForm.instant_coupon_discount_type === 'RATE' ? '%' : '원'}
                        </span>
                      </div>
                      <p className="help-text">
                        {couponForm.instant_coupon_discount_type === 'RATE'
                          ? '할인율을 입력하세요 (1~100)'
                          : '할인금액을 입력하세요'}
                      </p>
                    </div>

                    {/* 최대 할인금액 (정률 할인일 때만) */}
                    {couponForm.instant_coupon_discount_type === 'RATE' && (
                      <div className="form-row">
                        <label>최대 할인금액 (원)</label>
                        <div className="input-with-unit">
                          <input
                            type="number"
                            min="10"
                            placeholder="예) 10000"
                            value={couponForm.instant_coupon_max_discount_price}
                            onChange={(e) => setCouponForm(prev => ({
                              ...prev,
                              instant_coupon_max_discount_price: e.target.value
                            }))}
                          />
                          <span className="unit">원</span>
                        </div>
                        <p className="help-text">할인금액의 상한선입니다 (최소 10원)</p>
                      </div>
                    )}

                    {/* 쿠폰명 템플릿 */}
                    <div className="form-row">
                      <label>쿠폰명 템플릿</label>
                      <input
                        type="text"
                        maxLength={45}
                        placeholder="예) 신규상품 즉시할인"
                        value={couponForm.instant_coupon_title_template}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          instant_coupon_title_template: e.target.value
                        }))}
                      />
                      <p className="help-text">자동 생성되는 쿠폰 이름 (최대 45자, 뒤에 #1, #2 등 번호가 붙습니다)</p>
                    </div>

                    {/* 쿠폰 유효기간 */}
                    <div className="form-row">
                      <label>쿠폰 유효기간 (일)</label>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={couponForm.instant_coupon_duration_days}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          instant_coupon_duration_days: parseInt(e.target.value) || 30
                        }))}
                      />
                      <p className="help-text">생성일로부터 쿠폰이 유효한 기간 (기본 30일)</p>
                    </div>
                  </>
                )}

                {/* 기존 쿠폰 사용 모드일 때의 설정 */}
                {!couponForm.instant_coupon_auto_create && (
                  <>
                    <div className="form-row">
                      <label>쿠폰 ID</label>
                      <input
                        type="number"
                        placeholder="쿠폰 ID를 입력하세요"
                        value={couponForm.instant_coupon_id}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          instant_coupon_id: e.target.value
                        }))}
                      />
                      <p className="help-text warning">
                        * 주의: 즉시할인쿠폰은 1만개 상품까지만 추가 가능합니다. 초과 시 실패합니다.
                      </p>
                    </div>

                    <div className="form-row">
                      <label>쿠폰명 (메모용)</label>
                      <input
                        type="text"
                        placeholder="예) 10% 할인쿠폰"
                        value={couponForm.instant_coupon_name}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          instant_coupon_name: e.target.value
                        }))}
                      />
                    </div>

                    <div className="coupon-select-wrapper">
                      <label>또는 기존 쿠폰에서 선택</label>
                      <div className="select-with-button">
                        <select
                          value={couponForm.instant_coupon_id}
                          onChange={(e) => {
                            const coupon = instantCoupons.find(c => c.couponId === parseInt(e.target.value))
                            setCouponForm(prev => ({
                              ...prev,
                              instant_coupon_id: e.target.value,
                              instant_coupon_name: coupon?.couponName || prev.instant_coupon_name
                            }))
                          }}
                        >
                          <option value="">쿠폰 선택</option>
                          {instantCoupons.map(coupon => (
                            <option key={coupon.couponId} value={coupon.couponId}>
                              [{coupon.couponId}] {coupon.couponName}
                            </option>
                          ))}
                        </select>
                        <button
                          className="load-coupons-btn"
                          onClick={() => loadInstantCoupons('APPLIED')}
                        >
                          <RefreshCw size={14} />
                          불러오기
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* 다운로드쿠폰 */}
          <div className={`coupon-card ${couponForm.download_coupon_enabled ? 'active' : ''}`}>
            <div className="coupon-card-header">
              <label className="coupon-toggle">
                <input
                  type="checkbox"
                  checked={couponForm.download_coupon_enabled}
                  onChange={(e) => setCouponForm(prev => ({
                    ...prev,
                    download_coupon_enabled: e.target.checked
                  }))}
                />
                <span className="toggle-slider"></span>
              </label>
              <div className="coupon-type-info">
                <Download size={20} />
                <span>다운로드쿠폰</span>
              </div>
            </div>

            {couponForm.download_coupon_enabled && (
              <div className="coupon-card-body">
                {/* 자동 생성 모드 토글 */}
                <div className="form-row mode-toggle">
                  <label className="checkbox-label mode-switch">
                    <input
                      type="checkbox"
                      checked={couponForm.download_coupon_auto_create}
                      onChange={(e) => setCouponForm(prev => ({
                        ...prev,
                        download_coupon_auto_create: e.target.checked
                      }))}
                    />
                    <span className="checkmark"></span>
                    <span className="mode-label">
                      <Zap size={16} />
                      자동 생성 모드 (권장)
                    </span>
                  </label>
                  <p className="help-text">
                    {couponForm.download_coupon_auto_create
                      ? '100개 상품마다 새 쿠폰이 자동 생성됩니다 (쿠폰 1개당 최대 100개 상품 제한)'
                      : '기존 쿠폰에 상품을 추가합니다 (이미 등록된 상품 100개 이상이면 실패)'}
                  </p>
                </div>

                {/* 자동 생성 모드일 때의 설정 */}
                {couponForm.download_coupon_auto_create && (
                  <>
                    {/* 계약서 선택 */}
                    <div className="form-row required">
                      <label>계약서 선택 <span className="required-mark">*</span></label>
                      <div className="select-with-button">
                        <select
                          value={couponForm.contract_id}
                          onChange={(e) => setCouponForm(prev => ({
                            ...prev,
                            contract_id: e.target.value
                          }))}
                        >
                          <option value="">계약서를 선택하세요</option>
                          {contracts.map(contract => (
                            <option key={contract.contractId} value={contract.contractId}>
                              [{contract.contractId}] {contract.type} ({contract.start?.split(' ')[0]} ~ {contract.end?.split(' ')[0]})
                            </option>
                          ))}
                        </select>
                        <button
                          className="load-coupons-btn"
                          onClick={loadContracts}
                        >
                          <RefreshCw size={14} />
                          새로고침
                        </button>
                      </div>
                      <p className="help-text">쿠폰 생성에 필요한 계약서를 선택하세요</p>
                    </div>

                    {/* 기존 쿠폰에서 정책 복사 */}
                    <div className="form-row required">
                      <label>정책 복사할 원본 계정 <span className="required-mark">*</span></label>
                      <select
                        className="source-account-select"
                        value={policySourceAccount || ''}
                        onChange={(e) => setPolicySourceAccount(e.target.value ? parseInt(e.target.value) : null)}
                      >
                        <option value="">-- 원본 계정 선택 --</option>
                        {accounts.map(account => (
                          <option key={account.id} value={account.id}>
                            {account.name} ({account.vendor_id})
                          </option>
                        ))}
                      </select>
                      <p className="help-text">정책을 복사할 쿠폰이 있는 계정을 선택하세요</p>
                    </div>

                    <div className="form-row required">
                      <label>정책 복사할 기존 쿠폰 ID <span className="required-mark">*</span></label>
                      <div className="input-with-button">
                        <input
                          type="number"
                          placeholder="기존 쿠폰 ID를 입력하세요"
                          value={couponForm.download_coupon_id}
                          onChange={(e) => setCouponForm(prev => ({
                            ...prev,
                            download_coupon_id: e.target.value
                          }))}
                        />
                        <button
                          className="fetch-coupon-btn copy-policy"
                          onClick={() => fetchDownloadCouponById(true)}
                          disabled={!couponForm.download_coupon_id || !policySourceAccount}
                        >
                          <Search size={14} />
                          정책 복사
                        </button>
                      </div>
                      <p className="help-text">선택한 원본 계정의 쿠폰에서 할인 정책을 복사합니다</p>
                    </div>

                    {/* 복사된 정책 표시 */}
                    {copiedPolicies && copiedPolicies.length > 0 && (
                      <div className="copied-policies">
                        <div className="policies-header">
                          <CheckCircle size={16} style={{ color: '#10b981' }} />
                          <span>복사된 정책 ({copiedPolicies.length}개)</span>
                        </div>
                        <div className="policies-list">
                          {copiedPolicies.map((policy, index) => (
                            <div key={index} className="policy-item">
                              <span className="policy-discount">
                                {(policy.discountType === 'RATE' || policy.discountType === 'PERCENT')
                                  ? `${policy.discountValue}% 할인`
                                  : `${policy.discountValue?.toLocaleString()}원 할인`}
                              </span>
                              {policy.minimumPurchasePrice > 0 && (
                                <span className="policy-condition">
                                  (최소 {policy.minimumPurchasePrice?.toLocaleString()}원 이상)
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 쿠폰명 템플릿 */}
                    <div className="form-row">
                      <label>쿠폰명 템플릿</label>
                      <input
                        type="text"
                        placeholder="예) 신규상품 할인쿠폰"
                        value={couponForm.download_coupon_title_template}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          download_coupon_title_template: e.target.value
                        }))}
                      />
                      <p className="help-text">자동 생성되는 쿠폰 이름 (뒤에 #1, #2 등 번호가 붙습니다)</p>
                    </div>

                    {/* 쿠폰 유효기간 */}
                    <div className="form-row">
                      <label>쿠폰 유효기간 (일)</label>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={couponForm.download_coupon_duration_days}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          download_coupon_duration_days: parseInt(e.target.value) || 30
                        }))}
                      />
                      <p className="help-text">생성일로부터 쿠폰이 유효한 기간 (기본 30일)</p>
                    </div>
                  </>
                )}

                {/* 기존 쿠폰 사용 모드일 때의 설정 */}
                {!couponForm.download_coupon_auto_create && (
                  <>
                    <div className="form-row">
                      <label>쿠폰 ID</label>
                      <div className="input-with-button">
                        <input
                          type="number"
                          placeholder="쿠폰 ID를 입력하세요"
                          value={couponForm.download_coupon_id}
                          onChange={(e) => setCouponForm(prev => ({
                            ...prev,
                            download_coupon_id: e.target.value
                          }))}
                        />
                        <button
                          className="fetch-coupon-btn"
                          onClick={() => fetchDownloadCouponById(false)}
                          disabled={!couponForm.download_coupon_id}
                        >
                          <Search size={14} />
                          조회
                        </button>
                      </div>
                      <p className="help-text warning">
                        * 주의: 다운로드쿠폰은 100개 상품까지만 추가 가능합니다. 초과 시 실패합니다.
                      </p>
                    </div>

                    <div className="form-row">
                      <label>쿠폰명 (메모용)</label>
                      <input
                        type="text"
                        placeholder="예) 1000원 할인쿠폰"
                        value={couponForm.download_coupon_name}
                        onChange={(e) => setCouponForm(prev => ({
                          ...prev,
                          download_coupon_name: e.target.value
                        }))}
                      />
                    </div>

                    <div className="coupon-select-wrapper">
                      <label>또는 기존 쿠폰에서 선택</label>
                      <div className="select-with-button">
                        <select
                          value={couponForm.download_coupon_id}
                          onChange={(e) => {
                            const coupon = downloadCoupons.find(c => c.couponId === parseInt(e.target.value))
                            setCouponForm(prev => ({
                              ...prev,
                              download_coupon_id: e.target.value,
                              download_coupon_name: coupon?.couponName || prev.download_coupon_name
                            }))
                          }}
                        >
                          <option value="">쿠폰 선택</option>
                          {downloadCoupons.map(coupon => (
                            <option key={coupon.couponId} value={coupon.couponId}>
                              [{coupon.couponId}] {coupon.couponName}
                            </option>
                          ))}
                        </select>
                        <button
                          className="load-coupons-btn"
                          onClick={() => loadDownloadCoupons('IN_PROGRESS')}
                        >
                          <RefreshCw size={14} />
                          불러오기
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* STEP 2: 적용 옵션 */}
      <div className="config-step">
        <div className="step-header">
          <span className="step-number">STEP 2</span>
          <span className="step-title">적용 옵션을 선택하십시오</span>
        </div>

        <div className="apply-options">
          <div className="option-row checkbox-row">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={couponForm.auto_apply_to_all}
                onChange={(e) => setCouponForm(prev => ({
                  ...prev,
                  auto_apply_to_all: e.target.checked
                }))}
              />
              <span className="checkmark"></span>
              <span>저장 시 기존 전체 상품에도 쿠폰 자동 적용</span>
            </label>
            <p className="help-text">체크하면 승인된 모든 상품에 쿠폰이 일괄 적용됩니다</p>
          </div>
        </div>
      </div>

      {/* 저장 버튼 */}
      <div className="config-actions">
        <button
          className="cancel-btn"
          onClick={loadConfig}
          disabled={saving}
        >
          취소
        </button>
        <button
          className="save-btn"
          onClick={saveAndApplyConfig}
          disabled={saving || (!couponForm.instant_coupon_enabled && !couponForm.download_coupon_enabled)}
        >
          {saving ? (
            <>
              <RefreshCw size={18} className="spinning" />
              저장 중...
            </>
          ) : (
            <>
              <Save size={18} />
              설정 저장 및 적용
            </>
          )}
        </button>
      </div>

      {/* 현재 설정 상태 */}
      {config?.is_enabled && (
        <div className="current-config-status">
          <h4>현재 적용된 설정</h4>
          <div className="status-grid">
            {config.instant_coupon_enabled && (
              <div className="status-item">
                <Zap size={16} />
                <span>즉시할인: {config.instant_coupon_name || `ID ${config.instant_coupon_id}`}</span>
              </div>
            )}
            {config.download_coupon_enabled && (
              <div className="status-item">
                <Download size={16} />
                <span>다운로드: {config.download_coupon_name || `ID ${config.download_coupon_id}`}</span>
              </div>
            )}
            <div className="status-item">
              <Clock size={16} />
              <span>신규상품 대기: {config.apply_delay_days}일</span>
            </div>
            {config.last_sync_at && (
              <div className="status-item">
                <RefreshCw size={16} />
                <span>마지막 동기화: {new Date(config.last_sync_at).toLocaleString()}</span>
              </div>
            )}
          </div>
          <button
            className="disable-btn"
            onClick={() => toggleConfig(false)}
          >
            <Pause size={16} />
            자동연동 비활성화
          </button>
        </div>
      )}
    </div>
  )

  const renderTrackingSection = () => (
    <div className="promotion-tracking-section">
      <div className="tracking-header">
        <h3>상품 추적 목록</h3>
        <button className="refresh-btn" onClick={() => loadTrackingList()}>
          <RefreshCw size={16} />
        </button>
      </div>
      <div className="tracking-filters">
        <button className="filter-btn active" onClick={() => loadTrackingList()}>전체</button>
        <button className="filter-btn" onClick={() => loadTrackingList('pending')}>대기</button>
        <button className="filter-btn" onClick={() => loadTrackingList('processing')}>처리중</button>
        <button className="filter-btn" onClick={() => loadTrackingList('completed')}>완료</button>
        <button className="filter-btn" onClick={() => loadTrackingList('failed')}>실패</button>
      </div>
      <div className="tracking-list">
        {trackingList.length === 0 ? (
          <div className="empty-state">
            <Package size={48} />
            <p>추적 중인 상품이 없습니다</p>
          </div>
        ) : (
          trackingList.map(item => (
            <div key={item.id} className={`tracking-item status-${item.status}`}>
              <div className="tracking-info">
                <div className="tracking-product">
                  <span className="product-id">#{item.seller_product_id}</span>
                  <span className="product-name">{item.seller_product_name || '상품명 없음'}</span>
                </div>
                <div className="tracking-dates">
                  <span><Calendar size={14} /> 등록: {new Date(item.product_created_at).toLocaleDateString()}</span>
                  <span><Clock size={14} /> 예정: {new Date(item.coupon_apply_scheduled_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className="tracking-status">
                <span className={`status-badge ${item.status}`}>
                  {item.status === 'pending' && '대기'}
                  {item.status === 'processing' && '처리중'}
                  {item.status === 'completed' && '완료'}
                  {item.status === 'failed' && '실패'}
                  {item.status === 'skipped' && '건너뜀'}
                </span>
                {item.instant_coupon_applied && <span className="coupon-badge instant">즉시할인</span>}
                {item.download_coupon_applied && <span className="coupon-badge download">다운로드</span>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )

  const renderLogsSection = () => (
    <div className="promotion-logs-section">
      <div className="logs-header">
        <h3>적용 이력</h3>
        <button className="refresh-btn" onClick={loadApplyLogs}>
          <RefreshCw size={16} />
        </button>
      </div>
      <div className="logs-list">
        {applyLogs.length === 0 ? (
          <div className="empty-state">
            <FileText size={48} />
            <p>적용 이력이 없습니다</p>
          </div>
        ) : (
          applyLogs.map(log => (
            <div key={log.id} className={`log-item ${log.success ? 'success' : 'failed'}`}>
              <div className="log-icon">
                {log.success ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
              </div>
              <div className="log-info">
                <div className="log-main">
                  <span className="log-type">{log.coupon_type === 'instant' ? '즉시할인' : '다운로드'}</span>
                  <span className="log-coupon">{log.coupon_name || `쿠폰 #${log.coupon_id}`}</span>
                </div>
                <div className="log-detail">
                  <span>상품: #{log.seller_product_id}</span>
                  {log.vendor_item_id && <span>옵션: #{log.vendor_item_id}</span>}
                </div>
                {log.error_message && (
                  <div className="log-error">{log.error_message}</div>
                )}
              </div>
              <div className="log-time">
                {new Date(log.created_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )

  const renderStatistics = () => (
    <div className="promotion-stats">
      {statistics && (
        <>
          <div className="stat-card">
            <div className="stat-icon total"><Package size={24} /></div>
            <div className="stat-info">
              <span className="stat-value">{statistics.total_tracking || 0}</span>
              <span className="stat-label">총 추적 상품</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon pending"><Clock size={24} /></div>
            <div className="stat-info">
              <span className="stat-value">{statistics.pending || 0}</span>
              <span className="stat-label">대기 중</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon completed"><CheckCircle size={24} /></div>
            <div className="stat-info">
              <span className="stat-value">{statistics.completed || 0}</span>
              <span className="stat-label">적용 완료</span>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon failed"><AlertCircle size={24} /></div>
            <div className="stat-info">
              <span className="stat-value">{statistics.failed || 0}</span>
              <span className="stat-label">실패</span>
            </div>
          </div>
        </>
      )}
    </div>
  )

  return (
    <div className="promotion-management">
      <div className="promotion-header">
        <div className="header-title">
          <Ticket size={32} />
          <div>
            <h1>프로모션 관리</h1>
            <p>쿠폰을 설정하면 전체 상품에 자동으로 적용됩니다</p>
          </div>
        </div>
        <div className="header-actions">
          <select
            className="account-select"
            value={selectedAccount || ''}
            onChange={(e) => setSelectedAccount(parseInt(e.target.value))}
          >
            <option value="">계정 선택</option>
            {accounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.vendor_id})
              </option>
            ))}
          </select>
          <button className="refresh-btn" onClick={loadConfig} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'spinning' : ''} />
          </button>
        </div>
      </div>

      {selectedAccount ? (
        <>
          {renderStatistics()}

          <div className="promotion-tabs">
            <button
              className={`tab-btn ${activeSection === 'config' ? 'active' : ''}`}
              onClick={() => setActiveSection('config')}
            >
              <Settings size={18} />
              쿠폰 설정
            </button>
            <button
              className={`tab-btn ${activeSection === 'tracking' ? 'active' : ''}`}
              onClick={() => {
                setActiveSection('tracking')
                loadTrackingList()
              }}
            >
              <Package size={18} />
              추적 목록
            </button>
            <button
              className={`tab-btn ${activeSection === 'logs' ? 'active' : ''}`}
              onClick={() => {
                setActiveSection('logs')
                loadApplyLogs()
              }}
            >
              <FileText size={18} />
              적용 이력
            </button>
          </div>

          <div className="promotion-content">
            <AnimatePresence mode="wait">
              {activeSection === 'config' && (
                <motion.div
                  key="config"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  {renderCouponConfigSection()}
                </motion.div>
              )}
              {activeSection === 'tracking' && (
                <motion.div
                  key="tracking"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  {renderTrackingSection()}
                </motion.div>
              )}
              {activeSection === 'logs' && (
                <motion.div
                  key="logs"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  {renderLogsSection()}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      ) : (
        <div className="no-account-selected">
          <AlertCircle size={48} />
          <h3>계정을 선택해주세요</h3>
          <p>쿠폰 자동연동을 설정할 쿠팡 계정을 선택하세요</p>
        </div>
      )}

      {/* 플로팅 튜토리얼 버튼 */}
      <TutorialButton tabId="promotion" variant="floating" />
    </div>
  )
}

export default PromotionManagement
