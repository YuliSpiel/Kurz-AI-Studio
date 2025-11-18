import { useState, useEffect } from 'react'
import { enhancePrompt, PromptEnhancementResult } from '../api/client'

interface HeroChatProps {
  onSubmit: (prompt: string, mode: 'general' | 'story' | 'ad') => void
  onEnhancementReady?: (enhancement: PromptEnhancementResult, originalPrompt: string) => void
  disabled?: boolean
}

const ROTATING_WORDS = ['Epic', 'Cool', 'Fire', 'Viral', 'Neat', 'Bold']
const COLORS = ['#6f9fa0', '#7189a0', '#c9a989'] // 짙게 한 버전

const PLACEHOLDERS = {
  general: ['2030 직장인 공감 썰', '세계 5대 명소 추천'],
  story: ['소꿉친구랑 결혼 골인한 이야기', '아기 고양이의 우주 모험'],
  ad: ['상품 페이지 링크를 입력하세요']
}

function HeroChat({ onSubmit, onEnhancementReady, disabled = false }: HeroChatProps) {
  const [prompt, setPrompt] = useState('')
  const [selectedMode, setSelectedMode] = useState<'general' | 'story' | 'ad'>('general')
  const [currentWordIndex, setCurrentWordIndex] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)
  const [typedPlaceholder, setTypedPlaceholder] = useState('')
  const [currentPlaceholderText, setCurrentPlaceholderText] = useState('')

  // Enhancement states
  const [isEnhancing, setIsEnhancing] = useState(false)
  const [enhancementResult, setEnhancementResult] = useState<PromptEnhancementResult | null>(null)
  const [showEnhancementModal, setShowEnhancementModal] = useState(false)

  // Editable enhancement values
  const [editedTitle, setEditedTitle] = useState('')
  const [editedPlot, setEditedPlot] = useState('')
  const [editedNumCuts, setEditedNumCuts] = useState(3)
  const [editedNumCharacters, setEditedNumCharacters] = useState(1)
  const [editedArtStyle, setEditedArtStyle] = useState('')
  const [editedMusicGenre, setEditedMusicGenre] = useState('')
  const [editedNarrativeTone, setEditedNarrativeTone] = useState('')
  const [editedPlotStructure, setEditedPlotStructure] = useState('')

  // Rotating words animation
  useEffect(() => {
    const interval = setInterval(() => {
      setIsAnimating(true)
      setTimeout(() => {
        setCurrentWordIndex((prev) => (prev + 1) % ROTATING_WORDS.length)
        setIsAnimating(false)
      }, 300)
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  // Typing effect for placeholder
  useEffect(() => {
    if (!currentPlaceholderText) return

    // Ad mode: no typing effect, show immediately
    if (selectedMode === 'ad') {
      setTypedPlaceholder(currentPlaceholderText)
      return
    }

    let currentCharIndex = 0
    setTypedPlaceholder('')

    // Typing animation
    const typingInterval = setInterval(() => {
      if (currentCharIndex <= currentPlaceholderText.length) {
        setTypedPlaceholder(currentPlaceholderText.slice(0, currentCharIndex))
        currentCharIndex++
      } else {
        clearInterval(typingInterval)
        // Stay on completed text - don't switch automatically
      }
    }, 100) // Type one character every 100ms

    return () => clearInterval(typingInterval)
  }, [currentPlaceholderText, selectedMode])

  // Initialize with random placeholder on mount
  useEffect(() => {
    const placeholders = PLACEHOLDERS[selectedMode]
    const randomIndex = Math.floor(Math.random() * placeholders.length)
    setCurrentPlaceholderText(placeholders[randomIndex])
  }, [])

  const handleModeChange = (mode: 'general' | 'story' | 'ad') => {
    const placeholders = PLACEHOLDERS[mode]
    const randomIndex = Math.floor(Math.random() * placeholders.length)
    setCurrentPlaceholderText(placeholders[randomIndex])
    setSelectedMode(mode)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || disabled) return

    // For general mode, trigger AI enhancement
    if (selectedMode === 'general') {
      // Show modal immediately with loading state
      setShowEnhancementModal(true)
      setIsEnhancing(true)

      try {
        const result = await enhancePrompt(prompt, 'general')
        setEnhancementResult(result)
      } catch (error: any) {
        console.error('Failed to enhance prompt:', error)
        setShowEnhancementModal(false)
        alert(`프롬프트 풍부화 실패:\n${error?.message || String(error)}\n\n백엔드 서버가 실행 중인지 확인해주세요.`)
      } finally {
        setIsEnhancing(false)
      }
    } else {
      // For story/ad modes, proceed directly
      onSubmit(prompt, selectedMode)
    }
  }

  // Initialize editable state when enhancement result arrives
  useEffect(() => {
    if (enhancementResult) {
      setEditedTitle(enhancementResult.suggested_title)
      setEditedPlot(enhancementResult.suggested_plot_outline)
      setEditedNumCuts(enhancementResult.suggested_num_cuts)
      setEditedNumCharacters(enhancementResult.suggested_num_characters)
      setEditedArtStyle(enhancementResult.suggested_art_style)
      setEditedMusicGenre(enhancementResult.suggested_music_genre)
      setEditedNarrativeTone(enhancementResult.suggested_narrative_tone)
      setEditedPlotStructure(enhancementResult.suggested_plot_structure)
    }
  }, [enhancementResult])

  const handleAutoGenerate = () => {
    if (!enhancementResult) return

    // Create edited enhancement object
    const editedEnhancement: PromptEnhancementResult = {
      ...enhancementResult,
      suggested_title: editedTitle,
      suggested_plot_outline: editedPlot,
      suggested_num_cuts: editedNumCuts,
      suggested_num_characters: editedNumCharacters,
      suggested_art_style: editedArtStyle,
      suggested_music_genre: editedMusicGenre,
      suggested_narrative_tone: editedNarrativeTone,
      suggested_plot_structure: editedPlotStructure
    }

    // TODO: Directly trigger run creation with edited enhancement
    // For now, pass to review mode (will implement direct generation later)
    if (onEnhancementReady) {
      onEnhancementReady(editedEnhancement, prompt)
    }

    setShowEnhancementModal(false)
    setEnhancementResult(null)
  }

  const handleReviewMode = () => {
    if (!enhancementResult) return

    // Create edited enhancement object
    const editedEnhancement: PromptEnhancementResult = {
      ...enhancementResult,
      suggested_title: editedTitle,
      suggested_plot_outline: editedPlot,
      suggested_num_cuts: editedNumCuts,
      suggested_num_characters: editedNumCharacters,
      suggested_art_style: editedArtStyle,
      suggested_music_genre: editedMusicGenre,
      suggested_narrative_tone: editedNarrativeTone,
      suggested_plot_structure: editedPlotStructure
    }

    // Pass to RunForm for further review/modification
    if (onEnhancementReady) {
      onEnhancementReady(editedEnhancement, prompt)
    }

    setShowEnhancementModal(false)
    setEnhancementResult(null)
  }

  const handleCancelEnhancement = () => {
    setShowEnhancementModal(false)
    setEnhancementResult(null)
  }

  return (
    <section className="hero-chat-section">
      <div className="hero-chat-container">
        <div className="hero-chat-header">
          <h1 className="hero-chat-title">
            <span>Create something </span>
            <span
              className={`hero-chat-lovable ${isAnimating ? 'animating' : ''}`}
              style={{ color: COLORS[currentWordIndex % COLORS.length] }}
            >
              {ROTATING_WORDS[currentWordIndex]}
            </span>
          </h1>
          <p className="hero-chat-subtitle">
            텍스트 한 줄이면, 플롯·이미지·음악·보이스부터 숏폼영상까지 AI가 완성합니다
          </p>
        </div>

        <div className="hero-chat-form-wrapper">
          <form onSubmit={handleSubmit} className="hero-chat-form">
            <div className="hero-chat-input-container">
              <textarea
                className="hero-chat-textarea"
                placeholder={typedPlaceholder}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                maxLength={5000}
                disabled={disabled}
                rows={1}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = Math.min(target.scrollHeight, 200) + 'px'
                }}
              />
            </div>

            <div className="hero-chat-actions">
              <div className="hero-chat-mode-selector">
                <button
                  type="button"
                  className={`hero-mode-chip ${selectedMode === 'general' ? 'active' : ''}`}
                  onClick={() => handleModeChange('general')}
                  disabled={disabled}
                >
                  일반
                </button>
                <button
                  type="button"
                  className={`hero-mode-chip ${selectedMode === 'story' ? 'active' : ''}`}
                  onClick={() => handleModeChange('story')}
                  disabled={disabled}
                >
                  스토리
                </button>
                <button
                  type="button"
                  className={`hero-mode-chip ${selectedMode === 'ad' ? 'active' : ''}`}
                  onClick={() => handleModeChange('ad')}
                  disabled={disabled}
                >
                  광고
                </button>
              </div>

              <button
                type="submit"
                className="hero-chat-submit"
                disabled={!prompt.trim() || disabled}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  className="hero-submit-icon"
                >
                  <path d="M11 19V7.415l-3.293 3.293a1 1 0 1 1-1.414-1.414l5-5 .074-.067a1 1 0 0 1 1.34.067l5 5a1 1 0 1 1-1.414 1.414L13 7.415V19a1 1 0 1 1-2 0"></path>
                </svg>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* AI Enhancement Modal */}
      {showEnhancementModal && (
        <div className="enhancement-modal-overlay">
          <div className="enhancement-modal-container">
            <div className="enhancement-modal-layout">
              {/* Left: Stepper */}
              <div className="enhancement-stepper">
                <div className={`enhancement-step ${!isEnhancing ? 'completed' : 'active'}`}>
                  <div className="enhancement-step-icon">
                    {!isEnhancing ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="#FFFFFF">
                        <path d="M19.7071 6.29289C20.0976 6.68342 20.0976 7.31658 19.7071 7.70711L9.70711 17.7071C9.31658 18.0976 8.68342 18.0976 8.29289 17.7071L4.29289 13.7071C3.90237 13.3166 3.90237 12.6834 4.29289 12.2929C4.68342 11.9024 5.31658 11.9024 5.70711 12.2929L9 15.5858L18.2929 6.29289C18.6834 5.90237 19.3166 5.90237 19.7071 6.29289Z"/>
                      </svg>
                    ) : (
                      <div className="enhancement-step-spinner"></div>
                    )}
                  </div>
                  <div className="enhancement-step-content">
                    <div className="enhancement-step-label">프롬프트 분석</div>
                  </div>
                </div>

                <div className={`enhancement-step-connector ${!isEnhancing ? 'completed' : ''}`}></div>

                <div className={`enhancement-step ${enhancementResult ? 'completed' : isEnhancing ? 'active' : ''}`}>
                  <div className="enhancement-step-icon">
                    {enhancementResult ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="#FFFFFF">
                        <path d="M19.7071 6.29289C20.0976 6.68342 20.0976 7.31658 19.7071 7.70711L9.70711 17.7071C9.31658 18.0976 8.68342 18.0976 8.29289 17.7071L4.29289 13.7071C3.90237 13.3166 3.90237 12.6834 4.29289 12.2929C4.68342 11.9024 5.31658 11.9024 5.70711 12.2929L9 15.5858L18.2929 6.29289C18.6834 5.90237 19.3166 5.90237 19.7071 6.29289Z"/>
                      </svg>
                    ) : isEnhancing ? (
                      <div className="enhancement-step-spinner"></div>
                    ) : (
                      <span className="enhancement-step-number">2</span>
                    )}
                  </div>
                  <div className="enhancement-step-content">
                    <div className="enhancement-step-label">영상 설정 생성</div>
                  </div>
                </div>

                <div className={`enhancement-step-connector ${enhancementResult ? 'completed' : ''}`}></div>

                <div className={`enhancement-step ${enhancementResult ? 'active' : ''}`}>
                  <div className="enhancement-step-icon">
                    <span className="enhancement-step-number">3</span>
                  </div>
                  <div className="enhancement-step-content">
                    <div className="enhancement-step-label">결과 확인</div>
                  </div>
                </div>
              </div>

              {/* Right: Content */}
              <div className="enhancement-content">
                {isEnhancing ? (
                  // Loading state
                  <div className="enhancement-loading">
                    <div className="loading-spinner">⚙️</div>
                    <h3 className="loading-title">AI 풍부화 진행 중...</h3>
                    <p className="loading-subtitle">
                      프롬프트를 분석하고 최적의 영상 설정을 추천하고 있습니다
                    </p>
                  </div>
                ) : enhancementResult ? (
                  // Content state
                  <>
                    <div className="enhancement-content-header">
                      <p className="enhancement-step-caption">Step 3</p>
                      <h3 className="enhancement-modal-title">✨ AI 풍부화 결과</h3>
                    </div>

                    <div className="enhancement-section">
                      <label className="enhancement-label">제안된 영상 제목</label>
                      <input
                        type="text"
                        className="enhancement-input"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        placeholder="영상 제목 입력"
                      />
                    </div>

                    <div className="enhancement-section">
                      <label className="enhancement-label">📖 예상 플롯</label>
                      <textarea
                        className="enhancement-textarea"
                        value={editedPlot}
                        onChange={(e) => setEditedPlot(e.target.value)}
                        placeholder="플롯 내용 입력"
                        rows={4}
                      />
                    </div>

                    <div className="enhancement-grid">
                      <div className="enhancement-grid-item">
                        <label className="enhancement-grid-label">컷 수</label>
                        <input
                          type="number"
                          className="enhancement-input-small"
                          value={editedNumCuts}
                          onChange={(e) => setEditedNumCuts(parseInt(e.target.value) || 3)}
                          min="1"
                          max="20"
                        />
                      </div>

                      <div className="enhancement-grid-item">
                        <label className="enhancement-grid-label">캐릭터 수</label>
                        <input
                          type="number"
                          className="enhancement-input-small"
                          value={editedNumCharacters}
                          onChange={(e) => setEditedNumCharacters(parseInt(e.target.value) || 1)}
                          min="1"
                          max="5"
                        />
                      </div>

                      <div className="enhancement-grid-item">
                        <label className="enhancement-grid-label">화풍</label>
                        <input
                          type="text"
                          className="enhancement-input-small"
                          value={editedArtStyle}
                          onChange={(e) => setEditedArtStyle(e.target.value)}
                          placeholder="화풍"
                        />
                      </div>

                      <div className="enhancement-grid-item">
                        <label className="enhancement-grid-label">음악 장르</label>
                        <input
                          type="text"
                          className="enhancement-input-small"
                          value={editedMusicGenre}
                          onChange={(e) => setEditedMusicGenre(e.target.value)}
                          placeholder="음악 장르"
                        />
                      </div>

                      <div className="enhancement-grid-item-full">
                        <label className="enhancement-grid-label">말투</label>
                        <select
                          className="enhancement-select"
                          value={editedNarrativeTone}
                          onChange={(e) => setEditedNarrativeTone(e.target.value)}
                        >
                          <option value="격식형">격식형 (-입니다체) - 뉴스, 해설, 교육</option>
                          <option value="서술형">서술형 (-함.체) - 요약, 정보전달</option>
                          <option value="친근한반말">친근한 반말 (-거야, -지?) - 광고, 추천</option>
                          <option value="진지한나레이션">진지한 나레이션체 - 스토리, 다큐</option>
                          <option value="감정강조">감정 강조형 - 리액션, 감정 몰입</option>
                          <option value="코믹풍자">코믹/풍자형 - 병맛, 밈 기반</option>
                        </select>
                      </div>

                      <div className="enhancement-grid-item-full">
                        <label className="enhancement-grid-label">전개 구조</label>
                        <select
                          className="enhancement-select"
                          value={editedPlotStructure}
                          onChange={(e) => setEditedPlotStructure(e.target.value)}
                        >
                          <option value="기승전결">고전적 기승전결 - 스토리텔링, 교육</option>
                          <option value="고구마사이다">고구마-사이다형 - 답답함→반전 해결</option>
                          <option value="3막구조">3막 구조 (시작-위기-해결) - 간결한 내러티브</option>
                          <option value="비교형">비교형 (Before-After) - 변화 강조</option>
                          <option value="반전형">반전형 (Twist Ending) - 밈, 코믹, 리액션</option>
                          <option value="정보나열">정보 나열형 (Listicle) - 트렌드 요약</option>
                          <option value="감정곡선">감정 곡선형 - 공감→위로→희망</option>
                          <option value="질문형">질문형 오프닝 - 호기심 유발</option>
                        </select>
                      </div>
                    </div>

                    <div className="enhancement-reasoning">
                      <div className="enhancement-reasoning-label">💡 제안 이유</div>
                      <div className="enhancement-reasoning-value">
                        {enhancementResult.reasoning}
                      </div>
                    </div>

                    <div className="enhancement-actions">
                      <button onClick={handleCancelEnhancement} className="enhancement-btn-cancel">
                        취소
                      </button>
                      <div className="enhancement-btn-wrapper">
                        <button
                          onClick={handleReviewMode}
                          className="enhancement-btn-review"
                        >
                          검수 모드
                        </button>
                        <span className="enhancement-tooltip">상세 폼에서 추가 설정을 조정할 수 있습니다</span>
                      </div>
                      <div className="enhancement-btn-wrapper">
                        <button
                          onClick={handleAutoGenerate}
                          className="enhancement-btn-apply"
                        >
                          자동 생성
                        </button>
                        <span className="enhancement-tooltip">현재 설정으로 바로 영상 제작을 시작합니다</span>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

export default HeroChat
