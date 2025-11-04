import { useState } from 'react'
import RunForm from './components/RunForm'
import RunStatus from './components/RunStatus'
import Player from './components/Player'

function App() {
  const [currentRunId, setCurrentRunId] = useState<string | null>(null)
  const [completedRun, setCompletedRun] = useState<any>(null)

  const handleRunCreated = (runId: string) => {
    setCurrentRunId(runId)
    setCompletedRun(null)
  }

  const handleRunCompleted = (runData: any) => {
    setCompletedRun(runData)
    setCurrentRunId(null)
  }

  const handleReset = () => {
    setCurrentRunId(null)
    setCompletedRun(null)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>AutoShorts</h1>
        <p>스토리텔링형 숏츠 자동 제작 시스템</p>
      </header>

      <main className="main">
        {!currentRunId && !completedRun && (
          <RunForm onRunCreated={handleRunCreated} />
        )}

        {currentRunId && (
          <RunStatus
            runId={currentRunId}
            onCompleted={handleRunCompleted}
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

      <footer className="footer">
        <p>Powered by FastAPI + Celery + ComfyUI + React</p>
      </footer>
    </div>
  )
}

export default App
