<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const opened = ref(null)
const parse = (h) => {
  let input = {}, result = {}
  try { input = JSON.parse(h.input_json) } catch { /* skip */ }
  try { result = JSON.parse(h.result_json) } catch { /* skip */ }
  return { ...h, input, result }
}
const openRow = async (h) => {
  opened.value = parse(await getJSON('/api/history/' + h.id))
}
onMounted(async () => { items.value = (await getJSON('/api/history')).items.map(parse) })
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr v-for="h in items" :key="h.id" style="cursor:pointer" @click="openRow(h)">
        <td>#{{ h.id }}</td>
        <td>应付 ¥{{ h.result.fare }}</td>
      </tr>
    </table>
    <div v-if="opened" class="panel">
      <p>应付 ¥{{ opened.result.fare }} · 分段参考合计 ¥{{ opened.result.reference_fare }}</p>
    </div>
  </div>
</template>
