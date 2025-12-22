import React, { useState, useEffect } from 'react'
import { Reorder, useDragControls } from 'framer-motion'
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  Moon,
  Sun,
  PackageX,
  Key,
  ShoppingBag,
  Ticket,
  Star,
  Truck,
  Search,
  GripVertical,
  BarChart3,
  AlertTriangle
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import '../styles/Sidebar.css'

const defaultMenuItems = [
  { id: 'dashboard', label: '대시보드', icon: 'LayoutDashboard' },
  { id: 'upload-monitoring', label: '업로드 모니터링', icon: 'BarChart3' },
  { id: 'inquiries', label: '문의 관리', icon: 'MessageSquare' },
  { id: 'returns', label: '반품 관리', icon: 'PackageX' },
  { id: 'issue-response', label: '문제 대응', icon: 'AlertTriangle' },
  { id: 'promotion', label: '프로모션', icon: 'Ticket' },
  { id: 'naverpay-delivery', label: '배송 추적', icon: 'Truck' },
  { id: 'product-search', label: '상품 검색', icon: 'Search' },
  { id: 'coupang-accounts', label: '쿠팡 계정', icon: 'ShoppingBag' },
  { id: 'naver-accounts', label: '네이버 계정', icon: 'Key' },
  { id: 'naver-review', label: '네이버 리뷰', icon: 'Star' },
  { id: 'settings', label: '설정', icon: 'Settings' },
]

const iconMap = {
  LayoutDashboard,
  MessageSquare,
  Settings,
  PackageX,
  Key,
  ShoppingBag,
  Ticket,
  Star,
  Truck,
  Search,
  BarChart3,
  AlertTriangle
}

const MenuItem = ({ item, isActive, onClick }) => {
  const dragControls = useDragControls()
  const Icon = iconMap[item.icon]

  return (
    <Reorder.Item
      value={item}
      dragListener={false}
      dragControls={dragControls}
      className={`sidebar-item ${isActive ? 'active' : ''}`}
      whileDrag={{
        scale: 1.02,
        boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3)',
        zIndex: 50
      }}
    >
      <div
        className="drag-handle"
        onPointerDown={(e) => dragControls.start(e)}
      >
        <GripVertical size={16} />
      </div>
      <button onClick={onClick} className="menu-button">
        {Icon && <Icon size={20} />}
        <span>{item.label}</span>
      </button>
    </Reorder.Item>
  )
}

const Sidebar = ({ activeTab, setActiveTab }) => {
  const { theme, toggleTheme } = useTheme()

  // localStorage에서 저장된 순서 불러오기
  const [menuItems, setMenuItems] = useState(() => {
    const saved = localStorage.getItem('sidebarMenuOrder')
    if (saved) {
      try {
        const savedOrder = JSON.parse(saved)
        // 저장된 순서대로 정렬, 새 메뉴 항목은 끝에 추가
        const orderedItems = []
        savedOrder.forEach(id => {
          const item = defaultMenuItems.find(m => m.id === id)
          if (item) orderedItems.push(item)
        })
        // 새로 추가된 항목들
        defaultMenuItems.forEach(item => {
          if (!orderedItems.find(m => m.id === item.id)) {
            orderedItems.push(item)
          }
        })
        return orderedItems
      } catch {
        return defaultMenuItems
      }
    }
    return defaultMenuItems
  })

  // 순서 변경 시 저장
  const handleReorder = (newOrder) => {
    setMenuItems(newOrder)
    localStorage.setItem('sidebarMenuOrder', JSON.stringify(newOrder.map(item => item.id)))
  }

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
        <Reorder.Group
          axis="y"
          values={menuItems}
          onReorder={handleReorder}
          className="menu-list"
        >
          {menuItems.map((item) => (
            <MenuItem
              key={item.id}
              item={item}
              isActive={activeTab === item.id}
              onClick={() => setActiveTab(item.id)}
            />
          ))}
        </Reorder.Group>
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
