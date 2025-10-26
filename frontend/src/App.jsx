
import React, { useState } from 'react'

export default function App() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [error, setError] = useState(null)

  const backendBase = process.env.REACT_APP_BACKEND || 'http://localhost:8000'

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    if (!file) return setError('Please select a file')
    setUploading(true)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch(`${backendBase}/upload`, {
        method: 'POST',
        body: form,
      })

      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || 'Upload failed')
      }

      const j = await res.json()
      setDownloadUrl(`${backendBase}${j.download_url}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1>Video Converter — Upload to MP4</h1>
      <form onSubmit={onSubmit}>
        <input type="file" accept="video/*" onChange={(e)=>setFile(e.target.files[0])} />
        <div style={{ marginTop: 12 }}>
          <button type="submit" disabled={uploading}>{uploading ? 'Converting...' : 'Upload & Convert'}</button>
        </div>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {downloadUrl && (
        <p>
          <strong>Done:</strong> <a href={downloadUrl} target="_blank" rel="noreferrer">Download converted MP4</a>
        </p>
      )}

      <p style={{ marginTop: 24, color: '#666' }}>Small UI. Files are converted server-side using ffmpeg.</p>
    </div>
  )
}
