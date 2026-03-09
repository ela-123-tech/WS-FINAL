import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchTrip } from '../lib/api'

const statFacts = [
  { value: '120+', label: 'Destinations supported' },
  { value: '8K+', label: 'POIs synced from OpenStreetMap' },
  { value: 'Instant', label: 'Word exports ready' },
]

const featureDetails = [
  {
    icon: '🗺️',
    title: 'Route map + distance + steps',
    description: 'High-level overview with precise distances, travel steps and optional breaks.',
  },
  {
    icon: '🚗',
    title: 'Transport options',
    description: 'Car, bike, pedestrian and extract bus demos so you can compare each mode.',
  },
  {
    icon: '🏨',
    title: 'Hotels + food + attractions',
    description: 'Curated places sourced from OSM to fill your itinerary with comfort stops.',
  },
  {
    icon: '🌤️',
    title: 'Weather + destination summary',
    description: 'Contextual snapshots to know what to pack and what to expect on arrival.',
  },
  {
    icon: '📄',
    title: 'Word export',
    description: 'Full journey document plus focused selection ready to share with partners.',
  },
]

const heroTip = 'Origin + destination → route + options + POIs → Word export.'

const processSteps = [
  { title: 'Define the journey', description: 'Share the places you care about and TripGen fills in the accurate route and distance.' },
  { title: 'Compare every mode', description: 'See car, bike, foot, and demo bus options side by side so you can select the pace that fits.' },
  { title: 'Pick POIs + assets', description: 'Hotels, food, attractions and weather sync to give you a full picture before you travel.' },
  { title: 'Export & share', description: 'Generate Word exports (full or final) and hand them straight to collaborators.' },
]

const experienceHighlights = [
  { title: 'Curated pace', detail: 'Auto-adjusted stopovers keep each leg realistic for the selected mode.' },
  { title: 'Data-backed confidence', detail: 'Weather, distance, and POI counts appear in one glance.' },
  { title: 'Share-ready', detail: 'Downloadable Word docs make it easy to present or archive plans.' },
]

export default function Home() {
  const nav = useNavigate()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const trip = await searchTrip({ origin, destination })
      nav(`/trip/${trip.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to build trip')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <section className="hero card">
        <div className="hero-chip">TripGen Studio</div>
        <div className="h1 hero-title">Plan unforgettable journeys in minutes</div>
        <p className="hero-subtitle">{heroTip}</p>
        <div className="hero-stats">
          {statFacts.map((fact) => (
            <div key={fact.label} className="hero-stat">
              <div className="hero-stat-value">{fact.value}</div>
              <div className="hero-stat-label">{fact.label}</div>
            </div>
          ))}
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-visual-ring" />
          <div className="hero-visual-ring hero-visual-ring--pulse" />
        </div>
      </section>

      <section className="panel-grid">
        <div className="card form-panel">
          <div className="h2">Build your itinerary</div>
          <p className="sub">Tell TripGen where you want to start and finish so we can present routes, transport and options.</p>

          <form onSubmit={onSubmit} className="form-grid">
            <div className="input-group">
              <label className="small">Origin</label>
              <input
                className="input"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g., Erode Bus Stand"
              />
            </div>
            <div className="input-group">
              <label className="small">Destination</label>
              <input
                className="input"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g., Valparai"
              />
            </div>

            {error && <div className="form-error">{error}</div>}

            <div className="form-actions">
              <button
                className="btn btn-primary"
                disabled={loading || origin.trim().length < 2 || destination.trim().length < 2}
              >
                {loading ? 'Building trip…' : 'Search'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setOrigin('Erode')
                  setDestination('Valparai')
                }}
              >
                Try a sample
              </button>
            </div>
          </form>
        </div>

        <div className="card features-panel">
          <div className="h2">What you unlock</div>
          <div className="features-list">
            {featureDetails.map((feature) => (
              <div key={feature.title} className="feature-item">
                <div className="feature-icon">{feature.icon}</div>
                <div>
                  <div className="feature-title">{feature.title}</div>
                  <div className="feature-description">{feature.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="process-panel">
        <div className="card process-card">
          <div className="panel-heading">
            <div className="h2">How TripGen feels</div>
            <p className="sub">Designed for modern planners who want speed plus polish.</p>
          </div>
          <div className="process-steps">
            {processSteps.map((step, index) => (
              <div key={step.title} className="process-step">
                <div className="process-step-number">{index + 1}</div>
                <div>
                  <div className="feature-title">{step.title}</div>
                  <div className="feature-description">{step.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card experience-card">
          <div className="h2">Designed for modern explorers</div>
          <div className="experience-grid">
            {experienceHighlights.map((item) => (
              <div key={item.title} className="experience-item">
                <div className="experience-pill">⚡</div>
                <div>
                  <div className="feature-title">{item.title}</div>
                  <div className="feature-description">{item.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="footer-panel">
        <div className="card footer-card">
          <div>
            <div className="footer-text">
              DESIGN AND DEVELOPED BY <a className="footer-link" href="https://pvs-apps.in" target="_blank" rel="noreferrer">PVS</a>
            </div>
            <div className="small">Tip: Use clear place names (e.g., “Erode Bus Stand”, “Valparai”).</div>
          </div>
        </div>
      </section>
    </div>
  )
}
