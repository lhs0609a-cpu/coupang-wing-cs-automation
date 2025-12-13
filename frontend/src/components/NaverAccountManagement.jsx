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
  Star,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import '../styles/NaverAccountManagement.css'

const NaverAccountManagement = ({ apiBaseUrl, showNotification }) => {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    client_id: '',
    client_secret: '',
    callback_url: 'http://localhost:3000/naver/callback',
    naver_username: '',
    naver_password: '',
    is_default: false
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${apiBaseUrl}/naver-accounts`)
      setAccounts(response.data.data || [])
    } catch (error) {
      console.error('계정 목록 로드 실패:', error)
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
        await axios.put(`${apiBaseUrl}/naver-accounts/${editingAccount.id}`, formData)
        showNotification?.('네이버 계정이 수정되었습니다', 'success')
      } else {
        // 신규 생성
        await axios.post(`${apiBaseUrl}/naver-accounts`, formData)
        showNotification?.('네이버 계정이 등록되었습니다', 'success')
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
      description: account.description || '',
      client_id: account.client_id || '',
      client_secret: '', // 보안상 비워둠
      callback_url: account.callback_url || 'http://localhost:3000/naver/callback',
      naver_username: account.naver_username || '',
      naver_password: '', // 보안상 비워둠
      is_default: account.is_default || false
    })
    setShowForm(true)
  }

  const handleDelete = async (accountId) => {
    if (!confirm('정말 이 계정을 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/naver-accounts/${accountId}`)
      showNotification?.('네이버 계정이 삭제되었습니다', 'success')
      loadAccounts()
    } catch (error) {
      console.error('계정 삭제 실패:', error)
      showNotification?.('계정 삭제에 실패했습니다', 'error')
    }
  }

  const handleSetDefault = async (accountId) => {
    try {
      await axios.post(`${apiBaseUrl}/naver-accounts/${accountId}/set-default`)
      showNotification?.('기본 계정으로 설정되었습니다', 'success')
      loadAccounts()
    } catch (error) {
      console.error('기본 계정 설정 실패:', error)
      showNotification?.('기본 계정 설정에 실패했습니다', 'error')
    }
  }

  const handleTest = async (accountId) => {
    try {
      const response = await axios.post(`${apiBaseUrl}/naver-accounts/${accountId}/test`)
      if (response.data.success) {
        showNotification?.('네이버 계정 연결이 정상입니다', 'success')

        // 테스트 로그인 URL 새 창에서 열기
        if (response.data.test_login_url) {
          window.open(response.data.test_login_url, '_blank')
        }
      } else {
        showNotification?.(response.data.message || '연결 테스트에 실패했습니다', 'error')
      }
    } catch (error) {
      console.error('연결 테스트 실패:', error)
      showNotification?.('연결 테스트에 실패했습니다', 'error')
    }
  }

  const resetForm = () => {
    setShowForm(false)
    setEditingAccount(null)
    setFormData({
      name: '',
      description: '',
      client_id: '',
      client_secret: '',
      callback_url: 'http://localhost:3000/naver/callback',
      naver_username: '',
      naver_password: '',
      is_default: false
    })
  }

  return (
    <div className="naver-account-management">
      <div className="page-header">
        <div>
          <h1>네이버 계정 관리</h1>
          <p>네이버 API 계정을 등록하고 관리하세요</p>
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
                <h2>{editingAccount ? '네이버 계정 수정' : '네이버 계정 추가'}</h2>
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
                        placeholder="예: 기본 네이버 계정"
                        required
                      />
                    </div>

                    <div className="form-group full-width">
                      <label>설명</label>
                      <input
                        type="text"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="계정 설명 (선택사항)"
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3>네이버 API 인증 정보</h3>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Client ID *</label>
                      <input
                        type="text"
                        value={formData.client_id}
                        onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                        placeholder="네이버 개발자 센터에서 발급"
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label>Client Secret *</label>
                      <input
                        type="password"
                        value={formData.client_secret}
                        onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
                        placeholder={editingAccount ? '변경 시에만 입력' : '네이버 개발자 센터에서 발급'}
                        required={!editingAccount}
                      />
                    </div>

                    <div className="form-group full-width">
                      <label>Callback URL</label>
                      <input
                        type="text"
                        value={formData.callback_url}
                        onChange={(e) => setFormData({ ...formData, callback_url: e.target.value })}
                        placeholder="http://localhost:3000/naver/callback"
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3>네이버 로그인 정보 (선택사항)</h3>
                  <p className="form-help-text">Selenium 자동화에 사용됩니다</p>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>네이버 아이디</label>
                      <input
                        type="text"
                        value={formData.naver_username}
                        onChange={(e) => setFormData({ ...formData, naver_username: e.target.value })}
                        placeholder="선택사항"
                      />
                    </div>

                    <div className="form-group">
                      <label>네이버 비밀번호</label>
                      <input
                        type="password"
                        value={formData.naver_password}
                        onChange={(e) => setFormData({ ...formData, naver_password: e.target.value })}
                        placeholder={editingAccount ? '변경 시에만 입력' : '선택사항'}
                      />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_default}
                      onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                    />
                    <span>기본 계정으로 설정</span>
                  </label>
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
            <Key size={64} />
            <h3>등록된 네이버 계정이 없습니다</h3>
            <p>네이버 API를 사용하려면 계정을 먼저 등록해주세요</p>
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
                  {account.is_default && (
                    <span className="badge badge-primary">
                      <Star size={14} />
                      <span>기본</span>
                    </span>
                  )}
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
                    onClick={() => handleTest(account.id)}
                    title="연결 테스트"
                  >
                    <ExternalLink size={18} />
                  </button>
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

              {account.description && (
                <p className="account-description">{account.description}</p>
              )}

              <div className="account-info">
                <div className="info-row">
                  <span className="info-label">Client ID:</span>
                  <span className="info-value">{account.client_id}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Callback URL:</span>
                  <span className="info-value">{account.callback_url}</span>
                </div>
                {account.naver_username && (
                  <div className="info-row">
                    <span className="info-label">네이버 ID:</span>
                    <span className="info-value">{account.naver_username}</span>
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
              </div>

              {!account.is_default && (
                <button
                  className="btn-set-default"
                  onClick={() => handleSetDefault(account.id)}
                >
                  <Star size={16} />
                  <span>기본 계정으로 설정</span>
                </button>
              )}
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}

export default NaverAccountManagement
