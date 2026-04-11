<script setup>
import { ref, computed, onMounted } from 'vue'
import { declarationService, missionService, authService } from '@/services/api'

// --- ÉTATS ---
const declarations = ref([])
const catalogueMissions = ref([])
const loading = ref(true)
const profilComplet = ref(true)

// Extraction des données de l'utilisateur depuis le Token
const token = localStorage.getItem('token')
let userRole = null
let currentUserId = null

if (token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
    }).join(''))
    const decoded = JSON.parse(jsonPayload)
    userRole = decoded.role
    currentUserId = decoded.id || decoded.sub 
    console.log("Token décodé - ID:", currentUserId, "Role:", userRole)
  } catch (e) {
    console.error("Erreur de décodage du token dans DeclarationsView")
  }
}

// Variables d'état pour les permissions
const isAdmin = computed(() => userRole === 'admin')
const canCreate = computed(() => userRole !== 'admin')

const showFormulaire = ref(false)
const declarationEnCours = ref({
  mois: new Date().getMonth() + 1,
  annee: new Date().getFullYear(),
  lignes: []
})

const canCreerSaisie = computed(() => {
  return canCreate.value && profilComplet.value
})

// --- ÉTATS POUR LA RECHERCHE ET LE TRI (LOGIQUE INTÉGRALE) ---
const recherche = ref('')
const colonneTriee = ref('updated_at')
const ordreTri = ref('desc')
const statutsSelectionnes = ref(['brouillon', 'soumise', 'validee'])

const changerTri = (colonne) => {
  if (colonneTriee.value === colonne) {
    ordreTri.value = ordreTri.value === 'asc' ? 'desc' : 'asc'
  } else {
    colonneTriee.value = colonne
    ordreTri.value = 'asc'
  }
}

const declarationsFiltreesEtTriees = computed(() => {
  let resultat = [...declarations.value]

  // 1. FILTRAGE PAR STATUT (Boutons toggles)
  resultat = resultat.filter(dec => statutsSelectionnes.value.includes(dec.statut))

  // 2. FILTRAGE PAR RECHERCHE TEXTUELLE
  if (recherche.value.trim() !== '') {
    const terme = recherche.value.toLowerCase().trim()
    resultat = resultat.filter(dec => {
      const auteur = `${dec.user?.prenom || ''} ${dec.user?.nom || ''}`.toLowerCase()
      const site = (dec.user?.site || '').toLowerCase()
      const role = (dec.user?.role || '').toLowerCase()
      const programme = (dec.user?.programme || '').toLowerCase()
      const matiere = (dec.user?.matiere || '').toLowerCase()
      const statut = (dec.statut || '').toLowerCase()

      return (
        auteur.includes(terme) ||
        site.includes(terme) ||
        role.includes(terme) ||
        programme.includes(terme) ||
        matiere.includes(terme) ||
        statut.includes(terme)
      )
    })
  }

  // 3. TRI (Logique intégrale)
  return resultat.sort((a, b) => {
    let valeurA, valeurB
    switch (colonneTriee.value) {
      case 'auteur':
        valeurA = `${a.user?.nom || ''} ${a.user?.prenom || ''}`.toLowerCase()
        valeurB = `${b.user?.nom || ''} ${b.user?.prenom || ''}`.toLowerCase()
        break
      case 'site':
        valeurA = (a.user?.site || '').toLowerCase()
        valeurB = (b.user?.site || '').toLowerCase()
        break
      case 'role':
        valeurA = (a.user?.role || '').toLowerCase()
        valeurB = (b.user?.role || '').toLowerCase()
        break
      case 'programme':
        valeurA = (a.user?.programme || '').toLowerCase()
        valeurB = (b.user?.programme || '').toLowerCase()
        break
      case 'matiere':
        valeurA = (a.user?.matiere || '').toLowerCase()
        valeurB = (b.user?.matiere || '').toLowerCase()
        break
      case 'total_brut':
        valeurA = a.total_remuneration || 0
        valeurB = b.total_remuneration || 0
        break
      case 'statut':
        valeurA = (a.statut || '').toLowerCase()
        valeurB = (b.statut || '').toLowerCase()
        break
      case 'updated_at':
        valeurA = new Date(a.updated_at || 0)
        valeurB = new Date(b.updated_at || 0)
        break
      case 'mois':
        // Tri chronologique intelligent (Année + Mois)
        valeurA = (a.annee * 100) + a.mois
        valeurB = (b.annee * 100) + b.mois
        break
      default:
        valeurA = ''
        valeurB = ''
    }
    if (valeurA < valeurB) return ordreTri.value === 'asc' ? -1 : 1
    if (valeurA > valeurB) return ordreTri.value === 'asc' ? 1 : -1
    return 0
  })
})
// --- CHARGEMENT DES DONNÉES ---
const chargerDonnees = async () => {
  loading.value = true
  try {
    const [mesDeclarations, toutesLesMissions, monProfil] = await Promise.all([
      declarationService.getAllDeclarations(),
      missionService.getAllMissions(),
      authService.getUserProfile()
    ])
    
    declarations.value = mesDeclarations
    catalogueMissions.value = toutesLesMissions
    
    if (monProfil) {
      const p = monProfil
      profilComplet.value = !!(
        p.email && p.telephone && p.adresse && p.code_postal && 
        p.ville && p.nss && p.iban
      )
      console.log("Check profil complet:", profilComplet.value)
    }
  } catch (error) {
    console.error("Erreur lors du chargement API:", error)
    alert("Erreur de communication avec le serveur.")
    declarations.value = []
    catalogueMissions.value = []
  } finally {
    loading.value = false 
  }
}

// --- FILTRAGE ET GROUPEMENT DES MISSIONS ---
const missionsGroupees = computed(() => {
  if (!catalogueMissions.value.length) return {}

  // On ne garde que les missions ACTIVES pour le menu déroulant du formulaire
  const missionsActives = catalogueMissions.value.filter(mission => {
    const roleMatch = /* ta logique de rôle existante... */ true; 
    return mission.is_active && roleMatch; // Ajout du check is_active
  })

  // Groupage par catégorie...
  return missionsActives.reduce((acc, mission) => {
    const cat = mission.categorie || 'Autre'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(mission)
    return acc
  }, {})
})

// --- CALCULS DE PRIX ET FORMATAGE ---
const totalDeclarationEnCours = computed(() => {
  if (!declarationEnCours.value.lignes) return 0
  return declarationEnCours.value.lignes.reduce((acc, ligne) => {
    const mission = catalogueMissions.value.find(m => m.id === ligne.mission_id)
    const tarif = mission ? (mission.tarif_unitaire || 0) : 0
    return acc + ((ligne.quantite || 0) * tarif)
  }, 0)
})

const formatPrix = (prix) => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(prix || 0)
}

const nomMois = (num) => {
  return new Date(2026, num - 1).toLocaleString('fr-FR', { month: 'long' })
}

// --- ACTIONS DU FORMULAIRE ---
const ajouterLigne = () => {
  if (!declarationEnCours.value.lignes) declarationEnCours.value.lignes = []
  declarationEnCours.value.lignes.push({ mission_id: null, quantite: 1 })
}

const retirerLigne = (index) => {
  declarationEnCours.value.lignes.splice(index, 1)
}

const validerEtEnvoyer = async () => {
  if (declarationEnCours.value.lignes.length === 0) {
    alert("Vous devez ajouter au moins une mission.")
    return
  }
  try {
    if (declarationEnCours.value.id) {
      await declarationService.updateDeclaration(declarationEnCours.value.id, declarationEnCours.value)
      alert("Brouillon mis à jour avec succès !")
    } else {
      await declarationService.createDeclaration(declarationEnCours.value)
      alert("Déclaration enregistrée en brouillon !")
    }
    showFormulaire.value = false
    declarationEnCours.value = { mois: new Date().getMonth() + 1, annee: new Date().getFullYear(), lignes: [] }
    chargerDonnees()
  } catch (error) {
    alert("Erreur lors de l'enregistrement: " + error.message)
  }
}

const soumettreAction = async (id) => {
  if (!confirm("Voulez-vous soumettre cette déclaration ? Elle ne sera plus modifiable.")) return
  try {
    const idNettoye = String(id).replace(':', '')
    await declarationService.soumettreDeclaration(idNettoye)
    alert("Déclaration soumise avec succès !")
    chargerDonnees()
  } catch (error) {
    alert("Erreur de soumission: " + error.message)
  }
}

const peutSoumettre = (dec) => {
  const maintenant = new Date()
  const anneeActuelle = maintenant.getFullYear()
  const moisActuel = maintenant.getMonth() + 1
  const jourActuel = maintenant.getDate()
  if (dec.annee < anneeActuelle) return true
  if (dec.annee === anneeActuelle && dec.mois < moisActuel) return true
  if (dec.annee === anneeActuelle && dec.mois === moisActuel) return jourActuel >= 20
  return false
}

// --- ADMIN REVIEW ET RÉOUVERTURE ---
const showModaleReview = ref(false)
const declarationAValider = ref(null)
const reviewForm = ref({ statut: 'validee', commentaire_refus: '' })

const ouvrirModaleReview = (declaration) => {
  declarationAValider.value = declaration
  reviewForm.value = { statut: 'validee', commentaire_refus: '' }
  showModaleReview.value = true
}

const validerDecision = async () => {
  if (reviewForm.value.statut === 'brouillon' && !reviewForm.value.commentaire_refus.trim()) {
    alert("Le motif est obligatoire pour un rejet.")
    return
  }
  try {
    await declarationService.reviewDeclaration(declarationAValider.value.id, {
      statut: reviewForm.value.statut,
      commentaire_refus: reviewForm.value.statut === 'brouillon' ? reviewForm.value.commentaire_refus : null
    })
    showModaleReview.value = false
    chargerDonnees()
  } catch (error) {
    alert("Erreur validation: " + error.message)
  }
}

const reouvrirDeclaration = async (dec) => {
  if (!confirm("Voulez-vous vraiment réouvrir cette déclaration validée ?")) return
  const motif = prompt("Motif obligatoire de la réouverture :")
  if (!motif || !motif.trim()) {
    alert("Action annulée : motif manquant.")
    return
  }
  try {
    await declarationService.reviewDeclaration(dec.id, {
      statut: 'brouillon',
      commentaire_refus: `[Réouverture Admin] ${motif}`
    })
    alert("Déclaration réouverte avec succès.")
    chargerDonnees()
  } catch (error) {
    alert("Erreur lors de la réouverture: " + error.message)
  }
}

// --- CONSULTATION ET ÉDITION ---
const showModaleVoir = ref(false)
const declarationConsultee = ref(null)

const ouvrirModaleVoir = (declaration) => {
  declarationConsultee.value = declaration
  showModaleVoir.value = true
}

const chargerBrouillonPourEdition = (declaration) => {
  const lignesNettoyees = declaration.lignes.map(ligne => ({
    mission_id: ligne.mission_id,
    quantite: ligne.quantite
  }))
  declarationEnCours.value = {
    id: String(declaration.id).replace(':', ''),
    mois: declaration.mois,
    annee: declaration.annee,
    lignes: lignesNettoyees
  }
  showFormulaire.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

const getNomMission = (missionId) => {
  const mission = catalogueMissions.value.find(m => m.id === missionId)
  if (!mission) return `Mission #${missionId} (Supprimée du système)`
  
  if (!mission.is_active) {
    return `${mission.titre} (Archivée)`
  }
  return mission.titre
}

const getInfoMission = (declaration, cle) => {
  if (!declaration.lignes || declaration.lignes.length === 0) return 'N/A'
  const missionId = declaration.lignes[0].mission_id
  const mission = catalogueMissions.value.find(m => m.id === missionId)
  if (!mission) return 'N/A'
  if (cle === 'titre') console.warn("DEBUG INFO MISSION:", mission)
  return mission[cle] || 'N/A'
}

const toggleFiltreStatut = (statut) => {
  const index = statutsSelectionnes.value.indexOf(statut)
  if (index > -1) {
    // On retire le statut s'il y est, mais on en garde au moins un
    if (statutsSelectionnes.value.length > 1) {
      statutsSelectionnes.value.splice(index, 1)
    }
  } else {
    statutsSelectionnes.value.push(statut)
  }
}

onMounted(async () => {
  try {
    await chargerDonnees()
  } catch (e) {
    console.error("Crash onMounted DeclarationsView:", e)
  } finally {
    loading.value = false 
  }
})
</script>

<template>
  <div class="p-4 p-md-5">
    
    <div class="d-flex justify-content-between align-items-center mb-5">
      <div>
        <h1 class="h1-avicenne">Suivi des Déclarations</h1>
        <p class="text-muted">Saisissez et pilotez les déclarations mensuelles.</p>
      </div>
      <button v-if="canCreate" @click="showFormulaire = !showFormulaire" class="btn shadow-sm px-4" :class="showFormulaire ? 'btn-outline-danger' : 'btn-avicenne-submit'">
        {{ showFormulaire ? '✕ Annuler' : '＋ Nouvelle Déclaration' }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary mb-3"></div>
      <p class="text-muted">Chargement en cours...</p>
    </div>

    <div v-else>
      <div class="row mb-4 align-items-center">
        <div class="col-md-8">
          <div class="d-flex gap-2">
            <div class="btn-group shadow-sm bg-white rounded-3 p-1">
              <button 
                @click="toggleFiltreStatut('brouillon')"
                class="btn btn-sm px-3 border-0"
                :class="statutsSelectionnes.includes('brouillon') ? 'btn-secondary' : 'text-muted bg-transparent'">
                Brouillons
              </button>
              <button 
                @click="toggleFiltreStatut('soumise')"
                class="btn btn-sm px-3 border-0"
                :class="statutsSelectionnes.includes('soumise') ? 'btn-primary' : 'text-muted bg-transparent'">
                Soumises
              </button>
              <button 
                @click="toggleFiltreStatut('validee')"
                class="btn btn-sm px-3 border-0"
                :class="statutsSelectionnes.includes('validee') ? 'btn-success' : 'text-muted bg-transparent'">
                Validées
              </button>
            </div>
            
            <span class="text-muted small align-self-center ms-2">
              {{ declarationsFiltreesEtTriees.length }} résultat(s)
            </span>
          </div>
        </div>

        <div class="col-md-4">
          <div class="input-group custom-group shadow-sm">
            <span class="input-group-text bg-white border-end-0">
              <i class="bi bi-search text-muted"></i>
            </span>
            <input 
              v-model="recherche" 
              type="text" 
              class="form-control border-start-0" 
              placeholder="Rechercher...">
            <button 
              v-if="recherche" 
              class="btn btn-white border-start-0 text-muted" 
              @click="recherche = ''">✕</button>
          </div>
        </div>
      </div>

      <div v-if="showFormulaire && canCreate" class="card login-card mb-5 animate__animated animate__fadeIn border-2 border-primary">
        <div class="card-body p-4">
          <h3 class="h5 fw-bold mb-4" style="color: var(--avicenne-blue)">{{ declarationEnCours.id ? 'Modifier la Déclaration' : 'Nouvelle Déclaration' }}</h3>
          
          <div class="row g-3 mb-4 border-bottom pb-4">
            <div class="col-md-3">
              <label class="form-label small fw-bold">MOIS</label>
              <select v-model="declarationEnCours.mois" class="form-select border-2">
                <option v-for="m in 12" :key="m" :value="m">{{ new Date(2026, m - 1).toLocaleString('fr-FR', { month: 'long' }) }}</option>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label small fw-bold">ANNÉE</label>
              <input v-model.number="declarationEnCours.annee" type="number" class="form-control border-2" min="2025" max="2030" />
            </div>
          </div>

          <h4 class="h6 fw-bold text-muted mb-3 text-uppercase">Missions effectuées :</h4>
          <div v-for="(ligne, index) in declarationEnCours.lignes" :key="index" class="row g-2 mb-3 align-items-end bg-light p-3 rounded">
            <div class="col-md-7">
              <label class="form-label small">Mission</label>
              <select v-model="ligne.mission_id" class="form-select" required>
                <option :value="null" disabled>-- Choisir --</option>
                <optgroup v-for="(missions, cat) in missionsGroupees" :key="cat" :label="cat">
                  <option v-for="m in missions" :key="m.id" :value="m.id">{{ m.titre }} ({{ m.tarif_unitaire }}€)</option>
                </optgroup>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label small">Quantité</label>
              <input v-model.number="ligne.quantite" type="number" step="0.5" class="form-control" />
            </div>
            <div class="col-md-2">
              <button @click="retirerLigne(index)" class="btn btn-outline-danger w-100"><i class="bi bi-trash"></i></button>
            </div>
          </div>

          <div class="d-flex justify-content-between mt-4">
            <button @click="ajouterLigne" class="btn btn-outline-primary px-4">＋ Ajouter</button>
            <button @click="validerEtEnvoyer" class="btn btn-avicenne-submit px-5" :disabled="declarationEnCours.lignes.length === 0">
              💾 {{ declarationEnCours.id ? 'Mettre à jour' : 'Enregistrer' }}
            </button>
          </div>
        </div>
      </div>

      <div class="card shadow-avicenne border-0 rounded-4 overflow-hidden">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead style="background-color: #f8fafc; border-bottom: 2px solid var(--avicenne-blue);">
              <tr class="small text-uppercase">
                <th v-if="['admin', 'coordo', 'resp', 'top_com'].includes(userRole)" @click="changerTri('auteur')" class="px-4 py-3 cursor-pointer text-avicenne">Auteur ↑↓</th>
                <th @click="changerTri('site')" class="px-4 py-3 cursor-pointer text-avicenne">Site</th>
                <th @click="changerTri('role')" class="px-4 py-3 cursor-pointer text-avicenne">Rôle</th>
                <th @click="changerTri('programme')" class="px-4 py-3 cursor-pointer text-avicenne">Programme</th>
                <th @click="changerTri('matiere')" class="px-4 py-3 cursor-pointer text-avicenne">Matière</th>
                <th @click="changerTri('total_brut')" class="px-4 py-3 cursor-pointer text-avicenne fw-bold">Total Brut</th>
                <th @click="changerTri('statut')" class="px-4 py-3 cursor-pointer text-avicenne text-center">Statut</th>
                <th @click="changerTri('mois')" class="px-4 py-3 cursor-pointer text-avicenne">Période</th>
                <th class="px-4 py-3 text-end text-avicenne">Actions</th>
              </tr>
            </thead>
            <tbody class="text-avicenne-dark">
              <tr v-for="dec in declarationsFiltreesEtTriees" :key="dec.id">
                <td v-if="['admin', 'coordo', 'resp', 'top_com'].includes(userRole)" class="px-4 fw-bold">
                  {{ dec.user?.prenom }} {{ dec.user?.nom }}
                </td>
                <td class="px-4">{{ dec.user?.site || 'N/A' }}</td>
                <td class="px-4">
                  <span class="badge-role" 
                      :class="{
                          'badge-role-admin': dec.user?.role === 'admin',
                          'badge-role-coordo': dec.user?.role === 'coordo',
                          'badge-role-resp': dec.user?.role === 'resp'
                      }">
                    {{ dec.user?.role }}
                </span>
                </td>
                <td class="px-4 small">{{ dec.user?.programme || 'N/A' }}</td>
                <td class="px-4 small">{{ dec.user?.matiere || 'N/A' }}</td>
                <td class="px-4 fw-bold">{{ dec.total_remuneration.toFixed(2) }} €</td>
                <td class="px-4 text-center">
                  <span class="badge-statut" :class="dec.statut">{{ dec.statut.toUpperCase() }}</span>
                </td>
                <td class="px-4 fw-bold text-capitalize">{{ nomMois(dec.mois) }} {{ dec.annee }}</td>
                <td class="px-4 text-end">
                  <div class="d-flex justify-content-end gap-2">
                    
                    <button v-if="dec.statut === 'brouillon' && canCreate" 
                            @click="chargerBrouillonPourEdition(dec)" 
                            class="btn-table btn-table-edit">
                      Modifier
                    </button>

                    <button v-if="dec.statut === 'brouillon' && canCreate" 
                            @click="soumettreAction(dec.id)" 
                            :disabled="!peutSoumettre(dec)"
                            class="btn-table btn-table-submit">
                      Soumettre
                    </button>

                    <button @click="ouvrirModaleVoir(dec)" 
                            class="btn-table btn-table-view">
                      Visualiser
                    </button>
                    
                    <button v-if="dec.statut === 'soumise' && isAdmin" 
                            @click="ouvrirModaleReview(dec)" 
                            class="btn-table btn-table-evaluate">
                      Évaluer
                    </button>

                    <button v-if="dec.statut === 'validee' && isAdmin" 
                            @click="reouvrirDeclaration(dec)" 
                            class="btn-table btn-table-reopen">
                      Réouvrir
                    </button>

                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="showModaleReview" class="modal-backdrop-custom">
      <div class="card login-card p-4 shadow-lg w-100" style="max-width: 500px;">
        <h3 class="h5 fw-bold mb-4" style="color: var(--avicenne-blue)">Traiter la déclaration</h3>
        <div class="mb-4">
          <div class="form-check mb-2">
            <input type="radio" v-model="reviewForm.statut" value="validee" class="form-check-input" id="v"/><label class="form-check-label text-success fw-bold" for="v">Valider</label>
          </div>
          <div class="form-check">
            <input type="radio" v-model="reviewForm.statut" value="brouillon" class="form-check-input" id="r"/><label class="form-check-label text-danger fw-bold" for="r">Rejeter</label>
          </div>
        </div>
        <textarea v-model="reviewForm.commentaire_refus" class="form-control mb-4" rows="3" placeholder="Commentaire..."></textarea>
        <div class="d-flex justify-content-end gap-2">
          <button @click="showModaleReview = false" class="btn btn-light border">Annuler</button>
          <button @click="validerDecision" class="btn btn-avicenne-submit">Confirmer</button>
        </div>
      </div>
    </div>

    <div v-if="showModaleVoir" class="modal-backdrop-custom">
      <div class="card login-card p-0 shadow-lg w-100 overflow-hidden" style="max-width: 900px; border: none;">        
        <div class="px-4 py-3 text-white d-flex justify-content-end" style="background-color: var(--avicenne-blue)">
          <button @click="showModaleVoir = false" class="btn-close btn-close-white"></button>
        </div>

        <div class="p-4">
          <div class="d-flex align-items-center mb-4 border-bottom pb-3">
            <i class="bi bi-file-earmark-text me-3 fs-3 text-avicenne"></i>
            <div>
              <h3 class="h4 fw-bold mb-0 text-avicenne-dark">Détail de la déclaration</h3>
              <p class="text-muted small mb-0">Récapitulatif officiel des missions et tarifs</p>
            </div>
          </div>

          <div class="bg-light p-3 rounded mb-4 row g-2 small border-start border-4" style="border-color: var(--avicenne-blue) !important;">
            <div class="col-6"><strong>Auteur :</strong> {{ declarationConsultee?.user?.prenom }} {{ declarationConsultee?.user?.nom }}</div>
            <div class="col-6 text-capitalize"><strong>Période :</strong> {{ nomMois(declarationConsultee?.mois) }} {{ declarationConsultee?.annee }}</div>
            <div class="col-6"><strong>Total :</strong> <span class="fw-bold">{{ declarationConsultee?.total_remuneration.toFixed(2) }} €</span></div>
            <div class="col-6"><strong>Statut :</strong> <span class="badge-statut" :class="declarationConsultee?.statut">{{ declarationConsultee?.statut?.toUpperCase() }}</span></div>
          </div>

          <div class="table-responsive">
            <table class="table table-sm align-middle">
              <thead>
                <tr class="small text-uppercase" style="color: var(--avicenne-blue); border-bottom: 2px solid #eee;">
                  <th>Mission</th>
                  <th class="text-center">Qté</th>
                  <th class="text-end">Tarif</th>
                  <th class="text-end">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="ligne in declarationConsultee?.lignes" :key="ligne.id" class="text-avicenne-dark">
                  <td class="small py-2">{{ getNomMission(ligne.mission_id) }}</td>
                  <td class="text-center">{{ ligne.quantite }}</td>
                  <td class="text-end text-muted">{{ (ligne.tarif_applique || 0).toFixed(2) }} €</td>
                  <td class="text-end fw-semibold">{{ ((ligne.quantite || 0) * (ligne.tarif_applique || 0)).toFixed(2) }} €</td>
                </tr>
              </tbody>
              <tfoot class="border-top-2">
                <tr class="text-avicenne-dark" style="background-color: #f8fafc;">
                  <td colspan="3" class="text-end fw-bold py-3">MONTANT TOTAL À PERCEVOIR :</td>
                  <td class="text-end fw-bold py-3 fs-5 text-avicenne">
                    {{ (declarationConsultee?.total_remuneration || 0).toFixed(2) }} €
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div class="text-end mt-4">
            <button @click="showModaleVoir = false" class="btn btn-avicenne-submit px-5">Fermer</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
