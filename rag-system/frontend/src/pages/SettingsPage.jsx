import { useEffect, useState } from 'react'
import { apiJson, put } from '../api.js'

export default function SettingsPage() {
  const [settings, setSettings] = useState(null)
  const [chunkSize, setChunkSize] = useState('')
  const [overlap, setOverlap] = useState('')
  const [topK, setTopK] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    apiJson('/api/settings').then(s => {
      setSettings(s)
      setChunkSize(String(s.chunk_size))
      setOverlap(String(s.chunk_overlap))
      setTopK(String(s.top_k))
    }).catch(e => setError(String(e.message)))
  }, [])

  const save = async () => {
    setError(''); setSaved(false)
    try {
      const s = await put('/api/settings', {
        chunk_size: Number(chunkSize),
        chunk_overlap: Number(overlap),
        top_k: Number(topK),
      })
      setSettings(s); setSaved(true)
    } catch (e) { setError(String(e.message)) }
  }

  if (!settings) return <p className="muted">読み込み中...</p>
  return (
    <div>
      <h2>設定</h2>
      <p className="muted">要件14: チャンクサイズは候補から選択し、値を直接編集することもできます。</p>
      <div className="panel">
        <label>チャンクサイズ（候補から選択）</label>
        <select value={chunkSize} onChange={e => setChunkSize(e.target.value)}>
          {settings.chunk_size_options.map(o => <option key={o} value={o}>{o}</option>)}
          {!settings.chunk_size_options.includes(Number(chunkSize)) &&
            <option value={chunkSize}>{chunkSize}（カスタム）</option>}
        </select>
        <label>チャンクサイズ（直接編集）</label>
        <input value={chunkSize} onChange={e => setChunkSize(e.target.value)} />
        <label>オーバーラップ</label>
        <select value={overlap} onChange={e => setOverlap(e.target.value)}>
          {settings.chunk_overlap_options.map(o => <option key={o} value={o}>{o}</option>)}
          {!settings.chunk_overlap_options.includes(Number(overlap)) &&
            <option value={overlap}>{overlap}（カスタム）</option>}
        </select>
        <label>検索件数 (top_k)</label>
        <input value={topK} onChange={e => setTopK(e.target.value)} />
        <button onClick={save}>保存</button>
        {saved && <span className="badge ok" style={{ marginLeft: 10 }}>保存しました</span>}
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  )
}
