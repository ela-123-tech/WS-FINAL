import React from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'

const icon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

type Props = {
  origin: { lat: number; lng: number; label: string }
  dest: { lat: number; lng: number; label: string }
  line?: { type: string; coordinates: Array<[number, number]> } | null
}

export default function TripMap({ origin, dest, line }: Props) {
  const center = [(origin.lat + dest.lat) / 2, (origin.lng + dest.lng) / 2] as [number, number]
  const poly: [number, number][] = []
  if (line && Array.isArray(line.coordinates)) {
    for (const c of line.coordinates) poly.push([c[1], c[0]])
  }
  return (
    <MapContainer center={center} zoom={9} scrollWheelZoom style={{height: 420, width: '100%'}}>
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[origin.lat, origin.lng]} icon={icon}><Popup>{origin.label}</Popup></Marker>
      <Marker position={[dest.lat, dest.lng]} icon={icon}><Popup>{dest.label}</Popup></Marker>
      {poly.length > 0 && <Polyline positions={poly} />}
    </MapContainer>
  )
}
