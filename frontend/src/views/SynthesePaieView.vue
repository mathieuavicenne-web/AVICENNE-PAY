<template>
  <div class="p-6">
    <div class="mb-8 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h1-avicenne m-0">Synthèse de Paie</h1>
        <p class="text-muted small mb-0">Consultez les montants globaux et exportez les données de paie.</p>
      </div>
      
      <div class="d-flex gap-2">
        <button 
          class="btn btn-avicenne-success px-4 shadow-sm d-flex align-items-center" 
          @click="exporterJournalDetails"
          :disabled="loading" 
        >
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="bi bi-file-earmark-excel me-2"></i>
          
          <span>{{ loading ? 'Génération...' : 'Exporter Journal Détaillé' }}</span>
        </button>
      </div>
    </div>

    <div class="card shadow-avicenne border-0 rounded-4 mb-4 overflow-hidden">
      <div class="card-body p-4 bg-white">
        <div class="row g-3 align-items-end">
          <div class="col-md-5">
            <div class="row g-2">
              <div class="col-6">
                <label class="form-label fw-bold small text-avicenne">DU (MOIS / ANNÉE)</label>
                <div class="input-group input-group-sm">
                  <select v-model="filtres.moisDebut" class="form-select border-2">
                    <option v-for="m in 12" :key="m" :value="m">{{ donnerNomMois(m) }}</option>
                  </select>
                  <select v-model="filtres.anneeDebut" class="form-select border-2">
                    <option v-for="a in listeAnnees" :key="a" :value="a">{{ a }}</option>
                  </select>
                </div>
              </div>
              <div class="col-6">
                <label class="form-label fw-bold small text-avicenne">AU (MOIS / ANNÉE)</label>
                <div class="input-group input-group-sm">
                  <select v-model="filtres.moisFin" class="form-select border-2">
                    <option v-for="m in 12" :key="m" :value="m">{{ donnerNomMois(m) }}</option>
                  </select>
                  <select v-model="filtres.anneeFin" class="form-select border-2">
                    <option v-for="a in listeAnnees" :key="a" :value="a">{{ a }}</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-3">
            <label class="form-label fw-bold small text-avicenne">FILTRER PAR STATUT</label>
            <select v-model="filtreStatut" class="form-select form-select-sm border-2">
              <option value="tous">Tous les statuts</option>
              <option value="brouillon">Brouillon</option>
              <option value="soumise">Soumise</option>
              <option value="validee">Validée</option>
            </select>
          </div>

          <div class="col-md-4 d-flex align-items-end justify-content-end">
            <button 
              class="btn btn-avicenne-primary px-5 fw-bold shadow-sm d-flex align-items-center justify-content-center" 
              @click="chargerSynthese"
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-search me-2"></i>
              
              <span>{{ loading ? 'Actualisation...' : 'Actualiser la synthèse' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="card shadow-avicenne border-0 rounded-4 overflow-hidden">
      <div v-if="loading" class="text-center my-5 py-5">
        <div class="d-flex flex-column align-items-center">
          <div class="avicenne-heart-logo animate-pulse-heart mb-3">
            <i class="bi bi-suit-heart-fill"></i>
            <i class="bi bi-activity"></i>
          </div>
          <div class="mt-2">
            <span class="text-avicenne fw-bold">Récupération des données comptables...</span>
            <div class="progress mt-2 mx-auto" style="width: 150px; height: 4px; border-radius: 10px; background-color: rgba(67, 150, 209, 0.1);">
              <div class="progress-bar progress-bar-striped progress-bar-animated" 
                  role="progressbar" 
                  style="width: 100%; background-color: var(--primary-color);">
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="table-responsive">
        <table class="table table-hover mb-0 align-middle">
          <thead style="background-color: #f8fafc; border-bottom: 2px solid var(--avicenne-blue);">
            <tr class="small text-uppercase">
              <th class="px-4 py-3 text-avicenne">Nom</th>
              <th class="px-4 py-3 text-avicenne">Prénom</th>
              <th class="px-4 py-3 text-avicenne text-center">Site</th>
              <th class="px-4 py-3 text-avicenne text-center">Rôle</th>
              <th class="px-4 py-3 text-avicenne text-center">Période</th>
              <th class="px-4 py-3 text-avicenne text-center">Statut</th>
              <th class="px-4 py-3 text-avicenne text-end">Montant Brut</th>
            </tr>
          </thead>
          
          <tbody class="text-avicenne-dark">
            <tr v-if="donneesFiltrees.length === 0">
              <td colspan="7" class="text-center py-5 text-muted italic">
                <i class="bi bi-search me-2"></i> Aucune déclaration trouvée pour cette période.
              </td>
            </tr>

            <tr v-for="(ligne, index) in donneesFiltrees" :key="index">
              <td class="px-4 fw-bold">{{ ligne.nom }}</td>
              <td class="px-4">{{ ligne.prenom }}</td>
              <td class="px-4 text-center">
                <span class="badge bg-light text-dark border">{{ ligne.site }}</span>
              </td>
              <td class="px-4 text-center">
                <span :class="['badge-role', `badge-role-${ligne.role?.toLowerCase()}`]">
                  {{ ligne.role.toUpperCase() }}
                </span>
              </td>
              <td class="px-4 text-center fw-bold text-muted small">{{ ligne.periode }}</td>
              <td class="px-4 text-center">
                <span class="badge-statut" :class="ligne.statut.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')">
                  {{ ligne.statut.toUpperCase() }}
                </span>
              </td>
              <td class="px-4 text-end fw-bold" style="color: var(--avicenne-blue)">
                {{ ligne.montant_brut.toFixed(2) }} €
              </td>
            </tr>
          </tbody>
          
          <tfoot v-if="donneesFiltrees.length > 0" class="border-top-2">
            <tr style="background-color: #f8fafc;">
              <td colspan="5" class="px-4 py-3 text-end fw-bold text-avicenne">TOTAL GÉNÉRAL :</td>
              <td></td>
              <td class="px-4 py-3 text-end fw-bold fs-5 text-avicenne">
                {{ calculMontantTotal.toFixed(2) }} €
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>
<style scoped>
/* --- BOUTON VERT EXPORT (Excel) --- */
.btn-avicenne-success {
    background-color: #2D6A4F !important; 
    color: white !important;
    border: 1px solid #2D6A4F !important;
    border-radius: 0.75rem; /* Harmonisation avec main.css */
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex !important;
    align-items: center;
    justify-content: center;
}

.btn-avicenne-success:hover:not(:disabled) {
    background-color: #1B4332 !important;
    border-color: #1B4332 !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(27, 67, 50, 0.3) !important;
}

.btn-avicenne-success:active {
    transform: translateY(1px);
}

.btn-avicenne-success:disabled {
    background-color: #2D6A4F !important;
    opacity: 0.6 !important;
    cursor: not-allowed;
    transform: none !important;
}

/* --- BOUTON BLEU ACTUALISER (Filtres) --- */
.btn-avicenne-primary {
    /* Utilisation de la variable correcte de main.css */
    background-color: var(--primary-color) !important; 
    color: white !important;
    border: 1px solid var(--primary-color) !important;
    border-radius: 0.75rem; /* Harmonisation avec main.css */
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex !important;
    align-items: center;
    justify-content: center;
}

.btn-avicenne-primary:hover:not(:disabled) {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(67, 150, 209, 0.3) !important;
}

.btn-avicenne-primary:active {
    transform: translateY(1px);
}

.btn-avicenne-primary:disabled {
    background-color: var(--primary-color) !important;
    opacity: 0.6 !important;
    border-color: transparent !important;
    cursor: not-allowed;
    transform: none !important;
}
/* --- STYLE DES BADGES STATUT (Exemple) --- */
.badge-statut {
  padding: 5px 12px;
  border-radius: 50px;
  font-size: 0.7rem;
  font-weight: 700;
}
.badge-statut.valide { background-color: #d1fae5; color: #065f46; }
.badge-statut.enattente { background-color: #fef3c7; color: #92400e; }
</style>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const dateActuelle = new Date()
const anneeEnCours = dateActuelle.getFullYear()

// 🎯 1. ON CRÉE LA VARIABLE MANQUANTE : Génération immédiate des années (de 2024 à N+1)
const listeAnnees = computed(() => {
  const anneeDepart = 2024
  const anneeMax = anneeEnCours + 1
  const annees = []
  for (let i = anneeDepart; i <= anneeMax; i++) {
    annees.push(i)
  }
  return annees
})

// 🎯 2. ON ADAPTE LES FILTRES : Pour correspondre aux v-model de ton HTML
const filtres = ref({
  moisDebut: 1, // Janvier par défaut
  anneeDebut: 2026,
  moisFin: dateActuelle.getMonth() + 1, // Mois actuel
  anneeFin: 2026
})

const donneesPaie = ref([])
const loading = ref(false)

const filtreStatut = ref('tous')

const donneesFiltrees = computed(() => {
  if (filtreStatut.value === 'tous') {
    return donneesPaie.value
  }
  return donneesPaie.value.filter(ligne => {
    // Normalisation au cas où il y aurait un accent (validée / validee)
    const statutNormalise = ligne.statut.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    const filtreNormalise = filtreStatut.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    
    return statutNormalise === filtreNormalise
  })
})

const calculMontantTotal = computed(() => {
  return donneesFiltrees.value.reduce((acc, current) => acc + current.montant_brut, 0)
})

const donnerNomMois = (num) => {
  const mois = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
  return mois[num - 1]
}

// Classe de couleur Bootstrap pour les statuts
const getStatutColorClass = (statut) => {
  switch (statut?.toLowerCase()) {
    case 'validee':
    case 'validée':
      return 'bg-success'
    case 'soumise':
      return 'bg-warning text-dark'
    case 'brouillon':
      return 'bg-secondary'
    default:
      return 'bg-info'
  }
}

// 🎯 3. ON MODIFIE L'APPEL API : On envoie les plages de dates au Backend
const chargerSynthese = async () => {
  const debut = (filtres.value.anneeDebut * 100) + filtres.value.moisDebut
  const fin = (filtres.value.anneeFin * 100) + filtres.value.moisFin
  
  if (fin < debut) {
    alert("La période de fin ne peut pas être antérieure à la période de début.")
    return
  }

  loading.value = true
  try {
    const response = await api.get('/paie/synthese-mensuelle', {
      params: {
        mois_debut: filtres.value.moisDebut,
        annee_debut: filtres.value.anneeDebut,
        mois_fin: filtres.value.moisFin,
        annee_fin: filtres.value.anneeFin
      }
    })
    
    donneesPaie.value = response.data
  } catch (error) {
    console.error("Erreur lors de la récupération de la synthèse :", error)
    alert("Impossible de charger la synthèse de paie. Vérifie que le backend a bien été mis à jour avec les paramètres de début et de fin !")
  } finally {
    loading.value = false
  }
}

const exporterJournalDetails = async () => {
  loading.value = true
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
    const response = await api.get('/paie/synthese-mensuelle/details', {
      params: {
        mois_debut: filtres.value.moisDebut,
        annee_debut: filtres.value.anneeDebut,
        mois_fin: filtres.value.moisFin,
        annee_fin: filtres.value.anneeFin
      }
    })

    const donneesDetails = response.data
    if (donneesDetails.length === 0) {
      alert("Aucune donnée détaillée à exporter.")
      return
    }

    const workbook = new ExcelJS.Workbook()

    // 1. ONGLET RÉSUMÉ (Regroupé par Nom+Prénom pour éviter les doublons NSS de test)
    const sheetResume = workbook.addWorksheet('Résumé par Utilisateur')
    sheetResume.columns = [
      { header: 'Type Contrat', key: 'type_contrat', width: 15 },
      { header: 'NOM', key: 'nom', width: 20 },
      { header: 'PRÉNOM', key: 'prenom', width: 20 },
      { header: 'Num. Sécu (NSS)', key: 'nss', width: 20 },
      { header: 'IBAN', key: 'iban', width: 28 },
      { header: 'Site', key: 'site', width: 15 },
      { header: 'Rôle', key: 'role', width: 15 },
      { header: 'TOTAL BRUT', key: 'montant_brut', width: 18 }
    ]

    sheetResume.getRow(1).eachCell((cell) => {
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF2D6A4F' } }
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
    })

    const resumeMap = {}
    donneesDetails.forEach(item => {
      const userKey = `${item.nom.trim()}_${item.prenom.trim()}`.toLowerCase()
      if (!resumeMap[userKey]) {
        resumeMap[userKey] = { ...item, montant_brut: 0 }
      }
      resumeMap[userKey].montant_brut += parseFloat(item.montant_brut || 0)
    })

    Object.values(resumeMap).forEach((user, index) => {
      const row = sheetResume.addRow({ ...user, nom: user.nom.toUpperCase() })
      row.getCell(8).numFmt = '#,##0.00" €"'
      if (index % 2 !== 0) {
        row.eachCell(c => c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8F9FA' } })
      }
    })

    const totalRowRes = sheetResume.rowCount + 1
    sheetResume.mergeCells(`A${totalRowRes}:G${totalRowRes}`)
    sheetResume.getCell(`A${totalRowRes}`).value = "TOTAL GÉNÉRAL DES VIREMENTS"
    sheetResume.getCell(`A${totalRowRes}`).alignment = { horizontal: 'right' }
    sheetResume.getCell(`H${totalRowRes}`).value = { formula: `SUM(H2:H${totalRowRes - 1})` }
    sheetResume.getCell(`H${totalRowRes}`).numFmt = '#,##0.00" €"'
    sheetResume.getCell(`H${totalRowRes}`).font = { bold: true }

    // 2. ONGLET DÉTAILLÉ
    const worksheet = workbook.addWorksheet('Détails Paie')
    worksheet.columns = [
      { header: 'Type Contrat', key: 'type_contrat', width: 15 },
      { header: 'NOM', key: 'nom', width: 20 },
      { header: 'PRÉNOM', key: 'prenom', width: 20 },
      { header: 'Num. Sécu (NSS)', key: 'nss', width: 20 },
      { header: 'IBAN', key: 'iban', width: 28 },
      { header: 'Site', key: 'site', width: 15 },
      { header: 'Rôle', key: 'role', width: 15 },
      { header: 'Programme', key: 'programme', width: 20 },
      { header: 'Matière / Intitulé', key: 'matiere', width: 25 },
      { header: 'Type de Mission', key: 'mission', width: 30 },
      { header: 'Quantité', key: 'quantite', width: 12 },
      { header: 'Tarif unitaire', key: 'tarif_unitaire', width: 15 },
      { header: 'Montant brut', key: 'montant_brut', width: 15 }
    ]

    worksheet.getRow(1).eachCell((cell) => {
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4396D1' } }
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
    })

    donneesDetails.forEach((item, index) => {
      const row = worksheet.addRow({ ...item, nom: item.nom.toUpperCase() })
      row.getCell(12).numFmt = '#,##0.00" €"'
      row.getCell(13).numFmt = '#,##0.00" €"'
      if (index % 2 !== 0) {
        row.eachCell(c => c.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8F9FA' } })
      }
    })

    const totalRowDet = worksheet.rowCount + 1
    worksheet.mergeCells(`A${totalRowDet}:L${totalRowDet}`)
    worksheet.getCell(`A${totalRowDet}`).value = "TOTAL BRUT GÉNÉRAL"
    worksheet.getCell(`A${totalRowDet}`).alignment = { horizontal: 'right' }
    worksheet.getCell(`M${totalRowDet}`).value = { formula: `SUM(M2:M${totalRowDet - 1})` }
    worksheet.getCell(`M${totalRowDet}`).numFmt = '#,##0.00" €"'
    worksheet.getCell(`M${totalRowDet}`).font = { bold: true, color: { argb: 'FFDC3545' } }

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `Synthese_Paie_Detaillée_${donnerNomMois(filtres.value.moisFin)}.xlsx`
    link.click()
  } catch (error) {
    console.error("Erreur export :", error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  chargerSynthese()
})
</script>