import { useEffect, useState } from 'react'
import { apiJson, post } from '../api.js'

export default function EvaluationPage() {
  const [query, setQuery] = useState('')
  const [expected, setExpected] = useState('')
  const [docs, setDocs] = useState([])
  const [result, setResult] = useState(null)
  const [summary, setSummary] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadSummary = () => apiJson('/api/evaluation/summary').then(setSummary).catch(() => {})
  useEffect(() => {
    apiJson('/api/documents').then(setDocs).catch(() => {})
    loadSummary()
  }, [])

  const run = async () => {
    setBusy(true); setError('')
    try {
      setResult(await post('/api/evaluation', { query, expected_filename: expected }))
      loadSummary()
    } catch (e) { setError(String(e.message)) }
    setBusy(false)
  }

  return (
    <div>
      <h2>ベクトルDB評価（定量比較）</h2>
      <p className="muted">要件13/15: 同一クエリを3つのベクトルDBに投げ、正解文書の順位から Hit Rate / MRR / レイテンシを比較します。</p>
      <div className="panel">
        <label>テストクエリ</label>
        <textarea value={query} onChange={e => setQuery(e.target.value)} />
        <label>正解となる文書（このクエリでヒットすべきファイル）</label>
        <select value={expected} onChange={e => setExpected(e.target.value)}>
          <option value="">選択してください</option>
          {docs.map(d => <option key={d.document_id} value={d.filename}>{d.filename}</option>)}
        </select>
        <button onClick={run} disabled={!query || !expected || busy}>
          {busy ? '評価中...' : '3DB同時評価を実行'}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {result && (
        <div className="panel">
          <h3>評価結果 #{result.evaluation_id}</h3>
          <table>
            <thead><tr><th>DB</th><th>正解の順位</th><th>Hit@1</th><th>Hit@3</th><th>Hit@5</th><th>RR</th><th>レイテンシ</th></tr></thead>
            <tbody>
              {Object.entries(result.results).map(([name, r]) => (
                <tr key={name}>
                  <td>{name}</td>
                  {r.error ? <td colSpan={6} className="error">{r.error}</td> : <>
                    <td>{r.rank_of_expected ?? '圏外'}</td>
                    <td>{r['hit@1'] ? '✅' : '－'}</td>
                    <td>{r['hit@3'] ? '✅' : '－'}</td>
                    <td>{r['hit@5'] ? '✅' : '－'}</td>
                    <td>{r.reciprocal_rank.toFixed(3)}</td>
                    <td>{r.latency_ms}ms</td>
                  </>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {summary && summary.count > 0 && (
        <div className="panel">
          <h3>累積サマリ（{summary.count}件の評価）</h3>
          <table>
            <thead><tr><th>DB</th><th>評価数</th><th>MRR</th><th>Hit@1</th><th>Hit@3</th><th>Hit@5</th><th>平均レイテンシ</th></tr></thead>
            <tbody>
              {Object.entries(summary.per_db).map(([name, s]) => (
                <tr key={name}>
                  <td>{name}</td><td>{s.evaluations}</td><td>{s.MRR}</td>
                  <td>{s['hit_rate@1']}</td><td>{s['hit_rate@3']}</td><td>{s['hit_rate@5']}</td>
                  <td>{s.avg_latency_ms}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p><strong>推奨:</strong> {summary.recommendation}</p>
        </div>
      )}
    </div>
  )
}
