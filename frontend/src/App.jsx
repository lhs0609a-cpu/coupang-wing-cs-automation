import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { ThemeProvider } from './contexts/ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import InquiryManagement from './components/InquiryManagement'
import ReturnManagement from './components/ReturnManagement'
import CoupangAccountManagement from './components/CoupangAccountManagement'
import NaverAccountManagement from './components/NaverAccountManagement'
import NaverOAuthCallback from './components/NaverOAuthCallback'
import PromotionManagement from './components/PromotionManagement'
import NaverReviewManagement from './components/NaverReviewManagement'
import NaverPayDelivery from './components/NaverPayDelivery'
import NaverDeliverySync from './components/NaverDeliverySync'
import ProductSearch from './components/ProductSearch'
import UploadMonitoring from './components/UploadMonitoring'
import IssueResponseManager from './components/IssueResponseManager'
import ServerConnection from './components/ServerConnection'
import { X, CheckCircle, AlertCircle } from 'lucide-react'
import { getApiBaseUrl } from './utils/apiConfig'
import './App.css'

function AppContent() {
  // 클라우드 백엔드 URL 하드코딩 (환경변수 문제 해결)
  const CLOUD_BACKEND_URL = 'https://coupang-wing-cs-backend.fly.dev/api'
  const defaultApiUrl = CLOUD_BACKEND_URL

  const [serverConnected, setServerConnected] = useState(false)
  const [apiBaseUrl, setApiBaseUrl] = useState(defaultApiUrl)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [responses, setResponses] = useState([])
  const [stats, setStats] = useState(null)
  const [automationStats, setAutomationStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState(null)

  // OAuth 콜백 체크
  const isOAuthCallback = window.location.pathname === '/naver/callback' ||
                          window.location.search.includes('code=')

  const handleServerConnected = (port) => {
    const newApiBaseUrl = getApiBaseUrl(port)
    setApiBaseUrl(newApiBaseUrl)
    setServerConnected(true)
    // 연결 성공 후 데이터 로드
    setTimeout(() => {
      loadData()
    }, 500)
  }

  useEffect(() => {
    if (serverConnected) {
      const interval = setInterval(loadData, 30000) // Refresh every 30s
      return () => clearInterval(interval)
    }
  }, [serverConnected])

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 5000)
  }

  const loadData = async () => {
    try {
      setLoading(true)
      const [responsesRes, statsRes, autoStatsRes] = await Promise.all([
        axios.get(`${apiBaseUrl}/responses/pending-approval`),
        axios.get(`${apiBaseUrl}/system/stats`),
        axios.get(`${apiBaseUrl}/automation/stats`)
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

  const handleApprove = async (responseId, editedText = null) => {
    try {
      await axios.post(`${apiBaseUrl}/responses/${responseId}/approve`, {
        approved_by: 'admin',
        edited_text: editedText
      })

      await axios.post(`${apiBaseUrl}/responses/${responseId}/submit`, {
        submitted_by: 'admin'
      })

      showNotification('승인 및 제출이 완료되었습니다', 'success')
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
      await axios.post(`${apiBaseUrl}/responses/${responseId}/reject`, null, {
        params: { reason }
      })
      showNotification('거부되었습니다', 'success')
      loadData()
    } catch (error) {
      console.error('거부 실패:', error)
      showNotification('거부에 실패했습니다', 'error')
    }
  }

  // 클라우드 백엔드 자동 연결
  useEffect(() => {
    console.log('=== 초기화 시작 ===')
    console.log('현재 apiBaseUrl:', apiBaseUrl)
    console.log('serverConnected:', serverConnected)

    if (!serverConnected) {
      console.log('클라우드 백엔드 자동 연결 시작:', apiBaseUrl)
      setServerConnected(true)
      setTimeout(() => {
        console.log('loadData 호출')
        loadData()
      }, 500)
    }
  }, [])

  // OAuth 콜백 페이지 처리
  if (isOAuthCallback) {
    return <NaverOAuthCallback apiBaseUrl={apiBaseUrl} showNotification={showNotification} />
  }

  // 서버 연결 화면을 건너뛰고 바로 연결 (클라우드 백엔드 사용)
  // if (!serverConnected) {
  //   return <ServerConnection onConnected={handleServerConnected} />
  // }

  return (
    <div className="app-layout">
      {/* Notification Toast */}
      <AnimatePresence>
        {notification && (
          <motion.div
            className={`notification-toast ${notification.type}`}
            initial={{ opacity: 0, y: -100, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: -100, x: '-50%' }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          >
            <div className="notification-content">
              {notification.type === 'success' ? (
                <CheckCircle size={24} className="notification-icon success" />
              ) : (
                <AlertCircle size={24} className="notification-icon error" />
              )}
              <div className="notification-message">{notification.message}</div>
              <button
                onClick={() => setNotification(null)}
                className="notification-close"
              >
                <X size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          {activeTab === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <Dashboard stats={stats} automationStats={automationStats} apiBaseUrl={apiBaseUrl} />
            </motion.div>
          )}

          {activeTab === 'upload-monitoring' && (
            <motion.div
              key="upload-monitoring"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <UploadMonitoring
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'inquiries' && (
            <motion.div
              key="inquiries"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <InquiryManagement
                responses={responses}
                onApprove={handleApprove}
                onReject={handleReject}
                loading={loading}
                apiBaseUrl={apiBaseUrl}
              />
            </motion.div>
          )}

          {activeTab === 'returns' && (
            <motion.div
              key="returns"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <ReturnManagement
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'issue-response' && (
            <motion.div
              key="issue-response"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <IssueResponseManager
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'promotion' && (
            <motion.div
              key="promotion"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <PromotionManagement
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'coupang-accounts' && (
            <motion.div
              key="coupang-accounts"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <CoupangAccountManagement
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'naver-accounts' && (
            <motion.div
              key="naver-accounts"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <NaverAccountManagement
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'automation' && (
            <motion.div
              key="automation"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              style={{ padding: '32px' }}
            >
              <h1 style={{ fontSize: '36px', fontWeight: 800, marginBottom: '16px', color: 'var(--text-primary)' }}>
                자동화 설정
              </h1>
              <p style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
                AI 자동화 기능을 설정하고 관리하세요
              </p>
              <div style={{
                background: 'var(--card-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '48px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '64px', marginBottom: '20px' }}>🚧</div>
                <h3 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>
                  곧 출시 예정
                </h3>
                <p style={{ fontSize: '16px', color: 'var(--text-secondary)' }}>
                  자동화 설정 기능이 개발 중입니다
                </p>
              </div>
            </motion.div>
          )}

          {activeTab === 'naver-review' && (
            <motion.div
              key="naver-review"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <NaverReviewManagement
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'naverpay-delivery' && (
            <motion.div
              key="naverpay-delivery"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <NaverPayDelivery
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'delivery-sync' && (
            <motion.div
              key="delivery-sync"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <NaverDeliverySync
                apiBaseUrl={apiBaseUrl}
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'product-search' && (
            <motion.div
              key="product-search"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <ProductSearch
                showNotification={showNotification}
              />
            </motion.div>
          )}

          {activeTab === 'settings' && (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              style={{ padding: '32px' }}
            >
              <h1 style={{ fontSize: '36px', fontWeight: 800, marginBottom: '16px', color: 'var(--text-primary)' }}>
                {activeTab === 'analytics' && '통계'}
                {activeTab === 'reports' && '리포트'}
                {activeTab === 'settings' && '설정'}
              </h1>
              <p style={{ fontSize: '16px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
                {activeTab === 'analytics' && '상세한 통계와 분석을 확인하세요'}
                {activeTab === 'reports' && '업무 리포트를 생성하고 관리하세요'}
                {activeTab === 'settings' && '시스템 설정을 변경하세요'}
              </p>
              <div style={{
                background: 'var(--card-bg)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '48px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '64px', marginBottom: '20px' }}>🚧</div>
                <h3 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>
                  곧 출시 예정
                </h3>
                <p style={{ fontSize: '16px', color: 'var(--text-secondary)' }}>
                  이 기능이 개발 중입니다
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}

export default App
