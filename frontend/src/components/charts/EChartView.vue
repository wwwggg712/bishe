<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  height: {
    type: [String, Number],
    default: 260
  }
})

const rootRef = ref(null)
const isEnabled = ref(true)
let chart = null

function resize() {
  chart?.resize()
}

onMounted(() => {
  const element = rootRef.value
  const canUseCanvas =
    typeof HTMLCanvasElement !== 'undefined' &&
    typeof HTMLCanvasElement.prototype?.getContext === 'function'
  const hasSize = Boolean(element && element.clientWidth > 0 && element.clientHeight > 0)

  if (!element || !canUseCanvas || !hasSize) {
    isEnabled.value = false
    return
  }

  chart = echarts.init(element)
  chart.setOption(props.option || {}, true)
  window.addEventListener('resize', resize)
})

watch(
  () => props.option,
  (nextOption) => {
    chart?.setOption(nextOption || {}, true)
  },
  { deep: true }
)

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div
    ref="rootRef"
    :data-echarts-enabled="isEnabled ? 'true' : 'false'"
    :style="{ width: '100%', height: typeof height === 'number' ? `${height}px` : height }"
  ></div>
</template>
