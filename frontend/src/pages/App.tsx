import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Home from './Home'
import TripPage from './TripPage'

export default function App() {
  return (
    <div>
      <div className="container">
        <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', gap: 12, marginBottom: 14}}>
          <Link to="/" style={{textDecoration:'none'}}>
            <div style={{display:'flex', alignItems:'center', gap: 10}}>
              <div style={{width: 36, height: 36, borderRadius: 12, background:'#0f172a', color:'white', display:'grid', placeItems:'center', fontWeight: 900}}>
                T
              </div>
              <div>
                <div style={{fontWeight: 900, letterSpacing:'-0.02em'}}>TripGen</div>
                <div className="small">Routes • Transport • Food • Hotels • Word</div>
              </div>
            </div>
          </Link>
          <span className="badge">Frontend + Backend</span>
        </div>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/trip/:id" element={<TripPage />} />
        </Routes>

        <div className="small" style={{marginTop: 18}}>
          Tip: Use clear place names (e.g., “Erode Bus Stand”, “Valparai”).
        </div>
      </div>
    </div>
  )
}
