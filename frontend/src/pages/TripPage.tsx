import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { exportAll, exportFinal, getTrip, selectTrip, Trip, TransportOption, POI, TripPlan } from '../lib/api'
import TripMap from '../components/TripMap'

type Tab = 'transport' | 'plans' | 'hotels' | 'food' | 'route' | 'extras'

export default function TripPage() {
  const { id } = useParams()
  const tripId = Number(id)
  const [trip, setTrip] = useState<Trip | null>(null)
  const [tab, setTab] = useState<Tab>('transport')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selectedTransport, setSelectedTransport] = useState<number | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null)

  const [exportAllUrl, setExportAllUrl] = useState<string | null>(null)
  const [exportFinalUrl, setExportFinalUrl] = useState<string | null>(null)

  useEffect(() => {
    let ok = true
    ;(async () => {
      setLoading(true); setError(null)
      try {
        const t = await getTrip(tripId)
        if (!ok) return
        setTrip(t)
        const bus = t.transport_options.find(x => x.mode === 'bus')?.id
        setSelectedTransport(bus || t.transport_options[0]?.id || null)
        setSelectedPlan(t.plans[0]?.id || null)
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load trip')
      } finally {
        setLoading(false)
      }
    })()
    return () => { ok = false }
  }, [tripId])

  const hotels = useMemo(() => (trip?.pois || []).filter(p => p.kind === 'hotel'), [trip])
  const food = useMemo(() => (trip?.pois || []).filter(p => p.kind === 'food'), [trip])
  const attractions = useMemo(() => (trip?.pois || []).filter(p => p.kind === 'attraction'), [trip])

  async function saveSelection() {
    if (!selectedTransport || !selectedPlan) return
    setError(null)
    try {
      await selectTrip(tripId, selectedTransport, selectedPlan)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save selection')
    }
  }
  async function doExportAll() {
    setError(null)
    try {
      const r = await exportAll(tripId)
      setExportAllUrl(r.download_url)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Export failed')
    }
  }
  async function doExportFinal() {
    setError(null)
    try {
      const r = await exportFinal(tripId)
      setExportFinalUrl(r.download_url)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Export failed (select first)')
    }
  }

  if (loading) return <div className="card" style={{padding: 18}}>Loading…</div>
  if (error) return <div className="card" style={{padding: 18, color:'#b91c1c', fontWeight: 800}}>{error}</div>
  if (!trip) return null

  const distanceKm = trip.route ? (trip.route.distance_m / 1000).toFixed(1) : '-'
  const durationMin = trip.route ? Math.round(trip.route.duration_s / 60) : '-'

  return (
    <div className="trip-page">
      <section className="trip-hero card">
        <div className="trip-hero-content">
          <div>
            <div className="h1 hero-title" style={{ fontSize: 24 }}>Trip #{trip.id}</div>
            <div className="sub">{trip.origin_display} → {trip.destination_display}</div>
            <div className="trip-hero-stats">
              <div className="stat-pill">{distanceKm} km • {durationMin} min</div>
              <div className="stat-pill">{trip.transport_options.length} transport options</div>
              <div className="stat-pill">{hotels.length} hotels</div>
            </div>
            {trip.destination_summary?.page && (
              <a className="hero-link" href={trip.destination_summary.page} target="_blank" rel="noreferrer">
                Explore destination guide →
              </a>
            )}
          </div>
          <div className="trip-hero-meta">
            <div className="hero-badge">Instant Word export</div>
            <div className="hero-badge hero-badge--alt">Smart POIs</div>
          </div>
        </div>
        <div className="trip-actions">
          <button className="btn btn-secondary" onClick={saveSelection} disabled={!selectedTransport || !selectedPlan}>Save selection</button>
          <button className="btn btn-primary" onClick={doExportAll}>Export all (Word)</button>
          <button className="btn btn-primary" onClick={doExportFinal}>Export final (Word)</button>
        </div>
        {(exportAllUrl || exportFinalUrl) && (
          <div className="trip-downloads">
            {exportAllUrl && <a href={exportAllUrl} target="_blank" rel="noreferrer">Download all plan doc</a>}
            {exportFinalUrl && <a href={exportFinalUrl} target="_blank" rel="noreferrer">Download final itinerary</a>}
          </div>
        )}
      </section>

      <section className="trip-layout">
        <div className="card map-card">
          <TripMap
            origin={{ lat: trip.origin_lat, lng: trip.origin_lng, label: trip.origin_display }}
            dest={{ lat: trip.dest_lat, lng: trip.dest_lng, label: trip.destination_display }}
            line={trip.route?.geometry_geojson || null}
          />
        </div>

        <div className="card detail-card">
          <div className="detail-heading">
            <div className="h2">Quick picks</div>
            <div className="small">Hotels: {hotels.length} • Food: {food.length} • Attractions: {attractions.length}</div>
          </div>
          {trip.destination_summary?.extract && (
            <div className="detail-summary">
              {trip.destination_summary.extract}
            </div>
          )}
          {trip.weather?.daily?.time && (
            <div className="weather-card">
              <div className="detail-heading">
                <div className="h2">Weather snapshot</div>
                <div className="small">{trip.weather.timezone}</div>
              </div>
              <div className="weather-grid">
                {(trip.weather.daily.time as string[]).slice(0, 3).map((d, i) => (
                  <div key={d} className="weather-day">
                    <span className="weather-date">{d}</span>
                    <span className="weather-temp small">{trip.weather.daily.temperature_2m_min?.[i]}° – {trip.weather.daily.temperature_2m_max?.[i]}°</span>
                    <span className="weather-precip small">Rain {trip.weather.daily.precipitation_sum?.[i]}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="tab-card card">
        <div className="tabs">
          <button className={tab === 'transport' ? 'tab active' : 'tab'} onClick={() => setTab('transport')}>Transport</button>
          <button className={tab === 'plans' ? 'tab active' : 'tab'} onClick={() => setTab('plans')}>Trip Plans</button>
          <button className={tab === 'hotels' ? 'tab active' : 'tab'} onClick={() => setTab('hotels')}>Hotels</button>
          <button className={tab === 'food' ? 'tab active' : 'tab'} onClick={() => setTab('food')}>Food</button>
          <button className={tab === 'route' ? 'tab active' : 'tab'} onClick={() => setTab('route')}>Route Steps</button>
          <button className={tab === 'extras' ? 'tab active' : 'tab'} onClick={() => setTab('extras')}>Attractions</button>
        </div>

        <div className="tab-content">
          {tab === 'transport' && <TransportTab options={trip.transport_options} selected={selectedTransport} onSelect={setSelectedTransport} />}
          {tab === 'plans' && <PlansTab plans={trip.plans} selected={selectedPlan} onSelect={setSelectedPlan} />}
          {tab === 'hotels' && <POITab title="Hotels" items={hotels} />}
          {tab === 'food' && <POITab title="Food" items={food} />}
          {tab === 'extras' && <POITab title="Attractions" items={attractions} />}
          {tab === 'route' && <RouteTab steps={trip.route?.steps || []} />}
        </div>
      </section>

      <section className="footer-panel trip-footer">
        <div className="card footer-card">
          <div className="footer-text">
            DESIGN AND DEVELOPED BY <a className="footer-link" href="https://pvs-apps.in" target="_blank" rel="noreferrer">PVS</a>
          </div>
        </div>
      </section>
    </div>
  )
}

function TransportTab({ options, selected, onSelect }:{
  options: TransportOption[]; selected: number | null; onSelect: (id:number)=>void
}) {
  return (
    <div>
      <div className="small" style={{marginBottom: 8}}>Choose a preferred bus (or any mode). Then choose a plan.</div>
      <table className="table">
        <thead><tr><th>Select</th><th>Mode</th><th>Title</th><th>Time</th><th>Price (INR)</th><th>Stops</th><th>Book</th></tr></thead>
        <tbody>
          {options.map(o => (
            <tr key={o.id}>
              <td><input type="radio" name="transport" checked={selected===o.id} onChange={()=>onSelect(o.id)} /></td>
              <td style={{fontWeight: 800}}>{o.mode}</td>
              <td>{o.title}<div className="small">{o.operator || ''}</div></td>
              <td className="small">
                {o.departure_iso && <div>Dep: {o.departure_iso}</div>}
                {o.arrival_iso && <div>Arr: {o.arrival_iso}</div>}
                {o.duration_s && <div>Dur: {Math.round(o.duration_s/60)} min</div>}
              </td>
              <td>{o.price_inr ?? '-'}</td>
              <td>{o.stops ?? '-'}</td>
              <td>
                <div style={{display:'flex', gap: 6, flexWrap:'wrap'}}>
                  {o.booking_url && (
                    <a className="btn btn-primary" href={o.booking_url} target="_blank" rel="noreferrer">Book</a>
                  )}
                  {(o.booking_links || []).map(link => (
                    <a key={link.provider} className="btn btn-secondary" href={link.url} target="_blank" rel="noreferrer">
                      {link.label || link.provider}
                    </a>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PlansTab({ plans, selected, onSelect }:{
  plans: TripPlan[]; selected: number | null; onSelect: (id:number)=>void
}) {
  return (
    <div className="grid" style={{gap: 12}}>
      <div className="small">Pick a plan (Cheapest / Fastest / Balanced / Comfort).</div>
      {plans.map(p => (
        <div key={p.id} className="card" style={{padding: 14, borderRadius: 14}}>
          <div style={{display:'flex', justifyContent:'space-between', gap: 10, flexWrap:'wrap'}}>
            <div>
              <div style={{fontWeight: 900}}>{p.name} <span className="small">score {p.score.toFixed(2)}</span></div>
              <div className="small" style={{marginTop: 6}}>{p.summary}</div>
            </div>
            <button className={selected===p.id?'btn btn-primary':'btn btn-secondary'} onClick={()=>onSelect(p.id)}>
              {selected===p.id?'Selected':'Select plan'}
            </button>
          </div>
          {p.timeline?.length ? (
            <div style={{marginTop: 10}}>
              <div className="small" style={{fontWeight: 800}}>Timeline</div>
              <ul className="small" style={{lineHeight: 1.7, marginTop: 6}}>
                {p.timeline.slice(0,6).map((t, idx) => <li key={idx}><b>{t.t}</b>: {t.note}</li>)}
              </ul>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  )
}

function POITab({ title, items }:{ title: string; items: POI[] }) {
  return (
    <div>
      <div style={{fontWeight: 900, marginBottom: 10}}>{title}</div>
      <table className="table">
        <thead><tr><th>Name</th><th>Address</th><th>Tags</th><th>Map</th></tr></thead>
        <tbody>
          {items.slice(0,30).map(p => (
            <tr key={p.id}>
              <td style={{fontWeight: 900}}>{p.name}</td>
              <td className="small">{p.address || '-'}</td>
              <td className="small">{(p.tags || []).slice(0,4).join(', ')}</td>
              <td className="small"><a target="_blank" rel="noreferrer" href={`https://www.openstreetmap.org/?mlat=${p.lat}&mlon=${p.lng}#map=16/${p.lat}/${p.lng}`}>open</a></td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <div className="small">No results (provider may have rate-limited).</div>}
    </div>
  )
}

function RouteTab({ steps }:{ steps: Array<Record<string, any>> }) {
  return (
    <div>
      <div style={{fontWeight: 900, marginBottom: 10}}>Route steps</div>
      <table className="table">
        <thead><tr><th>#</th><th>Instruction</th><th>Distance</th><th>Duration</th></tr></thead>
        <tbody>
          {steps.slice(0,120).map((s, idx) => (
            <tr key={idx}>
              <td className="small">{idx+1}</td>
              <td>{s.instruction || s.type || '-'}</td>
              <td className="small">{s.distance ? `${Math.round(s.distance)} m` : '-'}</td>
              <td className="small">{s.duration ? `${Math.round(s.duration)} s` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
