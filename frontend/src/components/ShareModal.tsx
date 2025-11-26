import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getYouTubeStatus, getYouTubeAuthUrl, uploadToYouTube, disconnectYouTube } from '../api/client'
import './ShareModal.css'

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  videoUrl: string
  runId: string
  defaultTitle?: string
}

const DEFAULT_DESCRIPTION = `텍스트 한줄을 바로 숏폼으로!
Kurz AI Studio에서 생성한 숏폼입니다.`

export default function ShareModal({ isOpen, onClose, videoUrl: _videoUrl, runId, defaultTitle = '' }: ShareModalProps) {
  const { user } = useAuth()
  const [title, setTitle] = useState(defaultTitle)
  const [description, setDescription] = useState(DEFAULT_DESCRIPTION)
  const [scheduledTime, setScheduledTime] = useState('')
  const [isScheduled, setIsScheduled] = useState(false)
  const [youtubeConnected, setYoutubeConnected] = useState(false)
  const [youtubeChannelName, setYoutubeChannelName] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState<{ videoUrl: string } | null>(null)

  // Suppress unused variable warning
  void _videoUrl

  // Update title when defaultTitle changes
  useEffect(() => {
    if (defaultTitle) {
      setTitle(defaultTitle)
    }
  }, [defaultTitle])

  // Check YouTube connection status on mount
  useEffect(() => {
    if (isOpen && user) {
      checkYouTubeStatus()
    }
  }, [isOpen, user])

  // Handle YouTube OAuth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('youtube_connected') === 'true') {
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
      // Refresh status
      checkYouTubeStatus()
    }
  }, [])

  const checkYouTubeStatus = async () => {
    setCheckingStatus(true)
    try {
      const status = await getYouTubeStatus()
      setYoutubeConnected(status.connected)
      setYoutubeChannelName(status.channel_name)
    } catch (err) {
      console.error('Failed to check YouTube status:', err)
    } finally {
      setCheckingStatus(false)
    }
  }

  const handleConnectYouTube = () => {
    window.location.href = getYouTubeAuthUrl()
  }

  const handleDisconnectYouTube = async () => {
    try {
      await disconnectYouTube()
      setYoutubeConnected(false)
      setYoutubeChannelName(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'YouTube 연결 해제 실패')
    }
  }

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('제목을 입력해주세요')
      return
    }

    if (!youtubeConnected) {
      setError('먼저 YouTube 계정을 연결해주세요')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await uploadToYouTube({
        run_id: runId,
        title: title.trim(),
        description: description.trim() || `Created with Kurz AI Studio\n\n업로드 시각: ${new Date().toLocaleString('ko-KR')}`,
        scheduled_time: isScheduled && scheduledTime ? scheduledTime : undefined,
      })

      if (response.success && response.video_url) {
        setSuccess({ videoUrl: response.video_url })
      } else {
        setError(response.message || '업로드 실패')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '업로드 실패')
    } finally {
      setLoading(false)
    }
  }

  // Calculate min datetime (now)
  const now = new Date()
  const minTime = now.toISOString().slice(0, 16)

  if (!isOpen) return null

  // Success state
  if (success) {
    return (
      <div className="share-modal-overlay" onClick={onClose}>
        <div className="share-modal" onClick={(e) => e.stopPropagation()}>
          <div className="share-modal-header">
            <div className="share-modal-title">
              <span>업로드 완료!</span>
            </div>
            <button className="share-modal-close" onClick={onClose}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          <div className="share-modal-content success-content">
            <div className="success-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="64" height="64">
                <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clipRule="evenodd" />
              </svg>
            </div>
            <p className="success-message">YouTube에 영상이 업로드되었습니다!</p>
            <a
              href={success.videoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="youtube-link-btn"
            >
              <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 576 512" height="20" width="20">
                <path d="M549.655 124.083c-6.281-23.65-24.787-42.276-48.284-48.597C458.781 64 288 64 288 64S117.22 64 74.629 75.486c-23.497 6.322-42.003 24.947-48.284 48.597-11.412 42.867-11.412 132.305-11.412 132.305s0 89.438 11.412 132.305c6.281 23.65 24.787 41.5 48.284 47.821C117.22 448 288 448 288 448s170.78 0 213.371-11.486c23.497-6.321 42.003-24.171 48.284-47.821 11.412-42.867 11.412-132.305 11.412-132.305s0-89.438-11.412-132.305zm-317.51 213.508V175.185l142.739 81.205-142.739 81.201z"></path>
              </svg>
              YouTube에서 보기
            </a>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="share-modal-overlay" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="share-modal-header">
          <div className="share-modal-title">
            <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 576 512" className="youtube-icon-header" height="24" width="24">
              <path d="M549.655 124.083c-6.281-23.65-24.787-42.276-48.284-48.597C458.781 64 288 64 288 64S117.22 64 74.629 75.486c-23.497 6.322-42.003 24.947-48.284 48.597-11.412 42.867-11.412 132.305-11.412 132.305s0 89.438 11.412 132.305c6.281 23.65 24.787 41.5 48.284 47.821C117.22 448 288 448 288 448s170.78 0 213.371-11.486c23.497-6.321 42.003-24.171 48.284-47.821 11.412-42.867 11.412-132.305 11.412-132.305s0-89.438-11.412-132.305zm-317.51 213.508V175.185l142.739 81.205-142.739 81.201z"></path>
            </svg>
            <span>YouTube 업로드</span>
          </div>
          <button className="share-modal-close" onClick={onClose}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="share-modal-content">
          {/* YouTube Connection Status */}
          <div className="youtube-connection-section">
            {checkingStatus ? (
              <div className="connection-checking">연결 상태 확인 중...</div>
            ) : youtubeConnected ? (
              <div className="connection-status connected">
                <div className="connection-info">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20" className="check-icon">
                    <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clipRule="evenodd" />
                  </svg>
                  <span>연결됨: <strong>{youtubeChannelName || 'YouTube 채널'}</strong></span>
                </div>
                <button className="disconnect-btn" onClick={handleDisconnectYouTube}>
                  연결 해제
                </button>
              </div>
            ) : (
              <div className="connection-status disconnected">
                <p>YouTube 계정을 연결하여 영상을 업로드하세요</p>
                <button className="connect-youtube-btn" onClick={handleConnectYouTube}>
                  <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 576 512" height="20" width="20">
                    <path d="M549.655 124.083c-6.281-23.65-24.787-42.276-48.284-48.597C458.781 64 288 64 288 64S117.22 64 74.629 75.486c-23.497 6.322-42.003 24.947-48.284 48.597-11.412 42.867-11.412 132.305-11.412 132.305s0 89.438 11.412 132.305c6.281 23.65 24.787 41.5 48.284 47.821C117.22 448 288 448 288 448s170.78 0 213.371-11.486c23.497-6.321 42.003-24.171 48.284-47.821 11.412-42.867 11.412-132.305 11.412-132.305s0-89.438-11.412-132.305zm-317.51 213.508V175.185l142.739 81.205-142.739 81.201z"></path>
                  </svg>
                  YouTube 계정 연결
                </button>
              </div>
            )}
          </div>

          {/* Upload Form - only show when connected */}
          {youtubeConnected && (
            <>
              {/* Title Input */}
              <div className="share-form-group">
                <label>제목 *</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="영상의 매력적인 제목을 입력하세요"
                  disabled={loading}
                  maxLength={100}
                />
                <span className="char-count">{title.length}/100</span>
              </div>

              {/* Description Input */}
              <div className="share-form-group">
                <label>설명</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="영상에 대한 설명을 입력하세요 (선택사항)"
                  disabled={loading}
                  rows={4}
                  maxLength={5000}
                />
                <span className="char-count">{description.length}/5000</span>
              </div>

              {/* Schedule Toggle */}
              <div className="share-form-group schedule-toggle">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={isScheduled}
                    onChange={(e) => setIsScheduled(e.target.checked)}
                    disabled={loading}
                  />
                  <span className="toggle-text">예약 업로드</span>
                </label>
              </div>

              {/* Schedule Time - only show when scheduled */}
              {isScheduled && (
                <div className="share-form-group">
                  <label>게시 시간</label>
                  <input
                    type="datetime-local"
                    value={scheduledTime}
                    onChange={(e) => setScheduledTime(e.target.value)}
                    min={minTime}
                    disabled={loading}
                  />
                </div>
              )}
            </>
          )}

          {/* Legal disclaimer */}
          <div className="legal-disclaimer">
            <p>* YouTube 기능을 사용하면 <a href="https://www.youtube.com/t/terms" target="_blank" rel="noreferrer">YouTube 서비스 약관</a>에 동의하고, YouTube API 사용 및 <a href="https://www.google.com/policies/privacy" target="_blank" rel="noreferrer">Google 개인정보처리방침</a>을 인정하는 것입니다. 액세스를 취소하려면 <a href="https://security.google.com/settings/security/permissions" target="_blank" rel="noreferrer">Google 계정 권한</a>을 방문하세요.</p>
          </div>

          {/* Error message */}
          {error && <div className="share-error">{error}</div>}

          {/* Submit Button */}
          <div className="share-submit-section">
            {user ? (
              <button
                className="share-submit-btn"
                onClick={handleSubmit}
                disabled={loading || !youtubeConnected || !title.trim()}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    업로드 중...
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                      <path fillRule="evenodd" d="M11.47 2.47a.75.75 0 011.06 0l4.5 4.5a.75.75 0 01-1.06 1.06l-3.22-3.22V16.5a.75.75 0 01-1.5 0V4.81L8.03 8.03a.75.75 0 01-1.06-1.06l4.5-4.5zM3 15.75a.75.75 0 01.75.75v2.25a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5V16.5a.75.75 0 011.5 0v2.25a3 3 0 01-3 3H5.25a3 3 0 01-3-3V16.5a.75.75 0 01.75-.75z" clipRule="evenodd" />
                    </svg>
                    {isScheduled ? '예약 업로드' : '지금 업로드'}
                  </>
                )}
              </button>
            ) : (
              <button className="share-submit-btn login-required" onClick={onClose}>
                계속하려면 로그인
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
