import React from 'react'
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  BarChart3,
  FileText,
  Zap,
  Moon,
  Sun,
  PackageX,
  Key,
  ShoppingBag,
  Ticket,
  Star
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import '../styles/Sidebar.css'

const Sidebar = ({ activeTab, setActiveTab }) => {
  const { theme, toggleTheme } = useTheme()

  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: LayoutDashboard },
    { id: 'inquiries', label: '문의 관리', icon: MessageSquare },
    { id: 'returns', label: '반품 관리', icon: PackageX },
    { id: 'promotion', label: '프로모션', icon: Ticket },
    { id: 'automation', label: '자동화', icon: Zap },
    { id: 'coupang-accounts', label: '쿠팡 계정', icon: ShoppingBag },
    { id: 'naver-accounts', label: '네이버 계정', icon: Key },
    { id: 'analytics', label: '통계', icon: BarChart3 },
    { id: 'naver-review', label: '네이버 리뷰', icon: Star },
    { id: 'reports', label: '리포트', icon: FileText },
    { id: 'settings', label: '설정', icon: Settings },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon">🤖</div>
          <div className="logo-text">
            <h1>Wing CS AI</h1>
            <p>자동화 시스템</p>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="sidebar-footer">
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          <span>{theme === 'dark' ? '라이트 모드' : '다크 모드'}</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
