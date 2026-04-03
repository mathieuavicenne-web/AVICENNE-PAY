<script setup>
import { ref, onMounted, watch, computed } from 'vue' 
import { userService } from '@/services/api'
import { getReferentiels } from '@/services/api'

const utilisateurs = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

// --- États pour le formulaire ---
const afficherFormulaire = ref(false)
const isSubmitting = ref(false)
const isEditing = ref(false) // 🔵 Flag pour savoir si on est en train de modifier

const referentiels = ref({
  sites: [],
  roles: [],
  matieres: {}
})

const nouveauUser = ref({
  email: '',
  password: '',
  prenom: '',
  nom: '',
  role: 'tcp',
  site: '',
  programme: '',
  matiere: ''
})

const matieresDisponibles = ref([])

// On surveille le programme pour charger les matières sans crasher
watch(() => nouveauUser.value.programme, (nouveauProgramme) => {
  nouveauUser.value.matiere = '' // On reset la matière
  if (nouveauProgramme && referentiels.value.matieres[nouveauProgramme]) {
    matieresDisponibles.value = referentiels.value.matieres[nouveauProgramme]
  } else {
    matieresDisponibles.value = []
  }
})

const chargerDonnees = async () => {
  isLoading.value = true
  
  try {
    const usersData = await userService.getAllUsers()
    if (Array.isArray(usersData)) {
      utilisateurs.value = usersData
    } else if (usersData && Array.isArray(usersData.data)) {
      utilisateurs.value = usersData.data
    } else if (usersData && Array.isArray(usersData.users)) {
      utilisateurs.value = usersData.users
    } else if (usersData && typeof usersData === 'object' && usersData.email) {
      utilisateurs.value = [usersData]
    } else {
      utilisateurs.value = []
    }
  } catch (error) {
    console.error("Erreur lors du chargement des utilisateurs :", error)
  }

  try {
    const refsData = await getReferentiels()
    referentiels.value = refsData
    
    if (refsData.sites && refsData.sites.length > 0 && !isEditing.value) {
      nouveauUser.value.site = refsData.sites[0]
    }
  } catch (error) {
    console.error("Erreur lors du chargement des référentiels :", error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  chargerDonnees()
})

const basculerFormulaire = () => {
  errorMessage.value = ''
  isEditing.value = false // 🔵 On s'assure qu'on est en mode création
  afficherFormulaire.value = !afficherFormulaire.value
  if (!afficherFormulaire.value) {
    annulerEtFermer()
  }
}

// 🔵 Fonction déclenchée quand on clique sur "Modifier" dans le tableau
const editerUtilisateur = (user) => {
  errorMessage.value = ''
  isEditing.value = true
  afficherFormulaire.value = true
  
  // On remplit le formulaire avec les données de l'utilisateur cliqué
  nouveauUser.value = {
    id: user.id, // On garde l'ID pour savoir qui modifier
    email: user.email,
    password: '', // On n'affiche pas le mot de passe actuel par sécurité
    prenom: user.prenom,
    nom: user.nom,
    role: user.role,
    site: user.site || '',
    programme: user.programme || '',
    matiere: user.matiere || ''
  }

  // Petit hack pour forcer le chargement des matières correspondantes au programme
  if (user.programme && referentiels.value.matieres[user.programme]) {
    matieresDisponibles.value = referentiels.value.matieres[user.programme]
    // On doit réassigner la matière APRES le chargement de la liste
    setTimeout(() => {
      nouveauUser.value.matiere = user.matiere || ''
    }, 0)
  }
}

const annulerEtFermer = () => {
  afficherFormulaire.value = false
  isEditing.value = false
  nouveauUser.value = {
    email: '', password: '', prenom: '', nom: '',
    role: 'tcp', site: referentiels.value.sites[0] || '', programme: '', matiere: ''
  }
}

const soumettreFormulaire = async () => {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    const donneesAEnvoyer = { ...nouveauUser.value }

    if (donneesAEnvoyer.role === 'admin' && !donneesAEnvoyer.site) {
      donneesAEnvoyer.site = null
    }

    if (!donneesAEnvoyer.programme) donneesAEnvoyer.programme = null
    if (!donneesAEnvoyer.matiere) donneesAEnvoyer.matiere = null

    // 🔵 Tri selon qu'on crée ou qu'on modifie
    if (isEditing.value) {
      const { id, ...payload } = donneesAEnvoyer
      // Si le mot de passe est vide, on ne l'envoie pas pour ne pas l'écraser
      if (!payload.password) delete payload.password
      
      console.log(`🚀 Mise à jour du user ${id} :`, payload)
      await userService.updateUser(id, payload)
      alert("Utilisateur mis à jour avec succès !")
    } else {
      console.log("🚀 Envoi des données au backend :", donneesAEnvoyer)
      await userService.createUser(donneesAEnvoyer)
      alert("Utilisateur créé avec succès !")
    }
    
    annulerEtFermer()
    await chargerDonnees()
    
  } catch (error) {
    console.error("❌ Erreur :", error)
    errorMessage.value = error.message || "Une erreur inconnue est survenue."
  } finally {
    isSubmitting.value = false
  }
}

const getRoleBadgeClass = (role) => {
  const mapping = {
    'admin': 'bg-danger',
    'coordo': 'bg-warning text-dark',
    'resp': 'bg-primary',
    'top': 'bg-info text-dark',
    'tcp': 'bg-success',
    'com': 'bg-secondary'
  }
  return mapping[role] || 'bg-light text-dark'
}

const totalAdminsActifs = computed(() => {
  return utilisateurs.value.filter(u => u.role === 'admin' && u.is_active).length
})

const basculerStatut = async (user) => {
  if (user.role === 'admin' && user.is_active && totalAdminsActifs.value <= 1) {
    alert("Action impossible : Il doit toujours rester au moins un administrateur actif !")
    return
  }

  try {
    await userService.toggleUserStatus(user.id)
    await chargerDonnees()
  } catch (error) {
    alert("Impossible de modifier le statut de l'utilisateur.")
  }
}
</script>

<template>
  <div class="container mt-4 text-start">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h1 class="fw-bold" style="color: var(--primary-color);">Gestion des Utilisateurs</h1>
        <p class="text-muted">Visualisez et gérez les utilisateurs selon votre périmètre de droits.</p>
      </div>
      <button class="btn btn-primary" @click="basculerFormulaire">
        {{ afficherFormulaire ? '✖ Masquer le formulaire' : '+ Ajouter un utilisateur' }}
      </button>
    </div>

    <div v-if="afficherFormulaire" class="card shadow-sm border-0 mb-4 bg-light">
      <div class="card-body p-4">
        <h5 class="fw-bold mb-3">{{ isEditing ? 'Modifier l\'utilisateur' : 'Créer un nouvel utilisateur' }}</h5>
        
        <div v-if="errorMessage" class="alert alert-danger mb-3">
          {{ errorMessage }}
        </div>

        <form @submit.prevent="soumettreFormulaire">
          <div class="row g-3">
            <div class="col-md-3">
              <label class="form-label fw-bold small">Prénom</label>
              <input v-model="nouveauUser.prenom" type="text" class="form-control form-control-sm" required>
            </div>
            <div class="col-md-3">
              <label class="form-label fw-bold small">Nom</label>
              <input v-model="nouveauUser.nom" type="text" class="form-control form-control-sm" required>
            </div>
            <div class="col-md-3">
              <label class="form-label fw-bold small">Email</label>
              <input v-model="nouveauUser.email" type="email" class="form-control form-control-sm" required>
            </div>
            <div class="col-md-3">
              <label class="form-label fw-bold small">Mot de passe <span v-if="isEditing" class="text-muted fw-normal">(Optionnel)</span></label>
              <input v-model="nouveauUser.password" type="password" class="form-control form-control-sm" :required="!isEditing">
            </div>
            
            <div class="col-md-3">
              <label class="form-label fw-bold small">Rôle</label>
              <select v-model="nouveauUser.role" class="form-select form-select-sm" required>
                <option v-for="role in referentiels.roles" :key="role" :value="role">
                  {{ role.toUpperCase() }}
                </option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small">
                Site <span v-if="nouveauUser.role === 'admin'" class="text-muted fw-normal">(Optionnel)</span>
              </label>
              <select 
                v-model="nouveauUser.site" 
                class="form-select form-select-sm" 
                :required="nouveauUser.role !== 'admin'"
              >
                <option value="">-- Sélectionner --</option>
                <option v-for="site in referentiels.sites" :key="site" :value="site">
                  {{ site }}
                </option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small">Programme (Optionnel)</label>
              <select v-model="nouveauUser.programme" class="form-select form-select-sm">
                <option value="">-- Sélectionner --</option>
                <option v-for="(liste, nomProg) in referentiels.matieres" :key="nomProg" :value="nomProg">
                  {{ nomProg }}
                </option>
              </select>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small">Matière (Optionnel)</label>
              <select v-model="nouveauUser.matiere" class="form-select form-select-sm" :disabled="!nouveauUser.programme">
                <option value="">-- Sélectionner --</option>
                <option v-for="mat in matieresDisponibles" :key="mat" :value="mat">
                  {{ mat }}
                </option>
              </select>
            </div>
          </div>

          <div class="mt-3 d-flex justify-content-end gap-2">
            <button type="button" class="btn btn-sm btn-secondary" @click="annulerEtFermer">Annuler</button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="isSubmitting">
              <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-1"></span>
              {{ isEditing ? 'Mettre à jour' : 'Enregistrer l\'utilisateur' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Chargement...</span>
      </div>
    </div>

    <div v-else class="card shadow-sm border-0">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th class="ps-4">Nom / Prénom</th>
                <th>Email</th>
                <th>Site</th>
                <th>Rôle</th>
                <th>Statut</th>
                <th class="text-center pe-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in utilisateurs" :key="user.id">
                <td class="ps-4 fw-bold">{{ user.prenom }} {{ user.nom.toUpperCase() }}</td>
                <td>{{ user.email }}</td>
                <td><span class="badge bg-light text-dark border">{{ user.site || 'N/A' }}</span></td>
                <td><span class="badge text-uppercase" :class="getRoleBadgeClass(user.role)">{{ user.role }}</span></td>
                <td>
                  <span v-if="user.is_active" class="badge bg-soft-success text-success">Actif</span>
                  <span v-else class="badge bg-soft-danger text-danger">Inactif</span>
                </td>
                <td class="text-center pe-4">
                    <button class="btn btn-sm btn-outline-secondary me-2" @click="editerUtilisateur(user)">Modifier</button>
                    
                    <button 
                        class="btn btn-sm" 
                        :class="user.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                        @click="basculerStatut(user)"
                        :disabled="user.role === 'admin' && user.is_active && totalAdminsActifs <= 1"
                    >
                        {{ user.is_active ? 'Désactiver' : 'Activer' }}
                    </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-soft-success { background-color: #d1e7dd; }
.text-success { color: #0f5132 !important; }
.bg-soft-danger { background-color: #f8d7da; }
.text-danger { color: #842029 !important; }
.bg-light { background-color: #f8f9fa !important; }
</style>