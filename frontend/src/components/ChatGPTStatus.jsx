import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Bot, CheckCircle, XCircle, Loader, RefreshCw } from 'lucide-react'
import axios from 'axios'
import { getApiBaseUrl, getSavedPort } from '../utils/apiConfig'
import '../styles/ChatGPTStatus.css'

const ChatGPTStatus = () => {
  const [status, setStatus] = useState('checking') // checking, connected, disconnected, error
  const [statusData, setStatusData] = useState(null)
  const [testing, setTesting] = useState(false)

  const getApiUrl = () => {
    const port = getSavedPort()
    return getApiBaseUrl(port)
  }

  const checkStatus = async () => {
    try {
      setStatus('checking')
      const API_BASE_URL = getApiUrl()
      if (!API_BASE_URL) {
        throw new Error('백엔드 서버가 연결되지 않았습니다')
      }
      const response = await axios.get(`${API_BASE_URL}/automation/chatgpt/status`)
      setStatusData(response.data)
      setStatus(response.data.connected ? 'connected' : 'disconnected')
    } catch (error) {
      console.error('ChatGPT 상태 확인 실패:', error)
      setStatus('error')
      setStatusData({
        connected: false,
        status: 'error',
        message: error.message || '상태 확인 실패'
      })
    }
  }

  const testConnection = async () => {
    try {
      setTesting(true)
      const API_BASE_URL = getApiUrl()
      if (!API_BASE_URL) {
        throw new Error('백엔드 서버가 연결되지 않았습니다')
      }
      const response = await axios.post(`${API_BASE_URL}/automation/chatgpt/test-connection`)

      if (response.data.connected) {
        setStatus('connected')
        setStatusData({
          connected: true,
          status: 'connected',
          message: response.data.message,
          model: response.data.model
        })
      }
    } catch (error) {
      console.error('ChatGPT 연결 테스트 실패:', error)
      const errorMessage = error.response?.data?.detail || error.message || '연결 테스트 실패'
      setStatus('disconnected')
      setStatusData({
        connected: false,
        status: 'error',
        message: errorMessage
      })
    } finally {
      setTesting(false)
    }
  }

  useEffect(() => {
    checkStatus()
    // 30초마다 상태 확인
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    switch (status) {
      case 'checking':
        return <Loader size={24} className="status-icon checking" />
      case 'connected':
        return <CheckCircle size={24} className="status-icon connected" />
      case 'disconnected':
      case 'error':
        return <XCircle size={24} className="status-icon disconnected" />
      default:
        return <Loader size={24} className="status-icon checking" />
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'checking':
        return '확인 중...'
      case 'connected':
        return '연결됨'
      case 'disconnected':
        return '연결 안됨'
      case 'error':
        return '오류'
      default:
        return '알 수 없음'
    }
  }

  return (
    <motion.div
      className="chatgpt-status-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
    >
      <div className="chatgpt-header">
        <div className="chatgpt-title-section">
          <Bot size={24} className="chatgpt-icon" />
          <h3>ChatGPT 연결 상태</h3>
        </div>
        {getStatusIcon()}
      </div>

      <div className="chatgpt-content">
        <div className={`status-badge ${status}`}>
          {getStatusText()}
        </div>

        {statusData && (
          <div className="status-details">
            <p className="status-message">{statusData.message}</p>
            {statusData.model && (
              <p className="model-info">모델: {statusData.model}</p>
            )}
          </div>
        )}

        <div className="chatgpt-actions">
          <button
            className="status-button refresh"
            onClick={checkStatus}
            disabled={status === 'checking'}
          >
            <RefreshCw size={16} className={status === 'checking' ? 'spinning' : ''} />
            <span>상태 확인</span>
          </button>

          {status !== 'connected' && (
            <button
              className="status-button connect"
              onClick={testConnection}
              disabled={testing}
            >
              {testing ? (
                <>
                  <Loader size={16} className="spinning" />
                  <span>연결 시도 중...</span>
                </>
              ) : (
                <>
                  <Bot size={16} />
                  <span>자동 연결 시도</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default ChatGPTStatus
