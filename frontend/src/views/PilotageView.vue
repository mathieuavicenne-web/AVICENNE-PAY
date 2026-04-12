<template>
  <div class="p-6">
    <div class="mb-8 d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h1-avicenne m-0">Pilotage & Analyses</h1>
        <p class="text-muted small mb-0">Indicateurs de performance et suivi budgétaire global de l'activité.</p>
      </div>
      <span class="badge badge-avicenne-admin px-3 py-2"><i class="bi bi-shield-check me-1"></i> Accès Administrateur</span>
    </div>

    <div class="card shadow-sm border-0 mb-4 bg-light">
      <div class="card-body p-4">
        <div class="row g-3 align-items-end">
          <div class="col-md-3">
            <label class="form-label fw-bold x-small text-uppercase text-muted">Année d'exercice</label>
            <select v-model="filtres.annee" class="form-select shadow-sm">
              <option v-for="a in anneesDisponibles" :key="a" :value="a">{{ a }}</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label fw-bold x-small text-uppercase text-muted">Site géographique</label>
            <select v-model="filtres.site" class="form-select shadow-sm">
              <option value="all">Tous les sites</option>
              <option value="lyon_est">Lyon Est</option>
              <option value="lyon_sud">Lyon Sud</option>
            </select>
          </div>
          <div class="col-md-4">
            <button 
              class="btn btn-avicenne-primary px-5 fw-bold shadow-sm d-flex align-items-center justify-content-center w-100" 
              @click="chargerDonneesPilotage"
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-search me-2"></i>
              <span>{{ loading ? 'Actualisation...' : 'Actualiser les indicateurs' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-avicenne border-0 overflow-hidden">
      <div class="card-header bg-white border-bottom p-4">
        <h5 class="m-0 fw-bold text-avicenne">Évolution mensuelle des dépenses</h5>
      </div>
      <div class="card-body p-4">
        <div style="height: 450px; position: relative;">
          <Bar v-if="chartData && !loading" :data="chartData" :options="chartOptions" />
          
          <div v-else class="h-100 d-flex flex-column align-items-center justify-content-center">
            <div class="avicenne-heart-logo animate-pulse-heart mb-3">
              <i class="bi bi-suit-heart-fill"></i>
              <i class="bi bi-activity"></i>
            </div>
            <div class="text-center">
              <p class="fw-bold text-avicenne mb-1">Analyse des données budgétaires en cours...</p>
              <div class="progress mx-auto" style="width: 150px; height: 4px; border-radius: 10px; background-color: rgba(67, 150, 209, 0.1);">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                    role="progressbar" 
                    style="width: 100%; background-color: var(--primary-color);">
                </div>
              </div>
            </div>
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
import api from '@/services/api'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const loading = ref(false)
const filtres = ref({
  annee: 2026,
  site: 'all'
})
const anneesDisponibles = [2024, 2025, 2026]

const chartData = ref(null)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      position: 'top',
      labels: { font: { family: 'Inter', weight: '600' }, usePointStyle: true } 
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { callback: (value) => value.toLocaleString() + ' €' }
    }
  }
}

const chargerDonneesPilotage = async () => {
  loading.value = true
  try {
    const response = await api.get('/paie/pilotage/depenses', {
      params: { annee: filtres.value.annee, site: filtres.value.site }
    })

    const data = response.data.donnees
    const labelsMois = ['Janv', 'Févr', 'Mars', 'Avril', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']

    chartData.value = {
      labels: labelsMois,
      datasets: [
        {
          label: 'Dépenses CCDA',
          backgroundColor: '#4396d1', // Bleu Avicenne
          borderRadius: 6,
          data: data.map(item => item.depenses_ccda)
        },
        {
          label: 'Dépenses CCDU',
          backgroundColor: '#ffca2c', // Jaune Avicenne
          borderRadius: 6,
          data: data.map(item => item.depenses_ccdu)
        }
      ]
    }
  } catch (error) {
    console.error("Erreur pilotage:", error)
  } finally {
    loading.value = false
  }
}

onMounted(() => chargerDonneesPilotage())
</script>

<style scoped>
/* --- BOUTON BLEU ACTUALISER (Filtres) --- */
.btn-avicenne-primary {
    background-color: var(--primary-color) !important; 
    color: white !important;
    border: 1px solid var(--primary-color) !important;
    border-radius: 0.75rem; 
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

/* --- AUTRES STYLES DE LA VUE --- */
.shadow-avicenne {
    box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.08);
}
.x-small {
    font-size: 0.75rem;
}
/* --- BADGE ADMIN PREMIUM --- */
.badge-avicenne-admin {
    background-color: rgba(67, 150, 209, 0.1) !important; /* Bleu Avicenne très léger */
    color: var(--primary-color) !important; /* Bleu Avicenne pur pour le texte */
    border: 1px solid rgba(67, 150, 209, 0.2) !important;
    border-radius: 50px; /* Forme pilule parfaite */
    font-weight: 600;
    letter-spacing: 0.3px;
    font-size: 0.75rem;
    text-transform: uppercase;
}

/* Optionnel : un petit effet au survol pour le côté "élégant" */
.badge-avicenne-admin:hover {
    background-color: rgba(67, 150, 209, 0.15) !important;
    transition: all 0.3s ease;
}
</style>