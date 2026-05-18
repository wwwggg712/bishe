<script setup>
import TrendBarChart from '../../components/charts/TrendBarChart.vue'

defineEmits(['update:selectedCategory'])

defineProps({
  brands: {
    type: Array,
    default: () => []
  },
  categories: {
    type: Array,
    default: () => []
  },
  selectedCategory: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">BRAND HEAT</p>
        <h3>品类-品牌热度</h3>
        <p>先选品类，再查看该品类下品牌热度排行。</p>
      </div>
      <span class="dashboard-panel__badge">{{ brands.length }} 个品牌</span>
    </div>

    <div v-if="categories.length" class="admin-page__actions" style="justify-content: flex-start; padding: 0 0 12px;">
      <span class="dashboard-panel__badge">品类</span>
      <select class="admin-log-preview__page-size" :value="selectedCategory" @change="$emit('update:selectedCategory', $event.target.value)">
        <option v-for="item in categories" :key="item.category" :value="item.category">
          {{ item.category }}
        </option>
      </select>
    </div>

    <TrendBarChart v-if="brands.length" :items="brands" label-key="brand" />
    <p v-else class="empty-state">暂无品牌数据</p>
  </article>
</template>
