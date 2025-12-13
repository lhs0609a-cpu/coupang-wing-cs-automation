import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Square,
  Plus,
  Trash2,
  Edit,
  Star,
  Image as ImageIcon,
  Upload,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  X,
  Shuffle,
  MessageSquare,
  TrendingUp,
  Award,
  Clock
} from 'lucide-react'
import '../styles/NaverReviewManagement.css'

const NaverReviewManagement = ({ apiBaseUrl, showNotification }) => {
  // State
  const [loading, setLoading] = useState(false)
  const [botStatus, setBotStatus] = useState({
    is_running: false,
    current: 0,
    total: 0,
    status: '대기 중'
  })
  const [templates, setTemplates] = useState([])
  const [images, setImages] = useState([])
  const [naverAccounts, setNaverAccounts] = useState([])
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [todayStats, setTodayStats] = useState(null)

  // Form state
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [templateForm, setTemplateForm] = useState({
    star_rating: 5,
    review_text: '',
    image_paths: []
  })

  // Automation settings
  const [selectedAccountId, setSelectedAccountId] = useState('')
  const [loginMethod, setLoginMethod] = useState('manual')

  const logContainerRef = useRef(null)
  const statusIntervalRef = useRef(null)

  // Load data on mount
  useEffect(() => {
    if (apiBaseUrl) {
      loadAllData()
    }
  }, [apiBaseUrl])

  // Poll bot status when running
  useEffect(() => {
    if (botStatus.is_running) {
      statusIntervalRef.current = setInterval(() => {
        loadBotStatus()
        loadRealtimeLogs()
      }, 2000)
    } else {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
      }
    }

    return () => {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
      }
    }
  }, [botStatus.is_running])

  // Auto scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs])

  const loadAllData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadBotStatus(),
        loadTemplates(),
        loadImages(),
        loadNaverAccounts(),
        loadStats(),
        loadTodayStats(),
        loadRealtimeLogs()
      ])
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadBotStatus = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/status`)
      setBotStatus(response.data)
    } catch (error) {
      console.error('Failed to load bot status:', error)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/templates`)
      setTemplates(response.data)
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const loadImages = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/images`)
      setImages(response.data)
    } catch (error) {
      console.error('Failed to load images:', error)
    }
  }

  const loadNaverAccounts = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-accounts`)
      // API returns {success, count, data: [...]}
      const accounts = response.data.data || response.data || []
      setNaverAccounts(accounts)
      if (accounts.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accounts[0].id)
      }
    } catch (error) {
      console.error('Failed to load naver accounts:', error)
    }
  }

  const loadStats = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/stats?days=7`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const loadTodayStats = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/stats/today`)
      setTodayStats(response.data)
    } catch (error) {
      console.error('Failed to load today stats:', error)
    }
  }

  const loadRealtimeLogs = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/logs/realtime?limit=50`)
      setLogs(response.data)
    } catch (error) {
      console.error('Failed to load logs:', error)
    }
  }

  // Automation controls
  const startAutomation = async () => {
    if (!selectedAccountId) {
      showNotification?.('네이버 계정을 선택해주세요', 'error')
      return
    }

    if (templates.length === 0) {
      showNotification?.('리뷰 템플릿을 먼저 추가해주세요', 'error')
      return
    }

    try {
      const response = await axios.post(`${apiBaseUrl}/naver-review/start`, {
        naver_account_id: parseInt(selectedAccountId),
        login_method: loginMethod,
        headless: false
      })

      if (response.data.success) {
        showNotification?.('자동화가 시작되었습니다', 'success')
        setBotStatus(prev => ({ ...prev, is_running: true }))
      }
    } catch (error) {
      console.error('Failed to start automation:', error)
      showNotification?.(error.response?.data?.detail || '자동화 시작 실패', 'error')
    }
  }

  const stopAutomation = async () => {
    try {
      await axios.post(`${apiBaseUrl}/naver-review/stop`)
      showNotification?.('자동화가 중지되었습니다', 'warning')
      setBotStatus(prev => ({ ...prev, is_running: false, status: '중지됨' }))
    } catch (error) {
      console.error('Failed to stop automation:', error)
      showNotification?.('자동화 중지 실패', 'error')
    }
  }

  // Template management
  const handleTemplateSubmit = async (e) => {
    e.preventDefault()

    try {
      if (editingTemplate) {
        await axios.put(`${apiBaseUrl}/naver-review/templates/${editingTemplate.id}`, templateForm)
        showNotification?.('템플릿이 수정되었습니다', 'success')
      } else {
        await axios.post(`${apiBaseUrl}/naver-review/templates`, templateForm)
        showNotification?.('템플릿이 추가되었습니다', 'success')
      }

      resetTemplateForm()
      loadTemplates()
    } catch (error) {
      console.error('Failed to save template:', error)
      showNotification?.('템플릿 저장 실패', 'error')
    }
  }

  const deleteTemplate = async (templateId) => {
    if (!confirm('이 템플릿을 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/naver-review/templates/${templateId}`)
      showNotification?.('템플릿이 삭제되었습니다', 'success')
      loadTemplates()
    } catch (error) {
      console.error('Failed to delete template:', error)
      showNotification?.('템플릿 삭제 실패', 'error')
    }
  }

  const editTemplate = (template) => {
    setEditingTemplate(template)
    setTemplateForm({
      star_rating: template.star_rating,
      review_text: template.review_text,
      image_paths: template.image_paths || []
    })
    setShowTemplateForm(true)
  }

  const resetTemplateForm = () => {
    setShowTemplateForm(false)
    setEditingTemplate(null)
    setTemplateForm({
      star_rating: 5,
      review_text: '',
      image_paths: []
    })
  }

  // Image management
  const handleImageUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)

      try {
        await axios.post(`${apiBaseUrl}/naver-review/images`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } catch (error) {
        console.error('Failed to upload image:', error)
        showNotification?.(`이미지 업로드 실패: ${file.name}`, 'error')
      }
    }

    showNotification?.('이미지가 업로드되었습니다', 'success')
    loadImages()
  }

  const deleteImage = async (imageId) => {
    if (!confirm('이 이미지를 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/naver-review/images/${imageId}`)
      showNotification?.('이미지가 삭제되었습니다', 'success')
      loadImages()
    } catch (error) {
      console.error('Failed to delete image:', error)
      showNotification?.('이미지 삭제 실패', 'error')
    }
  }

  const applyRandomImages = async () => {
    if (images.length === 0) {
      showNotification?.('업로드된 이미지가 없습니다', 'error')
      return
    }

    try {
      const response = await axios.post(`${apiBaseUrl}/naver-review/images/apply-random`, {
        min_images: 1,
        max_images: Math.min(3, images.length)
      })

      showNotification?.(response.data.message, 'success')
      loadTemplates()
    } catch (error) {
      console.error('Failed to apply random images:', error)
      showNotification?.('이미지 배분 실패', 'error')
    }
  }

  const clearLogs = async () => {
    try {
      await axios.delete(`${apiBaseUrl}/naver-review/logs/realtime`)
      setLogs([])
      showNotification?.('로그가 초기화되었습니다', 'success')
    } catch (error) {
      console.error('Failed to clear logs:', error)
    }
  }

  const getLogLevelClass = (level) => {
    switch (level) {
      case 'success': return 'log-success'
      case 'error': return 'log-error'
      case 'warning': return 'log-warning'
      default: return 'log-info'
    }
  }

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        size={16}
        className={i < rating ? 'star-filled' : 'star-empty'}
      />
    ))
  }

  return (
    <div className="naver-review-management">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>네이버 리뷰 자동화</h1>
          <p>네이버 쇼핑 리뷰를 자동으로 작성합니다</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary" onClick={loadAllData} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'spinning' : ''} />
            <span>새로고침</span>
          </button>
          {botStatus.is_running ? (
            <button className="btn-danger" onClick={stopAutomation}>
              <Square size={18} />
              <span>중지</span>
            </button>
          ) : (
            <button className="btn-primary" onClick={startAutomation}>
              <Play size={18} />
              <span>자동화 시작</span>
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">
            <MessageSquare size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">오늘 작성</span>
            <span className="stat-value">{todayStats?.success_count || 0}건</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">
            <Award size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">총 포인트</span>
            <span className="stat-value">{(todayStats?.total_points || 0).toLocaleString()}P</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">성공률</span>
            <span className="stat-value">{todayStats?.success_rate || 0}%</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">
            <Clock size={24} />
          </div>
          <div className="stat-content">
            <span className="stat-label">상태</span>
            <span className={`stat-value ${botStatus.is_running ? 'running' : ''}`}>
              {botStatus.status}
            </span>
          </div>
        </div>
      </div>

      {/* Settings Row */}
      <div className="settings-row">
        <div className="setting-item">
          <label>네이버 계정</label>
          <select
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            disabled={botStatus.is_running}
          >
            <option value="">계정 선택</option>
            {naverAccounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.naver_id})
              </option>
            ))}
          </select>
        </div>

        <div className="setting-item">
          <label>로그인 방식</label>
          <select
            value={loginMethod}
            onChange={(e) => setLoginMethod(e.target.value)}
            disabled={botStatus.is_running}
          >
            <option value="manual">수동 로그인 (권장)</option>
            <option value="auto">자동 로그인</option>
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Templates Section */}
        <div className="section templates-section">
          <div className="section-header">
            <h2>리뷰 템플릿</h2>
            <button className="btn-primary-small" onClick={() => setShowTemplateForm(true)}>
              <Plus size={16} />
              <span>템플릿 추가</span>
            </button>
          </div>

          <div className="templates-list">
            {templates.length === 0 ? (
              <div className="empty-state">
                <MessageSquare size={48} />
                <p>등록된 템플릿이 없습니다</p>
                <button className="btn-primary-small" onClick={() => setShowTemplateForm(true)}>
                  템플릿 추가하기
                </button>
              </div>
            ) : (
              templates.map(template => (
                <div key={template.id} className="template-card">
                  <div className="template-header">
                    <div className="template-rating">
                      {renderStars(template.star_rating)}
                    </div>
                    <div className="template-actions">
                      <button className="btn-icon" onClick={() => editTemplate(template)}>
                        <Edit size={16} />
                      </button>
                      <button className="btn-icon danger" onClick={() => deleteTemplate(template.id)}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                  <p className="template-text">{template.review_text}</p>
                  {template.image_paths && template.image_paths.length > 0 && (
                    <div className="template-images">
                      <ImageIcon size={14} />
                      <span>{template.image_paths.length}개 이미지</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Images Section */}
        <div className="section images-section">
          <div className="section-header">
            <h2>이미지 관리</h2>
            <div className="section-actions">
              <button
                className="btn-secondary-small"
                onClick={applyRandomImages}
                disabled={images.length === 0}
              >
                <Shuffle size={16} />
                <span>랜덤 배분</span>
              </button>
              <label className="btn-primary-small upload-btn">
                <Upload size={16} />
                <span>업로드</span>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleImageUpload}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          </div>

          <div className="images-grid">
            {images.length === 0 ? (
              <div className="empty-state">
                <ImageIcon size={48} />
                <p>업로드된 이미지가 없습니다</p>
              </div>
            ) : (
              images.map(image => (
                <div key={image.id} className="image-card">
                  <img
                    src={`${apiBaseUrl}/naver-review/images/file/${image.filename}`}
                    alt={image.original_filename}
                  />
                  <button
                    className="image-delete"
                    onClick={() => deleteImage(image.id)}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Logs Section */}
        <div className="section logs-section">
          <div className="section-header">
            <h2>실시간 로그</h2>
            <button className="btn-secondary-small" onClick={clearLogs}>
              <Trash2 size={16} />
              <span>로그 삭제</span>
            </button>
          </div>

          <div className="logs-container" ref={logContainerRef}>
            {logs.length === 0 ? (
              <div className="empty-logs">
                <p>로그가 없습니다</p>
              </div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className={`log-item ${getLogLevelClass(log.level)}`}>
                  <span className="log-time">[{log.time}]</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Template Form Modal */}
      <AnimatePresence>
        {showTemplateForm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetTemplateForm}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>{editingTemplate ? '템플릿 수정' : '템플릿 추가'}</h2>
                <button className="btn-icon" onClick={resetTemplateForm}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleTemplateSubmit} className="template-form">
                <div className="form-group">
                  <label>별점</label>
                  <div className="star-rating-input">
                    {[1, 2, 3, 4, 5].map(rating => (
                      <button
                        key={rating}
                        type="button"
                        className={`star-btn ${templateForm.star_rating >= rating ? 'active' : ''}`}
                        onClick={() => setTemplateForm({ ...templateForm, star_rating: rating })}
                      >
                        <Star size={24} />
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label>리뷰 내용 (최소 10자)</label>
                  <textarea
                    value={templateForm.review_text}
                    onChange={(e) => setTemplateForm({ ...templateForm, review_text: e.target.value })}
                    placeholder="리뷰 내용을 입력하세요..."
                    rows={4}
                    required
                    minLength={10}
                  />
                  <span className="char-count">{templateForm.review_text.length}자</span>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={resetTemplateForm}>
                    취소
                  </button>
                  <button type="submit" className="btn-primary">
                    <CheckCircle size={18} />
                    <span>{editingTemplate ? '수정' : '추가'}</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default NaverReviewManagement
