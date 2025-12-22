import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  Shield,
  FileText,
  Send,
  Copy,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  BookOpen,
  History,
  BarChart3,
  Trash2,
  Edit3,
  Clipboard,
  AlertCircle,
  Info,
  Check
} from 'lucide-react'
import '../styles/IssueResponseManager.css'

const IssueResponseManager = ({ apiBaseUrl, showNotification }) => {
  // 탭 관리
  const [activeTab, setActiveTab] = useState('new') // new, guides, history, stats

  // 새 문제 분석 상태
  const [issueContent, setIssueContent] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)

  // 답변 생성 상태
  const [responseType, setResponseType] = useState('appeal')
  const [additionalContext, setAdditionalContext] = useState('')
  const [sellerName, setSellerName] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generatedResponse, setGeneratedResponse] = useState(null)
  const [copied, setCopied] = useState(false)

  // 가이드라인 상태
  const [guides, setGuides] = useState({})
  const [expandedGuide, setExpandedGuide] = useState(null)
  const [expandedSubtype, setExpandedSubtype] = useState(null)

  // 이력 상태
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [selectedHistory, setSelectedHistory] = useState(null)

  // 통계 상태
  const [statistics, setStatistics] = useState(null)

  // 초기 로드
  useEffect(() => {
    loadGuides()
  }, [])

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory()
    } else if (activeTab === 'stats') {
      loadStatistics()
    }
  }, [activeTab])

  // API 함수들
  const loadGuides = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/issue-response/guides`)
      if (res.data.success) {
        setGuides(res.data.data)
      }
    } catch (error) {
      console.error('가이드라인 로드 실패:', error)
    }
  }

  const loadHistory = async () => {
    try {
      setHistoryLoading(true)
      const res = await axios.get(`${apiBaseUrl}/issue-response/history?limit=50`)
      if (res.data.success) {
        setHistory(res.data.data)
      }
    } catch (error) {
      console.error('이력 로드 실패:', error)
      showNotification?.('이력 로드에 실패했습니다', 'error')
    } finally {
      setHistoryLoading(false)
    }
  }

  const loadStatistics = async () => {
    try {
      const res = await axios.get(`${apiBaseUrl}/issue-response/statistics`)
      if (res.data.success) {
        setStatistics(res.data.data)
      }
    } catch (error) {
      console.error('통계 로드 실패:', error)
    }
  }

  const analyzeIssue = async () => {
    if (!issueContent.trim()) {
      showNotification?.('문제 내용을 입력해주세요', 'warning')
      return
    }

    try {
      setAnalyzing(true)
      setAnalysisResult(null)
      setGeneratedResponse(null)

      const res = await axios.post(`${apiBaseUrl}/issue-response/analyze`, {
        content: issueContent
      })

      if (res.data.success) {
        setAnalysisResult(res.data.data)
        showNotification?.('분석이 완료되었습니다', 'success')
      }
    } catch (error) {
      console.error('분석 실패:', error)
      showNotification?.('분석 중 오류가 발생했습니다', 'error')
    } finally {
      setAnalyzing(false)
    }
  }

  const generateResponse = async () => {
    if (!analysisResult) {
      showNotification?.('먼저 문제를 분석해주세요', 'warning')
      return
    }

    try {
      setGenerating(true)

      const res = await axios.post(`${apiBaseUrl}/issue-response/generate`, {
        issue_id: analysisResult.id,
        response_type: responseType,
        additional_context: additionalContext,
        seller_name: sellerName
      })

      if (res.data.success) {
        setGeneratedResponse(res.data.data)
        showNotification?.('답변이 생성되었습니다', 'success')
      }
    } catch (error) {
      console.error('답변 생성 실패:', error)
      showNotification?.('답변 생성 중 오류가 발생했습니다', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const copyToClipboard = async () => {
    if (!generatedResponse?.generated_response) return

    try {
      await navigator.clipboard.writeText(generatedResponse.generated_response)
      setCopied(true)
      showNotification?.('클립보드에 복사되었습니다', 'success')

      // 상태 업데이트
      await axios.put(`${apiBaseUrl}/issue-response/${analysisResult.id}/status`, {
        status: 'copied'
      })

      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      showNotification?.('복사에 실패했습니다', 'error')
    }
  }

  const deleteHistoryItem = async (issueId) => {
    if (!window.confirm('이 이력을 삭제하시겠습니까?')) return

    try {
      await axios.delete(`${apiBaseUrl}/issue-response/${issueId}`)
      showNotification?.('삭제되었습니다', 'success')
      loadHistory()
    } catch (error) {
      showNotification?.('삭제에 실패했습니다', 'error')
    }
  }

  const markAsResolved = async (issueId) => {
    try {
      await axios.put(`${apiBaseUrl}/issue-response/${issueId}/status`, {
        status: 'resolved'
      })
      showNotification?.('해결 완료로 표시되었습니다', 'success')
      loadHistory()
      loadStatistics()
    } catch (error) {
      showNotification?.('상태 변경에 실패했습니다', 'error')
    }
  }

  // 심각도 배지 렌더링
  const renderSeverityBadge = (severity) => {
    const severityConfig = {
      critical: { color: '#ef4444', text: '위험', icon: AlertTriangle },
      high: { color: '#f97316', text: '높음', icon: AlertCircle },
      medium: { color: '#eab308', text: '보통', icon: Info },
      low: { color: '#22c55e', text: '낮음', icon: Check }
    }
    const config = severityConfig[severity] || severityConfig.medium
    const Icon = config.icon

    return (
      <span className="severity-badge" style={{ backgroundColor: `${config.color}20`, color: config.color }}>
        <Icon size={14} />
        {config.text}
      </span>
    )
  }

  // 문제 유형 이름 반환
  const getIssueTypeName = (type) => {
    const names = {
      ip_infringement: '지재권 침해',
      reseller: '리셀러/재판매',
      suspension: '상품 삭제/정지',
      other: '기타 문제'
    }
    return names[type] || type
  }

  // 탭 렌더링
  const renderTabs = () => (
    <div className="issue-tabs">
      <button
        className={`tab-btn ${activeTab === 'new' ? 'active' : ''}`}
        onClick={() => setActiveTab('new')}
      >
        <FileText size={18} />
        새 문제
      </button>
      <button
        className={`tab-btn ${activeTab === 'guides' ? 'active' : ''}`}
        onClick={() => setActiveTab('guides')}
      >
        <BookOpen size={18} />
        가이드라인
      </button>
      <button
        className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
        onClick={() => setActiveTab('history')}
      >
        <History size={18} />
        이력
      </button>
      <button
        className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
        onClick={() => setActiveTab('stats')}
      >
        <BarChart3 size={18} />
        통계
      </button>
    </div>
  )

  // 새 문제 분석 탭
  const renderNewIssueTab = () => (
    <div className="new-issue-container">
      {/* 입력 섹션 */}
      <div className="issue-input-section">
        <h3>
          <Clipboard size={20} />
          문제 내용 입력
        </h3>
        <p className="help-text">
          쿠팡에서 받은 메일이나 알림 내용을 붙여넣기 해주세요
        </p>
        <textarea
          className="issue-textarea"
          placeholder="메일/알림 내용을 붙여넣기 해주세요..."
          value={issueContent}
          onChange={(e) => setIssueContent(e.target.value)}
          rows={8}
        />
        <button
          className="analyze-btn"
          onClick={analyzeIssue}
          disabled={analyzing || !issueContent.trim()}
        >
          {analyzing ? (
            <>
              <RefreshCw size={18} className="spinning" />
              분석 중...
            </>
          ) : (
            <>
              <Shield size={18} />
              분석하기
            </>
          )}
        </button>
      </div>

      {/* 분석 결과 */}
      <AnimatePresence>
        {analysisResult && (
          <motion.div
            className="analysis-result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <h3>
              <CheckCircle size={20} />
              분석 결과
            </h3>

            <div className="result-grid">
              <div className="result-item">
                <span className="label">문제 유형</span>
                <span className="value">{analysisResult.issue_type_name}</span>
              </div>
              <div className="result-item">
                <span className="label">세부 유형</span>
                <span className="value">
                  {analysisResult.subtype_info?.name || analysisResult.issue_subtype || '-'}
                </span>
              </div>
              <div className="result-item">
                <span className="label">심각도</span>
                {renderSeverityBadge(analysisResult.severity)}
              </div>
              {analysisResult.deadline && (
                <div className="result-item">
                  <span className="label">대응 기한</span>
                  <span className="value deadline">
                    <Clock size={14} />
                    {analysisResult.deadline}
                  </span>
                </div>
              )}
            </div>

            <div className="result-summary">
              <strong>요약:</strong> {analysisResult.summary}
            </div>

            {analysisResult.recommended_actions?.length > 0 && (
              <div className="recommended-actions">
                <strong>권장 조치:</strong>
                <ul>
                  {analysisResult.recommended_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            )}

            {analysisResult.subtype_info?.checklist && (
              <div className="checklist-section">
                <strong>체크리스트:</strong>
                <ul className="checklist">
                  {analysisResult.subtype_info.checklist.map((item, idx) => (
                    <li key={idx}>
                      <input type="checkbox" id={`check-${idx}`} />
                      <label htmlFor={`check-${idx}`}>{item}</label>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 답변 생성 섹션 */}
      <AnimatePresence>
        {analysisResult && (
          <motion.div
            className="response-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h3>
              <Edit3 size={20} />
              답변 생성
            </h3>

            <div className="response-options">
              <div className="option-group">
                <label>답변 유형</label>
                <div className="radio-group">
                  <label className={responseType === 'appeal' ? 'selected' : ''}>
                    <input
                      type="radio"
                      name="responseType"
                      value="appeal"
                      checked={responseType === 'appeal'}
                      onChange={(e) => setResponseType(e.target.value)}
                    />
                    이의제기서
                  </label>
                  <label className={responseType === 'statement' ? 'selected' : ''}>
                    <input
                      type="radio"
                      name="responseType"
                      value="statement"
                      checked={responseType === 'statement'}
                      onChange={(e) => setResponseType(e.target.value)}
                    />
                    소명서
                  </label>
                  <label className={responseType === 'report' ? 'selected' : ''}>
                    <input
                      type="radio"
                      name="responseType"
                      value="report"
                      checked={responseType === 'report'}
                      onChange={(e) => setResponseType(e.target.value)}
                    />
                    신고 답변
                  </label>
                </div>
              </div>

              <div className="option-group">
                <label>판매자 이름</label>
                <input
                  type="text"
                  placeholder="(주)OOO 또는 홍길동"
                  value={sellerName}
                  onChange={(e) => setSellerName(e.target.value)}
                />
              </div>

              <div className="option-group">
                <label>추가 설명 (선택)</label>
                <textarea
                  placeholder="정품 인증서 보유, 직접 촬영 이미지 등..."
                  value={additionalContext}
                  onChange={(e) => setAdditionalContext(e.target.value)}
                  rows={3}
                />
              </div>
            </div>

            <button
              className="generate-btn"
              onClick={generateResponse}
              disabled={generating}
            >
              {generating ? (
                <>
                  <RefreshCw size={18} className="spinning" />
                  생성 중...
                </>
              ) : (
                <>
                  <Send size={18} />
                  답변 생성
                </>
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 생성된 답변 */}
      <AnimatePresence>
        {generatedResponse && (
          <motion.div
            className="generated-response"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="response-header">
              <h3>
                <FileText size={20} />
                생성된 답변
              </h3>
              <div className="response-meta">
                <span className="confidence">
                  신뢰도: {generatedResponse.confidence}%
                </span>
                <button
                  className={`copy-btn ${copied ? 'copied' : ''}`}
                  onClick={copyToClipboard}
                >
                  {copied ? (
                    <>
                      <CheckCircle size={16} />
                      복사됨
                    </>
                  ) : (
                    <>
                      <Copy size={16} />
                      복사하기
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="response-content">
              <pre>{generatedResponse.generated_response}</pre>
            </div>

            {generatedResponse.suggestions?.length > 0 && (
              <div className="suggestions">
                <strong>첨부 권장 서류:</strong>
                <ul>
                  {generatedResponse.suggestions.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )

  // 가이드라인 탭
  const renderGuidesTab = () => (
    <div className="guides-container">
      {Object.entries(guides).map(([type, guide]) => (
        <div key={type} className="guide-card">
          <div
            className="guide-header"
            onClick={() => setExpandedGuide(expandedGuide === type ? null : type)}
          >
            <div className="guide-title">
              <Shield size={20} />
              <span>{guide.title}</span>
            </div>
            {expandedGuide === type ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
          </div>

          <AnimatePresence>
            {expandedGuide === type && (
              <motion.div
                className="guide-content"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <p className="guide-description">{guide.description}</p>

                <div className="subtypes-list">
                  {guide.subtypes?.map((subtype) => (
                    <div key={subtype.id} className="subtype-item">
                      <div
                        className="subtype-header"
                        onClick={() => setExpandedSubtype(
                          expandedSubtype === subtype.id ? null : subtype.id
                        )}
                      >
                        <span className="subtype-name">{subtype.name}</span>
                        {renderSeverityBadge(subtype.severity_default)}
                        {expandedSubtype === subtype.id ?
                          <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </div>

                      <AnimatePresence>
                        {expandedSubtype === subtype.id && (
                          <motion.div
                            className="subtype-content"
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                          >
                            <p>{subtype.description}</p>

                            {subtype.checklist?.length > 0 && (
                              <div className="guide-section">
                                <h4>체크리스트</h4>
                                <ul>
                                  {subtype.checklist.map((item, idx) => (
                                    <li key={idx}>{item}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {subtype.tips?.length > 0 && (
                              <div className="guide-section">
                                <h4>대응 팁</h4>
                                <ul>
                                  {subtype.tips.map((tip, idx) => (
                                    <li key={idx}>{tip}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {subtype.required_documents?.length > 0 && (
                              <div className="guide-section">
                                <h4>필요 서류</h4>
                                <ul>
                                  {subtype.required_documents.map((doc, idx) => (
                                    <li key={idx}>{doc}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>

                {guide.legal_references?.length > 0 && (
                  <div className="legal-references">
                    <h4>관련 법규</h4>
                    <ul>
                      {guide.legal_references.map((ref, idx) => (
                        <li key={idx}>{ref}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {guide.common_mistakes?.length > 0 && (
                  <div className="common-mistakes">
                    <h4>흔한 실수</h4>
                    <ul>
                      {guide.common_mistakes.map((mistake, idx) => (
                        <li key={idx}><XCircle size={14} /> {mistake}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )

  // 이력 탭
  const renderHistoryTab = () => (
    <div className="history-container">
      <div className="history-header">
        <h3>
          <History size={20} />
          대응 이력
        </h3>
        <button className="refresh-btn" onClick={loadHistory} disabled={historyLoading}>
          <RefreshCw size={16} className={historyLoading ? 'spinning' : ''} />
          새로고침
        </button>
      </div>

      {historyLoading ? (
        <div className="loading-state">
          <RefreshCw size={32} className="spinning" />
          <p>로딩 중...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="empty-state">
          <History size={48} />
          <p>아직 대응 이력이 없습니다</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((item) => (
            <div key={item.id} className="history-item">
              <div className="history-main">
                <div className="history-type">
                  {getIssueTypeName(item.issue_type)}
                  {item.issue_subtype && ` - ${item.issue_subtype}`}
                </div>
                <div className="history-summary">{item.summary}</div>
                <div className="history-meta">
                  {renderSeverityBadge(item.severity)}
                  <span className={`status-badge ${item.status}`}>
                    {item.status === 'resolved' ? '해결됨' :
                     item.status === 'copied' ? '복사됨' : '초안'}
                  </span>
                  <span className="date">
                    {new Date(item.created_at).toLocaleDateString('ko-KR')}
                  </span>
                </div>
              </div>
              <div className="history-actions">
                {item.status !== 'resolved' && (
                  <button
                    className="action-btn resolve"
                    onClick={() => markAsResolved(item.id)}
                    title="해결 완료"
                  >
                    <CheckCircle size={16} />
                  </button>
                )}
                <button
                  className="action-btn delete"
                  onClick={() => deleteHistoryItem(item.id)}
                  title="삭제"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // 통계 탭
  const renderStatsTab = () => (
    <div className="stats-container">
      {!statistics ? (
        <div className="loading-state">
          <RefreshCw size={32} className="spinning" />
          <p>로딩 중...</p>
        </div>
      ) : (
        <>
          <div className="stats-overview">
            <div className="stat-card total">
              <div className="stat-value">{statistics.total}</div>
              <div className="stat-label">전체 문제</div>
            </div>
            <div className="stat-card resolved">
              <div className="stat-value">{statistics.resolved}</div>
              <div className="stat-label">해결됨</div>
            </div>
            <div className="stat-card pending">
              <div className="stat-value">{statistics.pending}</div>
              <div className="stat-label">대기 중</div>
            </div>
            <div className="stat-card rate">
              <div className="stat-value">{statistics.resolution_rate}%</div>
              <div className="stat-label">해결률</div>
            </div>
          </div>

          <div className="stats-details">
            <div className="stats-section">
              <h4>문제 유형별</h4>
              <div className="type-stats">
                {Object.entries(statistics.by_type || {}).map(([type, data]) => (
                  <div key={type} className="type-stat-item">
                    <span className="type-name">{data.name}</span>
                    <span className="type-count">{data.count}건</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="stats-section">
              <h4>심각도별</h4>
              <div className="severity-stats">
                {Object.entries(statistics.by_severity || {}).map(([severity, count]) => (
                  <div key={severity} className="severity-stat-item">
                    {renderSeverityBadge(severity)}
                    <span className="severity-count">{count}건</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )

  return (
    <motion.div
      className="issue-response-manager"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="manager-header">
        <h2>
          <AlertTriangle size={24} />
          문제 대응 센터
        </h2>
        <p>쿠팡 판매 관련 문제에 대한 가이드라인 및 자동 답변 생성</p>
      </div>

      {renderTabs()}

      <div className="tab-content">
        {activeTab === 'new' && renderNewIssueTab()}
        {activeTab === 'guides' && renderGuidesTab()}
        {activeTab === 'history' && renderHistoryTab()}
        {activeTab === 'stats' && renderStatsTab()}
      </div>
    </motion.div>
  )
}

export default IssueResponseManager
