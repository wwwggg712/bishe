<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchPriceCompare } from '../../api/priceCompare'
import { fetchMyRecommendations, fetchTrendProducts } from '../../api/recommendation.js'

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)
const errorMessage = ref('')
const comparePayload = ref(null)
const productOptions = ref([])
const selectedProductId = ref('')

const offers = computed(() => comparePayload.value?.offers || [])
const bestOffer = computed(() => comparePayload.value?.best || null)
const product = computed(() => comparePayload.value?.product || null)
const sortedOffers = computed(() =>
  [...offers.value].sort((left, right) => Number(left.price || 0) - Number(right.price || 0))
)

function normalizeProductId(value) {
  const parsed = Number.parseInt(String(value || ''), 10)
  return Number.isFinite(parsed) ? parsed : null
}

function formatPrice(value) {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue.toFixed(2) : '0.00'
}

async function loadCompare(productId) {
  if (!productId) {
    comparePayload.value = null
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchPriceCompare(productId)
    comparePayload.value = payload
  } catch (error) {
    comparePayload.value = null
    errorMessage.value = error?.response?.data?.message || '比价数据加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

function buildProductOptions(recommendations = [], trends = []) {
  const combined = [...(recommendations || []), ...(trends || [])]
  const map = new Map()
  combined.forEach((item) => {
    if (!item?.product_id) return
    if (map.has(item.product_id)) return
    map.set(item.product_id, {
      product_id: item.product_id,
      label: `${item.product_name} · ￥${formatPrice(item.price)}`
    })
  })
  return Array.from(map.values())
}

async function loadProductOptions() {
  errorMessage.value = ''
  try {
    const [recommendationPayload, trendPayload] = await Promise.all([
      fetchMyRecommendations(),
      fetchTrendProducts()
    ])
    productOptions.value = buildProductOptions(recommendationPayload.items, trendPayload.items)
  } catch (error) {
    productOptions.value = []
  }
}

function syncFromRoute() {
  const productId = normalizeProductId(route.query.product_id)
  selectedProductId.value = productId ? String(productId) : ''
  return productId
}

function handleSearch() {
  errorMessage.value = ''
  const productId = normalizeProductId(selectedProductId.value)
  if (!productId) {
    errorMessage.value = '请选择要比价的商品'
    return
  }
  router.push({
    name: 'customer-price-compare',
    query: {
      product_id: productId
    }
  })
}

watch(
  () => route.query.product_id,
  () => {
    const productId = syncFromRoute()
    loadCompare(productId)
  }
)

onMounted(() => {
  loadProductOptions()
  const productId = syncFromRoute()
  loadCompare(productId)
})
</script>

<template>
  <section class="customer-page">
    <header class="customer-page__header">
      <div>
        <p class="section-kicker">PRICE COMPARE</p>
        <h2>平台比价</h2>
        <p>从下拉框选择商品后查询比价，或从推荐卡片直接进入。</p>
      </div>
      <div class="customer-price-compare__search">
        <select v-model="selectedProductId" class="form-input" data-testid="price-compare-select">
          <option value="">选择商品</option>
          <option v-for="option in productOptions" :key="option.product_id" :value="String(option.product_id)">
            {{ option.label }}
          </option>
        </select>
        <button class="ghost-button" type="button" data-testid="price-compare-search" @click="handleSearch">
          查询
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div class="dashboard-panel" :aria-busy="isLoading">
      <div v-if="product" class="price-compare-product">
        <div class="recommend-product__media">
          <img
            v-if="product.image_url"
            class="recommend-product__image"
            :src="product.image_url"
            :alt="product.name"
            loading="lazy"
          />
          <div v-else class="recommend-product__placeholder">{{ (product.name || '商品').slice(0, 1) }}</div>
        </div>
        <div class="price-compare-product__body">
          <div class="recommend-product__title-row">
            <strong>{{ product.name }}</strong>
            <span class="recommend-product__price">￥{{ formatPrice(product.price) }}</span>
          </div>
          <div class="recommend-product__tags">
            <span class="recommend-product__tag">{{ product.brand || '未知品牌' }}</span>
            <span class="recommend-product__tag">{{ product.category }}</span>
          </div>
        </div>
      </div>

      <ul v-if="sortedOffers.length" class="compare-offer-list">
        <li v-for="offer in sortedOffers" :key="offer.platform" class="compare-offer-list__item">
          <div class="compare-offer-list__meta">
            <strong>{{ offer.platform }}</strong>
            <p v-if="offer.delivery_hint || offer.coupon_hint">
              {{ offer.delivery_hint }}{{ offer.delivery_hint && offer.coupon_hint ? ' · ' : '' }}{{ offer.coupon_hint }}
            </p>
          </div>
          <div class="compare-offer-list__price">
            <span
              class="admin-status-pill"
              data-status="success"
              v-if="bestOffer && bestOffer.platform === offer.platform"
            >
              最低价
            </span>
            <span class="compare-offer-list__amount">￥{{ formatPrice(offer.price) }}</span>
          </div>
        </li>
      </ul>

      <p v-else-if="!isLoading" class="empty-state">请选择商品后点击查询，查看比价结果。</p>

      <div v-if="comparePayload?.advice" class="price-compare-advice">
        <p class="admin-log-preview__note">{{ comparePayload.advice }}</p>
      </div>
    </div>
  </section>
</template>
