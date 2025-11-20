import { useState } from 'react'
import HeroChat from './components/HeroChat'
import RunForm from './components/RunForm'
import StoryModeForm from './components/StoryModeForm'
import AdModeForm from './components/AdModeForm'
import RunStatus from './components/RunStatus'
import Player from './components/Player'
import AuthModal from './components/AuthModal'
import Library from './components/Library'
import { PromptEnhancementResult } from './api/client'
import { useAuth } from './contexts/AuthContext'

type AppMode = 'general' | 'story' | 'ad'
type ViewMode = 'home' | 'library'

function App() {
  const { user, logout } = useAuth()
  const [viewMode, setViewMode] = useState<ViewMode>('home')
  const [appMode, setAppMode] = useState<AppMode>('general')
  const [currentRunId, setCurrentRunId] = useState<string | null>(null)
  const [completedRun, setCompletedRun] = useState<any>(null)
  const [showDetailedForm, setShowDetailedForm] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login')

  // Enhancement data from HeroChat
  const [enhancementData, setEnhancementData] = useState<{
    enhancement: PromptEnhancementResult
    originalPrompt: string
  } | null>(null)

  // Review mode flag
  const [isReviewMode, setIsReviewMode] = useState(false)

  const handleRunCreated = (runId: string, reviewMode: boolean = false) => {
    setCurrentRunId(runId)
    setCompletedRun(null)
    setIsReviewMode(reviewMode)
  }

  const handleRunCompleted = (runData: any) => {
    setCompletedRun(runData)
    setCurrentRunId(null)
  }

  const handleReset = () => {
    setCurrentRunId(null)
    setCompletedRun(null)
    setShowDetailedForm(false)
    setEnhancementData(null)
    setIsReviewMode(false)
    setViewMode('home')
  }

  const handleEditorMode = () => {
    setShowDetailedForm(true)
    setAppMode('general')
    setEnhancementData(null)
    setViewMode('home')
  }

  const handleLibraryClick = () => {
    if (!user) {
      setAuthModalMode('login')
      setShowAuthModal(true)
      return
    }
    setViewMode('library')
  }

  const handleHeroChatSubmit = (_prompt: string, mode: 'general' | 'story' | 'ad') => {
    setAppMode(mode)
    setShowDetailedForm(true)
  }

  const handleEnhancementReady = (enhancement: PromptEnhancementResult, originalPrompt: string) => {
    setEnhancementData({ enhancement, originalPrompt })
    setAppMode('general')
    setShowDetailedForm(true)
  }

  const renderModeButtons = () => (
    <div className="mode-selector">
      <button
        className={`mode-btn ${appMode === 'general' ? 'active' : ''}`}
        onClick={() => setAppMode('general')}
        disabled={!!currentRunId || !!completedRun}
      >
        일반 모드
      </button>
      <button
        className={`mode-btn ${appMode === 'story' ? 'active' : ''}`}
        onClick={() => setAppMode('story')}
        disabled={!!currentRunId || !!completedRun}
      >
        스토리 모드
      </button>
      <button
        className={`mode-btn ${appMode === 'ad' ? 'active' : ''}`}
        onClick={() => setAppMode('ad')}
        disabled={!!currentRunId || !!completedRun}
      >
        광고모드
      </button>
    </div>
  )

  const renderInputForm = () => {
    switch (appMode) {
      case 'general':
        return <RunForm onRunCreated={handleRunCreated} enhancementData={enhancementData} />
      case 'story':
        return <StoryModeForm onRunCreated={handleRunCreated} />
      case 'ad':
        return <AdModeForm onRunCreated={handleRunCreated} />
    }
  }

  return (
    <>
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-left">
            <div className="navbar-logo" onClick={handleReset} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.0001px' }}>
                <img src="/logo/kurz_logo.png" alt="Kurz Logo" style={{ height: '2.7rem', width: 'auto' }} />
                <h1>KURZ AI</h1>
              </div>
              <p style={{ textAlign: 'center', marginLeft: '5px' }}>가장 쉬운 숏폼 제작 플랫폼</p>
            </div>
            <div className="navbar-menu">
              <a href="#" onClick={(e) => { e.preventDefault(); handleEditorMode(); }} className="navbar-menu-item">에디터 모드</a>
              <a href="#" onClick={(e) => { e.preventDefault(); handleLibraryClick(); }} className="navbar-menu-item">라이브러리</a>
              <a href="#" className="navbar-menu-item">캘린더</a>
              <a href="#" className="navbar-menu-item">커뮤니티</a>
            </div>
          </div>
          <div className="navbar-right">
            {user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{user.username}</div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>Credits: {user.credits}</div>
                </div>
                <button
                  className="auth-btn login-btn"
                  onClick={logout}
                >
                  Log out
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <button
                  className="auth-btn login-btn"
                  onClick={() => {
                    setAuthModalMode('login')
                    setShowAuthModal(true)
                  }}
                >
                  Log in
                </button>
                <button
                  className="auth-btn signup-btn"
                  onClick={() => {
                    setAuthModalMode('register')
                    setShowAuthModal(true)
                  }}
                >
                  Get started
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <div className="app">
        {viewMode === 'library' ? (
          <Library onSelectVideo={(runId) => {
            setCurrentRunId(runId)
            setViewMode('home')
          }} />
        ) : (
          <>
            {!currentRunId && !completedRun && !showDetailedForm && (
              <HeroChat
                onSubmit={handleHeroChatSubmit}
                onEnhancementReady={handleEnhancementReady}
                onRunCreated={handleRunCreated}
                disabled={!!currentRunId || !!completedRun}
              />
            )}

            {(showDetailedForm || currentRunId || completedRun) && (
              <main className="main">
                {showDetailedForm && !currentRunId && !completedRun && (
                  <>
                    {renderModeButtons()}
                    {renderInputForm()}
                  </>
                )}

                {currentRunId && (
                  <RunStatus
                    runId={currentRunId}
                    onCompleted={handleRunCompleted}
                    reviewMode={isReviewMode}
                  />
                )}

                {completedRun && (
                  <>
                    <Player runData={completedRun} />
                    <button onClick={handleReset} className="btn-reset">
                      새로 만들기
                    </button>
                  </>
                )}
              </main>
            )}
          </>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialMode={authModalMode}
      />
    </>
  )
}

export default App
