<template>
  <form @submit.prevent="reserve">
    <input v-model="vehicle_number" class="form-control mb-2" required placeholder="Vehicle Number" />
    <input v-model="remarks" class="form-control mb-2" placeholder="Remarks (optional)" />
    <button class="btn btn-primary w-100" :disabled="loading">Reserve</button>
    <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>
  </form>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps(['lot'])
const emit = defineEmits(['success'])
const vehicle_number = ref('')
const remarks = ref('')
const error = ref('')
const loading = ref(false)

async function reserve() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetch(`/api/parkinglots/${props.lot.id}/reserve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ vehicle_number: vehicle_number.value, remarks: remarks.value })
    })

    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (e) {}

    if (res.ok) {
      emit('success')
      vehicle_number.value = ''
      remarks.value = ''
    } else {
      error.value = (data && data.message) || text || res.statusText || 'Reservation failed'
    }
  } catch (e) {
    console.error('reserve error', e)
    error.value = 'Network error'
  } finally {
    loading.value = false
  }
}
</script>