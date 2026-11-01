import api from './api.js'

export const companyService = {
  getRecruiterProfile: async () => {
    const response = await api.get('/companies/recruiter/profile/')
    return response.data
  },
  updateRecruiterProfile: async (values) => {
    const response = await api.patch('/companies/recruiter/profile/', values)
    return response.data
  },
  updateCompany: async (values) => {
    const response = await api.patch('/companies/recruiter/company/', values)
    return response.data
  },
  requestCollegeAccess: async (collegeId) => {
    const response = await api.post('/companies/recruiter/partnerships/', { college_id: collegeId })
    return response.data
  },
  cancelCollegeRequest: async (id) => {
    await api.delete(`/companies/recruiter/partnerships/${id}/`)
  },
  listPartnerships: async (status = '') => {
    const response = await api.get('/companies/admin/partnerships/', { params: status ? { status } : {} })
    return response.data.results ?? response.data
  },
  reviewPartnership: async (id, values) => {
    const response = await api.patch(`/companies/admin/partnerships/${id}/`, values)
    return response.data
  },
}
