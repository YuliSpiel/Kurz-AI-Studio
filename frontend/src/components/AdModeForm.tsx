import { useState, FormEvent } from 'react'
import { createRun, AuthenticationError } from '../api/client'

interface AdModeFormProps {
  onRunCreated: (runId: string) => void
  onAuthRequired: () => void
}

export default function AdModeForm({ onRunCreated, onAuthRequired }: AdModeFormProps) {
  const [productName, setProductName] = useState('')
  const [productDescription, setProductDescription] = useState('')
  const [keyFeatures, setKeyFeatures] = useState('')
  const [targetAudience, setTargetAudience] = useState('')
  const [callToAction, setCallToAction] = useState('')
  const [adDuration, setAdDuration] = useState<15 | 30 | 60>(15)
  const [adTone, setAdTone] = useState<'professional' | 'casual' | 'energetic'>('professional')
  const [numCuts, setNumCuts] = useState(5)
  const [artStyle, setArtStyle] = useState('현대적이고 세련된')
  const [musicGenre, setMusicGenre] = useState('upbeat')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Create enhanced prompt for ad mode
      const adPrompt = `
제품: ${productName}
설명: ${productDescription}
주요 기능: ${keyFeatures}
타겟: ${targetAudience}
CTA: ${callToAction}
톤: ${adTone}
      `.trim()

      const result = await createRun({
        mode: 'ad',
        prompt: adPrompt,
        num_characters: 1, // Ad mode typically has 1 spokesperson or no character
        num_cuts: numCuts,
        art_style: artStyle,
        music_genre: musicGenre,
      })

      onRunCreated(result.run_id)
    } catch (error) {
      console.error('Failed to create run:', error)
      if (error instanceof AuthenticationError) {
        onAuthRequired()
      } else {
        alert('Run 생성 실패: ' + error)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="run-form ad-mode-form">
      <h2>광고 모드</h2>
      <p className="mode-description">제품이나 서비스를 효과적으로 홍보하는 숏츠를 만들어보세요</p>

      <div className="form-group">
        <label>제품/서비스 이름</label>
        <input
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          placeholder="예: 스마트 워치 Pro"
          required
        />
      </div>

      <div className="form-group">
        <label>제품 설명</label>
        <textarea
          value={productDescription}
          onChange={(e) => setProductDescription(e.target.value)}
          placeholder="예: 건강과 편의를 동시에 챙기는 차세대 웨어러블 디바이스"
          rows={3}
          required
        />
      </div>

      <div className="form-group">
        <label>주요 기능 (쉼표로 구분)</label>
        <input
          type="text"
          value={keyFeatures}
          onChange={(e) => setKeyFeatures(e.target.value)}
          placeholder="예: 심박수 모니터링, 수면 분석, 방수 기능"
          required
        />
      </div>

      <div className="form-group">
        <label>타겟 고객</label>
        <input
          type="text"
          value={targetAudience}
          onChange={(e) => setTargetAudience(e.target.value)}
          placeholder="예: 20-30대 직장인, 건강 관리에 관심 많은 분"
          required
        />
      </div>

      <div className="form-group">
        <label>행동 유도 문구 (CTA)</label>
        <input
          type="text"
          value={callToAction}
          onChange={(e) => setCallToAction(e.target.value)}
          placeholder="예: 지금 바로 구매하고 20% 할인받으세요!"
          required
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>광고 길이 (초)</label>
          <select
            value={adDuration}
            onChange={(e) => setAdDuration(Number(e.target.value) as 15 | 30 | 60)}
          >
            <option value={15}>15초 (짧고 강렬)</option>
            <option value={30}>30초 (표준)</option>
            <option value={60}>60초 (상세)</option>
          </select>
        </div>

        <div className="form-group">
          <label>광고 톤</label>
          <select
            value={adTone}
            onChange={(e) => setAdTone(e.target.value as 'professional' | 'casual' | 'energetic')}
          >
            <option value="professional">전문적이고 신뢰감 있는</option>
            <option value="casual">편안하고 친근한</option>
            <option value="energetic">역동적이고 활기찬</option>
          </select>
        </div>
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

      <div className="form-group">
        <label>비주얼 스타일</label>
        <select
          value={artStyle}
          onChange={(e) => setArtStyle(e.target.value)}
        >
          <option value="현대적이고 세련된">현대적이고 세련된</option>
          <option value="미니멀하고 깔끔한">미니멀하고 깔끔한</option>
          <option value="생동감 넘치는">생동감 넘치는</option>
          <option value="프리미엄 럭셔리">프리미엄 럭셔리</option>
        </select>
      </div>

      <div className="form-group">
        <label>배경음악</label>
        <select
          value={musicGenre}
          onChange={(e) => setMusicGenre(e.target.value)}
        >
          <option value="upbeat">경쾌하고 활기찬</option>
          <option value="corporate">기업용 프로페셔널</option>
          <option value="energetic">에너제틱하고 강렬한</option>
          <option value="modern">모던하고 트렌디한</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={isSubmitting || !productName || !productDescription}
        className="btn-submit"
      >
        {isSubmitting ? '광고 생성 중...' : '광고 숏츠 만들기'}
      </button>
    </form>
  )
}
