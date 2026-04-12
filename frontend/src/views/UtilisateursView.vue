<script setup>
import { ref, onMounted, watch, computed } from 'vue' 
import { userService, authService, getReferentiels } from '@/services/api'

const utilisateurs = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

const idUserConnecte = ref(null)
const roleUserConnecte = ref('')
const siteUserConnecte = ref('') 
const programmeUserConnecte = ref('')
const matiereUserConnectee = ref('')
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

// --- État pour les filtres de statut ---
const filtreStatut = ref('tous') // 'tous', 'actifs', 'inactifs'

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
  
  // Filtre par statut (Nouveau)
  if (filtreStatut.value === 'actifs') {
    resultat = resultat.filter(u => u.is_active)
  } else if (filtreStatut.value === 'inactifs') {
    resultat = resultat.filter(u => !u.is_active)
  }

  // Filtre par recherche
  if (recherche.value.trim() !== '') {
    const terme = recherche.value.toLowerCase().trim()
    resultat = resultat.filter(user => {
      return (
        (user.nom?.toLowerCase().includes(terme)) ||
        (user.prenom?.toLowerCase().includes(terme)) || 
        (user.filiere?.toLowerCase().includes(terme)) ||
        (user.email?.toLowerCase().includes(terme)) ||
        (user.role?.toLowerCase().includes(terme)) ||
        (user.site?.toLowerCase().includes(terme))
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

// 🎯: Export Excel des utilisateurs
const exporterUtilisateurs = async () => {
  console.log("DATA USER 17 :", utilisateursTries.value.find(u => u.id === 17));
  try {
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

    worksheet.columns = [
      { header: 'NOM', key: 'nom', width: 25 },
      { header: 'PRÉNOM', key: 'prenom', width: 25 },
      { header: 'EMAIL', key: 'email', width: 35 },
      { header: 'TÉLÉPHONE', key: 'telephone', width: 18 },
      { header: 'RÔLE', key: 'role', width: 15 },
      { header: 'SITE', key: 'site', width: 15 },
      { header: 'PROGRAMME', key: 'programme', width: 20 },
      { header: 'MATIÈRE', key: 'matiere', width: 20 },
      { header: 'IBAN', key: 'iban', width: 35 },
      { header: 'NSS', key: 'nss', width: 22 },
      { header: 'STATUT', key: 'statut', width: 12 }
    ]

    // Style de l'entête
    const headerRow = worksheet.getRow(1)
    headerRow.height = 30
    headerRow.eachCell((cell) => {
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4396D1' } }
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true, size: 12 }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
    })

    // Ajout des données
    utilisateursTries.value.forEach((user, index) => {
      const row = worksheet.addRow({
        nom: user.nom?.toUpperCase() || '',
        prenom: user.prenom || '',
        email: user.email || '',
        telephone: user.telephone || '-',
        role: user.role?.toUpperCase() || '',
        site: user.site || 'N/A',
        programme: user.programme || '-',
        matiere: user.matiere || '-',
        // PROTECTION ICI : On check 'iban' OU 'iban_encrypted'
        iban: user.iban || user.iban_encrypted || 'N/A', 
        nss: user.nss || user.nss_encrypted || 'N/A',
        statut: user.is_active ? 'Actif' : 'Inactif'
      })

      row.height = 25
      row.alignment = { vertical: 'middle' }
      if (index % 2 !== 0) {
        row.eachCell((cell) => {
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } }
        })
      }
    })

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `Export_Utilisateurs_${new Date().toISOString().slice(0, 10)}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

  } catch (error) {
    console.error("Erreur export :", error)
    alert("Erreur lors de l'export Excel.")
  }
}

const chargerDonnees = async () => {
  isLoading.value = true
  
  try {
    const me = await authService.getUserProfile()
    idUserConnecte.value = me.id
    roleUserConnecte.value = me.role
    siteUserConnecte.value = me.site || '' 
    programmeUserConnecte.value = me.programme || ''
    matiereUserConnectee.value = me.matiere || ''
    
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
const getEmojiFiliere = (filiere) => {
  if (!filiere) return '👤'; // Fallback si null
  
  // On transforme "medecine" ou "Médecine" en "medecine" pour comparer
  const val = filiere.toLowerCase()
                     .trim()
                     .normalize("NFD").replace(/[\u0300-\u036f]/g, ""); // Enlève les accents

  const emojis = {
    'medecine': '🩺',
    'pharmacie': '💊',
    'odontologie': '🦷',
    'maieutique': '🤰',
    'kinesitherapie': '💆'
  };
  
  return emojis[val] || '👤';
};

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
  <div class="p-6 text-start">
    <div class="mb-8 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h1-avicenne m-0">Gestion des Utilisateurs</h1>
        <p class="text-muted small mb-0">Visualisez et gérez les utilisateurs selon votre périmètre de droits.</p>
      </div>
      
      <button 
        v-if="peutGererUtilisateurs"
        class="btn-avicenne-submit shadow-sm" 
        @click="basculerFormulaire"
      >
        {{ afficherFormulaire ? '✖ Fermer' : '+ Ajouter un utilisateur' }}
      </button>
    </div>

    <div v-if="afficherFormulaire" class="card login-card mb-4">
      <div class="card-body p-4">
        <h5 class="fw-bold mb-4 text-avicenne">
          <i class="bi" :class="isEditing ? 'bi-pencil-square' : 'bi-person-plus-fill'"></i>
          {{ isEditing ? 'Modifier le profil' : 'Créer un nouvel utilisateur' }}
        </h5>
        
        <div v-if="errorMessage" class="alert alert-danger-soft mb-3 animate-pulse">
          <i class="bi bi-exclamation-triangle me-2"></i> {{ errorMessage }}
        </div>

        <form @submit.prevent="soumettreFormulaire">
          <div class="row g-3">
            <div class="col-md-3">
              <label class="form-label fw-bold small text-avicenne-dark">Prénom</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-person"></i></span>
                <input v-model="nouveauUser.prenom" type="text" class="form-control" placeholder="ex: Jean" required>
              </div>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small text-avicenne-dark">Nom</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-person-badge"></i></span>
                <input v-model="nouveauUser.nom" type="text" class="form-control" placeholder="ex: DUPONT" required>
              </div>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small text-avicenne-dark">Email</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                <input v-model="nouveauUser.email" type="email" class="form-control" placeholder="avicenne@contact.fr" required>
              </div>
            </div>

            <div class="col-md-3">
              <label class="form-label fw-bold small text-avicenne-dark">
                Mot de passe <span v-if="isEditing" class="text-muted fw-normal">(Optionnel)</span>
              </label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-key"></i></span>
                <input v-model="nouveauUser.password" type="password" class="form-control" :required="!isEditing" placeholder="••••••••">
              </div>
            </div>
            
            <div class="col-md-3">
              <label class="form-label fw-bold small text-avicenne-dark">Rôle</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-shield-lock"></i></span>
                <select v-model="nouveauUser.role" class="form-select" required>
                  <option v-for="role in rolesAutorises" :key="role" :value="role">
                    {{ role.toUpperCase() }}
                  </option>
                </select>
              </div>
            </div>

            <div class="col-md-3" v-if="nouveauUser.role !== 'admin' && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
              <label class="form-label fw-bold small text-avicenne-dark">Site</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-geo-alt"></i></span>
                <select v-model="nouveauUser.site" class="form-select" required>
                  <option value="">-- Sélectionner --</option>
                  <option v-for="site in sitesAutorises" :key="site" :value="site">
                    {{ site }}
                  </option>
                </select>
              </div>
            </div>

            <div class="col-md-3" v-if="besoinPedago && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
              <label class="form-label fw-bold small text-avicenne-dark">Programme</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-book"></i></span>
                <select v-model="nouveauUser.programme" class="form-select">
                  <option value="">-- Sélectionner --</option>
                  <option v-for="(liste, nomProg) in referentiels.matieres" :key="nomProg" :value="nomProg">
                    {{ nomProg }}
                  </option>
                </select>
              </div>
            </div>

            <div class="col-md-3" v-if="besoinPedago && !(roleUserConnecte === 'resp' && nouveauUser.role === 'tcp')">
              <label class="form-label fw-bold small text-avicenne-dark">Matière</label>
              <div class="input-group custom-group shadow-sm">
                <span class="input-group-text"><i class="bi bi-tags"></i></span>
                <select v-model="nouveauUser.matiere" class="form-select" :disabled="!nouveauUser.programme">
                  <option value="">-- Sélectionner --</option>
                  <option v-for="mat in matieresDisponibles" :key="mat" :value="mat">
                    {{ mat }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <div class="mt-4 d-flex justify-content-end gap-3">
            <button type="button" class="btn btn-link text-muted hover-underline" @click="annulerEtFermer">
              Annuler
            </button>
            <button type="submit" class="btn-avicenne-submit shadow-sm" :disabled="isSubmitting">
              <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-check-circle me-1"></i>
              {{ isEditing ? 'Mettre à jour le profil' : 'Enregistrer l\'utilisateur' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div class="row mb-4 align-items-center">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center">
          
          <div class="btn-group shadow-sm bg-white p-1" style="border-radius: 10px;">
            <button 
              @click="filtreStatut = 'tous'"
              class="btn btn-sm px-3 border-0"
              :class="filtreStatut === 'tous' ? 'btn-primary' : 'text-muted bg-transparent'">
              Tous
            </button>
            <button 
              @click="filtreStatut = 'actifs'"
              class="btn btn-sm px-3 border-0"
              :class="filtreStatut === 'actifs' ? 'btn-success' : 'text-muted bg-transparent'">
              Actifs
            </button>
            <button 
              @click="filtreStatut = 'inactifs'"
              class="btn btn-sm px-3 border-0"
              :class="filtreStatut === 'inactifs' ? 'btn-secondary' : 'text-muted bg-transparent'">
              Inactifs
            </button>
          </div>

          <button 
            v-if="roleUserConnecte === 'admin'" 
            class="btn btn-avicenne-success px-4 shadow-sm d-flex align-items-center" 
            @click="exporterUtilisateurs"
          >
            <i class="bi bi-file-earmark-excel me-2"></i>
            <span>Exporter Base (Excel)</span>
          </button>

        </div>
      </div>
    </div>

    <div class="row mb-4">
      <div class="col-12">
        <div class="input-group custom-group shadow-sm">
          <span class="input-group-text"><i class="bi bi-search"></i></span>
          <input 
            v-model="recherche" 
            type="text" 
            class="form-control" 
            placeholder="Rechercher un nom, site, email..."
          >
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="text-center my-5 py-5">
      <div class="d-flex flex-column align-items-center">
        <div class="avicenne-heart-logo animate-pulse-heart mb-3">
          <i class="bi bi-suit-heart-fill"></i>
          <i class="bi bi-activity"></i>
        </div>
        <div class="mt-2">
          <span class="text-avicenne fw-bold">Récupération des profils...</span>
          <div class="progress mt-2 mx-auto" style="width: 120px; height: 4px; border-radius: 10px; background-color: var(--primary-soft);">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                role="progressbar" 
                style="width: 100%; background-color: var(--primary-color);">
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="card shadow-avicenne border-0">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0 align-middle">
            <thead class="bg-light">
              <tr>
                <th class="ps-4" style="width: 50px;"></th>
                <th class="ps-4 th-triable" @click="changerTri('nom')">
                  NOM <i class="bi ms-1" :class="colonneTriee === 'nom' ? (ordreTri === 'asc' ? 'bi-sort-alpha-down' : 'bi-sort-alpha-up') : 'bi-hash'"></i>
                </th>
                <th class="th-triable" @click="changerTri('prenom')">
                  PRÉNOM <i class="bi ms-1" :class="colonneTriee === 'prenom' ? (ordreTri === 'asc' ? 'bi-sort-alpha-down' : 'bi-sort-alpha-up') : ''"></i>
                </th>
                <th class="th-triable" @click="changerTri('site')">
                  SITE <i class="bi ms-1" :class="colonneTriee === 'site' ? (ordreTri === 'asc' ? 'bi-sort-down' : 'bi-sort-up') : ''"></i>
                </th>
                <th class="th-triable" @click="changerTri('role')">
                  RÔLE <i class="bi ms-1" :class="colonneTriee === 'role' ? (ordreTri === 'asc' ? 'bi-filter' : 'bi-filter-right') : ''"></i>
                </th>
                <th class="th-triable d-none d-lg-table-cell" @click="changerTri('programme')">
                  PROGRAMME
                </th>
                <th class="th-triable d-none d-xl-table-cell" @click="changerTri('email')">
                  EMAIL
                </th>
                <th class="th-triable text-center" @click="changerTri('is_active')">
                  STATUT
                </th>
                <th class="text-center pe-4" v-if="peutGererUtilisateurs">
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="utilisateursTries.length === 0">
                <td colspan="8" class="text-center text-muted py-5">
                  <i class="bi bi-person-x d-block fs-2 mb-2"></i>
                  Aucun utilisateur ne correspond à votre recherche.
                </td>
              </tr>
              
              <tr v-for="user in utilisateursTries" :key="user.id">
                <td class="ps-4 text-center">
                  <span v-if="user.filiere" 
                        class="fs-5" 
                        :title="user.filiere" 
                        style="cursor: help; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">
                    {{ getEmojiFiliere(user.filiere) }}
                  </span>
                  <span v-else class="text-muted opacity-25 small">—</span>
                </td>
                <td class="ps-4 fw-bold text-avicenne-dark text-uppercase">{{ user.nom }}</td>
                <td>{{ user.prenom }}</td>
                <td>
                  <span class="badge-role">{{ user.site || 'N/A' }}</span>
                </td>
                <td>
                  <span :class="['badge-role', `badge-role-${user.role.toLowerCase()}`]">
                    {{ user.role }}
                  </span>
                </td>
                <td class="d-none d-lg-table-cell">
                  <small class="text-muted">{{ user.programme || '-' }}</small>
                  <div v-if="user.matiere" class="x-small text-primary" style="font-size: 0.7rem;">{{ user.matiere }}</div>
                </td>
                <td class="d-none d-xl-table-cell">
                  <span class="text-muted" style="font-size: 0.85rem;">{{ user.email }}</span>
                </td>
                <td class="text-center">
                  <span :class="['badge-statut', user.is_active ? 'validee' : 'brouillon']">
                    {{ user.is_active ? 'ACTIF' : 'INACTIF' }}
                  </span>
                </td>
                
                <td class="text-end pe-4" v-if="peutGererUtilisateurs">
                  <div class="d-flex justify-content-end gap-2">
                    <button 
                      class="btn-table btn-table-edit" 
                      @click="editerUtilisateur(user)"
                    >
                      Modifier
                    </button>
                    
                    <button 
                      v-if="!user.is_active"
                      class="btn-table btn-table-submit" 
                      @click="basculerStatut(user)"
                    >
                      Activer
                    </button>

                    <button 
                      v-else
                      class="btn-table btn-table-reopen" 
                      @click="basculerStatut(user)" 
                      :disabled="(user.role === 'admin' && totalAdminsActifs <= 1) || user.id === idUserConnecte"
                    >
                      Désactiver
                    </button>
                  </div>
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
/* --- BARRE DE RECHERCHE AFFINÉE --- */
.custom-group.shadow-sm {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important; /* Ombre très légère */
    border: 1px solid #e2e8f0 !important; /* Bordure fine grise */
    border-radius: 10px;
    background: white;
    transition: all 0.2s ease;
    max-width: 500px; /* Évite que la barre ne soit trop géante sur grand écran */
}

.custom-group.shadow-sm:focus-within {
    border-color: var(--primary-color) !important;
    box-shadow: 0 4px 12px rgba(67, 150, 209, 0.1) !important;
}

.custom-group .input-group-text {
    background-color: transparent !important;
    border: none !important;
    color: #a0aec0;
    padding-left: 1.25rem;
}

.custom-group .form-control {
    border: none !important;
    padding: 0.6rem 1rem; /* Hauteur plus élégante */
    font-size: 0.9rem;
}

.custom-group .form-control:focus {
    box-shadow: none !important;
}

/* --- TABLEAU & EMOJIS --- */
.filiere-table-emoji {
    font-size: 1.4rem;
    filter: drop-shadow(0 2px 3px rgba(0,0,0,0.1));
    display: inline-block;
    transition: transform 0.2s ease;
    cursor: help;
}

tr:hover .filiere-table-emoji {
    transform: scale(1.2);
}

.table td .fs-5 {
    display: inline-block;
    transform: scale(1.1);
    transition: transform 0.2s ease;
}

.table tr:hover td .fs-5 {
    transform: scale(1.3);
}

.table tbody tr td {
    padding-top: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--primary-subtle);
}

/* --- EN-TÊTES & TRI --- */
.th-triable { 
    cursor: pointer; 
    transition: all 0.2s ease;
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    vertical-align: middle;
}

.th-triable:hover { 
    background-color: var(--primary-subtle) !important; 
    color: var(--primary-color);
}

/* --- BOUTONS --- */
.btn-table {
    min-width: 100px;
    justify-content: center;
    display: inline-flex;
    align-items: center;
}

.btn-avicenne-success {
    background-color: #2D6A4F; 
    color: white;
    border: none;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.btn-avicenne-success:hover {
    background-color: #1B4332;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>