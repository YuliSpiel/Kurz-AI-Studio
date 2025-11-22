import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './ShareModal.css'

const API_BASE = '/api'

interface ShareModalProps {
  isOpen: boolean
  onClose: () => void
  videoUrl: string
  runId: string
  defaultTitle?: string
}

type Platform = 'youtube' | 'instagram' | 'tiktok' | 'linkedin'

interface PlatformConnection {
  youtube: boolean
  instagram: boolean
  tiktok: boolean
  linkedin: boolean
}

export default function ShareModal({ isOpen, onClose, videoUrl: _videoUrl, runId, defaultTitle = '' }: ShareModalProps) {
  const { user, token } = useAuth()
  const [title, setTitle] = useState(defaultTitle)
  const [scheduledTime, setScheduledTime] = useState(() => {
    const now = new Date()
    now.setMinutes(now.getMinutes() + 10)
    return now.toISOString().slice(0, 16)
  })
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [connections, _setConnections] = useState<PlatformConnection>({
    youtube: false,
    instagram: false,
    tiktok: false,
    linkedin: false
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Suppress unused variable warning - will be used when YouTube upload is fully implemented
  void _videoUrl

  if (!isOpen) return null

  const handleConnectYouTube = () => {
    // YouTube OAuth - use same Google OAuth but with YouTube scope
    window.location.href = `${API_BASE}/youtube/auth`
  }

  const handlePlatformToggle = (platform: Platform) => {
    if (!connections[platform]) {
      // Not connected, trigger connection
      if (platform === 'youtube') {
        handleConnectYouTube()
      } else {
        alert(`${platform} 연결 기능은 곧 추가됩니다`)
      }
      return
    }

    // Toggle selection
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    )
  }

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError('제목을 입력해주세요')
      return
    }

    if (selectedPlatforms.length === 0) {
      setError('최소 하나의 플랫폼을 선택해주세요')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_BASE}/youtube/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          run_id: runId,
          title: title,
          scheduled_time: scheduledTime,
          platforms: selectedPlatforms,
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Upload failed')
      }

      alert('영상이 예약되었습니다!')
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  // Calculate min/max datetime for scheduler
  const now = new Date()
  const minTime = now.toISOString().slice(0, 16)
  const maxTime = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16)

  return (
    <div className="share-modal-overlay" onClick={onClose}>
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="share-modal-header">
          <div className="share-modal-title">
            <span>콘텐츠 예약</span>
          </div>
          <button className="share-modal-close" onClick={onClose}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path fillRule="evenodd" d="M5.47 5.47a.75.75 0 011.06 0L12 10.94l5.47-5.47a.75.75 0 111.06 1.06L13.06 12l5.47 5.47a.75.75 0 11-1.06 1.06L12 13.06l-5.47 5.47a.75.75 0 01-1.06-1.06L10.94 12 5.47 6.53a.75.75 0 010-1.06z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="share-modal-content">
          {/* Title Input */}
          <div className="share-form-group">
            <label>릴 콘텐츠</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="릴의 매력적인 제목"
              disabled={loading}
            />
          </div>

          {/* Schedule Time */}
          <div className="share-form-group">
            <label>게시 시간</label>
            <input
              type="datetime-local"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
              min={minTime}
              max={maxTime}
              disabled={loading}
            />
          </div>

          {/* Platform Selection */}
          <div className="share-form-group">
            <label className="platform-label">
              릴을 게시할 플랫폼
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                <path fillRule="evenodd" d="M4.755 10.059a7.5 7.5 0 0112.548-3.364l1.903 1.903h-3.183a.75.75 0 100 1.5h4.992a.75.75 0 00.75-.75V4.356a.75.75 0 00-1.5 0v3.18l-1.9-1.9A9 9 0 003.306 9.67a.75.75 0 101.45.388zm15.408 3.352a.75.75 0 00-.919.53 7.5 7.5 0 01-12.548 3.364l-1.902-1.903h3.183a.75.75 0 000-1.5H2.984a.75.75 0 00-.75.75v4.992a.75.75 0 001.5 0v-3.18l1.9 1.9a9 9 0 0015.059-4.035.75.75 0 00-.53-.918z" clipRule="evenodd" />
              </svg>
            </label>
            <div className="platform-buttons">
              <button
                type="button"
                className={`platform-btn ${selectedPlatforms.includes('youtube') ? 'selected' : ''}`}
                onClick={() => handlePlatformToggle('youtube')}
                disabled={loading}
              >
                <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 576 512" className="youtube-icon" height="32" width="32">
                  <path d="M549.655 124.083c-6.281-23.65-24.787-42.276-48.284-48.597C458.781 64 288 64 288 64S117.22 64 74.629 75.486c-23.497 6.322-42.003 24.947-48.284 48.597-11.412 42.867-11.412 132.305-11.412 132.305s0 89.438 11.412 132.305c6.281 23.65 24.787 41.5 48.284 47.821C117.22 448 288 448 288 448s170.78 0 213.371-11.486c23.497-6.321 42.003-24.171 48.284-47.821 11.412-42.867 11.412-132.305 11.412-132.305s0-89.438-11.412-132.305zm-317.51 213.508V175.185l142.739 81.205-142.739 81.201z"></path>
                </svg>
                {connections.youtube ? 'YouTube' : 'YouTube 연결'}
              </button>

              <button
                type="button"
                className={`platform-btn ${selectedPlatforms.includes('instagram') ? 'selected' : ''}`}
                onClick={() => handlePlatformToggle('instagram')}
                disabled={loading}
              >
                <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 448 512" className="instagram-icon" height="32" width="32">
                  <path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"></path>
                </svg>
                {connections.instagram ? 'Instagram' : 'Instagram 연결'}
              </button>

              <button
                type="button"
                className={`platform-btn ${selectedPlatforms.includes('tiktok') ? 'selected' : ''}`}
                onClick={() => handlePlatformToggle('tiktok')}
                disabled={loading}
              >
                <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 448 512" className="tiktok-icon" height="32" width="32">
                  <path d="M448,209.91a210.06,210.06,0,0,1-122.77-39.25V349.38A162.55,162.55,0,1,1,185,188.31V278.2a74.62,74.62,0,1,0,52.23,71.18V0l88,0a121.18,121.18,0,0,0,1.86,22.17h0A122.18,122.18,0,0,0,381,102.39a121.43,121.43,0,0,0,67,20.14Z"></path>
                </svg>
                {connections.tiktok ? 'TikTok' : 'TikTok 연결'}
              </button>

              <button
                type="button"
                className={`platform-btn ${selectedPlatforms.includes('linkedin') ? 'selected' : ''}`}
                onClick={() => handlePlatformToggle('linkedin')}
                disabled={loading}
              >
                <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 448 512" className="linkedin-icon" height="32" width="32">
                  <path d="M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480H416c17.6 0 32-14.5 32-32.3V64.3c0-17.8-14.4-32.3-32-32.3zM135.4 416H69V202.2h66.5V416zm-33.2-243c-21.3 0-38.5-17.3-38.5-38.5S80.9 96 102.2 96c21.2 0 38.5 17.3 38.5 38.5 0 21.3-17.2 38.5-38.5 38.5zm282.1 243h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5 67.2 0 79.7 44.3 79.7 101.9V416z"></path>
                </svg>
                {connections.linkedin ? 'LinkedIn' : 'LinkedIn 연결'}
              </button>
            </div>

            {/* Legal disclaimer */}
            <div className="legal-disclaimer">
              <p>* By using YouTube publish feature, you consent to <a href="https://www.youtube.com/t/terms" target="_blank" rel="noreferrer">YouTube's ToS</a>, acknowledge our use of YouTube API and <a href="https://www.google.com/policies/privacy" target="_blank" rel="noreferrer">Google's Privacy Policy</a>. To revoke access, visit <a href="https://security.google.com/settings/security/permissions" target="_blank" rel="noreferrer">Google Account Permissions</a>.</p>
            </div>
          </div>

          {/* Error message */}
          {error && <div className="share-error">{error}</div>}

          {/* Submit Button */}
          <div className="share-submit-section">
            {user ? (
              <button
                className="share-submit-btn"
                onClick={handleSubmit}
                disabled={loading || selectedPlatforms.length === 0}
              >
                {loading ? (
                  '업로드 중...'
                ) : (
                  <>
                    <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 24 24" height="20" width="20">
                      <path d="m13 16 5-4-5-4v3H4v2h9z"></path>
                      <path d="M20 3h-9c-1.103 0-2 .897-2 2v4h2V5h9v14h-9v-4H9v4c0 1.103.897 2 2 2h9c1.103 0 2-.897 2-2V5c0-1.103-.897-2-2-2z"></path>
                    </svg>
                    예약하기
                  </>
                )}
              </button>
            ) : (
              <button className="share-submit-btn login-required" onClick={onClose}>
                <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 24 24" height="20" width="20">
                  <path d="m13 16 5-4-5-4v3H4v2h9z"></path>
                  <path d="M20 3h-9c-1.103 0-2 .897-2 2v4h2V5h9v14h-9v-4H9v4c0 1.103.897 2 2 2h9c1.103 0 2-.897 2-2V5c0-1.103-.897-2-2-2z"></path>
                </svg>
                계속하려면 로그인
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
