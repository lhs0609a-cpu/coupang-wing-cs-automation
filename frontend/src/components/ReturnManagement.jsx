import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import {
  PackageX,
  RefreshCw,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Filter,
  Download,
  Settings,
  Save
} from 'lucide-react'
import '../styles/ReturnManagement.css'

const ReturnManagement = ({ apiBaseUrl, showNotification }) => {
  const [returns, setReturns] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [selectedReturns, setSelectedReturns] = useState([])
  const [filterStatus, setFilterStatus] = useState('all')
  const [naverProcessed, setNaverProcessed] = useState(null)

  // 연결 상태
  const [connectionStatus, setConnectionStatus] = useState({
    coupang: { connected: false, loading: true },
    naver: { connected: false, loading: true }
  })

  // 저장된 계정 정보
  const [savedCoupangAccount, setSavedCoupangAccount] = useState(null)
  const [savedNaverAccount, setSavedNaverAccount] = useState(null)
  const [allCoupangAccounts, setAllCoupangAccounts] = useState([]) // 모든 쿠팡 계정
  const [allNaverAccounts, setAllNaverAccounts] = useState([]) // 모든 네이버 계정
  const [accountSets, setAccountSets] = useState([]) // 계정 세트 목록
  const [selectedAccountSetId, setSelectedAccountSetId] = useState(null) // 선택된 계정 세트 ID
  const [showCredentialsModal, setShowCredentialsModal] = useState(false)
  const [accountSetName, setAccountSetName] = useState('') // 세트 이름
  const [credentials, setCredentials] = useState({
    coupangAccessKey: '',
    coupangSecretKey: '',
    coupangVendorId: '',
    coupangUsername: '',
    coupangPassword: '',
    naverUsername: '',
    naverPassword: '',
    saveCredentials: false
  })

  // 실시간 처리 확인 모달
  const [showProcessingModal, setShowProcessingModal] = useState(false)
  const [currentProcessingItem, setCurrentProcessingItem] = useState(null)
  const [processingQueue, setProcessingQueue] = useState([])
  const [processedCount, setProcessedCount] = useState(0)
  const [skippedCount, setSkippedCount] = useState(0)
  const [processingItemIndex, setProcessingItemIndex] = useState(0)

  // 초기 로드: 계정 정보만 로드 (한 번만 실행)
  useEffect(() => {
    loadSavedAccounts()
    loadAccountSets()
    loadDefaultAccountSet() // 기본 계정 세트 자동 로드
  }, []) // 빈 배열 = 컴포넌트 마운트 시 한 번만 실행

  // 실시간 연결 상태 체크 (30초마다)
  useEffect(() => {
    const checkConnectionInterval = setInterval(() => {
      console.log('🔄 실시간 계정 연결 상태 확인 중...')
      loadSavedAccounts()
    }, 30000) // 30초마다 체크

    return () => clearInterval(checkConnectionInterval)
  }, [])

  // 반품 목록 로드: 필터가 변경될 때마다 실행
  useEffect(() => {
    loadReturns()
    loadStats()
  }, [filterStatus, naverProcessed])

  const loadSavedAccounts = async () => {
    try {
      // 쿠팡 계정 불러오기 (모든 계정)
      try {
        const coupangRes = await axios.get(`${apiBaseUrl}/coupang-accounts`)
        if (coupangRes.data && coupangRes.data.length > 0) {
          setAllCoupangAccounts(coupangRes.data) // 모든 계정 저장
          setSavedCoupangAccount(coupangRes.data[0]) // 첫 번째 계정을 기본으로
          console.log(`✅ 쿠팡 계정 ${coupangRes.data.length}개 불러오기 완료`)
          setConnectionStatus(prev => ({
            ...prev,
            coupang: { connected: true, loading: false }
          }))
        } else {
          setConnectionStatus(prev => ({
            ...prev,
            coupang: { connected: false, loading: false }
          }))
        }
      } catch (error) {
        console.log('ℹ️ 쿠팡 계정 없음')
        setConnectionStatus(prev => ({
          ...prev,
          coupang: { connected: false, loading: false }
        }))
      }

      // 네이버 계정 불러오기 (모든 계정)
      try {
        const naverListRes = await axios.get(`${apiBaseUrl}/naver-accounts`)
        if (naverListRes.data.success && naverListRes.data.data) {
          setAllNaverAccounts(naverListRes.data.data) // 모든 계정 저장
        }

        // 기본 계정 불러오기 (비밀번호 포함)
        const naverRes = await axios.get(`${apiBaseUrl}/naver-accounts/default/credentials`)
        if (naverRes.data.success && naverRes.data.data) {
          setSavedNaverAccount(naverRes.data.data)
          console.log('✅ 네이버 계정 불러오기 완료:', naverRes.data.data.name)
          showNotification?.(`저장된 네이버 계정을 불러왔습니다 (${naverRes.data.data.name})`, 'info')
          setConnectionStatus(prev => ({
            ...prev,
            naver: { connected: true, loading: false }
          }))
        } else {
          console.log('ℹ️ 저장된 네이버 계정이 없습니다')
          setConnectionStatus(prev => ({
            ...prev,
            naver: { connected: false, loading: false }
          }))
        }
      } catch (error) {
        console.log('ℹ️ 네이버 계정 없음 또는 불러오기 실패')
        setConnectionStatus(prev => ({
          ...prev,
          naver: { connected: false, loading: false }
        }))
      }
    } catch (error) {
      console.error('❌ 계정 불러오기 중 예상치 못한 오류:', error)
    }
  }

  const loadReturns = async () => {
    try {
      setLoading(true)
      const params = {
        limit: 100,
        offset: 0
      }

      if (filterStatus !== 'all') {
        params.status = filterStatus
      }

      if (naverProcessed !== null) {
        params.naver_processed = naverProcessed
      }

      const response = await axios.get(`${apiBaseUrl}/returns/list`, { params })
      setReturns(response.data.data || [])
    } catch (error) {
      console.error('반품 목록 로드 실패:', error)
      showNotification?.('반품 목록을 불러오는데 실패했습니다', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/returns/statistics`)
      setStats(response.data.statistics)
    } catch (error) {
      console.error('통계 로드 실패:', error)
    }
  }

  const fetchFromCoupang = async () => {
    // 쿠팡 계정 확인
    if (!savedCoupangAccount || !savedCoupangAccount.access_key) {
      showNotification?.('쿠팡 계정을 먼저 등록해주세요', 'error')
      setShowCredentialsModal(true)
      return
    }

    try {
      setLoading(true)

      const now = new Date()
      const totalDays = 30 // 최근 30일 데이터 조회
      const batchDays = 2 // 2일씩 나누어 요청 (타임아웃 방지 - 504 에러 해결)

      let totalFetched = 0
      let totalSaved = 0
      let totalUpdated = 0

      console.log(`📥 쿠팡 반품 조회 시작: 최근 ${totalDays}일 (${batchDays}일씩 분할)`)
      console.log(`   쿠팡 계정: ${savedCoupangAccount.name} (Vendor ID: ${savedCoupangAccount.vendor_id})`)

      // 30일을 2일씩 나누어 요청 (총 15번의 API 호출)
      for (let i = 0; i < totalDays; i += batchDays) {
        const batchEndDate = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
          .toISOString()
          .slice(0, 16)
        const batchStartDate = new Date(now.getTime() - (i + batchDays) * 24 * 60 * 60 * 1000)
          .toISOString()
          .slice(0, 16)

        console.log(`  📦 구간 ${Math.floor(i / batchDays) + 1}: ${batchStartDate} ~ ${batchEndDate}`)

        try {
          // 전체 조회 (RETURN: 반품, CANCEL: 출고중지 모두 가져오기)
          const response = await axios.get(`${apiBaseUrl}/returns/fetch-from-coupang`, {
            params: {
              start_date: batchStartDate,
              end_date: batchEndDate
              // cancel_type을 보내지 않으면 반품(RETURN) + 출고중지(CANCEL) 모두 조회
            }
          })

          const fetched = response.data.total_fetched || 0
          const saved = response.data.saved || 0
          const updated = response.data.updated || 0

          totalFetched += fetched
          totalSaved += saved
          totalUpdated += updated

          console.log(`    ✓ ${fetched}건 조회 (신규 ${saved}, 업데이트 ${updated})`)
        } catch (error) {
          console.error(`    ✗ 구간 조회 실패:`, error.message)
          // 한 구간이 실패해도 계속 진행
        }
      }

      showNotification?.(
        `쿠팡에서 총 ${totalFetched}건 조회 완료 (신규: ${totalSaved}, 업데이트: ${totalUpdated})`,
        'success'
      )
      console.log(`✅ 전체 조회 완료: 총 ${totalFetched}건 (신규 ${totalSaved}, 업데이트 ${totalUpdated})`)

      loadReturns()
      loadStats()
    } catch (error) {
      console.error('❌ 쿠팡 반품 조회 실패:', error)
      showNotification?.('쿠팡 반품 조회에 실패했습니다: ' + (error.response?.data?.detail || error.message), 'error')
    } finally {
      setLoading(false)
    }
  }

  const processNaverReturns = async () => {
    if (selectedReturns.length === 0) {
      showNotification?.('처리할 반품을 선택해주세요', 'error')
      return
    }

    let naverUsername, naverPassword

    // 저장된 계정이 있으면 사용
    if (savedNaverAccount && savedNaverAccount.username && savedNaverAccount.password) {
      naverUsername = savedNaverAccount.username
      naverPassword = savedNaverAccount.password
      console.log('✅ 저장된 네이버 계정 사용:', naverUsername)
    } else {
      // 저장된 계정이 없으면 입력 요청
      showNotification?.('네이버 계정을 먼저 등록해주세요', 'error')
      setShowCredentialsModal(true)
      return
    }

    try {
      setProcessing(true)

      const response = await axios.post(`${apiBaseUrl}/returns/process-naver`, {
        return_log_ids: selectedReturns,
        naver_credentials: {
          username: naverUsername,
          password: naverPassword
        },
        headless: false
      })

      if (response.data.success) {
        showNotification?.(
          `${response.data.statistics.processed}건 처리 완료`,
          'success'
        )
        setSelectedReturns([])
        loadReturns()
        loadStats()
      } else {
        showNotification?.(response.data.message, 'error')
      }
    } catch (error) {
      console.error('네이버 처리 실패:', error)
      showNotification?.('네이버 반품 처리에 실패했습니다', 'error')
    } finally {
      setProcessing(false)
    }
  }

  // 실시간 확인하며 반품을 하나씩 처리하는 함수
  const startAutoProcessing = async () => {
    // pending 상태이고 네이버 미처리인 반품들만 선택
    const pendingReturns = returns.filter(
      r => r.status === 'pending' && !r.naver_processed
    )

    if (pendingReturns.length === 0) {
      showNotification?.('처리할 반품이 없습니다', 'warning')
      return
    }

    // 네이버 계정 확인
    if (!savedNaverAccount || !savedNaverAccount.username || !savedNaverAccount.password) {
      showNotification?.('네이버 계정을 먼저 등록해주세요', 'error')
      setShowCredentialsModal(true)
      return
    }

    console.log(`🚀 실시간 확인 처리 시작: ${pendingReturns.length}건`)

    // 처리 대기열 설정
    setProcessingQueue(pendingReturns)
    setProcessedCount(0)
    setSkippedCount(0)
    setProcessingItemIndex(0)
    setCurrentProcessingItem(pendingReturns[0])
    setShowProcessingModal(true)
  }

  // 현재 항목 처리 확인 (사용자가 "확인" 버튼 클릭)
  const confirmCurrentItem = async () => {
    if (!currentProcessingItem) return

    const naverUsername = savedNaverAccount.username
    const naverPassword = savedNaverAccount.password

    try {
      setProcessing(true)

      const response = await axios.post(`${apiBaseUrl}/returns/process-naver`, {
        return_log_ids: [currentProcessingItem.id],
        naver_credentials: {
          username: naverUsername,
          password: naverPassword
        },
        headless: false
      })

      if (response.data.success) {
        showNotification?.(
          `✅ "${currentProcessingItem.product_name}" 처리 완료`,
          'success'
        )
        setProcessedCount(prev => prev + 1)
      } else {
        showNotification?.(
          `❌ "${currentProcessingItem.product_name}" 처리 실패: ${response.data.message}`,
          'error'
        )
      }
    } catch (error) {
      console.error('처리 실패:', error)
      showNotification?.(
        `❌ "${currentProcessingItem.product_name}" 처리 실패`,
        'error'
      )
    } finally {
      setProcessing(false)
      moveToNextItem()
    }
  }

  // 현재 항목 건너뛰기
  const skipCurrentItem = () => {
    showNotification?.(
      `⏭️ "${currentProcessingItem.product_name}" 건너뜀`,
      'info'
    )
    setSkippedCount(prev => prev + 1)
    moveToNextItem()
  }

  // 다음 항목으로 이동
  const moveToNextItem = () => {
    const nextIndex = processingItemIndex + 1

    if (nextIndex < processingQueue.length) {
      // 다음 항목으로 이동
      setProcessingItemIndex(nextIndex)
      setCurrentProcessingItem(processingQueue[nextIndex])
    } else {
      // 모든 항목 처리 완료
      showNotification?.(
        `🎉 처리 완료! (처리: ${processedCount + 1}건, 건너뜀: ${skippedCount}건)`,
        'success'
      )
      setShowProcessingModal(false)
      setCurrentProcessingItem(null)
      setProcessingQueue([])
      loadReturns()
      loadStats()
    }
  }

  // 처리 중단
  const cancelProcessing = () => {
    showNotification?.(
      `⚠️ 처리 중단됨 (처리: ${processedCount}건, 건너뜀: ${skippedCount}건)`,
      'warning'
    )
    setShowProcessingModal(false)
    setCurrentProcessingItem(null)
    setProcessingQueue([])
    loadReturns()
    loadStats()
  }

  const handleSaveCredentials = async () => {
    try {
      let naverSaved = false
      let coupangSaved = false

      // 네이버 계정 저장/업데이트 (아이디/비밀번호만 있으면 OK)
      if (credentials.naverUsername && credentials.naverPassword) {
        const naverPayload = {
          name: '반품 관리용 네이버 계정',
          client_id: credentials.naverUsername, // username을 client_id로 사용
          client_secret: 'naver_automation_secret', // Selenium 자동화용이므로 dummy 값
          callback_url: 'http://localhost:3000/naver/callback',
          naver_username: credentials.naverUsername,
          naver_password: credentials.naverPassword,
          is_default: true
        }

        // 기존 계정이 있으면 업데이트, 없으면 생성
        if (savedNaverAccount && savedNaverAccount.id) {
          await axios.put(`${apiBaseUrl}/naver-accounts/${savedNaverAccount.id}`, naverPayload)
          console.log('✅ 네이버 계정 업데이트 완료')
        } else {
          await axios.post(`${apiBaseUrl}/naver-accounts`, naverPayload)
          console.log('✅ 네이버 계정 생성 완료')
        }
        naverSaved = true
      }

      // 쿠팡 계정 저장/업데이트 (필수: Access Key, Secret Key, Vendor ID)
      if (credentials.coupangAccessKey && credentials.coupangSecretKey && credentials.coupangVendorId) {
        const coupangPayload = {
          name: '반품 관리용 쿠팡 계정',
          vendor_id: credentials.coupangVendorId,
          access_key: credentials.coupangAccessKey,
          secret_key: credentials.coupangSecretKey,
          wing_username: credentials.coupangUsername || credentials.coupangVendorId, // 기본값: vendor_id
          wing_password: credentials.coupangPassword || ''
        }

        // 기존 계정이 있으면 업데이트, 없으면 생성
        if (savedCoupangAccount && savedCoupangAccount.id) {
          await axios.put(`${apiBaseUrl}/coupang-accounts/${savedCoupangAccount.id}`, coupangPayload)
          console.log('✅ 쿠팡 계정 업데이트 완료')
        } else {
          await axios.post(`${apiBaseUrl}/coupang-accounts`, coupangPayload)
          console.log('✅ 쿠팡 계정 생성 완료')
        }
        coupangSaved = true
      }

      if (naverSaved || coupangSaved) {
        showNotification?.('계정 정보가 데이터베이스에 저장되었습니다. 어느 컴퓨터에서든 불러올 수 있습니다.', 'success')
      }

      // 계정 정보 새로고침 (DB에서 다시 불러오기)
      await loadSavedAccounts()
      setShowCredentialsModal(false)

      // 입력 필드 초기화
      setCredentials({
        coupangAccessKey: '',
        coupangSecretKey: '',
        coupangVendorId: '',
        coupangUsername: '',
        coupangPassword: '',
        naverUsername: '',
        naverPassword: '',
        saveCredentials: false
      })

      // 네이버 처리 다시 시도
      if (selectedReturns.length > 0) {
        setTimeout(() => processNaverReturns(), 500)
      }
    } catch (error) {
      console.error('❌ 계정 저장 실패:', error)
      const errorMsg = error.response?.data?.detail || error.message

      // 중복 에러 처리
      if (errorMsg && errorMsg.includes('already exists')) {
        showNotification?.('이미 등록된 계정입니다. 업데이트를 시도합니다...', 'warning')
        // 계정 다시 불러오기
        await loadSavedAccounts()
      } else {
        showNotification?.('계정 저장에 실패했습니다: ' + errorMsg, 'error')
      }
    }
  }

  const handleSelectReturn = (returnId) => {
    setSelectedReturns((prev) =>
      prev.includes(returnId)
        ? prev.filter((id) => id !== returnId)
        : [...prev, returnId]
    )
  }

  const handleSelectAll = () => {
    if (selectedReturns.length === returns.length) {
      setSelectedReturns([])
    } else {
      setSelectedReturns(returns.filter(r => !r.naver_processed).map((r) => r.id))
    }
  }

  // 저장된 쿠팡 계정 선택
  const handleSelectCoupangAccount = async (accountId) => {
    if (!accountId) return

    const account = allCoupangAccounts.find(acc => acc.id === parseInt(accountId))
    if (account) {
      setCredentials({
        ...credentials,
        coupangAccessKey: account.access_key,
        coupangSecretKey: account.secret_key,
        coupangVendorId: account.vendor_id,
        coupangUsername: account.wing_username || '',
        coupangPassword: '' // 비밀번호는 보안상 비워둠
      })
      console.log(`✅ 쿠팡 계정 선택: ${account.name}`)
      showNotification?.(`쿠팡 계정 "${account.name}"을(를) 불러왔습니다`, 'info')
    }
  }

  // 저장된 네이버 계정 선택
  const handleSelectNaverAccount = async (accountId) => {
    if (!accountId) return

    try {
      // 비밀번호를 포함한 전체 정보를 서버에서 가져오기
      const response = await axios.get(`${apiBaseUrl}/naver-accounts/${accountId}`, {
        params: { include_secrets: true }
      })

      if (response.data.success && response.data.data) {
        const account = response.data.data
        setCredentials({
          ...credentials,
          naverUsername: account.naver_username || '',
          naverPassword: account.naver_password || ''
        })
        console.log(`✅ 네이버 계정 선택: ${account.name}`)
        showNotification?.(`네이버 계정 "${account.name}"을(를) 불러왔습니다`, 'info')
      }
    } catch (error) {
      console.error('네이버 계정 불러오기 실패:', error)
      showNotification?.('네이버 계정 불러오기에 실패했습니다', 'error')
    }
  }

  // 계정 세트 목록 로드
  const loadAccountSets = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/account-sets`)
      if (response.data.success && response.data.data) {
        setAccountSets(response.data.data)
        console.log(`✅ 계정 세트 ${response.data.count}개 불러오기 완료`)
      }
    } catch (error) {
      console.log('ℹ️ 계정 세트 없음')
    }
  }

  // 기본 계정 세트 자동 로드 (페이지 로드 시 자동으로 계정 정보 채우기)
  const loadDefaultAccountSet = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/account-sets/default`)
      if (response.data.success && response.data.data) {
        const set = response.data.data

        // 세트 이름 설정
        setAccountSetName(set.name)

        // 쿠팡 + 네이버 정보 모두 자동 입력
        setCredentials({
          coupangAccessKey: set.coupang_account?.access_key || '',
          coupangSecretKey: set.coupang_account?.secret_key || '',
          coupangVendorId: set.coupang_account?.vendor_id || '',
          coupangUsername: set.coupang_account?.wing_username || '',
          coupangPassword: set.coupang_account?.wing_password || '',
          naverUsername: set.naver_account?.naver_username || '',
          naverPassword: set.naver_account?.naver_password || '',
          saveCredentials: false
        })

        // savedCoupangAccount와 savedNaverAccount도 업데이트
        if (set.coupang_account) {
          setSavedCoupangAccount(set.coupang_account)
        }
        if (set.naver_account) {
          setSavedNaverAccount({
            id: set.naver_account.id,
            name: set.naver_account.name,
            username: set.naver_account.naver_username,
            password: set.naver_account.naver_password
          })
        }

        console.log(`✅ 기본 계정 세트 자동 로드 완료: ${set.name}`)
        showNotification?.(`저장된 계정 세트를 불러왔습니다: ${set.name} (쿠팡 + 네이버)`, 'success')
      }
    } catch (error) {
      console.log('ℹ️ 기본 계정 세트 없음 - 처음 사용 시 계정을 등록해주세요')
    }
  }

  // 계정 세트 선택 (쿠팡 + 네이버 통합)
  const handleSelectAccountSet = async (setId) => {
    if (!setId) {
      // 초기화
      setSelectedAccountSetId(null)
      setAccountSetName('')
      setCredentials({
        coupangAccessKey: '',
        coupangSecretKey: '',
        coupangVendorId: '',
        coupangUsername: '',
        coupangPassword: '',
        naverUsername: '',
        naverPassword: '',
        saveCredentials: false
      })
      return
    }

    try {
      const response = await axios.get(`${apiBaseUrl}/account-sets/${setId}`)
      if (response.data.success && response.data.data) {
        const set = response.data.data

        // 세트 이름 설정
        setAccountSetName(set.name)

        // 쿠팡 + 네이버 정보 모두 입력
        setCredentials({
          coupangAccessKey: set.coupang_account?.access_key || '',
          coupangSecretKey: set.coupang_account?.secret_key || '',
          coupangVendorId: set.coupang_account?.vendor_id || '',
          coupangUsername: set.coupang_account?.wing_username || '',
          coupangPassword: set.coupang_account?.wing_password || '',
          naverUsername: set.naver_account?.naver_username || '',
          naverPassword: set.naver_account?.naver_password || '',
          saveCredentials: false
        })

        setSelectedAccountSetId(setId)
        console.log(`✅ 계정 세트 선택: ${set.name}`)
        showNotification?.(`계정 세트 "${set.name}"을(를) 불러왔습니다 (쿠팡 + 네이버 통합)`, 'success')
      }
    } catch (error) {
      console.error('계정 세트 불러오기 실패:', error)
      showNotification?.('계정 세트 불러오기에 실패했습니다', 'error')
    }
  }

  // 계정 세트 삭제
  const handleDeleteAccountSet = async () => {
    if (!selectedAccountSetId) {
      showNotification?.('삭제할 계정 세트를 선택해주세요', 'warning')
      return
    }

    const confirmDelete = window.confirm('정말로 이 계정 세트를 삭제하시겠습니까?')
    if (!confirmDelete) return

    try {
      const response = await axios.delete(`${apiBaseUrl}/account-sets/${selectedAccountSetId}`)

      if (response.data.success) {
        showNotification?.(response.data.message, 'success')

        // 계정 세트 목록 새로고침
        await loadAccountSets()

        // 선택 초기화
        setSelectedAccountSetId(null)
        setAccountSetName('')
        setCredentials({
          coupangAccessKey: '',
          coupangSecretKey: '',
          coupangVendorId: '',
          coupangUsername: '',
          coupangPassword: '',
          naverUsername: '',
          naverPassword: '',
          saveCredentials: false
        })
      }
    } catch (error) {
      console.error('계정 세트 삭제 실패:', error)
      showNotification?.('계정 세트 삭제에 실패했습니다', 'error')
    }
  }

  // 계정 세트로 저장 (쿠팡 + 네이버 통합)
  const handleSaveAsAccountSet = async () => {
    if (!accountSetName) {
      showNotification?.('세트 이름을 입력하세요', 'error')
      return
    }

    try {
      const payload = {
        name: accountSetName,
        description: `쿠팡 + 네이버 계정 세트`,

        // 쿠팡 계정 정보
        coupang_account_name: `${accountSetName} - 쿠팡`,
        coupang_vendor_id: credentials.coupangVendorId,
        coupang_access_key: credentials.coupangAccessKey,
        coupang_secret_key: credentials.coupangSecretKey,
        coupang_wing_username: credentials.coupangUsername,
        coupang_wing_password: credentials.coupangPassword,

        // 네이버 계정 정보
        naver_account_name: `${accountSetName} - 네이버`,
        naver_username: credentials.naverUsername,
        naver_password: credentials.naverPassword,

        is_default: accountSets.length === 0 // 첫 번째 세트는 자동으로 기본 설정
      }

      const response = await axios.post(`${apiBaseUrl}/account-sets`, payload)

      if (response.data.success) {
        showNotification?.(`계정 세트 "${accountSetName}"이(가) 저장되었습니다! 다음에 자동으로 불러옵니다. (쿠팡 + 네이버 통합)`, 'success')

        // 계정 세트 목록 새로고침
        await loadAccountSets()
        await loadSavedAccounts()

        // 저장한 세트를 바로 기본 세트로 불러오기 (자동 로드 테스트)
        await loadDefaultAccountSet()

        setShowCredentialsModal(false)

        // 폼은 초기화하지 않음 - 저장된 데이터가 자동으로 로드됨
        console.log('✅ 계정 세트 저장 완료 및 자동 로드 완료')
      }
    } catch (error) {
      console.error('계정 세트 저장 실패:', error)
      const errorMsg = error.response?.data?.detail || error.message
      showNotification?.('계정 세트 저장에 실패했습니다: ' + errorMsg, 'error')
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { label: '대기', color: 'badge-pending' },
      processing: { label: '처리중', color: 'badge-processing' },
      completed: { label: '완료', color: 'badge-completed' },
      failed: { label: '실패', color: 'badge-failed' }
    }

    const statusInfo = statusMap[status] || statusMap.pending
    return <span className={`badge ${statusInfo.color}`}>{statusInfo.label}</span>
  }

  const getReceiptStatusText = (status) => {
    const statusMap = {
      'RELEASE_STOP_UNCHECKED': '출고중지요청',
      'RETURNS_UNCHECKED': '반품접수',
      'VENDOR_WAREHOUSE_CONFIRM': '입고완료',
      'REQUEST_COUPANG_CHECK': '쿠팡확인요청',
      'RETURNS_COMPLETED': '반품완료'
    }
    return statusMap[status] || status
  }

  return (
    <div className="return-management">
      <div className="page-header">
        <div>
          <h1>반품 관리</h1>
          <p>쿠팡 반품을 조회하고 네이버에서 자동 처리하세요</p>
        </div>
        <div className="header-actions">
          {/* 계정 연결 상태 표시 */}
          <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            marginRight: '12px'
          }}>
            {/* 쿠팡 연결 상태 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '16px',
              background: connectionStatus.coupang.connected
                ? 'rgba(34, 197, 94, 0.1)'
                : 'rgba(239, 68, 68, 0.1)',
              border: `2px solid ${connectionStatus.coupang.connected ? '#22c55e' : '#ef4444'}`
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: connectionStatus.coupang.connected ? '#22c55e' : '#ef4444',
                animation: connectionStatus.coupang.loading
                  ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                  : 'none',
                boxShadow: connectionStatus.coupang.connected
                  ? '0 0 8px rgba(34, 197, 94, 0.6)'
                  : '0 0 8px rgba(239, 68, 68, 0.3)'
              }} />
              <span style={{
                fontSize: '12px',
                fontWeight: '600',
                color: connectionStatus.coupang.connected ? '#22c55e' : '#ef4444'
              }}>
                {connectionStatus.coupang.loading
                  ? '쿠팡'
                  : connectionStatus.coupang.connected
                    ? '쿠팡'
                    : '쿠팡 ✕'}
              </span>
            </div>

            {/* 네이버 연결 상태 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '16px',
              background: connectionStatus.naver.connected
                ? 'rgba(34, 197, 94, 0.1)'
                : 'rgba(239, 68, 68, 0.1)',
              border: `2px solid ${connectionStatus.naver.connected ? '#22c55e' : '#ef4444'}`
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: connectionStatus.naver.connected ? '#22c55e' : '#ef4444',
                animation: connectionStatus.naver.loading
                  ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                  : 'none',
                boxShadow: connectionStatus.naver.connected
                  ? '0 0 8px rgba(34, 197, 94, 0.6)'
                  : '0 0 8px rgba(239, 68, 68, 0.3)'
              }} />
              <span style={{
                fontSize: '12px',
                fontWeight: '600',
                color: connectionStatus.naver.connected ? '#22c55e' : '#ef4444'
              }}>
                {connectionStatus.naver.loading
                  ? '네이버'
                  : connectionStatus.naver.connected
                    ? '네이버'
                    : '네이버 ✕'}
              </span>
            </div>
          </div>

          <button
            className="btn-secondary"
            onClick={() => setShowCredentialsModal(true)}
          >
            <Settings size={20} />
            <span>계정 설정</span>
          </button>
          <button
            className="btn-secondary"
            onClick={fetchFromCoupang}
            disabled={loading}
          >
            <RefreshCw size={20} className={loading ? 'spinning' : ''} />
            <span>쿠팡에서 조회</span>
          </button>
          <button
            className="btn-primary"
            onClick={startAutoProcessing}
            disabled={processing || returns.filter(r => r.status === 'pending' && !r.naver_processed).length === 0}
            style={{
              fontSize: '16px',
              fontWeight: 'bold',
              padding: '12px 24px'
            }}
          >
            <Play size={24} />
            <span>🚀 자동 처리 시작 ({returns.filter(r => r.status === 'pending' && !r.naver_processed).length})</span>
          </button>
          <button
            className="btn-secondary"
            onClick={processNaverReturns}
            disabled={processing || selectedReturns.length === 0}
          >
            <Play size={20} />
            <span>선택 항목 처리 ({selectedReturns.length})</span>
          </button>
        </div>
      </div>

      {/* 계정 설정 모달 */}
      {showCredentialsModal && (
        <div className="modal-overlay" onClick={() => setShowCredentialsModal(false)}>
          <motion.div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
          >
            <div className="modal-header">
              <h2>계정 정보 설정</h2>
              <p>쿠팡과 네이버 계정 정보를 저장하면 다음부터 자동으로 사용됩니다</p>
              <div style={{
                background: '#fff3cd',
                border: '1px solid #ffc107',
                padding: '12px',
                borderRadius: '8px',
                marginTop: '12px',
                fontSize: '14px',
                color: '#856404'
              }}>
                <strong>💡 필수 입력 사항:</strong>
                <ul style={{ marginTop: '8px', marginBottom: '0', paddingLeft: '20px' }}>
                  <li><strong>쿠팡</strong>: Access Key, Secret Key, Vendor ID (3개 모두 필수)</li>
                  <li><strong>네이버</strong>: 아이디, 비밀번호 (2개 모두 필수)</li>
                  <li>쿠팡 또는 네이버 중 최소 1개는 입력해야 합니다</li>
                </ul>
              </div>
            </div>

            <div className="modal-body">
              {/* 계정 세트 선택 섹션 (항상 표시) */}
              <div className="form-section" style={{
                background: accountSets.length > 0 ? '#e8f5e9' : '#f5f5f5',
                border: accountSets.length > 0 ? '3px solid #4caf50' : '2px solid #999',
                padding: '20px',
                borderRadius: '10px',
                marginBottom: '20px'
              }}>
                <h3 style={{ color: accountSets.length > 0 ? '#2e7d32' : '#666', marginTop: 0, fontSize: '18px' }}>
                  {accountSets.length > 0 ? '🎯 저장된 계정 세트 (쿠팡 + 네이버 통합)' : '📦 저장된 계정 세트'}
                </h3>
                <p style={{ fontSize: '14px', color: '#555', marginBottom: '16px' }}>
                  {accountSets.length > 0
                    ? '계정 세트를 선택하면 쿠팡과 네이버 정보가 모두 자동으로 입력됩니다'
                    : '아직 저장된 계정 세트가 없습니다. 아래에 정보를 입력하고 저장하세요.'}
                </p>

                {accountSets.length > 0 ? (
                  <div className="form-group">
                    <label style={{ fontWeight: 'bold', color: '#2e7d32', fontSize: '15px' }}>
                      📦 계정 세트 선택
                    </label>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                      <select
                        onChange={(e) => handleSelectAccountSet(e.target.value)}
                        value={selectedAccountSetId || ''}
                        style={{
                          flex: 1,
                          padding: '12px',
                          borderRadius: '8px',
                          border: '3px solid #4caf50',
                          fontSize: '15px',
                          fontWeight: 'bold',
                          cursor: 'pointer'
                        }}
                      >
                        <option value="">-- 새로 입력하기 --</option>
                        {accountSets.map((set) => (
                          <option key={set.id} value={set.id}>
                            {set.name} {set.is_default && '⭐'}
                            {set.coupang_account && set.naver_account && ' (쿠팡+네이버)'}
                            {set.coupang_account && !set.naver_account && ' (쿠팡만)'}
                            {!set.coupang_account && set.naver_account && ' (네이버만)'}
                          </option>
                        ))}
                      </select>
                      {selectedAccountSetId && (
                        <button
                          onClick={handleDeleteAccountSet}
                          style={{
                            padding: '12px 20px',
                            borderRadius: '8px',
                            border: 'none',
                            background: '#f44336',
                            color: 'white',
                            fontSize: '15px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                            transition: 'background 0.2s'
                          }}
                          onMouseOver={(e) => e.target.style.background = '#d32f2f'}
                          onMouseOut={(e) => e.target.style.background = '#f44336'}
                        >
                          🗑️ 삭제
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '16px',
                    background: '#fff',
                    borderRadius: '8px',
                    border: '2px dashed #ccc',
                    textAlign: 'center',
                    color: '#999',
                    fontSize: '14px'
                  }}>
                    💡 저장된 계정 세트가 없습니다. 아래에서 계정을 입력하고 저장하세요.
                  </div>
                )}
              </div>

              {/* 세트 이름 입력 */}
              <div className="form-section" style={{
                background: '#fff8e1',
                border: '2px solid #ffc107',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <h3 style={{ color: '#f57c00', marginTop: 0 }}>💾 계정 세트 이름</h3>
                <div className="form-group">
                  <label style={{ fontWeight: 'bold' }}>세트 이름</label>
                  <input
                    type="text"
                    value={accountSetName}
                    onChange={(e) => setAccountSetName(e.target.value)}
                    placeholder="예: 기본 계정, 회사 계정, 개인 계정"
                    style={{
                      padding: '10px',
                      borderRadius: '6px',
                      border: '2px solid #ffc107',
                      fontSize: '14px',
                      width: '100%'
                    }}
                  />
                  <small style={{ color: '#666', marginTop: '4px', display: 'block' }}>
                    쿠팡 + 네이버 계정을 하나의 세트로 저장합니다
                  </small>
                </div>
              </div>

              {/* 저장된 개별 계정 불러오기 섹션 (하위 옵션) */}
              {(allCoupangAccounts.length > 0 || allNaverAccounts.length > 0) && (
                <div className="form-section" style={{
                  background: '#e7f3ff',
                  border: '2px solid #2196F3',
                  padding: '16px',
                  borderRadius: '8px',
                  marginBottom: '20px'
                }}>
                  <h3 style={{ color: '#1976d2', marginTop: 0 }}>📋 저장된 계정 불러오기</h3>
                  <p style={{ fontSize: '14px', color: '#555', marginBottom: '16px' }}>
                    이전에 저장한 계정을 선택하면 자동으로 입력됩니다
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    {/* 쿠팡 계정 선택 */}
                    {allCoupangAccounts.length > 0 && (
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontWeight: 'bold', color: '#1976d2' }}>
                          🔑 쿠팡 계정 선택
                        </label>
                        <select
                          onChange={(e) => handleSelectCoupangAccount(e.target.value)}
                          defaultValue=""
                          style={{
                            padding: '10px',
                            borderRadius: '6px',
                            border: '2px solid #2196F3',
                            fontSize: '14px',
                            cursor: 'pointer'
                          }}
                        >
                          <option value="">-- 계정 선택 --</option>
                          {allCoupangAccounts.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                              {acc.name} (Vendor: {acc.vendor_id})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* 네이버 계정 선택 */}
                    {allNaverAccounts.length > 0 && (
                      <div className="form-group" style={{ marginBottom: 0 }}>
                        <label style={{ fontWeight: 'bold', color: '#1976d2' }}>
                          🟢 네이버 계정 선택
                        </label>
                        <select
                          onChange={(e) => handleSelectNaverAccount(e.target.value)}
                          defaultValue=""
                          style={{
                            padding: '10px',
                            borderRadius: '6px',
                            border: '2px solid #2196F3',
                            fontSize: '14px',
                            cursor: 'pointer'
                          }}
                        >
                          <option value="">-- 계정 선택 --</option>
                          {allNaverAccounts.map((acc) => (
                            <option key={acc.id} value={acc.id}>
                              {acc.name} ({acc.naver_username}){acc.is_default && ' ⭐'}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="form-section">
                <h3>🔑 쿠팡 API 설정</h3>
                <div className="form-group">
                  <label>Access Key</label>
                  <input
                    type="text"
                    value={credentials.coupangAccessKey}
                    onChange={(e) => setCredentials({ ...credentials, coupangAccessKey: e.target.value })}
                    placeholder="예: A00492891"
                  />
                </div>
                <div className="form-group">
                  <label>Secret Key</label>
                  <input
                    type="password"
                    value={credentials.coupangSecretKey}
                    onChange={(e) => setCredentials({ ...credentials, coupangSecretKey: e.target.value })}
                    placeholder="Secret Key 입력"
                  />
                </div>
                <div className="form-group">
                  <label>Vendor ID</label>
                  <input
                    type="text"
                    value={credentials.coupangVendorId}
                    onChange={(e) => setCredentials({ ...credentials, coupangVendorId: e.target.value })}
                    placeholder="예: A00492891"
                  />
                </div>
              </div>

              <div className="form-section">
                <h3>👤 쿠팡 Wing 로그인 (선택사항)</h3>
                <div className="form-group">
                  <label>아이디</label>
                  <input
                    type="text"
                    value={credentials.coupangUsername}
                    onChange={(e) => setCredentials({ ...credentials, coupangUsername: e.target.value })}
                    placeholder="쿠팡 Wing 아이디 (웹 자동화용)"
                  />
                </div>
                <div className="form-group">
                  <label>비밀번호</label>
                  <input
                    type="password"
                    value={credentials.coupangPassword}
                    onChange={(e) => setCredentials({ ...credentials, coupangPassword: e.target.value })}
                    placeholder="쿠팡 Wing 비밀번호 (웹 자동화용)"
                  />
                </div>
              </div>

              <div className="form-section">
                <h3>네이버 계정</h3>
                <div className="form-group">
                  <label>아이디</label>
                  <input
                    type="text"
                    value={credentials.naverUsername}
                    onChange={(e) => setCredentials({ ...credentials, naverUsername: e.target.value })}
                    placeholder="네이버 아이디"
                  />
                </div>
                <div className="form-group">
                  <label>비밀번호</label>
                  <input
                    type="password"
                    value={credentials.naverPassword}
                    onChange={(e) => setCredentials({ ...credentials, naverPassword: e.target.value })}
                    placeholder="네이버 비밀번호"
                  />
                </div>
              </div>

              <div className="form-note">
                <Save size={16} />
                <p>
                  입력하신 계정 정보는 암호화되어 안전하게 저장됩니다.
                  저장된 계정은 '네이버 계정' 메뉴에서 관리할 수 있습니다.
                </p>
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setShowCredentialsModal(false)}
              >
                취소
              </button>
              <button
                className="btn-primary"
                onClick={handleSaveAsAccountSet}
                disabled={
                  !accountSetName ||
                  // 쿠팡과 네이버 둘 다 입력되지 않았으면 비활성화
                  (!credentials.coupangAccessKey && !credentials.naverUsername) ||
                  // 쿠팡 필드 중 하나라도 입력했으면 Access Key, Secret Key, Vendor ID 모두 필수
                  ((credentials.coupangAccessKey || credentials.coupangSecretKey || credentials.coupangVendorId) &&
                   (!credentials.coupangAccessKey || !credentials.coupangSecretKey || !credentials.coupangVendorId)) ||
                  // 네이버는 아이디/비밀번호 둘 다 필수
                  (credentials.naverUsername && !credentials.naverPassword) ||
                  (credentials.naverPassword && !credentials.naverUsername)
                }
                style={{
                  fontSize: '16px',
                  fontWeight: 'bold',
                  padding: '12px 24px',
                  background: '#4caf50',
                  borderColor: '#4caf50'
                }}
              >
                <Save size={20} />
                💾 계정 세트로 저장
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* 실시간 처리 확인 모달 */}
      {showProcessingModal && currentProcessingItem && (
        <div className="modal-overlay" style={{ zIndex: 1000 }}>
          <motion.div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            style={{ maxWidth: '700px' }}
          >
            <div className="modal-header">
              <h2>🔍 반품 처리 확인</h2>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '12px',
                padding: '12px',
                background: '#f0f9ff',
                borderRadius: '8px',
                border: '2px solid #0ea5e9'
              }}>
                <div>
                  <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#0369a1' }}>
                    진행 상황: {processingItemIndex + 1} / {processingQueue.length}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '14px' }}>
                  <span style={{ color: '#22c55e', fontWeight: 'bold' }}>
                    ✅ 처리: {processedCount}건
                  </span>
                  <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>
                    ⏭️ 건너뜀: {skippedCount}건
                  </span>
                </div>
              </div>
            </div>

            <div className="modal-body">
              <div style={{
                background: '#fef3c7',
                border: '3px solid #f59e0b',
                padding: '16px',
                borderRadius: '12px',
                marginBottom: '20px'
              }}>
                <h3 style={{ margin: '0 0 12px 0', color: '#d97706', fontSize: '18px' }}>
                  ⚠️ 아래 정보를 확인하고 일치하면 "확인" 버튼을 눌러주세요
                </h3>
                <p style={{ margin: 0, fontSize: '14px', color: '#92400e' }}>
                  잘못된 처리는 큰 문제가 될 수 있습니다. 신중하게 확인해주세요!
                </p>
              </div>

              {/* 쿠팡 정보 */}
              <div style={{
                background: '#fff',
                border: '2px solid #e5e7eb',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '16px'
              }}>
                <h4 style={{
                  margin: '0 0 16px 0',
                  fontSize: '16px',
                  color: '#6b7280',
                  borderBottom: '2px solid #e5e7eb',
                  paddingBottom: '8px'
                }}>
                  🛒 쿠팡 반품 정보
                </h4>

                <div style={{ display: 'grid', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                      주문번호
                    </label>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      padding: '8px 12px',
                      background: '#f9fafb',
                      borderRadius: '6px',
                      fontFamily: 'monospace'
                    }}>
                      {currentProcessingItem.coupang_order_id}
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                      상품명
                    </label>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      padding: '12px',
                      background: '#dbeafe',
                      borderRadius: '6px',
                      border: '2px solid #3b82f6'
                    }}>
                      {currentProcessingItem.product_name}
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                      수령인
                    </label>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      padding: '12px',
                      background: '#dcfce7',
                      borderRadius: '6px',
                      border: '2px solid #22c55e'
                    }}>
                      {currentProcessingItem.receiver_name || '정보 없음'}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                        전화번호
                      </label>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: 'bold',
                        color: '#1f2937',
                        padding: '8px 12px',
                        background: '#f9fafb',
                        borderRadius: '6px',
                        fontFamily: 'monospace'
                      }}>
                        {currentProcessingItem.receiver_phone || '-'}
                      </div>
                    </div>

                    <div>
                      <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                        수량
                      </label>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: 'bold',
                        color: '#1f2937',
                        padding: '8px 12px',
                        background: '#f9fafb',
                        borderRadius: '6px'
                      }}>
                        {currentProcessingItem.cancel_count}개
                      </div>
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                      반품 사유
                    </label>
                    <div style={{
                      fontSize: '14px',
                      color: '#4b5563',
                      padding: '8px 12px',
                      background: '#f9fafb',
                      borderRadius: '6px'
                    }}>
                      {currentProcessingItem.cancel_reason_category1}
                      {currentProcessingItem.cancel_reason_category2 && ` - ${currentProcessingItem.cancel_reason_category2}`}
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '13px', color: '#6b7280', display: 'block', marginBottom: '4px' }}>
                      쿠팡 상태
                    </label>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: 'bold',
                      color: '#ea580c',
                      padding: '8px 12px',
                      background: '#ffedd5',
                      borderRadius: '6px',
                      border: '1px solid #fb923c'
                    }}>
                      {getReceiptStatusText(currentProcessingItem.receipt_status)}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{
                background: '#fee2e2',
                border: '2px solid #ef4444',
                borderRadius: '8px',
                padding: '12px',
                fontSize: '14px',
                color: '#991b1b',
                marginTop: '16px'
              }}>
                <strong>⚠️ 주의:</strong> 위 정보가 네이버 주문 정보와 일치하는지 꼭 확인하세요!
              </div>
            </div>

            <div className="modal-footer" style={{ display: 'flex', gap: '12px' }}>
              <button
                className="btn-secondary"
                onClick={cancelProcessing}
                disabled={processing}
                style={{ flex: 1 }}
              >
                🛑 중단
              </button>
              <button
                className="btn-secondary"
                onClick={skipCurrentItem}
                disabled={processing}
                style={{
                  flex: 2,
                  background: '#f59e0b',
                  borderColor: '#f59e0b',
                  color: 'white'
                }}
              >
                ⏭️ 건너뛰기
              </button>
              <button
                className="btn-primary"
                onClick={confirmCurrentItem}
                disabled={processing}
                style={{
                  flex: 2,
                  fontSize: '18px',
                  fontWeight: 'bold',
                  background: '#22c55e',
                  borderColor: '#22c55e'
                }}
              >
                {processing ? '처리 중...' : '✅ 확인 및 처리'}
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* 통계 카드 */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.1)' }}>
              <PackageX size={24} style={{ color: '#6366f1' }} />
            </div>
            <div className="stat-content">
              <div className="stat-label">전체 반품</div>
              <div className="stat-value">{stats.total}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(251, 191, 36, 0.1)' }}>
              <Clock size={24} style={{ color: '#fbbf24' }} />
            </div>
            <div className="stat-content">
              <div className="stat-label">대기중</div>
              <div className="stat-value">{stats.status.pending}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(34, 197, 94, 0.1)' }}>
              <CheckCircle size={24} style={{ color: '#22c55e' }} />
            </div>
            <div className="stat-content">
              <div className="stat-label">처리완료</div>
              <div className="stat-value">{stats.status.completed}</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.1)' }}>
              <XCircle size={24} style={{ color: '#ef4444' }} />
            </div>
            <div className="stat-content">
              <div className="stat-label">실패</div>
              <div className="stat-value">{stats.status.failed}</div>
            </div>
          </div>
        </div>
      )}

      {/* 필터 */}
      <div className="filters">
        <div className="filter-group">
          <Filter size={20} />
          <span>상태:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">전체</option>
            <option value="pending">대기</option>
            <option value="processing">처리중</option>
            <option value="completed">완료</option>
            <option value="failed">실패</option>
          </select>
        </div>

        <div className="filter-group">
          <span>네이버 처리:</span>
          <select
            value={naverProcessed === null ? 'all' : naverProcessed.toString()}
            onChange={(e) => {
              const value = e.target.value
              setNaverProcessed(value === 'all' ? null : value === 'true')
            }}
          >
            <option value="all">전체</option>
            <option value="false">미처리</option>
            <option value="true">처리완료</option>
          </select>
        </div>
      </div>

      {/* 반품 목록 */}
      <div className="returns-table-container">
        <table className="returns-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  checked={selectedReturns.length === returns.filter(r => !r.naver_processed).length && returns.filter(r => !r.naver_processed).length > 0}
                  onChange={handleSelectAll}
                />
              </th>
              <th>쿠팡 주문번호</th>
              <th>상품명</th>
              <th>수령인</th>
              <th>전화번호</th>
              <th>쿠팡 상태</th>
              <th>수량</th>
              <th>반품 사유</th>
              <th>네이버 처리</th>
              <th>상태</th>
              <th>생성일시</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="11" style={{ textAlign: 'center', padding: '40px' }}>
                  <div className="spinner" style={{ margin: '0 auto' }}></div>
                  <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>
                    로딩 중...
                  </p>
                </td>
              </tr>
            ) : returns.length === 0 ? (
              <tr>
                <td colSpan="11" style={{ textAlign: 'center', padding: '40px' }}>
                  <PackageX size={48} style={{ color: 'var(--text-tertiary)', marginBottom: '16px' }} />
                  <p style={{ color: 'var(--text-secondary)' }}>
                    반품 내역이 없습니다
                  </p>
                </td>
              </tr>
            ) : (
              returns.map((returnItem) => (
                <motion.tr
                  key={returnItem.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedReturns.includes(returnItem.id)}
                      onChange={() => handleSelectReturn(returnItem.id)}
                      disabled={returnItem.naver_processed}
                    />
                  </td>
                  <td>
                    <span className="order-id">{returnItem.coupang_order_id}</span>
                  </td>
                  <td>
                    <div className="product-name" title={returnItem.product_name}>
                      {returnItem.product_name}
                    </div>
                  </td>
                  <td>
                    <strong style={{ color: 'var(--primary-color)' }}>
                      {returnItem.receiver_name || '-'}
                    </strong>
                  </td>
                  <td>
                    <span style={{ fontFamily: 'monospace' }}>
                      {returnItem.receiver_phone || '-'}
                    </span>
                  </td>
                  <td>
                    <span className="receipt-status">
                      {getReceiptStatusText(returnItem.receipt_status)}
                    </span>
                  </td>
                  <td>{returnItem.cancel_count}</td>
                  <td>
                    <div className="return-reason">
                      <div>{returnItem.cancel_reason_category1}</div>
                      {returnItem.cancel_reason_category2 && (
                        <small>{returnItem.cancel_reason_category2}</small>
                      )}
                    </div>
                  </td>
                  <td>
                    {returnItem.naver_processed ? (
                      <div className="naver-processed">
                        <CheckCircle size={16} style={{ color: '#22c55e' }} />
                        <span>완료</span>
                        {returnItem.naver_process_type && (
                          <small>{returnItem.naver_process_type === 'RETURN_REQUEST' ? '반품신청' : '주문취소'}</small>
                        )}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-tertiary)' }}>미처리</span>
                    )}
                  </td>
                  <td>{getStatusBadge(returnItem.status)}</td>
                  <td>
                    <div className="datetime">
                      {new Date(returnItem.created_at).toLocaleDateString('ko-KR')}
                      <small>{new Date(returnItem.created_at).toLocaleTimeString('ko-KR')}</small>
                    </div>
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ReturnManagement
