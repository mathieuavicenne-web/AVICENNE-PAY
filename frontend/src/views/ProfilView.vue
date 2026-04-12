<script setup>
import { ref, onMounted, computed } from 'vue'
import { authService } from '@/services/api' // On suppose que authService a une méthode updateProfile()

const profil = ref({
  prenom: '',
  nom: '',
  email: '',
  role: '',
  telephone: '',
  adresse: '',
  code_postal: '',
  ville: '',
  nss: '',
  iban: '',
  filiere: '', // 🔥 Ajouté
  annee: '',   // 🔥 Ajouté
  profil_complete: false
})

const isEditing = ref(false)
const isLoading = ref(true)
const isSaving = ref(false)

// 🔥 LISTES DES ENUMS (Aussi récupérables via un getReferentiels si tu préfères)
const filieres = ["Médecine", "Pharmacie", "Maïeutique", "Odontologie", "Kinésithérapie"]
const annees = ["P2", "D1", "D2", "D3"]

// Pour calculer les initiales de l'avatar
const initiales = computed(() => {
  if (!profil.value.prenom || !profil.value.nom) return '??'
  return `${profil.value.prenom.charAt(0)}${profil.value.nom.charAt(0)}`.toUpperCase()
})

const iconeFiliere = computed(() => {
  const mapping = {
    'Médecine': 'bi-heart-pulse-fill', // Plus universel que le stéthoscope
    'Pharmacie': 'bi-capsule',
    'Odontologie': 'bi-brightness-high-fill', // On va tricher avec un style "éclatant" ou bi-shield-plus
    'Maïeutique': 'bi-person-arms-up',
    'Kinésithérapie': 'bi-body-text'
  }
  
  // Option "Sécurité" : Si tu veux des vrais symboles colorés sans dépendre des polices :
  const emojiMapping = {
    'Médecine': '🩺',
    'Pharmacie': '💊',
    'Odontologie': '🦷',
    'Maïeutique': '👶',
    'Kinésithérapie': '🏃'
  }
  
  return mapping[profil.value.filiere] || 'bi-person-fill'
})

// Ajoute ce computed pour l'option Emoji si les icônes buggent
const emojiFiliere = computed(() => {
  const emojis = {
    'Médecine': '🩺',
    'Pharmacie': '💊',
    'Odontologie': '🦷',
    'Maïeutique': '🤰',
    'Kinésithérapie': '💆'
  }
  return emojis[profil.value.filiere] || ''
})

// 🔒 FONCTION POUR MASQUER LE NSS (Mode lecture)
const masquerNSS = (nss) => {
  if (!nss || typeof nss !== 'string' || nss.length < 15) {
    return "***********"
  }
  return `${nss.slice(0, 1)}*************${nss.slice(-2)}`
}

// 🔒 FONCTION POUR MASQUER L'IBAN (Mode lecture)
const masquerIBAN = (iban) => {
  if (!iban || typeof iban !== 'string' || iban.length < 10) {
    return "*************************"
  }
  return `${iban.slice(0, 4)}*******************${iban.slice(-4)}`
}

onMounted(async () => {
  await chargerProfil()
})

const chargerProfil = async () => {
  try {
    isLoading.value = true
    const userData = await authService.getUserProfile()
    profil.value = { ...profil.value, ...userData }
  } catch (error) {
    console.error("Erreur lors de la récupération du profil", error)
  } finally {
    isLoading.value = false
  }
}

const sauvegarderProfil = async () => {
  try {
    isSaving.value = true
    
    // 1. On ne met que les champs texte classiques au départ
    const payload = {
      nom: profil.value.nom,
      prenom: profil.value.prenom,
      telephone: profil.value.telephone,
      adresse: profil.value.adresse,
      code_postal: profil.value.code_postal,
      ville: profil.value.ville,
      filiere: profil.value.filiere || null, // 🔥 Ajouté
      annee: profil.value.annee || null      // 🔥 Ajouté
    }

    // 2. Traitement sécurisé du NSS (si applicable)
    if (profil.value.nss) {
      const nssNettoye = profil.value.nss.replace(/[\s-]/g, '')
      if (nssNettoye.length > 0) {
        payload.nss = nssNettoye
      }
    }

    // 3. Traitement sécurisé de l'IBAN (si applicable)
    if (profil.value.iban) {
      const ibanNettoye = profil.value.iban.replace(/\s/g, '').toUpperCase()
      if (ibanNettoye.length > 0) {
        payload.iban = ibanNettoye
      }
    }

    // 4. Envoi propre au serveur
    await authService.updateUserProfile(payload) 
    
    // 5. On repasse en mode lecture et on rafraîchit
    isEditing.value = false
    await chargerProfil() 
    
  } catch (error) {
    console.error("Erreur lors de la sauvegarde", error)
    alert("Impossible de sauvegarder. Vérifiez que :\n- Le NSS contient bien 15 chiffres.\n- L'IBAN est un IBAN FR valide.")
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="p-6 text-start">
    <div class="mb-8 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h1-avicenne m-0">Mon Profil</h1>
        <p class="text-muted small mb-0">Retrouvez et complétez vos informations personnelles.</p>
      </div>
      <span v-if="profil.profil_complete" class="badge bg-success-soft text-success px-3 py-2 rounded-pill">
        <i class="bi bi-check-circle-fill me-1"></i> Profil Vérifié
      </span>
    </div>

    <div v-if="!isLoading && !profil.profil_complete && profil.role !== 'admin'" 
         class="alert alert-warning border-0 shadow-sm mb-4 animate__animated animate__shakeX" role="alert">
      <div class="d-flex align-items-center">
        <i class="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
        <div>
          <strong class="d-block">Profil incomplet !</strong> 
          Vous devez renseigner votre adresse, NSS et IBAN pour pouvoir saisir des déclarations.
        </div>
      </div>
    </div>

    <div v-if="isLoading" class="text-center my-5 py-5">
      <div class="d-flex flex-column align-items-center">
        <div class="avicenne-heart-logo animate-pulse-heart mb-3">
          <i class="bi bi-suit-heart-fill"></i>
          <i class="bi bi-activity"></i>
        </div>
        <p class="text-avicenne fw-bold">Chargement de vos informations...</p>
      </div>
    </div>

    <div v-else class="card shadow-avicenne border-0 rounded-3 mx-auto position-relative" style="max-width: 700px; margin-top: 40px;">
      
      <div v-if="profil.filiere && profil.role !== 'admin'" 
          class="filiere-premium-blason shadow animate__animated animate__backInDown">
        <span class="filiere-emoji-giant">{{ emojiFiliere }}</span>
      </div>

      <div class="card-body p-4 pt-4">
        
        <div class="d-flex align-items-start justify-content-between mb-4">
          <div class="d-flex align-items-center" :class="{ 'ms-extra': profil.filiere && profil.role !== 'admin' }">
            <div class="position-relative">
              <div class="bg-avicenne-avatar text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" 
                  :class="{ 'avatar-mini-overlap': profil.filiere && profil.role !== 'admin' }"
                  style="width: 55px; height: 55px; font-size: 1.4rem; font-weight: bold; background-color: var(--primary-color) !important;">
                {{ initiales }}
              </div>
            </div>

            <div class="ms-3">
              <h4 class="mb-0 fw-bold text-avicenne-dark">{{ profil.prenom }} {{ profil.nom }}</h4>
              <div class="d-flex align-items-center gap-2">
                <span class="badge-role small" :class="`badge-role-${profil.role?.toLowerCase()}`">
                  {{ profil.role?.toUpperCase() }}
                </span>
                <span v-if="profil.annee" class="text-muted fw-bold" style="font-size: 0.75rem;">
                  • {{ profil.annee }}
                </span>
              </div>
            </div>
          </div>
          
          <button v-if="!isEditing" @click="isEditing = true" class="btn btn-avicenne-outline btn-sm px-3 rounded-pill">
            <i class="bi bi-pencil-square me-1"></i>Modifier
          </button>
        </div>

        <form @submit.prevent="sauvegarderProfil">
          <div class="row g-2">
            
            <div class="col-12 border-bottom pb-1 mb-2">
              <h6 class="text-avicenne fw-bold x-small text-uppercase mb-0">Compte</h6>
            </div>

            <div class="col-sm-4 text-muted small fw-bold">Email</div>
            <div class="col-sm-8 text-avicenne-dark small">{{ profil.email }}</div>

            <div class="col-12 border-bottom pb-1 mb-2 mt-3">
              <h6 class="text-avicenne fw-bold x-small text-uppercase mb-0">Coordonnées</h6>
            </div>

            <div class="col-sm-4 text-muted small fw-bold align-self-center">Téléphone</div>
            <div class="col-sm-8">
              <input v-if="isEditing" type="tel" class="form-control form-control-sm" v-model="profil.telephone">
              <div v-else class="small text-avicenne-dark">{{ profil.telephone || '—' }}</div>
            </div>

            <template v-if="profil.role !== 'admin'">
              <div class="col-sm-4 text-muted small fw-bold mt-2">Adresse</div>
              <div class="col-sm-8 mt-2">
                <div v-if="isEditing" class="row g-2">
                  <div class="col-12"><input type="text" class="form-control form-control-sm mb-1" v-model="profil.adresse" placeholder="Rue"></div>
                  <div class="col-4"><input type="text" class="form-control form-control-sm" v-model="profil.code_postal" placeholder="CP"></div>
                  <div class="col-8"><input type="text" class="form-control form-control-sm" v-model="profil.ville" placeholder="Ville"></div>
                </div>
                <div v-else class="small text-avicenne-dark">
                  {{ profil.adresse }} {{ profil.code_postal }} {{ profil.ville }}
                  <span v-if="!profil.adresse">—</span>
                </div>
              </div>

              <div class="col-sm-4 text-muted small fw-bold mt-2">Filière / Année</div>
              <div class="col-sm-8 mt-2">
                <div v-if="isEditing" class="row g-2">
                  <div class="col-6">
                    <select class="form-select form-select-sm" v-model="profil.filiere">
                      <option v-for="fil in filieres" :key="fil" :value="fil">{{ fil }}</option>
                    </select>
                  </div>
                  <div class="col-6">
                    <select class="form-select form-select-sm" v-model="profil.annee">
                      <option v-for="ann in annees" :key="ann" :value="ann">{{ ann }}</option>
                    </select>
                  </div>
                </div>
                <div v-else class="small text-avicenne-dark">
                  {{ profil.filiere }} <span v-if="profil.annee">({{ profil.annee }})</span>
                </div>
              </div>

              <div class="col-12 border-bottom pb-1 mb-2 mt-3">
                <h6 class="text-avicenne fw-bold x-small text-uppercase mb-0">Paiement</h6>
              </div>

              <div class="col-sm-4 text-muted small fw-bold">Sécurité Sociale</div>
              <div class="col-sm-8 font-monospace small text-avicenne-dark">
                {{ profil.nss ? masquerNSS(profil.nss) : '—' }}
              </div>

              <div class="col-sm-4 text-muted small fw-bold">IBAN</div>
              <div class="col-sm-8 font-monospace small text-avicenne-dark">
                {{ profil.iban ? masquerIBAN(profil.iban) : '—' }}
              </div>
            </template>
          </div>

          <div v-if="isEditing" class="d-flex justify-content-end mt-4 pt-3 border-top">
            <button type="button" class="btn btn-sm btn-light px-3 me-2 rounded-pill" @click="isEditing = false">
              Annuler
            </button>
            <button type="submit" class="btn btn-sm btn-avicenne-primary px-4 rounded-pill">
              <span v-if="isSaving" class="spinner-border spinner-border-sm me-2"></span>
              Enregistrer
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* --- BASES & COULEURS --- */
.bg-success-soft {
  background-color: rgba(25, 135, 84, 0.1);
}

.text-avicenne-dark {
  color: #2c3e50;
  font-weight: 500;
}

.x-small {
  font-size: 0.7rem;
  letter-spacing: 0.5px;
}

/* --- AFFICHAGE DONNÉES (Mode lecture) --- */
.font-monospace {
  letter-spacing: 1px;
  color: var(--primary-color);
  font-family: 'Courier New', Courier, monospace;
}

/* --- FORMULAIRES (Mode édition) --- */
.form-control-sm, .form-select-sm {
  font-size: 0.85rem;
  padding: 0.4rem 0.7rem;
}

/* --- BOUTONS AVICENNE --- */
.btn-avicenne-primary {
  background-color: var(--primary-color) !important;
  color: white !important;
  border: none !important;
  transition: all 0.3s ease;
}

.btn-avicenne-primary:hover {
  background-color: var(--primary-dark, #357abd) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(67, 150, 209, 0.2);
}

.btn-avicenne-outline {
  color: var(--primary-color) !important;
  border: 1px solid var(--primary-color) !important;
  background: transparent;
  transition: all 0.3s ease;
}

.btn-avicenne-outline:hover {
  background-color: var(--primary-color) !important;
  color: white !important;
}

/* --- AVATAR & HARMONISATION --- */
.bg-avicenne-avatar {
  background-color: var(--primary-color) !important;
}

/* --- LE GRAND BLASON DE SPÉCIALITÉ (UX Premium) --- */
.filiere-premium-blason {
  position: absolute;
  top: -35px; 
  left: -35px;
  width: 130px;
  height: 130px;
  /* Un léger dégradé pour donner du relief au blason */
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 35px; 
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.12);
  border: 4px solid #ffffff;
}

/* L'EMOJI GÉANT (Remplace le style de l'icône) */
.filiere-emoji-giant {
  font-size: 5.5rem; /* Taille massive pour le clin d'oeil */
  filter: drop-shadow(0 5px 10px rgba(0,0,0,0.1));
  line-height: 1;
  user-select: none;
}

/* L'Avatar devient un badge flottant sur le blason */
.avatar-mini-overlap {
  position: absolute !important;
  bottom: -10px;
  right: -10px;
  width: 50px !important;
  height: 50px !important;
  font-size: 1.2rem !important;
  z-index: 11;
  border: 4px solid white !important;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15) !important;
  background-color: var(--primary-color) !important;
}

/* --- AJUSTEMENTS DE MISE EN PAGE --- */
.ms-extra {
  margin-left: 105px !important; /* Ajusté pour laisser passer le grand blason */
  transition: margin 0.3s ease;
}

/* Animations */
.animate__backInDown {
  animation-duration: 1s;
}
</style>