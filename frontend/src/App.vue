<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView, RouterLink } from 'vue-router'
import { useAzureAD } from './composables/useAzureAD'

const nightMode = ref(false)
function toggleNightMode() {
  nightMode.value = !nightMode.value
  document.body.classList.toggle('night', nightMode.value)
}

const { isAuthenticated, account } = useAzureAD()

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
  if (isAuthenticated.value) {
    initPendo()
  }
})
</script>

<template>
  <div :class="{ night: nightMode }">
    <button @click="toggleNightMode" style="float:right;">{{ nightMode ? 'Day Mode' : 'Night Mode' }}</button>

    <nav>
      <RouterLink to="/" style="margin-right: 0.5rem;">Main</RouterLink>
      <RouterLink to="/admin" style="margin-right: 0.5rem;">Admin</RouterLink>
      <RouterLink v-if="!isAuthenticated" to="/login" style="margin-right: 0.5rem;">Login</RouterLink>
      <RouterLink v-if="isAuthenticated" to="/login" style="margin-right: 0.5rem;">Logout</RouterLink>
      <span v-else style="margin-left:1rem;">Welcome, <b>{{ account?.name || account?.username }}</b></span>
    </nav>

    <h1>Dumbling String Review</h1>
    <RouterView />
  </div>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 2rem;
}
th, td {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: left;
}
th {
  background: #f0f0f0;
}
button {
  margin: 0.2rem 0;
}
.night {
  background: #181a1b;
  color: #7b8aa1;
}
.night table {
  background: #23272e;
  color: #e8eaed;
}
.night th, .night td {
  border-color: #333;
}
.night th {
  background: #23272e;
}
.night button {
  background: #23272e;
  color: #e8eaed;
  border: 1px solid #444;
}
body.night {
  background: #181a1b !important;
  color: #e8eaed !important;
}
</style>
