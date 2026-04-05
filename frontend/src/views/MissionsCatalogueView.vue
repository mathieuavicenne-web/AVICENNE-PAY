<template>
  <div class="p-6">
    <div class="mb-6 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">
          Catalogue des Missions {{ type.toUpperCase() }}
        </h1>
        <p class="text-gray-600">Consultez la liste des missions disponibles pour ce type de contrat.</p>
      </div>
      
      <button 
        v-if="peutGerer" 
        @click="ouvrirModalCreation" 
        class="btn btn-primary"
      >
        ➕ Ajouter une mission
      </button>
    </div>

    <div v-if="loading" class="text-center py-10">
      <span class="text-gray-500 text-lg">Chargement du catalogue en cours...</span>
    </div>

    <div v-else-if="missions.length === 0" class="text-center py-10 bg-white rounded-lg shadow">
      <span class="text-gray-500">Aucune mission trouvée pour le catalogue {{ type.toUpperCase() }}.</span>
    </div>

    <div v-else class="overflow-x-auto bg-white rounded-lg shadow">
      <table class="min-w-full table-auto border-collapse">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mission / Catégorie</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tarif</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unité</th>
            <th v-if="peutGerer" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>

        <tbody v-for="(listeMissions, nomCategorie) in missionsGroupees" :key="nomCategorie" class="border-b">
          
          <tr 
            @click="toggleCategorie(nomCategorie)" 
            class="bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors"
          >
            <td colspan="3" class="px-6 py-3 font-semibold text-gray-800">
              <span 
                class="inline-block me-2 transition-transform" 
                :style="categoriesOuvertes.includes(nomCategorie) ? 'transform: rotate(90deg);' : ''"
              >
                ▶
              </span>
              {{ nomCategorie }} 
              <span class="text-sm text-gray-500 ms-2">({{ listeMissions.length }} niveaux)</span>
            </td>
            <td v-if="peutGerer" class="px-6 py-3"></td>
          </tr>

          <tr 
            v-if="categoriesOuvertes.includes(nomCategorie)" 
            v-for="mission in listeMissions" 
            :key="mission.id"
            class="hover:bg-gray-50 transition-colors bg-white border-t"
          >
            <td class="px-10 py-3 text-sm text-gray-700">
              {{ mission.titre }}
            </td>
            <td class="px-6 py-3 text-sm font-semibold text-green-600">
              {{ mission.tarif_unitaire }}€
            </td>
            <td class="px-6 py-3 text-sm text-gray-500">
              {{ mission.unite }}
            </td>
            
            <td v-if="peutGerer" class="px-6 py-3 text-sm d-flex align-items-center gap-2">
              <div class="form-check form-switch mb-0">
                <input 
                  type="checkbox" 
                  class="form-check-input" 
                  role="switch"
                  :checked="mission.is_active" 
                  @change="basculerStatutMission(mission)"
                />
              </div>
              <button @click.stop="ouvrirModalEdition(mission)" class="btn btn-sm btn-outline-primary">✏️</button>
              <button @click.stop="supprimerMission(mission.id)" class="btn btn-sm btn-outline-danger">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="modal-backdrop" @click.self="fermerModal">
      <div class="modal-content p-4 rounded shadow bg-white" style="max-width: 500px; width: 100%;">
        <h3 class="text-xl font-bold mb-4">
          {{ modeEdition ? 'Modifier la mission' : 'Créer une mission' }}
        </h3>
        
        <form @submit.prevent="enregistrerMission">
          <div class="mb-3">
            <label class="form-label text-sm font-medium text-gray-600">Catégorie</label>
            <input v-model="formMission.categorie" type="text" class="form-control" placeholder="Ex: 📚 QCM" required />
          </div>

          <div class="mb-3">
            <label class="form-label text-sm font-medium text-gray-600">Titre</label>
            <input v-model="formMission.titre" type="text" class="form-control" placeholder="Ex: Rédaction QCM LVL 1" required />
          </div>

          <div class="mb-3">
            <label class="form-label text-sm font-medium text-gray-600">Tarif Unitaire (€)</label>
            <input v-model.number="formMission.tarif_unitaire" type="number" step="0.01" class="form-control" required />
          </div>

          <div class="mb-3">
            <label class="form-label text-sm font-medium text-gray-600">Unité</label>
            <select v-model="formMission.unite" class="form-select" required>
                <option value="" disabled>Sélectionnez une unité</option>
                
                <optgroup label="⏱️ Temps">
                  <option value="par heure">par heure</option>
                  <option value="par jour">par jour</option>
                  <option value="par mois">par mois</option>
                  <option value="par séance">par séance</option>
                </optgroup>

                <optgroup label="📚 Volume / Rédaction">
                  <option value="par qcm">par qcm</option>
                  <option value="par annale et par année">par annale et par année</option>
                  <option value="par post-it">par post-it</option>
                  <option value="par support / map">par support / map</option>
                </optgroup>

                <optgroup label="🎯 Forfaitaire">
                  <option value="forfait mise à jour estivale">forfait mise à jour estivale</option>
                  <option value="par pré-colle">par pré-colle</option>
                </optgroup>
            </select>
          </div>

          <div class="mb-3">
            <label class="form-label text-sm font-medium text-gray-600 mb-2 d-block">Visibilité de la mission</label>
            <div class="d-flex gap-4">
                <div class="form-check form-switch">
                  <input v-model="formMission.dispo_resp" type="checkbox" class="form-check-input" id="dispResp" />
                  <label class="form-check-label text-sm" for="dispResp">Disponible pour les Responsables</label>
                </div>
                <div class="form-check form-switch">
                  <input v-model="formMission.dispo_tcp" type="checkbox" class="form-check-input" id="dispTcp" />
                  <label class="form-check-label text-sm" for="dispTcp">Disponible pour les TCP</label>
                </div>
            </div>
          </div>
          
          <div class="d-flex justify-content-end gap-2 mt-4">
            <button type="button" class="btn btn-secondary" @click="fermerModal">Annuler</button>
            <button type="submit" class="btn btn-success">
              {{ modeEdition ? 'Enregistrer les modifications' : 'Créer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { missionService } from '@/services/api'

const props = defineProps({
  type: {
    type: String,
    required: true
  }
})

// --- ÉTATS ---
const missions = ref([])
const loading = ref(true)
const userRole = ref('')

// États pour la fenêtre Modale
const showModal = ref(false)
const modeEdition = ref(false)
const idMissionEnCours = ref(null)

// 🆕 ÉTAT POUR L'ACCORDÉON : On stocke les noms des catégories ouvertes
const categoriesOuvertes = ref([])

// Formulaire relié au v-model
const formMission = ref({
  categorie: '',
  titre: '',
  tarif_unitaire: 0,
  unite: '',
  dispo_resp: true,
  dispo_tcp: true,
  type_contrat: ''
})

// --- DECODAGE DU ROLE ---
const extraireRoleDuToken = () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''))
      userRole.value = JSON.parse(jsonPayload).role
    } catch (e) {
      console.error("Erreur d'extraction du rôle")
    }
  }
}

// 🔐 Vérification des droits : Seuls Admins et Coordos gèrent le catalogue
const peutGerer = computed(() => ['admin', 'coordo'].includes(userRole.value))

// 🆕 LOGIQUE DE L'ACCORDÉON : Fonction pour ouvrir/fermer une catégorie
const toggleCategorie = (categorie) => {
  if (categoriesOuvertes.value.includes(categorie)) {
    // Si elle est déjà ouverte, on l'enlève de la liste (donc elle se ferme)
    categoriesOuvertes.value = categoriesOuvertes.value.filter(c => c !== categorie)
  } else {
    // Sinon, on l'ajoute à la liste (elle s'ouvre)
    categoriesOuvertes.value.push(categorie)
  }
}

// 🆕 LOGIQUE DE TRI ET GROUPEMENT : On transforme la liste plate en dossiers
const missionsGroupees = computed(() => {
  // 1. On prend les missions récupérées de l'API
  const filtre = props.type.toUpperCase()
  const missionsFiltrees = missions.value.filter(m => m.type_contrat === filtre)
  
  // 2. On les range dans un objet par catégorie
  const groupe = missionsFiltrees.reduce((acc, mission) => {
    const cat = mission.categorie
    if (!acc[cat]) {
      acc[cat] = [] // Crée le dossier s'il n'existe pas
    }
    acc[cat].push(mission) // Range la mission dedans
    return acc
  }, {})
  
  return groupe
})

// --- ACTIONS API ---
const chargerCatalogue = async () => {
  loading.value = true
  try {
    const toutesLesMissions = await missionService.getAllMissions()
    missions.value = toutesLesMissions // Plus besoin de filtrer ici, c'est fait dans missionsGroupees !
  } catch (error) {
    console.error("Erreur lors du chargement des missions :", error)
  } finally {
    loading.value = false
  }
}

const enregistrerMission = async () => {
  try {
    formMission.value.type_contrat = props.type.toUpperCase()

    if (modeEdition.value) {
      await missionService.updateMission(idMissionEnCours.value, formMission.value)
      alert("Mission mise à jour !")
    } else {
      await missionService.createMission(formMission.value)
      alert("Mission créée avec succès !")
    }
    
    fermerModal()
    chargerCatalogue() 
  } catch (error) {
    alert(error.message)
  }
}

const basculerStatutMission = async (mission) => {
  try {
    const nouveauStatut = !mission.is_active
    await missionService.updateMission(mission.id, { is_active: nouveauStatut })
    mission.is_active = nouveauStatut 
    alert(nouveauStatut ? "Mission activée !" : "Mission désactivée !")
  } catch (error) {
    alert("Impossible de modifier le statut : " + error.message)
  }
}

const supprimerMission = async (id) => {
  if (confirm("Êtes-vous sûr de vouloir SUPPRIMER DÉFINITIVEMENT cette mission du catalogue ? Cette action est irréversible !")) {
    try {
      // 🎯 C'est ici qu'on appelle notre nouvelle fonction du front !
      await missionService.deleteMissionDefinitive(id) 
      alert("Mission supprimée définitivement.")
      
      chargerCatalogue() // On rafraîchit le tableau pour faire disparaître la ligne
    } catch (error) {
      alert("Erreur lors de la suppression : " + error.message)
    }
  }
}

// --- LOGIQUE DES MODALES ---
const ouvrirModalCreation = () => {
  modeEdition.value = false
  idMissionEnCours.value = null
  formMission.value = {
    categorie: '',
    titre: '',
    tarif_unitaire: 0,
    unite: 'l\'unité',
    dispo_resp: true,
    dispo_tcp: true,
    type_contrat: props.type.toUpperCase()
  }
  showModal.value = true
}

const ouvrirModalEdition = (mission) => {
  modeEdition.value = true
  idMissionEnCours.value = mission.id
  formMission.value = { ...mission } 
  showModal.value = true
}

const fermerModal = () => {
  showModal.value = false
}

// --- CYCLE DE VIE ---
onMounted(() => {
  extraireRoleDuToken()
  chargerCatalogue()
})

watch(() => props.type, () => {
  chargerCatalogue()
})
</script>

<style scoped>
/* Petit style basique pour simuler une fenêtre modale qui passe au premier plan */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}
.modal-content {
  background: white;
}
</style>