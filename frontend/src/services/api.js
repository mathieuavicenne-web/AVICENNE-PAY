import axios from 'axios'

// 1. On crée l'instance Axios configurée
const api = axios.create({
  baseURL: 'http://localhost:8000', 
  headers: {
    'Content-Type': 'application/json'
  }
})

// 2. INTERCEPTEUR : Injection automatique du Token JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 3. INTERCEPTEUR : Gestion globale des erreurs (ex: Token expiré)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Session expirée ou non autorisée. Déconnexion...")
      localStorage.removeItem('token')
      // Tu pourras ajouter ici une redirection vers le login si tu utilises Vue Router
    }
    return Promise.reject(error)
  }
)

// 4. Fonctions d'authentification
export const authService = {
  async login(email, password) {
    console.log("Tentative d'envoi des identifiants...")
    
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)

    try {
      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      
      console.log("Réponse du serveur reçue !", response.data)

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)
      }
      
      return response.data
    } catch (error) {
      console.error("Détails de l'erreur API :", error.response ? error.response.data : error.message)
      throw error
    }
  },

  async getUserProfile() {
    try {
      const response = await api.get('/users/me')
      return response.data
    } catch (error) {
      console.error("Erreur lors de la récupération du profil :", error)
      throw error
    }
  },

  async updateUserProfile(profileData) {
    try {
      const response = await api.patch('/users/me', profileData)
      return response.data
    } catch (error) {
      console.error("Erreur lors de la mise à jour du profil :", error)
      if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail)
      }
      throw new Error("Impossible de mettre à jour le profil.")
    }
  },

  logout() {
    localStorage.removeItem('token')
  }
}

// 5. Fonctions de gestion des utilisateurs
export const userService = {
  async getReferentiels() {
    try {
      const response = await api.get('/users/constants/referentiels')
      return response.data
    } catch (error) {
      console.error("Impossible de récupérer les référentiels :", error)
      throw error
    }
  },
  
  async getAllUsers() {
    try {
      const response = await api.get('/users/')
      return response.data
    } catch (error) {
      console.error("Impossible de récupérer la liste des utilisateurs :", error)
      throw error
    }
  },

  async createUser(userData) {
    try {
      const response = await api.post('/users/', userData)
      return response.data
    } catch (error) {
      if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail)
      }
      throw new Error("Erreur lors de la création de l'utilisateur")
    }
  },

  async toggleUserStatus(userId) {
    try {
      const response = await api.patch(`/users/${userId}/toggle`, {})
      return response.data
    } catch (error) {
      console.error("Erreur lors de la modification du statut :", error)
      throw error
    }
  },

  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/users/${userId}`, userData)
      return response.data
    } catch (error) {
      console.error("Erreur lors de la mise à jour de l'utilisateur :", error)
      if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail)
      }
      throw new Error("Impossible de mettre à jour l'utilisateur.")
    }
  }
}

export const getReferentiels = userService.getReferentiels
export default api