import { useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import type { LatLngExpression } from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix leaflet marker icon issue
import L from 'leaflet'
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

interface Location {
  lat: number
  lng: number
}

interface MapViewProps {
  locations: Location[]
  pois: { name: string; category?: string }[]
  center?: Location
}

// Fit map to show all markers
function MapBounds({ locations }: { locations: Location[] }) {
  const map = useMap()
  
  useEffect(() => {
    if (locations.length > 0) {
      const bounds = locations.map(loc => [loc.lat, loc.lng] as LatLngExpression)
      map.fitBounds(bounds as any, { padding: [50, 50] })
    }
  }, [locations, map])
  
  return null
}

export default function MapView({ locations, pois, center }: MapViewProps) {
  const defaultCenter: Location = center || (locations[0] || { lat: 30.2741, lng: 120.1551 })
  
  // Filter valid locations
  const validLocations = locations.filter(loc => loc && typeof loc.lat === 'number' && typeof loc.lng === 'number')
  
  if (validLocations.length === 0) {
    return (
      <div className="map-container">
        <div className="map-placeholder">
          <p>No location data available</p>
        </div>
      </div>
    )
  }

  // Create route polyline
  const routePositions: LatLngExpression[] = validLocations.map(loc => [loc.lat, loc.lng])
  
  // Color for markers based on day
  const getMarkerColor = (index: number) => {
    const colors = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    return colors[index % colors.length]
  }

  return (
    <div className="map-container">
      <MapContainer
        center={[defaultCenter.lat, defaultCenter.lng]}
        zoom={13}
        style={{ height: '300px', width: '100%', borderRadius: '12px' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapBounds locations={validLocations} />
        
        {/* Route line */}
        {routePositions.length > 1 && (
          <Polyline
            positions={routePositions}
            pathOptions={{ color: '#0ea5e9', weight: 3, opacity: 0.7, dashArray: '10, 10' }}
          />
        )}
        
        {/* Markers */}
        {validLocations.map((loc, index) => (
          <Marker key={index} position={[loc.lat, loc.lng]}>
            <Popup>
              <div style={{ minWidth: '120px' }}>
                <strong style={{ color: getMarkerColor(index) }}>
                  {index + 1}. {pois[index]?.name || `Spot #${index + 1}`}
                </strong>
                {pois[index]?.category && (
                  <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#666' }}>
                    {pois[index].category}
                  </p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
