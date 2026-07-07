import { NavLink, Route, Routes } from 'react-router-dom'
import DocumentsPage from './pages/DocumentsPage.jsx'
import EvaluationPage from './pages/EvaluationPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import SearchPage from './pages/SearchPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import TemplatesPage from './pages/TemplatesPage.jsx'
import UploadPage from './pages/UploadPage.jsx'

const NAV = [
  ['/', '検索', SearchPage],
  ['/upload', 'アップロード', UploadPage],
  ['/documents', '文書管理', DocumentsPage],
  ['/history', '検索履歴', HistoryPage],
  ['/templates', 'テンプレート', TemplatesPage],
  ['/evaluation', 'DB評価', EvaluationPage],
  ['/settings', '設定', SettingsPage],
]

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>RAG System</h1>
        <nav>
          {NAV.map(([path, label]) => (
            <NavLink key={path} to={path} end={path === '/'}>{label}</NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          {NAV.map(([path, , C]) => <Route key={path} path={path} element={<C />} />)}
        </Routes>
      </main>
    </div>
  )
}
