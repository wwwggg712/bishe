<script setup>
import { onMounted, ref } from 'vue'

import { fetchMyRecommendations } from '../../api/recommendation.js'

const isLoading = ref(true)
const errorMessage = ref('')
const recommendations = ref([])

function formatPrice(value) {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue.toFixed(2) : '0.00'
}

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
          <div class="recommend-product">
            <div class="recommend-product__media">
              <img
                v-if="item.image_url"
                class="recommend-product__image"
                :src="item.image_url"
                :alt="item.product_name"
                loading="lazy"
              />
              <div v-else class="recommend-product__placeholder">
                {{ (item.product_name || '商品').slice(0, 1) }}
              </div>
            </div>
            <div class="recommend-product__body">
              <div class="recommend-product__title-row">
                <strong>{{ item.product_name }}</strong>
                <span class="recommend-product__price">￥{{ formatPrice(item.price) }}</span>
              </div>
              <div class="recommend-product__tags">
                <span class="recommend-product__tag">{{ item.brand || '未知品牌' }}</span>
                <span class="recommend-product__tag">{{ item.category }}</span>
              </div>
              <p>{{ item.reason }}</p>
            </div>
          </div>
          <div class="customer-action-buttons">
            <router-link
              class="ghost-button"
              :to="{ name: 'customer-price-compare', query: { product_id: item.product_id } }"
            >
              比价
            </router-link>
          </div>
        </li>
      </ul>
      <p v-else class="empty-state">暂无推荐结果，可先在推荐首页查看趋势变化。</p>
    </div>
  </section>
</template>
