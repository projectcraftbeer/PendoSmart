<script setup lang="ts">
import { ref } from 'vue'
import { RouterView, RouterLink } from 'vue-router'

const nightMode = ref(false)
function toggleNightMode() {
  nightMode.value = !nightMode.value
  document.body.classList.toggle('night', nightMode.value)
}
</script>

<template>
  <div :class="{ night: nightMode }">
    <button @click="toggleNightMode" style="float:right;">{{ nightMode ? 'Day Mode' : 'Night Mode' }}</button>

      <RouterLink to="/" style="margin-right: 0.5rem;">Main</RouterLink>
      <RouterLink to="/admin">Admin</RouterLink>

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
