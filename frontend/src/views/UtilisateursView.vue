<script setup>
import { ref, onMounted, watch, computed } from 'vue' 
import { userService, authService, getReferentiels } from '@/services/api'

const utilisateurs = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

const idUserConnecte = ref(null)
const roleUserConnecte = ref('')
const siteUserConnecte = ref('') 
const programmeUserConnecte = ref('') // 📍 Stocke le programme du user connecté
const matiereUserConnectee = ref('')  // 📍 Stocke la matière du user connecté
const peutGererUtilisateurs = ref(false)

// --- État pour la recherche ---
const recherche = ref('')

// --- États pour le tri ---
const colonneTriee = ref('role')
const ordreTri = ref('asc')

// --- États pour le formulaire ---
const afficherFormulaire = ref(false)
const isSubmitting = ref(false)
const isEditing = ref(false)

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

// 🔥 Calcule si le rôle sélectionné a besoin d'un programme et d'une matière (uniquement TCP et RESP)
const besoinPedago = computed(() => {
  return ['tcp', 'resp'].includes(nouveauUser.value.role)
})

// On surveille le rôle pour masquer et vider les programmes/matières si le profil n'en a pas besoin
watch(() => nouveauUser.value.role, (nouveauRole) => {
  if (!besoinPedago.value) {
    nouveauUser.value.programme = ''
    nouveauUser.value.matiere = ''
    matieresDisponibles.value = []
  }
  // 🔥 Si le nouveau rôle est admin, on vide aussi le site
  if (nouveauRole === 'admin') {
    nouveauUser.value.site = ''
  }
})

// On surveille le programme pour charger les matières sans crasher
watch(() => nouveauUser.value.programme, (nouveauProgramme) => {
  nouveauUser.value.matiere = '' // On reset la matière
  if (nouveauProgramme && referentiels.value.matieres[nouveauProgramme]) {
    matieresDisponibles.value = referentiels.value.matieres[nouveauProgramme]
  } else {
    matieresDisponibles.value = []
  }
})

// Fonction pour changer la colonne de tri
const changerTri = (colonne) => {
  if (colonneTriee.value === colonne) {
    ordreTri.value = ordreTri.value === 'asc' ? 'desc' : 'asc'
  } else {
    colonneTriee.value = colonne
    ordreTri.value = 'asc'
  }
}

// 🔥 1. Rôles autorisés selon qui est connecté
const rolesAutorises = computed(() => {
  const role = roleUserConnecte.value
  
  if (role === 'admin') return referentiels.value.roles
  if (role === 'coordo') return ['resp', 'tcp']
  if (role === 'top_com') return ['com'] 
  if (role === 'resp') return ['tcp']
  
  return []
})

// 🔥 2. Sites autorisés selon qui est connecté
const sitesAutorises = computed(() => {
  const role = roleUserConnecte.value
  if (role === 'admin') return referentiels.value.sites
  
  if (['coordo', 'top_com', 'resp'].includes(role) && siteUserConnecte.value) {
    return [siteUserConnecte.value]
  }
  return []
})

// 🔥 Tableau filtré ET trié réactif
// Définition de l'ordre personnalisé pour les rôles
const ordrePrioriteRoles = {
  'admin': 1,
  'coordo': 2,
  'top_com': 3,
  'top': 4,
  'resp': 5,
  'tcp': 6,
  'com': 7
}

const utilisateursTries = computed(() => {
  let resultat = [...utilisateurs.value]
  
  if (recherche.value.trim() !== '') {
    const terme = recherche.value.toLowerCase().trim()
    resultat = resultat.filter(user => {
      return (
        (user.nom && user.nom.toLowerCase().includes(terme)) ||
        (user.prenom && user.prenom.toLowerCase().includes(terme)) ||
        (user.email && user.email.toLowerCase().includes(terme)) ||
        (user.role && user.role.toLowerCase().includes(terme)) ||
        (user.site && user.site.toLowerCase().includes(terme)) ||
        (user.programme && user.programme.toLowerCase().includes(terme)) ||
        (user.matiere && user.matiere.toLowerCase().includes(terme))
      )
    })
  }

  return resultat.sort((a, b) => {
    let valeurA = a[colonneTriee.value]
    let valeurB = b[colonneTriee.value]

    if (valeurA === null || valeurA === undefined) valeurA = ''
    if (valeurB === null || valeurB === undefined) valeurB = ''

    // 🔥 TRI SPÉCIFIQUE POUR LES RÔLES
    if (colonneTriee.value === 'role') {
      const poidsA = ordrePrioriteRoles[valeurA.toLowerCase()] || 99
      const poidsB = ordrePrioriteRoles[valeurB.toLowerCase()] || 99
      
      if (poidsA !== poidsB) {
        return ordreTri.value === 'asc' ? poidsA - poidsB : poidsB - poidsA
      }
    }

    // Le reste du tri (alphabétique pour les autres colonnes)
    if (typeof valeurA === 'string' && typeof valeurB === 'string') {
      valeurA = valeurA.toLowerCase()
      valeurB = valeurB.toLowerCase()
    }

    if (valeurA < valeurB) return ordreTri.value === 'asc' ? -1 : 1
    if (valeurA > valeurB) return ordreTri.value === 'asc' ? 1 : -1
    return 0
  })
})

// 🎯 NOUVEAU : Export Excel des utilisateurs
const exporterUtilisateurs = async () => {
  try {
    // Chargement dynamique d'ExcelJS si pas déjà présent
    if (!window.ExcelJS) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.4.0/exceljs.min.js'
        script.onload = resolve
        script.onerror = reject
        document.head.appendChild(script)
      })
    }
    
    const ExcelJS = window.ExcelJS
    const workbook = new ExcelJS.Workbook()
    const worksheet = workbook.addWorksheet('Base Utilisateurs')

    // Définition des colonnes
    worksheet.columns = [
      { header: 'ID', key: 'id', width: 10 },
      { header: 'NOM', key: 'nom', width: 20 },
      { header: 'PRÉNOM', key: 'prenom', width: 20 },
      { header: 'EMAIL', key: 'email', width: 30 },
      { header: 'RÔLE', key: 'role', width: 15 },
      { header: 'SITE', key: 'site', width: 15 },
      { header: 'PROGRAMME', key: 'programme', width: 20 },
      { header: 'MATIÈRE', key: 'matiere', width: 25 },
      { header: 'STATUT', key: 'statut', width: 12 }
    ]

    // Style de l'entête
    const headerRow = worksheet.getRow(1)
    headerRow.height = 25
    headerRow.eachCell((cell) => {
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF198754' } } // Vert Bootstrap
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true, size: 11 }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
    })

    // Remplissage des lignes (on prend utilisateursTries pour respecter la recherche en cours !)
    utilisateursTries.value.forEach((user, index) => {
      const row = worksheet.addRow({
        id: user.id,
        nom: user.nom ? user.nom.toUpperCase() : '',
        prenom: user.prenom || '',
        email: user.email || '',
        role: user.role ? user.role.toUpperCase() : '',
        site: user.site || 'N/A',
        programme: user.programme || '-',
        matiere: user.matiere || '-',
        statut: user.is_active ? 'Actif' : 'Inactif'
      })

      row.height = 20
      
      // Alignements
      row.getCell(1).alignment = { horizontal: 'center' }
      row.getCell(5).alignment = { horizontal: 'center' }
      row.getCell(6).alignment = { horizontal: 'center' }
      row.getCell(9).alignment = { horizontal: 'center' }

      // Alternance de couleur pour les lignes
      if (index % 2 !== 0) {
        row.eachCell((cell) => {
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8F9FA' } }
        })
      }
    })

    // Génération et téléchargement du fichier
    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Base_Utilisateurs_${new Date().toISOString().slice(0, 10)}.xlsx`)
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

  } catch (error) {
    console.error("Erreur lors de l'export Excel :", error)
    alert("Impossible de générer le fichier Excel.")
  }
}

const chargerDonnees = async () => {
  isLoading.value = true
  
  try {
    const me = await authService.getUserProfile()
    idUserConnecte.value = me.id
    roleUserConnecte.value = me.role
    siteUserConnecte.value = me.site || '' 
    programmeUserConnecte.value = me.programme || '' // 📍 On mémorise le programme du resp
    matiereUserConnectee.value = me.matiere || ''   // 📍 On mémorise la matière du resp
    
    peutGererUtilisateurs.value = ['admin', 'coordo', 'top_com', 'resp'].includes(roleUserConnecte.value)

    console.log("Mon rôle identifié :", roleUserConnecte.value, "sur le site :", siteUserConnecte.value)

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
    
    if (!isEditing.value) {
      nouveauUser.value.role = rolesAutorises.value[0] || 'tcp'
      nouveauUser.value.site = nouveauUser.value.role === 'admin' ? '' : (sitesAutorises.value[0] || '')
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
  isEditing.value = false 
  afficherFormulaire.value = !afficherFormulaire.value
  if (!afficherFormulaire.value) {
    annulerEtFermer()
  }
}

const editerUtilisateur = (user) => {
  errorMessage.value = ''
  isEditing.value = true
  afficherFormulaire.value = true
  
  nouveauUser.value = {
    id: user.id, 
    email: user.email,
    password: '', 
    prenom: user.prenom,
    nom: user.nom,
    role: user.role,
    site: user.site || '',
    programme: user.programme || '',
    matiere: user.matiere || ''
  }

  if (user.programme && referentiels.value.matieres[user.programme]) {
    matieresDisponibles.value = referentiels.value.matieres[user.programme]
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
    role: rolesAutorises.value[0] || 'tcp', 
    site: rolesAutorises.value[0] === 'admin' ? '' : (sitesAutorises.value[0] || ''), 
    programme: '', matiere: ''
  }
}

const soumettreFormulaire = async () => {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    const donneesAEnvoyer = { ...nouveauUser.value }

    // 🔥 Héritage automatique si le RESP gère un TCP
    if (roleUserConnecte.value === 'resp' && donneesAEnvoyer.role === 'tcp') {
      donneesAEnvoyer.site = siteUserConnecte.value
      donneesAEnvoyer.programme = programmeUserConnecte.value
      donneesAEnvoyer.matiere = matiereUserConnectee.value
    }

    // Si on crée un admin, on s'assure que le site envoyé est null
    if (donneesAEnvoyer.role === 'admin') {
      donneesAEnvoyer.site = null
    }

    if (!donneesAEnvoyer.programme) donneesAEnvoyer.programme = null
    if (!donneesAEnvoyer.matiere) donneesAEnvoyer.matiere = null

    if (isEditing.value) {
      const { id, ...payload } = donneesAEnvoyer
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
    'top_com': 'bg-info text-dark',
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
      
      <button 
        v-if="peutGererUtilisateurs"
        class="btn btn-primary" 
        @click="basculerFormulaire"
      >
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
                <option v-for="role in rolesAutorises" :key="role" :value="role">
                  {{ role.toUpperCase() }}
                </option>
              </select>
            </div>

            <div class="col-md-3" v-if="nouveauUser.role !== 'admin' && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
              <label class="form-label fw-bold small">Site</label>
              <select 
                v-model="nouveauUser.site" 
                class="form-select form-select-sm" 
                required
              >
                <option value="">-- Sélectionner --</option>
                <option v-for="site in sitesAutorises" :key="site" :value="site">
                  {{ site }}
                </option>
              </select>
            </div>

            <div class="col-md-3" v-if="besoinPedago && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
              <label class="form-label fw-bold small">Programme (Optionnel)</label>
              <select v-model="nouveauUser.programme" class="form-select form-select-sm">
                <option value="">-- Sélectionner --</option>
                <option v-for="(liste, nomProg) in referentiels.matieres" :key="nomProg" :value="nomProg">
                  {{ nomProg }}
                </option>
              </select>
            </div>

            <div class="col-md-3" v-if="besoinPedago && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
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

   <div class="row mb-3 align-items-center">
      <div class="col-md-4">
        <button 
          v-if="roleUserConnecte === 'admin'" 
          class="btn btn-outline-success btn-sm fw-bold" 
          @click="exporterUtilisateurs"
        >
          📊 Exporter la base (Excel)
        </button>
      </div>
      
      <div class="col-md-4 ms-auto">
        <div class="input-group input-group-sm">
          <span class="input-group-text bg-white border-end-0">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-search text-muted" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"/>
            </svg>
          </span>
          <input 
            v-model="recherche" 
            type="text" 
            class="form-control border-start-0 ps-1" 
            placeholder="Rechercher un nom, email, site, rôle..."
          >
          <button v-if="recherche" class="btn btn-outline-secondary" type="button" @click="recherche = ''">✖</button>
        </div>
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
                <th class="ps-4 th-triable" @click="changerTri('nom')">
                  NOM <span class="tri-icon">{{ colonneTriee === 'nom' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('prenom')">
                  PRÉNOM <span class="tri-icon">{{ colonneTriee === 'prenom' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('site')">
                  SITE <span class="tri-icon">{{ colonneTriee === 'site' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('role')">
                  RÔLE <span class="tri-icon">{{ colonneTriee === 'role' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('programme')">
                  PROGRAMME <span class="tri-icon">{{ colonneTriee === 'programme' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('matiere')">
                  MATIÈRE <span class="tri-icon">{{ colonneTriee === 'matiere' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('email')">
                  EMAIL <span class="tri-icon">{{ colonneTriee === 'email' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="th-triable" @click="changerTri('is_active')">
                  STATUT <span class="tri-icon">{{ colonneTriee === 'is_active' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="text-center pe-4" v-if="peutGererUtilisateurs">
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="utilisateursTries.length === 0">
                <td colspan="9" class="text-center text-muted py-4">
                  Aucun utilisateur trouvé.
                </td>
              </tr>
              
              <tr v-for="user in utilisateursTries" :key="user.id">
                <td class="ps-4 fw-bold text-uppercase">{{ user.nom }}</td>
                <td>{{ user.prenom }}</td>
                <td>
                  <span class="badge bg-light text-dark border">{{ user.site || 'N/A' }}</span>
                </td>
                <td>
                  <span class="badge text-uppercase" :class="getRoleBadgeClass(user.role)">{{ user.role }}</span>
                </td>
                <td>{{ user.programme || '-' }}</td>
                <td>{{ user.matiere || '-' }}</td>
                <td>{{ user.email }}</td>
                <td>
                  <span v-if="user.is_active" class="badge bg-soft-success text-success">Actif</span>
                  <span v-else class="badge bg-soft-danger text-danger">Inactif</span>
                </td>
                
                <td class="text-center pe-4" v-if="peutGererUtilisateurs">
                  <button class="btn btn-sm btn-outline-secondary me-2" @click="editerUtilisateur(user)">Modifier</button>
                  
                  <button 
                    class="btn btn-sm" 
                    :class="user.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                    @click="basculerStatut(user)"
                    :disabled="(user.role === 'admin' && user.is_active && totalAdminsActifs <= 1) || user.id === idUserConnecte"
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
.th-triable { cursor: pointer; position: relative; transition: background-color 0.2s ease; }
.th-triable:hover { background-color: #e9ecef !important; }
.tri-icon { display: inline-block; width: 15px; font-size: 0.8rem; margin-left: 5px; }
</style>