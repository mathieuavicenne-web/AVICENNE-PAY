<template>
  <div style="min-height: 100vh; background-color: #f8f9fa; padding: 2rem;">
    <div class="container">
      
      <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 class="hospital-title mb-1">Mon Tableau de Bord</h1>
          <div class="d-flex align-items-center gap-2">
            <p class="text-muted mb-0">
              Bienvenue sur l'interface Avicenne Pay, 
              <strong v-if="userProfile" class="text-dark">{{ userProfile.prenom }} {{ userProfile.nom }}</strong>
            </p>
            <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">Profil Actif</span>
            <span class="badge bg-light text-secondary border px-2 py-1">Accès : Aujourd'hui</span>
          </div>
        </div>
      </div>

      <hr class="mb-4 opacity-10">

      <div class="row g-4">
        
        <div v-if="userProfile?.role === 'admin'" class="col-md-4">
          <div class="card card-action border-0 shadow-sm h-100" @click="goToUsers">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon bg-hospital-blue-subtle text-hospital-blue mb-3">
                  <i class="bi bi-people-fill fs-4"></i>
                </div>
                <h5 class="fw-bold text-dark mb-2">Gestion Utilisateurs</h5>
                <p class="text-muted small">Pilotez les accès, ajoutez de nouveaux membres et gérez les rôles de l'équipe.</p>
              </div>
              <div class="text-end mt-3">
                <span class="text-hospital-blue fw-bold small">Y aller <i class="bi bi-arrow-right ms-1"></i></span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card card-action border-0 shadow-sm h-100" @click="goToDeclarations">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon bg-hospital-blue-subtle text-hospital-blue mb-3">
                  <i class="bi bi-file-earmark-medical-fill fs-4"></i>
                </div>
                <h5 class="fw-bold text-dark mb-2">Déclarations</h5>
                <p class="text-muted small">Consultez l'historique, téléchargez les documents et suivez l'état des déclarations.</p>
              </div>
              <div class="text-end mt-3">
                <span class="text-hospital-blue fw-bold small">Y aller <i class="bi bi-arrow-right ms-1"></i></span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card border-0 shadow-sm h-100" style="border-radius: 1rem;">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon bg-hospital-blue-subtle text-hospital-blue mb-3">
                  <i class="bi bi-folder-fill fs-4"></i>
                </div>
                <h5 class="fw-bold text-dark mb-2">Catalogues</h5>
                <p class="text-muted small">Accédez rapidement aux missions et grilles tarifaires des catalogues.</p>
              </div>
              
              <div class="mt-3">
                <div v-if="userProfile?.role === 'admin'" class="d-flex flex-column gap-2">
                  <button @click="goToCcda" class="btn btn-sm btn-outline-hospital-blue w-100 text-start d-flex justify-content-between align-items-center">
                    <span>Catalogue CCDA</span>
                    <i class="bi bi-arrow-right"></i>
                  </button>
                  <button @click="goToCcdu" class="btn btn-sm btn-outline-hospital-blue w-100 text-start d-flex justify-content-between align-items-center">
                    <span>Catalogue CCDU</span>
                    <i class="bi bi-arrow-right"></i>
                  </button>
                </div>

                <div v-else class="text-end">
                  <span @click="goToCcda" class="text-hospital-blue fw-bold small" style="cursor: pointer;">
                    Y aller <i class="bi bi-arrow-right ms-1"></i>
                  </span>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div> </div> </div> </template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/api'

const router = useRouter()
const userProfile = ref(null)

// 🧭 Toutes tes fonctions de navigation regroupées ici
const goToUsers = () => router.push('/utilisateurs')
const goToDeclarations = () => router.push('/declarations')
const goToCcda = () => router.push('/missions/ccda')
const goToCcdu = () => router.push('/missions/cddu')

onMounted(async () => {
  try {
    const data = await authService.getUserProfile()
    userProfile.value = data
    console.log("Profil chargé :", data)
  } catch (error) {
    console.error("Impossible de récupérer le profil :", error)
  }
})
</script>

<style scoped>
/* 🎨 Uniformisation des bleus */
.text-hospital-blue {
  color: #3498db !important;
}
.bg-hospital-blue-subtle {
  background-color: rgba(52, 152, 219, 0.1) !important;
}

.hospital-title {
  color: #2c3e50;
  font-weight: 700;
}

/* 🖱️ Style des cartes "Boutons" */
.card-action {
  border-radius: 1rem !important;
  transition: all 0.2s ease-in-out;
  cursor: pointer;
}

.card-action:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.05) !important;
  background-color: #ffffff;
}

/* Rond de couleur derrière les icônes */
.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Customisation des badges plus fins */
.badge {
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
}

/* Boutons catalogues */
.btn-outline-hospital-blue {
  color: #3498db;
  border-color: #3498db;
  font-weight: 600;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}
.btn-outline-hospital-blue:hover {
  background-color: #3498db;
  color: #ffffff;
}
</style>