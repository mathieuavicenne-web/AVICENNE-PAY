<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { authService } from '@/services/api' 

const router = useRouter()
const route = useRoute()

const estConnecte = ref(false)
const userRole = ref('')
const prenomUtilisateur = ref('Utilisateur')

const chargerProfil = async () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const userData = await authService.getUserProfile()
      prenomUtilisateur.value = userData.prenom
      userRole.value = userData.role
      estConnecte.value = true
    } catch (error) {
      console.error("Erreur de récupération du profil dans App.vue", error)
      seDeconnecter()
    }
  } else {
    estConnecte.value = false
    userRole.value = ''
    prenomUtilisateur.value = 'Utilisateur'
  }
}

watch(() => route.path, () => {
  chargerProfil()
})

onMounted(() => {
  chargerProfil()
})

const seDeconnecter = () => {
  authService.logout() 
  userRole.value = ''
  prenomUtilisateur.value = 'Utilisateur'
  estConnecte.value = false
  router.push('/login')
}

const peutVoirGestionUtilisateurs = computed(() => ['admin', 'coordo', 'resp', 'top_com'].includes(userRole.value))
const peutVoirCcda = computed(() => ['admin', 'coordo'].includes(userRole.value))
const peutVoirCcdu = computed(() => userRole.value === 'admin')
const peutVoirPilotageEtPaie = computed(() => userRole.value === 'admin')
</script>

<template>
  <div class="min-vh-100 bg-hospital-light">
    
    <div v-if="$route.name === 'login'">
      <RouterView />
    </div>

    <div v-else>
      
      <nav class="navbar navbar-expand-lg navbar-dark bg-hospital-blue shadow-sm py-2 mb-4">
        <div class="container-fluid px-4">
          
          <div class="d-flex align-items-center gap-3">
            <RouterLink to="/dashboard" class="navbar-brand d-flex align-items-center me-0">
              <span class="fs-4 me-2">🩺</span>
              <span class="fw-bold text-white fs-5">Avicenne Pay</span>
            </RouterLink>

            <div v-if="estConnecte" class="d-flex flex-column d-none d-md-flex text-white-50">
              <span class="text-white fw-bold small lh-1 mb-1">{{ prenomUtilisateur }}</span>
              <span class="badge bg-white bg-opacity-25 text-white user-badge">{{ userRole }}</span>
            </div>
          </div>

          <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarAvicenne">
            <span class="navbar-toggler-icon"></span>
          </button>

          <div class="collapse navbar-collapse" id="navbarAvicenne">
            <ul class="navbar-nav mx-auto gap-1 my-3 my-lg-0 align-items-center">
              
              <li class="nav-item">
                <RouterLink to="/dashboard" class="nav-link px-3">Tableau de bord</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/declarations" class="nav-link px-3">Déclarations</RouterLink>
              </li>
              <li class="nav-item" v-if="peutVoirGestionUtilisateurs">
                <RouterLink to="/utilisateurs" class="nav-link px-3">Utilisateurs</RouterLink>
              </li>

              <li class="nav-item dropdown" v-if="peutVoirCcda || peutVoirCcdu">
                <a class="nav-link dropdown-toggle px-3" href="#" role="button" data-bs-toggle="dropdown">
                  Catalogues
                </a>
                <ul class="dropdown-menu border-0 shadow-lg rounded-3 mt-2">
                  <li v-if="peutVoirCcda">
                    <RouterLink to="/missions/ccda" class="dropdown-item py-2">Catalogue CCDA</RouterLink>
                  </li>
                  <li v-if="peutVoirCcdu">
                    <RouterLink to="/missions/cddu" class="dropdown-item py-2">Catalogue CCDU</RouterLink>
                  </li>
                </ul>
              </li>

              <li class="nav-item dropdown" v-if="peutVoirPilotageEtPaie">
                <a class="nav-link dropdown-toggle px-3" href="#" role="button" data-bs-toggle="dropdown">
                  Analyses & Paie
                </a>
                <ul class="dropdown-menu border-0 shadow-lg rounded-3 mt-2">
                  <li>
                    <RouterLink to="/pilotage" class="dropdown-item py-2">Tableaux de Pilotage</RouterLink>
                  </li>
                  <li>
                    <RouterLink to="/synthese-paie" class="dropdown-item py-2">Synthèse Paie Globale</RouterLink>
                  </li>
                </ul>
              </li>
            </ul>

            <div class="d-flex align-items-center gap-3 justify-content-center justify-content-lg-end">
              <RouterLink to="/profil" class="text-white-50 hover-white fs-5" title="Mon Profil">
                <i class="bi bi-person-circle"></i>
              </RouterLink>
              
              <div class="vr text-white opacity-25 d-none d-lg-block" style="height: 20px;"></div>

              <button class="btn btn-sm text-white-50 hover-white fw-bold border-0 d-flex align-items-center gap-1 p-0" @click="seDeconnecter" title="Déconnexion">
                <i class="bi bi-power fs-5"></i>
                <span class="d-none d-xl-inline small">Quitter</span>
              </button>
            </div>
          </div>

        </div>
      </nav>

      <main class="container-fluid px-4">
        <RouterView />
      </main>
    </div>

  </div>
</template>

<style scoped>
/* Fond blanc cassé général */
.bg-hospital-light {
  background-color: #f8f9fa;
}

/* 🎨 Le Bleu Doux (Hôpital/Stéthoscope) pour la Navbar */
.bg-hospital-blue {
  background-color: #3498db !important;
}

/* Liens de navigation (Blancs avec opacité pour les inactifs) */
.nav-link {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85) !important;
  border-radius: 0.375rem;
  transition: all 0.2s ease;
}

.nav-link:hover, .nav-link:focus {
  color: #ffffff !important;
  background-color: rgba(255, 255, 255, 0.15);
}

/* Le lien actif s'applique uniquement aux éléments de la liste du menu */
.navbar-nav .router-link-exact-active {
  color: #ffffff !important;
  background-color: rgba(255, 255, 255, 0.25);
}

/* Classes utilitaires pour le profil et déconnexion */
.text-white-50 {
  color: rgba(255, 255, 255, 0.7) !important;
  transition: color 0.2s;
}
.hover-white:hover {
  color: #ffffff !important;
}

/* Badge du rôle en haut à gauche */
.user-badge {
  font-size: 0.6rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.15em 0.4em;
  border-radius: 4px;
}

/* Dropdowns élégants */
.dropdown-menu {
  font-size: 0.9rem;
  min-width: 200px;
}
.dropdown-item {
  font-weight: 600;
  color: #4b5563;
  border-radius: 0.25rem;
}
.dropdown-item:hover {
  background-color: #f3f4f6;
  color: #3498db !important;
}
</style>