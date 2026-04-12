<script setup>
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
      console.error("Erreur de récupération du profil", error)
      seDeconnecter()
    }
  } else {
    estConnecte.value = false
    userRole.value = ''
    prenomUtilisateur.value = 'Utilisateur'
  }
}

// Gestion de la fermeture des menus et rafraîchissement profil au changement de route
watch(() => route.path, () => {
  // 1. Fermer le menu mobile (hamburger) proprement
  const menuEnroulable = document.getElementById('navbarAvicenne')
  if (menuEnroulable && window.bootstrap) {
    const bCollapse = window.bootstrap.Collapse.getInstance(menuEnroulable)
    if (bCollapse) bCollapse.hide()
  }
  
  // 2. Supprimer les classes 'show' résiduelles sur les dropdowns
  document.querySelectorAll('.dropdown-menu.show').forEach(el => {
    el.classList.remove('show')
  })
  
  document.querySelectorAll('.dropdown-toggle.show').forEach(el => {
    el.classList.remove('show')
    el.setAttribute('aria-expanded', 'false')
  })

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
      <nav class="navbar navbar-expand-lg navbar-dark bg-hospital-blue shadow-sm py-2 sticky-top">
        <div class="container-fluid px-4">
          
          <div class="d-flex align-items-center gap-3">
            <RouterLink to="/dashboard" class="navbar-brand d-flex align-items-center me-0">
              <div class="avicenne-heart-logo nav-logo-container animate-pulse-heart">
                <i class="bi bi-suit-heart-fill text-white"></i>
                <i class="bi bi-activity nav-activity-blue"></i>
              </div>
              <span class="fw-bold text-white fs-5 tracking-tight ms-2">Avicenne Pay</span>
            </RouterLink>

            <div v-if="estConnecte" class="d-flex flex-column d-none d-md-flex">
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
                <a class="nav-link dropdown-toggle px-3" 
                   href="#" 
                   role="button" 
                   data-bs-toggle="dropdown" 
                   data-bs-display="static"
                   data-bs-auto-close="true"
                   :class="{ 'active': $route.path.includes('/missions') }">
                   Catalogues
                </a>
                <ul class="dropdown-menu border-0 shadow">
                  <li v-if="peutVoirCcda">
                    <RouterLink to="/missions/ccda" class="dropdown-item">Catalogue CCDA</RouterLink>
                  </li>
                  <li v-if="peutVoirCcdu">
                    <RouterLink to="/missions/cddu" class="dropdown-item">Catalogue CCDU</RouterLink>
                  </li>
                </ul>
              </li>

              <li class="nav-item dropdown" v-if="peutVoirPilotageEtPaie">
                <a class="nav-link dropdown-toggle px-3" 
                   href="#" 
                   role="button" 
                   data-bs-toggle="dropdown" 
                   data-bs-display="static"
                   data-bs-auto-close="true" 
                   :class="{ 'active': $route.path.includes('/pilotage') || $route.path.includes('/synthese') }">
                   Analyses & Paie
                </a>
                <ul class="dropdown-menu border-0 shadow">
                  <li><RouterLink to="/pilotage" class="dropdown-item">Tableaux de Pilotage</RouterLink></li>
                  <li><RouterLink to="/synthese-paie" class="dropdown-item">Synthèse Paie Globale</RouterLink></li>
                </ul>
              </li>
            </ul>

            <div class="d-flex align-items-center gap-3 justify-content-center justify-content-lg-end">
              <RouterLink to="/profil" class="text-white-50 hover-white fs-5" title="Mon Profil">
                <i class="bi bi-person-circle"></i>
              </RouterLink>
              <div class="vr text-white opacity-25 d-none d-lg-block" style="height: 20px;"></div>
              <button class="btn btn-sm text-white-50 hover-white fw-bold border-0 d-flex align-items-center gap-1 p-0" @click="seDeconnecter">
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
.bg-hospital-blue { 
  background-color: var(--primary-color) !important; 
}

/* --- DROPDOWN POSITIONING --- */
.nav-item.dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute !important;
  top: 100% !important;
  left: 0 !important;
  margin-top: 8px !important;
  background-color: #ffffff !important;
  border: none !important;
  border-radius: 0.75rem !important;
  padding: 0.5rem !important;
  min-width: 240px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
  z-index: 1060;
}

.dropdown-item {
  color: var(--text-dark) !important;
  font-weight: 600;
  padding: 0.7rem 1rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.dropdown-item:hover, 
.dropdown-item.router-link-exact-active {
  background-color: var(--primary-soft) !important;
  color: var(--primary-color) !important;
}

/* --- NAVBAR LINKS --- */
.nav-link {
  color: rgba(255, 255, 255, 0.85) !important;
  font-weight: 600;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.nav-link:hover, 
.nav-link.show {
  color: #fff !important;
  background-color: rgba(255, 255, 255, 0.15) !important;
}

.nav-link.active {
  color: #fff !important;
  background-color: rgba(255, 255, 255, 0.25) !important;
}

/* --- UTILS --- */
.scale-navbar-logo { 
  transform: scale(0.65); 
  width: 50px; 
}

.user-badge { 
  font-size: 0.65rem; 
  text-transform: uppercase; 
  letter-spacing: 0.5px;
}

/* --- RESPONSIVE MOBILE --- */
@media (max-width: 991px) {
  .dropdown-menu {
    position: static !important;
    background-color: rgba(255, 255, 255, 0.05) !important;
    box-shadow: none !important;
    min-width: 100%;
    margin-top: 0 !important;
  }
  
  .dropdown-item {
    color: #fff !important;
    padding-left: 1.5rem;
  }
}

/* Fix pour éviter les menus fantômes après clic sur lien */
.router-link-active + .dropdown-menu,
.router-link-exact-active + .dropdown-menu {
    display: none !important;
}

.dropdown-toggle.show + .dropdown-menu {
    display: block !important;
}
/* On ajoute de l'espace en haut du contenu pour compenser la navbar fixe */
main.container-fluid {
  padding-top: 1.5rem; /* Ajuste selon tes préférences */
}

/* On s'assure que la navbar reste au-dessus de tout le reste du contenu */
.navbar.sticky-top {
  z-index: 1020;
}
/* --- STYLE LOGO NAVBAR (Inversé) --- */
.nav-logo-container {
  transform: scale(0.7); /* Ajustement taille pour navbar */
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-logo-container .bi-suit-heart-fill {
  font-size: 2.5rem; /* Taille du coeur */
}

.nav-activity-blue {
  position: absolute;
  /* L'activité électrique prend la couleur de fond de la navbar */
  color: var(--primary-color) !important; 
  font-size: 1.3rem;
  z-index: 2;
}

/* On ré-applique l'animation ici au cas où elle n'est pas globale */
@keyframes heartPulse {
  0% { transform: scale(0.7); }
  15% { transform: scale(0.78); }
  30% { transform: scale(0.7); }
  45% { transform: scale(0.8); }
  100% { transform: scale(0.7); }
}

.animate-pulse-heart {
  animation: heartPulse 1.5s infinite cubic-bezier(0.215, 0.61, 0.355, 1);
}
</style>