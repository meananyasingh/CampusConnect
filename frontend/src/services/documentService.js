import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

async function download(path, filename) {
  const response = await api.get(path, { responseType: 'blob' })
  const objectUrl = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(objectUrl)
}

export const documentService = {
  listStudent: async () => unpack(await api.get('/documents/student/')),
  getSummary: async () => (await api.get('/documents/student/summary/')).data,
  upload: async (formData) => (await api.post('/documents/student/', formData)).data,
  remove: async (id) => api.delete(`/documents/student/${id}/`),
  downloadStudent: (document) => download(`/documents/student/${document.id}/download/`, document.original_filename),
  listAdmin: async (params = {}) => unpack(await api.get('/documents/admin/', { params })),
  review: async (id, values) => (await api.patch(`/documents/admin/${id}/`, values)).data,
  downloadAdmin: (document) => download(`/documents/admin/${document.id}/download/`, document.original_filename),
}
