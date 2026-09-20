<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const dryRun = ref(true)
const out = ref(null)
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
const nameOf = (code) => stations.value.find((s) => s.code === code)?.name ?? code
const run = async () => {
  out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: !dryRun.value })
}
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <label class="muted"><input type="checkbox" v-model="dryRun" /> 只读试算（不落库）</label>
      <button @click="run">试算</button>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>
          <span v-if="out.fare_source === 'flat'">
            一口价 <span class="hero-num">¥{{ out.fare }}</span>
            <span class="flat-badge">一口价</span>
          </span>
          <span v-else>
            分段票价 <span class="hero-num">¥{{ out.fare }}</span>
          </span>
        </p>
        <p class="muted">{{ out.hops }} 站 · 最短途经：{{ out.path.map(nameOf).join(' → ') }}</p>
        <table>
          <thead><tr><th>#</th><th>区间</th><th>累计站数</th><th>分段参考价</th></tr></thead>
          <tbody>
            <tr v-for="seg in out.segments" :key="seg.seq">
              <td>{{ seg.seq }}</td>
              <td>{{ nameOf(seg.from) }} → {{ nameOf(seg.to) }}</td>
              <td>{{ seg.cum_hops }}</td>
              <td>¥{{ seg.price.toFixed(2) }}</td>
            </tr>
            <tr>
              <td colspan="3">行加总（按 {{ out.hops }} 站取分段价）</td>
              <td>¥{{ out.segment_total.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="out.fare_source === 'flat'" class="muted">
          命中一口价：应付按一口价 ¥{{ out.fare }}，分段参考合计 ¥{{ out.segment_total }} 仅作对照。
        </p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
