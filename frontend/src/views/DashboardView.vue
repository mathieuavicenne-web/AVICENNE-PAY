<template>
  <div style="min-height: 100vh; background-color: #f8f9fa; padding: 2rem;">
    <div class="container">
      
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 style="color: var(--primary-dark); font-weight: 700;">Mon Tableau de Bord</h1>
          <p class="text-muted mb-0">
            Bienvenue sur l'interface Avicenne Pay, 
            <strong v-if="userProfile" class="text-dark">{{ userProfile.prenom }} {{ userProfile.nom }}</strong>
          </p>
        </div>
        <button @click="handleLogout" class="btn btn-outline-danger px-4" style="border-radius: 0.5rem;">
          Se déconnecter
        </button>
      </div>

      <hr class="mb-4">

      <div class="row g-4">
        <div class="col-md-4">
          <div class="card shadow-sm border-0 h-100" style="border-radius: 0.75rem;">
            <div class="card-body p-4">
              <h5 class="text-muted text-uppercase" style="font-size: 0.8rem; font-weight: 700;">Statut du profil</h5>
              <p class="h3 mb-0 text-success" style="font-weight: 700;">Actif</p>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card shadow-sm border-0 h-100" style="border-radius: 0.75rem;">
            <div class="card-body p-4">
              <h5 class="text-muted text-uppercase" style="font-size: 0.8rem; font-weight: 700;">Dernière connexion</h5>
              <p class="h3 mb-0" style="font-weight: 700; color: var(--primary-dark);">Aujourd'hui</p>
            </div>
          </div>
        </div>

        <div v-if="userProfile?.role === 'admin'" class="col-md-4">
          <div class="card shadow-sm border-0 h-100 bg-primary text-white" style="border-radius: 0.75rem; cursor: pointer;" @click="goToUsers">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <h5 class="text-uppercase" style="font-size: 0.8rem; font-weight: 700; opacity: 0.8;">Administration</h5>
                <p class="h4 mb-0 fw-bold">Gestion Utilisateurs</p>
              </div>
              <div class="text-end mt-2">
                <span class="btn btn-sm btn-light">Y aller →</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/api'

const router = useRouter()
const userProfile = ref(null)

onMounted(async () => {
  try {
    const data = await authService.getUserProfile()
    userProfile.value = data
    // 🔍 On s'assure dans la console que le nom remonte bien
    console.log("Profil chargé :", data)
  } catch (error) {
    console.error("Impossible de récupérer le profil :", error)
  }
})

const handleLogout = () => {
  authService.logout()
  router.push('/')
}

const goToUsers = () => {
  router.push('/utilisateurs') // ⚠️ Clique sur la carte bleue pour y aller !
}
</script>