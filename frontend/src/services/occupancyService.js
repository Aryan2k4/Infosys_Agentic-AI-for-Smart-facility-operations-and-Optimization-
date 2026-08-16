import api from './energyService'

export const occupancyService = {
  getBuilding: (buildingId = 'BLD-HQ-01') =>
    api.get('/occupancy/building', { params: { building_id: buildingId } }).then(r => r.data),

  getZones: (buildingId = 'BLD-HQ-01') =>
    api.get('/occupancy/zones', { params: { building_id: buildingId } }).then(r => r.data),

  getZoneDetail: (zoneId) =>
    api.get(`/occupancy/zones/${zoneId}`).then(r => r.data),

  getZoneHistory: (zoneId, limit = 300) =>
    api.get(`/occupancy/zones/${zoneId}/history`, { params: { limit } }).then(r => r.data),

  getAlerts: (buildingId = 'BLD-HQ-01') =>
    api.get('/occupancy/alerts', { params: { building_id: buildingId } }).then(r => r.data),

  getInvestigation: (buildingId = 'BLD-HQ-01') =>
    api.get('/occupancy/investigate', { params: { building_id: buildingId } }).then(r => r.data),

  ingest: () => api.post('/occupancy/ingest').then(r => r.data),
}

export default occupancyService
