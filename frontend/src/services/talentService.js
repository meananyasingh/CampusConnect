import api from './api.js'

export const talentService = {
  listCandidates: async (params = {}) => {
    const response = await api.get('/talent/recruiter/candidates/', { params })
    return response.data
  },
  getCandidate: async (id) => {
    const response = await api.get(`/talent/recruiter/candidates/${id}/`)
    return response.data
  },
  downloadResume: async (candidate) => {
    const response = await api.get(`/talent/recruiter/candidates/${candidate.id}/resume/`, {
      responseType: 'blob',
    })
    const objectUrl = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = candidate.primary_resume?.original_filename || 'resume.pdf'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
  },
  listPools: async () => {
    const response = await api.get('/talent/recruiter/pools/')
    return response.data
  },
  createPool: async (values) => {
    const response = await api.post('/talent/recruiter/pools/', values)
    return response.data
  },
  updatePool: async (id, values) => {
    const response = await api.patch(`/talent/recruiter/pools/${id}/`, values)
    return response.data
  },
  deletePool: async (id) => {
    await api.delete(`/talent/recruiter/pools/${id}/`)
  },
  addMember: async (poolId, values) => {
    const response = await api.post(`/talent/recruiter/pools/${poolId}/members/`, values)
    return response.data
  },
  updateMember: async (poolId, memberId, values) => {
    const response = await api.patch(`/talent/recruiter/pools/${poolId}/members/${memberId}/`, values)
    return response.data
  },
  removeMember: async (poolId, memberId) => {
    await api.delete(`/talent/recruiter/pools/${poolId}/members/${memberId}/`)
  },
}
