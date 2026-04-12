<template>
  <div class="p-6">
    <div class="mb-8 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h1-avicenne m-0">
          Catalogue <span class="text-primary">{{ type.toUpperCase() }}</span>
        </h1>
        <p class="text-muted small">Gestion du référentiel et des tarifs unitaires.</p>
      </div>
      
      <button 
        v-if="peutGerer" 
        @click="ouvrirModalCreation" 
        class="btn-avicenne-submit shadow-sm"
      >
        <i class="bi bi-plus-circle me-2"></i>Ajouter une mission
      </button>
    </div>

    <div v-if="loading" class="text-center my-5 py-5">
      <div class="d-flex flex-column align-items-center">
        <div class="avicenne-heart-logo animate-pulse-heart mb-3">
          <i class="bi bi-suit-heart-fill"></i>
          <i class="bi bi-activity"></i>
        </div>
        <div class="mt-2">
          <span class="text-avicenne fw-bold">Chargement du catalogue de missions...</span>
          <div class="progress mt-2 mx-auto" style="width: 150px; height: 4px; border-radius: 10px; background-color: rgba(67, 150, 209, 0.1);">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                role="progressbar" 
                style="width: 100%; background-color: var(--primary-color);">
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="missions.length === 0" class="card p-10 text-center shadow-avicenne border-0">
      <i class="bi bi-folder2-open text-muted" style="font-size: 3rem;"></i>
      <p class="text-muted mt-3">Aucune mission trouvée pour le catalogue {{ type.toUpperCase() }}.</p>
    </div>

    <div v-else class="card shadow-avicenne overflow-hidden border-0">
      <table class="table mb-0 align-middle">
        <thead class="bg-light">
          <tr>
            <th class="px-4 py-3 text-muted small text-uppercase fw-bold border-0">Mission / Catégorie</th>
            <th class="px-4 py-3 text-muted small text-uppercase fw-bold border-0" style="width: 150px;">Tarif</th>
            <th class="px-4 py-3 text-muted small text-uppercase fw-bold border-0" style="width: 180px;">Unité</th>
            <th v-if="peutGerer" class="px-4 py-3 text-muted small text-uppercase fw-bold border-0 text-center" style="width: 200px;">Actions</th>
          </tr>
        </thead>

        <tbody v-for="(listeMissions, nomCategorie) in missionsGroupees" :key="nomCategorie">
          <tr @click="toggleCategorie(nomCategorie)" class="cursor-pointer border-bottom" style="background-color: var(--primary-subtle);">
            <td colspan="3" class="px-4 py-3 fw-bold text-dark">
              <span class="inline-block me-2 transition-all d-inline-block" 
                    :style="categoriesOuvertes.includes(nomCategorie) ? 'transform: rotate(90deg); color: var(--primary-color);' : 'color: #cbd5e1;'">
                ▶
              </span>
              {{ nomCategorie }} 
              <span class="badge badge-soft ms-2">{{ listeMissions.length }} items</span>
            </td>
            <td v-if="peutGerer" class="px-4 py-3 border-0"></td>
          </tr>

          <tr v-if="categoriesOuvertes.includes(nomCategorie)" 
              v-for="mission in listeMissions" 
              :key="mission.id" 
              class="hover-bg-light transition-all">
            <td class="px-5 py-3 text-dark small italic border-bottom">{{ mission.titre }}</td>
            <td class="px-4 py-3 border-bottom">
              <span class="fw-bold text-primary">{{ mission.tarif_unitaire }}€</span>
            </td>
            <td class="px-4 py-3 text-muted small border-bottom">{{ mission.unite }}</td>
            <td v-if="peutGerer" class="px-4 py-3 border-bottom">
              <div class="d-flex justify-content-center align-items-center gap-3">
                <div class="form-check form-switch m-0 p-0">
                  <input type="checkbox" class="form-check-input cursor-pointer" :checked="mission.is_active" @change="basculerStatutMission(mission)" />
                </div>
                <button @click.stop="ouvrirModalEdition(mission)" class="btn-table btn-table-edit" title="Modifier">
                  <i class="bi bi-pencil"></i>
                </button>
                <button @click.stop="supprimerMission(mission.id)" class="btn-table btn-table-reopen" title="Supprimer">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="modal-backdrop-custom" @click.self="fermerModal">
      <div class="card shadow-avicenne p-0 border-0" style="max-width: 550px; width: 100%;">
        <div class="p-4 border-bottom d-flex justify-content-between align-items-center bg-light" style="border-radius: 1rem 1rem 0 0;">
          <h5 class="m-0 fw-bold text-primary uppercase small letter-spacing">
            {{ modeEdition ? '📋 Modification Mission' : '✨ Nouvelle Mission' }}
          </h5>
          <button @click="fermerModal" class="btn-close shadow-none"></button>
        </div>
        
        <form @submit.prevent="enregistrerMission" class="p-4">
          <div class="row g-4">
            <div class="col-12 custom-group">
              <label class="text-muted small fw-bold mb-2 d-block">CATÉGORIE</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-tag"></i></span>
                <input v-model="formMission.categorie" type="text" class="form-control" list="categoriesList" placeholder="Ex: Rédaction" required />
              </div>
              <datalist id="categoriesList">
                <option v-for="cat in categoriesDisponibles" :key="cat" :value="cat" />
              </datalist>
            </div>

            <div class="col-12 custom-group">
              <label class="text-muted small fw-bold mb-2 d-block">LIBELLÉ DE LA MISSION</label>
              <input v-model="formMission.titre" type="text" class="form-control" style="border-left: 1px solid var(--color-border) !important; padding-left: 1rem;" placeholder="Ex: Rédaction QCM LVL 1" required />
            </div>

            <div class="col-md-6 custom-group">
              <label class="text-muted small fw-bold mb-2 d-block">TARIF UNITAIRE</label>
              <div class="input-group">
                <input v-model.number="formMission.tarif_unitaire" type="number" step="0.01" class="form-control" style="border-left: 1px solid var(--color-border) !important; padding-left: 1rem;" required />
                <span class="input-group-text bg-light fw-bold text-primary">€</span>
              </div>
            </div>

            <div class="col-md-6 custom-group">
              <label class="text-muted small fw-bold mb-2 d-block">UNITÉ</label>
              <select v-model="formMission.unite" class="form-select" style="border-left: 1px solid var(--color-border) !important; padding-left: 1rem;" required>
                <option value="" disabled selected>Choisir...</option>
                <optgroup v-for="(listeUnites, famille) in UNITES_STRUCTUREES" :key="famille" :label="famille">
                  <option v-for="u in listeUnites" :key="u" :value="u">{{ u }}</option>
                </optgroup>
              </select>
            </div>

            <div class="col-12">
              <div class="p-3 bg-light rounded-3 border">
                <label class="text-muted small fw-bold mb-3 d-block">VISIBILITÉ DU RÔLE</label>
                <div class="d-flex gap-4">
                  <div class="form-check form-switch">
                    <input v-model="formMission.dispo_resp" type="checkbox" class="form-check-input" id="dispResp" />
                    <label class="form-check-label small" for="dispResp">Responsables</label>
                  </div>
                  <div class="form-check form-switch">
                    <input v-model="formMission.dispo_tcp" type="checkbox" class="form-check-input" id="dispTcp" />
                    <label class="form-check-label small" for="dispTcp">TCP</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="d-flex justify-content-end gap-2 mt-5">
            <button type="button" class="btn btn-light text-muted fw-bold px-4" @click="fermerModal">ANNULER</button>
            <button type="submit" class="btn-avicenne-submit">
              {{ modeEdition ? 'ENREGISTRER' : 'CRÉER LA MISSION' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hover-bg-light:hover {
  background-color: var(--primary-subtle);
}

.letter-spacing {
  letter-spacing: 0.1em;
}

.transition-all {
  transition: all 0.2s ease-in-out;
}

/* On override légèrement bootstrap pour coller au main.css */
.form-check-input:checked {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.text-avicenne {
  color: var(--primary-color);
}
</style>

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

// ÉTAT POUR L'ACCORDÉON
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

// --- RÉFÉRENTIEL DES UNITÉS (Structuré par famille) ---
const UNITES_STRUCTUREES = {
  "⏱️ Temps": [
    "par heure", "par jour", "par mois", "par séance"
  ],
  "📚 Volume / Rédaction": [
    "par qcm", "par annale et par année", "par post-it", "par support / map"
  ],
  "🎯 Forfaitaire": [
    "forfait mise à jour estivale", "par pré-colle"
  ]
}

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

// --- LOGIQUE DYNAMIQUE POUR LE FORMULAIRE ---

// 1. Récupère les catégories existantes pour la datalist (suggestions)
const categoriesDisponibles = computed(() => {
  const cats = missions.value.map(m => m.categorie).filter(Boolean)
  return [...new Set(cats)].sort()
})

// 2. Détecte si des unités "hors référentiel" existent en base de données
const unitesHorsReferentiel = computed(() => {
  const toutesLesUnitesOfficielles = Object.values(UNITES_STRUCTUREES).flat()
  const unitesEnBase = missions.value.map(m => m.unite).filter(Boolean)
  return [...new Set(unitesEnBase.filter(u => !toutesLesUnitesOfficielles.includes(u)))]
})

// 🔐 Vérification des droits
const peutGerer = computed(() => ['admin', 'coordo'].includes(userRole.value))

// LOGIQUE DE L'ACCORDÉON
const toggleCategorie = (categorie) => {
  if (categoriesOuvertes.value.includes(categorie)) {
    categoriesOuvertes.value = categoriesOuvertes.value.filter(c => c !== categorie)
  } else {
    categoriesOuvertes.value.push(categorie)
  }
}

// LOGIQUE DE TRI ET GROUPEMENT POUR LE TABLEAU
const missionsGroupees = computed(() => {
  if (!Array.isArray(missions.value) || missions.value.length === 0) return {}

  const filtreType = props.type.toUpperCase()

  const missionsFiltrees = missions.value.filter(m => {
    return (m.type_contrat || '').toUpperCase() === filtreType
  })

  return missionsFiltrees.reduce((acc, mission) => {
    const cat = mission.categorie || 'Sans Catégorie'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(mission)
    return acc
  }, {})
})

// --- ACTIONS API ---
const chargerCatalogue = async () => {
  loading.value = true
  try {
    const toutesLesMissions = await missionService.getAllMissions()
    missions.value = toutesLesMissions
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
    } else {
      await missionService.createMission(formMission.value)
    }
    
    fermerModal()
    chargerCatalogue() 
  } catch (error) {
    alert("Erreur lors de l'enregistrement : " + error.message)
  }
}

const basculerStatutMission = async (mission) => {
  try {
    const nouveauStatut = !mission.is_active
    await missionService.updateMission(mission.id, { is_active: nouveauStatut })
    mission.is_active = nouveauStatut 
  } catch (error) {
    alert("Impossible de modifier le statut : " + error.message)
  }
}

const supprimerMission = async (id) => {
  if (confirm("Supprimer définitivement cette mission ? Cette action est irréversible.")) {
    try {
      await missionService.deleteMissionDefinitive(id) 
      chargerCatalogue()
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
    unite: '', // Laissé vide pour forcer le choix
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
  categoriesOuvertes.value = [] // Reset l'accordéon au changement d'onglet
})
</script>
