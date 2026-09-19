<script setup>
import { computed, onMounted, ref } from 'vue'
import { deleteJSON, getJSON, postJSON } from '../api'

const stations = ref([])
const items = ref([])
const start = ref('A1')
const end = ref('B2')
const price = ref(2.5)
const error = ref('')

const nameOf = (code) => stations.value.find((s) => s.code === code)?.name ?? code

const load = async () => { items.value = (await getJSON('/api/flat-fares')).items }
onMounted(async () => {
  stations.value = (await getJSON('/api/stations')).items
  await load()
})

const submit = async () => {
  error.value = ''
  try {
    await postJSON('/api/flat-fares', { start: start.value, end: end.value, price: Number(price.value) })
    await load()
  } catch (e) {
    error.value = e.message
  }
}

const remove = async (f) => {
  await deleteJSON(`/api/flat-fares/${f.start}/${f.end}`)
  await load()
}

const endOptions = computed(() => stations.value.filter((s) => s.code !== start.value))
</script>
<template>
  <div class="page">
    <h1>点对点一口价</h1>
    <p class="muted">仅作用于指定的有向起终点对；未命中时仍按站数走分段票价表。</p>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in endOptions" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <input v-model="price" type="number" min="0" step="0.5" style="width:6rem" />
      <button @click="submit">登记一口价</button>
      <p v-if="error" class="muted">{{ error }}</p>
    </div>
    <table>
      <thead><tr><th>起点</th><th>终点</th><th>一口价</th><th>登记时间</th><th></th></tr></thead>
      <tbody>
        <tr v-for="f in items" :key="f.id">
          <td>{{ nameOf(f.start) }}（{{ f.start }}）</td>
          <td>{{ nameOf(f.end) }}（{{ f.end }}）</td>
          <td>¥{{ f.price }}</td>
          <td>{{ f.created_at }}</td>
          <td><button @click="remove(f)">删除</button></td>
        </tr>
        <tr v-if="!items.length"><td colspan="5" class="muted">尚未登记一口价</td></tr>
      </tbody>
    </table>
  </div>
</template>
