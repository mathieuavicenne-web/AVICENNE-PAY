import axios from 'axios'

// 1. On crée l'instance Axios configurée
const api = axios.create({
  baseURL: 'http://localhost:8000', 
  headers: {
    'Content-Type': 'application/json'
  }
})

// 2. Fonctions d'authentification
export const authService = {
  async login(email, password) {
    console.log("Tentative d'envoi des identifiants...");
    
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)

    try {
      const response = await api.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      console.log("Réponse du serveur reçue !", response.data);

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token)
      }
      
      return response.data
    } catch (error) {
      console.error("Détails de l'erreur API :", error.response ? error.response.data : error.message);
      throw error;
    }
  },

  async getUserProfile() {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.get('/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return response.data
    } catch (error) {
      console.error("Erreur lors de la récupération du profil :", error)
      throw error
    }
  },

  logout() {
    localStorage.removeItem('token')
  }
}

// 3. Fonctions de gestion des utilisateurs (Passée sous Axios !)
export const userService = {
  async getReferentiels() {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.get('/users/constants/referentiels', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.data
    } catch (error) {
      console.error("Impossible de récupérer les référentiels :", error)
      throw error
    }
  },
  
  async getAllUsers() {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.get('/users/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.data
    } catch (error) {
      console.error("Impossible de récupérer la liste des utilisateurs :", error)
      throw error
    }
  },

  // 👤 CREATION UTILISATEUR
  async createUser(userData) {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.post('/users/', userData, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.data
    } catch (error) {
      if (error.response && error.response.data && error.response.data.detail) {
        throw new Error(error.response.data.detail)
      }
      throw new Error("Erreur lors de la création de l'utilisateur")
    }
  },

  // 👤 RÉCUPÉRER LE PROFIL DE L'UTILISATEUR CONNECTÉ
  async getProfile() {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.get('/users/me', { // 👈 ou l'URL exacte de ton endpoint "me"
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.data
    } catch (error) {
      console.error("Impossible de récupérer le profil connecté :", error)
      throw error
    }
  },

  // 👤 BASCULER LE STATUT ACTIF/INACTIF
  async toggleUserStatus(userId) {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      const response = await api.patch(`/users/${userId}/toggle`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      return response.data
    } catch (error) {
      console.error("Erreur lors de la modification du statut :", error)
      throw error
    }
  },

  // 👤 MISE À JOUR DE L'UTILISATEUR
  async updateUser(userId, userData) {
    const token = localStorage.getItem('token')
    if (!token) throw new Error("Aucun token trouvé")

    try {
      // J'utilise PUT ici. Si ton backend FastAPI attend un PATCH, 
      // remplace simplement "api.put" par "api.patch" ci-dessous.
      const response = await api.put(`/users/${userId}`, userData, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
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

// On ajoute cet export spécifique tout en bas
export const getReferentiels = userService.getReferentiels

// 4. L'export par défaut bien rangé tout en bas 🧹
export default api