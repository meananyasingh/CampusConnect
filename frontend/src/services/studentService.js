import api from './api.js'

const portfolioPaths = {
  skills: 'skills',
  projects: 'projects',
  certifications: 'certifications',
  experiences: 'experiences',
}

const unpackList = (response) => response.data.results ?? response.data

export const studentService = {
  getProfile: async () => {
    const response = await api.get('/students/profile/')
    return response.data
  },
  updateProfile: async (formData) => {
    const response = await api.patch('/students/profile/', formData)
    return response.data
  },
  getPortfolio: async () => {
    const [skills, projects, certifications, experiences] = await Promise.all(
      Object.values(portfolioPaths).map((path) => api.get(`/students/portfolio/${path}/`)),
    )
    return {
      skills: unpackList(skills),
      projects: unpackList(projects),
      certifications: unpackList(certifications),
      experiences: unpackList(experiences),
    }
  },
  createPortfolioItem: async (type, values) => {
    const response = await api.post(`/students/portfolio/${portfolioPaths[type]}/`, values)
    return response.data
  },
  updatePortfolioItem: async (type, id, values) => {
    const response = await api.patch(`/students/portfolio/${portfolioPaths[type]}/${id}/`, values)
    return response.data
  },
  deletePortfolioItem: async (type, id) => {
    await api.delete(`/students/portfolio/${portfolioPaths[type]}/${id}/`)
  },
  getResumes: async () => {
    const response = await api.get('/students/resumes/')
    return unpackList(response)
  },
  uploadResume: async (formData) => {
    const response = await api.post('/students/resumes/', formData)
    return response.data
  },
  updateResume: async (id, values) => {
    const response = await api.patch(`/students/resumes/${id}/`, values)
    return response.data
  },
  deleteResume: async (id) => {
    await api.delete(`/students/resumes/${id}/`)
  },
  getProfileCompletion: async () => {
    const response = await api.get('/students/profile-completion/')
    return response.data
  },
  listImports: async () => {
    const response = await api.get('/students/admin/imports/')
    return unpackList(response)
  },
  previewImport: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/students/admin/imports/', formData)
    return response.data
  },
  confirmImport: async (id) => {
    const response = await api.post(`/students/admin/imports/${id}/confirm/`)
    return response.data
  },
  downloadImportTemplate: async () => {
    const response = await api.get('/students/admin/imports/template/', { responseType: 'blob' })
    const objectUrl = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = 'campusconnect-student-import.csv'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
  },
}
