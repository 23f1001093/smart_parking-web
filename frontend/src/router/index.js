import { createRouter, createWebHistory } from 'vue-router'

import Login from '../components/Login.vue'
import Register from '../components/Register.vue'
import UserDashboard from '../components/UserDashboard.vue'
import ParkingLots from '../components/ParkingLots.vue'
import MyReservations from '../components/MyReservations.vue'
import AdminDashboard from '../components/AdminDashboard.vue'
import AdminLots from '../components/AdminLots.vue'
import AdminUsers from '../components/AdminUsers.vue'
import LotStatus from '../components/LotStatus.vue'
import AdminSummary from '../components/AdminSummary.vue' // newly added summary page
import LotSpots from '../components/LotSpots.vue' // new

const routes = [
  { path: '/', component: Login },
  { path: '/register', component: Register },
  { path: '/user', component: UserDashboard },
  { path: '/lots', component: ParkingLots },
  { path: '/reservations', component: MyReservations },
  { path: '/admin', component: AdminDashboard },
  { path: '/admin/lots', component: AdminLots },
  { path: '/admin/users', component: AdminUsers },
  { path: '/admin/status', component: LotStatus },
  { path: '/admin/summary', component: AdminSummary, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/lots/:id/spots', component: LotSpots, meta: { requiresAuth: true, requiresAdmin: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
