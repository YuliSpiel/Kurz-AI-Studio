import { useState, FormEvent } from 'react'
import { createRun } from '../api/client'

interface StoryModeFormProps {
  onRunCreated: (runId: string) => void
}

export default function StoryModeForm({ onRunCreated }: StoryModeFormProps) {
  const [prompt, setPrompt] = useState('')
  const [numCharacters, setNumCharacters] = useState<1 | 2>(1)
  const [numCuts, setNumCuts] = useState(3)
  const [artStyle, setArtStyle] = useState('파스텔 수채화')
  const [musicGenre, setMusicGenre] = useState('ambient')
  const [storyTheme, setStoryTheme] = useState('')
  const [targetAge, setTargetAge] = useState<'kids' | 'teens' | 'adults'>('kids')
  const [narrativeTone, setNarrativeTone] = useState<'cheerful' | 'serious' | 'mysterious'>('cheerful')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Create enhanced prompt for story mode
      const enhancedPrompt = `${prompt} (테마: ${storyTheme}, 대상: ${targetAge}, 톤: ${narrativeTone})`

      const result = await createRun({
        mode: 'story',
        prompt: enhancedPrompt,
        num_characters: numCharacters,
        num_cuts: numCuts,
        art_style: artStyle,
        music_genre: musicGenre,
      })

      onRunCreated(result.run_id)
    } catch (error) {
      console.error('Failed to create run:', error)
      alert('Run 생성 실패: ' + error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="run-form story-mode-form">
      <h2>스토리 모드</h2>
      <p className="mode-description">캐릭터 중심의 이야기를 만들어보세요</p>

      <div className="form-group">
        <label>스토리 주제</label>
        <input
          type="text"
          value={storyTheme}
          onChange={(e) => setStoryTheme(e.target.value)}
          placeholder="예: 우정, 용기, 모험, 성장"
          required
        />
      </div>

      <div className="form-group">
        <label>스토리 개요</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="예: 작은 고양이가 용기를 내어 높은 나무에 올라가는 이야기"
          rows={4}
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>주인공 수</label>
          <select
            value={numCharacters}
            onChange={(e) => setNumCharacters(Number(e.target.value) as 1 | 2)}
          >
            <option value={1}>1명 (단독 주인공)</option>
            <option value={2}>2명 (듀오)</option>
          </select>
        </div>

        <div className="form-group">
          <label>장면 수</label>
          <input
            type="number"
            value={numCuts}
            onChange={(e) => setNumCuts(Number(e.target.value))}
            min={3}
            max={10}
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>대상 연령</label>
          <select
            value={targetAge}
            onChange={(e) => setTargetAge(e.target.value as 'kids' | 'teens' | 'adults')}
          >
            <option value="kids">어린이 (5-12세)</option>
            <option value="teens">청소년 (13-18세)</option>
            <option value="adults">성인 (19세+)</option>
          </select>
        </div>

        <div className="form-group">
          <label>서사 톤</label>
          <select
            value={narrativeTone}
            onChange={(e) => setNarrativeTone(e.target.value as 'cheerful' | 'serious' | 'mysterious')}
          >
            <option value="cheerful">밝고 경쾌한</option>
            <option value="serious">진지하고 감동적인</option>
            <option value="mysterious">신비롭고 긴장감 있는</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label>화풍</label>
        <select
          value={artStyle}
          onChange={(e) => setArtStyle(e.target.value)}
        >
          <option value="파스텔 수채화">파스텔 수채화</option>
          <option value="애니메이션">애니메이션</option>
          <option value="동화책 일러스트">동화책 일러스트</option>
          <option value="3D 카툰">3D 카툰</option>
        </select>
      </div>

      <div className="form-group">
        <label>배경음악</label>
        <select
          value={musicGenre}
          onChange={(e) => setMusicGenre(e.target.value)}
        >
          <option value="ambient">잔잔한 앰비언트</option>
          <option value="cinematic">영화 같은 감동적</option>
          <option value="upbeat">경쾌하고 밝은</option>
          <option value="mysterious">신비롭고 몽환적</option>
        </select>
      </div>

      <button type="submit" disabled={isSubmitting || !prompt || !storyTheme} className="btn-submit">
        {isSubmitting ? '스토리 생성 중...' : '스토리 숏츠 만들기'}
      </button>
    </form>
  )
}
