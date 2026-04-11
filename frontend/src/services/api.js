import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Session expirée ou non autorisée. Déconnexion...")
      localStorage.removeItem('token')
    }
    return Promise.reject(error)
  }
)

export const authService = {
  async login(email, password) {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)

    try {
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)
      }
      return response.data
    } catch (err) {
      console.error("Détails de l'erreur API :", err.response ? err.response.data : err.message)
      throw err
    }
  },

  async getUserProfile() {
    try {
      const response = await api.get('/users/me')
      return response.data
    } catch (error) {
      throw error
    }
  },

  async updateUserProfile(profileData) {
    try {
      const response = await api.patch('/users/me', profileData)
      return response.data
    } catch (err) {
      if (err.response?.data?.detail) throw new Error(err.response.data.detail)
      throw new Error("Impossible de mettre à jour le profil.")
    }
  },

  logout() {
    localStorage.removeItem('token')
  }
}

export const userService = {
  async getReferentiels() {
    const response = await api.get('/users/constants/referentiels')
    return response.data
  },
  
  async getAllUsers() {
    const response = await api.get('/users/')
    return response.data
  },

  async createUser(userData) {
    try {
      const response = await api.post('/users/', userData)
      return response.data
    } catch (err) {
      if (err.response?.data?.detail) throw new Error(err.response.data.detail)
      throw new Error("Erreur création")
    }
  },

  async toggleUserStatus(userId) {
    const response = await api.patch(`/users/${userId}/toggle`, {})
    return response.data
  },

  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/users/${userId}`, userData)
      return response.data
    } catch (err) {
      if (err.response?.data?.detail) throw new Error(err.response.data.detail)
      throw new Error("Erreur mise à jour")
    }
  }
}

export const missionService = {
  async getAllMissions() {
    const response = await api.get('/missions/')
    return response.data
  },

  async createMission(missionData) {
    const response = await api.post('/missions/', missionData)
    return response.data
  },

  async updateMission(missionId, missionData) {
    const response = await api.put(`/missions/${missionId}`, missionData)
    return response.data
  },

  async deleteMission(missionId) {
    const response = await api.delete(`/missions/${missionId}`)
    return response.data
  },

  async deleteMissionDefinitive(missionId) {
    const response = await api.delete(`/missions/${missionId}/definitive`)
    return response.data
  }
}

export const declarationService = {
  async getAllDeclarations() {
    const response = await api.get('/declarations/')
    return response.data
  },

  async createDeclaration(declarationData) {
    const response = await api.post('/declarations/', declarationData)
    return response.data
  },

  async updateDeclaration(id, declarationData) {
    const response = await api.put(`/declarations/${id}`, declarationData)
    return response.data
  },

  async soumettreDeclaration(id) {
    const response = await api.post(`/declarations/${id}/soumettre`)
    return response.data
  },

  async reviewDeclaration(id, reviewData) {
    const response = await api.post(`/declarations/${id}/review`, reviewData)
    return response.data
  }
}

export const getReferentiels = userService.getReferentiels
export default api