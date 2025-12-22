import React, { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  Lightbulb,
  MousePointer,
  ArrowRight
} from 'lucide-react'
import { useTutorial } from '../contexts/TutorialContext'
import '../styles/TutorialOverlay.css'

const TutorialOverlay = () => {
  const {
    isActive,
    currentStep,
    nextStep,
    prevStep,
    endTutorial,
    skipTutorial,
    getCurrentStepData,
    getTotalSteps
  } = useTutorial()

  const [targetRect, setTargetRect] = useState(null)
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 })
  const tooltipRef = useRef(null)

  const stepData = getCurrentStepData()
  const totalSteps = getTotalSteps()

  useEffect(() => {
    if (!isActive || !stepData) return

    const findTarget = () => {
      const target = document.querySelector(stepData.target)
      if (target) {
        const rect = target.getBoundingClientRect()
        setTargetRect(rect)

        // 타겟 요소로 스크롤
        target.scrollIntoView({ behavior: 'smooth', block: 'center' })

        // 툴팁 위치 계산
        setTimeout(() => {
          calculateTooltipPosition(rect, stepData.position)
        }, 100)
      } else {
        setTargetRect(null)
      }
    }

    // 약간의 딜레이 후 타겟 찾기 (DOM 렌더링 대기)
    const timer = setTimeout(findTarget, 300)

    // 윈도우 리사이즈 시 재계산
    window.addEventListener('resize', findTarget)

    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', findTarget)
    }
  }, [isActive, stepData, currentStep])

  const calculateTooltipPosition = (rect, position) => {
    if (!tooltipRef.current) return

    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const padding = 20
    let top, left

    switch (position) {
      case 'top':
        top = rect.top - tooltipRect.height - padding
        left = rect.left + (rect.width / 2) - (tooltipRect.width / 2)
        break
      case 'bottom':
        top = rect.bottom + padding
        left = rect.left + (rect.width / 2) - (tooltipRect.width / 2)
        break
      case 'left':
        top = rect.top + (rect.height / 2) - (tooltipRect.height / 2)
        left = rect.left - tooltipRect.width - padding
        break
      case 'right':
        top = rect.top + (rect.height / 2) - (tooltipRect.height / 2)
        left = rect.right + padding
        break
      default:
        top = rect.bottom + padding
        left = rect.left + (rect.width / 2) - (tooltipRect.width / 2)
    }

    // 화면 밖으로 나가지 않게 조정
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    if (left < padding) left = padding
    if (left + tooltipRect.width > viewportWidth - padding) {
      left = viewportWidth - tooltipRect.width - padding
    }
    if (top < padding) top = rect.bottom + padding
    if (top + tooltipRect.height > viewportHeight - padding) {
      top = rect.top - tooltipRect.height - padding
    }

    setTooltipPosition({ top, left })
  }

  const handleKeyDown = (e) => {
    if (!isActive) return
    if (e.key === 'Escape') skipTutorial()
    if (e.key === 'ArrowRight' || e.key === 'Enter') nextStep()
    if (e.key === 'ArrowLeft') prevStep()
  }

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isActive])

  if (!isActive || !stepData) return null

  return (
    <AnimatePresence>
      <div className="tutorial-overlay">
        {/* 배경 오버레이 */}
        <motion.div
          className="tutorial-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={skipTutorial}
        />

        {/* 하이라이트 영역 */}
        {targetRect && (
          <motion.div
            className="tutorial-highlight"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
              top: targetRect.top - 8,
              left: targetRect.left - 8,
              width: targetRect.width + 16,
              height: targetRect.height + 16
            }}
          >
            {stepData.highlight && (
              <motion.div
                className="highlight-pulse"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </motion.div>
        )}

        {/* 화살표 */}
        {targetRect && (
          <motion.div
            className={`tutorial-arrow ${stepData.position}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={getArrowStyle(targetRect, stepData.position)}
          >
            <ArrowRight size={24} />
          </motion.div>
        )}

        {/* 툴팁 */}
        <motion.div
          ref={tooltipRef}
          className="tutorial-tooltip"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          style={{
            top: tooltipPosition.top,
            left: tooltipPosition.left
          }}
        >
          {/* 헤더 */}
          <div className="tooltip-header">
            <div className="tooltip-icon">
              <Lightbulb size={20} />
            </div>
            <div className="tooltip-title">{stepData.title}</div>
            <button className="tooltip-close" onClick={skipTutorial}>
              <X size={18} />
            </button>
          </div>

          {/* 내용 */}
          <div className="tooltip-content">
            <p>{stepData.content}</p>

            {stepData.action && (
              <div className="tooltip-action-hint">
                <MousePointer size={16} />
                <span>
                  {stepData.action === 'click' && '클릭해보세요!'}
                  {stepData.action === 'select' && '선택해보세요!'}
                  {stepData.action === 'input' && '입력해보세요!'}
                </span>
              </div>
            )}
          </div>

          {/* 진행 표시 */}
          <div className="tooltip-progress">
            <div className="progress-dots">
              {Array.from({ length: totalSteps }).map((_, i) => (
                <div
                  key={i}
                  className={`progress-dot ${i === currentStep ? 'active' : ''} ${i < currentStep ? 'completed' : ''}`}
                />
              ))}
            </div>
            <span className="progress-text">
              {currentStep + 1} / {totalSteps}
            </span>
          </div>

          {/* 버튼 */}
          <div className="tooltip-actions">
            <button
              className="tooltip-btn secondary"
              onClick={prevStep}
              disabled={currentStep === 0}
            >
              <ChevronLeft size={18} />
              이전
            </button>

            {currentStep === totalSteps - 1 ? (
              <button className="tooltip-btn primary complete" onClick={endTutorial}>
                <CheckCircle size={18} />
                완료!
              </button>
            ) : (
              <button className="tooltip-btn primary" onClick={nextStep}>
                다음
                <ChevronRight size={18} />
              </button>
            )}
          </div>

          {/* 건너뛰기 */}
          <button className="tooltip-skip" onClick={skipTutorial}>
            튜토리얼 건너뛰기
          </button>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

const getArrowStyle = (rect, position) => {
  const padding = 12
  switch (position) {
    case 'top':
      return {
        top: rect.top - 40,
        left: rect.left + rect.width / 2 - 12,
        transform: 'rotate(90deg)'
      }
    case 'bottom':
      return {
        top: rect.bottom + padding,
        left: rect.left + rect.width / 2 - 12,
        transform: 'rotate(90deg)'
      }
    case 'left':
      return {
        top: rect.top + rect.height / 2 - 12,
        left: rect.left - 40,
        transform: 'rotate(180deg)'
      }
    case 'right':
      return {
        top: rect.top + rect.height / 2 - 12,
        left: rect.right + padding,
        transform: 'rotate(0deg)'
      }
    default:
      return {}
  }
}

export default TutorialOverlay
