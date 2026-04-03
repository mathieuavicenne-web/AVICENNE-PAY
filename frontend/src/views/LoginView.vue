<template>
  <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh; width: 100vw; background-color: #f8f9fa;">
    
    <div class="card shadow-sm" style="max-width: 400px; width: 100%; padding: 2rem; background-color: white;">
      <div class="card-body">
        <h2 class="navbar-brand text-center d-block mb-4" style="font-size: 1.6rem; color: var(--primary-dark);">
          Avicenne Pay
        </h2>
        
        <p class="text-center text-muted mb-4" style="font-size: 0.9rem;">
          Veuillez vous connecter pour accéder au tableau de bord.
        </p>

        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label for="email" class="form-label" style="font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: var(--gray-muted);">
              Email Professionnel
            </label>
            <input 
              type="email" 
              id="email" 
              class="form-control" 
              v-model="email" 
              required 
              placeholder="admin@avicenne.fr"
              style="border-radius: 0.5rem;"
            >
          </div>
          
          <div class="mb-4">
            <label for="password" class="form-label" style="font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: var(--gray-muted);">
              Mot de passe
            </label>
            <input 
              type="password" 
              id="password" 
              class="form-control" 
              v-model="password" 
              required 
              placeholder="••••••"
              style="border-radius: 0.5rem;"
            >
          </div>

          <button 
            type="submit" 
            class="btn btn-success w-100 py-2" 
            :disabled="isLoading"
            style="border-radius: 0.5rem;"
          >
            {{ isLoading ? 'Connexion en cours...' : 'Se connecter' }}
          </button>
          
          <div v-if="errorMessage" class="mt-3 text-center badge bg-soft-danger w-100 py-2">
            ⚠️ {{ errorMessage }}
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/services/api' 

const router = useRouter()

const email = ref('')
const password = ref('')
const isLoading = ref(false) // On garde bien isLoading ici !
const errorMessage = ref('')

const handleLogin = async () => {
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    await authService.login(email.value, password.value)
    router.push('/dashboard')
  } catch (error) {
    console.error('Erreur de connexion:', error)
    errorMessage.value = "Email ou mot de passe incorrect."
  } finally {
    isLoading.value = false
  }
}
</script>