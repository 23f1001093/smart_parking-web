<template>
  <div class="container py-3">
    <h3>All Registered Users</h3>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <table class="table table-striped" v-if="users.length">
      <thead>
        <tr>
          <th>UserID</th>
          <th>Username</th>
          <th>Email</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.username }}</td>
          <td>{{ u.email }}</td>
        </tr>
      </tbody>
    </table>

    <div v-else class="text-muted">No users found or loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiGet } from '../utils/api'

const users = ref([])
const error = ref('')

async function fetchUsers() {
  error.value = ''
  try {
    const data = await apiGet('/admin/users')
    users.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = e.message || 'Failed to load users'
  }
}

onMounted(fetchUsers)
</script>