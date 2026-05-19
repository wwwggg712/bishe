<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  valueKey: {
    type: String,
    default: 'count'
  },
  labelKey: {
    type: String,
    default: 'product_name'
  },
  subLabelKey: {
    type: String,
    default: ''
  }
})

const maxValue = computed(() => Math.max(...props.items.map((item) => item?.[props.valueKey] || 0), 1))

function formatWidth(value) {
  return `${Math.max((value / maxValue.value) * 100, 8)}%`
}
</script>

<template>
  <div class="mini-bar-chart">
    <article
      v-for="item in items"
      :key="`${item[labelKey]}-${item[valueKey]}`"
      class="mini-bar-chart__row"
    >
      <div class="mini-bar-chart__meta">
        <div class="mini-bar-chart__label">
          <strong>{{ item[labelKey] }}</strong>
          <small v-if="subLabelKey && item?.[subLabelKey]">{{ item[subLabelKey] }}</small>
        </div>
        <span>{{ item[valueKey] }}</span>
      </div>
      <div class="mini-bar-chart__track">
        <div class="mini-bar-chart__fill" :style="{ width: formatWidth(item[valueKey]) }"></div>
      </div>
    </article>
  </div>
</template>
