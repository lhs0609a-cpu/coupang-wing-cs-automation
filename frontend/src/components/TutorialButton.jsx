import React from 'react'
import { motion } from 'framer-motion'
import { HelpCircle, PlayCircle, CheckCircle2, RotateCcw } from 'lucide-react'
import { useTutorial, TUTORIAL_STEPS } from '../contexts/TutorialContext'
import '../styles/TutorialButton.css'

const TutorialButton = ({ tabId, variant = 'default' }) => {
  const { startTutorial, completedTabs, isActive } = useTutorial()

  // 해당 탭에 튜토리얼이 없으면 렌더링 안함
  if (!TUTORIAL_STEPS[tabId]) return null

  const isCompleted = completedTabs.includes(tabId)
  const stepCount = TUTORIAL_STEPS[tabId].length

  const handleClick = () => {
    if (!isActive) {
      startTutorial(tabId)
    }
  }

  if (variant === 'floating') {
    return (
      <motion.button
        className={`tutorial-btn-floating ${isCompleted ? 'completed' : ''}`}
        onClick={handleClick}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        disabled={isActive}
      >
        {isCompleted ? (
          <>
            <RotateCcw size={18} />
            <span>다시 보기</span>
          </>
        ) : (
          <>
            <PlayCircle size={18} />
            <span>튜토리얼 시작</span>
          </>
        )}
      </motion.button>
    )
  }

  if (variant === 'banner') {
    if (isCompleted) return null

    return (
      <motion.div
        className="tutorial-banner"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
      >
        <div className="banner-content">
          <div className="banner-icon">
            <HelpCircle size={24} />
          </div>
          <div className="banner-text">
            <h4>처음이신가요?</h4>
            <p>이 기능의 사용법을 {stepCount}단계로 쉽게 알려드릴게요!</p>
          </div>
        </div>
        <button className="banner-btn" onClick={handleClick}>
          <PlayCircle size={18} />
          튜토리얼 시작
        </button>
      </motion.div>
    )
  }

  // default variant
  return (
    <motion.button
      className={`tutorial-btn ${isCompleted ? 'completed' : ''}`}
      onClick={handleClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      disabled={isActive}
    >
      {isCompleted ? (
        <>
          <CheckCircle2 size={16} />
          <span>튜토리얼 다시 보기</span>
        </>
      ) : (
        <>
          <HelpCircle size={16} />
          <span>사용법 보기 ({stepCount}단계)</span>
        </>
      )}
    </motion.button>
  )
}

export default TutorialButton
