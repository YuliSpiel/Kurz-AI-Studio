import { useState, FormEvent } from 'react'
import { createRun, uploadReferenceImage } from '../api/client'

interface RunFormProps {
  onRunCreated: (runId: string) => void
}

export default function RunForm({ onRunCreated }: RunFormProps) {
  const [mode, setMode] = useState<'general' | 'story' | 'ad'>('general')
  const [prompt, setPrompt] = useState('')
  const [numCharacters, setNumCharacters] = useState<1 | 2>(1)
  const [numCuts, setNumCuts] = useState(3)
  const [artStyle, setArtStyle] = useState('파스텔 수채화')
  const [musicGenre, setMusicGenre] = useState('ambient')
  const [referenceFiles, setReferenceFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Layout customization states
  const [videoTitle, setVideoTitle] = useState('')
  const [titleBgColor, setTitleBgColor] = useState('#323296') // Dark blue
  const [titleFont, setTitleFont] = useState('NanumGothicBold')
  const [titleFontSize, setTitleFontSize] = useState(120)
  const [subtitleFont, setSubtitleFont] = useState('NanumGothic')
  const [subtitleFontSize, setSubtitleFontSize] = useState(90)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Upload reference images
      const referenceImages: string[] = []
      for (const file of referenceFiles) {
        const filename = await uploadReferenceImage(file)
        referenceImages.push(filename)
      }

      // Create run with layout customization
      const result = await createRun({
        mode,
        prompt,
        num_characters: numCharacters,
        num_cuts: numCuts,
        art_style: artStyle,
        music_genre: musicGenre,
        reference_images: referenceImages.length > 0 ? referenceImages : undefined,
        video_title: videoTitle,
        layout_config: {
          title_bg_color: titleBgColor,
          title_font: titleFont,
          title_font_size: titleFontSize,
          subtitle_font: subtitleFont,
          subtitle_font_size: subtitleFontSize,
        },
      })

      onRunCreated(result.run_id)
    } catch (error) {
      console.error('Failed to create run:', error)
      alert('Run 생성 실패: ' + error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setReferenceFiles(Array.from(e.target.files))
    }
  }

  return (
    <div className="run-form-wrapper">
      <form onSubmit={handleSubmit} className="run-form">
        <h2>새 숏츠 생성</h2>

      <div className="form-group">
        <label>모드</label>
        <select value={mode} onChange={(e) => setMode(e.target.value as 'general' | 'story' | 'ad')}>
          <option value="general">일반</option>
          <option value="story">스토리텔링</option>
          <option value="ad">광고</option>
        </select>
      </div>

      <div className="form-group">
        <label>프롬프트</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="예: 우주를 여행하는 고양이 이야기"
          rows={4}
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>등장인물 수</label>
          <select
            value={numCharacters}
            onChange={(e) => setNumCharacters(Number(e.target.value) as 1 | 2)}
          >
            <option value={1}>1명</option>
            <option value={2}>2명</option>
          </select>
        </div>

        <div className="form-group">
          <label>컷 수 (1-10)</label>
          <input
            type="number"
            value={numCuts}
            onChange={(e) => setNumCuts(Number(e.target.value))}
            min={1}
            max={10}
            required
          />
        </div>
      </div>

      <div className="form-group">
        <label>화풍</label>
        <input
          type="text"
          value={artStyle}
          onChange={(e) => setArtStyle(e.target.value)}
          placeholder="예: 파스텔 수채화, 애니메이션, 사실적"
        />
      </div>

      <div className="form-group">
        <label>음악 장르</label>
        <input
          type="text"
          value={musicGenre}
          onChange={(e) => setMusicGenre(e.target.value)}
          placeholder="예: ambient, cinematic, upbeat"
        />
      </div>

      <div className="form-group">
        <label>참조 이미지 (선택)</label>
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
        />
        {referenceFiles.length > 0 && (
          <p className="file-count">{referenceFiles.length}개 파일 선택됨</p>
        )}
      </div>
      </form>

      {/* Layout Customization Section */}
      <div className="layout-customization-section">
        <h3>레이아웃 커스터마이징</h3>

        <div className="layout-customization-grid">
          {/* Left: Preview */}
          <div className="preview-container">
            <div className="layout-preview">
              <div
                className="preview-title-block"
                style={{
                  backgroundColor: titleBgColor,
                  height: '12.5%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <span style={{
                  color: 'white',
                  fontSize: `${titleFontSize / 8}px`,
                  fontWeight: 'bold',
                  whiteSpace: 'pre-wrap',
                  textAlign: 'center'
                }}>
                  {videoTitle || '샘플 타이틀'}
                </span>
              </div>
              <div className="preview-content" style={{
                height: '87.5%',
                position: 'relative',
                overflow: 'hidden',
                backgroundColor: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {/* Background Image - 1:1 centered */}
                <img
                  src="/outputs/20251107_1617_고구마를좋아하는/scene_1_scene.png"
                  alt="Preview"
                  style={{
                    maxWidth: '100%',
                    maxHeight: '100%',
                    objectFit: 'contain',
                    position: 'relative',
                    zIndex: 1
                  }}
                />
                {/* Subtitle overlay */}
                <div style={{
                  position: 'absolute',
                  top: '10%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '90%',
                  textAlign: 'center',
                  zIndex: 2
                }}>
                  <span style={{
                    fontSize: `${subtitleFontSize / 6}px`,
                    color: 'white',
                    textShadow: '1px 1px 2px black',
                    fontWeight: 'bold'
                  }}>
                    "고구마가 세상에서 제일 맛있어!"
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Settings */}
          <div className="settings-container">
            <div className="form-group">
              <label>영상 제목</label>
              <textarea
                value={videoTitle}
                onChange={(e) => setVideoTitle(e.target.value)}
                placeholder="영상 제목을 입력하세요 (엔터로 줄바꿈 가능)"
                rows={2}
                style={{ resize: 'vertical' }}
              />
            </div>

            <div className="form-group">
              <label>타이틀 블록 색상</label>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <input
                  type="color"
                  value={titleBgColor}
                  onChange={(e) => setTitleBgColor(e.target.value)}
                  style={{ width: '60px', height: '40px' }}
                />
                <input
                  type="text"
                  value={titleBgColor}
                  onChange={(e) => setTitleBgColor(e.target.value)}
                  placeholder="#323296"
                  style={{ flex: 1 }}
                />
              </div>
            </div>

            <div className="form-group">
              <label>타이틀 폰트 크기: {titleFontSize}px</label>
              <input
                type="range"
                min="100"
                max="150"
                value={titleFontSize}
                onChange={(e) => setTitleFontSize(Number(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label>자막 폰트 크기: {subtitleFontSize}px</label>
              <input
                type="range"
                min="70"
                max="120"
                value={subtitleFontSize}
                onChange={(e) => setSubtitleFontSize(Number(e.target.value))}
              />
            </div>
          </div>
        </div>

        <button type="submit" disabled={isSubmitting || !prompt} className="btn-submit" onClick={handleSubmit}>
          {isSubmitting ? '생성 중...' : '숏츠 생성 시작'}
        </button>
      </div>
    </div>
  )
}
