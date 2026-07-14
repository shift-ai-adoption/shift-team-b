import { useEffect, useState } from 'react'
import { apiJson, downloadExport, post } from '../api.js'

const ROLES = [['general', '一般'], ['manager', '管理職'], ['executive', '役員']]
const DBS = ['pgvector', 'chroma', 'qdrant']

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [db, setDb] = useState('pgvector')
  const [role, setRole] = useState('general')
  const [templateId, setTemplateId] = useState('')
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    apiJson(`/api/templates?role=${role}`).then(setTemplates).catch(() => {})
  }, [role])

  const search = async () => {
    if (!query.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      setResult(await post('/api/search', {
        query, db, role,
        template_id: templateId ? Number(templateId) : null,
      }))
    } catch (e) { setError(String(e.message)) }
    setLoading(false)
  }

  return (
    <div>
      <h2>検索</h2>
      <div className="panel">
        <label>質問</label>
        <textarea value={query} onChange={e => setQuery(e.target.value)}
          placeholder="蓄積された文書に対する質問を入力..." />
        <div className="row">
          <div>
            <label>ベクトルDB</label>
            <select value={db} onChange={e => setDb(e.target.value)}>
              {DBS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label>役職</label>
            <select value={role} onChange={e => setRole(e.target.value)}>
              {ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div>
            <label>出力テンプレート</label>
            <select value={templateId} onChange={e => setTemplateId(e.target.value)}>
              <option value="">（指定なし）</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name} ({t.format})</option>
              ))}
            </select>
          </div>
        </div>
        <button onClick={search} disabled={loading}>
          {loading ? '検索中...' : '検索実行'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="panel">
          <h3>回答 <span className="muted">({result.db} / {result.latency_ms}ms)</span></h3>
          <div className="answer">{result.answer || '(回答生成なし)'}</div>
          <div style={{ marginTop: 12 }}>
            {['markdown', 'word', 'excel'].map(f => (
              <button key={f} className="secondary" style={{ marginRight: 8 }}
                onClick={() => downloadExport(result.history_id, f)}>
                {f} で出力
              </button>
            ))}
          </div>
          <details>
            <summary>参照チャンク ({result.hits.length}件)</summary>
            <table>
              <thead><tr><th>#</th><th>ファイル</th><th>ver</th><th>スコア</th><th>内容</th></tr></thead>
              <tbody>
                {result.hits.map((h, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td><td>{h.filename}</td><td>{h.version}</td>
                    <td>{h.score.toFixed(4)}</td>
                    <td>{h.content.slice(0, 100)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      )}
    </div>
  )
}
