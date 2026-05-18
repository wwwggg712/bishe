<script setup>
import { onMounted, ref } from 'vue'

import { fetchMyRecommendations } from '../../api/recommendation.js'

const isLoading = ref(true)
const errorMessage = ref('')
const recommendations = ref([])

async function loadRecommendations() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchMyRecommendations()
    recommendations.value = payload.items || []
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '推荐列表加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadRecommendations()
})
</script>

<template>
  <section class="customer-page">
    <header class="customer-page__header">
      <div>
        <p class="section-kicker">RECOMMENDATION CENTER</p>
        <h2>推荐中心</h2>
        <p>聚合展示推荐商品与推荐理由，便于用户快速筛选目标商品。</p>
      </div>
      <button class="ghost-button" type="button" @click="loadRecommendations">刷新列表</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div class="dashboard-panel" :aria-busy="isLoading">
      <ul v-if="recommendations.length" class="recommend-list">
        <li
          v-for="item in recommendations"
          :key="item.product_id"
          class="recommend-list__item"
        >
          <strong>{{ item.product_name }}</strong>
          <span>{{ item.category }}</span>
          <p>{{ item.reason }}</p>
        </li>
      </ul>
      <p v-else class="empty-state">暂无推荐结果，可先在推荐首页查看趋势变化。</p>
    </div>
  </section>
</template>
