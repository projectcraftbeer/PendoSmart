<template>
  <div>
        <div style="margin-top:2rem;">
      <button @click="fetchAllTranslations" :disabled="fetchTranslationsLoading || !projectId">
        {{ fetchTranslationsLoading ? 'Fetching...' : 'Fetch All Translated Strings' }}
      </button>
      <button @click="fetchAllJobFiles" :disabled="fetchJobFilesLoading || !projectId">
        {{ fetchJobFilesLoading ? 'Fetching...' : 'Fetch All Job File URIs' }}
      </button>
      <span v-if="fetchTranslationsResult" style="margin-left:1rem;">{{ fetchTranslationsResult }}</span>
    </div>
   
    <span v-if="flagResult" :style="{color: flagResult?.success ? 'green' : 'red'}">{{ flagResult?.message }}</span>
    <TableView :projectId="projectId" :refreshKey="refreshKey" :locale="selectedLocale" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TableView from '../components/TableView.vue'
const projectId = ref('d7fbf6904')
const selectedLocale = ref('ja-JP')
const refreshKey = ref(0)
const flagResult = ref<{success: boolean, message: string} | null>(null)
const fetchJobFilesLoading = ref(false)
const fetchJobFilesResult = ref<string | null>(null)
import { useAzureAD } from '../composables/useAzureAD'
const { getAccessToken } = useAzureAD()

async function fetchAllJobFiles() {
  if (!projectId.value) {
    fetchJobFilesResult.value = 'No project ID set.'
    return
  }
  fetchJobFilesLoading.value = true
  fetchJobFilesResult.value = null
  try {
    const token = await getAccessToken()
    const res = await fetch('https://smartlingbe.yellowpond-6d891245.japaneast.azurecontainerapps.io/admin/smartling-job-files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ project_id: projectId.value })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to fetch job files')
    fetchJobFilesResult.value = `Fetched and saved ${data.saved} job/file pairs.`
  } catch (e: any) {
    fetchJobFilesResult.value = e.message
  } finally {
    fetchJobFilesLoading.value = false
  }
}


// async function fetchProjectAndLocale() {
//   try {
//     // Import and use AzureAD composable to get JWT
//     const { getAccessToken } = useAzureAD()
//     const token = await getAccessToken()
//     const res = await fetch('/admin/smartling-keys', {
//       headers: { 'Authorization': `Bearer ${token}` }
//     })
//     if (!res.ok) throw new Error('Failed to fetch project id/locale')
//     const data = await res.json()
//     projectId.value = data.project_id || ''
//     selectedLocale.value = data.locale || 'ja-JP'
//   } catch (e: any) {
//     console.error('Error fetching project and locale:', e.message)
//   }
// }

const fetchTranslationsLoading = ref(false)
const fetchTranslationsResult = ref<string | null>(null)
const locale = ref('ja-JP')
async function fetchAllTranslations() {
  if (!projectId.value) {
    fetchTranslationsResult.value = 'No project ID set.'
    return
  }
  fetchTranslationsLoading.value = true
  fetchTranslationsResult.value = null
  try {
    const token = await getAccessToken()
    const res = await fetch('https://smartlingbe.yellowpond-6d891245.japaneast.azurecontainerapps.io/admin/smartling-fetch-translations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ project_id: projectId.value, locale: locale.value })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Failed to fetch translations')
    fetchTranslationsResult.value = (data && typeof data.saved !== 'undefined')
      ? `Fetched and saved ${data.saved} translations.`
      : 'Fetch completed.'
  } catch (e: any) {
    fetchTranslationsResult.value = e.message
  } finally {
    fetchTranslationsLoading.value = false
  }
}

onMounted(() => {
  
})


</script>
