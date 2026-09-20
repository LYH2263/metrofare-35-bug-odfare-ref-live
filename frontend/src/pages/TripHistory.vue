<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const stations = ref([])
const opened = ref(null)
const nameOf = (code) => stations.value.find((s) => s.code === code)?.name ?? code
const parse = (h) => {
  let input = {}, result = {}
  try { input = JSON.parse(h.input_json) } catch { /* skip */ }
  try { result = JSON.parse(h.result_json) } catch { /* skip */ }
  return { ...h, input, result }
}
const openRow = async (h) => {
  const row = parse(await getJSON('/api/history/' + h.id))
  // persisted snapshot: values shown are exactly what was written at the time
  row.result.segments ??= []
  opened.value = row
}
onMounted(async () => {
  const [hits, st] = await Promise.all([getJSON('/api/history'), getJSON('/api/stations')])
  items.value = hits.items.map(parse)
  stations.value = st.items
})
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr v-for="h in items" :key="h.id" style="cursor:pointer" @click="openRow(h)">
        <td>#{{ h.id }}</td>
        <td>
          应付 ¥{{ h.result.fare }}
          <span v-if="h.result.fare_source === 'flat'" class="flat-badge">一口价</span>
        </td>
      </tr>
    </table>
    <div v-if="opened" class="panel">
      <template v-if="opened.result.reachable">
        <p>
          应付 <span class="hero-num">¥{{ opened.result.fare }}</span>
          <span v-if="opened.result.fare_source === 'flat'" class="flat-badge">一口价</span>
          · 分段参考合计 ¥{{ opened.result.segment_total ?? opened.result.reference_fare }}
        </p>
        <p class="muted" v-if="opened.result.path">
          {{ opened.result.hops }} 站 · 最短途经：{{ opened.result.path.map(nameOf).join(' → ') }}
        </p>
        <table v-if="opened.result.segments.length">
          <thead><tr><th>#</th><th>区间</th><th>累计站数</th><th>分段参考价</th></tr></thead>
          <tbody>
            <tr v-for="seg in opened.result.segments" :key="seg.seq">
              <td>{{ seg.seq }}</td>
              <td>{{ nameOf(seg.from) }} → {{ nameOf(seg.to) }}</td>
              <td>{{ seg.cum_hops }}</td>
              <td>¥{{ Number(seg.price).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
