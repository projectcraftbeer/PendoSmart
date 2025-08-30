<script setup lang="ts">
import { useAzureAD } from '../composables/useAzureAD'
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const { login, logout, isAuthenticated, account, handleRedirect } = useAzureAD()
const router = useRouter()

function initPendo() {
  // Ensure Pendo script is loaded and pendo is available
  if (typeof window !== 'undefined' && (window as any).pendo) {
    (window as any).pendo.initialize({
      visitor: {
        id: account.value?.username
      },
      account:{
        id: account.value?.tenantId
      }
    });
  } else {
    console.warn('Pendo is not loaded.');
  }
}

onMounted(() => {
  if(isAuthenticated.value) {
    initPendo()
  }
  handleRedirect()
})

// Redirect to root page after successful login
watch(isAuthenticated, (val) => {

  if (val) {
    initPendo()
    router.push('/')
  }
})
</script>

<template>
  <div class="login-page">
    <h2>Login</h2>
    <div v-if="!isAuthenticated">
      <button @click="login">Sign in with Azure AD</button>
    </div>
    <div v-else>
      <p>Welcome, <b>{{ account?.name || account?.username }}</b></p>
      <button @click="logout">Sign out</button>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  max-width: 400px;
  margin: 4rem auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #fafafa;
  text-align: center;
}
.login-page button {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  font-size: 1.1em;
}
</style>
