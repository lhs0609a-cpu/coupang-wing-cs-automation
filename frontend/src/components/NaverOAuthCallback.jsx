import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { CheckCircle, XCircle, Loader } from 'lucide-react'
import '../styles/NaverOAuthCallback.css'

const NaverOAuthCallback = ({ apiBaseUrl, showNotification }) => {
  const [status, setStatus] = useState('processing') // processing, success, error
  const [message, setMessage] = useState('네이버 로그인을 처리하는 중...')

  useEffect(() => {
    handleOAuthCallback()
  }, [])

  const handleOAuthCallback = async () => {
    try {
      // URL에서 code와 state 파라미터 추출
      const urlParams = new URLSearchParams(window.location.search)
      const code = urlParams.get('code')
      const state = urlParams.get('state')
      const error = urlParams.get('error')
      const errorDescription = urlParams.get('error_description')

      // 에러가 있는 경우
      if (error) {
        setStatus('error')
        setMessage(errorDescription || '네이버 로그인에 실패했습니다')
        showNotification?.(errorDescription || '네이버 로그인에 실패했습니다', 'error')

        // 3초 후 메인 페이지로 리디렉션
        setTimeout(() => {
          window.close() // 팝업이면 닫기
          window.location.href = '/' // 또는 메인 페이지로 이동
        }, 3000)
        return
      }

      // code가 없는 경우
      if (!code) {
        setStatus('error')
        setMessage('인증 코드가 없습니다')
        showNotification?.('인증 코드가 없습니다', 'error')

        setTimeout(() => {
          window.close()
          window.location.href = '/'
        }, 3000)
        return
      }

      // 백엔드에 code와 state 전송하여 access token 받기
      const response = await axios.post(`${apiBaseUrl}/naver/oauth/callback`, {
        code: code,
        state: state || 'RANDOM_STATE'
      })

      if (response.data.success) {
        setStatus('success')
        setMessage('네이버 로그인이 완료되었습니다!')
        showNotification?.('네이버 로그인이 완료되었습니다', 'success')

        // 로그인 성공 시 사용자 정보 표시 (선택사항)
        if (response.data.user_info) {
          console.log('User Info:', response.data.user_info)
        }

        // 2초 후 창 닫기 또는 리디렉션
        setTimeout(() => {
          window.close() // 팝업이면 닫기
          if (!window.closed) {
            // 팝업이 닫히지 않으면 메인 페이지로 이동
            window.location.href = '/'
          }
        }, 2000)
      } else {
        setStatus('error')
        setMessage(response.data.message || '로그인 처리에 실패했습니다')
        showNotification?.(response.data.message || '로그인 처리에 실패했습니다', 'error')

        setTimeout(() => {
          window.close()
          window.location.href = '/'
        }, 3000)
      }
    } catch (error) {
      console.error('OAuth Callback Error:', error)
      setStatus('error')
      setMessage('네이버 로그인 처리 중 오류가 발생했습니다')
      showNotification?.('네이버 로그인 처리 중 오류가 발생했습니다', 'error')

      setTimeout(() => {
        window.close()
        window.location.href = '/'
      }, 3000)
    }
  }

  return (
    <div className="oauth-callback-container">
      <div className="oauth-callback-card">
        {status === 'processing' && (
          <>
            <div className="oauth-icon processing">
              <Loader size={64} className="spinning" />
            </div>
            <h2>처리 중...</h2>
            <p>{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="oauth-icon success">
              <CheckCircle size={64} />
            </div>
            <h2>로그인 성공</h2>
            <p>{message}</p>
            <p className="redirect-message">잠시 후 자동으로 창이 닫힙니다...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="oauth-icon error">
              <XCircle size={64} />
            </div>
            <h2>로그인 실패</h2>
            <p>{message}</p>
            <p className="redirect-message">잠시 후 자동으로 이동합니다...</p>
          </>
        )}
      </div>
    </div>
  )
}

export default NaverOAuthCallback
