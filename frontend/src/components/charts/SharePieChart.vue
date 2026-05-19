<script setup>
import { computed } from 'vue'

import EChartView from './EChartView.vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const option = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { top: 0, left: 'center' },
  series: [
    {
      type: 'pie',
      radius: ['35%', '70%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: { label: { show: true, fontWeight: 'bold' } },
      data: props.items
    }
  ]
}))
</script>

<template>
  <EChartView :option="option" :height="280" />
</template>

