<template>
  <div class="container py-3">
    <h4>Available Parking Lots</h4>
    <div class="row">
      <div v-for="lot in lots" :key="lot.id" class="col-md-4 mb-3">
        <div class="card shadow">
          <div class="card-body">
            <h5>{{ lot.prime_location_name }}</h5>
            <p>{{ lot.address }}, {{ lot.pin_code }}</p>
            <span class="badge bg-info text-dark mb-2">₹{{ lot.price }}</span>
            <span class="badge" :class="lot.available_spots > 0 ? 'bg-success' : 'bg-danger'">
              {{ lot.available_spots > 0 ? `Available: ${lot.available_spots}` : 'Full' }}
            </span>
          </div>
          <div class="card-footer">
            <ReserveForm v-if="lot.available_spots > 0" :lot="lot" @success="fetchLots"/>
          </div>
        </div>
      </div>
    </div>
    <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ReserveForm from './ReserveForm.vue'
const lots = ref([])
const error = ref('')

async function fetchLots() {
  error.value = ''
  try {
    const res = await fetch('/api/parkinglots', { credentials: 'include' })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (e) {}

    if (res.ok) {
      // backend sends available_spots in each lot in your routes; if not, compute here
      lots.value = Array.isArray(data) ? data : []
    } else {
      error.value = (data && data.message) || text || res.statusText || 'Failed to load parking lots'
    }
  } catch (e) {
    console.error('fetch lots error', e)
    error.value = 'Network error'
  }
}

onMounted(fetchLots)
</script>