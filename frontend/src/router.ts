import { createRouter, createWebHistory } from 'vue-router'
// Add global navigation guard for authentication
import { useAzureAD } from './composables/useAzureAD'

import MainView from './views/MainView.vue'
import AdminSmartling from './components/AdminSmartling.vue'
import Login from './pages/Login.vue'

const routes = [
  { path: '/', name: 'Main', component: MainView },
  { path: '/admin', name: 'Admin', component: AdminSmartling },
  { path: '/login', name: 'Login', component: Login },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})



router.beforeEach((to, _from, next) => {
  const { isAuthenticated, handleRedirect, getAccessToken } = useAzureAD()
  // Protect /admin and root routes
  if (to.path === '/admin' || to.path === '/') {
    handleRedirect()
    
    if (!isAuthenticated.value) {
      next('/login')
      return
    }
    // Restrict /admin to users with 'Admin' app role
    if (to.path === '/admin') {
      getAccessToken().then(token => {
        // Decode JWT to get roles claim
      const base64Url = token.split('.')[1]
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      }).join(''))
      const payload = JSON.parse(jsonPayload)
      // Log the decoded payload for debugging
      
      const roles = payload.roles || []
      if (Array.isArray(roles) && roles.includes('admin')) {
        next()
      } else {
        next('/') // redirect to main if not admin
      }
      }).catch(() => {
      next('/login')
      })
      return // wait for async check
    }
  }
  next()
})

export default router
