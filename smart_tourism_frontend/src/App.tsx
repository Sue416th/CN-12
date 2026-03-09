import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ItineraryList from './pages/ItineraryList'
import ItineraryDetail from './pages/ItineraryDetail'
import UserProfile from './pages/UserProfile'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/itineraries" element={<ItineraryList />} />
        <Route path="/itinerary/:id" element={<ItineraryDetail />} />
        <Route path="/profile" element={<UserProfile />} />
      </Routes>
    </BrowserRouter>
  )
}
