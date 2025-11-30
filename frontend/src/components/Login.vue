<template>
  <div class="container my-5">
    <div class="row justify-content-center">
      <div class="col-md-4">
        <div class="card p-4 shadow">
          <h3 class="card-title mb-3">Login</h3>
          <form @submit.prevent="login">
            <div class="mb-3">
              <input v-model="email" type="email" class="form-control" placeholder="Email" required />
            </div>
            <div class="mb-3">
              <input v-model="password" type="password" class="form-control" placeholder="Password" required />
            </div>
            <button class="btn btn-primary w-100" :disabled="loading">Login</button>
          </form>
          <div class="mt-3 text-center">
            <router-link to="/register">New user? Register</router-link>
          </div>
          <div v-if="error" class="alert alert-danger mt-2">{{ error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

async function login() {
  loading.value = true
  error.value = ''
  try {
    // Use /api/login so Vite can proxy it to the Flask backend (see vite.config.js)
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    // Safely handle responses that may not be JSON or may have empty bodies
    const contentType = res.headers.get('content-type') || ''
    let data = null
    let textBody = ''

    if (contentType.includes('application/json')) {
      try {
        data = await res.json()
      } catch (e) {
        // JSON parsing failed; fall back to text
        textBody = await res.text()
      }
    } else {
      textBody = await res.text()
      try { data = textBody ? JSON.parse(textBody) : null } catch (e) { /* not JSON */ }
    }

    if (res.ok) {
      // Successful response
      if (data && data.role) {
        localStorage.setItem('role', data.role)
        router.push(data.role === 'admin' ? '/admin' : '/user')
      } else {
        // backend succeeded but didn't return role; go to default route
        router.push('/user')
      }
    } else {
      // Try to extract an error message from JSON or text, else use statusText
      const msg = (data && data.message) || textBody || res.statusText || 'Login failed'
      error.value = msg
    }
  } catch (e) {
    console.error('login error', e)
    error.value = 'Network error'
  } finally {
    loading.value = false
  }
}
</script>