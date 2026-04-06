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
    currentUserId = decoded.id || decoded.sub // Selon comment est nommé l'ID dans ton JWT
  } catch (e) {
    console.error("Erreur de décodage du token")
  }
}

// Variables d'état
const isAdmin = computed(() => userRole === 'admin')
const canCreate = computed(() => userRole !== 'admin') // L'admin ne crée pas de déclarations

const showFormulaire = ref(false)
const declarationEnCours = ref({
  mois: new Date().getMonth() + 1,
  annee: new Date().getFullYear(),
  lignes: []
})

const canCreerSaisie = computed(() => {
  return canCreate.value && profilComplet.value
})

// --- ÉTATS POUR LA RECHERCHE ET LE TRI ---
const recherche = ref('')
const colonneTriee = ref('updated_at') // Tri par défaut sur la date de mise à jour
const ordreTri = ref('desc') // Du plus récent au plus ancien par défaut

// Fonction pour changer la colonne de tri
const changerTri = (colonne) => {
  if (colonneTriee.value === colonne) {
    ordreTri.value = ordreTri.value === 'asc' ? 'desc' : 'asc'
  } else {
    colonneTriee.value = colonne
    ordreTri.value = 'asc'
  }
}

// 🔥 Filtrage et Tri combinés des déclarations
const declarationsFiltreesEtTriees = computed(() => {
  let resultat = [...declarations.value]

  // 1. Recherche dynamique
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

  // 2. Tri dynamique
  return resultat.sort((a, b) => {
    let valeurA, valeurB

    // Récupération des valeurs selon la colonne ciblée
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
      default:
        valeurA = ''
        valeurB = ''
    }

    // Comparaison
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
      authService.getUserProfile() // 🔥 On utilise le bon service ici !
    ])
    
    declarations.value = mesDeclarations
    catalogueMissions.value = toutesLesMissions
    
    // 🚨 VÉRIFICATION DU PROFIL COMPLET
    if (monProfil) {
      const p = monProfil
      profilComplet.value = !!(
        p.email && 
        p.telephone && 
        p.adresse && 
        p.code_postal && 
        p.ville && 
        p.nss &&
        p.iban
      )
    }
    
    console.log("Mes déclarations reçues :", mesDeclarations)
  } catch (error) {
    console.error("Erreur lors du chargement :", error)
    alert("Erreur de communication avec le serveur.")
    
    declarations.value = []
    catalogueMissions.value = []
  } finally {
    loading.value = false 
  }
}

// --- 🎯 FILTRAGE ET GROUPEMENT DES MISSIONS SELON LE RÔLE ---
const missionsGroupees = computed(() => {
  // 💡 Sécurité : Si catalogueMissions n'est pas un tableau ou est vide, on renvoie un objet vide
  if (!Array.isArray(catalogueMissions.value) || catalogueMissions.value.length === 0) {
    return {}
  }

  // 1. Filtrage selon le catalogue autorisé
  const missionsFiltrees = catalogueMissions.value.filter(mission => {
    if (!mission) return false // Sécurité si la mission est nulle
    
    if (['coordo', 'top_com', 'top'].includes(userRole)) {
      return mission.type_contrat === 'CDDU' || mission.type_contrat === 'BOTH'
    } else if (['resp', 'tcp'].includes(userRole)) {
      return mission.type_contrat === 'CCDA' || mission.type_contrat === 'BOTH'
    }
    return false
  })

  // 2. Groupement par catégorie
  return missionsFiltrees.reduce((acc, mission) => {
    const cat = mission.categorie || 'Autre' // Sécurité si pas de catégorie
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(mission)
    return acc
  }, {})
})

// --- ACTIONS DU FORMULAIRE ---
const ajouterLigne = () => {
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
    // Si la déclaration a un ID, c'est qu'on modifie un brouillon existant
    if (declarationEnCours.value.id) {
      // ⚠️ ATTENTION : Vérifie bien que "updateDeclaration" est le nom exact dans ton declarationService
      await declarationService.updateDeclaration(declarationEnCours.value.id, declarationEnCours.value)
      alert("Brouillon mis à jour avec succès !")
    } else {
      // Sinon, on crée une toute nouvelle déclaration
      await declarationService.createDeclaration(declarationEnCours.value)
      alert("Déclaration enregistrée en brouillon !")
    }
    
    // On ferme le formulaire et on réinitialise l'état
    showFormulaire.value = false
    declarationEnCours.value = {
      mois: new Date().getMonth() + 1,
      annee: new Date().getFullYear(),
      lignes: []
    }
    chargerDonnees() // On recharge le tableau
    
  } catch (error) {
    alert(error.message)
  }
}

const soumettreAction = async (id) => {
  try {
    const idNettoye = String(id).replace(':', '')
    
    await declarationService.soumettreDeclaration(idNettoye)
    alert("Déclaration soumise avec succès !")
    chargerDonnees()
  } catch (error) {
    alert(error.message)
  }
}

// --- ⏱️ VÉRIFICATION DE LA RÈGLE DU 20 DU MOIS ---
const peutSoumettre = (dec) => {
  const maintenant = new Date()
  const anneeActuelle = maintenant.getFullYear()
  const moisActuel = maintenant.getMonth() + 1 // getMonth() va de 0 à 11
  const jourActuel = maintenant.getDate()

  // CAS 1 : C'est une déclaration d'une année passée -> Open bar, on peut soumettre !
  if (dec.annee < anneeActuelle) return true

  // CAS 2 : C'est une déclaration d'un mois passé de cette année (ex: Mars alors qu'on est en Avril)
  // -> Open bar aussi pour les retardataires !
  if (dec.annee === anneeActuelle && dec.mois < moisActuel) return true

  // CAS 3 : C'est la déclaration du mois en cours (ex: Avril et on est en Avril)
  // -> On applique STRICTEMENT la règle du 20 du mois.
  if (dec.annee === anneeActuelle && dec.mois === moisActuel) {
    return jourActuel >= 20
  }

  // Par défaut (si la date est dans le futur par exemple), on bloque
  return false
}

// --- ÉTATS POUR LA MODALE DE VALIDATION ---
const showModaleReview = ref(false)
const declarationAValider = ref(null)
const reviewForm = ref({
  statut: 'validee', // Par défaut sur validation
  commentaire_refus: ''
})

// Ouvre la modale en ciblant une déclaration
const ouvrirModaleReview = (declaration) => {
  declarationAValider.value = declaration
  reviewForm.value = {
    statut: 'validee',
    commentaire_refus: ''
  }
  showModaleReview.value = true
}

// Soumission de la décision au Backend
const validerDecision = async () => {
  // Vérification si rejet sans motif
  if (reviewForm.value.statut === 'brouillon' && !reviewForm.value.commentaire_refus.trim()) {
    alert("Vous devez obligatoirement saisir un motif d'explication pour rejeter cette déclaration.")
    return
  }

  try {
    await declarationService.reviewDeclaration(declarationAValider.value.id, {
      statut: reviewForm.value.statut,
      commentaire_refus: reviewForm.value.statut === 'brouillon' ? reviewForm.value.commentaire_refus : null
    })
    
    alert(reviewForm.value.statut === 'validee' ? "Déclaration validée !" : "Déclaration renvoyée en brouillon à l'utilisateur.")
    showModaleReview.value = false
    chargerDonnees() // On rafraîchit le tableau
  } catch (error) {
    alert(error.message)
  }
}

// Fonction spéciale "Super Admin" pour forcer la réouverture d'un dossier validé
const reouvrirDeclaration = async (dec) => {
  if (!confirm("Voulez-vous vraiment réouvrir cette déclaration validée et la renvoyer en brouillon ?")) return
  
  const motif = prompt("Motif obligatoire de la réouverture :")
  if (!motif || !motif.trim()) {
    alert("Action annu  lée : Le motif est obligatoire.")
    return
  }

  try {
    await declarationService.reviewDeclaration(dec.id, {
      statut: 'brouillon',
      commentaire_refus: `[Réouverture Admin] ${motif}`
    })
    alert("Déclaration réouverte et renvoyée en brouillon.")
    chargerDonnees()
  } catch (error) {
    alert(error.message)
  }
}

// --- 1. POUR CONSULTER ---
const showModaleVoir = ref(false)
const declarationConsultee = ref(null)

const ouvrirModaleVoir = (declaration) => {
  declarationConsultee.value = declaration
  showModaleVoir.value = true
}

// --- 2. POUR MODIFIER / COMPLÉTER  ---
const chargerBrouillonPourEdition = (declaration) => {
  console.log("Tentative d'édition de la déclaration :", declaration)

  // 1. On nettoie les lignes pour ne garder QUE ce dont le formulaire a besoin
  const lignesNettoyees = declaration.lignes.map(ligne => ({
    mission_id: ligne.mission_id,
    quantite: ligne.quantite
  }))

  // 2. On injecte les données propres dans le formulaire
  declarationEnCours.value = {
    id: String(declaration.id).replace(':', ''),
    mois: declaration.mois,
    annee: declaration.annee,
    lignes: lignesNettoyees
  }

  // 3. On affiche le formulaire et on remonte la page
  showFormulaire.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Fonction pour récupérer le titre d'une mission à partir de son ID
const getNomMission = (missionId) => {
  const mission = catalogueMissions.value.find(m => m.id === missionId)
  return mission ? mission.titre : `Mission #${missionId}`
}

// Fonction pour extraire le programme ou la matière de la première mission d'une déclaration
const getInfoMission = (declaration, cle) => {
  if (!declaration.lignes || declaration.lignes.length === 0) return 'N/A'
  
  const missionId = declaration.lignes[0].mission_id
  if (!catalogueMissions.value || catalogueMissions.value.length === 0) return '...'
  
  const mission = catalogueMissions.value.find(m => m.id === missionId)
  
  if (!mission) return 'N/A'

  // 🔥 ON CHANGE LE LOG ICI POUR LE METTRE EN ORANGE/JAUNE BIEN VISIBLE
  console.warn("TROUVÉ ! Voici la mission complète :", mission)

  return mission[cle] || 'N/A'
}

// 💡 ON AJOUTE / CORRIGE LE ONMOUNTED ICI :
onMounted(async () => {
  try {
    await chargerDonnees()
  } catch (e) {
    console.error("Erreur au montage du composant :", e)
  } finally {
    // Le coup de grâce pour être sûr que l'écran se débloque !
    loading.value = false 
  }
})
</script>

<template>
  <div class="p-6">
    
    <div class="mb-6 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Suivi des Déclarations</h1>
        <p class="text-gray-600">Saisissez et pilotez les déclarations mensuelles.</p>
      </div>
      
      <button 
        v-if="canCreate"
        @click="showFormulaire = !showFormulaire" 
        class="btn"
        :class="showFormulaire ? 'btn-secondary' : 'btn-primary'"
      >
        {{ showFormulaire ? '❌ Annuler' : '➕ Nouvelle Déclaration' }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-10">
      <span class="text-gray-500 text-lg">Chargement de vos données en cours...</span>
    </div>

    <div v-else>
      <div class="row mb-3">
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
              placeholder="Rechercher un auteur, site, rôle..."
            >
            <button v-if="recherche" class="btn btn-outline-secondary" type="button" @click="recherche = ''">✖</button>
          </div>
        </div>
      </div>
      <div v-if="showFormulaire && canCreate" class="bg-white p-6 rounded-lg shadow mb-6 border-2 border-primary">
        <h3 class="text-lg font-bold mb-4 text-primary">
          {{ declarationEnCours.id ? 'Modifier la Déclaration' : 'Nouvelle Déclaration' }}
        </h3>
        
        <div class="row g-3 mb-4">
          <div class="col-md-3">
            <label class="form-label font-medium text-gray-700">Mois</label>
            <select v-model="declarationEnCours.mois" class="form-select">
              <option v-for="m in 12" :key="m" :value="m">
                {{ new Date(2026, m - 1).toLocaleString('fr-FR', { month: 'long' }) }}
              </option>
            </select>
          </div>
          
          <div class="col-md-3">
            <label class="form-label font-medium text-gray-700">Année</label>
            <input v-model.number="declarationEnCours.annee" type="number" class="form-control" min="2025" max="2030" />
          </div>
        </div>

        <h4 class="text-md font-semibold text-gray-700 mb-3">Missions effectuées :</h4>

        <div v-for="(ligne, index) in declarationEnCours.lignes" :key="index" class="row g-2 mb-3 align-items-end border-bottom pb-3">
          
          <div class="col-md-7">
            <label class="form-label text-sm text-gray-600">Sélectionnez la mission</label>
            <select v-model="ligne.mission_id" class="form-select" required>
              <option :value="null" disabled>-- Choisir une mission --</option>
              <optgroup v-for="(missions, categorie) in missionsGroupees" :key="categorie" :label="categorie">
                <option v-for="m in missions" :key="m.id" :value="m.id">
                  {{ m.titre }} ({{ m.tarif_unitaire }}€ / {{ m.unite }})
                </option>
              </optgroup>
            </select>
          </div>

          <div class="col-md-3">
            <label class="form-label text-sm text-gray-600">Quantité</label>
            <input v-model.number="ligne.quantite" type="number" step="0.5" min="0.5" class="form-control" placeholder="Ex: 2.5" />
          </div>

          <div class="col-md-2">
            <button @click="retirerLigne(index)" class="btn btn-outline-danger w-100">🗑️ Supprimer</button>
          </div>
        </div>

        <div class="d-flex justify-content-between mt-4">
          <button @click="ajouterLigne" class="btn btn-outline-primary">
            ➕ Ajouter une ligne
          </button>
          
          <button 
            @click="validerEtEnvoyer" 
            class="btn btn-success"
            :disabled="declarationEnCours.lignes.length === 0"
          >
            💾 {{ declarationEnCours.id ? 'Mettre à jour le Brouillon' : 'Enregistrer en Brouillon' }}
          </button>
        </div>
      </div>


      <div v-if="declarations.length === 0" class="text-center py-10 bg-white rounded-lg shadow">
        <span class="text-gray-500">Aucune déclaration trouvée.</span>
      </div>

      <div v-else class="overflow-x-auto bg-white rounded-lg shadow">
        <table class="min-w-full table-auto">
            <thead class="bg-gray-50 border-b">
                <tr>
                <th v-if="['admin', 'coordo', 'resp', 'top_com'].includes(userRole)" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('auteur')">
                  Auteur <span class="ms-1">{{ colonneTriee === 'auteur' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('site')">
                  Site <span class="ms-1">{{ colonneTriee === 'site' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('role')">
                  Rôle <span class="ms-1">{{ colonneTriee === 'role' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('programme')">
                  Programme <span class="ms-1">{{ colonneTriee === 'programme' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('matiere')">
                  Matière <span class="ms-1">{{ colonneTriee === 'matiere' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('total_brut')">
                  Total Brut <span class="ms-1">{{ colonneTriee === 'total_brut' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('statut')">
                  Statut <span class="ms-1">{{ colonneTriee === 'statut' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" @click="changerTri('updated_at')">
                  Dernière MàJ <span class="ms-1">{{ colonneTriee === 'updated_at' ? (ordreTri === 'asc' ? '▲' : '▼') : '' }}</span>
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
            </thead>
            
            <tbody class="divide-y divide-gray-200">
                <tr v-for="dec in declarationsFiltreesEtTriees" :key="dec.id" class="hover:bg-gray-50 transition-colors">
                
                <td v-if="['admin', 'coordo', 'resp', 'top_com'].includes(userRole)" class="px-6 py-4 text-sm font-medium text-gray-700">
                    <span v-if="dec.user?.prenom || dec.user?.nom">
                        {{ dec.user?.prenom }} {{ dec.user?.nom }}
                    </span>
                    <span v-else class="text-gray-400">Utilisateur #{{ dec.user_id }}</span>
                </td>

                <td class="px-6 py-4 text-sm text-gray-700">
                    {{ dec.user?.site || 'N/A' }}
                </td>

                <td class="px-6 py-4 text-sm text-gray-700 capitalize">
                    {{ dec.user?.role || 'N/A' }}
                </td>

                <td class="px-6 py-4 text-sm text-gray-700">
                    {{ dec.user?.programme || 'N/A' }}
                </td>

                <td class="px-6 py-4 text-sm text-gray-700">
                    {{ dec.user?.matiere || 'N/A' }}
                </td>
                                
                <td class="px-6 py-4 text-sm font-bold text-green-600">
                    {{ dec.total_remuneration.toFixed(2) }} €
                </td>
                
                <td class="px-6 py-4 text-sm">
                    <span 
                    class="px-2 py-1 rounded-full text-xs font-semibold"
                    :class="{
                        'bg-yellow-100 text-yellow-800': dec.statut === 'brouillon',
                        'bg-blue-100 text-blue-800': dec.statut === 'soumise',
                        'bg-green-100 text-green-800': dec.statut === 'validee'
                    }"
                    >
                    {{ dec.statut.toUpperCase() }}
                    </span>
                </td>

                <td class="px-6 py-4 text-sm text-gray-500">
                    {{ new Date(dec.updated_at).toLocaleDateString('fr-FR') }}
                </td>
                
                <td class="px-6 py-4 text-sm d-flex gap-2">
                    <button v-if="dec.statut === 'brouillon' && canCreate" @click="chargerBrouillonPourEdition(dec)" class="btn btn-sm btn-outline-primary">✏️ Modifier</button>
                    <button v-if="dec.statut === 'brouillon' && (!dec.user_id || dec.user_id == currentUserId)" @click="soumettreAction(dec.id)" class="btn btn-sm btn-success" :disabled="!peutSoumettre(dec)">🚀 Soumettre</button>
                    <button @click="ouvrirModaleVoir(dec)" class="btn btn-sm btn-outline-secondary">👁️ Voir</button>
                    <button v-if="dec.statut === 'soumise' && ['admin', 'coordo', 'top_com'].includes(userRole)" @click="ouvrirModaleReview(dec)" class="btn btn-sm btn-primary">⚖️ Évaluer</button>
                    <button v-if="dec.statut === 'validee' && isAdmin" @click="reouvrirDeclaration(dec)" class="btn btn-sm btn-outline-danger">🔓 Réouvrir</button>
                </td>

                </tr>
            </tbody>
            </table>
      </div>

    </div>

    <div v-if="showModaleReview" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" style="background: rgba(0,0,0,0.5); z-index: 1050;">
      <div class="bg-white p-6 rounded-lg shadow-lg" style="width: 500px; max-width: 90%;">
        
        <h3 class="text-lg font-bold mb-2">Traiter la déclaration</h3>
        <p class="text-sm text-gray-600 mb-4">
          Vous évaluez la déclaration de l'utilisateur #{{ declarationAValider?.user_id }} pour le mois de {{ new Date(2026, declarationAValider?.mois - 1).toLocaleString('fr-FR', { month: 'long' }) }}.
        </p>

        <div class="mb-4">
          <label class="form-label font-medium">Décision :</label>
          <div class="d-flex gap-4 mt-2">
            <label class="d-flex align-items-center gap-2 cursor-pointer">
              <input type="radio" v-model="reviewForm.statut" value="validee" class="form-check-input" />
              <span class="text-green-600 font-semibold">Valider la déclaration</span>
            </label>
            <label class="d-flex align-items-center gap-2 cursor-pointer">
              <input type="radio" v-model="reviewForm.statut" value="brouillon" class="form-check-input" />
              <span class="text-red-600 font-semibold">Rejeter / Refuser</span>
            </label>
          </div>
        </div>

        <div class="mb-4">
          <label class="form-label font-medium">
            Commentaire {{ reviewForm.statut === 'brouillon' ? '(Obligatoire)' : '(Optionnel)' }} :
          </label>
          <textarea 
            v-model="reviewForm.commentaire_refus" 
            class="form-control" 
            rows="4" 
            placeholder="Écrivez ici vos remarques ou les raisons du rejet..."
          ></textarea>
        </div>

        <div class="d-flex justify-content-end gap-2">
          <button @click="showModaleReview = false" class="btn btn-outline-secondary">Annuler</button>
          <button 
            @click="validerDecision" 
            class="btn"
            :class="reviewForm.statut === 'validee' ? 'btn-success' : 'btn-danger'"
          >
            Confirmer
          </button>
        </div>

      </div>
    </div>

    <div v-if="showModaleVoir" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" style="background: rgba(0,0,0,0.5); z-index: 1050;">
      <div class="bg-white p-6 rounded-lg shadow-lg" style="width: 600px; max-width: 90%;">
        
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h3 class="text-lg font-bold">Détail de la Déclaration</h3>
          <button @click="showModaleVoir = false" class="btn-close">❌</button>
        </div>

        <div class="mb-4 bg-gray-50 p-3 rounded">
          <p class="text-sm">
            <strong>Auteur :</strong> 
            <span v-if="declarationConsultee?.user?.prenom || declarationConsultee?.user?.nom">
              {{ declarationConsultee.user.prenom }} {{ declarationConsultee.user.nom }}
            </span>
            <span v-else class="text-gray-500">
              Utilisateur #{{ declarationConsultee?.user_id }}
            </span>
          </p>
          <p class="text-sm"><strong>Période :</strong> {{ new Date(2026, declarationConsultee?.mois - 1).toLocaleString('fr-FR', { month: 'long' }) }} {{ declarationConsultee?.annee }}</p>
          <p class="text-sm"><strong>Statut :</strong> <span class="font-semibold">{{ declarationConsultee?.statut.toUpperCase() }}</span></p>
        </div>

        <div class="overflow-x-auto mb-4">
          <table class="min-w-full table-auto text-sm">
            <thead class="bg-gray-100">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Mission</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Quantité</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Tarif Appliqué</th>
                <th class="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="ligne in declarationConsultee?.lignes" :key="ligne.id">
                <td class="px-4 py-2 font-medium">{{ getNomMission(ligne.mission_id) }}</td>
                <td class="px-4 py-2">{{ ligne.quantite }}</td>
                <td class="px-4 py-2">{{ ligne.tarif_applique.toFixed(2) }} €</td>
                <td class="px-4 py-2 font-semibold">{{ (ligne.quantite * ligne.tarif_applique).toFixed(2) }} €</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="d-flex justify-content-end">
          <button @click="showModaleVoir = false" class="btn btn-secondary">Fermer</button>
        </div>

      </div>
    </div>

  </div>
</template>