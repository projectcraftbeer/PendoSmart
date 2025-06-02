<script setup lang="ts">
import { ref, onMounted } from 'vue'

const userId = ref('')
const secret = ref('')
const projectId = ref('')
const saved = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchKeys() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-keys')
    if (!res.ok) throw new Error('Failed to fetch keys')
    const data = await res.json()
    userId.value = data.user_id || ''
    projectId.value = data.project_id || ''
    secret.value = data.secret ? '********' : ''
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function saveKeys() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId.value, secret: secret.value, project_id: projectId.value })
    })
    if (!res.ok) throw new Error('Failed to save keys')
    saved.value = true
    setTimeout(() => (saved.value = false), 2000)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchKeys)
</script>

<template>
  <div class="admin-page">
    <h2>Smartling API Keys</h2>
    <form @submit.prevent="saveKeys">
      <div>
        <label>User ID:</label>
        <input v-model="userId" required />
      </div>
      <div>
        <label>Secret:</label>
        <input v-model="secret" type="password" required />
      </div>
      <div>
        <label>Project ID:</label>
        <input v-model="projectId" required />
      </div>
      <button type="submit" :disabled="loading">Save</button>
      <span v-if="saved" style="color:green;">Saved!</span>
      <span v-if="error" style="color:red;">{{ error }}</span>
    </form>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #fafafa;
}
.admin-page label {
  display: inline-block;
  width: 100px;
}
.admin-page input {
  width: 220px;
  margin-bottom: 1rem;
}
.admin-page button {
  margin-top: 1rem;
}
</style>
