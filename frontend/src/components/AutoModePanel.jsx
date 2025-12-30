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
  Phone,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Power,
  User,
  Settings,
  Activity,
  Edit3,
  Send,
  X,
  ExternalLink,
  RotateCcw
} from 'lucide-react'
import '../styles/AutoModePanel.css'

const AutoModePanel = ({ apiBaseUrl }) => {
  // 세션 목록
  const [sessions, setSessions] = useState([])
  const [expandedSessions, setExpandedSessions] = useState({})

  // 실패 문의 관리
  const [failedInquiries, setFailedInquiries] = useState([])
  const [showFailedPanel, setShowFailedPanel] = useState(false)
  const [selectedInquiry, setSelectedInquiry] = useState(null)
  const [manualReplyText, setManualReplyText] = useState('')
  const [isGeneratingAI, setIsGeneratingAI] = useState(false)
  const [isSubmittingReply, setIsSubmittingReply] = useState(false)

  // 특수 양식 처리 상태
  const [processingSpecialForm, setProcessingSpecialForm] = useState({})
  const [specialFormStatus, setSpecialFormStatus] = useState({})

  // 새 세션 생성 폼
  const [showNewForm, setShowNewForm] = useState(false)
  const [newSession, setNewSession] = useState({
    accountId: '',
    intervalMinutes: 5,
    inquiryTypes: { online: true, callcenter: true }
  })

  // 계정 목록
  const [accounts, setAccounts] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [togglingAccounts, setTogglingAccounts] = useState({}) // 토글 중인 계정 추적

  // 폴링 인터벌
  const pollingRef = useRef(null)

  // 계정 목록 로드
  useEffect(() => {
    const loadAccounts = async () => {
      try {
        console.log('[AutoModePanel] 계정 목록 로드 시작, apiBaseUrl:', apiBaseUrl)
        const response = await fetch(`${apiBaseUrl}/coupang-accounts`)
        console.log('[AutoModePanel] API 응답 상태:', response.status)
        if (response.ok) {
          const data = await response.json()
          console.log('[AutoModePanel] 로드된 계정 목록:', data)
          setAccounts(data)
          if (data.length > 0 && !newSession.accountId) {
            setNewSession(prev => ({ ...prev, accountId: data[0].id }))
          }
        } else {
          const errorText = await response.text()
          console.error('[AutoModePanel] API 응답 에러:', response.status, errorText)
        }
      } catch (error) {
        console.error('[AutoModePanel] 계정 목록 로드 실패:', error)
      }
    }

    if (apiBaseUrl) {
      loadAccounts()
    }
  }, [apiBaseUrl])

  // 세션 목록 로드
  const loadSessions = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/sessions`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (error) {
      console.error('세션 목록 로드 실패:', error)
    }
  }, [apiBaseUrl])

  // 초기 로드 및 폴링
  useEffect(() => {
    if (apiBaseUrl) {
      loadSessions()
      // 5초마다 세션 상태 폴링
      pollingRef.current = setInterval(loadSessions, 5000)
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [apiBaseUrl, loadSessions])

  // 새 세션 생성
  const createSession = async () => {
    if (!newSession.accountId) {
      alert('계정을 선택해주세요')
      return
    }

    const selectedTypes = []
    if (newSession.inquiryTypes.online) selectedTypes.push('online')
    if (newSession.inquiryTypes.callcenter) selectedTypes.push('callcenter')

    if (selectedTypes.length === 0) {
      alert('문의 유형을 선택해주세요')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: parseInt(newSession.accountId),
          interval_minutes: newSession.intervalMinutes,
          inquiry_types: selectedTypes
        })
      })

      if (response.ok) {
        await loadSessions()
        setShowNewForm(false)
        // 폼 초기화
        setNewSession({
          accountId: accounts.length > 0 ? accounts[0].id : '',
          intervalMinutes: 5,
          inquiryTypes: { online: true, callcenter: true }
        })
      } else {
        const error = await response.json()
        alert(`세션 생성 실패: ${error.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      alert(`오류: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  // 세션 토글 (시작/중지)
  const toggleSession = async (sessionId, currentStatus) => {
    const endpoint = currentStatus === 'running' ? 'stop' : 'start'
    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/sessions/${sessionId}/${endpoint}`, {
        method: 'POST'
      })
      if (response.ok) {
        await loadSessions()
      }
    } catch (error) {
      console.error(`세션 ${endpoint} 실패:`, error)
    }
  }

  // 계정별 자동모드 토글 (세션이 없으면 생성, 있으면 시작/중지)
  const toggleAccountAutoMode = async (accountId) => {
    setTogglingAccounts(prev => ({ ...prev, [accountId]: true }))

    try {
      // 이 계정의 세션 찾기
      const existingSession = sessions.find(s => s.account_id === accountId)

      if (existingSession) {
        // 세션이 있으면 상태 토글
        const endpoint = existingSession.status === 'running' ? 'stop' : 'start'
        const response = await fetch(`${apiBaseUrl}/auto-mode/sessions/${existingSession.session_id}/${endpoint}`, {
          method: 'POST'
        })
        if (response.ok) {
          await loadSessions()
        }
      } else {
        // 세션이 없으면 새로 생성
        const response = await fetch(`${apiBaseUrl}/auto-mode/sessions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            account_id: accountId,
            interval_minutes: 5,
            inquiry_types: ['online', 'callcenter']
          })
        })
        if (response.ok) {
          await loadSessions()
        }
      }
    } catch (error) {
      console.error('계정 토글 실패:', error)
    } finally {
      setTogglingAccounts(prev => ({ ...prev, [accountId]: false }))
    }
  }

  // 전체 자동모드 토글
  const toggleAllAutoMode = async () => {
    const runningCount = sessions.filter(s => s.status === 'running').length
    const shouldStop = runningCount > 0

    setIsLoading(true)
    try {
      for (const session of sessions) {
        if (shouldStop && session.status === 'running') {
          await fetch(`${apiBaseUrl}/auto-mode/sessions/${session.session_id}/stop`, {
            method: 'POST'
          })
        } else if (!shouldStop && session.status === 'stopped') {
          await fetch(`${apiBaseUrl}/auto-mode/sessions/${session.session_id}/start`, {
            method: 'POST'
          })
        }
      }
      await loadSessions()
    } catch (error) {
      console.error('전체 토글 실패:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 세션 삭제
  const deleteSession = async (sessionId) => {
    if (!confirm('이 세션을 삭제하시겠습니까?')) return

    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/sessions/${sessionId}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        await loadSessions()
      }
    } catch (error) {
      console.error('세션 삭제 실패:', error)
    }
  }

  // 계정이 자동모드 실행 중인지 확인
  const getAccountSession = (accountId) => {
    return sessions.find(s => s.account_id === accountId)
  }

  // 세션 확장/축소 토글
  const toggleExpand = (sessionId) => {
    setExpandedSessions(prev => ({
      ...prev,
      [sessionId]: !prev[sessionId]
    }))
  }

  // 실패 문의 목록 로드
  const loadFailedInquiries = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/failed-inquiries`)
      if (response.ok) {
        const data = await response.json()
        setFailedInquiries(data.inquiries || [])
      }
    } catch (error) {
      console.error('실패 문의 로드 실패:', error)
    }
  }, [apiBaseUrl])

  // 실패 패널 열기
  const openFailedPanel = async () => {
    setShowFailedPanel(true)
    await loadFailedInquiries()
  }

  // 수동 답변 모달 열기
  const openManualReply = (inquiry) => {
    setSelectedInquiry(inquiry)
    setManualReplyText('')
  }

  // 수동 답변 모달 닫기
  const closeManualReply = () => {
    setSelectedInquiry(null)
    setManualReplyText('')
  }

  // AI 답변 생성
  const generateAIReply = async () => {
    if (!selectedInquiry?.inquiry_content) {
      alert('문의 내용이 없습니다')
      return
    }

    setIsGeneratingAI(true)
    try {
      const response = await fetch(
        `${apiBaseUrl}/auto-mode/generate-reply?inquiry_text=${encodeURIComponent(selectedInquiry.inquiry_content)}&customer_name=${encodeURIComponent(selectedInquiry.customer_name || '고객')}`,
        { method: 'POST' }
      )
      const data = await response.json()
      if (data.success) {
        setManualReplyText(data.response_text)
      } else {
        alert(`AI 답변 생성 실패: ${data.message}`)
      }
    } catch (error) {
      alert(`오류: ${error.message}`)
    } finally {
      setIsGeneratingAI(false)
    }
  }

  // 수동 답변 제출
  const submitManualReply = async () => {
    if (!manualReplyText.trim()) {
      alert('답변 내용을 입력해주세요')
      return
    }

    setIsSubmittingReply(true)
    try {
      const response = await fetch(`${apiBaseUrl}/auto-mode/manual-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: selectedInquiry.account_id,
          inquiry_id: selectedInquiry.inquiry_id,
          inquiry_type: selectedInquiry.inquiry_type || 'online',
          content: manualReplyText,
          reply_by: 'manual'
        })
      })
      const data = await response.json()
      if (data.success) {
        alert('답변이 제출되었습니다')
        closeManualReply()
        await loadFailedInquiries()
      } else {
        alert(`제출 실패: ${data.message}`)
      }
    } catch (error) {
      alert(`오류: ${error.message}`)
    } finally {
      setIsSubmittingReply(false)
    }
  }

  // 특수 양식 상태 확인
  const checkSpecialFormStatus = async (accountId) => {
    try {
      const response = await fetch(`${apiBaseUrl}/special-form/status/${accountId}`)
      if (response.ok) {
        const data = await response.json()
        setSpecialFormStatus(prev => ({ ...prev, [accountId]: data }))
        return data
      }
    } catch (error) {
      console.error('특수 양식 상태 확인 실패:', error)
    }
    return null
  }

  // 특수 양식 자동 처리
  const processSpecialForm = async (inquiry) => {
    const inquiryKey = `${inquiry.account_id}-${inquiry.inquiry_id}`

    // Wing 비밀번호 상태 확인
    const status = await checkSpecialFormStatus(inquiry.account_id)
    if (!status?.can_process) {
      alert(`특수 양식 처리 불가: ${status?.message || 'Wing 로그인 정보가 필요합니다'}`)
      return
    }

    setProcessingSpecialForm(prev => ({ ...prev, [inquiryKey]: true }))

    try {
      const response = await fetch(`${apiBaseUrl}/special-form/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: inquiry.account_id,
          inquiry_id: inquiry.inquiry_id,
          inquiry_content: inquiry.inquiry_content || '',
          customer_name: inquiry.customer_name || '고객',
          special_reply_content: inquiry.special_reply_content || '',
          special_link: inquiry.special_link,
          ai_response: inquiry.response_text,
          headless: true
        })
      })

      const data = await response.json()

      if (data.success) {
        alert('특수 양식 답변이 성공적으로 제출되었습니다!')
        await loadFailedInquiries()
      } else {
        alert(`특수 양식 처리 실패: ${data.result?.error || '알 수 없는 오류'}`)
      }
    } catch (error) {
      alert(`오류: ${error.message}`)
    } finally {
      setProcessingSpecialForm(prev => ({ ...prev, [inquiryKey]: false }))
    }
  }

  // 특수 양식 케이스인지 확인
  const isSpecialFormCase = (inquiry) => {
    const content = inquiry.inquiry_content || inquiry.special_reply_content || ''
    const keywords = ['coupa.ng', '링크를 클릭', '[판매자님 회신필요 사항]', '응답 제출을 위해']
    return keywords.some(keyword => content.includes(keyword))
  }

  // 시간 포맷팅
  const formatTime = (isoString) => {
    if (!isoString) return '-'
    const date = new Date(isoString)
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // 실행 중인 세션 수
  const runningCount = sessions.filter(s => s.status === 'running').length

  // 전체 통계 계산
  const totalStats = sessions.reduce((acc, session) => ({
    collected: acc.collected + (session.stats?.total_collected || 0),
    answered: acc.answered + (session.stats?.total_answered || 0),
    submitted: acc.submitted + (session.stats?.total_submitted || 0),
    confirmed: acc.confirmed + (session.stats?.total_confirmed || 0),
    failed: acc.failed + (session.stats?.total_failed || 0)
  }), { collected: 0, answered: 0, submitted: 0, confirmed: 0, failed: 0 })

  return (
    <motion.div
      className={`auto-mode-panel ${runningCount > 0 ? 'active' : ''}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* 헤더 */}
      <div className="auto-mode-header">
        <div className="header-left">
          <Zap size={24} className={`auto-mode-icon ${runningCount > 0 ? 'active' : ''}`} />
          <div>
            <h3>실시간 자동모드</h3>
            <p>계정별로 자동모드를 ON/OFF하여 관리하세요</p>
          </div>
        </div>

        <div className="header-right">
          <span className={`status-badge ${runningCount > 0 ? 'active' : 'inactive'}`}>
            {runningCount > 0 ? `${runningCount}개 실행 중` : '대기 중'}
          </span>
          {sessions.length > 0 && (
            <button
              className={`master-toggle-btn ${runningCount > 0 ? 'active' : ''}`}
              onClick={toggleAllAutoMode}
              disabled={isLoading}
            >
              {isLoading ? (
                <RefreshCw size={16} className="spinning" />
              ) : (
                <Power size={16} />
              )}
              <span>{runningCount > 0 ? '전체 OFF' : '전체 ON'}</span>
            </button>
          )}
        </div>
      </div>

      {/* 계정 목록 - 토글 스위치 */}
      <div className="accounts-toggle-list">
        <div className="accounts-list-header">
          <Activity size={16} />
          <span>계정별 자동모드 상태</span>
          <button
            className="add-account-btn"
            onClick={() => setShowNewForm(!showNewForm)}
          >
            <Plus size={14} />
            <span>계정 추가</span>
          </button>
        </div>

        {/* 새 세션 생성 폼 */}
        <AnimatePresence>
          {showNewForm && (
            <motion.div
              className="new-session-form"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <div className="form-row">
                <div className="form-group">
                  <label>계정 선택</label>
                  <select
                    value={newSession.accountId}
                    onChange={(e) => setNewSession(prev => ({ ...prev, accountId: e.target.value }))}
                  >
                    <option value="">계정을 선택하세요</option>
                    {accounts.filter(acc => !sessions.find(s => s.account_id === acc.id)).map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} ({acc.vendor_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>실행 주기</label>
                  <select
                    value={newSession.intervalMinutes}
                    onChange={(e) => setNewSession(prev => ({ ...prev, intervalMinutes: parseInt(e.target.value) }))}
                  >
                    <option value={1}>1분</option>
                    <option value={3}>3분</option>
                    <option value={5}>5분</option>
                    <option value={10}>10분</option>
                    <option value={15}>15분</option>
                  </select>
                </div>

                <div className="form-group inquiry-types">
                  <label>문의 유형</label>
                  <div className="checkbox-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newSession.inquiryTypes.online}
                        onChange={(e) => setNewSession(prev => ({
                          ...prev,
                          inquiryTypes: { ...prev.inquiryTypes, online: e.target.checked }
                        }))}
                      />
                      <MessageSquare size={14} />
                      <span>고객문의</span>
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newSession.inquiryTypes.callcenter}
                        onChange={(e) => setNewSession(prev => ({
                          ...prev,
                          inquiryTypes: { ...prev.inquiryTypes, callcenter: e.target.checked }
                        }))}
                      />
                      <Phone size={14} />
                      <span>고객센터</span>
                    </label>
                  </div>
                </div>

                <div className="form-group button-group">
                  <button
                    className="create-btn"
                    onClick={createSession}
                    disabled={isLoading}
                  >
                    {isLoading ? <RefreshCw size={16} className="spinning" /> : <Play size={16} />}
                    <span>추가</span>
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 계정별 토글 리스트 */}
        <div className="accounts-grid">
          {sessions.length === 0 ? (
            <div className="no-accounts">
              <User size={20} />
              <p>등록된 자동모드 계정이 없습니다</p>
              <span>위의 "계정 추가" 버튼을 클릭하여 자동모드를 시작하세요</span>
            </div>
          ) : (
            sessions.map((session) => {
              const isRunning = session.status === 'running'
              const isToggling = togglingAccounts[session.account_id]
              const isExpanded = expandedSessions[session.session_id]

              return (
                <motion.div
                  key={session.session_id}
                  className={`account-toggle-card ${isRunning ? 'running' : 'stopped'}`}
                  layout
                >
                  <div className="account-toggle-header">
                    <div className="account-info" onClick={() => toggleExpand(session.session_id)}>
                      <div className={`status-indicator ${isRunning ? 'running' : 'stopped'}`}>
                        {isRunning && <span className="pulse-dot"></span>}
                      </div>
                      <div className="account-details">
                        <span className="account-name">{session.account_name}</span>
                        <span className="account-meta">
                          {session.vendor_id} · {session.interval_minutes}분 주기
                        </span>
                      </div>
                    </div>

                    <div className="account-controls">
                      {/* 실시간 통계 미니 뱃지 */}
                      {isRunning && (
                        <div className="mini-stats">
                          <span className="mini-stat success">{session.stats.total_submitted}</span>
                        </div>
                      )}

                      {/* ON/OFF 토글 스위치 */}
                      <label className="toggle-switch">
                        <input
                          type="checkbox"
                          checked={isRunning}
                          onChange={() => toggleSession(session.session_id, session.status)}
                          disabled={isToggling}
                        />
                        <span className="toggle-slider">
                          {isToggling && <RefreshCw size={12} className="spinning toggle-loading" />}
                        </span>
                        <span className="toggle-label">{isRunning ? 'ON' : 'OFF'}</span>
                      </label>

                      {/* 삭제 버튼 */}
                      <button
                        className="delete-btn-small"
                        onClick={() => deleteSession(session.session_id)}
                        title="세션 삭제"
                      >
                        <Trash2 size={14} />
                      </button>

                      {/* 확장 아이콘 */}
                      <button
                        className="expand-btn"
                        onClick={() => toggleExpand(session.session_id)}
                      >
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                    </div>
                  </div>

                  {/* 확장된 상세 정보 */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        className="account-expanded"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                      >
                        {/* 실행 시간 정보 */}
                        <div className="time-info">
                          <div className="time-item">
                            <Clock size={14} />
                            <span>마지막: {formatTime(session.last_run)}</span>
                          </div>
                          <div className="time-item">
                            <RefreshCw size={14} className={isRunning ? 'spinning' : ''} />
                            <span>다음: {isRunning ? formatTime(session.next_run) : '-'}</span>
                          </div>
                        </div>

                        {/* 문의 유형 */}
                        <div className="inquiry-type-badges">
                          {session.inquiry_types.includes('online') && (
                            <span className="type-badge online">
                              <MessageSquare size={12} /> 고객문의
                            </span>
                          )}
                          {session.inquiry_types.includes('callcenter') && (
                            <span className="type-badge callcenter">
                              <Phone size={12} /> 고객센터
                            </span>
                          )}
                        </div>

                        {/* 통계 */}
                        <div className="session-stats compact">
                          <div className="stat-item">
                            <span className="stat-value">{session.stats.total_collected}</span>
                            <span className="stat-label">수집</span>
                          </div>
                          <div className="stat-item">
                            <span className="stat-value">{session.stats.total_answered}</span>
                            <span className="stat-label">답변</span>
                          </div>
                          <div className="stat-item success">
                            <span className="stat-value">{session.stats.total_submitted}</span>
                            <span className="stat-label">제출</span>
                          </div>
                          <div className="stat-item confirmed">
                            <span className="stat-value">{session.stats.total_confirmed}</span>
                            <span className="stat-label">확인</span>
                          </div>
                          <div className="stat-item error">
                            <span className="stat-value">{session.stats.total_failed}</span>
                            <span className="stat-label">실패</span>
                          </div>
                        </div>

                        {/* 최근 로그 */}
                        <div className="session-logs compact">
                          <div className="logs-header">
                            <AlertCircle size={12} />
                            <span>최근 로그</span>
                          </div>
                          <div className="logs-content">
                            {session.recent_logs.length === 0 ? (
                              <div className="no-logs">로그 없음</div>
                            ) : (
                              session.recent_logs.slice(0, 3).map((log, i) => (
                                <div key={i} className={`log-item ${log.type}`}>
                                  {log.type === 'success' && <CheckCircle size={10} />}
                                  {log.type === 'error' && <XCircle size={10} />}
                                  {log.type === 'info' && <AlertCircle size={10} />}
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
            })
          )}
        </div>
      </div>

      {/* 전체 통계 요약 (세션이 있을 때만) */}
      {sessions.length > 0 && (
        <div className="total-stats-summary">
          <div className="summary-title">전체 통계</div>
          <div className="summary-stats">
            <div className="summary-item">
              <span className="summary-value">{totalStats.collected}</span>
              <span className="summary-label">수집</span>
            </div>
            <div className="summary-item">
              <span className="summary-value">{totalStats.answered}</span>
              <span className="summary-label">답변</span>
            </div>
            <div className="summary-item success">
              <span className="summary-value">{totalStats.submitted}</span>
              <span className="summary-label">제출</span>
            </div>
            <div className="summary-item confirmed">
              <span className="summary-value">{totalStats.confirmed}</span>
              <span className="summary-label">확인</span>
            </div>
            <div
              className="summary-item error clickable"
              onClick={openFailedPanel}
              title="클릭하여 실패 문의 확인"
            >
              <span className="summary-value">{totalStats.failed}</span>
              <span className="summary-label">실패</span>
            </div>
          </div>
        </div>
      )}

      {/* 실패 문의 패널 */}
      <AnimatePresence>
        {showFailedPanel && (
          <motion.div
            className="failed-panel-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowFailedPanel(false)}
          >
            <motion.div
              className="failed-panel"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="failed-panel-header">
                <h3>
                  <XCircle size={20} />
                  실패한 문의 ({failedInquiries.length}건)
                </h3>
                <div className="failed-panel-actions">
                  <button onClick={loadFailedInquiries} className="refresh-btn">
                    <RefreshCw size={16} />
                  </button>
                  <button onClick={() => setShowFailedPanel(false)} className="close-btn">
                    <X size={20} />
                  </button>
                </div>
              </div>

              <div className="failed-panel-content">
                {failedInquiries.length === 0 ? (
                  <div className="no-failed">
                    <CheckCircle size={48} />
                    <p>실패한 문의가 없습니다</p>
                  </div>
                ) : (
                  <div className="failed-list">
                    {failedInquiries.map((inquiry, idx) => (
                      <div key={`${inquiry.inquiry_id}-${idx}`} className="failed-item">
                        <div className="failed-item-header">
                          <span className="account-badge">{inquiry.account_name}</span>
                          <span className="time-badge">{inquiry.time || formatTime(inquiry.timestamp)}</span>
                          <span className={`status-badge ${inquiry.status}`}>
                            {inquiry.status === 'failed' ? '실패' : '건너뜀'}
                          </span>
                        </div>

                        <div className="failed-reason">
                          <AlertCircle size={14} />
                          <span>{inquiry.error || '알 수 없는 오류'}</span>
                        </div>

                        <div className="failed-customer">
                          <User size={14} />
                          <span>{inquiry.customer_name || '고객'}</span>
                        </div>

                        <div className="failed-content">
                          <p>{inquiry.inquiry_content || '(문의 내용 없음)'}</p>
                        </div>

                        {inquiry.response_text && (
                          <div className="ai-response-preview">
                            <span className="label">AI 답변:</span>
                            <p>{inquiry.response_text.substring(0, 100)}...</p>
                          </div>
                        )}

                        <div className="failed-actions">
                          <button
                            className="action-btn primary"
                            onClick={() => openManualReply(inquiry)}
                          >
                            <Edit3 size={14} />
                            수동 답변
                          </button>
                          {isSpecialFormCase(inquiry) && (
                            <button
                              className="action-btn special"
                              onClick={() => processSpecialForm(inquiry)}
                              disabled={processingSpecialForm[`${inquiry.account_id}-${inquiry.inquiry_id}`]}
                            >
                              {processingSpecialForm[`${inquiry.account_id}-${inquiry.inquiry_id}`] ? (
                                <>
                                  <RefreshCw size={14} className="spinning" />
                                  처리 중...
                                </>
                              ) : (
                                <>
                                  <Zap size={14} />
                                  특수 양식 자동 처리
                                </>
                              )}
                            </button>
                          )}
                          {inquiry.special_reply_content && (
                            <button
                              className="action-btn secondary"
                              onClick={() => window.open(`https://wing.coupang.com`, '_blank')}
                            >
                              <ExternalLink size={14} />
                              링크 열기
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 수동 답변 모달 */}
      <AnimatePresence>
        {selectedInquiry && (
          <motion.div
            className="manual-reply-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeManualReply}
          >
            <motion.div
              className="manual-reply-modal"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>
                  <Edit3 size={20} />
                  수동 답변 작성
                </h3>
                <button onClick={closeManualReply} className="close-btn">
                  <X size={20} />
                </button>
              </div>

              <div className="modal-content">
                <div className="inquiry-info">
                  <div className="info-row">
                    <span className="label">계정:</span>
                    <span>{selectedInquiry.account_name}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">문의 ID:</span>
                    <span>{selectedInquiry.inquiry_id}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">고객:</span>
                    <span>{selectedInquiry.customer_name || '고객'}</span>
                  </div>
                </div>

                <div className="inquiry-content-box">
                  <div className="box-label">문의 내용</div>
                  <div className="box-content">
                    {selectedInquiry.inquiry_content || '(문의 내용 없음)'}
                  </div>
                </div>

                <div className="reply-input-box">
                  <div className="box-label">
                    답변 작성
                    <button
                      className="ai-generate-btn"
                      onClick={generateAIReply}
                      disabled={isGeneratingAI}
                    >
                      {isGeneratingAI ? (
                        <>
                          <RefreshCw size={14} className="spinning" />
                          생성 중...
                        </>
                      ) : (
                        <>
                          <RotateCcw size={14} />
                          AI 답변 생성
                        </>
                      )}
                    </button>
                  </div>
                  <textarea
                    value={manualReplyText}
                    onChange={(e) => setManualReplyText(e.target.value)}
                    placeholder="답변 내용을 입력하세요..."
                    rows={8}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  className="cancel-btn"
                  onClick={closeManualReply}
                >
                  취소
                </button>
                <button
                  className="submit-btn"
                  onClick={submitManualReply}
                  disabled={isSubmittingReply || !manualReplyText.trim()}
                >
                  {isSubmittingReply ? (
                    <>
                      <RefreshCw size={16} className="spinning" />
                      제출 중...
                    </>
                  ) : (
                    <>
                      <Send size={16} />
                      답변 제출
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default AutoModePanel
