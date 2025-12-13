import React from 'react'
import { motion } from 'framer-motion'
import {
  Inbox,
  CheckCircle,
  Clock,
  Send,
  Activity,
  Zap
} from 'lucide-react'
import StatCard from './StatCard'
import ChatGPTStatus from './ChatGPTStatus'
import CoupangWingAutomation from './CoupangWingAutomation'
import { AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import '../styles/Dashboard.css'

const Dashboard = ({ stats, automationStats, apiBaseUrl }) => {
  // 샘플 차트 데이터
  const weeklyData = [
    { name: '월', 문의: 45, 처리: 42 },
    { name: '화', 문의: 52, 처리: 50 },
    { name: '수', 문의: 38, 처리: 36 },
    { name: '목', 문의: 65, 처리: 63 },
    { name: '금', 문의: 58, 처리: 55 },
    { name: '토', 문의: 28, 처리: 27 },
    { name: '일', 문의: 22, 처리: 21 },
  ]

  const automationData = [
    { name: '자동 승인', value: automationStats?.auto_approval_rate || 0, color: '#10b981' },
    { name: '수동 검토', value: 100 - (automationStats?.auto_approval_rate || 0), color: '#f59e0b' },
  ]

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">대시보드</h1>
          <p className="dashboard-subtitle">실시간 시스템 현황을 확인하세요</p>
        </div>
        <div className="dashboard-status">
          <div className="status-dot"></div>
          <span>백엔드 연결 성공 ✅ | 시스템 정상 작동 중</span>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="stats-grid">
          <StatCard
            title="대기 중인 문의"
            value={stats.inquiries?.pending || 0}
            icon={Inbox}
            trend="up"
            trendValue={12}
            color="blue"
            delay={0}
          />
          <StatCard
            title="처리 완료"
            value={stats.inquiries?.processed || 0}
            icon={CheckCircle}
            trend="up"
            trendValue={8}
            color="green"
            delay={0.1}
          />
          <StatCard
            title="승인 대기"
            value={stats.submissions?.pending_submission || 0}
            icon={Clock}
            trend="down"
            trendValue={5}
            color="orange"
            delay={0.2}
          />
          <StatCard
            title="제출 완료"
            value={stats.submissions?.submission_success || 0}
            icon={Send}
            trend="up"
            trendValue={15}
            color="purple"
            delay={0.3}
          />
        </div>
      )}

      {/* Automation Stats */}
      {automationStats && (
        <div className="automation-stats">
          <motion.div
            className="automation-card"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="automation-header">
              <Zap size={24} className="automation-icon" />
              <h3>AI 자동화 효율</h3>
            </div>
            <div className="automation-metrics">
              <div className="metric">
                <div className="metric-label">자동 승인률</div>
                <div className="metric-value">{automationStats.auto_approval_rate || 0}%</div>
                <div className="metric-bar">
                  <div
                    className="metric-bar-fill green"
                    style={{ width: `${automationStats.auto_approval_rate || 0}%` }}
                  ></div>
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">자동 제출률</div>
                <div className="metric-value">{automationStats.auto_submission_rate || 0}%</div>
                <div className="metric-bar">
                  <div
                    className="metric-bar-fill purple"
                    style={{ width: `${automationStats.auto_submission_rate || 0}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="automation-card"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
          >
            <div className="automation-header">
              <Activity size={24} className="automation-icon" />
              <h3>자동화 분포</h3>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={automationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {automationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* ChatGPT Status Card */}
          <ChatGPTStatus />
        </div>
      )}

      {/* Charts */}
      <div className="charts-grid">
        <motion.div
          className="chart-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <h3 className="chart-title">주간 문의 처리 현황</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={weeklyData}>
                <defs>
                  <linearGradient id="colorInquiry" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorProcessed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip
                  contentStyle={{
                    background: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px'
                  }}
                />
                <Area type="monotone" dataKey="문의" stroke="#3b82f6" fillOpacity={1} fill="url(#colorInquiry)" strokeWidth={2} />
                <Area type="monotone" dataKey="처리" stroke="#10b981" fillOpacity={1} fill="url(#colorProcessed)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          className="chart-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <h3 className="chart-title">시간대별 문의량</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip
                  contentStyle={{
                    background: 'var(--card-bg)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="문의" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Coupang Wing Automation */}
      <CoupangWingAutomation apiBaseUrl={apiBaseUrl} />
    </div>
  )
}

export default Dashboard
