import api from './api.js'

const unpack = (response) => response.data.results ?? response.data

export const announcementService = {
  listAdmin: async () => unpack(await api.get('/announcements/admin/')),
  createAdmin: async (values) => (await api.post('/announcements/admin/', values)).data,
  updateAdmin: async (id, values) => (await api.patch(`/announcements/admin/${id}/`, values)).data,
  deleteAdmin: async (id) => api.delete(`/announcements/admin/${id}/`),
  review: async (id, values) => (await api.post(`/announcements/admin/${id}/review/`, values)).data,
  listRecruiter: async () => unpack(await api.get('/announcements/recruiter/')),
  createRecruiter: async (values) => (await api.post('/announcements/recruiter/', values)).data,
  updateRecruiter: async (id, values) => (await api.patch(`/announcements/recruiter/${id}/`, values)).data,
  deleteRecruiter: async (id) => api.delete(`/announcements/recruiter/${id}/`),
  listStudent: async () => unpack(await api.get('/announcements/student/')),
  markRead: async (id) => (await api.post(`/announcements/student/${id}/read/`)).data,
}
