import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { CountryProvider } from './context/CountryContext'
import ActivitiesPage from './pages/ActivitiesPage'
import AgentPage from './pages/AgentPage'
import IdeasPage from './pages/IdeasPage'
import OverviewPage from './pages/OverviewPage'
import PriceBoardPage from './pages/PriceBoardPage'
import SocialPage from './pages/SocialPage'

export default function App() {
  return (
    <CountryProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<OverviewPage />} />
          <Route path="prices" element={<PriceBoardPage />} />
          <Route path="activities" element={<ActivitiesPage />} />
          <Route path="social" element={<SocialPage />} />
          <Route path="agent" element={<AgentPage />} />
          <Route path="ideas" element={<IdeasPage />} />
        </Route>
      </Routes>
    </CountryProvider>
  )
}
