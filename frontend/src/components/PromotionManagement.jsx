import React, { useState, useEffect } from 'react'
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
import '../styles/PromotionManagement.css'

const PromotionManagement = ({ apiBaseUrl, showNotification }) => {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [config, setConfig] = useState(null)
  const [instantCoupons, setInstantCoupons] = useState([])
  const [downloadCoupons, setDownloadCoupons] = useState([])
  const [trackingList, setTrackingList] = useState([])
  const [applyLogs, setApplyLogs] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [activeSection, setActiveSection] = useState('config')
  const [syncInProgress, setSyncInProgress] = useState(false)
  const [bulkApplyInProgress, setBulkApplyInProgress] = useState(false)
  const [bulkApplyProgress, setBulkApplyProgress] = useState(null)

  // 쿠폰 설정 폼 상태
  const [couponForm, setCouponForm] = useState({
    // 기본 설정
    is_enabled: false,
    apply_delay_days: 0,  // 항상 즉시 적용

    // 즉시할인쿠폰 설정
    instant_coupon_enabled: false,
    instant_coupon_id: '',
    instant_coupon_name: '',

    // 다운로드쿠폰 설정
    download_coupon_enabled: false,
    download_coupon_id: '',
    download_coupon_name: '',

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
      loadConfig()
      loadStatistics()
      loadBulkApplyProgress()
      // 계정 선택하면 쿠폰 목록도 자동으로 로드
      loadInstantCoupons('APPLIED')
      loadDownloadCoupons('IN_PROGRESS')
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
    if (bulkApplyProgress && (bulkApplyProgress.status === 'collecting' || bulkApplyProgress.status === 'applying')) {
      interval = setInterval(() => {
        loadBulkApplyProgress()
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
        instant_coupon_enabled: config.instant_coupon_enabled || false,
        instant_coupon_id: config.instant_coupon_id || '',
        instant_coupon_name: config.instant_coupon_name || '',
        download_coupon_enabled: config.download_coupon_enabled || false,
        download_coupon_id: config.download_coupon_id || '',
        download_coupon_name: config.download_coupon_name || '',
        auto_apply_to_all: true,
      })
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

  const loadConfig = async () => {
    if (!selectedAccount) return
    setLoading(true)
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/config/${selectedAccount}`)
      setConfig(response.data.config)
    } catch (error) {
      console.error('Failed to load config:', error)
      setConfig(null)
    } finally {
      setLoading(false)
    }
  }

  const loadBulkApplyProgress = async () => {
    if (!selectedAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/progress/${selectedAccount}`)
      if (response.data.success && response.data.progress) {
        setBulkApplyProgress(response.data.progress)
        // 진행 중 상태 업데이트
        const status = response.data.progress.status
        setBulkApplyInProgress(status === 'collecting' || status === 'applying')
      } else {
        setBulkApplyProgress(null)
        setBulkApplyInProgress(false)
      }
    } catch (error) {
      console.error('Failed to load bulk apply progress:', error)
    }
  }

  const loadInstantCoupons = async (status = 'APPLIED') => {
    if (!selectedAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/coupons/instant/${selectedAccount}?status=${status}`)
      if (response.data.success) {
        setInstantCoupons(response.data.coupons || [])
      }
    } catch (error) {
      console.error('Failed to load instant coupons:', error)
    }
  }

  const loadDownloadCoupons = async (status = 'IN_PROGRESS') => {
    if (!selectedAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/coupons/download/${selectedAccount}?status=${status}`)
      if (response.data.success) {
        setDownloadCoupons(response.data.coupons || [])
      } else {
        // API 미지원 등의 이유로 실패해도 빈 배열 설정
        setDownloadCoupons([])
      }
    } catch (error) {
      console.error('Failed to load download coupons:', error)
      // 에러 발생 시 빈 배열로 설정 (UI 깨짐 방지)
      setDownloadCoupons([])
    }
  }

  // 다운로드쿠폰 단건 조회 (쿠폰 ID로 직접 조회)
  const fetchDownloadCouponById = async () => {
    if (!selectedAccount || !couponForm.download_coupon_id) {
      showNotification('쿠폰 ID를 입력해주세요', 'error')
      return
    }

    try {
      const response = await axios.get(
        `${apiBaseUrl}/promotion/coupons/download/${selectedAccount}/${couponForm.download_coupon_id}`
      )

      if (response.data.success && response.data.coupon) {
        const coupon = response.data.coupon
        setCouponForm(prev => ({
          ...prev,
          download_coupon_name: coupon.couponName || `쿠폰 #${coupon.couponId}`
        }))
        showNotification(`쿠폰 조회 성공: ${coupon.couponName}`, 'success')
      } else {
        showNotification(response.data.message || '쿠폰을 찾을 수 없습니다', 'error')
      }
    } catch (error) {
      console.error('Failed to fetch download coupon:', error)
      showNotification('쿠폰 조회에 실패했습니다', 'error')
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

  const loadStatistics = async () => {
    if (!selectedAccount) return
    try {
      const response = await axios.get(`${apiBaseUrl}/promotion/statistics/${selectedAccount}`)
      setStatistics(response.data.statistics || response.data)
    } catch (error) {
      console.error('Failed to load statistics:', error)
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

    // 유효성 검사
    if (couponForm.instant_coupon_enabled && !couponForm.instant_coupon_id) {
      showNotification('즉시할인쿠폰 ID를 입력해주세요', 'error')
      return
    }
    if (couponForm.download_coupon_enabled && !couponForm.download_coupon_id) {
      showNotification('다운로드쿠폰 ID를 입력해주세요', 'error')
      return
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
        instant_coupon_enabled: couponForm.instant_coupon_enabled,
        instant_coupon_id: couponForm.instant_coupon_id ? parseInt(couponForm.instant_coupon_id) : null,
        instant_coupon_name: couponForm.instant_coupon_name,
        download_coupon_enabled: couponForm.download_coupon_enabled,
        download_coupon_id: couponForm.download_coupon_id ? parseInt(couponForm.download_coupon_id) : null,
        download_coupon_name: couponForm.download_coupon_name,
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
                  <p className="help-text">쿠팡윙 → 할인쿠폰 관리에서 쿠폰 ID를 확인하세요</p>
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
                      onClick={fetchDownloadCouponById}
                      disabled={!couponForm.download_coupon_id}
                    >
                      <Search size={14} />
                      조회
                    </button>
                  </div>
                  <p className="help-text">쿠팡윙 → 할인쿠폰 관리에서 쿠폰 ID를 확인 후 입력하고 조회 버튼을 클릭하세요</p>
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
                  <label>또는 기존 쿠폰에서 선택 (목록이 비어있을 수 있음)</label>
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
                  <p className="help-text warning">* 쿠팡 API 제한으로 목록 조회가 불가할 수 있습니다. 쿠폰 ID를 직접 입력 후 조회 버튼을 사용하세요.</p>
                </div>
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
    </div>
  )
}

export default PromotionManagement
