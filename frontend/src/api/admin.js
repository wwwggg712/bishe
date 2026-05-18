import http from './http'

export async function fetchSystemOverview() {
  const response = await http.get('/api/admin/overview')
  return response.data
}

export async function fetchJobs() {
  const response = await http.get('/api/admin/jobs')
  return response.data
}

export async function fetchSimulationTasks() {
  const response = await http.get('/api/simulation/tasks')
  return response.data
}

export async function fetchAdminUsers() {
  const response = await http.get('/api/admin/users')
  return response.data
}

export async function fetchAdminLogPreview(params = {}) {
  const response = await http.get('/api/admin/logs/preview', { params })
  return response.data
}

export async function fetchAdminLogMetrics(params = {}) {
  const response = await http.get('/api/admin/logs/metrics', { params })
  return response.data
}

export async function fetchAdminAlgorithmPipeline() {
  const response = await http.get('/api/admin/algorithm-pipeline')
  return response.data
}

export async function runJob(jobName) {
  const response = await http.post('/api/admin/jobs/run', { job_name: jobName })
  return response.data
}

export async function fetchPredictionAnomalies(params = {}) {
  const response = await http.get('/api/prediction/anomalies', { params })
  return response.data
}

export async function cleanupAdminLogs(keepLast) {
  const response = await http.post('/api/admin/logs/cleanup', { keep_last: keepLast })
  return response.data
}
