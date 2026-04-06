import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import ProfilView from '@/views/ProfilView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: { name: 'dashboard' } // 💡 Redirige l'adresse de base vers le tableau de bord
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }  
    },
    {
      path: '/profil',
      name: 'profil',
      component: ProfilView,
      meta: { requiresAuth: true }
    },
    {
      path: '/declarations',
      name: 'declarations',
      component: () => import('../views/DeclarationsView.vue'), 
      meta: { requiresAuth: true }
    },
    {
      path: '/utilisateurs',
      name: 'utilisateurs',
      component: () => import('../views/UtilisateursView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin', 'coordo', 'resp', 'top_com'] }
    },
    
    // 🎯 STRATÉGIE B : Une seule route pour les deux catalogues !
    {
      path: '/missions/:type',
      name: 'catalogue-missions',
      component: () => import('../views/MissionsCatalogueView.vue'),
      props: true,
      meta: { requiresAuth: true }, // Tout le monde peut voir les catalogues (les rôles sont gérés par ton back !)
      beforeEnter: (to, from, next) => {
        // Petite sécurité supplémentaire pour éviter qu'un malin tape /missions/nimportequoi dans l'URL
        const typeDemande = to.params.type.toLowerCase();
        if (['ccda', 'cddu'].includes(typeDemande)) {
          next();
        } else {
          next({ name: 'dashboard' }); // On redirige si le type de contrat n'existe pas
        }
      }
    },
    {
      path: '/pilotage',
      name: 'pilotage',
      component: () => import('@/views/PilotageView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin'] }
    },
    {
      path: '/synthese-paie',
      name: 'synthese-paie',
      component: () => import('../views/SynthesePaieView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin', 'coordo'] }
    }
  ],
})

// 🛡️ LE GARDE-FRONTIÈRE (Navigation Guard)
router.beforeEach((to, from) => {
  const token = localStorage.getItem('token')
  let userRole = null

  // 1. Si on a un token, on extrait le rôle pour les vérifications
  if (token) {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join(''))
      userRole = JSON.parse(jsonPayload).role
    } catch (e) {
      console.error("Erreur de décodage du token dans le router")
    }
  }

  // 🚪 Règle 1 : Si la page demande à être connecté et qu'on n'a pas de token -> Direction Login
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' } 
  } 
  
  // ⛔ Règle 2 : Si la page demande des rôles spécifiques et que l'utilisateur n'a pas le bon
  if (to.meta.rolesAutorises && !to.meta.rolesAutorises.includes(userRole)) {
    alert("Accès interdit : Vous n'avez pas les droits nécessaires.")
    return { name: 'dashboard' } 
  } 

  // 🟢 Règle 3 : Tout est OK, on laisse passer
  return true
})

export default router