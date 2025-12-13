/**
 * API 설정 및 자동 서버 연결
 * 클라우드 백엔드 URL 하드코딩 (환경변수 문제 방지)
 */

// 클라우드 백엔드 URL (하드코딩)
const CLOUD_BACKEND_URL = 'https://coupang-wing-cs-backend.fly.dev'
const API_URL_FROM_ENV = CLOUD_BACKEND_URL

const POSSIBLE_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009]
const TIMEOUT = 20000 // 20초 (클라우드 백엔드의 느린 응답을 위해)

/**
 * 클라우드 백엔드 사용 여부 확인
 */
export function isUsingCloudBackend() {
  return API_URL_FROM_ENV && API_URL_FROM_ENV.startsWith('https://')
}

/**
 * 특정 포트에서 서버가 실행 중인지 확인
 */
async function checkServer(port) {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT)

    const response = await fetch(`http://localhost:${port}/health`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      }
    })

    clearTimeout(timeoutId)

    // 응답이 있고 200-299 범위면 성공
    if (response.ok) {
      const data = await response.json()
      // 서버가 응답했고 status가 있으면 연결 성공
      return data && (data.status === 'healthy' || data.status === 'degraded')
    }
    return false
  } catch (error) {
    // 네트워크 오류나 타임아웃
    return false
  }
}

/**
 * 사용 가능한 백엔드 서버 포트 찾기
 * 클라우드 환경에서는 환경변수 URL 사용
 */
export async function findBackendServer(onProgress) {
  // 클라우드 백엔드를 사용하는 경우
  if (isUsingCloudBackend()) {
    if (onProgress) {
      onProgress({
        current: 1,
        total: 1,
        port: null,
        message: `클라우드 백엔드에 연결 중...`,
        cloudUrl: API_URL_FROM_ENV
      })
    }

    // 클라우드 백엔드 헬스체크
    try {
      const response = await fetch(`${API_URL_FROM_ENV}/health`)
      if (response.ok) {
        if (onProgress) {
          onProgress({
            current: 1,
            total: 1,
            port: 'cloud',
            message: `클라우드 백엔드 연결 성공!`,
            success: true,
            cloudUrl: API_URL_FROM_ENV
          })
        }
        return 'cloud' // 특수 값으로 클라우드 사용 표시
      }
    } catch (error) {
      console.error('클라우드 백엔드 연결 실패:', error)
    }
  }

  // 로컬 개발 환경 - 포트 스캔
  for (let i = 0; i < POSSIBLE_PORTS.length; i++) {
    const port = POSSIBLE_PORTS[i]

    if (onProgress) {
      onProgress({
        current: i + 1,
        total: POSSIBLE_PORTS.length,
        port,
        message: `포트 ${port} 확인 중...`
      })
    }

    const isAvailable = await checkServer(port)

    if (isAvailable) {
      if (onProgress) {
        onProgress({
          current: i + 1,
          total: POSSIBLE_PORTS.length,
          port,
          message: `포트 ${port}에 연결 성공!`,
          success: true
        })
      }
      return port
    }
  }

  return null
}

/**
 * API 기본 URL 가져오기
 * 환경변수에 클라우드 URL이 있으면 그것을 사용, 없으면 로컬 포트 사용
 */
export function getApiBaseUrl(port) {
  // 클라우드 백엔드 URL이 환경변수에 설정되어 있으면 사용
  if (API_URL_FROM_ENV) {
    return `${API_URL_FROM_ENV}/api`
  }

  // 로컬 개발 환경
  if (!port) return null
  return `http://localhost:${port}/api`
}

/**
 * 저장된 포트 가져오기
 */
export function getSavedPort() {
  const saved = localStorage.getItem('backend_port')
  return saved ? parseInt(saved) : null
}

/**
 * 포트 저장하기
 */
export function savePort(port) {
  localStorage.setItem('backend_port', port.toString())
}

/**
 * 저장된 포트 제거
 */
export function clearSavedPort() {
  localStorage.removeItem('backend_port')
}

/**
 * 모든 포트 관련 캐시 초기화
 */
export function clearAllPortCache() {
  localStorage.removeItem('backend_port')
  localStorage.removeItem('used_ports')
  localStorage.removeItem('last_sync_time')
}

/**
 * 사용된 포트 기록
 */
function markPortAsUsed(port) {
  const used = JSON.parse(localStorage.getItem('used_ports') || '[]')
  if (!used.includes(port)) {
    used.push(port)
    localStorage.setItem('used_ports', JSON.stringify(used))
  }
}

/**
 * 사용된 포트 목록 가져오기
 */
function getUsedPorts() {
  return JSON.parse(localStorage.getItem('used_ports') || '[]')
}

/**
 * 자동 동기화: 연결될 때까지 계속 시도
 */
export async function autoSyncServers(onProgress, maxAttempts = 50) {
  let attempts = 0

  while (attempts < maxAttempts) {
    attempts++

    if (onProgress) {
      onProgress({
        attempt: attempts,
        maxAttempts,
        message: `동기화 시도 중... (${attempts}/${maxAttempts})`,
        isAutoSync: true
      })
    }

    // 사용 가능한 포트 찾기
    const port = await findBackendServer(onProgress)

    if (port) {
      savePort(port)
      markPortAsUsed(port)
      localStorage.setItem('last_sync_time', Date.now().toString())

      if (onProgress) {
        onProgress({
          attempt: attempts,
          maxAttempts,
          port,
          message: `백엔드 연결 성공! (포트: ${port})`,
          success: true,
          isAutoSync: true
        })
      }

      return port
    }

    // 실패 시 1초 대기 후 재시도
    await new Promise(resolve => setTimeout(resolve, 1000))
  }

  return null
}

/**
 * 포트 충돌 체크 및 새로운 포트 할당
 */
export async function checkAndReassignPort(currentPort) {
  // 현재 포트가 여전히 사용 가능한지 확인
  const isStillAvailable = await checkServer(currentPort)

  if (isStillAvailable) {
    return currentPort // 문제 없음
  }

  // 충돌 발생 - 새 포트 찾기
  const usedPorts = getUsedPorts()
  const availablePorts = POSSIBLE_PORTS.filter(p => !usedPorts.includes(p))

  for (const port of availablePorts) {
    const isAvailable = await checkServer(port)
    if (isAvailable) {
      savePort(port)
      markPortAsUsed(port)
      return port
    }
  }

  // 모든 포트가 사용 중이면 캐시 초기화 후 재시도
  clearAllPortCache()
  return await findBackendServer()
}
