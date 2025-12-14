import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Truck,
  RefreshCw,
  Play,
  Download,
  Copy,
  ExternalLink,
  Calendar,
  Package,
  User,
  LogIn,
  LogOut,
  Clock,
  CheckCircle,
  XCircle,
  Search,
  Filter,
  Trash2,
  BarChart3,
  Timer,
  Pause,
  PlayCircle,
  Plus,
  History,
  Settings2,
  Bug,
  AlertTriangle,
  Info,
  Terminal
} from 'lucide-react'
import '../styles/NaverPayDelivery.css'

const NaverPayDelivery = ({ apiBaseUrl, showNotification }) => {
  // 상태 관리
  const [deliveries, setDeliveries] = useState([])
  const [stats, setStats] = useState(null)
  const [couriers, setCouriers] = useState([])
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [loginStatus, setLoginStatus] = useState({ is_logged_in: false, username: null })

  // 필터
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedCourier, setSelectedCourier] = useState('')
  const [availableDates, setAvailableDates] = useState([])

  // 로그인 모달
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [loginCredentials, setLoginCredentials] = useState({ username: '', password: '' })
  const [loginLoading, setLoginLoading] = useState(false)

  // 스크래핑 진행 상태
  const [scrapeProgress, setScrapeProgress] = useState([])
  const [scrapeStats, setScrapeStats] = useState({ total: 0, new: 0 })

  // 탭 관리
  const [activeTab, setActiveTab] = useState('deliveries') // 'deliveries' | 'schedules' | 'history' | 'logs'

  // 스케줄 관리
  const [schedules, setSchedules] = useState([])

  // 디버그 로그
  const [debugLogs, setDebugLogs] = useState([])
  const [pageDebugInfo, setPageDebugInfo] = useState(null)
  const [logsLoading, setLogsLoading] = useState(false)
  const [scheduleHistory, setScheduleHistory] = useState([])
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [newSchedule, setNewSchedule] = useState({
    schedule_type: 'interval',
    interval_minutes: 60,
    cron_expression: '0 9 * * *'
  })

  // 초기 로드
  useEffect(() => {
    loadCouriers()
    checkLoginStatus()
    loadAvailableDates()
    loadSchedules()
  }, [])

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'schedules') {
      loadSchedules()
    } else if (activeTab === 'history') {
      loadScheduleHistory()
    } else if (activeTab === 'logs') {
      loadDebugLogs()
    }
  }, [activeTab])

  // 날짜/택배사 필터 변경 시 데이터 로드
  useEffect(() => {
    loadDeliveries()
    loadStats()
  }, [selectedDate, selectedCourier])

  // API 호출 함수들
  const checkLoginStatus = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/login-status`)
      setLoginStatus(res.data)
    } catch (error) {
      console.error('로그인 상태 확인 실패:', error)
    }
  }

  const loadCouriers = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/couriers`)
      setCouriers(res.data)
    } catch (error) {
      console.error('택배사 목록 로드 실패:', error)
    }
  }

  const loadAvailableDates = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/deliveries/dates`)
      setAvailableDates(res.data)
      if (res.data.length > 0 && !selectedDate) {
        setSelectedDate(res.data[0])
      }
    } catch (error) {
      console.error('날짜 목록 로드 실패:', error)
    }
  }

  const loadDeliveries = async () => {
    try {
      setLoading(true)
      const params = {}
      if (selectedDate) {
        params.start_date = selectedDate
        params.end_date = selectedDate
      }
      if (selectedCourier) {
        params.courier = selectedCourier
      }

      const res = await axios.get(`${apiBaseUrl}/naverpay/deliveries`, { params })
      setDeliveries(res.data)
    } catch (error) {
      console.error('배송 정보 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const params = {}
      if (selectedDate) {
        params.start_date = selectedDate
        params.end_date = selectedDate
      }
      const res = await axios.get(`${apiBaseUrl}/naverpay/deliveries/stats`, { params })
      setStats(res.data)
    } catch (error) {
      console.error('통계 로드 실패:', error)
    }
  }

  // 스케줄 관련 API
  const loadSchedules = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/schedule/list`)
      setSchedules(res.data)
    } catch (error) {
      console.error('스케줄 목록 로드 실패:', error)
    }
  }

  const loadScheduleHistory = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/schedule/history?limit=50`)
      setScheduleHistory(res.data)
    } catch (error) {
      console.error('실행 이력 로드 실패:', error)
    }
  }

  // 디버그 로그 로드
  const loadDebugLogs = async () => {
    try {
      setLogsLoading(true)
      const res = await axios.get(`${apiBaseUrl}/naverpay/logs?limit=100`)
      if (res.data.success) {
        setDebugLogs(res.data.logs.reverse()) // 최신순 정렬
      }
    } catch (error) {
      console.error('디버그 로그 로드 실패:', error)
    } finally {
      setLogsLoading(false)
    }
  }

  // 페이지 디버그 정보 로드
  const loadPageDebugInfo = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/naverpay/debug/page-info`)
      setPageDebugInfo(res.data)
    } catch (error) {
      console.error('페이지 디버그 정보 로드 실패:', error)
    }
  }

  // 로그 초기화
  const clearDebugLogs = async () => {
    try {
      await axios.delete(`${apiBaseUrl}/naverpay/logs`)
      setDebugLogs([])
      showNotification('로그가 초기화되었습니다', 'success')
    } catch (error) {
      showNotification('로그 초기화 실패', 'error')
    }
  }

  const createSchedule = async () => {
    try {
      const res = await axios.post(`${apiBaseUrl}/naverpay/schedule`, newSchedule)
      if (res.data.success) {
        showNotification('스케줄이 생성되었습니다', 'success')
        setShowScheduleModal(false)
        loadSchedules()
      }
    } catch (error) {
      showNotification('스케줄 생성 실패', 'error')
    }
  }

  const deleteSchedule = async (jobId) => {
    if (!window.confirm('이 스케줄을 삭제하시겠습니까?')) return
    try {
      await axios.delete(`${apiBaseUrl}/naverpay/schedule/${jobId}`)
      showNotification('스케줄이 삭제되었습니다', 'success')
      loadSchedules()
    } catch (error) {
      showNotification('스케줄 삭제 실패', 'error')
    }
  }

  const toggleSchedule = async (jobId) => {
    try {
      const res = await axios.post(`${apiBaseUrl}/naverpay/schedule/${jobId}/toggle`)
      showNotification(res.data.message, 'success')
      loadSchedules()
    } catch (error) {
      showNotification('스케줄 토글 실패', 'error')
    }
  }

  const runScheduleNow = async (jobId) => {
    try {
      showNotification('즉시 실행 중...', 'success')
      await axios.post(`${apiBaseUrl}/naverpay/schedule/${jobId}/run-now`)
      showNotification('즉시 실행 완료', 'success')
      loadScheduleHistory()
      loadDeliveries()
      loadStats()
    } catch (error) {
      showNotification('즉시 실행 실패', 'error')
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

  // 로그아웃 처리
  const handleLogout = async () => {
    try {
      await axios.post(`${apiBaseUrl}/naverpay/logout`)
      setLoginStatus({ is_logged_in: false, username: null })
      showNotification('로그아웃 되었습니다', 'success')
    } catch (error) {
      showNotification('로그아웃 실패', 'error')
    }
  }

  // 배송 정보 수집
  const handleScrape = async () => {
    if (!loginStatus.is_logged_in) {
      showNotification('먼저 네이버에 로그인해주세요', 'error')
      setShowLoginModal(true)
      return
    }

    try {
      setScraping(true)
      setScrapeProgress([])
      setScrapeStats({ total: 0, new: 0 })

      const res = await axios.post(`${apiBaseUrl}/naverpay/scrape`)

      if (res.data.success) {
        showNotification(`수집 완료: ${res.data.new_saved}건 저장됨`, 'success')
        setScrapeStats({ total: res.data.total_found, new: res.data.new_saved })
        loadDeliveries()
        loadStats()
        loadAvailableDates()
      } else {
        showNotification('수집 실패', 'error')
      }
    } catch (error) {
      showNotification('수집 중 오류가 발생했습니다', 'error')
    } finally {
      setScraping(false)
    }
  }

  // 클립보드 복사
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    showNotification('클립보드에 복사되었습니다', 'success')
  }

  // 전체 복사 (엑셀 형식)
  const copyAllToClipboard = () => {
    const header = '수령인\t택배사\t송장번호\t상품명\t수집일'
    const rows = deliveries.map(d =>
      `${d.recipient}\t${d.courier}\t${d.tracking_number}\t${d.product_name || ''}\t${d.collected_date}`
    )
    const text = [header, ...rows].join('\n')
    navigator.clipboard.writeText(text)
    showNotification(`${deliveries.length}건 복사 완료`, 'success')
  }

  // CSV 내보내기
  const exportToCSV = async () => {
    try {
      const params = {}
      if (selectedDate) {
        params.start_date = selectedDate
        params.end_date = selectedDate
      }

      const res = await axios.get(`${apiBaseUrl}/naverpay/export/csv`, {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `deliveries_${selectedDate || 'all'}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()

      showNotification('CSV 다운로드 완료', 'success')
    } catch (error) {
      showNotification('CSV 내보내기 실패', 'error')
    }
  }

  // 배송 삭제
  const handleDelete = async (id) => {
    if (!window.confirm('이 배송 정보를 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/naverpay/deliveries/${id}`)
      showNotification('삭제 완료', 'success')
      loadDeliveries()
      loadStats()
    } catch (error) {
      showNotification('삭제 실패', 'error')
    }
  }

  // 택배 추적 URL 열기
  const openTrackingUrl = (url) => {
    if (url) {
      window.open(url, '_blank')
    } else {
      showNotification('추적 URL을 생성할 수 없습니다', 'error')
    }
  }

  return (
    <div className="naverpay-delivery">
      {/* 헤더 */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <Truck size={32} className="header-icon" />
            <div>
              <h1>네이버페이 배송 추적</h1>
              <p>배송중인 상품의 수령인, 택배사, 송장번호를 자동 수집합니다</p>
            </div>
          </div>

          <div className="header-actions">
            {loginStatus.is_logged_in ? (
              <>
                <div className="login-status connected">
                  <CheckCircle size={16} />
                  <span>{loginStatus.username} 로그인됨</span>
                </div>
                <button className="btn btn-secondary" onClick={handleLogout}>
                  <LogOut size={18} />
                  로그아웃
                </button>
              </>
            ) : (
              <button className="btn btn-primary" onClick={() => setShowLoginModal(true)}>
                <LogIn size={18} />
                네이버 로그인
              </button>
            )}

            <button
              className="btn btn-primary"
              onClick={handleScrape}
              disabled={scraping || !loginStatus.is_logged_in}
            >
              {scraping ? (
                <>
                  <RefreshCw size={18} className="spin" />
                  수집 중...
                </>
              ) : (
                <>
                  <Play size={18} />
                  배송 정보 수집
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'deliveries' ? 'active' : ''}`}
          onClick={() => setActiveTab('deliveries')}
        >
          <Package size={18} />
          배송 정보
        </button>
        <button
          className={`tab-btn ${activeTab === 'schedules' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedules')}
        >
          <Timer size={18} />
          자동 스케줄
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <History size={18} />
          실행 이력
        </button>
        <button
          className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <Terminal size={18} />
          디버그 로그
        </button>
      </div>

      {/* 배송 정보 탭 */}
      {activeTab === 'deliveries' && (
        <>
      {/* 통계 카드 */}
      <div className="stats-grid">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-icon blue">
            <Package size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">전체 배송</span>
            <span className="stat-value">{stats?.total_count || 0}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="stat-icon green">
            <Clock size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">오늘 수집</span>
            <span className="stat-value">{stats?.today_count || 0}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="stat-icon purple">
            <Truck size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">택배사</span>
            <span className="stat-value">{Object.keys(stats?.courier_stats || {}).length}</span>
          </div>
        </motion.div>

        <motion.div
          className="stat-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="stat-icon orange">
            <Calendar size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-label">수집 일수</span>
            <span className="stat-value">{stats?.recent_dates?.length || 0}</span>
          </div>
        </motion.div>
      </div>

      {/* 택배사별 통계 */}
      {stats?.courier_stats && Object.keys(stats.courier_stats).length > 0 && (
        <motion.div
          className="courier-stats-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3><BarChart3 size={20} /> 택배사별 현황</h3>
          <div className="courier-stats-grid">
            {Object.entries(stats.courier_stats).map(([courier, count]) => (
              <div key={courier} className="courier-stat-item">
                <span className="courier-name">{courier}</span>
                <span className="courier-count">{count}건</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* 필터 및 액션 */}
      <div className="filter-bar">
        <div className="filters">
          <div className="filter-group">
            <label><Calendar size={16} /> 날짜</label>
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            >
              <option value="">전체</option>
              {availableDates.map(date => (
                <option key={date} value={date}>{date}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label><Truck size={16} /> 택배사</label>
            <select
              value={selectedCourier}
              onChange={(e) => setSelectedCourier(e.target.value)}
            >
              <option value="">전체</option>
              {couriers.map(c => (
                <option key={c.code} value={c.name}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="action-buttons">
          <button className="btn btn-secondary" onClick={copyAllToClipboard}>
            <Copy size={16} />
            전체 복사
          </button>
          <button className="btn btn-secondary" onClick={exportToCSV}>
            <Download size={16} />
            CSV 내보내기
          </button>
          <button className="btn btn-secondary" onClick={loadDeliveries}>
            <RefreshCw size={16} />
            새로고침
          </button>
        </div>
      </div>

      {/* 배송 목록 테이블 */}
      <div className="delivery-table-container">
        {loading ? (
          <div className="loading-state">
            <RefreshCw size={32} className="spin" />
            <p>데이터 로딩 중...</p>
          </div>
        ) : deliveries.length === 0 ? (
          <div className="empty-state">
            <Package size={48} />
            <h3>배송 정보가 없습니다</h3>
            <p>배송 정보 수집 버튼을 눌러 데이터를 가져오세요</p>
          </div>
        ) : (
          <table className="delivery-table">
            <thead>
              <tr>
                <th>수령인</th>
                <th>택배사</th>
                <th>송장번호</th>
                <th>상품명</th>
                <th>수집일</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {deliveries.map((delivery, index) => (
                <motion.tr
                  key={delivery.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <td>
                    <div className="cell-with-icon">
                      <User size={16} />
                      {delivery.recipient}
                    </div>
                  </td>
                  <td>
                    <span className="courier-badge">{delivery.courier}</span>
                  </td>
                  <td>
                    <div className="tracking-cell">
                      <code>{delivery.tracking_number}</code>
                      <button
                        className="icon-btn"
                        onClick={() => copyToClipboard(delivery.tracking_number)}
                        title="송장번호 복사"
                      >
                        <Copy size={14} />
                      </button>
                    </div>
                  </td>
                  <td className="product-cell">
                    {delivery.product_name || '-'}
                  </td>
                  <td>{delivery.collected_date}</td>
                  <td>
                    <div className="action-cell">
                      <button
                        className="icon-btn primary"
                        onClick={() => openTrackingUrl(delivery.tracking_url)}
                        title="배송 추적"
                      >
                        <ExternalLink size={16} />
                      </button>
                      <button
                        className="icon-btn danger"
                        onClick={() => handleDelete(delivery.id)}
                        title="삭제"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
        </>
      )}

      {/* 스케줄 관리 탭 */}
      {activeTab === 'schedules' && (
        <div className="schedule-section">
          <div className="section-header">
            <h3><Timer size={20} /> 자동 수집 스케줄</h3>
            <button className="btn btn-primary" onClick={() => setShowScheduleModal(true)}>
              <Plus size={18} />
              스케줄 추가
            </button>
          </div>

          {schedules.length === 0 ? (
            <div className="empty-state">
              <Timer size={48} />
              <h3>등록된 스케줄이 없습니다</h3>
              <p>자동 수집 스케줄을 추가하여 배송 정보를 자동으로 수집하세요</p>
            </div>
          ) : (
            <div className="schedule-list">
              {schedules.map((schedule) => (
                <motion.div
                  key={schedule.job_id}
                  className={`schedule-card ${schedule.is_active ? 'active' : 'paused'}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="schedule-info">
                    <div className="schedule-type">
                      {schedule.schedule_type === 'interval' ? (
                        <>
                          <Clock size={18} />
                          <span>매 {schedule.interval_minutes}분마다</span>
                        </>
                      ) : (
                        <>
                          <Calendar size={18} />
                          <span>Cron: {schedule.cron_expression}</span>
                        </>
                      )}
                    </div>
                    <div className="schedule-status">
                      {schedule.is_active ? (
                        <span className="status-badge active">
                          <CheckCircle size={14} /> 활성
                        </span>
                      ) : (
                        <span className="status-badge paused">
                          <Pause size={14} /> 일시정지
                        </span>
                      )}
                      {schedule.next_run && (
                        <span className="next-run">
                          다음 실행: {new Date(schedule.next_run).toLocaleString('ko-KR')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="schedule-actions">
                    <button
                      className="icon-btn"
                      onClick={() => runScheduleNow(schedule.job_id)}
                      title="즉시 실행"
                    >
                      <PlayCircle size={18} />
                    </button>
                    <button
                      className={`icon-btn ${schedule.is_active ? 'warning' : 'success'}`}
                      onClick={() => toggleSchedule(schedule.job_id)}
                      title={schedule.is_active ? '일시정지' : '재개'}
                    >
                      {schedule.is_active ? <Pause size={18} /> : <Play size={18} />}
                    </button>
                    <button
                      className="icon-btn danger"
                      onClick={() => deleteSchedule(schedule.job_id)}
                      title="삭제"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 실행 이력 탭 */}
      {activeTab === 'history' && (
        <div className="history-section">
          <div className="section-header">
            <h3><History size={20} /> 실행 이력</h3>
            <button className="btn btn-secondary" onClick={loadScheduleHistory}>
              <RefreshCw size={18} />
              새로고침
            </button>
          </div>

          {scheduleHistory.length === 0 ? (
            <div className="empty-state">
              <History size={48} />
              <h3>실행 이력이 없습니다</h3>
              <p>스케줄이 실행되면 이력이 여기에 표시됩니다</p>
            </div>
          ) : (
            <div className="history-table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>실행 시각</th>
                    <th>발견</th>
                    <th>신규 저장</th>
                    <th>상태</th>
                    <th>에러</th>
                  </tr>
                </thead>
                <tbody>
                  {scheduleHistory.map((history) => (
                    <tr key={history.id} className={history.status}>
                      <td>{new Date(history.executed_at).toLocaleString('ko-KR')}</td>
                      <td>{history.total_found}건</td>
                      <td>{history.new_saved}건</td>
                      <td>
                        <span className={`status-badge ${history.status}`}>
                          {history.status === 'success' && <CheckCircle size={14} />}
                          {history.status === 'failed' && <XCircle size={14} />}
                          {history.status}
                        </span>
                      </td>
                      <td className="error-cell">{history.error_message || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 디버그 로그 탭 */}
      {activeTab === 'logs' && (
        <div className="logs-section">
          <div className="section-header">
            <h3><Terminal size={20} /> 스크래핑 디버그 로그</h3>
            <div className="header-actions">
              <button className="btn btn-secondary" onClick={loadPageDebugInfo}>
                <Bug size={18} />
                페이지 분석
              </button>
              <button className="btn btn-secondary" onClick={loadDebugLogs}>
                <RefreshCw size={18} />
                새로고침
              </button>
              <button className="btn btn-danger" onClick={clearDebugLogs}>
                <Trash2 size={18} />
                로그 초기화
              </button>
            </div>
          </div>

          {/* 페이지 디버그 정보 */}
          {pageDebugInfo && (
            <motion.div
              className="debug-info-card"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h4><Bug size={16} /> 현재 브라우저 상태</h4>
              <div className="debug-info-grid">
                <div className="debug-item">
                  <span className="label">브라우저 초기화:</span>
                  <span className={`value ${pageDebugInfo.browser_initialized ? 'success' : 'error'}`}>
                    {pageDebugInfo.browser_initialized ? '완료' : '미완료'}
                  </span>
                </div>
                <div className="debug-item">
                  <span className="label">로그인 상태:</span>
                  <span className={`value ${pageDebugInfo.is_logged_in ? 'success' : 'error'}`}>
                    {pageDebugInfo.is_logged_in ? `로그인됨 (${pageDebugInfo.username})` : '로그인 안됨'}
                  </span>
                </div>
                <div className="debug-item">
                  <span className="label">현재 URL:</span>
                  <span className="value url">{pageDebugInfo.current_url || '-'}</span>
                </div>
                <div className="debug-item">
                  <span className="label">페이지 제목:</span>
                  <span className="value">{pageDebugInfo.page_title || '-'}</span>
                </div>
              </div>
              {pageDebugInfo.page_analysis && (
                <div className="page-analysis">
                  <h5>페이지 분석 결과</h5>
                  <div className="analysis-items">
                    <div className="analysis-item">
                      <span>order_list 요소:</span>
                      <span className={pageDebugInfo.page_analysis.hasOrderList ? 'found' : 'not-found'}>
                        {pageDebugInfo.page_analysis.hasOrderList ? '발견됨' : '없음'}
                      </span>
                    </div>
                    <div className="analysis-item">
                      <span>delivery_list 요소:</span>
                      <span className={pageDebugInfo.page_analysis.hasDeliveryList ? 'found' : 'not-found'}>
                        {pageDebugInfo.page_analysis.hasDeliveryList ? '발견됨' : '없음'}
                      </span>
                    </div>
                  </div>
                  {pageDebugInfo.page_analysis.orderRelatedElements?.length > 0 && (
                    <div className="elements-list">
                      <h6>Order 관련 요소 ({pageDebugInfo.page_analysis.orderRelatedElements.length}개):</h6>
                      {pageDebugInfo.page_analysis.orderRelatedElements.slice(0, 5).map((el, idx) => (
                        <div key={idx} className="element-item">
                          <code>{`<${el.tag.toLowerCase()} class="${el.className?.substring(0, 50)}...">`}</code>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {pageDebugInfo.error && (
                <div className="debug-error">
                  <AlertTriangle size={16} />
                  <span>{pageDebugInfo.error}</span>
                </div>
              )}
            </motion.div>
          )}

          {/* 로그 목록 */}
          <div className="logs-container">
            {logsLoading ? (
              <div className="loading-state">
                <RefreshCw size={32} className="spin" />
                <p>로그 로딩 중...</p>
              </div>
            ) : debugLogs.length === 0 ? (
              <div className="empty-state">
                <Terminal size={48} />
                <h3>로그가 없습니다</h3>
                <p>배송 정보 수집을 실행하면 로그가 여기에 표시됩니다</p>
              </div>
            ) : (
              <div className="logs-list">
                {debugLogs.map((log, idx) => (
                  <motion.div
                    key={idx}
                    className={`log-entry ${log.level}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.02 }}
                  >
                    <div className="log-header">
                      <span className="log-time">
                        {new Date(log.timestamp).toLocaleTimeString('ko-KR')}
                      </span>
                      <span className={`log-level ${log.level}`}>
                        {log.level === 'error' && <XCircle size={14} />}
                        {log.level === 'warning' && <AlertTriangle size={14} />}
                        {log.level === 'info' && <Info size={14} />}
                        {log.level.toUpperCase()}
                      </span>
                    </div>
                    <div className="log-message">{log.message}</div>
                    {log.details && Object.keys(log.details).length > 0 && (
                      <div className="log-details">
                        <pre>{JSON.stringify(log.details, null, 2)}</pre>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 스케줄 추가 모달 */}
      <AnimatePresence>
        {showScheduleModal && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowScheduleModal(false)}
          >
            <motion.div
              className="modal-content"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2><Timer size={24} /> 스케줄 추가</h2>
              <p className="modal-desc">
                자동 수집 스케줄을 설정하세요
              </p>

              <div className="form-group">
                <label>스케줄 유형</label>
                <select
                  value={newSchedule.schedule_type}
                  onChange={(e) => setNewSchedule(prev => ({ ...prev, schedule_type: e.target.value }))}
                >
                  <option value="interval">간격 반복</option>
                  <option value="cron">Cron 표현식</option>
                </select>
              </div>

              {newSchedule.schedule_type === 'interval' ? (
                <div className="form-group">
                  <label>반복 간격 (분)</label>
                  <input
                    type="number"
                    value={newSchedule.interval_minutes}
                    onChange={(e) => setNewSchedule(prev => ({ ...prev, interval_minutes: parseInt(e.target.value) }))}
                    min="30"
                    max="1440"
                  />
                  <small>최소 30분, 최대 1440분 (24시간)</small>
                </div>
              ) : (
                <div className="form-group">
                  <label>Cron 표현식</label>
                  <input
                    type="text"
                    value={newSchedule.cron_expression}
                    onChange={(e) => setNewSchedule(prev => ({ ...prev, cron_expression: e.target.value }))}
                    placeholder="0 9 * * *"
                  />
                  <small>
                    예시: "0 9 * * *" (매일 9시), "0 9,18 * * *" (매일 9시, 18시)
                  </small>
                </div>
              )}

              <div className="modal-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowScheduleModal(false)}
                >
                  취소
                </button>
                <button
                  className="btn btn-primary"
                  onClick={createSchedule}
                >
                  <Plus size={18} />
                  스케줄 생성
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
              <p className="modal-desc">
                네이버페이 배송 정보를 수집하려면 로그인이 필요합니다
              </p>

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
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowLoginModal(false)}
                >
                  취소
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleLogin}
                  disabled={loginLoading}
                >
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
    </div>
  )
}

export default NaverPayDelivery
