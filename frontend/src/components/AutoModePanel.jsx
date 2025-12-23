import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Zap,
  Play,
  Square,
  Clock,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  MessageSquare,
  Phone
} from 'lucide-react'
import '../styles/AutoModePanel.css'

const AutoModePanel = ({ apiBaseUrl }) => {
  // 기본 설정 상태
  const [isAutoModeOn, setIsAutoModeOn] = useState(false)
  const [selectedAccountId, setSelectedAccountId] = useState('')
  const [intervalMinutes, setIntervalMinutes] = useState(5)
  const [accounts, setAccounts] = useState([])

  // 실행 상태
  const [isRunning, setIsRunning] = useState(false)
  const [lastRunTime, setLastRunTime] = useState(null)
  const [nextRunTime, setNextRunTime] = useState(null)
  const [countdown, setCountdown] = useState(null)

  // 통계
  const [stats, setStats] = useState({
    totalCollected: 0,
    totalAnswered: 0,
    totalSubmitted: 0,
    totalConfirmed: 0,
    totalFailed: 0
  })

  // 로그
  const [recentLogs, setRecentLogs] = useState([])

  // 문의 유형 선택
  const [inquiryTypes, setInquiryTypes] = useState({
    online: true,
    callcenter: true
  })

  // 타이머 refs
  const intervalRef = useRef(null)
  const countdownRef = useRef(null)

  // 계정 목록 로드
  useEffect(() => {
    const loadAccounts = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/coupang-accounts`)
        if (response.ok) {
          const data = await response.json()
          setAccounts(data)

          // localStorage에서 마지막 선택된 계정 복원
          const lastSelectedId = localStorage.getItem('autoMode_accountId')
          if (lastSelectedId && data.find(acc => acc.id === parseInt(lastSelectedId))) {
            setSelectedAccountId(parseInt(lastSelectedId))
          } else if (data.length > 0) {
            setSelectedAccountId(data[0].id)
          }
        }
      } catch (error) {
        console.error('계정 목록 로드 실패:', error)
      }
    }

    if (apiBaseUrl) {
      loadAccounts()
    }
  }, [apiBaseUrl])

  // localStorage에서 설정 복원
  useEffect(() => {
    const savedInterval = localStorage.getItem('autoMode_interval')
    if (savedInterval) {
      setIntervalMinutes(parseInt(savedInterval))
    }

    const savedTypes = localStorage.getItem('autoMode_inquiryTypes')
    if (savedTypes) {
      try {
        setInquiryTypes(JSON.parse(savedTypes))
      } catch (e) {
        // ignore
      }
    }
  }, [])

  // 카운트다운 업데이트
  useEffect(() => {
    if (isAutoModeOn && nextRunTime) {
      countdownRef.current = setInterval(() => {
        const now = new Date()
        const diff = nextRunTime - now
        if (diff > 0) {
          const minutes = Math.floor(diff / 60000)
          const seconds = Math.floor((diff % 60000) / 1000)
          setCountdown(`${minutes}:${seconds.toString().padStart(2, '0')}`)
        } else {
          setCountdown('실행 중...')
        }
      }, 1000)

      return () => {
        if (countdownRef.current) {
          clearInterval(countdownRef.current)
        }
      }
    }
  }, [isAutoModeOn, nextRunTime])

  // 로그 추가 함수
  const addLog = useCallback((message, type = 'info') => {
    const newLog = {
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      message,
      type
    }
    setRecentLogs(prev => [newLog, ...prev].slice(0, 10))
  }, [])

  // 자동화 사이클 실행
  const runAutoCycle = useCallback(async () => {
    if (isRunning) return

    setIsRunning(true)
    const runTime = new Date()
    setLastRunTime(runTime)

    // 선택된 문의 유형 배열 생성
    const selectedTypes = []
    if (inquiryTypes.online) selectedTypes.push('online')
    if (inquiryTypes.callcenter) selectedTypes.push('callcenter')

    if (selectedTypes.length === 0) {
      addLog('문의 유형을 선택해주세요', 'error')
      setIsRunning(false)
      return
    }

    try {
      addLog('자동 수집 시작...', 'info')

      const accountId = parseInt(selectedAccountId, 10)
      if (isNaN(accountId) || accountId <= 0) {
        addLog('유효한 계정을 선택해주세요', 'error')
        setIsRunning(false)
        return
      }

      const response = await fetch(`${apiBaseUrl}/auto-mode/cycle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          inquiry_types: selectedTypes,
          auto_submit: true
        })
      })

      const result = await response.json()

      // HTTP 에러 체크
      if (!response.ok) {
        addLog(`HTTP 에러: ${response.status} - ${result.detail || result.message || '알 수 없는 오류'}`, 'error')
        return
      }

      if (result.success) {
        // 고객센터 확인완료 건수 추출
        const confirmed = result.details?.callcenter?.confirmed || 0

        setStats(prev => ({
          totalCollected: prev.totalCollected + result.collected,
          totalAnswered: prev.totalAnswered + result.answered,
          totalSubmitted: prev.totalSubmitted + result.submitted,
          totalConfirmed: prev.totalConfirmed + confirmed,
          totalFailed: prev.totalFailed + result.failed
        }))

        if (result.collected === 0) {
          addLog('처리할 미답변 문의가 없습니다', 'info')
        } else {
          let logMsg = `수집: ${result.collected}, 제출: ${result.submitted}`
          if (confirmed > 0) {
            logMsg += `, 확인완료: ${confirmed}`
          }
          addLog(logMsg, 'success')
        }
      } else {
        addLog(`실행 실패: ${result.message}`, 'error')
      }
    } catch (error) {
      addLog(`오류: ${error.message}`, 'error')
    } finally {
      setIsRunning(false)
      // 다음 실행 시간 설정
      setNextRunTime(new Date(Date.now() + intervalMinutes * 60 * 1000))
    }
  }, [apiBaseUrl, selectedAccountId, inquiryTypes, intervalMinutes, isRunning, addLog])

  // 자동모드 시작
  const startAutoMode = useCallback(() => {
    if (!selectedAccountId) {
      addLog('계정을 선택해주세요', 'error')
      return
    }

    setIsAutoModeOn(true)

    // 설정 저장
    localStorage.setItem('autoMode_accountId', selectedAccountId.toString())
    localStorage.setItem('autoMode_interval', intervalMinutes.toString())
    localStorage.setItem('autoMode_inquiryTypes', JSON.stringify(inquiryTypes))

    addLog('자동모드가 시작되었습니다', 'success')

    // 즉시 한 번 실행
    runAutoCycle()

    // 주기적 실행 설정
    intervalRef.current = setInterval(runAutoCycle, intervalMinutes * 60 * 1000)
  }, [selectedAccountId, intervalMinutes, inquiryTypes, runAutoCycle, addLog])

  // 자동모드 중지
  const stopAutoMode = useCallback(() => {
    setIsAutoModeOn(false)

    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    setNextRunTime(null)
    setCountdown(null)
    addLog('자동모드가 중지되었습니다', 'info')
  }, [addLog])

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (countdownRef.current) {
        clearInterval(countdownRef.current)
      }
    }
  }, [])

  // 시간 포맷팅
  const formatTime = (date) => {
    if (!date) return '-'
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <motion.div
      className={`auto-mode-panel ${isAutoModeOn ? 'active' : ''}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* 헤더 */}
      <div className="auto-mode-header">
        <div className="header-left">
          <Zap size={24} className={`auto-mode-icon ${isAutoModeOn ? 'active' : ''}`} />
          <div>
            <h3>실시간 자동모드</h3>
            <p>주기적으로 문의를 수집하고 AI가 자동 응답합니다</p>
          </div>
        </div>

        <div className="auto-mode-toggle">
          <span className={`status-badge ${isAutoModeOn ? 'active' : 'inactive'}`}>
            {isAutoModeOn ? '실행 중' : '대기 중'}
          </span>
        </div>
      </div>

      {/* 설정 영역 */}
      <div className="auto-mode-settings">
        {/* 계정 선택 */}
        <div className="setting-group">
          <label>계정 선택</label>
          <select
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(parseInt(e.target.value))}
            disabled={isAutoModeOn}
          >
            <option value="">계정을 선택하세요</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name} ({acc.vendor_id})
              </option>
            ))}
          </select>
        </div>

        {/* 주기 선택 */}
        <div className="setting-group">
          <label>실행 주기</label>
          <select
            value={intervalMinutes}
            onChange={(e) => setIntervalMinutes(parseInt(e.target.value))}
            disabled={isAutoModeOn}
          >
            <option value={1}>1분</option>
            <option value={3}>3분</option>
            <option value={5}>5분</option>
            <option value={10}>10분</option>
            <option value={15}>15분</option>
          </select>
        </div>

        {/* 문의 유형 선택 */}
        <div className="setting-group inquiry-types">
          <label>문의 유형</label>
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={inquiryTypes.online}
                onChange={(e) => setInquiryTypes(prev => ({ ...prev, online: e.target.checked }))}
                disabled={isAutoModeOn}
              />
              <MessageSquare size={14} />
              <span>고객문의</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={inquiryTypes.callcenter}
                onChange={(e) => setInquiryTypes(prev => ({ ...prev, callcenter: e.target.checked }))}
                disabled={isAutoModeOn}
              />
              <Phone size={14} />
              <span>고객센터</span>
            </label>
          </div>
        </div>

        {/* 시작/중지 버튼 */}
        <div className="setting-group button-group">
          {!isAutoModeOn ? (
            <button
              className="start-auto-btn"
              onClick={startAutoMode}
              disabled={!selectedAccountId}
            >
              <Play size={18} />
              <span>자동모드 시작</span>
            </button>
          ) : (
            <button
              className="stop-auto-btn"
              onClick={stopAutoMode}
            >
              <Square size={18} />
              <span>중지</span>
            </button>
          )}
        </div>
      </div>

      {/* 실시간 상태 (자동모드 실행 중일 때만) */}
      <AnimatePresence>
        {isAutoModeOn && (
          <motion.div
            className="auto-mode-status"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            {/* 실행 시간 정보 */}
            <div className="status-row">
              <div className="status-item">
                <Clock size={16} />
                <span>마지막 실행: {formatTime(lastRunTime)}</span>
              </div>
              <div className="status-item">
                <RefreshCw size={16} className={isRunning ? 'spinning' : ''} />
                <span>
                  {isRunning ? '실행 중...' : `다음 실행: ${countdown || '-'}`}
                </span>
              </div>
            </div>

            {/* 통계 */}
            <div className="stats-row five-cols">
              <div className="stat-box">
                <span className="stat-value">{stats.totalCollected}</span>
                <span className="stat-label">수집됨</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{stats.totalAnswered}</span>
                <span className="stat-label">답변 생성</span>
              </div>
              <div className="stat-box success">
                <span className="stat-value">{stats.totalSubmitted}</span>
                <span className="stat-label">제출 완료</span>
              </div>
              <div className="stat-box confirmed">
                <span className="stat-value">{stats.totalConfirmed}</span>
                <span className="stat-label">확인완료</span>
              </div>
              <div className="stat-box error">
                <span className="stat-value">{stats.totalFailed}</span>
                <span className="stat-label">실패</span>
              </div>
            </div>

            {/* 최근 로그 */}
            <div className="recent-logs">
              <div className="logs-header">
                <AlertCircle size={14} />
                <span>실행 로그</span>
              </div>
              <div className="logs-content">
                {recentLogs.length === 0 ? (
                  <div className="no-logs">아직 로그가 없습니다</div>
                ) : (
                  recentLogs.map((log, i) => (
                    <div key={i} className={`log-item ${log.type}`}>
                      {log.type === 'success' && <CheckCircle size={12} />}
                      {log.type === 'error' && <XCircle size={12} />}
                      {log.type === 'info' && <AlertCircle size={12} />}
                      <span className="log-time">{log.time}</span>
                      <span className="log-msg">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default AutoModePanel
