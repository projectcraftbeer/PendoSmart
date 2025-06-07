<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'


interface TranslationRow {
  id: number;
  file_uri: string;
  parsed_string_text: string;
  translation: string;
  status: string;
  confidence: number | null;
  reason: string | null;
  flag: number | null;
  hashcode?: string;
}

const props = defineProps<{ projectId?: string, refreshKey?: number, locale?: string }>()
const strings = ref<TranslationRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const page = ref(1)
const perPage = ref(20)
const total = ref(0)
const flagFilter = ref('all') // 'all', 'flagged', 'unflagged'
const statusFilter = ref('all') // 'all', 'completed', 'pending'
const filteredStrings = computed(() => strings.value)
const searchType = ref('source') // 'source' or 'translation'
const searchText = ref('')
const pageCount = computed(() => Math.ceil(total.value / perPage.value))
const editingPage = ref(false)
const editPageValue = ref(page.value)

function startEditPage() {
  editPageValue.value = page.value
  editingPage.value = true
}

function commitEditPage() {
  let val = Math.max(1, Math.min(pageCount.value, editPageValue.value || 1))
  page.value = val
  editingPage.value = false
}

function resetPageOnFlagFilter() {
  page.value = 1;
}

async function fetchStrings() {
  loading.value = true
  error.value = null
  try {
    const pid = props.projectId || ''
    const loc = props.locale || 'ja-JP'
    if (!pid) {
      strings.value = []
      total.value = 0
      return
    }
    let url = `http://localhost:8000/admin/smartling-translations-table?project_id=${encodeURIComponent(pid)}&locale=${encodeURIComponent(loc)}&page=${page.value}&per_page=${perPage.value}`
    if (flagFilter.value === 'flagged') url += '&flag=1'
    if (flagFilter.value === 'unflagged') url += '&flag=0'
    if (statusFilter.value === 'completed') url += '&status=completed'
    if (statusFilter.value === 'pending') url += '&status=pending'
    if (searchText.value) {
      url += `&search_type=${encodeURIComponent(searchType.value)}&search_text=${encodeURIComponent(searchText.value)}`
    }
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed to fetch translations')
    const data = await res.json()
    strings.value = data.translations || []
    total.value = data.total || 0
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
// because TS hates none used stuff. ugh.
// async function evaluateString(row: StringPair) {
//   try {
//     const res = await fetch('http://localhost:8000/evaluate', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify({ id: row.id, source: row.source, japanese: row.japanese })
//     })
//     if (!res.ok) throw new Error('Evaluation failed')
//     const updated = await res.json()
//     const idx = strings.value.findIndex(s => s.id === row.id)
//     if (idx !== -1) strings.value[idx] = updated
//   } catch (e: any) {
//     alert(e.message)
//   }
// }

// TODO: sometimes reason get's updated when refreshing all string. I don't know why. 
const updateReason = async (row: TranslationRow) => {
  try {
    const res = await fetch('http://localhost:8000/admin/smartling-update-reason', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [row.id], reason: row.reason })
    })
    if (!res.ok) throw new Error('Failed to update reason')
  } catch (e: any) {
    alert(e.message)
  }
}

async function toggleFlag(row: TranslationRow) {
  const newFlag = row.flag === 1 ? 0 : 1
  try {
    const res = await fetch(`http://localhost:8000/admin/smartling-toggle-flag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: row.id, flag: newFlag })
    })
    if (!res.ok) throw new Error('Failed to update flag')
    row.flag = newFlag
  } catch (e: any) {
    alert(e.message)
  }
}

async function toggleStatus(row: TranslationRow) {
  const newStatus = row.status === 'completed' ? 'pending' : 'completed'
  try {
    const res = await fetch(`http://localhost:8000/admin/smartling-toggle-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: row.id, status: newStatus })
    })
    if (!res.ok) throw new Error('Failed to update status')
    row.status = newStatus
  } catch (e: any) {
    alert(e.message)
  }
}

async function setAllCompleted() {
  const ids = filteredStrings.value.map(row => row.id)
  try {
    const res = await fetch(`http://localhost:8000/admin/smartling-bulk-complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids })
    })
    if (!res.ok) throw new Error('Failed to update all statuses')
    for (const row of filteredStrings.value) row.status = 'completed'
  } catch (e: any) {
    alert(e.message)
  }
}
// hooks and other setup
watch([() => props.projectId, page, perPage, flagFilter, statusFilter, () => props.refreshKey], fetchStrings, { immediate: true })
defineExpose({ editingPage, editPageValue, startEditPage, commitEditPage, toggleStatus, setAllCompleted })
onMounted(fetchStrings)

</script>

<template>
  <div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    <div v-else>
      <div style="margin-bottom:1rem; display: flex; gap: 2rem; align-items: flex-end;">
        <div>
          <label>Flag Filter:</label>
          <select v-model="flagFilter" @change="resetPageOnFlagFilter">
            <option value="all">All</option>
            <option value="flagged">Flagged</option>
            <option value="unflagged">Unflagged</option>
          </select>
          <label style="margin-left:1rem;">Status Filter:</label>
          <select v-model="statusFilter" @change="resetPageOnFlagFilter">
            <option value="all">All</option>
            <option value="completed">Completed</option>
            <option value="pending">Pending</option>
          </select>
          <button @click="setAllCompleted" style="margin-bottom:0.5rem; margin-left:1rem;">Mark all as Completed (this page)</button>
        </div>
        <form @submit.prevent="fetchStrings">
          <label>Search:</label>
          <input v-model="searchText" placeholder="Enter text..." style="margin-right:0.5rem;" />
          <select v-model="searchType">
            <option value="source">Source String</option>
            <option value="translation">Translation</option>
          </select>
          <button type="submit">Search</button>
        </form>
      </div>
      <table>
        <thead>
          <tr>
            <!-- <th>ID</th> -->
            <th>File URI</th>
            <th>Source String</th>
            <th>Translation</th>
            <th>Status</th>
            <th>Confidence</th>
            <th>Reason</th>
            <th>Flag</th>
            <th>Hashcode</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filteredStrings" :key="row.id">
            <!-- <td>{{ row.id }}</td> -->
            <td>{{ row.file_uri }}</td>
            <td>{{ row.parsed_string_text }}</td>
            <td>{{ row.translation }}</td>
            <td>
              <button @click="toggleStatus(row)">{{ row.status === 'completed' ? '✅' : '⬜' }}</button>
            </td>
            <td>{{ row.confidence }}</td>
            <td>
              <textarea
                
                v-model="row.reason"
                @blur="updateReason(row)"
                :placeholder="'Edit reason'"
                style="width: 12em;"
              />
            </td>
            <td>
              <button @click="toggleFlag(row)">{{ row.flag === 1 ? '✅' : '⬜' }}</button>
            </td>
            <td style="font-family:monospace;max-width:12rem;overflow-x:auto;">
              <a v-if="row.hashcode" :href="`https://dashboard.smartling.com/app/projects/${props.projectId}/strings/?hashcodes=${row.hashcode}&localeIds=ja-JP`" target="_blank" rel="noopener noreferrer">{{ row.hashcode }}</a>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div style="margin-top:1rem;">
        <button @click="page > 1 && (page = page - 1)" :disabled="page === 1">Prev</button>
        <span>
          Page 
          <span v-if="!editingPage" @click="startEditPage" style="cursor:pointer; text-decoration:underline;">{{ page }}</span>
          <input v-else type="number" v-model.number="editPageValue" min="1" :max="pageCount" style="width:3em;" @keyup.enter="commitEditPage" @blur="commitEditPage" />
          of {{ pageCount }}
        </span>
        <button @click="page < pageCount && (page = page + 1)" :disabled="page === pageCount">Next</button>
        <select v-model="perPage">
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
        <span>Total: {{ total }}</span>
      </div>
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
