import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE_URL = 'http://localhost:8080/api'

function App() {
  const [responses, setResponses] = useState([])
  const [stats, setStats] = useState(null)
  const [automationStats, setAutomationStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editedText, setEditedText] = useState('')
  const [notification, setNotification] = useState(null)

  // Wing login credentials
  const [wingUsername, setWingUsername] = useState(localStorage.getItem('wingUsername') || '')
  const [wingPassword, setWingPassword] = useState(localStorage.getItem('wingPassword') || '')
  const [connectionStatus, setConnectionStatus] = useState('disconnected') // disconnected, connecting, connected, failed
  const [showLoginForm, setShowLoginForm] = useState(false)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const loadData = async () => {
    try {
      setLoading(true)
      const [responsesRes, statsRes, autoStatsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/responses/pending-approval`),
        axios.get(`${API_BASE_URL}/system/stats`),
        axios.get(`${API_BASE_URL}/automation/stats`)
      ])

      setResponses(responsesRes.data)
      setStats(statsRes.data)
      setAutomationStats(autoStatsRes.data)
    } catch (error) {
      console.error('데이터 로드 실패:', error)
      showNotification('데이터를 불러오는데 실패했습니다', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAutoWorkflow = async () => {
    if (!confirm('AI가 자동으로 문의를 처리하고 안전한 답변은 쿠팡에 자동 제출합니다. 계속하시겠습니까?')) return

    try {
      setLoading(true)
      const response = await axios.post(`${API_BASE_URL}/automation/auto-process-and-submit`, null, {
        params: { limit: 10 }
      })
      const results = response.data.results
      showNotification(
        `완전 자동 처리 완료!\n✅ 수집: ${results.collected}건\n🤖 AI 생성: ${results.generated}건\n✓ 자동 승인: ${results.auto_approved}건\n🚀 자동 제출: ${results.submitted}건\n⚠️ 사람 검토 필요: ${results.requires_human}건`,
        'success'
      )
      loadData()
    } catch (error) {
      console.error('자동 처리 실패:', error)
      showNotification('자동 처리에 실패했습니다', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleTestConnection = async () => {
    if (!wingUsername || !wingPassword) {
      showNotification('아이디와 비밀번호를 입력해주세요', 'error')
      return
    }

    try {
      setConnectionStatus('connecting')
      showNotification('쿠팡 윙 로그인 테스트 중...', 'success')

      const response = await axios.post(`${API_BASE_URL}/wing-web/test-login`, {
        username: wingUsername,
        password: wingPassword,
        headless: false
      })

      if (response.data.success) {
        setConnectionStatus('connected')
        showNotification('✅ 쿠팡 윙 로그인 성공!', 'success')
        // Save to localStorage
        localStorage.setItem('wingUsername', wingUsername)
        localStorage.setItem('wingPassword', wingPassword)
      } else {
        setConnectionStatus('failed')
        showNotification('❌ 로그인 실패: ' + response.data.message, 'error')
      }
    } catch (error) {
      setConnectionStatus('failed')
      console.error('연결 테스트 실패:', error)
      const errorMsg = error.response?.data?.detail || error.message
      showNotification(`연결 테스트 실패: ${errorMsg}`, 'error')
    }
  }

  const handleSaveCredentials = () => {
    if (!wingUsername || !wingPassword) {
      showNotification('아이디와 비밀번호를 입력해주세요', 'error')
      return
    }
    localStorage.setItem('wingUsername', wingUsername)
    localStorage.setItem('wingPassword', wingPassword)
    showNotification('로그인 정보가 저장되었습니다', 'success')
  }

  const handleWebAutomation = async () => {
    if (!wingUsername || !wingPassword) {
      showNotification('쿠팡 윙 로그인 정보를 먼저 입력해주세요', 'error')
      setShowLoginForm(true)
      return
    }

    if (!confirm('쿠팡 윙 웹사이트에 직접 접속하여 문의를 읽고 자동으로 답변을 작성합니다. 계속하시겠습니까?')) return

    try {
      setLoading(true)
      showNotification('웹 자동화를 시작합니다... 브라우저가 열리고 자동으로 작업이 진행됩니다.', 'success')

      const response = await axios.post(`${API_BASE_URL}/wing-web/auto-answer`, {
        username: wingUsername,
        password: wingPassword,
        headless: false
      })

      const { success, message, statistics } = response.data

      if (success) {
        showNotification(
          `✅ 웹 자동화 완료!\n총 문의: ${statistics.total}건\n성공: ${statistics.success}건\n실패: ${statistics.failed}건`,
          'success'
        )
      } else {
        showNotification(`웹 자동화 실패: ${message}`, 'error')
      }

      loadData()
    } catch (error) {
      console.error('웹 자동화 실패:', error)
      const errorMsg = error.response?.data?.detail || error.message
      showNotification(`웹 자동화 실패: ${errorMsg}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (responseId) => {
    try {
      await axios.post(`${API_BASE_URL}/responses/${responseId}/approve`, {
        approved_by: 'admin',
        edited_text: editingId === responseId ? editedText : null
      })

      await axios.post(`${API_BASE_URL}/responses/${responseId}/submit`, {
        submitted_by: 'admin'
      })

      showNotification('승인 및 제출이 완료되었습니다', 'success')
      setEditingId(null)
      loadData()
    } catch (error) {
      console.error('승인 실패:', error)
      showNotification('승인에 실패했습니다', 'error')
    }
  }

  const handleReject = async (responseId) => {
    const reason = prompt('거부 사유를 입력해주세요:')
    if (!reason) return

    try {
      await axios.post(`${API_BASE_URL}/responses/${responseId}/reject`, null, {
        params: { reason }
      })
      showNotification('거부되었습니다', 'success')
      loadData()
    } catch (error) {
      console.error('거부 실패:', error)
      showNotification('거부에 실패했습니다', 'error')
    }
  }

  const startEdit = (response) => {
    setEditingId(response.id)
    setEditedText(response.response_text)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditedText('')
  }

  const getRiskBadgeColor = (level) => {
    const colors = {
      low: { bg: '#10b981', text: '낮음', icon: '✓' },
      medium: { bg: '#f59e0b', text: '보통', icon: '⚠' },
      high: { bg: '#ef4444', text: '높음', icon: '!' }
    }
    return colors[level] || colors.medium
  }

  const getStatusBadgeColor = (status) => {
    const colors = {
      approved: { bg: '#10b981', text: '승인됨', icon: '✓' },
      pending_approval: { bg: '#3b82f6', text: '승인 대기', icon: '⏳' },
      draft: { bg: '#6b7280', text: '초안', icon: '📝' },
      rejected: { bg: '#ef4444', text: '거부됨', icon: '✗' }
    }
    return colors[status] || colors.draft
  }

  const getConnectionStatusColor = () => {
    const colors = {
      disconnected: { bg: '#6b7280', text: '미연결', icon: '⚪' },
      connecting: { bg: '#f59e0b', text: '연결 중...', icon: '🔄' },
      connected: { bg: '#10b981', text: '연결됨', icon: '✅' },
      failed: { bg: '#ef4444', text: '연결 실패', icon: '❌' }
    }
    return colors[connectionStatus] || colors.disconnected
  }

  return (
    <div className="app-container">
      {/* Notification */}
      {notification && (
        <div className={`notification ${notification.type === 'error' ? 'notification-error' : 'notification-success'}`}>
          <div className="notification-content">
            <span className="notification-icon">{notification.type === 'error' ? '❌' : '✅'}</span>
            <div className="notification-message">{notification.message}</div>
          </div>
        </div>
      )}

      <div className="container">
        {/* Header */}
        <div className="header-card">
          <div className="header-top">
            <div className="header-title-wrapper">
              <h1 className="header-title">
                <span className="header-icon">🤖</span>
                쿠팡 윙 CS AI 자동화
              </h1>
              <p className="header-subtitle">ChatGPT 기반 자동 답변 및 제출 시스템</p>
            </div>
            <div className="status-indicator">
              <div className="status-dot"></div>
              <span className="status-text">시스템 활성화</span>
            </div>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="stats-grid">
              <div className="stat-card" style={{ '--stat-color-start': '#3b82f6', '--stat-color-end': '#2563eb' }}>
                <div className="stat-label">📥 대기중</div>
                <div className="stat-value">{stats.inquiries.pending || 0}</div>
              </div>
              <div className="stat-card" style={{ '--stat-color-start': '#10b981', '--stat-color-end': '#059669' }}>
                <div className="stat-label">✅ 처리완료</div>
                <div className="stat-value">{stats.inquiries.processed || 0}</div>
              </div>
              <div className="stat-card" style={{ '--stat-color-start': '#f59e0b', '--stat-color-end': '#d97706' }}>
                <div className="stat-label">⏳ 승인대기</div>
                <div className="stat-value">{stats.submissions.pending_submission || 0}</div>
              </div>
              <div className="stat-card" style={{ '--stat-color-start': '#8b5cf6', '--stat-color-end': '#7c3aed' }}>
                <div className="stat-label">🚀 제출완료</div>
                <div className="stat-value">{stats.submissions.submission_success || 0}</div>
              </div>
            </div>
          )}

          {/* Automation Stats */}
          {automationStats && (
            <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
              <div className="stat-card" style={{ '--stat-color-start': '#667eea', '--stat-color-end': '#764ba2' }}>
                <div className="stat-label">🤖 자동 승인률</div>
                <div className="stat-value">{automationStats.auto_approval_rate || 0}%</div>
              </div>
              <div className="stat-card" style={{ '--stat-color-start': '#06b6d4', '--stat-color-end': '#0891b2' }}>
                <div className="stat-label">⚡ 자동 제출률</div>
                <div className="stat-value">{automationStats.auto_submission_rate || 0}%</div>
              </div>
            </div>
          )}
        </div>

        {/* Wing Login Form */}
        <div className="header-card" style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ color: 'white', fontSize: '20px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span>🔐</span>
              <span>쿠팡 윙 로그인</span>
            </h3>
            <button
              onClick={() => setShowLoginForm(!showLoginForm)}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              {showLoginForm ? '접기 ▲' : '펼치기 ▼'}
            </button>
          </div>

          {/* Connection Status Badge */}
          <div style={{ marginBottom: showLoginForm ? '20px' : '0' }}>
            {(() => {
              const statusColor = getConnectionStatusColor()
              return (
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: statusColor.bg,
                  padding: '10px 20px',
                  borderRadius: '100px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'white'
                }}>
                  <span>{statusColor.icon}</span>
                  <span>{statusColor.text}</span>
                </div>
              )
            })()}
          </div>

          {showLoginForm && (
            <div style={{ marginTop: '20px', animation: 'fadeIn 0.3s ease-out' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <label style={{
                    display: 'block',
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '8px'
                  }}>
                    아이디
                  </label>
                  <input
                    type="text"
                    value={wingUsername}
                    onChange={(e) => setWingUsername(e.target.value)}
                    placeholder="아이디를 입력하세요"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '12px',
                      color: 'white',
                      fontSize: '15px',
                      fontFamily: 'Inter, sans-serif'
                    }}
                  />
                </div>
                <div>
                  <label style={{
                    display: 'block',
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '8px'
                  }}>
                    비밀번호
                  </label>
                  <input
                    type="password"
                    value={wingPassword}
                    onChange={(e) => setWingPassword(e.target.value)}
                    placeholder="••••••••"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '2px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '12px',
                      color: 'white',
                      fontSize: '15px',
                      fontFamily: 'Inter, sans-serif'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  className="btn"
                  onClick={handleTestConnection}
                  disabled={loading || connectionStatus === 'connecting'}
                  style={{
                    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                    color: 'white',
                    padding: '12px 24px',
                    borderRadius: '12px',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  <span>🔍</span>
                  <span>연결 테스트</span>
                </button>
                <button
                  className="btn"
                  onClick={handleSaveCredentials}
                  disabled={loading}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: 'white',
                    padding: '12px 24px',
                    borderRadius: '12px',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  <span>💾</span>
                  <span>저장하기</span>
                </button>
              </div>

              <div style={{
                marginTop: '16px',
                padding: '12px 16px',
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '12px',
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '13px',
                lineHeight: '1.6'
              }}>
                <strong>💡 안내:</strong> 입력한 정보는 브라우저에만 저장되며, 로그인 테스트를 통해 연결을 확인할 수 있습니다.
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="action-buttons">
          <button
            className="btn btn-primary"
            onClick={handleWebAutomation}
            disabled={loading || connectionStatus !== 'connected'}
            style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}
          >
            <span className="btn-icon">🌐</span>
            <span>쿠팡 윙 웹 자동화</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={handleAutoWorkflow}
            disabled={loading}
          >
            <span className="btn-icon">🚀</span>
            <span>AI 자동 처리 + 제출</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={loadData}
            disabled={loading}
          >
            <span className="btn-icon">🔄</span>
            <span>새로고침</span>
          </button>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <div className="loading-text">처리 중...</div>
          </div>
        )}

        {/* Empty State */}
        {!loading && responses.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h2 className="empty-title">승인 대기 중인 답변이 없습니다</h2>
            <p className="empty-description">AI 자동 처리를 실행하여 새로운 답변을 생성하세요</p>
          </div>
        )}

        {/* Response Cards */}
        <div className="response-list">
          {responses.map((response) => {
            const statusBadge = getStatusBadgeColor(response.status)
            const riskBadge = getRiskBadgeColor(response.risk_level)

            return (
              <div key={response.id} className="response-card">
                {/* Card Header */}
                <div className="response-header">
                  <div className="response-badges">
                    <span className="badge" style={{ background: statusBadge.bg }}>
                      <span className="badge-icon">{statusBadge.icon}</span>
                      <span>{statusBadge.text}</span>
                    </span>
                    <span className="badge" style={{ background: riskBadge.bg }}>
                      <span className="badge-icon">{riskBadge.icon}</span>
                      <span>위험도: {riskBadge.text}</span>
                    </span>
                    <span className="badge" style={{ background: '#3b82f6' }}>
                      <span className="badge-icon">🎯</span>
                      <span>신뢰도: {response.confidence_score?.toFixed(1) || 'N/A'}%</span>
                    </span>
                    <span className="badge" style={{ background: response.validation_passed ? '#10b981' : '#ef4444' }}>
                      <span className="badge-icon">{response.validation_passed ? '✓' : '✗'}</span>
                      <span>{response.validation_passed ? '검증 통과' : '검증 실패'}</span>
                    </span>
                  </div>
                  <div className="response-id">ID: #{response.inquiry_id}</div>
                </div>

                {/* Inquiry Section */}
                {response.inquiry && (
                  <div className="inquiry-section">
                    <h3 className="response-section-title">
                      <span>📨</span>
                      <span>고객 문의</span>
                    </h3>
                    <div className="inquiry-text">{response.inquiry.inquiry_text || '문의 내용 없음'}</div>
                  </div>
                )}

                {/* Response Content */}
                <div className="response-content">
                  <h3 className="response-section-title">
                    <span>🤖</span>
                    <span>AI 생성 답변</span>
                  </h3>
                  {editingId === response.id ? (
                    <textarea
                      value={editedText}
                      onChange={(e) => setEditedText(e.target.value)}
                      className="response-textarea"
                      placeholder="답변을 입력하세요..."
                    />
                  ) : (
                    <div className="response-text-box">
                      {response.response_text}
                    </div>
                  )}
                </div>

                {/* Additional Info */}
                {response.template_used && (
                  <div style={{ marginBottom: '16px', fontSize: '13px', color: 'rgba(255, 255, 255, 0.6)' }}>
                    📄 템플릿: {response.template_used}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="response-actions">
                  {editingId === response.id ? (
                    <>
                      <button
                        className="btn btn-approve"
                        onClick={() => handleApprove(response.id)}
                      >
                        <span>✓</span>
                        <span>수정 후 승인 & 제출</span>
                      </button>
                      <button
                        className="btn btn-cancel"
                        onClick={cancelEdit}
                      >
                        취소
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn btn-approve"
                        onClick={() => handleApprove(response.id)}
                      >
                        <span>✓</span>
                        <span>승인 & 자동 제출</span>
                      </button>
                      <button
                        className="btn btn-edit"
                        onClick={() => startEdit(response)}
                      >
                        <span>✎</span>
                        <span>수정</span>
                      </button>
                      <button
                        className="btn btn-reject"
                        onClick={() => handleReject(response.id)}
                      >
                        <span>✗</span>
                        <span>거부</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default App
