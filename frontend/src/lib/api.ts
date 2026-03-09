import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000,
})

export type TripSearchRequest = { origin: string; destination: string }

export type TransportOption = {
  id: number
  mode: string
  operator?: string | null
  title: string
  departure_iso?: string | null
  arrival_iso?: string | null
  duration_s?: number | null
  distance_m?: number | null
  price_inr?: number | null
  stops?: number | null
  booking_url?: string | null
  booking_links?: Array<{ provider: string; label: string; url: string }>
}

export type POI = {
  id: number
  kind: 'hotel' | 'food' | 'attraction'
  name: string
  lat: number
  lng: number
  address?: string | null
  rating?: number | null
  price_level?: string | null
  tags: string[]
}

export type TripPlan = {
  id: number
  name: string
  score: number
  transport_option_id?: number | null
  hotel_poi_id?: number | null
  food_poi_id?: number | null
  summary: string
  costs: Record<string, any>
  timeline: Array<Record<string, any>>
}

export type Trip = {
  id: number
  origin_text: string
  destination_text: string
  origin_lat: number
  origin_lng: number
  dest_lat: number
  dest_lng: number
  origin_display: string
  destination_display: string
  route?: {
    distance_m: number
    duration_s: number
    geometry_geojson: any
    steps: Array<Record<string, any>>
  } | null
  transport_options: TransportOption[]
  pois: POI[]
  plans: TripPlan[]
  weather?: any
  destination_summary?: any
}

export async function searchTrip(payload: TripSearchRequest): Promise<Trip> {
  const res = await api.post('/api/trips/search', payload)
  return res.data
}
export async function getTrip(id: number): Promise<Trip> {
  const res = await api.get(`/api/trips/${id}`)
  return res.data
}
export async function selectTrip(id: number, selected_transport_option_id: number, selected_plan_id: number) {
  const res = await api.post(`/api/trips/${id}/select`, { selected_transport_option_id, selected_plan_id })
  return res.data
}
export async function exportAll(id: number) {
  const res = await api.get(`/api/trips/${id}/export/all`)
  return res.data as { ok: boolean; filename: string; download_url: string }
}
export async function exportFinal(id: number) {
  const res = await api.get(`/api/trips/${id}/export/final`)
  return res.data as { ok: boolean; filename: string; download_url: string }
}
