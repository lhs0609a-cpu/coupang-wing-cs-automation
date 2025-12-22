import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Truck,
  RefreshCw,
  Play,
  ArrowRight,
  Upload,
  Copy,
  ExternalLink,
  Package,
  User,
  LogIn,
  LogOut,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Link2,
  Unlink,
  BarChart3,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
  Zap,
  HelpCircle
} from 'lucide-react'
import TutorialButton from './TutorialButton'
import '../styles/NaverDeliverySync.css'

const NaverDeliverySync = ({ apiBaseUrl, showNotification }) => {
  // 상태 관리
  const [deliveries, setDeliveries] = useState([])
  const [coupangOrders, setCoupangOrders] = useState([])
  const [stats, setStats] = useState({ total: 0, pending: 0, matched: 0, uploaded: 0, failed: 0 })
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [loginStatus, setLoginStatus] = useState({ is_logged_in: false, username: null })

  // 쿠팡 계정
  const [coupangAccounts, setCoupangAccounts] = useState([])
  const [selectedCoupangAccount, setSelectedCoupangAccount] = useState(null)

  // 필터
  const [statusFilter, setStatusFilter] = useState('')

  // 로그인 모달
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [loginCredentials, setLoginCredentials] = useState({ username: '', password: '' })
  const [loginLoading, setLoginLoading] = useState(false)

  // 동기화 진행 상태
  const [syncProgress, setSyncProgress] = useState([])
  const [syncStats, setSyncStats] = useState({ collected: 0, matched: 0, uploaded: 0 })

  // 수동 매칭 모달
  const [showMatchModal, setShowMatchModal] = useState(false)
  const [matchingDelivery, setMatchingDelivery] = useState(null)
  const [selectedOrder, setSelectedOrder] = useState(null)

  // 탭 관리
  const [activeTab, setActiveTab] = useState('sync') // 'sync' | 'deliveries' | 'orders'

  // 확장된 행
  const [expandedRows, setExpandedRows] = useState(new Set())

  // 초기 로드
  useEffect(() => {
    loadCoupangAccounts()
    checkLoginStatus()
    loadStats()
  }, [])

  useEffect(() => {
    if (selectedCoupangAccount) {
      loadDeliveries()
      loadCoupangOrders()
    }
  }, [selectedCoupangAccount, statusFilter])

  // API 호출 함수들
  const checkLoginStatus = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/delivery-sync/debug/naver-login-status`)
      setLoginStatus(res.data)
    } catch (error) {
      console.error('로그인 상태 확인 실패:', error)
    }
  }

  const loadCoupangAccounts = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/coupang-accounts`)
      setCoupangAccounts(res.data)
      if (res.data.length > 0 && !selectedCoupangAccount) {
        setSelectedCoupangAccount(res.data[0].id)
      }
    } catch (error) {
      console.error('쿠팡 계정 로드 실패:', error)
    }
  }

  const loadDeliveries = async () => {
    try {
      setLoading(true)
      const params = {}
      if (statusFilter) params.status = statusFilter

      const res = await axios.get(`${apiBaseUrl}/delivery-sync/deliveries`, { params })
      setDeliveries(res.data)
    } catch (error) {
      console.error('배송 정보 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCoupangOrders = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/delivery-sync/coupang/pending-orders`, {
        params: { only_unuploaded: true }
      })
      setCoupangOrders(res.data)
    } catch (error) {
      console.error('쿠팡 발주서 로드 실패:', error)
    }
  }

  const loadStats = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/delivery-sync/stats`)
      setStats(res.data)
    } catch (error) {
      console.error('통계 로드 실패:', error)
    }
  }

  const fetchCoupangOrders = async () => {
    if (!selectedCoupangAccount) {
      showNotification('쿠팡 계정을 선택해주세요', 'error')
      return
    }

    try {
      setLoading(true)
      const res = await axios.post(`${apiBaseUrl}/delivery-sync/coupang/fetch-orders`, {
        coupang_account_id: selectedCoupangAccount,
        hours_back: 24
      })

      if (res.data.success) {
        showNotification(`쿠팡 발주서 ${res.data.count}건 조회됨`, 'success')
        loadCoupangOrders()
      }
    } catch (error) {
      showNotification('쿠팡 발주서 조회 실패', 'error')
    } finally {
      setLoading(false)
    }
  }

  // 로그인 처리
  const handleLogin = async () => {
    if (!loginCredentials.username || !loginCredentials.password) {
      showNotification('아이디와 비밀번호를 입력해주세요', 'error')
      return
    }

    try {
      setLoginLoading(true)
      const res = await axios.post(`${apiBaseUrl}/naverpay/login`, loginCredentials)

      if (res.data.success) {
        setLoginStatus({ is_logged_in: true, username: res.data.username })
        setShowLoginModal(false)
        showNotification('네이버 로그인 성공', 'success')
        setLoginCredentials({ username: '', password: '' })
      } else {
        showNotification(res.data.message || '로그인 실패', 'error')
      }
    } catch (error) {
      showNotification('로그인 중 오류가 발생했습니다', 'error')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await axios.post(`${apiBaseUrl}/naverpay/logout`)
      setLoginStatus({ is_logged_in: false, username: null })
      showNotification('로그아웃 되었습니다', 'success')
    } catch (error) {
      showNotification('로그아웃 실패', 'error')
    }
  }

  // 동기화 실행 (SSE 스트리밍)
  const handleSync = async (autoUpload = false) => {
    if (!loginStatus.is_logged_in) {
      showNotification('먼저 네이버에 로그인해주세요', 'error')
      setShowLoginModal(true)
      return
    }

    if (!selectedCoupangAccount) {
      showNotification('쿠팡 계정을 선택해주세요', 'error')
      return
    }

    try {
      setSyncing(true)
      setSyncProgress([])
      setSyncStats({ collected: 0, matched: 0, uploaded: 0 })

      const response = await fetch(`${apiBaseUrl}/delivery-sync/sync/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          auto_upload: autoUpload,
          coupang_account_id: selectedCoupangAccount
        })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(line => line.startsWith('data: '))

        for (const line of lines) {
          try {
            const data = JSON.parse(line.substring(6))
            handleSyncEvent(data)
          } catch (e) {
            console.error('SSE 파싱 오류:', e)
          }
        }
      }

      loadDeliveries()
      loadCoupangOrders()
      loadStats()

    } catch (error) {
      showNotification('동기화 중 오류가 발생했습니다', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const handleSyncEvent = (data) => {
    setSyncProgress(prev => [...prev, data])

    switch (data.type) {
      case 'delivery':
        setSyncStats(prev => ({ ...prev, collected: prev.collected + 1 }))
        break
      case 'matched':
        setSyncStats(prev => ({ ...prev, matched: prev.matched + 1 }))
        break
      case 'uploaded':
        if (data.data?.success) {
          setSyncStats(prev => ({ ...prev, uploaded: prev.uploaded + 1 }))
        }
        break
      case 'complete':
        showNotification(
          `동기화 완료: ${data.data.collected}건 수집, ${data.data.matched}건 매칭, ${data.data.uploaded}건 업로드`,
          'success'
        )
        break
      case 'error':
        showNotification(data.message, 'error')
        break
    }
  }

  // 수동 매칭
  const openMatchModal = (delivery) => {
    setMatchingDelivery(delivery)
    setSelectedOrder(null)
    setShowMatchModal(true)
  }

  const handleManualMatch = async () => {
    if (!matchingDelivery || !selectedOrder) {
      showNotification('매칭할 주문을 선택해주세요', 'error')
      return
    }

    try {
      const res = await axios.post(`${apiBaseUrl}/delivery-sync/manual/match`, {
        delivery_id: matchingDelivery.id,
        shipment_box_id: selectedOrder.shipment_box_id,
        order_id: selectedOrder.order_id,
        vendor_item_id: selectedOrder.vendor_item_id
      })

      if (res.data.success) {
        showNotification('매칭 완료', 'success')
        setShowMatchModal(false)
        loadDeliveries()
        loadStats()
      }
    } catch (error) {
      showNotification('매칭 실패', 'error')
    }
  }

  // 수동 업로드
  const handleManualUpload = async (deliveryId) => {
    if (!selectedCoupangAccount) {
      showNotification('쿠팡 계정을 선택해주세요', 'error')
      return
    }

    try {
      const res = await axios.post(
        `${apiBaseUrl}/delivery-sync/manual/upload?coupang_account_id=${selectedCoupangAccount}`,
        { delivery_id: deliveryId }
      )

      if (res.data.success) {
        showNotification('송장 업로드 완료', 'success')
        loadDeliveries()
        loadStats()
      } else {
        showNotification(res.data.error || '업로드 실패', 'error')
      }
    } catch (error) {
      showNotification('송장 업로드 실패', 'error')
    }
  }

  // 일괄 업로드
  const handleBulkUpload = async () => {
    const matchedDeliveries = deliveries.filter(d => d.status === 'matched')
    if (matchedDeliveries.length === 0) {
      showNotification('업로드할 매칭된 배송 정보가 없습니다', 'error')
      return
    }

    try {
      const res = await axios.post(
        `${apiBaseUrl}/delivery-sync/manual/bulk-upload?coupang_account_id=${selectedCoupangAccount}`,
        matchedDeliveries.map(d => d.id)
      )

      showNotification(
        `업로드 완료: 성공 ${res.data.success}건, 실패 ${res.data.failed}건`,
        res.data.failed > 0 ? 'warning' : 'success'
      )
      loadDeliveries()
      loadStats()
    } catch (error) {
      showNotification('일괄 업로드 실패', 'error')
    }
  }

  // 클립보드 복사
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    showNotification('클립보드에 복사되었습니다', 'success')
  }

  // 행 확장 토글
  const toggleRow = (id) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  // 상태 뱃지 렌더링
  const renderStatusBadge = (status) => {
    const statusConfig = {
      pending: { icon: Clock, color: 'yellow', text: '대기중' },
      matched: { icon: Link2, color: 'blue', text: '매칭됨' },
      uploaded: { icon: CheckCircle, color: 'green', text: '업로드완료' },
      failed: { icon: XCircle, color: 'red', text: '실패' }
    }

    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon

    return (
      <span className={`status-badge ${config.color}`}>
        <Icon size={14} />
        {config.text}
      </span>
    )
  }

  return (
    <div className="naver-delivery-sync">
      {/* 헤더 */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <div className="title-icon">
              <Truck size={28} />
              <ArrowRight size={20} />
              <Package size={28} />
            </div>
            <div>
              <h1>배송 정보 동기화</h1>
              <p>네이버 배송 정보를 쿠팡 송장으로 자동 등록합니다</p>
            </div>
          </div>

          <div className="header-actions">
            {/* 쿠팡 계정 선택 */}
            <select
              className="account-select"
              value={selectedCoupangAccount || ''}
              onChange={(e) => setSelectedCoupangAccount(parseInt(e.target.value))}
            >
              <option value="">쿠팡 계정 선택</option>
              {coupangAccounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.store_name || acc.vendor_id}</option>
              ))}
            </select>

            {/* 네이버 로그인 상태 */}
            {loginStatus.is_logged_in ? (
              <>
                <div className="login-status connected">
                  <CheckCircle size={16} />
                  <span>{loginStatus.username}</span>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                  <LogOut size={16} />
                </button>
              </>
            ) : (
              <button className="btn btn-outline" onClick={() => setShowLoginModal(true)}>
                <LogIn size={18} />
                네이버 로그인
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 튜토리얼 배너 */}
      <TutorialButton tabId="delivery-sync" variant="banner" />

      {/* 통계 카드 */}
      <div className="stats-grid">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-icon total">
            <Package size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">전체</span>
            <span className="stat-value">{stats.total}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="stat-icon pending">
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">대기중</span>
            <span className="stat-value">{stats.pending}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="stat-icon matched">
            <Link2 size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">매칭됨</span>
            <span className="stat-value">{stats.matched}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className="stat-icon uploaded">
            <CheckCircle size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">업로드완료</span>
            <span className="stat-value">{stats.uploaded}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="stat-icon failed">
            <XCircle size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">실패</span>
            <span className="stat-value">{stats.failed}</span>
          </div>
        </motion.div>
      </div>

      {/* 동기화 버튼 영역 */}
      <div className="sync-actions">
        <div className="sync-buttons">
          <button
            className="btn btn-primary btn-lg"
            onClick={() => handleSync(false)}
            disabled={syncing || !loginStatus.is_logged_in || !selectedCoupangAccount}
          >
            {syncing ? (
              <>
                <RefreshCw size={20} className="spin" />
                동기화 중...
              </>
            ) : (
              <>
                <Play size={20} />
                수집 및 매칭
              </>
            )}
          </button>

          <button
            className="btn btn-success btn-lg"
            onClick={() => handleSync(true)}
            disabled={syncing || !loginStatus.is_logged_in || !selectedCoupangAccount}
          >
            <Zap size={20} />
            자동 업로드
          </button>

          <button
            className="btn btn-secondary"
            onClick={handleBulkUpload}
            disabled={syncing || !selectedCoupangAccount}
          >
            <Upload size={18} />
            매칭건 일괄 업로드
          </button>

          <button
            className="btn btn-outline"
            onClick={fetchCoupangOrders}
            disabled={loading || !selectedCoupangAccount}
          >
            <RefreshCw size={18} />
            쿠팡 발주서 새로고침
          </button>
        </div>

        {/* 동기화 진행 상태 */}
        {syncing && (
          <div className="sync-progress">
            <div className="progress-stats">
              <span>수집: {syncStats.collected}건</span>
              <span>매칭: {syncStats.matched}건</span>
              <span>업로드: {syncStats.uploaded}건</span>
            </div>
            <div className="progress-messages">
              {syncProgress.slice(-3).map((p, i) => (
                <div key={i} className={`progress-item ${p.type}`}>
                  {p.type === 'status' && p.message}
                  {p.type === 'delivery' && `배송 수집: ${p.data?.recipient}`}
                  {p.type === 'matched' && `매칭: ${p.data?.naver_recipient} → ${p.data?.coupang_recipient}`}
                  {p.type === 'uploaded' && `업로드: ${p.data?.tracking_number}`}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'sync' ? 'active' : ''}`}
          onClick={() => setActiveTab('sync')}
        >
          <Link2 size={18} />
          동기화 현황
        </button>
        <button
          className={`tab-btn ${activeTab === 'deliveries' ? 'active' : ''}`}
          onClick={() => setActiveTab('deliveries')}
        >
          <Truck size={18} />
          네이버 배송 ({deliveries.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          <Package size={18} />
          쿠팡 발주서 ({coupangOrders.length})
        </button>
      </div>

      {/* 동기화 현황 탭 */}
      {activeTab === 'sync' && (
        <div className="sync-overview">
          {/* 필터 */}
          <div className="filter-bar">
            <div className="filters">
              <div className="filter-group">
                <label><Filter size={16} /> 상태</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">전체</option>
                  <option value="pending">대기중</option>
                  <option value="matched">매칭됨</option>
                  <option value="uploaded">업로드완료</option>
                  <option value="failed">실패</option>
                </select>
              </div>
            </div>
            <button className="btn btn-secondary" onClick={loadDeliveries}>
              <RefreshCw size={16} />
              새로고침
            </button>
          </div>

          {/* 배송 목록 */}
          <div className="delivery-list">
            {loading ? (
              <div className="loading-state">
                <RefreshCw size={32} className="spin" />
                <p>로딩 중...</p>
              </div>
            ) : deliveries.length === 0 ? (
              <div className="empty-state">
                <Truck size={48} />
                <h3>배송 정보가 없습니다</h3>
                <p>동기화 버튼을 눌러 배송 정보를 수집하세요</p>
              </div>
            ) : (
              <div className="delivery-cards">
                {deliveries.map((delivery, index) => (
                  <motion.div
                    key={delivery.id}
                    className={`delivery-card ${delivery.status}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                  >
                    <div className="card-header" onClick={() => toggleRow(delivery.id)}>
                      <div className="card-main-info">
                        <div className="recipient-info">
                          <User size={18} />
                          <span className="recipient-name">{delivery.receiver_name}</span>
                        </div>
                        <div className="tracking-info">
                          <span className="courier">{delivery.courier_name}</span>
                          <code className="tracking-number">{delivery.tracking_number}</code>
                          <button
                            className="icon-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              copyToClipboard(delivery.tracking_number)
                            }}
                          >
                            <Copy size={14} />
                          </button>
                        </div>
                      </div>
                      <div className="card-status">
                        {renderStatusBadge(delivery.status)}
                        {expandedRows.has(delivery.id) ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </div>
                    </div>

                    <AnimatePresence>
                      {expandedRows.has(delivery.id) && (
                        <motion.div
                          className="card-details"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                        >
                          <div className="detail-grid">
                            <div className="detail-item">
                              <span className="label">상품명</span>
                              <span className="value">{delivery.product_name || '-'}</span>
                            </div>
                            <div className="detail-item">
                              <span className="label">수집 시간</span>
                              <span className="value">
                                {delivery.collected_at ? new Date(delivery.collected_at).toLocaleString('ko-KR') : '-'}
                              </span>
                            </div>
                            {delivery.is_matched && (
                              <>
                                <div className="detail-item">
                                  <span className="label">쿠팡 주문번호</span>
                                  <span className="value">{delivery.coupang_order_id || '-'}</span>
                                </div>
                                <div className="detail-item">
                                  <span className="label">매칭 신뢰도</span>
                                  <span className="value">{delivery.match_confidence}%</span>
                                </div>
                              </>
                            )}
                            {delivery.error_message && (
                              <div className="detail-item full-width error">
                                <span className="label">오류</span>
                                <span className="value">{delivery.error_message}</span>
                              </div>
                            )}
                          </div>

                          <div className="card-actions">
                            {delivery.status === 'pending' && (
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() => openMatchModal(delivery)}
                              >
                                <Link2 size={16} />
                                수동 매칭
                              </button>
                            )}
                            {delivery.status === 'matched' && (
                              <button
                                className="btn btn-success btn-sm"
                                onClick={() => handleManualUpload(delivery.id)}
                              >
                                <Upload size={16} />
                                송장 업로드
                              </button>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 네이버 배송 탭 */}
      {activeTab === 'deliveries' && (
        <div className="deliveries-section">
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>수령인</th>
                  <th>택배사</th>
                  <th>송장번호</th>
                  <th>상품명</th>
                  <th>상태</th>
                  <th>수집 시간</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map(d => (
                  <tr key={d.id}>
                    <td>
                      <div className="cell-with-icon">
                        <User size={16} />
                        {d.receiver_name}
                      </div>
                    </td>
                    <td><span className="courier-badge">{d.courier_name}</span></td>
                    <td>
                      <code>{d.tracking_number}</code>
                      <button className="icon-btn" onClick={() => copyToClipboard(d.tracking_number)}>
                        <Copy size={14} />
                      </button>
                    </td>
                    <td className="truncate">{d.product_name || '-'}</td>
                    <td>{renderStatusBadge(d.status)}</td>
                    <td>{d.collected_at ? new Date(d.collected_at).toLocaleString('ko-KR') : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 쿠팡 발주서 탭 */}
      {activeTab === 'orders' && (
        <div className="orders-section">
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>수령인</th>
                  <th>주문번호</th>
                  <th>상품명</th>
                  <th>주문시간</th>
                  <th>송장등록</th>
                </tr>
              </thead>
              <tbody>
                {coupangOrders.map(o => (
                  <tr key={o.id}>
                    <td>
                      <div className="cell-with-icon">
                        <User size={16} />
                        {o.receiver_name}
                      </div>
                    </td>
                    <td><code>{o.order_id}</code></td>
                    <td className="truncate">{o.product_name || '-'}</td>
                    <td>{o.ordered_at ? new Date(o.ordered_at).toLocaleString('ko-KR') : '-'}</td>
                    <td>
                      {o.is_invoice_uploaded ? (
                        <span className="status-badge green">
                          <CheckCircle size={14} />
                          완료
                        </span>
                      ) : (
                        <span className="status-badge yellow">
                          <Clock size={14} />
                          대기
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 수동 매칭 모달 */}
      <AnimatePresence>
        {showMatchModal && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowMatchModal(false)}
          >
            <motion.div
              className="modal-content modal-lg"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2><Link2 size={24} /> 수동 매칭</h2>

              {matchingDelivery && (
                <div className="matching-info">
                  <h4>네이버 배송 정보</h4>
                  <div className="info-card">
                    <div><strong>수령인:</strong> {matchingDelivery.receiver_name}</div>
                    <div><strong>택배사:</strong> {matchingDelivery.courier_name}</div>
                    <div><strong>송장번호:</strong> {matchingDelivery.tracking_number}</div>
                  </div>
                </div>
              )}

              <div className="matching-orders">
                <h4>쿠팡 발주서 선택</h4>
                {coupangOrders.length === 0 ? (
                  <div className="empty-state small">
                    <p>발주서가 없습니다</p>
                  </div>
                ) : (
                  <div className="order-list">
                    {coupangOrders.map(order => (
                      <div
                        key={order.id}
                        className={`order-item ${selectedOrder?.id === order.id ? 'selected' : ''}`}
                        onClick={() => setSelectedOrder(order)}
                      >
                        <div className="order-info">
                          <span className="order-recipient">{order.receiver_name}</span>
                          <span className="order-product">{order.product_name}</span>
                        </div>
                        <code className="order-id">{order.order_id}</code>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={() => setShowMatchModal(false)}>
                  취소
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleManualMatch}
                  disabled={!selectedOrder}
                >
                  <Link2 size={18} />
                  매칭하기
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 로그인 모달 */}
      <AnimatePresence>
        {showLoginModal && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowLoginModal(false)}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2><LogIn size={24} /> 네이버 로그인</h2>
              <p className="modal-desc">배송 정보를 수집하려면 네이버 로그인이 필요합니다</p>

              <div className="form-group">
                <label>네이버 아이디</label>
                <input
                  type="text"
                  value={loginCredentials.username}
                  onChange={(e) => setLoginCredentials(prev => ({ ...prev, username: e.target.value }))}
                  placeholder="아이디 입력"
                />
              </div>

              <div className="form-group">
                <label>비밀번호</label>
                <input
                  type="password"
                  value={loginCredentials.password}
                  onChange={(e) => setLoginCredentials(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="비밀번호 입력"
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                />
              </div>

              <div className="modal-actions">
                <button className="btn btn-secondary" onClick={() => setShowLoginModal(false)}>
                  취소
                </button>
                <button className="btn btn-primary" onClick={handleLogin} disabled={loginLoading}>
                  {loginLoading ? (
                    <>
                      <RefreshCw size={18} className="spin" />
                      로그인 중...
                    </>
                  ) : (
                    <>
                      <LogIn size={18} />
                      로그인
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 플로팅 튜토리얼 버튼 */}
      <TutorialButton tabId="delivery-sync" variant="floating" />
    </div>
  )
}

export default NaverDeliverySync
