import http from './http'

export async function startSimulationTask() {
  const response = await http.post('/api/simulation/start')
  return response.data
}

export async function stopSimulationTask() {
  const response = await http.post('/api/simulation/stop')
  return response.data
}

export async function generateSimulationOnce() {
  const response = await http.post('/api/simulation/generate-once')
  return response.data
}

export async function generateSimulationBulk() {
  const response = await http.post('/api/simulation/generate-bulk')
  return response.data
}
