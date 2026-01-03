import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Edit,
  Trash2,
  Check,
  X,
  Key,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  ShoppingBag
} from 'lucide-react'
import TutorialButton from './TutorialButton'
import '../styles/NaverAccountManagement.css'

const CoupangAccountManagement = ({ apiBaseUrl, showNotification }) => {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    vendor_id: '',
    access_key: '',
    secret_key: '',
    wing_username: '',
    wing_password: ''
  })

  // apiBaseUrl이 변경되거나 컴포넌트가 마운트될 때 계정 로드
  useEffect(() => {
    if (apiBaseUrl) {
      console.log('CoupangAccountManagement mounted with apiBaseUrl:', apiBaseUrl)
      loadAccounts()
    } else {
      console.warn('apiBaseUrl이 없습니다!')
    }
  }, [apiBaseUrl])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      console.log('쿠팡 계정 로드 시작:', `${apiBaseUrl}/coupang-accounts`)
      const response = await axios.get(`${apiBaseUrl}/coupang-accounts`)
      console.log('쿠팡 계정 API 응답:', response.data)
      console.log('응답 타입:', typeof response.data, Array.isArray(response.data))
      setAccounts(response.data || [])
      console.log('설정된 계정 수:', (response.data || []).length)
    } catch (error) {
      console.error('계정 목록 로드 실패:', error)
      console.error('에러 상세:', error.response?.status, error.response?.data)
      showNotification?.('계정 목록을 불러오는데 실패했습니다', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      if (editingAccount) {
        // 수정
        await axios.put(`${apiBaseUrl}/coupang-accounts/${editingAccount.id}`, formData)
        showNotification?.('쿠팡 계정이 수정되었습니다', 'success')
      } else {
        // 신규 생성
        await axios.post(`${apiBaseUrl}/coupang-accounts`, formData)
        showNotification?.('쿠팡 계정이 등록되었습니다', 'success')
      }

      resetForm()
      loadAccounts()
    } catch (error) {
      console.error('계정 저장 실패:', error)
      showNotification?.('계정 저장에 실패했습니다', 'error')
    }
  }

  const handleEdit = (account) => {
    setEditingAccount(account)
    setFormData({
      name: account.name || '',
      vendor_id: account.vendor_id || '',
      access_key: account.access_key || '', // 현재 값 표시
      secret_key: account.secret_key || '', // 현재 값 표시
      wing_username: account.wing_username || '',
      wing_password: account.wing_password || '' // 현재 값 표시
    })
    setShowForm(true)
  }

  const handleDelete = async (accountId) => {
    if (!confirm('정말 이 계정을 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/coupang-accounts/${accountId}`)
      showNotification?.('쿠팡 계정이 삭제되었습니다', 'success')
      loadAccounts()
    } catch (error) {
      console.error('계정 삭제 실패:', error)
      showNotification?.('계정 삭제에 실패했습니다', 'error')
    }
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingAccount(null)
    setFormData({
      name: '',
      vendor_id: '',
      access_key: '',
      secret_key: '',
      wing_username: '',
      wing_password: ''
    })
  }

  return (
    <div className="naver-account-management">
      <div className="page-header">
        <div>
          <h1>쿠팡 계정 관리</h1>
          <p>쿠팡 윙 API 계정을 등록하고 관리하세요</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm(true)}
        >
          <Plus size={20} />
          <span>계정 추가</span>
        </button>
      </div>

      {/* 등록 폼 */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            className="form-modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={resetForm}
          >
            <motion.div
              className="form-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="form-modal-header">
                <h2>{editingAccount ? '쿠팡 계정 수정' : '쿠팡 계정 추가'}</h2>
                <button className="btn-icon" onClick={resetForm}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="naver-account-form">
                <div className="form-section">
                  <h3>기본 정보</h3>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>계정 이름 *</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="예: 기본 쿠팡 계정"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>Vendor ID *</label>
                      <input
                        type="text"
                        value={formData.vendor_id}
                        onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                        placeholder="쿠팡 윙 Vendor ID"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3>쿠팡 API 인증 정보</h3>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Access Key *</label>
                      <input
                        type="text"
                        value={formData.access_key}
                        onChange={(e) => setFormData({ ...formData, access_key: e.target.value })}
                        placeholder={editingAccount ? '변경 시에만 입력' : '쿠팡 API Access Key'}
                        required={!editingAccount}
                      />
                    </div>

                    <div className="form-group">
                      <label>Secret Key *</label>
                      <input
                        type="text"
                        value={formData.secret_key}
                        onChange={(e) => setFormData({ ...formData, secret_key: e.target.value })}
                        placeholder={editingAccount ? '변경 시에만 입력' : '쿠팡 API Secret Key'}
                        required={!editingAccount}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3>쿠팡 윙 로그인 정보</h3>
                  <p className="form-help-text">웹 자동화에 사용됩니다</p>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>쿠팡 윙 아이디 *</label>
                      <input
                        type="text"
                        value={formData.wing_username}
                        onChange={(e) => setFormData({ ...formData, wing_username: e.target.value })}
                        placeholder="쿠팡 윙 로그인 아이디"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>쿠팡 윙 비밀번호 *</label>
                      <input
                        type="text"
                        value={formData.wing_password}
                        onChange={(e) => setFormData({ ...formData, wing_password: e.target.value })}
                        placeholder={editingAccount ? '변경 시에만 입력' : '쿠팡 윙 로그인 비밀번호'}
                        required={!editingAccount}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-actions">
                  <button type="button" className="btn-secondary" onClick={resetForm}>
                    취소
                  </button>
                  <button type="submit" className="btn-primary">
                    <Check size={20} />
                    <span>{editingAccount ? '수정' : '등록'}</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 계정 목록 */}
      <div className="accounts-grid">
        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>계정 목록을 불러오는 중...</p>
          </div>
        ) : accounts.length === 0 ? (
          <div className="empty-state">
            <ShoppingBag size={64} />
            <h3>등록된 쿠팡 계정이 없습니다</h3>
            <p>쿠팡 윙 API를 사용하려면 계정을 먼저 등록해주세요</p>
            <button className="btn-primary" onClick={() => setShowForm(true)}>
              <Plus size={20} />
              <span>첫 계정 추가하기</span>
            </button>
          </div>
        ) : (
          accounts.map((account) => (
            <motion.div
              key={account.id}
              className="account-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="account-card-header">
                <div className="account-title">
                  <h3>{account.name}</h3>
                  {account.is_active ? (
                    <span className="badge badge-success">
                      <CheckCircle size={14} />
                      <span>활성</span>
                    </span>
                  ) : (
                    <span className="badge badge-inactive">
                      <AlertCircle size={14} />
                      <span>비활성</span>
                    </span>
                  )}
                </div>
                <div className="account-actions">
                  <button
                    className="btn-icon"
                    onClick={() => handleEdit(account)}
                    title="수정"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    className="btn-icon btn-danger"
                    onClick={() => handleDelete(account.id)}
                    title="삭제"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="account-info">
                <div className="info-row">
                  <span className="info-label">Vendor ID:</span>
                  <span className="info-value">{account.vendor_id}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Access Key:</span>
                  <span className={`info-value ${!account.access_key ? 'text-danger' : ''}`}>
                    {account.access_key
                      ? `${account.access_key.substring(0, 12)}...${account.access_key.substring(account.access_key.length - 4)}`
                      : '⚠️ 미설정'}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Secret Key:</span>
                  <span className={`info-value ${!account.secret_key ? 'text-danger' : ''}`}>
                    {account.secret_key
                      ? `${account.secret_key.substring(0, 8)}...${account.secret_key.substring(account.secret_key.length - 4)}`
                      : '⚠️ 미설정'}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">윙 아이디:</span>
                  <span className="info-value">{account.wing_username}</span>
                </div>
                {(!account.access_key || !account.secret_key) && (
                  <div className="info-row" style={{ marginTop: '8px' }}>
                    <span className="badge badge-warning" style={{ backgroundColor: '#ff6b6b', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '12px' }}>
                      ⚠️ API 키가 없습니다. 수정 버튼을 눌러 입력해주세요.
                    </span>
                  </div>
                )}
                {account.last_used_at && (
                  <div className="info-row">
                    <span className="info-label">마지막 사용:</span>
                    <span className="info-value">
                      {new Date(account.last_used_at).toLocaleString('ko-KR')}
                    </span>
                  </div>
                )}
                <div className="info-row">
                  <span className="info-label">생성일:</span>
                  <span className="info-value">
                    {new Date(account.created_at).toLocaleString('ko-KR')}
                  </span>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* 플로팅 튜토리얼 버튼 */}
      <TutorialButton tabId="coupang-accounts" variant="floating" />
    </div>
  )
}

export default CoupangAccountManagement
