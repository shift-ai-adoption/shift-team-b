import { useEffect, useState } from 'react'
import { apiJson, downloadExport, post } from '../api.js'

export default function HistoryPage() {
  const [items, setItems] = useState([])
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState('')

  const load = () => apiJson('/api/history').then(setItems).catch(e => setError(String(e.message)))
  useEffect(() => { load() }, [])

  const open = async (id) => {
    try { setDetail(await apiJson(`/api/history/${id}`)) }
    catch (e) { setError(String(e.message)) }
  }
  const rate = async (id, rating) => {
    try { await post(`/api/history/${id}/rating`, { rating }); load(); open(id) }
    catch (e) { setError(String(e.message)) }
  }

  return (
    <div>
      <h2>検索履歴</h2>
      <p className="muted">要件9: 検索時のプロンプト文言と結果を後から確認できます。要件13: ★評価で定性評価を記録します。</p>
      {error && <div className="error">{error}</div>}
      <div className="panel">
        <table>
          <thead><tr><th>ID</th><th>質問</th><th>DB</th><th>役職</th><th>評価</th><th>日時</th><th></th></tr></thead>
          <tbody>
            {items.map(h => (
              <tr key={h.id}>
                <td>{h.id}</td>
                <td>{h.query.slice(0, 40)}</td>
                <td>{h.db_used}</td>
                <td>{h.role}</td>
                <td>{h.rating ? '★'.repeat(h.rating) : '-'}</td>
                <td>{h.created_at.replace('T', ' ').slice(0, 16)}</td>
                <td><button className="secondary" style={{ marginTop: 0 }} onClick={() => open(h.id)}>詳細</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <div className="panel">
          <h3>履歴 #{detail.id}</h3>
          <label>質問</label>
          <div className="answer">{detail.query}</div>
          <label>回答</label>
          <div className="answer">{detail.answer || '(なし)'}</div>
          <details>
            <summary>LLMに送信したプロンプト全文</summary>
            <div className="answer">{detail.prompt || '(なし)'}</div>
          </details>
          <label>定性評価（1〜5）</label>
          <div>
            {[1, 2, 3, 4, 5].map(r => (
              <button key={r} className={detail.rating === r ? '' : 'secondary'}
                style={{ marginRight: 6 }} onClick={() => rate(detail.id, r)}>
                ★{r}
              </button>
            ))}
          </div>
          {detail.answer && (
            <div style={{ marginTop: 12 }}>
              {['markdown', 'word', 'excel'].map(f => (
                <button key={f} className="secondary" style={{ marginRight: 8 }}
                  onClick={() => downloadExport(detail.id, f)}>
                  {f} で出力
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
