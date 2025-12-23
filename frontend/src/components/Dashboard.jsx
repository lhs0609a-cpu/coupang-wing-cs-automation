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
import TutorialButton from './TutorialButton'
import AutoModePanel from './AutoModePanel'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'
import '../styles/Dashboard.css'

const Dashboard = ({ stats, automationStats, apiBaseUrl }) => {
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
          <span>백엔드 연결 성공 | 시스템 정상 작동 중</span>
        </div>
      </div>

      {/* Auto Mode Panel */}
      <AutoModePanel apiBaseUrl={apiBaseUrl} />

      {/* Stats Grid */}
      {stats && (
        <div className="stats-grid">
          <StatCard
            title="대기 중인 문의"
            value={stats.inquiries?.pending || 0}
            icon={Inbox}
            color="blue"
            delay={0}
          />
          <StatCard
            title="처리 완료"
            value={stats.inquiries?.processed || 0}
            icon={CheckCircle}
            color="green"
            delay={0.1}
          />
          <StatCard
            title="승인 대기"
            value={stats.submissions?.pending_submission || 0}
            icon={Clock}
            color="orange"
            delay={0.2}
          />
          <StatCard
            title="제출 완료"
            value={stats.submissions?.submission_success || 0}
            icon={Send}
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

      {/* Coupang Wing Automation */}
      <CoupangWingAutomation apiBaseUrl={apiBaseUrl} />

      {/* 플로팅 튜토리얼 버튼 */}
      <TutorialButton tabId="dashboard" variant="floating" />
    </div>
  )
}

export default Dashboard
