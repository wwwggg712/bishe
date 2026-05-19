<script setup>
import { computed } from 'vue'

import TrendBarChart from '../../components/charts/TrendBarChart.vue'

const props = defineProps({
  payload: {
    type: Object,
    required: true
  },
  showSummaryCards: {
    type: Boolean,
    default: true
  },
  onDeactivate: {
    type: Function,
    required: true
  },
  isDeactivatingId: {
    type: Number,
    default: 0
  }
})

const COLOR_ORDER = ['红', '蓝', '黑', '白', '灰', '绿']

function buildColorTiles(colorBreakdown) {
  const items = Array.isArray(colorBreakdown) ? colorBreakdown : []
  const map = new Map(items.map((item) => [item?.color, Number(item?.count || 0)]))
  return COLOR_ORDER.map((color) => ({ color, count: map.get(color) || 0 }))
}

function formatMoney(value) {
  const numberValue = Number(value || 0)
  return numberValue.toFixed(2)
}

const cards = computed(() => [
  {
    label: `近${props.payload?.summary?.days || 30}天收入`,
    value: formatMoney(props.payload?.summary?.revenue),
    hint: '估算：购买次数×商品售价'
  },
  {
    label: `近${props.payload?.summary?.days || 30}天成本`,
    value: formatMoney(props.payload?.summary?.cost),
    hint: '估算：购买次数×商品成本价'
  },
  {
    label: `近${props.payload?.summary?.days || 30}天利润`,
    value: formatMoney(props.payload?.summary?.profit),
    hint: '利润=收入-成本'
  }
])
</script>

<template>
  <section class="merchant-dashboard__layer">
    <div class="merchant-dashboard__layer-head">
      <div>
        <h3>经营总览</h3>
        <details class="metric-details">
          <summary>口径说明（点击展开）</summary>
          <p>用于答辩展示“利润、库存、下架、重点品牌”的经营视角（基于 purchase 行为次数估算）。</p>
        </details>
      </div>
    </div>

    <section v-if="showSummaryCards" class="merchant-dashboard__summary merchant-dashboard__summary--triple">
      <article v-for="card in cards" :key="card.label" class="metric-card">
        <p class="metric-card__label">{{ card.label }}</p>
        <strong class="metric-card__value">{{ card.value }}</strong>
        <span class="metric-card__hint">{{ card.hint }}</span>
      </article>
    </section>

    <div class="merchant-dashboard__layer-grid">
      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">FOCUS BRANDS</p>
            <h3>销量冠军品牌TOP</h3>
            <p>按近30天购买次数统计，每个品牌补充一个贡献最高的代表商品。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.focus_brands?.length || 0 }} 个品牌</span>
        </div>

        <TrendBarChart
          v-if="payload.focus_brands?.length"
          :items="payload.focus_brands"
          label-key="brand"
          value-key="purchase_count_30d"
          sub-label-key="top_product_name"
        />
        <p v-else class="empty-state">暂无品牌成交数据。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">INVENTORY</p>
            <h3>库存清单</h3>
            <p>展示当前有库存的商品（stock&gt;0）。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.inventory_items?.length || 0 }} 个SKU</span>
        </div>

        <ul v-if="payload.inventory_items?.length" class="strategy-list">
          <li v-for="item in payload.inventory_items" :key="item.product_id" class="strategy-list__item">
            <div class="merchant-product-row">
              <div class="merchant-product-thumb">
                <img
                  v-if="item.image_url"
                  class="merchant-product-thumb__image"
                  :src="item.image_url"
                  :alt="item.name"
                  loading="lazy"
                />
                <div v-else class="merchant-product-thumb__placeholder">
                  {{ String(item.name || '').trim().slice(0, 1) }}
                </div>
              </div>
              <div class="merchant-product-row__body">
                <div class="strategy-list__meta">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.category }} / {{ item.brand }}</span>
                </div>
                <p>
                  库存 {{ item.stock }} · 售价 {{ Number(item.price || 0).toFixed(2) }} · 成本
                  {{ Number(item.cost_price || 0).toFixed(2) }}
                </p>
              </div>
              <div v-if="item.color_breakdown?.length" class="merchant-color-breakdown">
                <div
                  v-for="part in buildColorTiles(item.color_breakdown)"
                  :key="`${item.product_id}-${part.color}`"
                  class="merchant-color-tile"
                  :data-color="part.color"
                  :data-empty="part.count <= 0 ? 'true' : 'false'"
                  :data-testid="`merchant-color-${item.product_id}-${part.color}`"
                >
                  <span class="merchant-color-tile__label">{{ part.color }}</span>
                  <strong class="merchant-color-tile__value">{{ part.count > 0 ? part.count : '—' }}</strong>
                </div>
              </div>
            </div>
          </li>
        </ul>
        <p v-else class="empty-state">暂无库存商品。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">DELIST SUGGESTIONS</p>
            <h3>建议下架（近30天购买&lt;3）</h3>
            <p>只给建议，点击按钮才会真正下架。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.delist_suggestions?.length || 0 }} 个</span>
        </div>

        <ul v-if="payload.delist_suggestions?.length" class="strategy-list">
          <li v-for="item in payload.delist_suggestions" :key="item.product_id" class="strategy-list__item">
            <div class="merchant-product-row">
              <div class="merchant-product-thumb">
                <img
                  v-if="item.image_url"
                  class="merchant-product-thumb__image"
                  :src="item.image_url"
                  :alt="item.name"
                  loading="lazy"
                />
                <div v-else class="merchant-product-thumb__placeholder">
                  {{ String(item.name || '').trim().slice(0, 1) }}
                </div>
              </div>
              <div class="merchant-product-row__body">
                <div class="strategy-list__meta">
                  <strong>{{ item.name }}</strong>
                  <span>近30天购买 {{ item.purchase_count_30d }} 次</span>
                </div>
                <p>{{ item.category }} / {{ item.brand }} · 库存 {{ item.stock }}</p>
                <div class="merchant-action-buttons">
                  <button
                    class="ghost-button"
                    type="button"
                    :data-testid="`merchant-delist-${item.product_id}`"
                    :disabled="isDeactivatingId === item.product_id"
                    @click="onDeactivate(item.product_id)"
                  >
                    {{ isDeactivatingId === item.product_id ? '下架中...' : '下架' }}
                  </button>
                </div>
              </div>
              <div v-if="item.color_breakdown?.length" class="merchant-color-breakdown">
                <div
                  v-for="part in buildColorTiles(item.color_breakdown)"
                  :key="`${item.product_id}-${part.color}`"
                  class="merchant-color-tile"
                  :data-color="part.color"
                  :data-empty="part.count <= 0 ? 'true' : 'false'"
                  :data-testid="`merchant-color-${item.product_id}-${part.color}`"
                >
                  <span class="merchant-color-tile__label">{{ part.color }}</span>
                  <strong class="merchant-color-tile__value">{{ part.count > 0 ? part.count : '—' }}</strong>
                </div>
              </div>
            </div>
          </li>
        </ul>
        <p v-else class="empty-state">暂无需要下架的低销量商品。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">INACTIVE</p>
            <h3>已下架商品</h3>
            <p>展示已下架商品清单。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.inactive_items?.length || 0 }} 个</span>
        </div>

        <ul v-if="payload.inactive_items?.length" class="strategy-list">
          <li v-for="item in payload.inactive_items" :key="item.product_id" class="strategy-list__item">
            <div class="merchant-product-row">
              <div class="merchant-product-thumb">
                <img
                  v-if="item.image_url"
                  class="merchant-product-thumb__image"
                  :src="item.image_url"
                  :alt="item.name"
                  loading="lazy"
                />
                <div v-else class="merchant-product-thumb__placeholder">
                  {{ String(item.name || '').trim().slice(0, 1) }}
                </div>
              </div>
              <div class="merchant-product-row__body">
                <div class="strategy-list__meta">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.category }} / {{ item.brand }}</span>
                </div>
                <p>库存 {{ item.stock }}</p>
              </div>
              <div v-if="item.color_breakdown?.length" class="merchant-color-breakdown">
                <div
                  v-for="part in buildColorTiles(item.color_breakdown)"
                  :key="`${item.product_id}-${part.color}`"
                  class="merchant-color-tile"
                  :data-color="part.color"
                  :data-empty="part.count <= 0 ? 'true' : 'false'"
                  :data-testid="`merchant-color-${item.product_id}-${part.color}`"
                >
                  <span class="merchant-color-tile__label">{{ part.color }}</span>
                  <strong class="merchant-color-tile__value">{{ part.count > 0 ? part.count : '—' }}</strong>
                </div>
              </div>
            </div>
          </li>
        </ul>
        <p v-else class="empty-state">暂无已下架商品。</p>
      </article>
    </div>
  </section>
</template>
