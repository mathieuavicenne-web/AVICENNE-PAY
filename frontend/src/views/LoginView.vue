<template>
  <div class="login-container d-flex align-items-center justify-content-center">
    <div class="col-12 col-sm-10 col-md-8 col-lg-5 col-xl-4 p-3 text-center">
      
      <h1 class="h1-avicenne mb-1">Avicenne Pay</h1>
      <p class="text-muted small mb-4">Portail d'excellence pour les futurs professionnels de santé</p>

      <div class="card shadow-avicenne login-card">
        <div class="card-body p-4 p-md-5">
          
          <div class="d-flex justify-content-center mb-4">
            <div class="avicenne-heart-logo animate-pulse-heart">
              <i class="bi bi-suit-heart-fill"></i>
              <i class="bi bi-activity"></i>
            </div>
          </div>

          <form @submit.prevent="handleLogin">
            <div class="mb-4 text-start">
              <label class="form-label small fw-bold text-muted">Identifiant Avicenne</label>
              <div class="input-group custom-group">
                <span class="input-group-text"><i class="bi bi-person-badge"></i></span>
                <input 
                  v-model="email" 
                  type="email" 
                  class="form-control" 
                  placeholder="nom@avicenne.fr" 
                  required
                >
              </div>
            </div>

            <div class="mb-4 text-start">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <label class="form-label small fw-bold text-muted mb-0">Code d'accès</label>
                <router-link to="/forgot-password" class="text-primary small fw-bold text-decoration-none">
                  Oublié ?
                </router-link>
              </div>
              <div class="input-group custom-group">
                <span class="input-group-text"><i class="bi bi-shield-lock"></i></span>
                <input 
                  v-model="password" 
                  type="password" 
                  class="form-control" 
                  placeholder="••••••••" 
                  required
                >
              </div>
            </div>

            <div v-if="error" class="alert alert-danger-soft small mb-4 animate-pulse">
               {{ error }}
            </div>

            <button type="submit" class="btn btn-avicenne-submit w-100" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              <span v-else>Accéder à mon espace <i class="bi bi-chevron-right ms-2"></i></span>
            </button>
          </form>

        </div>
      </div>

      <div class="text-center mt-5">
        <p class="text-muted small opacity-50">&copy; 2026 Avicenne Pay — Excellence & Réussite</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/api' // Branchement réel

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // APPEL RÉEL À TA BDD
    await authService.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    console.error("Erreur login:", err)
    error.value = err.response?.data?.message || "Identifiants incorrects ou accès refusé."
  } finally {
    loading.value = false
  }
}
</script>

  