import { useState } from 'react'
import { post, uploadFile } from '../api.js'

export default function UploadPage() {
  const [file, setFile] = useState(null)
  const [visibility, setVisibility] = useState(1)
  const [uploaded, setUploaded] = useState(null)
  const [chunkSize, setChunkSize] = useState('')
  const [vecResult, setVecResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const doUpload = async () => {
    if (!file) return
    setBusy(true); setError(''); setVecResult(null)
    try { setUploaded(await uploadFile(file, visibility)) }
    catch (e) { setError(String(e.message)) }
    setBusy(false)
  }

  const doVectorize = async () => {
    setBusy(true); setError('')
    try {
      setVecResult(await post('/api/vectorize', {
        version_id: uploaded.version_id,
        chunk_size: chunkSize ? Number(chunkSize) : null,
      }))
    } catch (e) { setError(String(e.message)) }
    setBusy(false)
  }

  return (
    <div>
      <h2>アップロード</h2>
      <div className="panel">
        <p className="muted">要件7: アップロードとベクトル化は分離されています。①ファイル保存 → ②ベクトル化 の2ステップです。</p>
        <label>ファイル (.pdf / .txt / .md / .docx)</label>
        <input type="file" onChange={e => setFile(e.target.files[0])} />
        <label>公開レベル（役職制御）</label>
        <select value={visibility} onChange={e => setVisibility(Number(e.target.value))}>
          <option value={1}>1: 一般（全役職が閲覧可）</option>
          <option value={2}>2: 管理職以上</option>
          <option value={3}>3: 役員のみ</option>
        </select>
        <button onClick={doUpload} disabled={!file || busy}>① アップロード</button>
        {error && <div className="error">{error}</div>}
      </div>

      {uploaded && (
        <div className="panel">
          <p>
            <span className="badge ok">アップロード完了</span>{' '}
            {uploaded.filename} — v{uploaded.version} ({uploaded.size_bytes} bytes)
          </p>
          <label>チャンクサイズ（空欄 = 設定画面の既定値）</label>
          <input value={chunkSize} onChange={e => setChunkSize(e.target.value)}
            placeholder="例: 512" />
          <button onClick={doVectorize} disabled={busy}>
            {busy ? 'ベクトル化中...' : '② ベクトル化実行（3DB同時登録）'}
          </button>
          {vecResult && (
            <p>
              <span className="badge ok">ベクトル化完了</span>{' '}
              {vecResult.chunks}チャンク / chunk_size={vecResult.chunk_size} /
              登録DB: {Object.keys(vecResult.registered_dbs).join(', ')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
