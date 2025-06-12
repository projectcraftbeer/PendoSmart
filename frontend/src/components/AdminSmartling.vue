<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
// TODO: cleanup 
const projectOptions = ref<string[]>([])
const projectLoading = ref(false)
const projectError = ref<string | null>(null)
const userId = ref('')
const secret = ref('')
const projectId = ref('')
const accountId = ref('')
const saved = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)
const accessToken = ref('')
const authLoading = ref(false)
const authError = ref<string | null>(null)
const jobOptions = ref<{ jobId: string, jobName: string }[]>([])
const jobId = ref('')
const jobLoading = ref(false)
const jobError = ref<string | null>(null)
const fetchJobFilesLoading = ref(false)
const fetchJobFilesResult = ref<string | null>(null)

async function fetchProjectOptions() {
  projectLoading.value = true
  projectError.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-projects')
    if (!res.ok) throw new Error('Failed to fetch Smartling projects')
    const data = await res.json()
    if (Array.isArray(data)) {
      projectOptions.value = data
    } else if (data.error) {
      projectError.value = data.error
    }
  } catch (e: any) {
    projectError.value = e.message
  } finally {
    projectLoading.value = false
  }
}

async function getSmartlingToken() {
  authLoading.value = true
  authError.value = null
  accessToken.value = ''
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId.value,
        secret: secret.value
      })
    })
    if (!res.ok) throw new Error('Smartling auth failed')
    const data = await res.json()
    accessToken.value = data?.response?.data?.accessToken || ''
    if (!accessToken.value) throw new Error('No access token returned')
  } catch (e: any) {
    authError.value = e.message
  } finally {
    authLoading.value = false
  }
}

async function fetchJobOptions() {
  if (!projectId.value) {
    jobOptions.value = []
    return
  }
  jobLoading.value = true
  jobError.value = null
  try {
    const res = await fetch(`http://localhost:8000/admin/smartling-jobs?project_id=${encodeURIComponent(projectId.value)}`)
    if (!res.ok) throw new Error('Failed to fetch Smartling jobs')
    const data = await res.json()
    if (Array.isArray(data)) {
      jobOptions.value = data
    } else if (data.error) {
      jobError.value = data.error
    }
  } catch (e: any) {
    jobError.value = e.message
  } finally {
    jobLoading.value = false
  }
}

async function fetchKeys() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-keys')
    if (!res.ok) throw new Error('Failed to fetch keys')
    const data = await res.json()
    userId.value = data.user_id || ''
    projectId.value = data.project_id || ''
    secret.value = data.secret || ''
    accountId.value = data.account_id || ''
    jobId.value = data.job_id || ''
    locale.value = data.locale || 'ja-JP'
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
    const payload: any = { user_id: userId.value, project_id: projectId.value, account_id: accountId.value, job_id: jobId.value, locale: locale.value };
    if (secret.value !== '********') {
      payload.secret = secret.value;
    }
    const res = await fetch('http://localhost:8000/admin/smartling-keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
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

async function fetchAllJobFiles() {
  if (!projectId.value) {
    fetchJobFilesResult.value = 'No project ID set.'
    return
  }
  fetchJobFilesLoading.value = true
  fetchJobFilesResult.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-job-files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
    const res = await fetch('http://localhost:8000/admin/smartling-fetch-translations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

const modelDownloadFlag = ref(false)
const modelDownloadLoading = ref(false)
const modelDownloadError = ref<string | null>(null)

async function fetchModelDownloadFlag() {
  try {
    const res = await fetch('http://localhost:8000/admin/get-model-download-flag')
    if (!res.ok) throw new Error('Failed to fetch model download flag')
    const data = await res.json()
    modelDownloadFlag.value = !!data.download_model
  } catch (e: any) {
    modelDownloadError.value = e.message
  }
}

async function setModelDownloadFlag(flag: boolean) {
  modelDownloadLoading.value = true
  modelDownloadError.value = null
  try {
    const res = await fetch('http://localhost:8000/admin/set-model-download-flag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ download_model: flag })
    })
    if (!res.ok) throw new Error('Failed to set model download flag')
    modelDownloadFlag.value = flag
  } catch (e: any) {
    modelDownloadError.value = e.message
  } finally {
    modelDownloadLoading.value = false
  }
}

watch(projectId, fetchJobOptions)
onMounted(() => {
  fetchKeys()
  fetchProjectOptions()
  fetchModelDownloadFlag()
})
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
        <input v-model="secret" required />
      </div>
      <div>
        <label>Account ID:</label>
        <input v-model="accountId" placeholder="Enter Account ID" />
      </div>
      <div>
        <label>Project ID:</label>
        <input v-if="projectOptions.length === 0" v-model="projectId" placeholder="Enter Project ID" />
        <select v-else v-model="projectId">
          <option value="">Select a project</option>
          <option v-for="option in projectOptions" :key="option" :value="option.split(' - ')[0]">
            {{ option }}
          </option>
        </select>
        <span v-if="projectLoading">Loading projects...</span>
        <span v-if="projectError" style="color:red;">{{ projectError }}</span>
      </div>
      <!-- <div>
        <label>Job:</label>
        <select v-if="jobOptions.length > 0" v-model="jobId">
          <option value="">Select a job</option>
          <option v-for="job in jobOptions" :key="job.jobId" :value="job.jobId">
            {{ job.jobName }} ({{ job.jobId }})
          </option>
        </select>
        <input v-else v-model="jobId" placeholder="Enter Job ID" />
        <span v-if="jobLoading">Loading jobs...</span>
        <span v-if="jobError" style="color:red">{{ jobError }}</span>
      </div> -->
      <div>
        <label>Locale:</label>
        <input v-model="locale" placeholder="e.g. ja-JP" />
      </div>
      <button type="submit" :disabled="loading">Save</button>
      <span v-if="saved" style="color:green;">Saved!</span>
      <span v-if="error" style="color:red;">{{ error }}</span>
      <hr />
      <button type="button" @click="getSmartlingToken" :disabled="authLoading">Get Smartling Access Token</button>
      <div v-if="authLoading">Authenticating...</div>
      <div v-if="accessToken" style="word-break:break-all; color:green;">Access Token: {{ accessToken }}</div>
      <div v-if="authError" style="color:red;">{{ authError }}</div>
    </form>
    <div>
      <h3>Fetch All Job/File URIs</h3>
      <button @click="fetchAllJobFiles" :disabled="fetchJobFilesLoading || !projectId">
        {{ fetchJobFilesLoading ? 'Fetching...' : 'Fetch All Job File URIs' }}
      </button>
      <span v-if="fetchJobFilesResult" style="margin-left:1rem;">{{ fetchJobFilesResult }}</span>
      <div v-if="error" style="color:red;">{{ error }}</div>
    </div>
    <div style="margin-top:2rem;">
      <h3>Fetch All Translated Strings</h3>
      <button @click="fetchAllTranslations" :disabled="fetchTranslationsLoading || !projectId">
        {{ fetchTranslationsLoading ? 'Fetching...' : 'Fetch All Translated Strings' }}
      </button>
      <span v-if="fetchTranslationsResult" style="margin-left:1rem;">{{ fetchTranslationsResult }}</span>
    </div>
    <div style="margin-top:2rem; ;">
      <h3 style="margin: 0; font-size: 1.1em; font-weight: 600;">AI Model Download</h3>
      <label style="align-items: center; gap: 0.5em; margin: 0;">
        <input type="checkbox" v-model="modelDownloadFlag" @change="setModelDownloadFlag(modelDownloadFlag)" :disabled="modelDownloadLoading" style="margin: 0;" />
        <span>Enable local AI model (download & load on backend)</span>
      </label>
      <span v-if="modelDownloadLoading" style="margin-left:0.5em; color: #888;">Saving...</span>
      <span v-if="modelDownloadError" style="color:red; margin-left:0.5em;">{{ modelDownloadError }}</span>
    </div>
    <div style="font-size:0.95em; color:#666; margin-top:0.5em; margin-left:0.5em;">
      <b>Note:</b> After enabling, restart the backend to download and load the model. Disabling will skip model loading on next restart.
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  /* max-width: 1000px; */
  width: 100%;
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
