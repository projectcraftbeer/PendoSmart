import { createRouter, createWebHistory } from 'vue-router'

import MainView from './views/MainView.vue'
import AdminSmartling from './components/AdminSmartling.vue'

const routes = [
  { path: '/', name: 'Main', component: MainView },
  { path: '/admin', name: 'Admin', component: AdminSmartling },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
