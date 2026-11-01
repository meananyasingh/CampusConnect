import api from './api.js'

export const collegeService = {
  list: async () => {
    const response = await api.get('/colleges/')
    return response.data
  },
  listPrograms: async (collegeId) => {
    const response = await api.get('/colleges/programs/', {
      params: { college: collegeId },
    })
    return response.data
  },
}
