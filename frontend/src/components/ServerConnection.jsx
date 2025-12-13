import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Server, CheckCircle, XCircle, Loader, RefreshCw, Zap } from 'lucide-react'
import {
  findBackendServer,
  savePort,
  clearSavedPort,
  getSavedPort,
  clearAllPortCache,
  autoSyncServers,
  checkAndReassignPort,
  isUsingCloudBackend
} from '../utils/apiConfig'
import '../styles/ServerConnection.css'

const ServerConnection = ({ onConnected }) => {
  const [status, setStatus] = useState('connecting') // connecting, success, failed, syncing
  const [progress, setProgress] = useState(null)
  const [port, setPort] = useState(null)
  const [autoSyncAttempts, setAutoSyncAttempts] = useState(0)

  const connectToServer = async (useAutoSync = false) => {
    setStatus(useAutoSync ? 'syncing' : 'connecting')
    setProgress(null)
    setPort(null)
    setAutoSyncAttempts(0)

    // 클라우드 백엔드 사용 시에는 캐시 초기화 불필요
    const usingCloud = isUsingCloudBackend()
    if (!usingCloud) {
      // 로컬 개발 환경에서만 캐시 초기화 (포트 충돌 방지)
      clearAllPortCache()
    }

    try {
      if (useAutoSync) {
        // 자동 동기화 모드: 연결될 때까지 계속 시도
        const foundPort = await autoSyncServers((progressInfo) => {
          if (progressInfo.isAutoSync) {
            setAutoSyncAttempts(progressInfo.attempt)
            setProgress(progressInfo)

            if (progressInfo.success) {
              setPort(progressInfo.port)
            }
          } else {
            setProgress(progressInfo)
          }
        })

        if (foundPort) {
          setStatus('success')
          onConnected(foundPort)
        } else {
          setStatus('failed')
        }
      } else {
        // 일반 연결 모드
        // 먼저 저장된 포트 확인 및 충돌 체크
        const savedPort = getSavedPort()
        if (savedPort) {
          setProgress({
            current: 1,
            total: 1,
            port: savedPort,
            message: `저장된 포트 ${savedPort} 충돌 체크 중...`
          })

          const checkedPort = await checkAndReassignPort(savedPort)

          if (checkedPort && checkedPort === savedPort) {
            // 저장된 포트 사용 가능
            setPort(checkedPort)
            setStatus('success')
            onConnected(checkedPort)
            return
          } else if (checkedPort) {
            // 다른 포트로 재할당됨
            setProgress({
              current: 1,
              total: 1,
              port: checkedPort,
              message: `포트 충돌 해결! 새 포트: ${checkedPort}`
            })
            setPort(checkedPort)
            setStatus('success')
            onConnected(checkedPort)
            return
          }

          // 실패하면 초기화
          clearSavedPort()
        }

        // 저장된 포트가 없거나 실패하면 자동 검색
        const foundPort = await findBackendServer((progressInfo) => {
          setProgress(progressInfo)

          if (progressInfo.success) {
            setPort(progressInfo.port)
            savePort(progressInfo.port)
          }
        })

        if (foundPort) {
          setStatus('success')
          onConnected(foundPort)
        } else {
          setStatus('failed')
        }
      }
    } catch (error) {
      console.error('서버 연결 오류:', error)
      setStatus('failed')
    }
  }

  const handleAutoSync = () => {
    connectToServer(true)
  }

  useEffect(() => {
    connectToServer()
  }, [])

  return (
    <div className="server-connection-overlay">
      <motion.div
        className="server-connection-modal"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="server-connection-header">
          <Server size={48} className="server-icon" />
          <h2>서버 연결</h2>
        </div>

        <div className="server-connection-content">
          {status === 'connecting' && (
            <>
              <div className="status-icon-wrapper">
                <Loader size={64} className="status-icon loading" />
              </div>
              <h3>
                {isUsingCloudBackend()
                  ? '클라우드 백엔드 연결 중...'
                  : '백엔드 서버 검색 중...'}
              </h3>
              {progress && (
                <div className="progress-info">
                  <p className="progress-message">{progress.message}</p>
                  {progress.cloudUrl && (
                    <p style={{fontSize: '0.85em', color: '#666', marginTop: '8px'}}>
                      {progress.cloudUrl}
                    </p>
                  )}
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{
                        width: `${(progress.current / progress.total) * 100}%`
                      }}
                    ></div>
                  </div>
                  <p className="progress-text">
                    {progress.cloudUrl
                      ? '클라우드 서버 연결 확인 중...'
                      : `${progress.current} / ${progress.total} 포트 확인됨`}
                  </p>
                </div>
              )}
            </>
          )}

          {status === 'syncing' && (
            <>
              <div className="status-icon-wrapper">
                <Zap size={64} className="status-icon syncing" />
              </div>
              <h3>자동 동기화 진행 중...</h3>
              <p className="sync-attempts">시도 횟수: {autoSyncAttempts}</p>
              {progress && (
                <div className="progress-info">
                  <p className="progress-message">{progress.message}</p>
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill syncing"
                      style={{
                        width: `${(progress.current / progress.total) * 100}%`
                      }}
                    ></div>
                  </div>
                  <p className="progress-text">
                    연결될 때까지 계속 시도합니다...
                  </p>
                </div>
              )}
            </>
          )}

          {status === 'success' && (
            <>
              <motion.div
                className="status-icon-wrapper"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 10 }}
              >
                <CheckCircle size={64} className="status-icon success" />
              </motion.div>
              <h3>연결 성공!</h3>
              <p className="status-message">
                {port === 'cloud'
                  ? '클라우드 백엔드 서버에 연결되었습니다'
                  : `포트 ${port}에서 백엔드 서버를 찾았습니다`}
              </p>
              <p className="status-submessage">
                {port === 'cloud' && progress?.cloudUrl && (
                  <span style={{fontSize: '0.9em', color: '#666'}}>
                    {progress.cloudUrl}
                  </span>
                )}
                {port !== 'cloud' && '잠시 후 대시보드가 표시됩니다...'}
              </p>
            </>
          )}

          {status === 'failed' && (
            <>
              <motion.div
                className="status-icon-wrapper"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 10 }}
              >
                <XCircle size={64} className="status-icon error" />
              </motion.div>
              <h3>연결 실패</h3>
              <p className="status-message">
                백엔드 서버를 찾을 수 없습니다
              </p>
              <p className="status-submessage">
                {isUsingCloudBackend()
                  ? `클라우드 백엔드 서버(${import.meta.env.VITE_API_URL})에 연결할 수 없습니다`
                  : '포트 8000-8009를 모두 확인했지만 서버가 실행되지 않고 있습니다'}
              </p>
              <div className="button-group">
                <button className="retry-button" onClick={() => connectToServer(false)}>
                  <RefreshCw size={20} />
                  <span>다시 시도</span>
                </button>
                {!isUsingCloudBackend() && (
                  <button className="auto-sync-button" onClick={handleAutoSync}>
                    <Zap size={20} />
                    <span>자동 동기화</span>
                  </button>
                )}
              </div>
              <div className="help-text">
                <p>💡 도움말:</p>
                {isUsingCloudBackend() ? (
                  <ul>
                    <li>클라우드 백엔드 서버가 정상 작동 중인지 확인하세요</li>
                    <li>네트워크 연결을 확인하세요</li>
                    <li>잠시 후 다시 시도해보세요</li>
                  </ul>
                ) : (
                  <ul>
                    <li>CoupangWingCS.exe가 실행 중인지 확인하세요</li>
                    <li>방화벽이 연결을 차단하지 않는지 확인하세요</li>
                    <li>프로그램을 재시작해보세요</li>
                    <li><strong>자동 동기화</strong>를 사용하면 연결될 때까지 계속 시도합니다</li>
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </motion.div>
    </div>
  )
}

export default ServerConnection
