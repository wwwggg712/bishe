<script setup>
import { computed } from 'vue'

import EChartView from './EChartView.vue'

const props = defineProps({
  days: {
    type: Array,
    default: () => []
  },
  series: {
    type: Array,
    default: () => []
  }
})

const option = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { left: 32, right: 18, top: 36, bottom: 24 },
  xAxis: { type: 'category', data: props.days },
  yAxis: { type: 'value' },
  series: props.series.map((item) => ({
    name: item.name,
    type: 'line',
    smooth: true,
    data: item.data
  }))
}))
</script>

<template>
  <EChartView :option="option" :height="280" />
</template>

