import React, { useState, useEffect } from 'react'
import axios from 'axios'
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
  FileText,
  Settings,
  Save,
  RefreshCw,
  Sliders,
  MessageSquare,
  Bot,
  ChevronDown,
  ChevronUp,
  Eye
} from 'lucide-react'
import AutomationLogs from './AutomationLogs'
import '../styles/InquiryManagement.css'

const InquiryManagement = ({ responses = [], onApprove, onReject, loading, apiBaseUrl, showNotification }) => {
  const [activeSubTab, setActiveSubTab] = useState('responses') // 'responses', 'logs', 'settings'
  const [searchTerm, setSearchTerm] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [editingId, setEditingId] = useState(null)
  const [editedText, setEditedText] = useState('')
  const [expandedIds, setExpandedIds] = useState(new Set())

  // GPT Settings state
  const [gptSettings, setGptSettings] = useState({
    model: 'gpt-4',
    temperature: 0.7,
    max_tokens: 800,
    top_p: 0.9,
    frequency_penalty: 0.3,
    presence_penalty: 0.3,
    system_prompt: '',
    auto_approve_enabled: false,
    auto_approve_threshold: 90.0,
    response_style: 'formal'
  })
  const [availableModels, setAvailableModels] = useState([])
  const [responseStyles, setResponseStyles] = useState([])
  const [settingsLoading, setSettingsLoading] = useState(false)

  // Load GPT settings on mount
  useEffect(() => {
    if (apiBaseUrl) {
      loadGptSettings()
      loadAvailableModels()
      loadResponseStyles()
    }
  }, [apiBaseUrl])

  const loadGptSettings = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/gpt-settings`)
      setGptSettings(response.data)
    } catch (error) {
      console.error('Failed to load GPT settings:', error)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/gpt-settings/models`)
      setAvailableModels(response.data.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const loadResponseStyles = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/gpt-settings/response-styles`)
      setResponseStyles(response.data.styles || [])
    } catch (error) {
      console.error('Failed to load response styles:', error)
    }
  }

  const saveGptSettings = async () => {
    setSettingsLoading(true)
    try {
      await axios.put(`${apiBaseUrl}/gpt-settings`, gptSettings)
      showNotification?.('GPT 설정이 저장되었습니다', 'success')
    } catch (error) {
      console.error('Failed to save GPT settings:', error)
      showNotification?.('GPT 설정 저장 실패', 'error')
    } finally {
      setSettingsLoading(false)
    }
  }

  const resetGptSettings = async () => {
    if (!confirm('GPT 설정을 초기화하시겠습니까?')) return

    setSettingsLoading(true)
    try {
      const response = await axios.post(`${apiBaseUrl}/gpt-settings/reset`)
      setGptSettings(response.data.settings)
      showNotification?.('GPT 설정이 초기화되었습니다', 'success')
    } catch (error) {
      console.error('Failed to reset GPT settings:', error)
      showNotification?.('GPT 설정 초기화 실패', 'error')
    } finally {
      setSettingsLoading(false)
    }
  }

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

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const getRiskBadge = (level) => {
    const badges = {
      low: { color: 'green', icon: CheckCircle, text: '낮음' },
      medium: { color: 'orange', icon: AlertCircle, text: '보통' },
      high: { color: 'red', icon: AlertCircle, text: '높음' }
    }
    return badges[level] || badges.medium
  }

  const renderGptSettings = () => (
    <div className="gpt-settings-panel">
      <div className="settings-header">
        <h2>
          <Settings size={24} />
          GPT 응답 설정
        </h2>
        <div className="settings-actions">
          <button className="btn-secondary" onClick={resetGptSettings} disabled={settingsLoading}>
            <RefreshCw size={16} />
            <span>초기화</span>
          </button>
          <button className="btn-primary" onClick={saveGptSettings} disabled={settingsLoading}>
            {settingsLoading ? <RefreshCw size={16} className="spinning" /> : <Save size={16} />}
            <span>저장</span>
          </button>
        </div>
      </div>

      <div className="settings-grid">
        {/* Model Selection */}
        <div className="setting-group">
          <label>
            <Bot size={16} />
            GPT 모델
          </label>
          <select
            value={gptSettings.model}
            onChange={(e) => setGptSettings({ ...gptSettings, model: e.target.value })}
          >
            {availableModels.map(model => (
              <option key={model.id} value={model.id}>
                {model.name} - {model.description}
              </option>
            ))}
          </select>
        </div>

        {/* Response Style */}
        <div className="setting-group">
          <label>
            <MessageSquare size={16} />
            응답 스타일
          </label>
          <select
            value={gptSettings.response_style}
            onChange={(e) => setGptSettings({ ...gptSettings, response_style: e.target.value })}
          >
            {responseStyles.map(style => (
              <option key={style.id} value={style.id}>
                {style.name} - {style.description}
              </option>
            ))}
          </select>
        </div>

        {/* Temperature */}
        <div className="setting-group">
          <label>
            <Sliders size={16} />
            Temperature (창의성): {gptSettings.temperature}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={gptSettings.temperature}
            onChange={(e) => setGptSettings({ ...gptSettings, temperature: parseFloat(e.target.value) })}
          />
          <div className="range-labels">
            <span>정확함</span>
            <span>창의적</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div className="setting-group">
          <label>최대 토큰 수</label>
          <input
            type="number"
            min="100"
            max="4000"
            value={gptSettings.max_tokens}
            onChange={(e) => setGptSettings({ ...gptSettings, max_tokens: parseInt(e.target.value) })}
          />
        </div>

        {/* Top P */}
        <div className="setting-group">
          <label>Top P: {gptSettings.top_p}</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={gptSettings.top_p}
            onChange={(e) => setGptSettings({ ...gptSettings, top_p: parseFloat(e.target.value) })}
          />
        </div>

        {/* Frequency Penalty */}
        <div className="setting-group">
          <label>반복 방지 (Frequency Penalty): {gptSettings.frequency_penalty}</label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={gptSettings.frequency_penalty}
            onChange={(e) => setGptSettings({ ...gptSettings, frequency_penalty: parseFloat(e.target.value) })}
          />
        </div>

        {/* Presence Penalty */}
        <div className="setting-group">
          <label>새 주제 선호 (Presence Penalty): {gptSettings.presence_penalty}</label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={gptSettings.presence_penalty}
            onChange={(e) => setGptSettings({ ...gptSettings, presence_penalty: parseFloat(e.target.value) })}
          />
        </div>

        {/* Auto Approve */}
        <div className="setting-group full-width">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={gptSettings.auto_approve_enabled}
              onChange={(e) => setGptSettings({ ...gptSettings, auto_approve_enabled: e.target.checked })}
            />
            <span>자동 승인 활성화 (신뢰도 {gptSettings.auto_approve_threshold}% 이상)</span>
          </label>
          {gptSettings.auto_approve_enabled && (
            <div className="threshold-slider">
              <input
                type="range"
                min="70"
                max="100"
                step="5"
                value={gptSettings.auto_approve_threshold}
                onChange={(e) => setGptSettings({ ...gptSettings, auto_approve_threshold: parseFloat(e.target.value) })}
              />
              <span>{gptSettings.auto_approve_threshold}%</span>
            </div>
          )}
        </div>

        {/* System Prompt */}
        <div className="setting-group full-width">
          <label>시스템 프롬프트 (GPT 지시사항)</label>
          <textarea
            value={gptSettings.system_prompt || ''}
            onChange={(e) => setGptSettings({ ...gptSettings, system_prompt: e.target.value })}
            placeholder="GPT에게 전달할 시스템 프롬프트를 입력하세요..."
            rows={10}
          />
        </div>
      </div>
    </div>
  )

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
        <button
          className={`sub-tab ${activeSubTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('settings')}
        >
          <Settings size={18} />
          <span>GPT 설정</span>
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
                  const isExpanded = expandedIds.has(response.id)

                  return (
                    <motion.div
                      key={response.id}
                      className={`response-card ${isExpanded ? 'expanded' : ''}`}
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
                            {response.status === 'pending_approval' ? '승인 대기' :
                             response.status === 'approved' ? '승인됨' :
                             response.status === 'rejected' ? '거부됨' : response.status}
                          </span>
                          <span className={`risk-badge risk-${risk.color}`}>
                            <RiskIcon size={14} />
                            위험도: {risk.text}
                          </span>
                          <span className="confidence-badge">
                            🎯 신뢰도: {response.confidence_score?.toFixed(1) || 'N/A'}%
                          </span>
                        </div>
                        <div className="header-right">
                          <span className="response-id">#{response.inquiry_id}</span>
                          <button
                            className="expand-btn"
                            onClick={() => toggleExpand(response.id)}
                          >
                            {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                          </button>
                        </div>
                      </div>

                      {/* Inquiry Summary (Always visible) */}
                      <div className="inquiry-summary" onClick={() => toggleExpand(response.id)}>
                        <div className="summary-label">
                          <MessageSquare size={16} />
                          <span>고객 문의</span>
                        </div>
                        <p className="summary-text">
                          {response.inquiry?.inquiry_text?.slice(0, 100) || '문의 내용 없음'}
                          {response.inquiry?.inquiry_text?.length > 100 && '...'}
                        </p>
                      </div>

                      {/* Expanded Content */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            className="expanded-content"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            {/* Full Inquiry */}
                            {response.inquiry && (
                              <div className="inquiry-section">
                                <h4 className="section-title">
                                  <span>📨</span>
                                  <span>고객 문의 전문</span>
                                </h4>
                                <div className="inquiry-meta">
                                  {response.inquiry.customer_name && (
                                    <span>고객: {response.inquiry.customer_name}</span>
                                  )}
                                  {response.inquiry.product_name && (
                                    <span>상품: {response.inquiry.product_name}</span>
                                  )}
                                  {response.inquiry.order_number && (
                                    <span>주문번호: {response.inquiry.order_number}</span>
                                  )}
                                </div>
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
                        )}
                      </AnimatePresence>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>
          )}
        </>
      ) : activeSubTab === 'logs' ? (
        <AutomationLogs apiBaseUrl={apiBaseUrl} />
      ) : (
        renderGptSettings()
      )}
    </div>
  )
}

export default InquiryManagement
