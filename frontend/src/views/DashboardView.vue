<template>
  <div class="p-6">
    <div class="container-fluid p-0">
      
      <div class="d-flex justify-content-between align-items-center" style="margin-bottom: 5rem;">
        <div>
          <h1 class="h1-avicenne m-0">Mon Tableau de Bord</h1>
          <div class="d-flex align-items-center gap-2 mt-1">
            <p class="text-muted small mb-0">
              Bienvenue sur l'interface Avicenne Pay, 
              <strong v-if="userProfile" class="text-dark">{{ userProfile.prenom }} {{ userProfile.nom }}</strong>
            </p>
            <span class="badge bg-success-subtle border border-success-subtle text-success small">Profil Actif</span>
          </div>
        </div>
        
        <div class="d-none d-md-block">
          <span class="badge badge-soft text-muted">Accès : Aujourd'hui</span>
        </div>
      </div>

      <div class="row g-4">
        <div v-if="userProfile?.role === 'admin'" class="col-md-4">
          <div class="card card-action shadow-sm h-100" @click="goToUsers">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon mb-3">
                  <i class="bi bi-people-fill fs-4"></i>
                </div>
                <h5 class="fw-bold mb-2">Gestion Utilisateurs</h5>
                <p class="text-muted small">Pilotez les accès, ajoutez de nouveaux membres et gérez les rôles de l'équipe.</p>
              </div>
              <div class="text-end mt-3">
                <span class="text-primary fw-bold small">Y aller <i class="bi bi-arrow-right ms-1"></i></span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card card-action shadow-sm h-100" @click="goToDeclarations">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon mb-3">
                  <i class="bi bi-file-earmark-medical-fill fs-4"></i>
                </div>
                <h5 class="fw-bold mb-2">Déclarations</h5>
                <p class="text-muted small">Consultez l'historique, téléchargez les documents et suivez l'état des déclarations.</p>
              </div>
              <div class="text-end mt-3">
                <span class="text-primary fw-bold small">Y aller <i class="bi bi-arrow-right ms-1"></i></span>
              </div>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <div class="card shadow-sm h-100">
            <div class="card-body p-4 d-flex flex-column justify-content-between">
              <div>
                <div class="action-icon mb-3">
                  <i class="bi bi-folder-fill fs-4"></i>
                </div>
                <h5 class="fw-bold mb-2">Catalogues</h5>
                <p class="text-muted small">Accédez rapidement aux missions et grilles tarifaires des catalogues.</p>
              </div>
              
              <div class="mt-4">
                <div v-if="userProfile?.role === 'admin'" class="d-flex flex-column gap-2">
                  <button @click="goToCcda" class="btn btn-sm btn-outline-primary-custom w-100 text-start d-flex justify-content-between align-items-center">
                    <span>Catalogue CCDA</span>
                    <i class="bi bi-arrow-right"></i>
                  </button>
                  <button @click="goToCcdu" class="btn btn-sm btn-outline-primary-custom w-100 text-start d-flex justify-content-between align-items-center">
                    <span>Catalogue CCDU</span>
                    <i class="bi bi-arrow-right"></i>
                  </button>
                </div>
                <div v-else class="text-end">
                  <span @click="goToCcda" class="text-primary fw-bold small hover-primary cursor-pointer">
                    Y aller <i class="bi bi-arrow-right ms-1"></i>
                  </span>
                </div>
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

const goToUsers = () => router.push('/utilisateurs')
const goToDeclarations = () => router.push('/declarations')
const goToCcda = () => router.push('/missions/ccda')
const goToCcdu = () => router.push('/missions/cddu')

onMounted(async () => {
  try {
    const data = await authService.getUserProfile()
    userProfile.value = data
  } catch (error) {
    console.error("Erreur profil :", error)
  }
})
</script>

<style scoped>
/* Vide : Vive le main.css ! */
</style>