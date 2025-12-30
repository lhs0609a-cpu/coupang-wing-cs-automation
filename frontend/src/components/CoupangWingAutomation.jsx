import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  Loader,
  CheckCircle,
  XCircle,
  Settings,
  Activity,
  Search,
  PlusCircle,
  History,
  Zap,
  RefreshCw,
  MessageSquare,
  Phone,
  Package,
  Calendar,
  Clock,
  Send,
  Eye,
  Edit3,
  Trash2,
  ChevronDown,
  ChevronUp,
  Filter
} from 'lucide-react'
import '../styles/CoupangWingAutomation.css'

const CoupangWingAutomation = ({ apiBaseUrl }) => {
  // 탭 상태
  const [activeTab, setActiveTab] = useState('inquiries') // 'inquiries', 'manual', 'auto', 'history'

  // 기본 상태
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState(null)
  const [error, setError] = useState(null)
  const [progressLogs, setProgressLogs] = useState([])
  const [currentStep, setCurrentStep] = useState('')

  // 계정 관리
  const [accounts, setAccounts] = useState([])
  const [selectedAccountId, setSelectedAccountId] = useState('')
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [newAccountName, setNewAccountName] = useState('')
  const [newAccessKey, setNewAccessKey] = useState('')
  const [newSecretKey, setNewSecretKey] = useState('')
  const [newVendorId, setNewVendorId] = useState('')
  const [newWingUsername, setNewWingUsername] = useState('')
  const [newWingPassword, setNewWingPassword] = useState('')

  // 문의 조회 상태
  const [inquiries, setInquiries] = useState([])
  const [callCenterInquiries, setCallCenterInquiries] = useState([])
  const [isLoadingInquiries, setIsLoadingInquiries] = useState(false)
  const [inquiryType, setInquiryType] = useState('product') // 'product' or 'callcenter'
  const [inquiryFilter, setInquiryFilter] = useState('NOANSWER') // 'NOANSWER', 'ANSWER', 'ALL'
  const [expandedInquiry, setExpandedInquiry] = useState(null)

  // 자동 답변 상태
  const [isRunningAuto, setIsRunningAuto] = useState(false)
  const [autoResult, setAutoResult] = useState(null)

  // 답변 내역 상태
  const [responseHistory, setResponseHistory] = useState([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

  // 특수 양식 처리 상태
  const [showSkippedList, setShowSkippedList] = useState(false)
  const [processingSpecialForm, setProcessingSpecialForm] = useState({})
  const [specialFormStatus, setSpecialFormStatus] = useState(null)

  // 수동 입력 상태
  const [manualInquiry, setManualInquiry] = useState({
    type: 'product',
    inquiryId: '',
    productName: '',
    customerQuestion: '',
    response: ''
  })

  // 계정 목록 불러오기
  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/coupang-accounts`)
        if (response.ok) {
          const accountsData = await response.json()
          setAccounts(accountsData)
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
  }, [apiBaseUrl])

  const getSelectedAccount = () => accounts.find(acc => acc.id === selectedAccountId) || null

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ko-KR')
    setProgressLogs(prev => [...prev, { message, type, timestamp }])
  }

  const clearLogs = () => {
    setProgressLogs([])
    setCurrentStep('')
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountData)
      })

      if (response.ok) {
        const newAccount = await response.json()
        const updatedAccounts = [...accounts, newAccount]
        setAccounts(updatedAccounts)
        setSelectedAccountId(newAccount.id)
        localStorage.setItem('coupang_last_selected_account', newAccount.id)
        setNewAccountName('')
        setNewAccessKey('')
        setNewSecretKey('')
        setNewVendorId('')
        setNewWingUsername('')
        setNewWingPassword('')
        setShowAddAccount(false)
        setConnectionStatus(null)
        addLog(`계정 "${newAccountName}" 추가 완료`, 'success')
        setError(null)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || '계정 추가 실패')
      }
    } catch (error) {
      setError('계정 추가 중 오류 발생')
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
        addLog('계정 삭제 완료', 'info')
      }
    } catch (error) {
      addLog(`계정 삭제 오류: ${error.message}`, 'error')
    }
  }

  const selectAccount = (accountId) => {
    setSelectedAccountId(accountId)
    localStorage.setItem('coupang_last_selected_account', accountId)
    setConnectionStatus(null)
  }

  // API 연결 테스트
  const testConnection = async () => {
    setIsTestingConnection(true)
    setConnectionStatus(null)
    setError(null)
    clearLogs()
    addLog('Coupang API 연결 테스트 중...', 'info')

    try {
      const selectedAccount = getSelectedAccount()
      const requestBody = selectedAccount ? {
        account_id: selectedAccount.id,
        credentials: {
          access_key: selectedAccount.access_key,
          secret_key: selectedAccount.secret_key,
          vendor_id: selectedAccount.vendor_id,
          wing_username: selectedAccount.wing_username
        }
      } : null

      const response = await fetch(`${apiBaseUrl}/coupang-api/test-connection`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()

      if (data.success) {
        setConnectionStatus('success')
        addLog('API 연결 성공!', 'success')
      } else {
        setConnectionStatus('failed')
        setError(data.message || 'API 연결 실패')
        addLog(`API 연결 실패: ${data.message}`, 'error')
      }
    } catch (err) {
      setConnectionStatus('failed')
      setError(`연결 오류: ${err.message}`)
      addLog(`연결 오류: ${err.message}`, 'error')
    } finally {
      setIsTestingConnection(false)
    }
  }

  // 문의 조회
  const fetchInquiries = async () => {
    if (connectionStatus !== 'success') {
      setError('먼저 API 연결 테스트를 완료해주세요')
      return
    }

    setIsLoadingInquiries(true)
    setError(null)
    addLog(`${inquiryType === 'product' ? '상품별' : '고객센터'} 문의 조회 중...`, 'info')

    try {
      const selectedAccount = getSelectedAccount()
      const credentials = selectedAccount ? {
        access_key: selectedAccount.access_key,
        secret_key: selectedAccount.secret_key,
        vendor_id: selectedAccount.vendor_id
      } : null

      const endpoint = inquiryType === 'product'
        ? `${apiBaseUrl}/coupang-api/inquiries`
        : `${apiBaseUrl}/coupang-api/call-center-inquiries`

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credentials,
          answered_type: inquiryFilter
        })
      })

      const data = await response.json()

      if (data.success) {
        if (inquiryType === 'product') {
          setInquiries(data.inquiries || [])
        } else {
          setCallCenterInquiries(data.inquiries || [])
        }
        addLog(`${data.inquiries?.length || 0}개 문의 조회 완료`, 'success')
      } else {
        setError(data.message || '문의 조회 실패')
        addLog(`문의 조회 실패: ${data.message}`, 'error')
      }
    } catch (err) {
      setError(`조회 오류: ${err.message}`)
      addLog(`조회 오류: ${err.message}`, 'error')
    } finally {
      setIsLoadingInquiries(false)
    }
  }

  // 자동 답변 실행
  const runAutoAnswer = async () => {
    if (connectionStatus !== 'success') {
      setError('먼저 API 연결 테스트를 완료해주세요')
      return
    }

    setIsRunningAuto(true)
    setAutoResult(null)
    setError(null)
    clearLogs()
    addLog(`${inquiryType === 'product' ? '상품별 고객문의' : '고객센터 문의'} 자동 답변 시작`, 'info')

    try {
      const selectedAccount = getSelectedAccount()
      const requestBody = {
        auto_generate: true,
        answered_type: 'NOANSWER'
      }

      if (selectedAccount) {
        requestBody.credentials = {
          access_key: selectedAccount.access_key,
          secret_key: selectedAccount.secret_key,
          vendor_id: selectedAccount.vendor_id,
          wing_username: selectedAccount.wing_username
        }
      }

      const endpoint = inquiryType === 'product'
        ? `${apiBaseUrl}/coupang-api/inquiries/auto-answer`
        : `${apiBaseUrl}/coupang-api/call-center-inquiries/auto-answer`

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()

      if (data.success) {
        setAutoResult(data)
        addLog('자동 답변 완료!', 'success')
        addLog(`총 문의: ${data.statistics?.total_inquiries || 0}개`, 'info')
        addLog(`답변 완료: ${data.statistics?.answered || 0}개`, 'success')
        addLog(`실패: ${data.statistics?.failed || 0}개`, data.statistics?.failed > 0 ? 'error' : 'info')
        // 답변 내역 새로고침
        fetchResponseHistory()
      } else {
        setError(data.message || '자동 답변 실패')
        addLog(`자동 답변 실패: ${data.message}`, 'error')
      }
    } catch (err) {
      setError(`오류: ${err.message}`)
      addLog(`오류: ${err.message}`, 'error')
    } finally {
      setIsRunningAuto(false)
    }
  }

  // 답변 내역 조회
  const fetchResponseHistory = async () => {
    setIsLoadingHistory(true)

    try {
      const response = await fetch(`${apiBaseUrl}/responses/history?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setResponseHistory(data.responses || data || [])
      }
    } catch (err) {
      console.error('답변 내역 조회 실패:', err)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  // 특수 양식 상태 확인
  const checkSpecialFormStatus = async () => {
    if (!selectedAccountId) return null
    try {
      const response = await fetch(`${apiBaseUrl}/special-form/status/${selectedAccountId}`)
      if (response.ok) {
        const data = await response.json()
        setSpecialFormStatus(data)
        return data
      }
    } catch (error) {
      console.error('특수 양식 상태 확인 실패:', error)
    }
    return null
  }

  // 특수 양식 자동 처리
  const processSpecialForm = async (inquiry) => {
    const inquiryKey = inquiry.inquiryId || inquiry.inquiry_id

    // Wing 비밀번호 상태 확인
    const status = await checkSpecialFormStatus()
    if (!status?.can_process) {
      setError(`특수 양식 처리 불가: ${status?.message || 'Wing 로그인 정보가 필요합니다'}`)
      return
    }

    setProcessingSpecialForm(prev => ({ ...prev, [inquiryKey]: true }))
    addLog(`특수 양식 처리 시작: ${inquiryKey}`, 'info')

    try {
      const response = await fetch(`${apiBaseUrl}/special-form/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: selectedAccountId,
          inquiry_id: inquiryKey,
          inquiry_content: inquiry.content || inquiry.inquiryContent || '',
          customer_name: inquiry.customerName || '고객',
          special_reply_content: inquiry.special_reply_content || inquiry.content || '',
          special_link: inquiry.special_link,
          ai_response: inquiry.ai_response || inquiry.response_text,
          headless: true
        })
      })

      const data = await response.json()

      if (data.success) {
        addLog(`특수 양식 처리 완료: ${inquiryKey}`, 'success')
        // 결과에서 해당 항목 제거
        if (autoResult?.skipped_inquiries) {
          setAutoResult(prev => ({
            ...prev,
            skipped_inquiries: prev.skipped_inquiries.filter(i => (i.inquiryId || i.inquiry_id) !== inquiryKey),
            statistics: {
              ...prev.statistics,
              skipped: Math.max(0, (prev.statistics?.skipped || 0) - 1),
              answered: (prev.statistics?.answered || 0) + 1
            }
          }))
        }
      } else {
        addLog(`특수 양식 처리 실패: ${data.result?.error || '알 수 없는 오류'}`, 'error')
        setError(`특수 양식 처리 실패: ${data.result?.error || '알 수 없는 오류'}`)
      }
    } catch (error) {
      addLog(`오류: ${error.message}`, 'error')
      setError(`오류: ${error.message}`)
    } finally {
      setProcessingSpecialForm(prev => ({ ...prev, [inquiryKey]: false }))
    }
  }

  // 특수 양식 전체 처리
  const processAllSpecialForms = async () => {
    if (!autoResult?.skipped_inquiries?.length) return

    const status = await checkSpecialFormStatus()
    if (!status?.can_process) {
      setError(`특수 양식 처리 불가: ${status?.message || 'Wing 로그인 정보가 필요합니다'}`)
      return
    }

    addLog(`특수 양식 일괄 처리 시작: ${autoResult.skipped_inquiries.length}건`, 'info')

    for (const inquiry of autoResult.skipped_inquiries) {
      await processSpecialForm(inquiry)
      // 다음 처리 전 잠시 대기
      await new Promise(resolve => setTimeout(resolve, 2000))
    }

    addLog('특수 양식 일괄 처리 완료', 'success')
  }

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history' && connectionStatus === 'success') {
      fetchResponseHistory()
    }
  }, [activeTab])

  // 수동 답변 제출
  const submitManualResponse = async () => {
    if (!manualInquiry.response) {
      setError('답변 내용을 입력해주세요')
      return
    }

    addLog('수동 답변 제출 중...', 'info')

    try {
      // TODO: 실제 API 연동
      addLog('답변이 제출되었습니다', 'success')
      setManualInquiry({
        type: 'product',
        inquiryId: '',
        productName: '',
        customerQuestion: '',
        response: ''
      })
    } catch (err) {
      setError(`제출 오류: ${err.message}`)
    }
  }

  const tabs = [
    { id: 'inquiries', label: '문의 조회', icon: Search },
    { id: 'manual', label: '수동 입력', icon: Edit3 },
    { id: 'auto', label: '자동 답변', icon: Zap },
    { id: 'history', label: '답변 내역', icon: History }
  ]

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
          <p className="section-description">쿠팡 API 인증 정보를 등록하고 관리합니다.</p>

          {accounts.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: 'var(--text-primary)' }}>
                사용할 계정 선택:
              </label>
              <select
                value={selectedAccountId}
                onChange={(e) => selectAccount(e.target.value)}
                className="account-select"
                disabled={isRunningAuto || isTestingConnection}
              >
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} ({account.vendor_id})
                  </option>
                ))}
              </select>

              <button
                onClick={() => deleteAccount(selectedAccountId)}
                disabled={isRunningAuto || isTestingConnection}
                className="delete-account-btn"
              >
                선택된 계정 삭제
              </button>
            </div>
          )}

          {!showAddAccount && (
            <button
              onClick={() => setShowAddAccount(true)}
              disabled={isRunningAuto || isTestingConnection}
              className="add-account-btn"
            >
              + 새 계정 추가
            </button>
          )}

          {showAddAccount && (
            <div className="add-account-form">
              <h5>새 계정 추가</h5>
              <input type="text" placeholder="계정 이름" value={newAccountName} onChange={(e) => setNewAccountName(e.target.value)} />
              <input type="text" placeholder="업체코드 (Vendor ID)" value={newVendorId} onChange={(e) => setNewVendorId(e.target.value)} />
              <input type="text" placeholder="액세스 키" value={newAccessKey} onChange={(e) => setNewAccessKey(e.target.value)} />
              <input type="password" placeholder="시크릿 키" value={newSecretKey} onChange={(e) => setNewSecretKey(e.target.value)} />
              <input type="text" placeholder="Wing 사용자명 (선택)" value={newWingUsername} onChange={(e) => setNewWingUsername(e.target.value)} />
              <input type="password" placeholder="Wing 비밀번호 (선택)" value={newWingPassword} onChange={(e) => setNewWingPassword(e.target.value)} />
              <div className="form-actions">
                <button onClick={addAccount} className="save-btn">저장</button>
                <button onClick={() => { setShowAddAccount(false); setNewAccountName(''); setNewAccessKey(''); setNewSecretKey(''); setNewVendorId(''); setNewWingUsername(''); setNewWingPassword(''); }} className="cancel-btn">취소</button>
              </div>
            </div>
          )}
        </div>

        {/* 1단계: API 연결 테스트 */}
        <div className="login-section">
          <h4>1단계: Coupang API 연결 확인</h4>
          <p className="section-description">먼저 Coupang Open API와의 연결을 테스트합니다.</p>

          <button
            className={`test-login-button ${isTestingConnection ? 'testing' : ''} ${connectionStatus === 'success' ? 'success' : ''}`}
            onClick={testConnection}
            disabled={isRunningAuto || isTestingConnection}
          >
            {isTestingConnection ? (
              <><Loader size={20} className="spinner" /><span>API 연결 테스트 중...</span></>
            ) : connectionStatus === 'success' ? (
              <><CheckCircle size={20} /><span>API 연결 성공!</span></>
            ) : (
              <><Activity size={20} /><span>API 연결 테스트</span></>
            )}
          </button>

          {connectionStatus === 'success' && (
            <motion.div className="login-success-message" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
              <CheckCircle size={16} />
              <span>Coupang API 연결 성공! 이제 기능을 사용할 수 있습니다.</span>
            </motion.div>
          )}

          {connectionStatus === 'failed' && (
            <motion.div className="login-failed-message" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
              <XCircle size={16} />
              <span>API 연결 실패. 백엔드 서버를 확인해주세요.</span>
            </motion.div>
          )}
        </div>

        {/* 2단계: 기능 탭 */}
        <div className="function-tabs-section">
          <h4>2단계: 기능 선택</h4>

          {/* 탭 버튼 */}
          <div className="tab-buttons">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                disabled={connectionStatus !== 'success'}
              >
                <tab.icon size={18} />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* 문의 유형 선택 (조회, 자동답변 탭에서 표시) */}
          {(activeTab === 'inquiries' || activeTab === 'auto') && connectionStatus === 'success' && (
            <div className="inquiry-type-selector">
              <button
                className={`type-btn ${inquiryType === 'product' ? 'active' : ''}`}
                onClick={() => setInquiryType('product')}
              >
                <Package size={16} />
                <span>상품별 고객문의</span>
              </button>
              <button
                className={`type-btn ${inquiryType === 'callcenter' ? 'active' : ''}`}
                onClick={() => setInquiryType('callcenter')}
              >
                <Phone size={16} />
                <span>고객센터 문의</span>
              </button>
            </div>
          )}

          {/* 탭 컨텐츠 */}
          <div className="tab-content">
            {/* 문의 조회 탭 */}
            {activeTab === 'inquiries' && connectionStatus === 'success' && (
              <div className="inquiries-tab">
                <div className="inquiries-header">
                  <div className="filter-section">
                    <label>필터:</label>
                    <select value={inquiryFilter} onChange={(e) => setInquiryFilter(e.target.value)}>
                      <option value="NOANSWER">미답변</option>
                      <option value="ANSWER">답변완료</option>
                      <option value="ALL">전체</option>
                    </select>
                  </div>
                  <button
                    className="fetch-btn"
                    onClick={fetchInquiries}
                    disabled={isLoadingInquiries}
                  >
                    {isLoadingInquiries ? (
                      <><Loader size={16} className="spinner" /><span>조회 중...</span></>
                    ) : (
                      <><RefreshCw size={16} /><span>문의 조회</span></>
                    )}
                  </button>
                </div>

                <div className="inquiries-list">
                  {(inquiryType === 'product' ? inquiries : callCenterInquiries).length === 0 ? (
                    <div className="empty-state">
                      <Search size={48} />
                      <p>조회된 문의가 없습니다</p>
                      <span>위의 "문의 조회" 버튼을 클릭하세요</span>
                    </div>
                  ) : (
                    (inquiryType === 'product' ? inquiries : callCenterInquiries).map((inquiry, index) => (
                      <motion.div
                        key={inquiry.inquiryId || index}
                        className="inquiry-card"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div
                          className="inquiry-header"
                          onClick={() => setExpandedInquiry(expandedInquiry === index ? null : index)}
                        >
                          <div className="inquiry-info">
                            <span className={`status-badge ${inquiry.answered ? 'answered' : 'pending'}`}>
                              {inquiry.answered ? '답변완료' : '미답변'}
                            </span>
                            <span className="inquiry-id">#{inquiry.inquiryId || inquiry.vendorItemId}</span>
                            <span className="inquiry-date">
                              <Calendar size={14} />
                              {inquiry.inquiryAt || inquiry.createdAt}
                            </span>
                          </div>
                          {expandedInquiry === index ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </div>

                        {inquiry.productTitle && (
                          <div className="inquiry-product">
                            <Package size={14} />
                            <span>{inquiry.productTitle}</span>
                          </div>
                        )}

                        <div className="inquiry-question">
                          <MessageSquare size={14} />
                          <span>{inquiry.content || inquiry.inquiryContent || '문의 내용 없음'}</span>
                        </div>

                        <AnimatePresence>
                          {expandedInquiry === index && (
                            <motion.div
                              className="inquiry-details"
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                            >
                              {inquiry.answer && (
                                <div className="inquiry-answer">
                                  <strong>답변:</strong>
                                  <p>{inquiry.answer}</p>
                                </div>
                              )}
                              <div className="inquiry-actions">
                                <button className="action-btn view">
                                  <Eye size={14} />
                                  <span>상세보기</span>
                                </button>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* 수동 입력 탭 */}
            {activeTab === 'manual' && connectionStatus === 'success' && (
              <div className="manual-tab">
                <div className="manual-form">
                  <div className="form-group">
                    <label>문의 유형</label>
                    <select
                      value={manualInquiry.type}
                      onChange={(e) => setManualInquiry({ ...manualInquiry, type: e.target.value })}
                    >
                      <option value="product">상품별 고객문의</option>
                      <option value="callcenter">고객센터 문의</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>문의 ID (선택)</label>
                    <input
                      type="text"
                      placeholder="문의 ID 입력"
                      value={manualInquiry.inquiryId}
                      onChange={(e) => setManualInquiry({ ...manualInquiry, inquiryId: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label>상품명 (선택)</label>
                    <input
                      type="text"
                      placeholder="상품명 입력"
                      value={manualInquiry.productName}
                      onChange={(e) => setManualInquiry({ ...manualInquiry, productName: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label>고객 문의 내용</label>
                    <textarea
                      placeholder="고객이 문의한 내용을 입력하세요"
                      value={manualInquiry.customerQuestion}
                      onChange={(e) => setManualInquiry({ ...manualInquiry, customerQuestion: e.target.value })}
                      rows={4}
                    />
                  </div>

                  <div className="form-group">
                    <label>답변 내용</label>
                    <textarea
                      placeholder="답변 내용을 입력하세요"
                      value={manualInquiry.response}
                      onChange={(e) => setManualInquiry({ ...manualInquiry, response: e.target.value })}
                      rows={6}
                    />
                  </div>

                  <button className="submit-btn" onClick={submitManualResponse}>
                    <Send size={18} />
                    <span>답변 제출</span>
                  </button>
                </div>
              </div>
            )}

            {/* 자동 답변 탭 */}
            {activeTab === 'auto' && connectionStatus === 'success' && (
              <div className="auto-tab">
                <div className="auto-description">
                  <h5>AI 자동 답변</h5>
                  <p>ChatGPT를 사용하여 미답변 문의에 자동으로 답변합니다.</p>
                </div>

                <div className="auto-options">
                  <div className="option-card">
                    <Package size={24} />
                    <h6>상품별 고객문의</h6>
                    <p>미답변 상품 문의를 자동으로 조회하고 AI가 답변합니다.</p>
                    <ul>
                      <li>최근 7일 미답변 문의 조회</li>
                      <li>ChatGPT 답변 자동 생성</li>
                      <li>답변 자동 제출</li>
                    </ul>
                  </div>

                  <div className="option-card">
                    <Phone size={24} />
                    <h6>고객센터 문의</h6>
                    <p>고객센터 문의를 자동으로 처리합니다.</p>
                    <ul>
                      <li>미답변 문의 자동 조회</li>
                      <li>특수 케이스 자동 감지</li>
                      <li>AI 답변 생성 및 제출</li>
                    </ul>
                  </div>
                </div>

                <button
                  className={`run-auto-btn ${isRunningAuto ? 'running' : ''}`}
                  onClick={runAutoAnswer}
                  disabled={isRunningAuto}
                >
                  {isRunningAuto ? (
                    <><Loader size={20} className="spinner" /><span>자동 답변 실행 중...</span></>
                  ) : (
                    <><Zap size={20} /><span>{inquiryType === 'product' ? '상품별' : '고객센터'} 자동 답변 실행</span></>
                  )}
                </button>

                {autoResult && (
                  <motion.div className="auto-result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="result-header">
                      <CheckCircle size={24} />
                      <h5>자동 답변 완료!</h5>
                    </div>
                    <div className="result-stats">
                      <div className="stat">
                        <span className="label">총 문의</span>
                        <span className="value">{autoResult.statistics?.total_inquiries || 0}</span>
                      </div>
                      <div className="stat success">
                        <span className="label">답변 완료</span>
                        <span className="value">{autoResult.statistics?.answered || 0}</span>
                      </div>
                      <div className="stat error">
                        <span className="label">실패</span>
                        <span className="value">{autoResult.statistics?.failed || 0}</span>
                      </div>
                      <div
                        className={`stat ${(autoResult.statistics?.skipped || 0) > 0 ? 'clickable warning' : ''}`}
                        onClick={() => (autoResult.statistics?.skipped || 0) > 0 && setShowSkippedList(!showSkippedList)}
                        title={autoResult.statistics?.skipped > 0 ? '클릭하여 특수 양식 문의 확인' : ''}
                      >
                        <span className="label">건너뜀</span>
                        <span className="value">{autoResult.statistics?.skipped || 0}</span>
                      </div>
                    </div>

                    {/* 건너뜀(특수 양식) 문의 목록 */}
                    {showSkippedList && autoResult.skipped_inquiries?.length > 0 && (
                      <motion.div
                        className="skipped-inquiries-section"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                      >
                        <div className="skipped-header">
                          <h6>⚡ 특수 양식 문의 ({autoResult.skipped_inquiries.length}건)</h6>
                          <p>coupa.ng 링크 클릭이 필요한 문의입니다</p>
                          <button
                            className="process-all-btn"
                            onClick={processAllSpecialForms}
                            disabled={Object.values(processingSpecialForm).some(v => v)}
                          >
                            <Zap size={16} />
                            <span>전체 자동 처리</span>
                          </button>
                        </div>
                        <div className="skipped-list">
                          {autoResult.skipped_inquiries.map((inquiry, idx) => {
                            const inquiryKey = inquiry.inquiryId || inquiry.inquiry_id
                            const isProcessing = processingSpecialForm[inquiryKey]
                            return (
                              <div key={inquiryKey || idx} className="skipped-item">
                                <div className="skipped-item-info">
                                  <span className="inquiry-id">#{inquiryKey}</span>
                                  <span className="customer-name">{inquiry.customerName || inquiry.customer_name || '고객'}</span>
                                </div>
                                <div className="skipped-item-content">
                                  {(inquiry.content || inquiry.inquiryContent || '').substring(0, 100)}...
                                </div>
                                <div className="skipped-item-actions">
                                  <button
                                    className="special-form-btn"
                                    onClick={() => processSpecialForm(inquiry)}
                                    disabled={isProcessing}
                                  >
                                    {isProcessing ? (
                                      <><Loader size={14} className="spinner" /> 처리 중...</>
                                    ) : (
                                      <><Zap size={14} /> 특수 양식 자동 처리</>
                                    )}
                                  </button>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </div>
            )}

            {/* 답변 내역 탭 */}
            {activeTab === 'history' && connectionStatus === 'success' && (
              <div className="history-tab">
                <div className="history-header">
                  <h5>내 답변 내역</h5>
                  <button className="refresh-btn" onClick={fetchResponseHistory} disabled={isLoadingHistory}>
                    {isLoadingHistory ? <Loader size={16} className="spinner" /> : <RefreshCw size={16} />}
                    <span>새로고침</span>
                  </button>
                </div>

                <div className="history-list">
                  {responseHistory.length === 0 ? (
                    <div className="empty-state">
                      <History size={48} />
                      <p>답변 내역이 없습니다</p>
                    </div>
                  ) : (
                    responseHistory.map((item, index) => {
                      // 백엔드 응답 필드 매핑
                      const inquiryType = item.inquiry_type || item.type || 'callcenter'
                      const createdAt = item.created_at || item.createdAt || item.answeredAt
                      const productName = item.product_name || item.productName
                      const questionText = item.inquiry_text || item.question || item.inquiryContent || ''
                      const answerText = item.response_text || item.answer || item.response || ''
                      const statusValue = item.status || 'pending'
                      const customerName = item.customer_name || item.customerName || ''

                      // 날짜 포맷팅
                      const formatDate = (dateStr) => {
                        if (!dateStr) return ''
                        try {
                          const date = new Date(dateStr)
                          return date.toLocaleString('ko-KR', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        } catch {
                          return dateStr
                        }
                      }

                      return (
                        <motion.div
                          key={item.id || index}
                          className="history-card"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <div className="history-meta">
                            <span className={`type-badge ${inquiryType}`}>
                              {inquiryType === 'product' || inquiryType === 'online' ? '상품문의' : '고객센터'}
                            </span>
                            <span className="history-date">
                              <Clock size={14} />
                              {formatDate(createdAt)}
                            </span>
                            {customerName && (
                              <span className="customer-name">{customerName}</span>
                            )}
                          </div>
                          {productName && (
                            <div className="history-product">{productName}</div>
                          )}
                          <div className="history-question">
                            <strong>문의:</strong> {questionText || '(문의 내용 없음)'}
                          </div>
                          <div className="history-answer">
                            <strong>답변:</strong> {answerText || '(답변 없음)'}
                          </div>
                          <div className={`history-status ${statusValue === 'submitted' || statusValue === 'success' ? 'success' : statusValue}`}>
                            {(statusValue === 'submitted' || statusValue === 'success') ? <CheckCircle size={14} /> : <XCircle size={14} />}
                            <span>
                              {statusValue === 'submitted' || statusValue === 'success' ? '제출 완료' :
                               statusValue === 'pending' ? '대기 중' :
                               statusValue === 'approved' ? '승인됨' :
                               statusValue === 'failed' ? '실패' : statusValue}
                            </span>
                          </div>
                        </motion.div>
                      )
                    })
                  )}
                </div>
              </div>
            )}

            {/* 연결 안됨 상태 */}
            {connectionStatus !== 'success' && (
              <div className="not-connected">
                <Activity size={48} />
                <p>먼저 API 연결 테스트를 완료해주세요</p>
              </div>
            )}
          </div>
        </div>

        {/* 진행 로그 */}
        {progressLogs.length > 0 && (
          <motion.div className="progress-logs-container" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="progress-header">
              <h4>실행 로그</h4>
              <button className="clear-logs-btn" onClick={clearLogs}>지우기</button>
            </div>
            <div className="progress-logs">
              {progressLogs.map((log, index) => (
                <div key={index} className={`log-entry log-${log.type}`}>
                  <span className="log-timestamp">{log.timestamp}</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* 에러 표시 */}
        {error && (
          <motion.div className="result-box error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <XCircle size={24} />
            <span>{error}</span>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

export default CoupangWingAutomation
