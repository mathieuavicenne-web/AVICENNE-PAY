<template>
  <div class="container-fluid mt-2">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="text-primary fw-bold">🧾 Synthèse de Paie</h2>
      <div>
        <button class="btn btn-outline-success fw-bold me-2" @click="exporterPaie">
          📥 Export Résumé (CSV)
        </button>
        <button class="btn btn-success fw-bold" @click="exporterJournalDetails">
          📊 Export Journal Détaillé (Excel)
        </button>
      </div>
    </div>

    <div class="card shadow-sm mb-4 border-0 bg-light">
      <div class="card-body">
        <div class="row g-3 align-items-end">
          <div class="col-md-2">
            <label class="form-label fw-bold small text-muted">Du (Mois)</label>
            <select v-model="filtres.moisDebut" class="form-select">
              <option v-for="m in 12" :key="m" :value="m">{{ donnerNomMois(m) }}</option>
            </select>
          </div>
          <div class="col-md-1">
            <label class="form-label fw-bold small text-muted">Du (Année)</label>
            <select v-model="filtres.anneeDebut" class="form-select">
              <option v-for="a in listeAnnees" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label fw-bold small text-muted">Au (Mois)</label>
            <select v-model="filtres.moisFin" class="form-select">
              <option v-for="m in 12" :key="m" :value="m">{{ donnerNomMois(m) }}</option>
            </select>
          </div>
          <div class="col-md-1">
            <label class="form-label fw-bold small text-muted">Au (Année)</label>
            <select v-model="filtres.anneeFin" class="form-select">
              <option v-for="a in listeAnnees" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>

          <div class="col-md-2">
            <label class="form-label fw-bold small text-muted">Statut</label>
            <select v-model="filtreStatut" class="form-select">
              <option value="tous">Tous les statuts</option>
              <option value="brouillon">Brouillon</option>
              <option value="soumise">Soumise</option>
              <option value="validee">Validée</option>
            </select>
          </div>

          <div class="col-md-4">
            <button class="btn btn-primary w-100 fw-bold" @click="chargerSynthese">
              🔍 Rechercher
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="donneesPaie.length > 0" class="d-flex gap-3 mb-3 justify-content-end">
      <div class="badge bg-light text-dark border p-2 fs-6">
        📁 Total : <strong>{{ donneesPaie.length }}</strong>
      </div>
      <div class="badge bg-secondary p-2 fs-6">
        ✏️ Brouillons : <strong>{{ compteursStatuts.brouillon }}</strong>
      </div>
      <div class="badge bg-warning text-dark p-2 fs-6">
        ⏳ Soumises : <strong>{{ compteursStatuts.soumise }}</strong>
      </div>
      <div class="badge bg-success p-2 fs-6">
        ✅ Validées : <strong>{{ compteursStatuts.validee }}</strong>
      </div>
    </div>
    <div class="card shadow-sm border-0">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0 align-middle">
            <thead class="table-light">
              <tr>
                <th class="ps-3">NOM</th>
                <th>PRÉNOM</th>
                <th class="text-center">SITE</th>
                <th class="text-center">RÔLE</th>
                <th class="text-center">MOIS/ANNÉE DÉCLARATION</th>
                <th class="text-center">STATUT DÉCLARATION</th>
                <th class="text-end pe-3">MONTANT BRUT GLOBAL</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="7" class="text-center py-4 text-muted">
                  Chargement des données comptables...
                </td>
              </tr>
              
              <tr v-else-if="donneesPaie.length === 0">
                <td colspan="7" class="text-center py-4 text-muted">
                  Aucune déclaration trouvée pour cette période.
                </td>
              </tr>

              <tr v-for="(ligne, index) in donneesFiltrees" :key="index">
                <td class="ps-3 fw-bold">{{ ligne.nom }}</td>
                <td>{{ ligne.prenom }}</td>
                <td class="text-center">
                  <span class="badge bg-secondary">{{ ligne.site }}</span>
                </td>
                <td class="text-center">
                  <span class="badge bg-light text-dark border">{{ ligne.role.toUpperCase() }}</span>
                </td>
                <td class="text-center fw-bold text-muted">{{ ligne.periode }}</td>
                <td class="text-center">
                  <span :class="['badge', getStatutColorClass(ligne.statut)]">
                    {{ ligne.statut.toUpperCase() }}
                  </span>
                </td>
                <td class="text-end pe-3 fw-bold text-success">
                  {{ ligne.montant_brut.toFixed(2) }} €
                </td>
              </tr>
            </tbody>
            
            <tfoot v-if="donneesPaie.length > 0 && !loading" class="table-light fw-bold">
              <tr>
                <td colspan="5" class="ps-3">Total Général ({{ donneesPaie.length }} déclarations affichées)</td>
                <td></td>
                <td class="text-end pe-3 text-primary fs-5">{{ calculMontantTotal.toFixed(2) }} €</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

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

//  Calcul automatique des compteurs par statut
const compteursStatuts = computed(() => {
  const totaux = { brouillon: 0, soumise: 0, validee: 0 }
  
  donneesPaie.value.forEach(ligne => {
    // On enlève les accents pour être sûr que ça matche
    const statutNormalise = ligne.statut.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    
    if (statutNormalise === 'brouillon') totaux.brouillon++
    if (statutNormalise === 'soumise') totaux.soumise++
    if (statutNormalise === 'validee' || statutNormalise === 'validée') totaux.validee++
  })
  
  return totaux
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

// Export CSV du tableau résumé
const exporterPaie = () => {
  if (donneesPaie.value.length === 0) {
    alert("Aucune donnée à exporter pour cette période.")
    return
  }

  const entetes = ["NOM", "PRENOM", "SITE", "ROLE", "MOIS/ANNEE", "STATUT", "MONTANT BRUT GLOBAL (€)"]
  
  const lignes = donneesPaie.value.map(ligne => [
    `"${ligne.nom}"`,
    `"${ligne.prenom}"`, 
    `"${ligne.site}"`,
    `"${ligne.role}"`,
    `"${ligne.periode}"`,
    `"${ligne.statut}"`,
    ligne.montant_brut.toFixed(2)
  ])

  const contenuCSV = [entetes.join(";"), ...lignes.map(l => l.join(";"))].join("\n")

  const blob = new Blob(["\ufeff", contenuCSV], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  
  const lien = document.createElement("a")
  lien.href = url
  
  const nomMoisDebut = donnerNomMois(filtres.value.moisDebut)
  const nomMoisFin = donnerNomMois(filtres.value.moisFin)
  lien.setAttribute("download", `Synthese_Paie_Du_${nomMoisDebut}_${filtres.value.anneeDebut}_Au_${nomMoisFin}_${filtres.value.anneeFin}.csv`)
  
  document.body.appendChild(lien)
  lien.click()
  document.body.removeChild(lien)
}

// Export Excel lourd pour la compta (concerne TOUJOURS uniquement le validé)
const exporterJournalDetails = async () => {
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

    // 🎯 4. ON MODIFIE AUSSI L'EXPORT : Pour exporter la plage sélectionnée
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
      alert("Aucune donnée détaillée à exporter pour cette période (seules les déclarations validées sont exportées).")
      return
    }

    const workbook = new ExcelJS.Workbook()
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

    const headerRow = worksheet.getRow(1)
    headerRow.height = 25
    headerRow.eachCell((cell) => {
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FF0D6EFD' }
      }
      cell.font = { color: { argb: 'FFFFFFFF' }, bold: true, size: 11 }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
    })

    donneesDetails.forEach((item, index) => {
      const row = worksheet.addRow({
        type_contrat: item.type_contrat,
        nom: item.nom.toUpperCase(),
        prenom: item.prenom,
        nss: item.nss,
        iban: item.iban,
        site: item.site,
        role: item.role,
        programme: item.programme,
        matiere: item.matiere,
        mission: item.mission,
        quantite: item.quantite,
        tarif_unitaire: item.tarif_unitaire,
        montant_brut: item.montant_brut
      })

      row.height = 20

      const centeredCols = [1, 4, 5, 6, 7, 8, 11]
      centeredCols.forEach(colIndex => {
        row.getCell(colIndex).alignment = { vertical: 'middle', horizontal: 'center' }
      })
      
      row.getCell(2).alignment = { vertical: 'middle', horizontal: 'left' }
      row.getCell(3).alignment = { vertical: 'middle', horizontal: 'left' }
      row.getCell(9).alignment = { vertical: 'middle', horizontal: 'left' }
      row.getCell(10).alignment = { vertical: 'middle', horizontal: 'left' }

      row.getCell(12).numFmt = '#,##0.00" €"'
      row.getCell(13).numFmt = '#,##0.00" €"'

      if (index % 2 !== 0) {
        row.eachCell((cell) => {
          cell.fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: 'FFF8F9FA' }
          }
        })
      }
    })

    const totalRowIndex = donneesDetails.length + 2
    const totalRow = worksheet.getRow(totalRowIndex)
    totalRow.height = 25
    
    worksheet.mergeCells(`A${totalRowIndex}:L${totalRowIndex}`)
    const totalLabelCell = totalRow.getCell(1)
    totalLabelCell.value = "TOTAL BRUT GÉNÉRAL"
    totalLabelCell.font = { bold: true, size: 11 }
    totalLabelCell.alignment = { vertical: 'middle', horizontal: 'right' }
    
    const totalSumCell = totalRow.getCell(13)
    totalSumCell.value = { formula: `SUM(M2:M${totalRowIndex - 1})` }
    totalSumCell.numFmt = '#,##0.00" €"'
    totalSumCell.font = { bold: true, size: 11, color: { argb: 'FFDC3545' } }
    totalSumCell.alignment = { vertical: 'middle', horizontal: 'right' }

    totalRow.eachCell((cell) => {
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFE9ECEF' }
      }
    })

    const buffer = await workbook.xlsx.writeBuffer()
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    link.href = url
    
    const nomMoisDebut = donnerNomMois(filtres.value.moisDebut)
    const nomMoisFin = donnerNomMois(filtres.value.moisFin)
    link.setAttribute('download', `Details_Paie_Du_${nomMoisDebut}_Au_${nomMoisFin}.xlsx`)
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

  } catch (error) {
    console.error("Erreur lors de l'export Excel :", error)
    alert("Impossible de générer le fichier Excel.")
  }
}

onMounted(() => {
  chargerSynthese()
})
</script>