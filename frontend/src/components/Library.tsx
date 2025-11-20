import { useState, useEffect } from 'react'
import { getMyRuns, deleteRun, RunListItem } from '../api/client'
import './Library.css'

export default function Library({ onSelectVideo }: { onSelectVideo?: (runId: string) => void }) {
  const [runs, setRuns] = useState<RunListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null)

  useEffect(() => {
    loadRuns()
  }, [])

  const loadRuns = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getMyRuns()
      setRuns(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load videos')
      console.error('Failed to load runs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (runId: string, event: React.MouseEvent) => {
    event.stopPropagation() // Prevent triggering onSelectVideo

    if (!confirm('이 영상을 삭제하시겠습니까? 삭제된 영상은 복구할 수 없습니다.')) {
      return
    }

    try {
      setDeletingRunId(runId)
      await deleteRun(runId)

      // Remove from local state
      setRuns(prev => prev.filter(run => run.run_id !== runId))

      console.log(`Deleted run: ${runId}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete video')
      console.error('Failed to delete run:', err)
    } finally {
      setDeletingRunId(null)
    }
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'COMPLETED':
        return '#10b981' // green
      case 'FAILED':
        return '#ef4444' // red
      case 'IDLE':
      case 'PLOT_GENERATION':
      case 'PLOT_REVIEW':
      case 'ASSET_GENERATION':
      case 'LAYOUT_REVIEW':
      case 'RENDERING':
      case 'QA':
        return '#f59e0b' // orange (in progress)
      default:
        return '#6b7280' // gray
    }
  }

  const getStateText = (state: string) => {
    const stateMap: Record<string, string> = {
      'IDLE': '대기중',
      'PLOT_GENERATION': '시나리오 생성중',
      'PLOT_REVIEW': '시나리오 검토',
      'ASSET_GENERATION': '에셋 생성중',
      'LAYOUT_REVIEW': '레이아웃 검토',
      'RENDERING': '영상 합성중',
      'QA': '품질 검수중',
      'COMPLETED': '완료',
      'FAILED': '실패',
    }
    return stateMap[state] || state
  }

  if (loading) {
    return (
      <div className="library-container">
        <div className="library-loading">영상 로딩중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="library-container">
        <div className="library-error">
          <p>{error}</p>
          <button onClick={loadRuns} className="retry-btn">다시 시도</button>
        </div>
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="library-container">
        <div className="library-empty">
          <h2>아직 만든 영상이 없어요</h2>
          <p>첫 번째 영상을 만들어보세요!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="library-container">
      <div className="library-header">
        <h1>내 영상 라이브러리</h1>
        <p className="library-count">총 {runs.length}개의 영상</p>
      </div>

      <div className="library-grid">
        {runs.map((run) => (
          <div
            key={run.id}
            className="library-item"
            onClick={() => onSelectVideo?.(run.run_id)}
            style={{ cursor: onSelectVideo ? 'pointer' : 'default' }}
          >
            {/* 9:16 Thumbnail */}
            <div className="library-thumbnail">
              {run.video_url && run.state === 'COMPLETED' ? (
                <video
                  src={run.video_url}
                  className="thumbnail-video"
                  muted
                  playsInline
                  preload="metadata"
                  onMouseEnter={(e) => {
                    e.currentTarget.play()
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.pause()
                    e.currentTarget.currentTime = 0
                  }}
                  poster={run.thumbnail_url || undefined}
                />
              ) : (
                <div className="thumbnail-placeholder">
                  <div className="placeholder-icon">🎬</div>
                  <div className="placeholder-text">{getStateText(run.state)}</div>
                </div>
              )}

              {/* State Badge */}
              <div
                className="state-badge"
                style={{ backgroundColor: getStateColor(run.state) }}
              >
                {getStateText(run.state)}
              </div>

              {/* Progress Bar */}
              {run.state !== 'COMPLETED' && run.state !== 'FAILED' && (
                <div className="progress-bar-container">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${run.progress}%` }}
                  />
                </div>
              )}
            </div>

            {/* Info */}
            <div className="library-info">
              <h3 className="library-title">{run.prompt.slice(0, 40)}{run.prompt.length > 40 ? '...' : ''}</h3>
              <div className="library-meta">
                <span className="meta-mode">{run.mode === 'general' ? '일반' : run.mode === 'story' ? '스토리' : '광고'}</span>
                <span className="meta-date">{new Date(run.created_at).toLocaleDateString('ko-KR')}</span>
              </div>

              {/* Delete Button */}
              <button
                className="delete-btn"
                onClick={(e) => handleDelete(run.run_id, e)}
                disabled={deletingRunId === run.run_id}
                title="영상 삭제"
              >
                {deletingRunId === run.run_id ? '삭제중...' : '🗑️ 삭제'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
