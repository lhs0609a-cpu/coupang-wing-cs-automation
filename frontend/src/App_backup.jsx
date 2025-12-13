import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { ThemeProvider } from './contexts/ThemeContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import InquiryManagement from './components/InquiryManagement'
import { Bell, X, CheckCircle, AlertCircle } from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000/api'

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [responses, setResponses] = useState([])
  const [stats, setStats] = useState(null)
  const [automationStats, setAutomationStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Refresh every 30s
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

  const handleApprove = async (responseId, editedText = null) => {
    try {
      await axios.post(`${API_BASE_URL}/responses/${responseId}/approve`, {
        approved_by: 'admin',
        edited_text: editedText
      })

      await axios.post(`${API_BASE_URL}/responses/${responseId}/submit`, {
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
              <Dashboard stats={stats} automationStats={automationStats} />
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

          {(activeTab === 'analytics' || activeTab === 'reports' || activeTab === 'settings') && (
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
