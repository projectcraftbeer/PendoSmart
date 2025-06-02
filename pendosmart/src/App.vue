<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AdminSmartling from './components/AdminSmartling.vue'
import TableView from './components/TableView.vue'

interface StringPair {
  id: number
  source: string
  japanese: string
  confidence?: number
  reason?: string
  suggestion?: string
}

const strings = ref<StringPair[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showAdmin = ref(false)

async function fetchStrings() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('http://localhost:8000/strings')
    if (!res.ok) throw new Error('Failed to fetch strings')
    strings.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function evaluateString(row: StringPair) {
  try {
    const res = await fetch('http://localhost:8000/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: row.id, source: row.source, japanese: row.japanese })
    })
    if (!res.ok) throw new Error('Evaluation failed')
    const updated = await res.json()
    // Update the row in the table
    const idx = strings.value.findIndex(s => s.id === row.id)
    if (idx !== -1) strings.value[idx] = updated
  } catch (e: any) {
    alert(e.message)
  }
}

onMounted(fetchStrings)
</script>

<template>
  <div>
    <button @click="showAdmin = !showAdmin" style="float:right;">{{ showAdmin ? 'Back' : 'Admin' }}</button>
    <h1>Smartling String Review</h1>
    <AdminSmartling v-if="showAdmin" />
    <div v-else>
      <TableView />
    </div>
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
</style>
