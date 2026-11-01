import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

export const applicationService = {
  listStudent: async (params = {}) => {
    const response = await api.get('/applications/student/', { params })
    return unpack(response)
  },
  apply: async (values) => {
    const response = await api.post('/applications/student/', values)
    return response.data
  },
  withdraw: async (id) => {
    const response = await api.post(`/applications/student/${id}/withdraw/`)
    return response.data
  },
  listRecruiter: async (params = {}) => {
    const response = await api.get('/applications/recruiter/', { params })
    return unpack(response)
  },
  updateStatus: async (id, values) => {
    const response = await api.patch(`/applications/recruiter/${id}/`, values)
    return response.data
  },
  listRounds: async (params = {}) => {
    const response = await api.get('/applications/recruiter/rounds/', { params })
    return unpack(response)
  },
  createRound: async (values) => {
    const response = await api.post('/applications/recruiter/rounds/', values)
    return response.data
  },
  listRecruiterInterviews: async (params = {}) => {
    const response = await api.get('/applications/recruiter/interviews/', { params })
    return unpack(response)
  },
  scheduleInterview: async (values) => {
    const response = await api.post('/applications/recruiter/interviews/', values)
    return response.data
  },
  updateInterview: async (id, values) => {
    const response = await api.patch(`/applications/recruiter/interviews/${id}/`, values)
    return response.data
  },
  listStudentInterviews: async (params = {}) => {
    const response = await api.get('/applications/student/interviews/', { params })
    return unpack(response)
  },
}
