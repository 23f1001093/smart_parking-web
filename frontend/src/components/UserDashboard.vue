<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-start mb-3">
      <div>
        <h2>User Dashboard</h2>
        <p class="text-muted">Welcome back, <strong>{{ user?.username || 'User' }}</strong></p>
      </div>
      <div class="text-end">
        <router-link to="/lots" class="btn btn-outline-primary me-2">View Parking Lots</router-link>
        <router-link to="/reservations" class="btn btn-success">My Reservations</router-link>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="row mb-4">
      <div class="col-md-4">
        <div class="card p-3">
          <h6 class="mb-2">Active Reservations</h6>
          <div class="display-6">{{ activeCount }}</div>
          <small class="text-muted">Currently parked</small>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card p-3">
          <h6 class="mb-2">Past Reservations</h6>
          <div class="display-6">{{ pastCount }}</div>
          <small class="text-muted">Completed reservations</small>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card p-3">
          <h6 class="mb-2">Available Lots</h6>
          <div class="display-6">{{ availableLots }}</div>
          <small class="text-muted">Lots with at least one spot</small>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        Recent Reservations
      </div>
      <div class="card-body p-0">
        <table class="table mb-0">
          <thead>
            <tr>
              <th>Spot</th>
              <th>Vehicle</th>
              <th>In</th>
              <th>Out</th>
              <th>Cost</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reservations" :key="r.id">
              <td>{{ r.spot_id }}</td>
              <td>{{ r.vehicle_number }}</td>
              <td>{{ r.parking_timestamp && new Date(r.parking_timestamp).toLocaleString() }}</td>
              <td>{{ r.leaving_timestamp && new Date(r.leaving_timestamp).toLocaleString() }}</td>
              <td>₹{{ r.parking_cost ?? '—' }}</td>
              <td>
                <span v-if="!r.leaving_timestamp" class="badge bg-warning text-dark">Active</span>
                <span v-else class="badge bg-success">Completed</span>
              </td>
              <td>
                <button
                  v-if="!r.leaving_timestamp"
                  class="btn btn-sm btn-danger"
                  @click="releaseReservation(r.id)"
                >Release</button>
                <small v-else class="text-muted">—</small>
              </td>
            </tr>
            <tr v-if="!reservations.length">
              <td colspan="7" class="text-center text-muted py-3">No reservations found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiGet, apiPost } from '../utils/api'

const router = useRouter()
const user = ref(null)
const reservations = ref([])
const availableLots = ref(0)
const activeCount = ref(0)
const pastCount = ref(0)
const error = ref('')

async function loadUser() {
  try {
    user.value = await apiGet('/me')
  } catch (e) {
    // not authenticated -> redirect to login
    router.push('/')
  }
}

async function loadReservations() {
  try {
    const data = await apiGet('/my/reservations')
    reservations.value = Array.isArray(data) ? data : []
    activeCount.value = reservations.value.filter(r => !r.leaving_timestamp).length
    pastCount.value = reservations.value.filter(r => r.leaving_timestamp).length
  } catch (e) {
    console.error('loadReservations error', e)
    error.value = e.message || 'Failed to load reservations'
  }
}

async function loadLotsSummary() {
  try {
    const lots = await apiGet('/parkinglots')
    if (Array.isArray(lots)) {
      availableLots.value = lots.filter(l => (l.available_spots ?? 0) > 0).length
    } else {
      availableLots.value = 0
    }
  } catch (e) {
    console.error('loadLotsSummary error', e)
    // non-fatal; show zero
    availableLots.value = 0
  }
}

async function releaseReservation(id) {
  if (!confirm('Release this spot?')) return
  try {
    await apiPost(`/reservations/${id}/release`, {})
    // refresh lists
    await loadReservations()
    await loadLotsSummary()
  } catch (e) {
    console.error('release error', e)
    alert(e.message || 'Release failed')
  }
}

onMounted(async () => {
  await loadUser()
  await Promise.all([loadReservations(), loadLotsSummary()])
})
</script>

<style scoped>
.display-6 {
  font-size: 2rem;
  font-weight: 600;
}
.card + .card {
  margin-top: 1rem;
}
</style>