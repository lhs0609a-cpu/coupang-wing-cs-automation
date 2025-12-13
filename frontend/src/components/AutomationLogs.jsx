import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader,
  Play,
  LogIn,
  Filter,
  Calendar,
  User,
  Eye
} from 'lucide-react'
import '../styles/AutomationLogs.css'

const AutomationLogs = ({ apiBaseUrl }) => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [expandedLog, setExpandedLog] = useState(null)

  useEffect(() => {
    loadLogs()
    // Refresh logs every 30 seconds
    const interval = setInterval(loadLogs, 30000)
    return () => clearInterval(interval)
  }, [filterType, filterStatus])

  const loadLogs = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filterType !== 'all') params.append('execution_type', filterType)
      if (filterStatus !== 'all') params.append('status', filterStatus)

      const response = await fetch(`${apiBaseUrl}/wing-web/execution-logs?${params}`)
      const data = await response.json()

      if (data.success) {
        setLogs(data.logs || [])
      }
    } catch (error) {
      console.error('로그 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    if (seconds < 60) return `${seconds}초`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}분 ${remainingSeconds}초`
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={20} className="status-icon success" />
      case 'failed':
        return <XCircle size={20} className="status-icon error" />
      case 'running':
        return <Loader size={20} className="status-icon running spinner" />
      default:
        return <Clock size={20} className="status-icon" />
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'test_login':
        return <LogIn size={18} />
      case 'auto_answer_v2':
      case 'auto_answer_v3':
        return <Play size={18} />
      default:
        return <Play size={18} />
    }
  }

  const getTypeLabel = (type) => {
    switch (type) {
      case 'test_login':
        return '로그인 테스트'
      case 'auto_answer_v2':
        return '자동 답변 V2'
      case 'auto_answer_v3':
        return '자동 답변 V3'
      default:
        return type
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'success':
        return '성공'
      case 'failed':
        return '실패'
      case 'running':
        return '실행 중'
      default:
        return status
    }
  }

  const toggleExpand = (logId) => {
    setExpandedLog(expandedLog === logId ? null : logId)
  }

  return (
    <div className="automation-logs">
      <div className="logs-header">
        <div>
          <h2 className="logs-title">자동화 실행 기록</h2>
          <p className="logs-subtitle">모든 자동화 실행 내역과 결과를 확인하세요</p>
        </div>
        <button className="refresh-button" onClick={loadLogs} disabled={loading}>
          {loading ? <Loader size={18} className="spinner" /> : '🔄'}
          <span>새로고침</span>
        </button>
      </div>

      {/* Filters */}
      <div className="logs-filters">
        <div className="filter-group">
          <Filter size={18} className="filter-icon" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="all">전체 타입</option>
            <option value="test_login">로그인 테스트</option>
            <option value="auto_answer_v2">자동 답변 V2</option>
            <option value="auto_answer_v3">자동 답변 V3</option>
          </select>
        </div>

        <div className="filter-group">
          <span className="filter-icon">🎯</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">전체 상태</option>
            <option value="success">성공</option>
            <option value="failed">실패</option>
            <option value="running">실행 중</option>
          </select>
        </div>
      </div>

      {/* Logs List */}
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>로그를 불러오는 중...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>표시할 로그가 없습니다</h3>
          <p>자동화를 실행하면 여기에 기록이 표시됩니다</p>
        </div>
      ) : (
        <div className="logs-list">
          <AnimatePresence mode="popLayout">
            {logs.map((log, index) => (
              <motion.div
                key={log.id}
                className={`log-card ${log.status}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ delay: index * 0.03 }}
                layout
              >
                {/* Log Header */}
                <div className="log-card-header">
                  <div className="log-info">
                    <div className="log-type">
                      {getTypeIcon(log.execution_type)}
                      <span>{getTypeLabel(log.execution_type)}</span>
                    </div>
                    <div className="log-meta">
                      <span className="log-id">#{log.id}</span>
                      <span className="log-date">
                        <Calendar size={14} />
                        {formatDate(log.started_at)}
                      </span>
                      {log.username && (
                        <span className="log-user">
                          <User size={14} />
                          {log.username}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="log-status">
                    {getStatusIcon(log.status)}
                    <span className={`status-text ${log.status}`}>
                      {getStatusLabel(log.status)}
                    </span>
                  </div>
                </div>

                {/* Log Stats (for automation runs) */}
                {log.statistics && log.execution_type !== 'test_login' && (
                  <div className="log-stats">
                    <div className="stat-item">
                      <span className="stat-label">총 문의</span>
                      <span className="stat-value">{log.statistics.total_inquiries || 0}</span>
                    </div>
                    <div className="stat-item success">
                      <span className="stat-label">답변 완료</span>
                      <span className="stat-value">{log.statistics.answered || 0}</span>
                    </div>
                    <div className="stat-item error">
                      <span className="stat-label">실패</span>
                      <span className="stat-value">{log.statistics.failed || 0}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">건너뜀</span>
                      <span className="stat-value">{log.statistics.skipped || 0}</span>
                    </div>
                  </div>
                )}

                {/* Duration */}
                {log.duration_seconds && (
                  <div className="log-duration">
                    <Clock size={14} />
                    <span>실행 시간: {formatDuration(log.duration_seconds)}</span>
                  </div>
                )}

                {/* Error Message */}
                {log.error_message && (
                  <div className="log-error">
                    <XCircle size={16} />
                    <span>{log.error_message}</span>
                  </div>
                )}

                {/* Expand Details Button */}
                {log.details && (
                  <button
                    className="expand-button"
                    onClick={() => toggleExpand(log.id)}
                  >
                    <Eye size={16} />
                    <span>{expandedLog === log.id ? '상세 정보 숨기기' : '상세 정보 보기'}</span>
                  </button>
                )}

                {/* Expanded Details */}
                <AnimatePresence>
                  {expandedLog === log.id && log.details && (
                    <motion.div
                      className="log-details"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <pre className="details-json">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default AutomationLogs
