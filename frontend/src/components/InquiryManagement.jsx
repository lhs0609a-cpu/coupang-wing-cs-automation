import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  Edit,
  Check,
  X,
  Send,
  AlertCircle,
  CheckCircle,
  Clock,
  List,
  FileText
} from 'lucide-react'
import AutomationLogs from './AutomationLogs'
import '../styles/InquiryManagement.css'

const InquiryManagement = ({ responses = [], onApprove, onReject, loading, apiBaseUrl }) => {
  const [activeSubTab, setActiveSubTab] = useState('responses') // 'responses' or 'logs'
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [editingId, setEditingId] = useState(null)
  const [editedText, setEditedText] = useState('')

  const filteredResponses = (responses || []).filter(response => {
    const matchesSearch = response.inquiry?.inquiry_text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          response.response_text?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === 'all' || response.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const startEdit = (response) => {
    setEditingId(response.id)
    setEditedText(response.response_text)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditedText('')
  }

  const handleApprove = (responseId) => {
    onApprove(responseId, editingId === responseId ? editedText : null)
    if (editingId === responseId) {
      cancelEdit()
    }
  }

  const getRiskBadge = (level) => {
    const badges = {
      low: { color: 'green', icon: CheckCircle, text: '낮음' },
      medium: { color: 'orange', icon: AlertCircle, text: '보통' },
      high: { color: 'red', icon: AlertCircle, text: '높음' }
    }
    return badges[level] || badges.medium
  }

  return (
    <div className="inquiry-management">
      <div className="inquiry-header">
        <div>
          <h1 className="inquiry-title">문의 관리</h1>
          <p className="inquiry-subtitle">AI가 생성한 답변을 검토하고 자동화 기록을 확인하세요</p>
        </div>
        {activeSubTab === 'responses' && (
          <div className="inquiry-count">
            <span className="count-badge">{filteredResponses.length}</span>
            <span>개의 문의</span>
          </div>
        )}
      </div>

      {/* Sub Tabs */}
      <div className="sub-tabs">
        <button
          className={`sub-tab ${activeSubTab === 'responses' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('responses')}
        >
          <List size={18} />
          <span>답변 검토</span>
        </button>
        <button
          className={`sub-tab ${activeSubTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('logs')}
        >
          <FileText size={18} />
          <span>자동화 기록</span>
        </button>
      </div>

      {/* Show content based on active sub tab */}
      {activeSubTab === 'responses' ? (
        <>
          {/* Search and Filter */}
          <div className="inquiry-controls">
        <div className="search-box">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            placeholder="문의 내용 또는 답변 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <Filter size={20} className="filter-icon" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="filter-select"
          >
            <option value="all">전체 상태</option>
            <option value="pending_approval">승인 대기</option>
            <option value="approved">승인됨</option>
            <option value="rejected">거부됨</option>
          </select>
        </div>
      </div>

      {/* Response List */}
      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>불러오는 중...</p>
        </div>
      ) : filteredResponses.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>표시할 문의가 없습니다</h3>
          <p>검색 조건을 변경하거나 새로운 문의를 수집하세요</p>
        </div>
      ) : (
        <div className="response-list">
          <AnimatePresence mode="popLayout">
            {filteredResponses.map((response, index) => {
              const risk = getRiskBadge(response.risk_level)
              const RiskIcon = risk.icon

              return (
                <motion.div
                  key={response.id}
                  className="response-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: index * 0.05 }}
                  layout
                >
                  {/* Card Header */}
                  <div className="response-card-header">
                    <div className="response-badges">
                      <span className={`status-badge status-${response.status}`}>
                        <Clock size={14} />
                        {response.status === 'pending_approval' ? '승인 대기' : response.status}
                      </span>
                      <span className={`risk-badge risk-${risk.color}`}>
                        <RiskIcon size={14} />
                        위험도: {risk.text}
                      </span>
                      <span className="confidence-badge">
                        🎯 신뢰도: {response.confidence_score?.toFixed(1) || 'N/A'}%
                      </span>
                    </div>
                    <span className="response-id">#{response.inquiry_id}</span>
                  </div>

                  {/* Inquiry */}
                  {response.inquiry && (
                    <div className="inquiry-section">
                      <h4 className="section-title">
                        <span>📨</span>
                        <span>고객 문의</span>
                      </h4>
                      <div className="inquiry-text">
                        {response.inquiry.inquiry_text || '문의 내용 없음'}
                      </div>
                    </div>
                  )}

                  {/* Response */}
                  <div className="response-section">
                    <h4 className="section-title">
                      <span>🤖</span>
                      <span>AI 생성 답변</span>
                    </h4>
                    {editingId === response.id ? (
                      <textarea
                        value={editedText}
                        onChange={(e) => setEditedText(e.target.value)}
                        className="response-textarea"
                        rows={8}
                      />
                    ) : (
                      <div className="response-text">
                        {response.response_text}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="response-actions">
                    {editingId === response.id ? (
                      <>
                        <button
                          className="action-btn approve"
                          onClick={() => handleApprove(response.id)}
                        >
                          <Check size={18} />
                          <span>수정 후 승인 & 제출</span>
                        </button>
                        <button
                          className="action-btn cancel"
                          onClick={cancelEdit}
                        >
                          <X size={18} />
                          <span>취소</span>
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className="action-btn approve"
                          onClick={() => handleApprove(response.id)}
                        >
                          <Send size={18} />
                          <span>승인 & 자동 제출</span>
                        </button>
                        <button
                          className="action-btn edit"
                          onClick={() => startEdit(response)}
                        >
                          <Edit size={18} />
                          <span>수정</span>
                        </button>
                        <button
                          className="action-btn reject"
                          onClick={() => onReject(response.id)}
                        >
                          <X size={18} />
                          <span>거부</span>
                        </button>
                      </>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      )}
        </>
      ) : (
        <AutomationLogs apiBaseUrl={apiBaseUrl} />
      )}
    </div>
  )
}

export default InquiryManagement
