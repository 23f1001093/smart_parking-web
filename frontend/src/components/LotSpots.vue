<template>
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-start mb-3">
      <h3>Parking Spots — {{ lotName || `Lot ${lotId}` }}</h3>
      <div>
        <router-link :to="'/admin/lots'" class="btn btn-outline-secondary me-2">Back to Lots</router-link>
        <button class="btn btn-sm btn-primary" @click="reload" :disabled="loading">Reload</button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
    </div>

    <div v-if="!loading && spots.length">
      <div class="table-responsive">
        <table class="table table-striped align-middle">
          <thead>
            <tr>
              <th>Spot ID</th>
              <th>Status</th>
              <th>Active</th>
              <th>Occupied By</th>
              <th>User ID</th>
              <th>Reserved At</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in spots" :key="s.id">
              <td>{{ s.id }}</td>
              <td>
                <span :class="s.status === 'O' ? 'badge bg-danger' : 'badge bg-success'">
                  {{ s.status === 'O' ? 'Occupied' : 'Available' }}
                </span>
              </td>
              <td>{{ s.is_active ? 'Yes' : 'No' }}</td>
              <td>{{ s.vehicle_number || '—' }}</td>
              <td>{{ s.user_id || '—' }}</td>
              <td>
                <small v-if="s.vehicle_number && s.reservation_timestamp">{{ new Date(s.reservation_timestamp).toLocaleString() }}</small>
                <span v-else class="text-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else-if="!loading" class="text-muted">No spots found for this lot.</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiGet } from '../utils/api'

const route = useRoute()
const router = useRouter()
const lotId = Number(route.params.id)
const lotName = ref('')
const spots = ref([])
const loading = ref(false)
const error = ref('')

if (!lotId) {
  // invalid route — go back
  router.push('/admin/lots')
}

async function loadSpots() {
  loading.value = true
  error.value = ''
  try {
    // GET /api/admin/parkinglots/<id>/spots
    const data = await apiGet(`/admin/parkinglots/${lotId}/spots`)
    // The API returns spot objects; augment if needed
    spots.value = Array.isArray(data) ? data.map(s => {
      // some spot entries include vehicle/user when occupied as we implemented server-side
      // include a best-effort reservation timestamp field if backend supplied it (some formats vary)
      return {
        id: s.id,
        status: s.status,
        is_active: s.is_active,
        vehicle_number: s.vehicle_number || null,
        user_id: s.user_id || null,
        reservation_timestamp: s.parking_timestamp || s.reservation_timestamp || null
      }
    }) : []
    // try to set lotName from route state or a quick fetch of lot list
    const lots = await apiGet('/admin/parkinglots')
    const found = Array.isArray(lots) ? lots.find(l => Number(l.id) === lotId) : null
    if (found) lotName.value = found.prime_location_name
  } catch (e) {
    console.error('loadSpots error', e)
    error.value = e.message || 'Failed to load spots'
  } finally {
    loading.value = false
  }
}

function reload() {
  loadSpots()
}

onMounted(loadSpots)
</script>

<style scoped>
.table td, .table th { vertical-align: middle; }
</style>