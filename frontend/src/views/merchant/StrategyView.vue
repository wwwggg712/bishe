<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

function formatRate(value) {
  return `${((value || 0) * 100).toFixed(1)}%`
}
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">STRATEGY</p>
        <h3>策略建议</h3>
      </div>
      <span class="dashboard-panel__badge">商品经营动作</span>
    </div>

    <ul v-if="items.length" class="strategy-list">
      <li v-for="item in items" :key="item.product_id" class="strategy-list__item">
        <div class="strategy-list__meta">
          <strong>{{ item.product_name }}</strong>
          <span>浏览 {{ item.views }} / 转化 {{ formatRate(item.purchase_rate) }}</span>
        </div>
        <p>{{ item.action }}</p>
      </li>
    </ul>
    <p v-else class="empty-state">当前没有需要提醒的经营策略，继续保持曝光与转化表现。</p>
  </article>
</template>
