import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import '../styles/StatCard.css'

const StatCard = ({ title, value, icon: Icon, trend, trendValue, color = 'blue', delay = 0 }) => {
  const isPositiveTrend = trend === 'up'

  return (
    <motion.div
      className="stat-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
    >
      <div className={`stat-card-inner stat-card-${color}`}>
        <div className="stat-card-header">
          <div className="stat-icon-wrapper">
            <Icon size={24} className="stat-icon" />
          </div>
          {trendValue && (
            <div className={`stat-trend ${isPositiveTrend ? 'positive' : 'negative'}`}>
              {isPositiveTrend ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{trendValue}%</span>
            </div>
          )}
        </div>
        <div className="stat-card-content">
          <h3 className="stat-title">{title}</h3>
          <div className="stat-value">{value.toLocaleString()}</div>
        </div>
      </div>
    </motion.div>
  )
}

export default StatCard
