<script setup>
import { ref, onMounted } from 'vue'
import { authService } from '@/services/api'

const profil = ref({
  prenom: '',
  nom: '',
  email: '',
  role: ''
})
const isLoading = ref(true)

onMounted(async () => {
  try {
    const userData = await authService.getUserProfile()
    profil.value = userData
  } catch (error) {
    console.error("Erreur lors de la récupération du profil", error)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="container mt-4 text-start">
    <div class="mb-4">
      <h1 class="fw-bold" style="color: var(--primary-color);">Mon Profil</h1>
      <p class="text-muted">Retrouvez ici vos informations personnelles enregistrées dans Avicenne Pay.</p>
    </div>

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Chargement...</span>
      </div>
    </div>

    <div v-else class="card shadow-sm border-0 mx-auto" style="max-width: 600px;">
      <div class="card-body p-4">
        <div class="d-flex align-items-center mb-4">
          <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center" style="width: 60px; height: 60px; font-size: 1.5rem; font-weight: bold;">
            {{ profil.prenom.charAt(0) }}{{ profil.nom.charAt(0) }}
          </div>
          <div class="ms-3">
            <h3 class="mb-0 fw-bold">{{ profil.prenom }} {{ profil.nom }}</h3>
            <span class="badge bg-secondary text-uppercase">{{ profil.role }}</span>
          </div>
        </div>

        <hr class="text-muted">

        <div class="row g-3">
          <div class="col-sm-4 text-muted fw-bold">Prénom</div>
          <div class="col-sm-8">{{ profil.prenom }}</div>

          <div class="col-sm-4 text-muted fw-bold">Nom</div>
          <div class="col-sm-8">{{ profil.nom }}</div>

          <div class="col-sm-4 text-muted fw-bold">Email</div>
          <div class="col-sm-8">{{ profil.email }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-primary {
  background-color: var(--primary-color) !important;
}
</style>