import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './UploadManager.css'

interface ScheduleItem {
  id: string
  topic: string
  narrativeTone: string
  plotStructure: string
  artStyle: string
  uploadTime: string
  repeatDays: string[]
  isActive: boolean
}

const DAYS_OF_WEEK = [
  { id: 'mon', label: '월' },
  { id: 'tue', label: '화' },
  { id: 'wed', label: '수' },
  { id: 'thu', label: '목' },
  { id: 'fri', label: '금' },
  { id: 'sat', label: '토' },
  { id: 'sun', label: '일' },
]

const NARRATIVE_TONES = [
  { id: '', label: '지정 안함 (AI 추천)' },
  { id: '격식형', label: '격식형 (-입니다체) - 뉴스, 해설, 교육' },
  { id: '서술형', label: '서술형 (-함.체) - 요약, 정보전달' },
  { id: '친근한반말', label: '친근한 반말 (-거야, -지?) - 광고, 추천' },
  { id: '진지한나레이션', label: '진지한 나레이션체 - 스토리, 다큐' },
  { id: '감정강조', label: '감정 강조형 - 리액션, 감정 몰입' },
  { id: '코믹풍자', label: '코믹/풍자형 - 병맛, 밈 기반' },
]

const PLOT_STRUCTURES = [
  { id: '', label: '지정 안함 (AI 추천)' },
  { id: '기승전결', label: '고전적 기승전결 - 스토리텔링, 교육' },
  { id: '고구마사이다', label: '고구마-사이다형 - 답답함→반전 해결' },
  { id: '3막구조', label: '3막 구조 (시작-위기-해결) - 간결한 내러티브' },
  { id: '비교형', label: '비교형 (Before-After) - 변화 강조' },
  { id: '반전형', label: '반전형 (Twist Ending) - 밈, 코믹, 리액션' },
  { id: '정보나열', label: '정보 나열형 (Listicle) - 트렌드 요약' },
  { id: '감정곡선', label: '감정 곡선형 - 공감→위로→희망' },
  { id: '질문형', label: '질문형 오프닝 - 호기심 유발' },
  { id: '루프형', label: '루프형 (Looped Ending) - 반복 시청 유도' },
]

const ART_STYLES = [
  { id: '', label: '지정 안함 (AI 추천)' },
  { id: '애니메이션', label: '애니메이션' },
  { id: '실사풍', label: '실사풍' },
  { id: '일러스트', label: '일러스트' },
  { id: '3D렌더링', label: '3D 렌더링' },
  { id: '수채화', label: '수채화' },
]

export default function UploadManager() {
  const { user } = useAuth()
  const [schedules, setSchedules] = useState<ScheduleItem[]>([])
  const [showForm, setShowForm] = useState(false)

  // Form state
  const [topic, setTopic] = useState('')
  const [narrativeTone, setNarrativeTone] = useState('')
  const [plotStructure, setPlotStructure] = useState('')
  const [artStyle, setArtStyle] = useState('')
  const [uploadTime, setUploadTime] = useState('18:00')
  const [repeatDays, setRepeatDays] = useState<string[]>(['mon', 'wed', 'fri'])

  const handleAddSchedule = () => {
    if (!topic.trim()) return

    const newSchedule: ScheduleItem = {
      id: Date.now().toString(),
      topic,
      narrativeTone,
      plotStructure,
      artStyle,
      uploadTime,
      repeatDays,
      isActive: true,
    }

    setSchedules([...schedules, newSchedule])
    setShowForm(false)
    resetForm()
  }

  const resetForm = () => {
    setTopic('')
    setNarrativeTone('')
    setPlotStructure('')
    setArtStyle('')
    setUploadTime('18:00')
    setRepeatDays(['mon', 'wed', 'fri'])
  }

  const toggleDay = (dayId: string) => {
    setRepeatDays(prev =>
      prev.includes(dayId)
        ? prev.filter(d => d !== dayId)
        : [...prev, dayId]
    )
  }

  const toggleScheduleActive = (id: string) => {
    setSchedules(prev =>
      prev.map(s => s.id === id ? { ...s, isActive: !s.isActive } : s)
    )
  }

  const deleteSchedule = (id: string) => {
    setSchedules(prev => prev.filter(s => s.id !== id))
  }

  const getDayLabels = (days: string[]) => {
    return DAYS_OF_WEEK
      .filter(d => days.includes(d.id))
      .map(d => d.label)
      .join(', ')
  }

  if (!user) {
    return (
      <div className="upload-manager">
        <div className="upload-manager-header">
          <h2>📅 업로드 매니저</h2>
          <p>자동으로 영상을 생성하고 YouTube에 업로드합니다</p>
        </div>
        <div className="upload-manager-login-required">
          <span style={{ fontSize: '48px' }}>📺</span>
          <h3>로그인이 필요합니다</h3>
          <p>업로드 매니저를 사용하려면 먼저 로그인해주세요.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="upload-manager">
      <div className="upload-manager-header">
        <h2>📅 업로드 매니저</h2>
        <p>주제와 스타일을 설정하면 자동으로 영상을 생성하고 YouTube에 업로드합니다</p>
      </div>

      {/* Schedule List */}
      <div className="schedule-list">
        {schedules.length === 0 && !showForm ? (
          <div className="schedule-empty">
            <span style={{ fontSize: '48px' }}>⏰</span>
            <h3>등록된 스케줄이 없습니다</h3>
            <p>아래 버튼을 눌러 첫 번째 자동 업로드 스케줄을 만들어보세요.</p>
          </div>
        ) : (
          schedules.map(schedule => (
            <div key={schedule.id} className={`schedule-card ${!schedule.isActive ? 'inactive' : ''}`}>
              <div className="schedule-card-header">
                <h4>{schedule.topic}</h4>
                <div className="schedule-card-actions">
                  <button
                    className={`toggle-btn ${schedule.isActive ? 'active' : ''}`}
                    onClick={() => toggleScheduleActive(schedule.id)}
                    title={schedule.isActive ? '일시정지' : '활성화'}
                  >
                    {schedule.isActive ? '⏸️' : '▶️'}
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => deleteSchedule(schedule.id)}
                    title="삭제"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              <div className="schedule-card-body">
                <div className="schedule-info">
                  <span className="schedule-tag">{schedule.narrativeTone || 'AI 추천 말투'}</span>
                  <span className="schedule-tag">{schedule.plotStructure || 'AI 추천 구조'}</span>
                  <span className="schedule-tag">{schedule.artStyle || 'AI 추천 스타일'}</span>
                </div>
                <div className="schedule-timing">
                  <span>🕐</span>
                  <span>{schedule.uploadTime}</span>
                  <span className="schedule-days">{getDayLabels(schedule.repeatDays)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Schedule Form */}
      {showForm && (
        <div className="schedule-form">
          <h3>새 스케줄 추가</h3>

          <div className="form-group">
            <label>주제 / 키워드</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="예: 재미있는 역사 이야기, IT 뉴스 요약, 요리 레시피..."
            />
            <span className="form-hint">매번 이 주제로 새로운 영상이 자동 생성됩니다</span>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>말투</label>
              <select value={narrativeTone} onChange={(e) => setNarrativeTone(e.target.value)}>
                {NARRATIVE_TONES.map(tone => (
                  <option key={tone.id} value={tone.id}>{tone.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>전개 구조</label>
              <select value={plotStructure} onChange={(e) => setPlotStructure(e.target.value)}>
                {PLOT_STRUCTURES.map(structure => (
                  <option key={structure.id} value={structure.id}>{structure.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>아트 스타일</label>
            <select value={artStyle} onChange={(e) => setArtStyle(e.target.value)}>
              {ART_STYLES.map(style => (
                <option key={style.id} value={style.id}>{style.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>업로드 시각</label>
            <input
              type="time"
              value={uploadTime}
              onChange={(e) => setUploadTime(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>반복 요일</label>
            <div className="day-selector">
              {DAYS_OF_WEEK.map(day => (
                <button
                  key={day.id}
                  type="button"
                  className={`day-btn ${repeatDays.includes(day.id) ? 'selected' : ''}`}
                  onClick={() => toggleDay(day.id)}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-actions">
            <button className="btn-cancel" onClick={() => { setShowForm(false); resetForm(); }}>
              취소
            </button>
            <button className="btn-submit" onClick={handleAddSchedule} disabled={!topic.trim()}>
              스케줄 추가
            </button>
          </div>
        </div>
      )}

      {/* Add Button */}
      {!showForm && (
        <button className="add-schedule-btn" onClick={() => setShowForm(true)}>
          ➕ 새 스케줄 추가
        </button>
      )}

      {/* Info Banner */}
      <div className="upload-manager-info">
        <span style={{ fontSize: '24px' }}>📺</span>
        <div>
          <strong>YouTube 연동 필요</strong>
          <p>자동 업로드를 위해서는 YouTube 계정 연동이 필요합니다. 라이브러리에서 공유 버튼을 눌러 연동할 수 있습니다.</p>
        </div>
      </div>
    </div>
  )
}
