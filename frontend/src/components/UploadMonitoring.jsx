import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  Users,
  Calendar,
  RefreshCw,
  Settings,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  TrendingUp,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line
} from 'recharts'
import axios from 'axios'
import '../styles/UploadMonitoring.css'

// 색상 팔레트 (사람별 색상)
const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
]

const UploadMonitoring = ({ apiBaseUrl }) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [chartData, setChartData] = useState([])
  const [personStats, setPersonStats] = useState([])
  const [uniqueNames, setUniqueNames] = useState([])
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [totalRecords, setTotalRecords] = useState(0)

  // 기간 필터
  const [selectedPeriod, setSelectedPeriod] = useState('month')

  // IP 매핑 관리
  const [ipMappings, setIpMappings] = useState([])
  const [showMappingModal, setShowMappingModal] = useState(false)
  const [editingMapping, setEditingMapping] = useState(null)
  const [newMapping, setNewMapping] = useState({ ip_address: '', name: '' })

  // 설정
  const [showSettings, setShowSettings] = useState(false)
  const [sheetConfig, setSheetConfig] = useState({
    sheet_id: '',
    sheet_name: 'Sheet1',
    date_column: 'D',
    email_column: 'E',
    ip_column: 'F'
  })

  // 데이터 로드
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`${apiBaseUrl}/upload-monitoring/data`, {
        params: { preset: selectedPeriod }
      })

      if (response.data.success) {
        setChartData(response.data.chart_data)
        setPersonStats(response.data.person_stats)
        setUniqueNames(response.data.unique_names)
        setDateRange(response.data.date_range)
        setTotalRecords(response.data.total_records)
      }
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err.response?.data?.detail || '데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }, [apiBaseUrl, selectedPeriod])

  // IP 매핑 로드
  const fetchMappings = useCallback(async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/upload-monitoring/ip-mappings`)
      if (response.data.success) {
        setIpMappings(response.data.mappings)
      }
    } catch (err) {
      console.error('Error fetching mappings:', err)
    }
  }, [apiBaseUrl])

  // 시트 설정 로드
  const fetchConfig = useCallback(async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/upload-monitoring/config`)
      if (response.data.success) {
        setSheetConfig(response.data.config)
      }
    } catch (err) {
      console.error('Error fetching config:', err)
    }
  }, [apiBaseUrl])

  useEffect(() => {
    fetchData()
    fetchMappings()
    fetchConfig()
  }, [fetchData, fetchMappings, fetchConfig])

  // IP 매핑 저장
  const saveMapping = async () => {
    try {
      if (editingMapping) {
        await axios.put(
          `${apiBaseUrl}/upload-monitoring/ip-mappings/${editingMapping.ip_address}`,
          { name: editingMapping.name }
        )
      } else {
        await axios.post(`${apiBaseUrl}/upload-monitoring/ip-mappings`, newMapping)
      }

      await fetchMappings()
      await fetchData()
      setEditingMapping(null)
      setNewMapping({ ip_address: '', name: '' })
      setShowMappingModal(false)
    } catch (err) {
      alert(err.response?.data?.detail || '저장에 실패했습니다.')
    }
  }

  // IP 매핑 삭제
  const deleteMapping = async (ip) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/upload-monitoring/ip-mappings/${ip}`)
      await fetchMappings()
      await fetchData()
    } catch (err) {
      alert('삭제에 실패했습니다.')
    }
  }

  // 시트 설정 저장
  const saveConfig = async () => {
    try {
      await axios.post(`${apiBaseUrl}/upload-monitoring/config`, sheetConfig)
      alert('설정이 저장되었습니다.')
      setShowSettings(false)
      fetchData()
    } catch (err) {
      alert('설정 저장에 실패했습니다.')
    }
  }

  // 기간 버튼
  const periodButtons = [
    { key: 'today', label: '오늘' },
    { key: 'week', label: '최근 일주일' },
    { key: 'month', label: '최근 한달' },
    { key: '3months', label: '3개월' }
  ]

  return (
    <div className="upload-monitoring">
      {/* Header */}
      <div className="monitoring-header">
        <div>
          <h1 className="monitoring-title">
            <BarChart3 className="title-icon" />
            상품 업로드 모니터링
          </h1>
          <p className="monitoring-subtitle">
            IP별 실시간 상품 업로드 현황을 확인하세요
          </p>
        </div>
        <div className="header-actions">
          <button
            className="action-btn settings-btn"
            onClick={() => setShowSettings(true)}
          >
            <Settings size={18} />
            설정
          </button>
          <button
            className="action-btn refresh-btn"
            onClick={fetchData}
            disabled={loading}
          >
            <RefreshCw size={18} className={loading ? 'spinning' : ''} />
            새로고침
          </button>
        </div>
      </div>

      {/* Period Filter */}
      <div className="period-filter">
        <Calendar size={18} />
        <span className="filter-label">기간 선택:</span>
        <div className="period-buttons">
          {periodButtons.map(btn => (
            <button
              key={btn.key}
              className={`period-btn ${selectedPeriod === btn.key ? 'active' : ''}`}
              onClick={() => setSelectedPeriod(btn.key)}
            >
              {btn.label}
            </button>
          ))}
        </div>
        {dateRange.start && (
          <span className="date-range-display">
            {dateRange.start} ~ {dateRange.end}
          </span>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="summary-cards">
        <motion.div
          className="summary-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="card-icon blue">
            <Users size={24} />
          </div>
          <div className="card-content">
            <div className="card-value">{personStats.length}</div>
            <div className="card-label">등록된 작업자</div>
          </div>
        </motion.div>

        <motion.div
          className="summary-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="card-icon green">
            <TrendingUp size={24} />
          </div>
          <div className="card-content">
            <div className="card-value">{totalRecords.toLocaleString()}</div>
            <div className="card-label">총 업로드 수</div>
          </div>
        </motion.div>

        <motion.div
          className="summary-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="card-icon purple">
            <CheckCircle size={24} />
          </div>
          <div className="card-content">
            <div className="card-value">
              {personStats.reduce((sum, p) => sum + p.today, 0)}
            </div>
            <div className="card-label">오늘 업로드</div>
          </div>
        </motion.div>
      </div>

      {/* Main Chart */}
      <motion.div
        className="chart-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="section-header">
          <h2>날짜별 업로드 현황</h2>
          <button
            className="manage-btn"
            onClick={() => setShowMappingModal(true)}
          >
            <Users size={16} />
            IP 이름 관리
          </button>
        </div>

        {loading ? (
          <div className="loading-state">
            <RefreshCw className="spinning" size={32} />
            <p>데이터를 불러오는 중...</p>
          </div>
        ) : chartData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis
                  dataKey="date"
                  stroke="var(--text-secondary)"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return `${date.getMonth() + 1}/${date.getDate()}`
                  }}
                />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip
                  contentStyle={{
                    background: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px'
                  }}
                  labelFormatter={(value) => `날짜: ${value}`}
                />
                <Legend />
                {uniqueNames.map((name, index) => (
                  <Bar
                    key={name}
                    dataKey={name}
                    fill={COLORS[index % COLORS.length]}
                    radius={[4, 4, 0, 0]}
                    stackId="stack"
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="empty-state">
            <BarChart3 size={48} />
            <p>표시할 데이터가 없습니다.</p>
          </div>
        )}
      </motion.div>

      {/* Person Stats Table */}
      <motion.div
        className="stats-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="section-header">
          <h2>개인별 업로드 통계</h2>
        </div>

        <div className="stats-table-wrapper">
          <table className="stats-table">
            <thead>
              <tr>
                <th>이름</th>
                <th>IP 주소</th>
                <th>오늘</th>
                <th>어제</th>
                <th>총합</th>
                <th>일평균</th>
              </tr>
            </thead>
            <tbody>
              {personStats.map((person, index) => (
                <tr key={person.ip}>
                  <td>
                    <div className="person-name">
                      <span
                        className="color-dot"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      {person.name}
                    </div>
                  </td>
                  <td className="ip-cell">{person.ip}</td>
                  <td className="number-cell">{person.today}</td>
                  <td className="number-cell">{person.yesterday}</td>
                  <td className="number-cell highlight">{person.total.toLocaleString()}</td>
                  <td className="number-cell">{person.average}</td>
                </tr>
              ))}
              {personStats.length === 0 && (
                <tr>
                  <td colSpan="6" className="empty-row">
                    데이터가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* IP Mapping Modal */}
      {showMappingModal && (
        <div className="modal-overlay" onClick={() => setShowMappingModal(false)}>
          <motion.div
            className="modal"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>IP 이름 관리</h3>
              <button className="close-btn" onClick={() => setShowMappingModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              {/* Add New Mapping */}
              <div className="add-mapping-form">
                <input
                  type="text"
                  placeholder="IP 주소"
                  value={newMapping.ip_address}
                  onChange={(e) => setNewMapping({ ...newMapping, ip_address: e.target.value })}
                />
                <input
                  type="text"
                  placeholder="이름"
                  value={newMapping.name}
                  onChange={(e) => setNewMapping({ ...newMapping, name: e.target.value })}
                />
                <button
                  className="add-btn"
                  onClick={() => {
                    if (newMapping.ip_address && newMapping.name) {
                      saveMapping()
                    }
                  }}
                >
                  <Plus size={18} />
                  추가
                </button>
              </div>

              {/* Existing Mappings */}
              <div className="mappings-list">
                {ipMappings.map((mapping) => (
                  <div key={mapping.ip_address} className="mapping-item">
                    {editingMapping?.ip_address === mapping.ip_address ? (
                      <>
                        <span className="mapping-ip">{mapping.ip_address}</span>
                        <input
                          type="text"
                          value={editingMapping.name}
                          onChange={(e) =>
                            setEditingMapping({ ...editingMapping, name: e.target.value })
                          }
                        />
                        <button className="icon-btn save" onClick={saveMapping}>
                          <Save size={16} />
                        </button>
                        <button
                          className="icon-btn cancel"
                          onClick={() => setEditingMapping(null)}
                        >
                          <X size={16} />
                        </button>
                      </>
                    ) : (
                      <>
                        <span className="mapping-ip">{mapping.ip_address}</span>
                        <span className="mapping-name">{mapping.name}</span>
                        <button
                          className="icon-btn edit"
                          onClick={() => setEditingMapping(mapping)}
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className="icon-btn delete"
                          onClick={() => deleteMapping(mapping.ip_address)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </>
                    )}
                  </div>
                ))}

                {ipMappings.length === 0 && (
                  <div className="empty-mappings">
                    등록된 IP 매핑이 없습니다.
                  </div>
                )}
              </div>

              {/* Discovered IPs from data */}
              {personStats.length > 0 && (
                <div className="discovered-ips">
                  <h4>데이터에서 발견된 IP</h4>
                  <div className="discovered-list">
                    {personStats
                      .filter(p => p.ip === p.name) // IP가 이름과 같으면 매핑 안된 것
                      .map(p => (
                        <div key={p.ip} className="discovered-item">
                          <span>{p.ip}</span>
                          <button
                            className="quick-add-btn"
                            onClick={() => {
                              setNewMapping({ ip_address: p.ip, name: '' })
                            }}
                          >
                            이름 지정
                          </button>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="modal-overlay" onClick={() => setShowSettings(false)}>
          <motion.div
            className="modal settings-modal"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>Google Sheets 설정</h3>
              <button className="close-btn" onClick={() => setShowSettings(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>시트 ID</label>
                <input
                  type="text"
                  value={sheetConfig.sheet_id}
                  onChange={(e) => setSheetConfig({ ...sheetConfig, sheet_id: e.target.value })}
                  placeholder="Google Sheets URL에서 /d/ 뒤의 ID"
                />
                <small>예: 1wBxJlm1_p3BJAi16hcgw0XxlnW4Fquk_gfm9dtE4QR0</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>날짜 열</label>
                  <input
                    type="text"
                    value={sheetConfig.date_column}
                    onChange={(e) => setSheetConfig({ ...sheetConfig, date_column: e.target.value })}
                    placeholder="D"
                  />
                </div>
                <div className="form-group">
                  <label>이메일 열</label>
                  <input
                    type="text"
                    value={sheetConfig.email_column}
                    onChange={(e) => setSheetConfig({ ...sheetConfig, email_column: e.target.value })}
                    placeholder="E"
                  />
                </div>
                <div className="form-group">
                  <label>IP 열</label>
                  <input
                    type="text"
                    value={sheetConfig.ip_column}
                    onChange={(e) => setSheetConfig({ ...sheetConfig, ip_column: e.target.value })}
                    placeholder="F"
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button className="cancel-btn" onClick={() => setShowSettings(false)}>
                  취소
                </button>
                <button className="save-btn" onClick={saveConfig}>
                  <Save size={16} />
                  저장
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

export default UploadMonitoring
