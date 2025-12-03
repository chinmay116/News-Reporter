// frontend/src/App.jsx

import React, { useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

const App = () => {
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState('')
  const [outputFile, setOutputFile] = useState('')

  const handleRun = async () => {
    setError('')
    setResult('')
    setOutputFile('')

    const trimmed = topic.trim()
    if (!trimmed) {
      setError('Please enter a topic.')
      return
    }

    setLoading(true)
    try {
      // Using /api here so Vite proxy sends it to FastAPI
      const response = await axios.post('http://localhost:8000/run-news', { topic: trimmed })
      setResult(response.data.result || '')
      setOutputFile(response.data.output_file || '')
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Something went wrong while running the news crew.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AI News Reporter</h1>
        <p>Enter a topic and let the CrewAI agents research and write an article.</p>
      </header>

      <main className="app-main">
        <div className="input-section">
          <label htmlFor="topic">Topic</label>
          <textarea
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Pricing differences between LLMs like ChatGPT, Gemini, Claude..."
            rows={4}
          />
          <button onClick={handleRun} disabled={loading}>
            {loading ? 'Generating...' : 'Generate Article'}
          </button>
          {error && <div className="error">{error}</div>}
        </div>

        <div className="output-section">
          <h2>Generated Article</h2>
          {loading && <p>Agents are researching and writing, please wait...</p>}
          {!loading && !result && <p>No article yet. Enter a topic and click "Generate Article".</p>}
          {!loading && result && (
            <div className="markdown-output">
              <ReactMarkdown>{result}</ReactMarkdown>
            </div>
          )}
          {!loading && outputFile && (
            <p className="file-info">
              Output also saved on server as: <code>{outputFile}</code>
            </p>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
