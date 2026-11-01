import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

export const opportunityService = {
  listRecruiter: async (params = {}) => {
    const response = await api.get('/opportunities/recruiter/', { params })
    return unpack(response)
  },
  getRecruiter: async (id) => {
    const response = await api.get(`/opportunities/recruiter/${id}/`)
    return response.data
  },
  create: async (values) => {
    const response = await api.post('/opportunities/recruiter/', values)
    return response.data
  },
  update: async (id, values) => {
    const response = await api.patch(`/opportunities/recruiter/${id}/`, values)
    return response.data
  },
  sendToColleges: async (id, values) => {
    const response = await api.post(`/opportunities/recruiter/${id}/colleges/`, values)
    return response.data
  },
  withdrawInvitation: async (id) => {
    await api.delete(`/opportunities/recruiter/invitations/${id}/`)
  },
  listCollegeInvitations: async (params = {}) => {
    const response = await api.get('/opportunities/admin/invitations/', { params })
    return unpack(response)
  },
  reviewCollegeInvitation: async (id, values) => {
    const response = await api.patch(`/opportunities/admin/invitations/${id}/`, values)
    return response.data
  },
  remove: async (id) => api.delete(`/opportunities/recruiter/${id}/`),
  listStudent: async (params = {}) => {
    const response = await api.get('/opportunities/student/', { params })
    return unpack(response)
  },
  listRecommended: async () => {
    const response = await api.get('/opportunities/student/recommended/')
    return unpack(response)
  },
  save: async (id) => {
    const response = await api.post(`/opportunities/student/${id}/save/`)
    return response.data
  },
  unsave: async (id) => {
    const response = await api.delete(`/opportunities/student/${id}/save/`)
    return response.data
  },
}
