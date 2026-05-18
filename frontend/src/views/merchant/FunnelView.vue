<script setup>
import { computed } from 'vue'

import FunnelChart from '../../components/charts/FunnelChart.vue'

const props = defineProps({
  funnel: {
    type: Object,
    default: () => ({})
  }
})

const steps = computed(() => [
  { key: 'view', label: '浏览', value: props.funnel.view || 0 },
  { key: 'click', label: '点击', value: props.funnel.click || 0 },
  { key: 'favorite', label: '收藏', value: props.funnel.favorite || 0 },
  { key: 'cart', label: '加购', value: props.funnel.cart || 0 },
  { key: 'purchase', label: '购买', value: props.funnel.purchase || 0 }
])

const conversionRate = computed(() => {
  const viewCount = props.funnel.view || 0
  const purchaseCount = props.funnel.purchase || 0

  if (!viewCount) {
    return '0.0%'
  }

  return `${((purchaseCount / viewCount) * 100).toFixed(1)}%`
})
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">FUNNEL</p>
        <h3>转化漏斗</h3>
        <p>基于五类行为事件统计经营转化指标，不代表单用户真实路径漏斗。</p>
      </div>
      <span class="dashboard-panel__badge">事件级经营转化指标</span>
    </div>

    <FunnelChart :steps="steps" />

    <div class="funnel-insight">
      <strong>整体成交转化率</strong>
      <p>{{ conversionRate }}</p>
      <span>购买行为 / 浏览行为</span>
    </div>
  </article>
</template>
