<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
    <div class="container">
      <router-link class="navbar-brand" to="/">Smart Parking</router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav ms-auto">
          <li v-if="!isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/">Login</router-link>
          </li>
          <li v-if="!isLoggedIn" class="nav-item">
            <router-link class="nav-link" to="/register">Register</router-link>
          </li>
          <li v-if="isLoggedIn && isAdmin" class="nav-item">
            <router-link class="nav-link" to="/admin">Admin Dashboard</router-link>
          </li>
          <li v-if="isLoggedIn && !isAdmin" class="nav-item">
            <router-link class="nav-link" to="/user">User Dashboard</router-link>
          </li>
          <li v-if="isLoggedIn" class="nav-item">
            <a class="nav-link" href="#" @click.prevent="handleLogout">Logout</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { apiGet, apiPost } from '../utils/api'

const router = useRouter()
const isLoggedIn = ref(false)
const isAdmin = ref(false)

async function refreshAuth() {
  // Try to get authoritative user from backend; fallback to localStorage role
  try {
    const user = await apiGet('/me')
    if (user) {
      isLoggedIn.value = true
      isAdmin.value = user.role === 'admin'
      try { localStorage.setItem('role', user.role) } catch (e) {}
      return
    }
  } catch (e) {
    // ignore and fall back to localStorage below
  }
  const role = localStorage.getItem('role')
  isLoggedIn.value = !!role
  isAdmin.value = role === 'admin'
}

async function handleLogout() {
  try {
    await apiPost('/logout', {}) // clear server-side session
  } catch (e) {
    // ignore network errors; still clear client state
    console.warn('Logout request failed', e)
  }
  try { localStorage.removeItem('role') } catch (e) {}
  isLoggedIn.value = false
  isAdmin.value = false
  router.push('/')
}

// keep navbar state in sync across tabs
function onStorage() {
  refreshAuth()
}

onMounted(() => {
  refreshAuth()
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', onStorage)
})
</script>

<style scoped>
.navbar-brand { font-weight: 600; }
</style>