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
  return `${profil.value.prenom.charAt(0)}${profil.value.nom.charAt(0)}`.toUpperCase()
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
      filiere: profil.value.filiere || null, // 🔥 Ajouté (on passe null si vide pour le backend)
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
  <div class="container mt-4 text-start">
    <div class="mb-4">
      <h1 class="fw-bold" style="color: var(--primary-color);">Mon Profil</h1>
      <p class="text-muted">Retrouvez et complétez vos informations personnelles enregistrées dans Avicenne Pay.</p>
    </div>

    <div v-if="!isLoading && !profil.profil_complete && profil.role !== 'admin'" class="alert alert-warning border-0 shadow-sm mb-4" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      <strong>Profil incomplet !</strong> Vous devez obligatoirement renseigner votre adresse, NSS et IBAN pour pouvoir saisir des déclarations.
    </div>

    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Chargement...</span>
      </div>
    </div>

    <div v-else class="card shadow-sm border-0 mx-auto mb-5" style="max-width: 700px;">
      <div class="card-body p-4">
        
        <div class="d-flex align-items-center justify-content-between mb-4">
          <div class="d-flex align-items-center">
            <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center" style="width: 60px; height: 60px; font-size: 1.5rem; font-weight: bold;">
              {{ initiales }}
            </div>
            <div class="ms-3">
              <h3 class="mb-0 fw-bold">{{ profil.prenom }} {{ profil.nom }}</h3>
              <span class="badge bg-secondary text-uppercase">{{ profil.role }}</span>
            </div>
          </div>
          
          <button v-if="!isEditing" @click="isEditing = true" class="btn btn-outline-primary btn-sm">
            Modifier le profil
          </button>
        </div>

        <hr class="text-muted">

        <form @submit.prevent="sauvegarderProfil">
          <div class="row g-3">
            
            <div class="col-sm-4 text-muted fw-bold align-self-center">Email</div>
            <div class="col-sm-8">
              <input type="email" class="form-control-plaintext" :value="profil.email" readonly>
            </div>

            <div class="col-sm-4 text-muted fw-bold align-self-center">Téléphone</div>
            <div class="col-sm-8">
              <input v-if="isEditing" type="tel" class="form-control" v-model="profil.telephone">
              <div v-else class="py-2">{{ profil.telephone || '—' }}</div>
            </div>

            <template v-if="profil.role !== 'admin'">
              <div class="col-sm-4 text-muted fw-bold align-self-center">Adresse</div>
              <div class="col-sm-8">
                <input v-if="isEditing" type="text" class="form-control" v-model="profil.adresse" required>
                <div v-else class="py-2">{{ profil.adresse || '—' }}</div>
              </div>

              <div class="col-sm-4 text-muted fw-bold align-self-center">Code Postal</div>
              <div class="col-sm-8">
                <input v-if="isEditing" type="text" class="form-control" v-model="profil.code_postal" required>
                <div v-else class="py-2">{{ profil.code_postal || '—' }}</div>
              </div>

              <div class="col-sm-4 text-muted fw-bold align-self-center">Ville</div>
              <div class="col-sm-8">
                <input v-if="isEditing" type="text" class="form-control" v-model="profil.ville" required>
                <div v-else class="py-2">{{ profil.ville || '—' }}</div>
              </div>

              <div class="col-sm-4 text-muted fw-bold align-self-center">Filière</div>
              <div class="col-sm-8">
                <select v-if="isEditing" class="form-select" v-model="profil.filiere">
                  <option value="">-- Non renseigné --</option>
                  <option v-for="fil in filieres" :key="fil" :value="fil">{{ fil }}</option>
                </select>
                <div v-else class="py-2">{{ profil.filiere || '—' }}</div>
              </div>

              <div class="col-sm-4 text-muted fw-bold align-self-center">Année d'étude</div>
              <div class="col-sm-8">
                <select v-if="isEditing" class="form-select" v-model="profil.annee">
                  <option value="">-- Non renseigné --</option>
                  <option v-for="ann in annees" :key="ann" :value="ann">{{ ann }}</option>
                </select>
                <div v-else class="py-2">{{ profil.annee || '—' }}</div>
              </div>
              <div class="col-sm-4 text-muted fw-bold align-self-center">N° Sécurité Sociale</div>
              <div class="col-sm-8">
                <input v-if="isEditing" type="text" class="form-control" v-model="profil.nss" placeholder="15 chiffres" required>
                <div v-else class="py-2">{{ profil.nss ? masquerNSS(profil.nss) : '—' }}</div>
              </div>

              <div class="col-sm-4 text-muted fw-bold align-self-center">IBAN</div>
              <div class="col-sm-8">
                <input v-if="isEditing" type="text" class="form-control" v-model="profil.iban" placeholder="FR..." required>
                <div v-else class="py-2">{{ profil.iban ? masquerIBAN(profil.iban) : '—' }}</div>
              </div>
            </template>

          </div>

          <div v-if="isEditing" class="d-flex justify-content-end mt-4 pt-3 border-top">
            <button type="button" class="btn btn-light me-2" @click="isEditing = false" :disabled="isSaving">
              Annuler
            </button>
            <button type="submit" class="btn btn-primary" :disabled="isSaving">
              <span v-if="isSaving" class="spinner-border spinner-border-sm me-1" role="status"></span>
              Enregistrer
            </button>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-primary {
  background-color: var(--primary-color) !important;
}
.btn-primary {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}
.btn-outline-primary {
  color: var(--primary-color);
  border-color: var(--primary-color);
}
.btn-outline-primary:hover {
  background-color: var(--primary-color);
  color: white;
}
</style>