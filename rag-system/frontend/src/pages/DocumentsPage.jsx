import { useEffect, useState } from 'react'
import { apiJson, del, post } from '../api.js'

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [error, setError] = useState('')

  const load = () => apiJson('/api/documents').then(setDocs).catch(e => setError(String(e.message)))
  useEffect(() => { load() }, [])

  const rollback = async (docId, version) => {
    try { await post(`/api/documents/${docId}/rollback?target_version=${version}`, {}); load() }
    catch (e) { setError(String(e.message)) }
  }
  const remove = async (docId) => {
    if (!confirm('この文書と全バージョンを削除しますか？')) return
    try { await del(`/api/documents/${docId}`); load() }
    catch (e) { setError(String(e.message)) }
  }

  return (
    <div>
      <h2>文書管理（バージョン管理）</h2>
      {error && <div className="error">{error}</div>}
      {docs.length === 0 && <p className="muted">文書がありません。アップロード画面から登録してください。</p>}
      {docs.map(d => (
        <div className="panel" key={d.document_id}>
          <h3>{d.filename}
            <button className="danger" style={{ float: 'right' }}
              onClick={() => remove(d.document_id)}>削除</button>
          </h3>
          <table>
            <thead>
              <tr><th>ver</th><th>状態</th><th>チャンク</th><th>chunk_size</th>
                  <th>公開レベル</th><th>検索対象</th><th>登録日時</th><th></th></tr>
            </thead>
            <tbody>
              {d.versions.map(v => (
                <tr key={v.version_id}>
                  <td>v{v.version}</td>
                  <td><span className={`badge ${v.status === 'vectorized' ? 'ok' : v.status === 'failed' ? 'ng' : ''}`}>{v.status}</span></td>
                  <td>{v.chunk_count}</td>
                  <td>{v.chunk_size ?? '-'}</td>
                  <td>{v.visibility_level}</td>
                  <td>{v.is_active ? '✅ 有効' : '－'}</td>
                  <td>{v.created_at.replace('T', ' ').slice(0, 16)}</td>
                  <td>
                    {!v.is_active && v.status === 'vectorized' && (
                      <button className="secondary" style={{ marginTop: 0 }}
                        onClick={() => rollback(d.document_id, v.version)}>
                        このverに切替
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
