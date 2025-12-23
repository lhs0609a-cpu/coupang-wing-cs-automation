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
  Activity
} from 'lucide-react'
import '../styles/AutoModePanel.css'

const AutoModePanel = ({ apiBaseUrl }) => {
  // 세션 목록
  const [sessions, setSessions] = useState([])
  const [expandedSessions, setExpandedSessions] = useState({})

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
        const response = await fetch(`${apiBaseUrl}/coupang-accounts`)
        if (response.ok) {
          const data = await response.json()
          setAccounts(data)
          if (data.length > 0 && !newSession.accountId) {
            setNewSession(prev => ({ ...prev, accountId: data[0].id }))
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
            <div className="summary-item error">
              <span className="summary-value">{totalStats.failed}</span>
              <span className="summary-label">실패</span>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  )
}

export default AutoModePanel
