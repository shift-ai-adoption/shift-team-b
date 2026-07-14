import { useEffect, useState } from 'react'
import { apiJson, del, post } from '../api.js'

const EMPTY = { name: '', format: 'markdown', description: '', structure: '', min_role_level: 1 }

export default function TemplatesPage() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')

  const load = () => apiJson('/api/templates').then(setItems).catch(e => setError(String(e.message)))
  useEffect(() => { load() }, [])

  const create = async () => {
    try { await post('/api/templates', form); setForm(EMPTY); load() }
    catch (e) { setError(String(e.message)) }
  }
  const remove = async (id) => {
    if (!confirm('このテンプレートを削除しますか？')) return
    try { await del(`/api/templates/${id}`); load() }
    catch (e) { setError(String(e.message)) }
  }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div>
      <h2>出力テンプレート</h2>
      <p className="muted">要件10/11: 出力フォーマット（markdown / word / excel）をテンプレートとして管理します。要件12: min_role_level で役職制御。</p>
      {error && <div className="error">{error}</div>}
      <div className="panel">
        <table>
          <thead><tr><th>ID</th><th>名前</th><th>形式</th><th>説明</th><th>必要役職Lv</th><th></th></tr></thead>
          <tbody>
            {items.map(t => (
              <tr key={t.id}>
                <td>{t.id}</td><td>{t.name}</td><td>{t.format}</td>
                <td>{t.description}</td><td>{t.min_role_level}</td>
                <td><button className="danger" style={{ marginTop: 0 }} onClick={() => remove(t.id)}>削除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h3>新規テンプレート</h3>
        <label>名前</label>
        <input value={form.name} onChange={set('name')} />
        <div className="row">
          <div>
            <label>形式</label>
            <select value={form.format} onChange={set('format')}>
              <option value="markdown">markdown</option>
              <option value="word">word (docx)</option>
              <option value="excel">excel (xlsx)</option>
            </select>
          </div>
          <div>
            <label>必要役職レベル (1=一般 2=管理職 3=役員)</label>
            <select value={form.min_role_level}
              onChange={e => setForm({ ...form, min_role_level: Number(e.target.value) })}>
              <option value={1}>1</option><option value={2}>2</option><option value={3}>3</option>
            </select>
          </div>
        </div>
        <label>説明</label>
        <input value={form.description} onChange={set('description')} />
        <label>出力構成の指示（LLMへの指示文）</label>
        <textarea value={form.structure} onChange={set('structure')} />
        <button onClick={create} disabled={!form.name || !form.structure}>作成</button>
      </div>
    </div>
  )
}
