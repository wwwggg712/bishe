<script setup>
import TrendBarChart from '../../components/charts/TrendBarChart.vue'

defineProps({
  products: {
    type: Array,
    default: () => []
  },
  regions: {
    type: Array,
    default: () => []
  }
})
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">TOP PRODUCTS</p>
        <h3>热销商品</h3>
      </div>
      <span class="dashboard-panel__badge">按行为热度排序</span>
    </div>

    <TrendBarChart :items="products" />

    <div class="region-list">
      <div class="region-list__header">
        <strong>重点区域</strong>
        <span>按活跃行为量聚合</span>
      </div>
      <ul v-if="regions.length" class="region-list__items">
        <li v-for="region in regions" :key="region.region" class="region-list__item">
          <span>{{ region.region }}</span>
          <strong>{{ region.count }}</strong>
        </li>
      </ul>
      <p v-else class="empty-state">暂无区域数据</p>
    </div>
  </article>
</template>
