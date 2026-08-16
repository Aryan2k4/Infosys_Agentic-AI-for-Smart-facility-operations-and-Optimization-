import api from './energyService'

export const securityService = {
  getBuilding: (buildingId = 'BLD-HQ-01') =>
    api.get('/security/building', { params: { building_id: buildingId } }).then(r => r.data),

  getAccessPoints: (buildingId = 'BLD-HQ-01') =>
    api.get('/security/access-points', { params: { building_id: buildingId } }).then(r => r.data),

  getEvents: (limit = 200) =>
    api.get('/security/events', { params: { limit } }).then(r => r.data),

  getAlerts: (buildingId = 'BLD-HQ-01', status = null) =>
    api.get('/security/alerts', { params: { building_id: buildingId, ...(status ? { status } : {}) } }).then(r => r.data),

  getInvestigation: (buildingId = 'BLD-HQ-01') =>
    api.get('/security/investigate', { params: { building_id: buildingId } }).then(r => r.data),

  ingest: () => api.post('/security/ingest').then(r => r.data),
}

export default securityService
