import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HelpCircle, PlayCircle, CheckCircle2, RotateCcw, Settings, X, ToggleLeft, ToggleRight, RefreshCw } from 'lucide-react'
import { useTutorial, TUTORIAL_STEPS } from '../contexts/TutorialContext'
import '../styles/TutorialButton.css'

const TutorialButton = ({ tabId, variant = 'default' }) => {
  const {
    startTutorial,
    completedTabs,
    isActive,
    tutorialEnabled,
    autoShowTutorial,
    toggleTutorialEnabled,
    toggleAutoShowTutorial,
    resetTutorials,
    resetTabTutorial
  } = useTutorial()

  const [showSettings, setShowSettings] = useState(false)

  // 해당 탭에 튜토리얼이 없으면 렌더링 안함
  if (!TUTORIAL_STEPS[tabId]) return null

  const isCompleted = completedTabs.includes(tabId)
  const stepCount = TUTORIAL_STEPS[tabId].length

  const handleClick = () => {
    if (!isActive && tutorialEnabled) {
      startTutorial(tabId)
    }
  }

  const handleResetAndStart = () => {
    resetTabTutorial(tabId)
    setTimeout(() => {
      startTutorial(tabId)
    }, 100)
  }

  // 설정 팝업
  const SettingsPopup = () => (
    <AnimatePresence>
      {showSettings && (
        <motion.div
          className="tutorial-settings-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setShowSettings(false)}
        >
          <motion.div
            className="tutorial-settings-popup"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="settings-header">
              <h3>📚 튜토리얼 설정</h3>
              <button className="close-btn" onClick={() => setShowSettings(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="settings-body">
              {/* 튜토리얼 온/오프 */}
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-label">튜토리얼 기능</span>
                  <span className="setting-desc">튜토리얼 버튼 표시 및 기능 활성화</span>
                </div>
                <button
                  className={`toggle-btn ${tutorialEnabled ? 'active' : ''}`}
                  onClick={toggleTutorialEnabled}
                >
                  {tutorialEnabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                </button>
              </div>

              {/* 자동 튜토리얼 */}
              <div className="setting-item">
                <div className="setting-info">
                  <span className="setting-label">처음 방문 시 자동 시작</span>
                  <span className="setting-desc">새 탭 방문 시 튜토리얼 자동 표시</span>
                </div>
                <button
                  className={`toggle-btn ${autoShowTutorial ? 'active' : ''}`}
                  onClick={toggleAutoShowTutorial}
                  disabled={!tutorialEnabled}
                >
                  {autoShowTutorial ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                </button>
              </div>

              {/* 완료 현황 */}
              <div className="setting-item completed-status">
                <div className="setting-info">
                  <span className="setting-label">완료한 튜토리얼</span>
                  <span className="setting-desc">
                    {completedTabs.length}개 / {Object.keys(TUTORIAL_STEPS).length}개 완료
                  </span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${(completedTabs.length / Object.keys(TUTORIAL_STEPS).length) * 100}%` }}
                  />
                </div>
              </div>

              {/* 초기화 버튼 */}
              <div className="setting-actions">
                <button className="reset-btn" onClick={resetTutorials}>
                  <RefreshCw size={16} />
                  <span>모든 튜토리얼 초기화</span>
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )

  if (variant === 'floating') {
    // 튜토리얼이 비활성화되어 있으면 설정 버튼만 표시
    if (!tutorialEnabled) {
      return (
        <>
          <motion.button
            className="tutorial-btn-floating disabled-mode"
            onClick={() => setShowSettings(true)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Settings size={18} />
            <span>튜토리얼 OFF</span>
          </motion.button>
          <SettingsPopup />
        </>
      )
    }

    return (
      <>
        <div className="tutorial-floating-container">
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
                <span>튜토리얼 ({stepCount}단계)</span>
              </>
            )}
          </motion.button>

          <motion.button
            className="tutorial-settings-btn"
            onClick={() => setShowSettings(true)}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
          >
            <Settings size={16} />
          </motion.button>
        </div>
        <SettingsPopup />
      </>
    )
  }

  if (variant === 'banner') {
    if (!tutorialEnabled) return null
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
            <h4>처음이신가요? 🎉</h4>
            <p>이 기능의 사용법을 {stepCount}단계로 쉽고 친절하게 알려드릴게요!</p>
          </div>
        </div>
        <div className="banner-actions">
          <button className="banner-btn" onClick={handleClick}>
            <PlayCircle size={18} />
            튜토리얼 시작
          </button>
          <button
            className="banner-settings-btn"
            onClick={() => setShowSettings(true)}
            title="튜토리얼 설정"
          >
            <Settings size={16} />
          </button>
        </div>
        <SettingsPopup />
      </motion.div>
    )
  }

  // default variant
  if (!tutorialEnabled) {
    return (
      <>
        <motion.button
          className="tutorial-btn disabled-mode"
          onClick={() => setShowSettings(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Settings size={16} />
          <span>튜토리얼 설정</span>
        </motion.button>
        <SettingsPopup />
      </>
    )
  }

  return (
    <>
      <motion.button
        className={`tutorial-btn ${isCompleted ? 'completed' : ''}`}
        onClick={isCompleted ? handleResetAndStart : handleClick}
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
      <SettingsPopup />
    </>
  )
}

export default TutorialButton
