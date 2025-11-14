import { useState, useEffect } from 'react'
import { getPlotCsv, confirmPlot, regeneratePlot, PlotCsvData } from '../api/client'

interface PlotReviewModalProps {
  runId: string
  onClose: () => void
  onConfirmed: () => void
}

export default function PlotReviewModal({ runId, onClose, onConfirmed }: PlotReviewModalProps) {
  const [plotData, setPlotData] = useState<PlotCsvData | null>(null)
  const [csvContent, setCsvContent] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isConfirming, setIsConfirming] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [hasEdited, setHasEdited] = useState(false)

  useEffect(() => {
    loadPlotCsv()
  }, [runId])

  const loadPlotCsv = async () => {
    setIsLoading(true)
    try {
      const data = await getPlotCsv(runId)
      setPlotData(data)
      setCsvContent(data.csv_content)
    } catch (error) {
      console.error('Failed to load plot CSV:', error)
      alert('플롯 CSV 로드 실패: ' + error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = async () => {
    setIsConfirming(true)
    try {
      await confirmPlot(runId, hasEdited ? csvContent : undefined)
      alert('플롯이 확정되었습니다. 에셋 생성이 시작됩니다.')
      onConfirmed()
      onClose()
    } catch (error) {
      console.error('Failed to confirm plot:', error)
      alert('플롯 확정 실패: ' + error)
    } finally {
      setIsConfirming(false)
    }
  }

  const handleRegenerate = async () => {
    if (!confirm('플롯을 재생성하시겠습니까? 현재 플롯은 삭제됩니다.')) {
      return
    }

    setIsRegenerating(true)
    try {
      await regeneratePlot(runId)
      alert('플롯 재생성이 시작되었습니다. 잠시 후 새로운 플롯이 표시됩니다.')
      onClose()
    } catch (error) {
      console.error('Failed to regenerate plot:', error)
      alert('플롯 재생성 실패: ' + error)
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleCsvChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCsvContent(e.target.value)
    setHasEdited(true)
  }

  if (isLoading) {
    return (
      <div style={overlayStyle}>
        <div style={modalStyle}>
          <h2>플롯 로딩 중...</h2>
          <p>잠시만 기다려주세요.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={headerStyle}>
          <h2>📋 플롯 검수</h2>
          <button onClick={onClose} style={closeButtonStyle}>✕</button>
        </div>

        <div style={contentStyle}>
          <div style={infoBoxStyle}>
            <p><strong>Run ID:</strong> {runId}</p>
            <p><strong>모드:</strong> {plotData?.mode || 'general'}</p>
            <p style={{ marginTop: '10px', fontSize: '14px', color: '#6B7280' }}>
              아래 CSV를 직접 수정할 수 있습니다. 수정 후 "확정" 버튼을 누르면 수정된 내용으로 영상이 생성됩니다.
            </p>
          </div>

          <div style={editorContainerStyle}>
            <label style={labelStyle}>플롯 CSV (수정 가능)</label>
            <textarea
              value={csvContent}
              onChange={handleCsvChange}
              style={textareaStyle}
              spellCheck={false}
            />
            {hasEdited && (
              <p style={editedWarningStyle}>
                ⚠️ CSV가 수정되었습니다. 확정 시 수정된 내용이 반영됩니다.
              </p>
            )}
          </div>
        </div>

        <div style={footerStyle}>
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating || isConfirming}
            style={{
              ...buttonStyle,
              backgroundColor: isRegenerating ? '#9CA3AF' : '#EF4444',
            }}
          >
            {isRegenerating ? '재생성 중...' : '🔄 다시 만들기'}
          </button>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={onClose}
              style={{
                ...buttonStyle,
                backgroundColor: '#6B7280',
              }}
            >
              취소
            </button>
            <button
              onClick={handleConfirm}
              disabled={isConfirming || isRegenerating}
              style={{
                ...buttonStyle,
                backgroundColor: isConfirming ? '#9CA3AF' : '#10B981',
              }}
            >
              {isConfirming ? '확정 중...' : '✓ 확정'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Styles
const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.75)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 2000,
}

const modalStyle: React.CSSProperties = {
  backgroundColor: 'white',
  borderRadius: '12px',
  width: '90%',
  maxWidth: '900px',
  maxHeight: '90vh',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
}

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '20px 30px',
  borderBottom: '1px solid #E5E7EB',
}

const closeButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  fontSize: '24px',
  cursor: 'pointer',
  color: '#6B7280',
  padding: '0',
  width: '30px',
  height: '30px',
}

const contentStyle: React.CSSProperties = {
  padding: '20px 30px',
  overflowY: 'auto',
  flex: 1,
}

const infoBoxStyle: React.CSSProperties = {
  backgroundColor: '#F3F4F6',
  padding: '15px',
  borderRadius: '8px',
  marginBottom: '20px',
}

const editorContainerStyle: React.CSSProperties = {
  marginBottom: '20px',
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontWeight: 'bold',
  marginBottom: '8px',
  fontSize: '14px',
  color: '#374151',
}

const textareaStyle: React.CSSProperties = {
  width: '100%',
  minHeight: '400px',
  padding: '12px',
  fontSize: '13px',
  fontFamily: 'monospace',
  border: '1px solid #D1D5DB',
  borderRadius: '6px',
  resize: 'vertical',
}

const editedWarningStyle: React.CSSProperties = {
  marginTop: '8px',
  fontSize: '13px',
  color: '#D97706',
  fontWeight: '500',
}

const footerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '20px 30px',
  borderTop: '1px solid #E5E7EB',
}

const buttonStyle: React.CSSProperties = {
  padding: '10px 20px',
  border: 'none',
  borderRadius: '6px',
  fontSize: '14px',
  fontWeight: '600',
  color: 'white',
  cursor: 'pointer',
  transition: 'opacity 0.2s',
}
