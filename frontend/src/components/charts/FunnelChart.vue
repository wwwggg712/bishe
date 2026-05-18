<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  }
})

const maxValue = computed(() => Math.max(...props.steps.map((item) => item.value || 0), 1))

function formatWidth(value) {
  return `${Math.max((value / maxValue.value) * 100, 10)}%`
}
</script>

<template>
  <div class="funnel-chart">
    <article
      v-for="step in steps"
      :key="step.key"
      class="funnel-chart__row"
    >
      <div class="funnel-chart__meta">
        <strong>{{ step.label }}</strong>
        <span>{{ step.value }}</span>
      </div>
      <div class="funnel-chart__track">
        <div class="funnel-chart__fill" :style="{ width: formatWidth(step.value) }"></div>
      </div>
    </article>
  </div>
</template>
