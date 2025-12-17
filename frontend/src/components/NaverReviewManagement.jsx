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
  Clock,
  LogIn,
  LogOut,
  User,
  Sparkles,
  RotateCcw,
  Monitor,
  Cloud,
  Wifi,
  WifiOff
} from 'lucide-react'
import '../styles/NaverReviewManagement.css'

const NaverReviewManagement = ({ apiBaseUrl: cloudApiBaseUrl, showNotification }) => {
  // 로컬 백엔드 설정 (브라우저 자동화용)
  const LOCAL_BACKEND_URL = 'http://localhost:8000/api'
  const [useLocalBackend, setUseLocalBackend] = useState(() => {
    return localStorage.getItem('naver_review_use_local') === 'true'
  })
  const [localBackendConnected, setLocalBackendConnected] = useState(false)
  const [checkingLocalBackend, setCheckingLocalBackend] = useState(false)

  // 실제 사용할 API URL
  const apiBaseUrl = useLocalBackend ? LOCAL_BACKEND_URL : cloudApiBaseUrl

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

  // Login state
  const [loginStatus, setLoginStatus] = useState({
    is_logged_in: false,
    username: null
  })
  const [loginLoading, setLoginLoading] = useState(false)
  const [showLoginForm, setShowLoginForm] = useState(false)
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  })

  // Auto-generate state
  const [showAutoGenerateForm, setShowAutoGenerateForm] = useState(false)
  const [autoGenerateForm, setAutoGenerateForm] = useState({
    count: 5,
    category: 'general',
    min_rating: 4,
    max_rating: 5
  })
  const [categories, setCategories] = useState([])

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
  const dropZoneRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  // 로컬 백엔드 연결 체크
  const checkLocalBackend = async () => {
    setCheckingLocalBackend(true)
    try {
      const response = await axios.get(`${LOCAL_BACKEND_URL.replace('/api', '')}/health`, {
        timeout: 3000
      })
      if (response.data && response.data.status) {
        setLocalBackendConnected(true)
        showNotification?.('로컬 백엔드 연결 성공!', 'success')
        return true
      }
    } catch (error) {
      setLocalBackendConnected(false)
      console.log('로컬 백엔드 연결 실패:', error.message)
    } finally {
      setCheckingLocalBackend(false)
    }
    return false
  }

  // 로컬 백엔드 토글
  const toggleLocalBackend = async (enabled) => {
    if (enabled) {
      const connected = await checkLocalBackend()
      if (!connected) {
        showNotification?.('로컬 백엔드에 연결할 수 없습니다. 먼저 로컬 서버를 실행해주세요.', 'error')
        return
      }
    }
    setUseLocalBackend(enabled)
    localStorage.setItem('naver_review_use_local', enabled.toString())
    if (enabled) {
      showNotification?.('로컬 모드로 전환되었습니다. 브라우저 창이 표시됩니다.', 'success')
    } else {
      showNotification?.('클라우드 모드로 전환되었습니다.', 'info')
    }
  }

  // 로컬 백엔드 상태 체크 (마운트 시)
  useEffect(() => {
    if (useLocalBackend) {
      checkLocalBackend()
    }
  }, [])

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

  // 클립보드 붙여넣기 이벤트 핸들러
  useEffect(() => {
    const handlePaste = async (e) => {
      const items = e.clipboardData?.items
      if (!items) return

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          if (file) {
            await uploadSingleImage(file)
          }
        }
      }
    }

    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [apiBaseUrl])

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
        loadRealtimeLogs(),
        loadLoginStatus(),
        loadCategories()
      ])
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadLoginStatus = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/login-status`)
      setLoginStatus(response.data)
    } catch (error) {
      console.error('Failed to load login status:', error)
      setLoginStatus({ is_logged_in: false, username: null })
    }
  }

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/naver-review/templates/categories`)
      setCategories(response.data.categories || [])
    } catch (error) {
      console.error('Failed to load categories:', error)
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
    // 로컬 모드 체크
    if (!useLocalBackend) {
      showNotification?.('브라우저 자동화를 실행하려면 로컬 모드를 활성화해주세요', 'error')
      return
    }

    if (!localBackendConnected) {
      showNotification?.('로컬 백엔드에 연결되어 있지 않습니다. 서버를 실행해주세요.', 'error')
      return
    }

    if (!selectedAccountId) {
      showNotification?.('네이버 계정을 선택해주세요', 'error')
      return
    }

    if (templates.length === 0) {
      showNotification?.('리뷰 템플릿을 먼저 추가해주세요', 'error')
      return
    }

    try {
      // 로컬에서는 headless: false로 브라우저 창 표시
      const response = await axios.post(`${apiBaseUrl}/naver-review/start`, {
        naver_account_id: parseInt(selectedAccountId),
        login_method: loginMethod,
        headless: false  // 브라우저 창 표시
      })

      if (response.data.success) {
        showNotification?.('자동화가 시작되었습니다. 브라우저 창을 확인하세요!', 'success')
        setBotStatus(prev => ({ ...prev, is_running: true }))
        // 로그 폴링 시작
        loadLogs()
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

  // Image management - 단일 이미지 업로드 함수
  const uploadSingleImage = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      showNotification?.('이미지 파일만 업로드 가능합니다', 'error')
      return false
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      await axios.post(`${apiBaseUrl}/naver-review/images`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      showNotification?.(`이미지 업로드 완료: ${file.name}`, 'success')
      loadImages()
      return true
    } catch (error) {
      console.error('Failed to upload image:', error)
      showNotification?.(`이미지 업로드 실패: ${file.name}`, 'error')
      return false
    }
  }

  // 파일 선택으로 이미지 업로드
  const handleImageUpload = async (e) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    for (const file of files) {
      await uploadSingleImage(file)
    }
  }

  // 드래그 앤 드롭 핸들러
  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    // 자식 요소로 이동할 때는 무시
    if (e.currentTarget.contains(e.relatedTarget)) return
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer?.files
    if (!files || files.length === 0) return

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        await uploadSingleImage(file)
      }
    }
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

  // 이미지 순환 배분
  const applyImageRotation = async () => {
    if (images.length === 0) {
      showNotification?.('업로드된 이미지가 없습니다', 'error')
      return
    }

    try {
      const response = await axios.post(`${apiBaseUrl}/naver-review/images/apply-rotation`, {
        images_per_template: 1
      })

      showNotification?.(response.data.message, 'success')
      loadTemplates()
    } catch (error) {
      console.error('Failed to apply image rotation:', error)
      showNotification?.('이미지 순환 배분 실패', 'error')
    }
  }

  // 네이버 로그인
  const handleLogin = async (e) => {
    e.preventDefault()
    if (!loginForm.username || !loginForm.password) {
      showNotification?.('아이디와 비밀번호를 입력해주세요', 'error')
      return
    }

    setLoginLoading(true)
    try {
      const response = await axios.post(`${apiBaseUrl}/naver-review/login`, {
        username: loginForm.username,
        password: loginForm.password
      })

      if (response.data.success) {
        showNotification?.('로그인 성공!', 'success')
        setLoginStatus({
          is_logged_in: true,
          username: loginForm.username
        })
        setShowLoginForm(false)
        setLoginForm({ username: '', password: '' })
      } else {
        showNotification?.(response.data.message || '로그인 실패', 'error')
      }
    } catch (error) {
      console.error('Login failed:', error)
      showNotification?.(error.response?.data?.detail || '로그인 실패', 'error')
    } finally {
      setLoginLoading(false)
    }
  }

  // 네이버 로그아웃
  const handleLogout = async () => {
    try {
      await axios.post(`${apiBaseUrl}/naver-review/logout`)
      showNotification?.('로그아웃 완료', 'success')
      setLoginStatus({ is_logged_in: false, username: null })
    } catch (error) {
      console.error('Logout failed:', error)
      showNotification?.('로그아웃 실패', 'error')
    }
  }

  // 템플릿 자동 생성
  const handleAutoGenerate = async (e) => {
    e.preventDefault()
    try {
      const response = await axios.post(`${apiBaseUrl}/naver-review/templates/auto-generate`, {
        count: autoGenerateForm.count,
        category: autoGenerateForm.category,
        min_rating: autoGenerateForm.min_rating,
        max_rating: autoGenerateForm.max_rating
      })

      if (response.data.success) {
        showNotification?.(response.data.message, 'success')
        loadTemplates()
        setShowAutoGenerateForm(false)
      } else {
        showNotification?.(response.data.message, 'warning')
      }
    } catch (error) {
      console.error('Auto-generate failed:', error)
      showNotification?.('템플릿 자동 생성 실패', 'error')
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

      {/* Login Section */}
      <div className="login-section">
        <div className="login-status-card">
          <div className="login-info">
            <User size={20} />
            {loginStatus.is_logged_in ? (
              <span className="logged-in">
                <CheckCircle size={16} className="status-icon success" />
                {loginStatus.username} 로그인됨
              </span>
            ) : (
              <span className="logged-out">
                <AlertCircle size={16} className="status-icon warning" />
                로그인 필요
              </span>
            )}
          </div>
          <div className="login-actions">
            {loginStatus.is_logged_in ? (
              <button className="btn-secondary-small" onClick={handleLogout}>
                <LogOut size={16} />
                <span>로그아웃</span>
              </button>
            ) : (
              <button className="btn-primary-small" onClick={() => setShowLoginForm(true)}>
                <LogIn size={16} />
                <span>로그인</span>
              </button>
            )}
          </div>
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

      {/* 실행 모드 설정 */}
      <div className="mode-toggle-section">
        <div className="mode-toggle-card">
          <div className="mode-info">
            {useLocalBackend ? (
              <>
                <Monitor size={24} className="mode-icon local" />
                <div className="mode-details">
                  <span className="mode-title">로컬 모드</span>
                  <span className="mode-desc">브라우저 창이 열리며 실행됩니다</span>
                </div>
              </>
            ) : (
              <>
                <Cloud size={24} className="mode-icon cloud" />
                <div className="mode-details">
                  <span className="mode-title">클라우드 모드</span>
                  <span className="mode-desc">서버에서 실행 (브라우저 자동화 불가)</span>
                </div>
              </>
            )}
          </div>
          <div className="mode-status">
            {useLocalBackend && (
              <span className={`connection-status ${localBackendConnected ? 'connected' : 'disconnected'}`}>
                {checkingLocalBackend ? (
                  <><RefreshCw size={14} className="spinning" /> 연결 확인 중...</>
                ) : localBackendConnected ? (
                  <><Wifi size={14} /> 연결됨</>
                ) : (
                  <><WifiOff size={14} /> 연결 안됨</>
                )}
              </span>
            )}
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={useLocalBackend}
                onChange={(e) => toggleLocalBackend(e.target.checked)}
                disabled={botStatus.is_running || checkingLocalBackend}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>
        {!useLocalBackend && (
          <div className="mode-warning">
            <AlertCircle size={16} />
            <span>브라우저 자동화를 사용하려면 <strong>로컬 모드</strong>를 활성화하세요.
              로컬 서버 실행: <code>cd backend && python -m uvicorn app.main:app --reload</code>
            </span>
          </div>
        )}
        {useLocalBackend && !localBackendConnected && (
          <div className="mode-warning error">
            <AlertCircle size={16} />
            <span>로컬 백엔드에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.</span>
            <button className="btn-retry" onClick={checkLocalBackend} disabled={checkingLocalBackend}>
              <RefreshCw size={14} /> 재연결
            </button>
          </div>
        )}
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
            <div className="section-actions">
              <button className="btn-secondary-small" onClick={() => setShowAutoGenerateForm(true)}>
                <Sparkles size={16} />
                <span>자동 생성</span>
              </button>
              <button className="btn-primary-small" onClick={() => setShowTemplateForm(true)}>
                <Plus size={16} />
                <span>템플릿 추가</span>
              </button>
            </div>
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
        <div
          className={`section images-section ${isDragging ? 'dragging' : ''}`}
          ref={dropZoneRef}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <div className="section-header">
            <h2>이미지 관리</h2>
            <div className="section-actions">
              <button
                className="btn-secondary-small"
                onClick={applyImageRotation}
                disabled={images.length === 0}
                title="이미지를 템플릿에 순환 배분"
              >
                <RotateCcw size={16} />
                <span>순환 배분</span>
              </button>
              <button
                className="btn-secondary-small"
                onClick={applyRandomImages}
                disabled={images.length === 0}
                title="이미지를 템플릿에 랜덤 배분"
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

          {/* 드래그 앤 드롭 / 붙여넣기 안내 영역 */}
          <div className={`drop-zone ${isDragging ? 'active' : ''}`}>
            {isDragging ? (
              <div className="drop-zone-content">
                <Upload size={48} />
                <p>여기에 이미지를 놓으세요</p>
              </div>
            ) : (
              <div className="drop-zone-content">
                <ImageIcon size={32} />
                <p>이미지를 드래그하거나 <strong>Ctrl+V</strong>로 붙여넣기</p>
                <span className="drop-zone-hint">PNG, JPG, GIF 지원 (최대 16MB)</span>
              </div>
            )}
          </div>

          <div className="images-grid">
            {images.length === 0 ? (
              <div className="empty-state small">
                <p>저장된 이미지가 없습니다</p>
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

          {images.length > 0 && (
            <div className="images-info">
              <span>{images.length}개 이미지 저장됨</span>
              <span className="info-hint">리뷰 작성 시 랜덤으로 사용됩니다</span>
            </div>
          )}
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

      {/* Login Modal */}
      <AnimatePresence>
        {showLoginForm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowLoginForm(false)}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>네이버 로그인</h2>
                <button className="btn-icon" onClick={() => setShowLoginForm(false)}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleLogin} className="login-form">
                <div className="form-group">
                  <label>네이버 아이디</label>
                  <input
                    type="text"
                    value={loginForm.username}
                    onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                    placeholder="네이버 아이디를 입력하세요"
                    required
                    autoComplete="username"
                  />
                </div>

                <div className="form-group">
                  <label>비밀번호</label>
                  <input
                    type="password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    placeholder="비밀번호를 입력하세요"
                    required
                    autoComplete="current-password"
                  />
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowLoginForm(false)}>
                    취소
                  </button>
                  <button type="submit" className="btn-primary" disabled={loginLoading}>
                    {loginLoading ? (
                      <>
                        <RefreshCw size={18} className="spinning" />
                        <span>로그인 중...</span>
                      </>
                    ) : (
                      <>
                        <LogIn size={18} />
                        <span>로그인</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Auto Generate Modal */}
      <AnimatePresence>
        {showAutoGenerateForm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAutoGenerateForm(false)}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2>리뷰 템플릿 자동 생성</h2>
                <button className="btn-icon" onClick={() => setShowAutoGenerateForm(false)}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleAutoGenerate} className="auto-generate-form">
                <div className="form-group">
                  <label>생성 개수</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={autoGenerateForm.count}
                    onChange={(e) => setAutoGenerateForm({ ...autoGenerateForm, count: parseInt(e.target.value) || 5 })}
                  />
                </div>

                <div className="form-group">
                  <label>카테고리</label>
                  <select
                    value={autoGenerateForm.category}
                    onChange={(e) => setAutoGenerateForm({ ...autoGenerateForm, category: e.target.value })}
                  >
                    {categories.length > 0 ? (
                      categories.map(cat => (
                        <option key={cat.value} value={cat.value}>{cat.label}</option>
                      ))
                    ) : (
                      <>
                        <option value="general">일반</option>
                        <option value="food">식품</option>
                        <option value="fashion">패션</option>
                        <option value="electronics">전자기기</option>
                        <option value="beauty">뷰티</option>
                      </>
                    )}
                  </select>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>최소 별점</label>
                    <select
                      value={autoGenerateForm.min_rating}
                      onChange={(e) => setAutoGenerateForm({ ...autoGenerateForm, min_rating: parseInt(e.target.value) })}
                    >
                      {[1, 2, 3, 4, 5].map(r => (
                        <option key={r} value={r}>{r}점</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>최대 별점</label>
                    <select
                      value={autoGenerateForm.max_rating}
                      onChange={(e) => setAutoGenerateForm({ ...autoGenerateForm, max_rating: parseInt(e.target.value) })}
                    >
                      {[1, 2, 3, 4, 5].map(r => (
                        <option key={r} value={r}>{r}점</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={() => setShowAutoGenerateForm(false)}>
                    취소
                  </button>
                  <button type="submit" className="btn-primary">
                    <Sparkles size={18} />
                    <span>자동 생성</span>
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
