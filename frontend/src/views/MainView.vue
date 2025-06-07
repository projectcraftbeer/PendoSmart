<template>
  <div>
    <button @click="flagMatchingStrings" style="margin-bottom:1rem;">Flag Matching Strings</button>
    <span v-if="flagResult" :style="{color: flagResult?.success ? 'green' : 'red'}">{{ flagResult?.message }}</span>
    <TableView :projectId="projectId" :refreshKey="refreshKey" :locale="selectedLocale" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TableView from '../components/TableView.vue'
const projectId = ref('')
const selectedLocale = ref('ja-JP')
const refreshKey = ref(0)
const flagResult = ref<{success: boolean, message: string} | null>(null)

async function fetchProjectAndLocale() {
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-keys')
    if (!res.ok) throw new Error('Failed to fetch project id/locale')
    const data = await res.json()
    projectId.value = data.project_id || ''
    selectedLocale.value = data.locale || 'ja-JP'
  } catch (e: any) {
    console.error('Error fetching project and locale:', e.message)
  }
}
async function flagMatchingStrings() {
  flagResult.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/flag-matching-strings', { method: 'POST' })
    const data = await res.json()
    if (!res.ok || !data.success) throw new Error(data.message || 'Flagging failed')
    flagResult.value = { success: true, message: data.message || 'Flagged successfully' }
    refreshKey.value++ // trigger TableView refresh
  } catch (e: any) {
    flagResult.value = { success: false, message: e.message }
  }
}

onMounted(() => {
  fetchProjectAndLocale()
})


</script>
