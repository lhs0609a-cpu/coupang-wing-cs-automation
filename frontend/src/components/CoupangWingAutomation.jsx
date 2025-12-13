import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Play, Loader, CheckCircle, XCircle, Settings, Activity } from 'lucide-react'
import '../styles/CoupangWingAutomation.css'

const CoupangWingAutomation = ({ apiBaseUrl }) => {
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState(null) // 'success', 'failed', null
  const [isRunningInquiries, setIsRunningInquiries] = useState(false) // 상품별 고객문의 실행 상태
  const [isRunningCallCenter, setIsRunningCallCenter] = useState(false) // 고객센터 문의 실행 상태
  const [inquiriesResult, setInquiriesResult] = useState(null) // 상품별 고객문의 결과
  const [callCenterResult, setCallCenterResult] = useState(null) // 고객센터 문의 결과
  const [error, setError] = useState(null)
  const [progressLogs, setProgressLogs] = useState([]) // 실시간 진행 로그
  const [currentStep, setCurrentStep] = useState('') // 현재 진행 중인 단계

  // 쿠팡 계정 관리
  const [accounts, setAccounts] = useState([]) // 저장된 계정 목록
  const [selectedAccountId, setSelectedAccountId] = useState('') // 선택된 계정 ID
  const [showAddAccount, setShowAddAccount] = useState(false) // 계정 추가 모달 표시

  // 새 계정 입력 필드
  const [newAccountName, setNewAccountName] = useState('')
  const [newAccessKey, setNewAccessKey] = useState('')
  const [newSecretKey, setNewSecretKey] = useState('')
  const [newVendorId, setNewVendorId] = useState('')
  const [newWingUsername, setNewWingUsername] = useState('')
  const [newWingPassword, setNewWingPassword] = useState('')

  // API에서 계정 목록 불러오기
  React.useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/coupang-accounts`)
        if (response.ok) {
          const accountsData = await response.json()
          setAccounts(accountsData)

          // 마지막으로 선택한 계정 불러오기 (localStorage)
          const lastSelectedId = localStorage.getItem('coupang_last_selected_account')
          if (lastSelectedId && accountsData.find(acc => acc.id === parseInt(lastSelectedId))) {
            setSelectedAccountId(parseInt(lastSelectedId))
          } else if (accountsData.length > 0) {
            setSelectedAccountId(accountsData[0].id)
          }
        }
      } catch (error) {
        console.error('Failed to fetch accounts:', error)
      }
    }
    fetchAccounts()
  }, [])

  // 선택된 계정 정보 가져오기
  const getSelectedAccount = () => {
    return accounts.find(acc => acc.id === selectedAccountId) || null
  }

  // 계정 추가
  const addAccount = async () => {
    if (!newAccountName || !newAccessKey || !newSecretKey || !newVendorId) {
      setError('모든 필드를 입력해주세요')
      return
    }

    const accountData = {
      name: newAccountName,
      access_key: newAccessKey,
      secret_key: newSecretKey,
      vendor_id: newVendorId,
      wing_username: newWingUsername || newVendorId,
      wing_password: newWingPassword || ''
    }

    try {
      const response = await fetch(`${apiBaseUrl}/coupang-accounts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(accountData)
      })

      if (response.ok) {
        const newAccount = await response.json()

        // 계정 목록에 추가
        const updatedAccounts = [...accounts, newAccount]
        setAccounts(updatedAccounts)

        // 새로 추가한 계정 선택
        setSelectedAccountId(newAccount.id)
        localStorage.setItem('coupang_last_selected_account', newAccount.id)

        // 입력 필드 초기화
        setNewAccountName('')
        setNewAccessKey('')
        setNewSecretKey('')
        setNewVendorId('')
        setNewWingUsername('')
        setNewWingPassword('')
        setShowAddAccount(false)
        setConnectionStatus(null)

        addLog(`✅ 계정 "${newAccountName}" 추가 완료`, 'success')
        setError(null)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '계정 추가 실패')
        addLog(`❌ 계정 추가 실패: ${errorData.detail}`, 'error')
      }
    } catch (error) {
      setError('계정 추가 중 오류 발생')
      addLog(`❌ 계정 추가 오류: ${error.message}`, 'error')
    }
  }

  // 계정 삭제
  const deleteAccount = async (accountId) => {
    if (!confirm('이 계정을 삭제하시겠습니까?')) return

    try {
      const response = await fetch(`${apiBaseUrl}/coupang-accounts/${accountId}`, {
        method: 'DELETE'
      })

      if (response.ok || response.status === 204) {
        const updatedAccounts = accounts.filter(acc => acc.id !== accountId)
        setAccounts(updatedAccounts)

        // 삭제된 계정이 선택되어 있었다면 다른 계정 선택
        if (selectedAccountId === accountId) {
          const newSelectedId = updatedAccounts.length > 0 ? updatedAccounts[0].id : ''
          setSelectedAccountId(newSelectedId)
          if (newSelectedId) {
            localStorage.setItem('coupang_last_selected_account', newSelectedId)
          } else {
            localStorage.removeItem('coupang_last_selected_account')
          }
          setConnectionStatus(null)
        }

        addLog('🗑️ 계정 삭제 완료', 'info')
      } else {
        addLog('❌ 계정 삭제 실패', 'error')
      }
    } catch (error) {
      addLog(`❌ 계정 삭제 오류: ${error.message}`, 'error')
    }
  }

  // 계정 선택
  const selectAccount = (accountId) => {
    setSelectedAccountId(accountId)
    localStorage.setItem('coupang_last_selected_account', accountId)
    setConnectionStatus(null) // 연결 상태 초기화
    addLog(`📋 계정 선택: ${accounts.find(acc => acc.id === accountId)?.name}`, 'info')
  }

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ko-KR')
    setProgressLogs(prev => [...prev, { message, type, timestamp }])
  }

  const clearLogs = () => {
    setProgressLogs([])
    setCurrentStep('')
  }

  const testConnection = async () => {
    setIsTestingConnection(true)
    setConnectionStatus(null)
    setError(null)
    clearLogs()

    addLog('🔌 Coupang API 연결 테스트 중...', 'info')
    setCurrentStep('API 연결 테스트 중')

    try {
      addLog(`📡 요청 전송: ${apiBaseUrl}/coupang-api/test-connection`, 'info')

      // 선택된 계정 정보 가져오기
      const selectedAccount = getSelectedAccount()
      const credentials = selectedAccount
        ? {
            access_key: selectedAccount.access_key,
            secret_key: selectedAccount.secret_key,
            vendor_id: selectedAccount.vendor_id,
            wing_username: selectedAccount.wing_username
          }
        : null

      if (selectedAccount) {
        addLog(`📋 사용 계정: ${selectedAccount.name}`, 'info')
      }

      const response = await fetch(`${apiBaseUrl}/coupang-api/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials)
      })

      addLog('✅ 서버 응답 수신', 'success')
      setCurrentStep('응답 처리 중')

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      addLog('📦 응답 데이터 파싱 완료', 'success')

      if (data.success) {
        setConnectionStatus('success')
        addLog('✅ Coupang API 연결 성공!', 'success')
        addLog(`📌 Vendor ID: ${data.data.vendor_id}`, 'info')
        addLog(`📌 API 상태: 정상 작동`, 'success')
        setCurrentStep('완료')
      } else {
        setConnectionStatus('failed')
        setError(data.message || 'API 연결 실패')
        addLog(`❌ API 연결 실패: ${data.message || '알 수 없는 오류'}`, 'error')
        setCurrentStep('실패')
      }
    } catch (err) {
      setConnectionStatus('failed')
      const errorMsg = `연결 오류: ${err.message}`
      setError(errorMsg)
      addLog(`❌ ${errorMsg}`, 'error')
      addLog('💡 백엔드 서버 상태를 확인해주세요', 'warning')
      setCurrentStep('연결 실패')
    } finally {
      setIsTestingConnection(false)
    }
  }

  const runInquiriesAutomation = async () => {
    if (!connectionStatus || connectionStatus !== 'success') {
      setError('먼저 API 연결 테스트를 성공해주세요')
      return
    }

    setIsRunningInquiries(true)
    setInquiriesResult(null)
    setError(null)
    clearLogs()

    addLog('🚀 상품별 고객문의 자동 답변 시작', 'info')
    addLog('🔌 백엔드 API 호출 중...', 'info')
    setCurrentStep('서버 연결 중')

    try {
      // 선택된 계정 정보 가져오기
      const selectedAccount = getSelectedAccount()
      if (selectedAccount) {
        addLog(`📋 사용 계정: ${selectedAccount.name}`, 'info')
      }

      addLog(`📡 요청 전송: ${apiBaseUrl}/coupang-api/inquiries/auto-answer`, 'info')
      addLog('⏳ 자동화 실행 중... (시간이 걸릴 수 있습니다)', 'info')
      setCurrentStep('상품별 고객문의 자동화 실행 중')

      const requestBody = {
        auto_generate: true,  // ChatGPT 자동 생성 활성화
        answered_type: "NOANSWER"  // 미답변 문의만 조회
      }

      // 계정이 선택되어 있으면 credentials 추가
      if (selectedAccount) {
        requestBody.credentials = {
          access_key: selectedAccount.access_key,
          secret_key: selectedAccount.secret_key,
          vendor_id: selectedAccount.vendor_id,
          wing_username: selectedAccount.wing_username
        }
      }

      const response = await fetch(`${apiBaseUrl}/coupang-api/inquiries/auto-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      addLog('✅ 서버 응답 수신', 'success')
      setCurrentStep('결과 처리 중')

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      addLog('📦 응답 데이터 파싱 완료', 'success')

      if (data.success) {
        setInquiriesResult(data)
        addLog('✅ 상품별 고객문의 자동화 완료!', 'success')
        addLog(`📊 총 문의: ${data.statistics?.total_inquiries || 0}개`, 'info')
        addLog(`✅ 답변 완료: ${data.statistics?.answered || 0}개`, 'success')
        addLog(`❌ 실패: ${data.statistics?.failed || 0}개`, data.statistics?.failed > 0 ? 'error' : 'info')
        addLog(`⏭️ 건너뜀: ${data.statistics?.skipped || 0}개`, 'info')
        setCurrentStep('완료')
      } else {
        const errorMsg = data.message || '자동화 실행 실패'
        setError(errorMsg)
        addLog(`❌ 자동화 실패: ${errorMsg}`, 'error')
        setCurrentStep('실패')
      }
    } catch (err) {
      const errorMsg = `연결 오류: ${err.message}`
      setError(errorMsg)
      addLog(`❌ ${errorMsg}`, 'error')
      addLog('💡 백엔드 서버 상태를 확인해주세요', 'warning')
      setCurrentStep('연결 실패')
    } finally {
      setIsRunningInquiries(false)
    }
  }

  const runCallCenterAutomation = async () => {
    if (!connectionStatus || connectionStatus !== 'success') {
      setError('먼저 API 연결 테스트를 성공해주세요')
      return
    }

    setIsRunningCallCenter(true)
    setCallCenterResult(null)
    setError(null)
    clearLogs()

    addLog('🚀 고객센터 문의 자동 답변 시작', 'info')
    addLog('🔌 백엔드 API 호출 중...', 'info')
    setCurrentStep('서버 연결 중')

    try {
      // 선택된 계정 정보 가져오기
      const selectedAccount = getSelectedAccount()
      if (selectedAccount) {
        addLog(`📋 사용 계정: ${selectedAccount.name}`, 'info')
      }

      addLog(`📡 요청 전송: ${apiBaseUrl}/coupang-api/call-center-inquiries/auto-answer`, 'info')
      addLog('⏳ 자동화 실행 중... (시간이 걸릴 수 있습니다)', 'info')
      setCurrentStep('고객센터 문의 자동화 실행 중')

      const requestBody = {
        auto_generate: true  // ChatGPT 자동 생성 활성화
      }

      // 계정이 선택되어 있으면 credentials 추가
      if (selectedAccount) {
        requestBody.credentials = {
          access_key: selectedAccount.access_key,
          secret_key: selectedAccount.secret_key,
          vendor_id: selectedAccount.vendor_id,
          wing_username: selectedAccount.wing_username
        }
      }

      const response = await fetch(`${apiBaseUrl}/coupang-api/call-center-inquiries/auto-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      addLog('✅ 서버 응답 수신', 'success')
      setCurrentStep('결과 처리 중')

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      addLog('📦 응답 데이터 파싱 완료', 'success')

      if (data.success) {
        setCallCenterResult(data)
        addLog('✅ 고객센터 문의 자동화 완료!', 'success')
        addLog(`📊 총 문의: ${data.statistics?.total_inquiries || 0}개`, 'info')
        addLog(`✅ 답변 완료: ${data.statistics?.answered || 0}개`, 'success')
        addLog(`❌ 실패: ${data.statistics?.failed || 0}개`, data.statistics?.failed > 0 ? 'error' : 'info')
        addLog(`⏭️ 건너뜀: ${data.statistics?.skipped || 0}개`, 'info')
        setCurrentStep('완료')
      } else {
        const errorMsg = data.message || '자동화 실행 실패'
        setError(errorMsg)
        addLog(`❌ 자동화 실패: ${errorMsg}`, 'error')
        setCurrentStep('실패')
      }
    } catch (err) {
      const errorMsg = `연결 오류: ${err.message}`
      setError(errorMsg)
      addLog(`❌ ${errorMsg}`, 'error')
      addLog('💡 백엔드 서버 상태를 확인해주세요', 'warning')
      setCurrentStep('연결 실패')
    } finally {
      setIsRunningCallCenter(false)
    }
  }

  return (
    <motion.div
      className="coupang-wing-automation"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
    >
      <div className="automation-header">
        <div className="header-title">
          <Settings size={24} className="header-icon" />
          <h3>쿠팡 윙 CS 자동화 (Open API)</h3>
        </div>
        <p className="header-subtitle">Coupang Open API 기반 자동 응답 시스템</p>
      </div>

      <div className="automation-content">
        {/* 0단계: 쿠팡 계정 설정 */}
        <div className="login-section">
          <h4>0단계: 쿠팡 계정 설정</h4>
          <p className="section-description">
            쿠팡 API 인증 정보를 등록하고 관리합니다.
          </p>

          {/* 계정 선택 드롭다운 */}
          {accounts.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#2d3748' }}>
                사용할 계정 선택:
              </label>
              <select
                value={selectedAccountId}
                onChange={(e) => selectAccount(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  backgroundColor: 'white'
                }}
                disabled={isRunningInquiries || isRunningCallCenter || isTestingConnection}
              >
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} ({account.vendor_id})
                  </option>
                ))}
              </select>

              {/* 계정 삭제 버튼 */}
              <button
                onClick={() => deleteAccount(selectedAccountId)}
                disabled={isRunningInquiries || isRunningCallCenter || isTestingConnection}
                style={{
                  marginTop: '8px',
                  padding: '8px 16px',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                선택된 계정 삭제
              </button>
            </div>
          )}

          {/* 계정 추가 버튼 */}
          {!showAddAccount && (
            <button
              onClick={() => setShowAddAccount(true)}
              disabled={isRunningInquiries || isRunningCallCenter || isTestingConnection}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                marginBottom: '16px'
              }}
            >
              + 새 계정 추가
            </button>
          )}

          {/* 계정 추가 폼 */}
          {showAddAccount && (
            <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
              <h5 style={{ marginTop: 0, marginBottom: '12px' }}>새 계정 추가</h5>

              <input
                type="text"
                placeholder="계정 이름 (예: 내 쿠팡 계정)"
                value={newAccountName}
                onChange={(e) => setNewAccountName(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <input
                type="text"
                placeholder="업체코드 (Vendor ID)"
                value={newVendorId}
                onChange={(e) => setNewVendorId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <input
                type="text"
                placeholder="액세스 키 (Access Key)"
                value={newAccessKey}
                onChange={(e) => setNewAccessKey(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <input
                type="password"
                placeholder="시크릿 키 (Secret Key)"
                value={newSecretKey}
                onChange={(e) => setNewSecretKey(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '10px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <input
                type="text"
                placeholder="Wing 사용자명 (선택사항)"
                value={newWingUsername}
                onChange={(e) => setNewWingUsername(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '12px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <input
                type="password"
                placeholder="Wing 비밀번호 (선택사항)"
                value={newWingPassword}
                onChange={(e) => setNewWingPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  marginBottom: '12px',
                  border: '2px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '0.95rem'
                }}
              />

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={addAccount}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  저장
                </button>
                <button
                  onClick={() => {
                    setShowAddAccount(false)
                    setNewAccountName('')
                    setNewAccessKey('')
                    setNewSecretKey('')
                    setNewVendorId('')
                    setNewWingUsername('')
                    setNewWingPassword('')
                  }}
                  style={{
                    flex: 1,
                    padding: '10px',
                    backgroundColor: '#6b7280',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </div>

        {/* API 연결 테스트 */}
        <div className="login-section">
          <h4>1단계: Coupang API 연결 확인</h4>
          <p className="section-description">
            먼저 Coupang Open API와의 연결을 테스트합니다.
          </p>

          {/* API 연결 테스트 버튼 */}
          <button
            className={`test-login-button ${isTestingConnection ? 'testing' : ''} ${connectionStatus === 'success' ? 'success' : ''}`}
            onClick={testConnection}
            disabled={isRunningInquiries || isRunningCallCenter || isTestingConnection}
          >
            {isTestingConnection ? (
              <>
                <Loader size={20} className="spinner" />
                <span>API 연결 테스트 중...</span>
              </>
            ) : connectionStatus === 'success' ? (
              <>
                <CheckCircle size={20} />
                <span>API 연결 성공! ✓</span>
              </>
            ) : (
              <>
                <Activity size={20} />
                <span>API 연결 테스트</span>
              </>
            )}
          </button>

          {/* 연결 상태 표시 */}
          {connectionStatus === 'success' && (
            <motion.div
              className="login-success-message"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <CheckCircle size={16} />
              <span>Coupang API 연결 성공! 이제 자동화를 실행할 수 있습니다.</span>
            </motion.div>
          )}

          {connectionStatus === 'failed' && (
            <motion.div
              className="login-failed-message"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <XCircle size={16} />
              <span>API 연결 실패. 백엔드 서버를 확인해주세요.</span>
            </motion.div>
          )}
        </div>

        {/* 2단계: 자동화 실행 */}
        <div className="automation-section">
          <h4>2단계: 자동화 실행</h4>
          <p className="section-description">
            {connectionStatus === 'success'
              ? 'API 연결 성공! 원하는 자동화를 선택하여 실행할 수 있습니다.'
              : '먼저 API 연결 테스트를 완료해주세요.'}
          </p>

          {/* 상품별 고객문의 자동 답변 버튼 */}
          <div className="automation-button-group">
            <button
              className={`run-button ${isRunningInquiries ? 'running' : ''}`}
              onClick={runInquiriesAutomation}
              disabled={isRunningInquiries || isRunningCallCenter || connectionStatus !== 'success'}
            >
              {isRunningInquiries ? (
                <>
                  <Loader size={20} className="spinner" />
                  <span>상품별 고객문의 자동화 실행 중...</span>
                </>
              ) : (
                <>
                  <Play size={20} />
                  <span>상품별 고객문의 답변</span>
                </>
              )}
            </button>

            {/* 고객센터 문의 자동 답변 버튼 */}
            <button
              className={`run-button ${isRunningCallCenter ? 'running' : ''}`}
              onClick={runCallCenterAutomation}
              disabled={isRunningInquiries || isRunningCallCenter || connectionStatus !== 'success'}
            >
              {isRunningCallCenter ? (
                <>
                  <Loader size={20} className="spinner" />
                  <span>고객센터 문의 자동화 실행 중...</span>
                </>
              ) : (
                <>
                  <Play size={20} />
                  <span>고객센터 문의 답변</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 실시간 진행 로그 */}
        {(isTestingConnection || isRunningInquiries || isRunningCallCenter || progressLogs.length > 0) && (
          <motion.div
            className="progress-logs-container"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="progress-header">
              <h4>
                {isTestingConnection || isRunningInquiries || isRunningCallCenter ? (
                  <>
                    <Loader size={18} className="spinner" />
                    <span>{currentStep}</span>
                  </>
                ) : (
                  <>
                    <CheckCircle size={18} />
                    <span>실행 로그</span>
                  </>
                )}
              </h4>
              {progressLogs.length > 0 && (
                <button
                  className="clear-logs-btn"
                  onClick={clearLogs}
                  disabled={isTestingConnection || isRunningInquiries || isRunningCallCenter}
                >
                  지우기
                </button>
              )}
            </div>
            <div className="progress-logs">
              {progressLogs.map((log, index) => (
                <motion.div
                  key={index}
                  className={`log-entry log-${log.type}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <span className="log-timestamp">{log.timestamp}</span>
                  <span className="log-message">{log.message}</span>
                </motion.div>
              ))}
              {(isTestingConnection || isRunningInquiries || isRunningCallCenter) && (
                <motion.div
                  className="log-entry log-loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                >
                  <Loader size={14} className="spinner" />
                  <span className="log-message">처리 중...</span>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* 상품별 고객문의 결과 표시 */}
        {inquiriesResult && (
          <motion.div
            className="result-box success"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="result-header">
              <CheckCircle size={24} className="result-icon" />
              <h4>상품별 고객문의 자동화 완료!</h4>
            </div>
            <p className="result-message">{inquiriesResult.message}</p>
            <div className="statistics">
              <div className="stat-item">
                <span className="stat-label">총 문의</span>
                <span className="stat-value">{inquiriesResult.statistics?.total_inquiries || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">답변 완료</span>
                <span className="stat-value success">{inquiriesResult.statistics?.answered || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">실패</span>
                <span className="stat-value error">{inquiriesResult.statistics?.failed || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">건너뜀</span>
                <span className="stat-value">{inquiriesResult.statistics?.skipped || 0}</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* 고객센터 문의 결과 표시 */}
        {callCenterResult && (
          <motion.div
            className="result-box success"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="result-header">
              <CheckCircle size={24} className="result-icon" />
              <h4>고객센터 문의 자동화 완료!</h4>
            </div>
            <p className="result-message">{callCenterResult.message}</p>
            <div className="statistics">
              <div className="stat-item">
                <span className="stat-label">총 문의</span>
                <span className="stat-value">{callCenterResult.statistics?.total_inquiries || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">답변 완료</span>
                <span className="stat-value success">{callCenterResult.statistics?.answered || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">확인완료</span>
                <span className="stat-value success">{callCenterResult.statistics?.confirmed || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">실패</span>
                <span className="stat-value error">{callCenterResult.statistics?.failed || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">건너뜀</span>
                <span className="stat-value">{callCenterResult.statistics?.skipped || 0}</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* 에러 표시 */}
        {error && (
          <motion.div
            className="result-box error"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <div className="result-header">
              <XCircle size={24} className="result-icon" />
              <h4>자동화 실패</h4>
            </div>
            <p className="result-message">{error}</p>
          </motion.div>
        )}

        {/* 안내 */}
        <div className="info-section">
          <h4>자동화 프로세스 (Open API)</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '16px' }}>
            <div>
              <h5 style={{ marginBottom: '8px', color: '#2d3748' }}>📦 상품별 고객문의</h5>
              <ol className="process-list" style={{ fontSize: '0.9rem' }}>
                <li>미답변 고객문의 조회 (최근 7일)</li>
                <li>ChatGPT로 답변 자동 생성</li>
                <li>생성된 답변 자동 제출</li>
                <li>결과 통계 제공</li>
              </ol>
            </div>
            <div>
              <h5 style={{ marginBottom: '8px', color: '#2d3748' }}>📞 고객센터 문의</h5>
              <ol className="process-list" style={{ fontSize: '0.9rem' }}>
                <li>미답변 고객센터 문의 조회</li>
                <li>특수 케이스 자동 감지</li>
                <li>ChatGPT로 답변 자동 생성</li>
                <li>생성된 답변 자동 제출</li>
              </ol>
            </div>
          </div>
          <p className="section-description" style={{ marginTop: '16px', fontSize: '0.9rem', color: '#718096' }}>
            💡 <strong>Open API 방식의 장점:</strong><br/>
            • 브라우저 필요 없음 (메모리 효율적)<br/>
            • 빠르고 안정적인 실행<br/>
            • 서버 배포 가능<br/>
            • API 키만 있으면 자동 인증
          </p>
        </div>
      </div>
    </motion.div>
  )
}

export default CoupangWingAutomation
