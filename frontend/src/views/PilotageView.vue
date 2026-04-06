<template>
  <div class="container-fluid mt-2">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="text-primary fw-bold">📊 Pilotage & Analyses</h2>
      <span class="badge bg-primary px-3 py-2">Accès Administrateur</span>
    </div>

    <div class="card shadow-sm mb-4 border-0 bg-light">
      <div class="card-body">
        <div class="row g-3 align-items-center">
          <div class="col-md-3">
            <label class="form-label fw-bold small text-muted">Année</label>
            <select v-model="filtres.annee" class="form-select">
              <option v-for="a in anneesDisponibles" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label fw-bold small text-muted">Site</label>
            <select v-model="filtres.site" class="form-select">
              <option value="all">Tous les sites</option>
              <option value="lyon_est">Lyon Est</option>
              <option value="lyon_sud">Lyon Sud</option>
            </select>
          </div>
          <div class="col-md-3 d-flex align-items-end">
            <button class="btn btn-primary w-100 fw-bold" @click="chargerDonneesPilotage">
              Mettre à jour
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm border-0 mb-4">
      <div class="card-body">
        <h5 class="card-title fw-bold mb-3">Évolution mensuelle des dépenses</h5>
        <div style="height: 400px; position: relative;">
          <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
          <div v-else class="text-center mt-5 text-muted">
            Chargement des données du graphique...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'
import api from '@/services/api' // 👈 Import de ton instance Axios

// Enregistrement des modules indispensables de Chart.js
ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

// États pour les filtres
const filtres = ref({
  annee: 2026,
  site: 'all'
})
const anneesDisponibles = [2024, 2025, 2026]

// Configuration et données du graphique
const chartData = ref(null)
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top' }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: (value) => value + ' €' }
    }
  }
}

// Appel API pour remplir le graphique
const chargerDonneesPilotage = async () => {
  chartData.value = null // Reset le graphique pour afficher l'état "chargement"
  
  try {
    const response = await api.get('/paie/pilotage/depenses', {
      params: {
        annee: filtres.value.annee,
        site: filtres.value.site
      }
    })

    const donneesBackend = response.data.donnees

    const labelsMois = ['Janv', 'Févr', 'Mars', 'Avril', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
    const depensesCCDA = donneesBackend.map(item => item.depenses_ccda)
    const depensesCCDU = donneesBackend.map(item => item.depenses_ccdu)

    chartData.value = {
      labels: labelsMois,
      datasets: [
        {
          label: 'Dépenses CCDA (€)',
          backgroundColor: '#0d6efd',
          data: depensesCCDA
        },
        {
          label: 'Dépenses CCDU (€)',
          backgroundColor: '#ffc107',
          data: depensesCCDU
        }
      ]
    }
  } catch (error) {
    console.error("Erreur lors de la récupération des données de pilotage :", error)
    alert("Impossible de charger les données de pilotage.")
  }
}

onMounted(() => {
  chargerDonneesPilotage()
})
</script>

<style scoped>
.card {
  border-radius: 10px;
}
</style>