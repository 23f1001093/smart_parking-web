<template>
  <div class="container py-3">
    <h3>Admin: Manage Parking Lots</h3>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="card mb-3 p-3">
      <h5>Create New Parking Lot</h5>
      <form @submit.prevent="createLot" class="row g-2">
        <div class="col-md-4">
          <input v-model="form.prime_location_name" class="form-control" placeholder="Prime location name" required />
        </div>
        <div class="col-md-4">
          <input v-model="form.address" class="form-control" placeholder="Address" />
        </div>
        <div class="col-md-2">
          <input v-model="form.pin_code" class="form-control" placeholder="Pin code" />
        </div>
        <div class="col-md-2">
          <input v-model.number="form.price" type="number" class="form-control" placeholder="Price" required />
        </div>
        <div class="col-md-2">
          <input v-model.number="form.number_of_spots" type="number" class="form-control" placeholder="Spots" min="1" required />
        </div>
        <div class="col-md-2 d-grid">
          <button class="btn btn-success" :disabled="creating">{{ creating ? 'Creating...' : 'Create' }}</button>
        </div>
      </form>
    </div>

    <div class="table-responsive">
      <table class="table table-striped align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Prime name</th>
            <th>Address</th>
            <th>Pin</th>
            <th>Price</th>
            <th>Spots</th>
            <th>Available</th>
            <th>Active</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="l in lots" :key="l.id">
            <td>{{ l.id }}</td>
            <td>{{ l.prime_location_name }}</td>
            <td>{{ l.address }}</td>
            <td>{{ l.pin_code }}</td>
            <td>₹{{ l.price }}</td>
            <td>{{ l.number_of_spots }}</td>
            <td>{{ l.available_spots ?? '—' }}</td>
            <td>{{ l.is_active ? 'Yes' : 'No' }}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-primary me-1" @click="editLot(l)">Edit</button>
              <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteLot(l.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="loading" class="text-center py-3">
      <div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'

const lots = ref([])
const loading = ref(false)
const error = ref('')
const creating = ref(false)
const deleting = ref(false)

const form = ref({
  prime_location_name: '',
  address: '',
  pin_code: '',
  price: 0,
  number_of_spots: 1
})

async function fetchLots() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiGet('/admin/parkinglots')
    lots.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = e.message || 'Failed to load lots'
  } finally {
    loading.value = false
  }
}

async function createLot() {
  creating.value = true
  error.value = ''
  try {
    const payload = {
      prime_location_name: form.value.prime_location_name,
      address: form.value.address,
      pin_code: form.value.pin_code,
      price: Number(form.value.price),
      number_of_spots: Number(form.value.number_of_spots)
    }
    await apiPost('/admin/parkinglots', payload)
    form.value = { prime_location_name: '', address: '', pin_code: '', price: 0, number_of_spots: 1 }
    await fetchLots()
  } catch (e) {
    error.value = e.message || 'Failed to create lot'
  } finally {
    creating.value = false
  }
}

async function deleteLot(id) {
  if (!confirm('Delete this parking lot?')) return
  deleting.value = true
  error.value = ''
  try {
    await apiDelete(`/admin/parkinglots/${id}`)
    await fetchLots()
  } catch (e) {
    error.value = e.message || 'Failed to delete lot'
  } finally {
    deleting.value = false
  }
}

async function editLot(lot) {
  const newName = prompt('Prime location name:', lot.prime_location_name)
  if (newName === null) return
  const newPrice = prompt('Price:', String(lot.price))
  if (newPrice === null) return
  const newSpots = prompt('Number of spots:', String(lot.number_of_spots))
  if (newSpots === null) return

  try {
    const payload = {
      prime_location_name: newName,
      price: Number(newPrice),
      number_of_spots: Number(newSpots)
    }
    await apiPut(`/admin/parkinglots/${lot.id}`, payload)
    await fetchLots()
  } catch (e) {
    alert(e.message || 'Failed to update lot')
  }
}

onMounted(fetchLots)
</script>