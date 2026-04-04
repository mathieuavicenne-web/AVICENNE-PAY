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
      component: DashboardView, // 🟢 Utilise bien notre DashboardView !
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
      component: () => import('../views/HomeView.vue'), // À remplacer par ta vraie vue plus tard !
      meta: { requiresAuth: true }
    },
    {
      path: '/utilisateurs',
      name: 'utilisateurs',
      component: () => import('../views/UtilisateursView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin', 'coordo', 'resp', 'top_com'] }
    },
    {
      path: '/catalogue-ccda',
      name: 'catalogue-ccda',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin', 'coordo'] }
    },
    {
      path: '/catalogue-ccdu',
      name: 'catalogue-ccdu',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin'] }
    },
    {
      path: '/pilotage',
      name: 'pilotage',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true, rolesAutorises: ['admin', 'coordo'] }
    },
    {
      path: '/synthese-paie',
      name: 'synthese-paie',
      component: () => import('../views/HomeView.vue'),
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
    return { name: 'login' } // 🟢 Méthode moderne sans next() !
  } 
  
  // ⛔ Règle 2 : Si la page demande des rôles spécifiques et que l'utilisateur n'a pas le bon
  if (to.meta.rolesAutorises && !to.meta.rolesAutorises.includes(userRole)) {
    alert("Accès interdit : Vous n'avez pas les droits nécessaires.")
    return { name: 'dashboard' } // 🟢 On le renvoie vers le dashboard plutôt que 'home' qui n'existe pas
  } 

  // 🟢 Règle 3 : Tout est OK, on laisse passer (pas besoin de retourner quoi que ce soit)
})

export default router