<template>
  <div class="container py-4">
    <h4>My Reservations</h4>
    <table class="table" v-if="reservations.length">
      <thead>
        <tr>
          <th>Spot ID</th>
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
          <td>{{ r.parking_cost }}</td>
          <td>
            <span v-if="!r.leaving_timestamp" class="badge bg-warning text-dark">Active</span>
            <span v-else class="badge bg-success">Completed</span>
          </td>
          <td>
            <button 
              v-if="!r.leaving_timestamp" 
              class="btn btn-danger btn-sm"
              @click="release(r.id)">Release</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="text-muted">No reservations found.</div>
    <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>

    <!-- EXPORT BUTTON AND FEEDBACK -->
    <div class="mt-4">
      <button class="btn btn-primary" @click="exportData" :disabled="exporting">
        {{ exporting ? "Exporting..." : "Export My Parking Data" }}
      </button>
      <div v-if="exportMsg" class="alert alert-info mt-2">{{ exportMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const reservations = ref([])
const error = ref('')
const exporting = ref(false)
const exportMsg = ref('')

async function fetchReservations() {
  error.value = ''
  try {
    const res = await fetch('/api/my/reservations', { credentials: 'include' })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (e) {}

    if (res.ok) {
      reservations.value = data || []
    } else {
      error.value = (data && data.message) || text || res.statusText || 'Failed to load reservations'
    }
  } catch (e) {
    console.error('fetch reservations error', e)
    error.value = 'Network error'
  }
}

async function release(reservation_id) {
  if (!confirm('Release this spot?')) return
  try {
    const res = await fetch('/api/reservations/' + reservation_id + '/release', {
      method: 'POST',
      credentials: 'include'
    })
    if (res.ok) {
      await fetchReservations()
    } else {
      const text = await res.text()
      let data = null
      try { data = text ? JSON.parse(text) : null } catch (e) {}
      alert((data && data.message) || text || res.statusText || 'Release failed.')
    }
  } catch (e) {
    console.error('release error', e)
    alert('Network error')
  }
}

// NEW: Export data handler
async function exportData() {
  exporting.value = true
  exportMsg.value = ''
  try {
    // Get your user's email via /api/me
    const meRes = await fetch('/api/me', { credentials: 'include' })
    const userData = await meRes.json()
    const email = userData.email

    // Call export endpoint
    const expRes = await fetch('/api/my/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email })
    })
    const text = await expRes.text()
    let respData = null
    try { respData = text ? JSON.parse(text) : null } catch (e) {}

    exportMsg.value = expRes.ok
      ? "Export started! Check your email shortly."
      : (respData && respData.message) || text || expRes.statusText || 'Export failed.'
  } catch (e) {
    exportMsg.value = 'Failed to start export.'
  } finally {
    exporting.value = false
  }
}

onMounted(fetchReservations)
</script>