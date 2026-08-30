import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { CountryProvider } from './context/CountryContext'
import AgentPage from './pages/AgentPage'
import DocumentPage from './pages/DocumentPage'
import EntitiesPage from './pages/EntitiesPage'
import EntityPage from './pages/EntityPage'
import InboxPage from './pages/InboxPage'
import PriceBoardPage from './pages/PriceBoardPage'
import SearchPage from './pages/SearchPage'
import TopicsPage from './pages/TopicsPage'

export default function App() {
  return (
    <CountryProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<InboxPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="documents/:id" element={<DocumentPage />} />
          <Route path="entities" element={<EntitiesPage />} />
          <Route path="entities/:id" element={<EntityPage />} />
          <Route path="topics" element={<TopicsPage />} />
          <Route path="prices" element={<PriceBoardPage />} />
          <Route path="collect" element={<AgentPage />} />
          <Route path="agent" element={<AgentPage />} />
        </Route>
      </Routes>
    </CountryProvider>
  )
}
