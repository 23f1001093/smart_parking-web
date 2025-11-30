<template>
  <div class="container py-4">
    <h2>Admin Summary & Charts</h2>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="row gy-4">
      <div class="col-md-6">
        <div class="card p-3 h-100">
          <h5>Spot Occupancy (All Lots)</h5>
          <canvas ref="occupancyCanvas" height="220"></canvas>
          <div class="mt-3">
            <small class="text-muted">Occupied vs Available spots across all parking lots.</small>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card p-3 h-100">
          <h5>Reservations (Last 7 Days)</h5>
          <canvas ref="reservationsCanvas" height="220"></canvas>
          <div class="mt-3">
            <small class="text-muted">Number of reservations per day for the last 7 days.</small>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="card p-3">
          <h5 class="mb-3">Per-Lot Summary</h5>

          <div v-if="!lots.length && !loading" class="text-muted">No lots available.</div>

          <div class="table-responsive" v-else>
            <table class="table table-sm table-striped">
              <thead>
                <tr>
                  <th>Lot</th>
                  <th>Price</th>
                  <th>Total Spots</th>
                  <th>Available</th>
                  <th>Occupied</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="l in lots" :key="l.id">
                  <td>{{ l.prime_location_name }}</td>
                  <td>₹{{ l.price }}</td>
                  <td>{{ l.number_of_spots }}</td>
                  <td>{{ l.available_spots }}</td>
                  <td>{{ l.occupied_spots }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-3">
      <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { apiGet } from '../utils/api'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const occupancyCanvas = ref(null)
const reservationsCanvas = ref(null)
let occupancyChart = null
let reservationsChart = null

const lots = ref([])
const loading = ref(false)
const error = ref('')

/**
 * Build last N days labels and zero-initialized counts
 */
function lastNDays(n) {
  const days = []
  const counts = []
  const now = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(now.getDate() - i)
    const label = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    days.push(label)
    counts.push(0)
  }
  const startDate = new Date(now)
  startDate.setDate(now.getDate() - (n - 1))
  startDate.setHours(0,0,0,0)
  return { days, counts, startDate }
}

function isoToIndexMapper(startDate, n) {
  const start = new Date(startDate)
  start.setHours(0,0,0,0)
  return (iso) => {
    try {
      const d = new Date(iso)
      d.setHours(0,0,0,0)
      const diff = Math.round((d - start) / (1000 * 60 * 60 * 24))
      return diff
    } catch (e) {
      return -1
    }
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    // 1) fetch lots
    const lotsData = await apiGet('/admin/parkinglots')
    // lotsData is array of lot objects (may not include spot counts)
    lots.value = Array.isArray(lotsData) ? lotsData.map(l => ({ ...l })) : []

    // 2) For each lot, fetch its spots to compute available/occupied
    // Use parallel requests; this means multiple calls but no backend changes required.
    const spotPromises = lots.value.map(async (lot) => {
      try {
        const spots = await apiGet(`/admin/parkinglots/${lot.id}/spots`)
        // spots is array of spot objects with status
        const occupied = Array.isArray(spots) ? spots.filter(s => s.status === 'O').length : 0
        const available = Array.isArray(spots) ? spots.filter(s => s.status === 'A').length : 0
        lot.occupied_spots = occupied
        lot.available_spots = available
      } catch (e) {
        // If a per-lot spots request fails, fallback to zeros and continue
        lot.occupied_spots = 0
        lot.available_spots = lot.number_of_spots || 0
        console.warn(`Failed to load spots for lot ${lot.id}`, e)
      }
    })

    await Promise.all(spotPromises)

    // compute totals for occupancy chart
    let totalOccupied = 0
    let totalAvailable = 0
    lots.value.forEach(l => {
      totalOccupied += Number(l.occupied_spots || 0)
      totalAvailable += Number(l.available_spots || 0)
    })

    // 3) fetch reservations and build last-7-days histogram (use parking_timestamp)
    const reservations = await apiGet('/admin/reservations')
    const N = 7
    const { days, counts, startDate } = lastNDays(N)
    const mapIso = isoToIndexMapper(startDate, N)

    if (Array.isArray(reservations)) {
      reservations.forEach(r => {
        const idx = mapIso(r.parking_timestamp)
        if (idx >= 0 && idx < counts.length) counts[idx]++
      })
    }

    // 4) render charts
    renderOccupancyChart(totalOccupied, totalAvailable)
    renderReservationsChart(days, counts)
  } catch (e) {
    console.error('AdminSummary load error', e)
    error.value = e.message || 'Failed to load summary data'
  } finally {
    loading.value = false
  }
}

function renderOccupancyChart(occupied, available) {
  const ctx = occupancyCanvas.value && occupancyCanvas.value.getContext('2d')
  if (!ctx) return
  if (occupancyChart) occupancyChart.destroy()
  occupancyChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Occupied', 'Available'],
      datasets: [{
        data: [occupied, available],
        backgroundColor: ['#dc3545', '#198754']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: { mode: 'index' }
      }
    }
  })
}

function renderReservationsChart(labels, counts) {
  const ctx = reservationsCanvas.value && reservationsCanvas.value.getContext('2d')
  if (!ctx) return
  if (reservationsChart) reservationsChart.destroy()
  reservationsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Reservations',
        data: counts,
        backgroundColor: '#0d6efd'
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } }
      },
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index' }
      }
    }
  })
}

onMounted(() => {
  loadData()
})

onBeforeUnmount(() => {
  try { if (occupancyChart) occupancyChart.destroy() } catch (e) {}
  try { if (reservationsChart) reservationsChart.destroy() } catch (e) {}
})
</script>

<style scoped>
.card { margin-bottom: 1rem; }
</style>