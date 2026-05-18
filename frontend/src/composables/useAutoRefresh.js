import { onMounted, onUnmounted, ref, watch } from 'vue'

function formatTime(value) {
  return value.toLocaleTimeString('zh-CN', { hour12: false })
}

export function useAutoRefresh(refreshFn, options = {}) {
  const enabled = ref(options.defaultEnabled ?? true)
  const intervalSec = ref(options.defaultIntervalSec ?? 60)
  const countdown = ref(intervalSec.value)
  const lastUpdatedAt = ref('')
  const isRefreshing = ref(false)

  let tickerId = null

  async function refreshNow(resetCountdown = true) {
    if (isRefreshing.value) return
    isRefreshing.value = true
    try {
      await refreshFn?.()
      lastUpdatedAt.value = formatTime(new Date())
    } finally {
      isRefreshing.value = false
      if (resetCountdown) {
        countdown.value = intervalSec.value
      }
    }
  }

  function tick() {
    if (!enabled.value) return
    if (typeof document !== 'undefined' && document.hidden) return
    if (countdown.value <= 0) return
    countdown.value -= 1
    if (countdown.value <= 0) {
      refreshNow(true)
    }
  }

  function handleVisibilityChange() {
    if (!enabled.value) return
    if (typeof document !== 'undefined' && document.hidden) return
    refreshNow(true)
  }

  function start() {
    if (tickerId) return
    tickerId = window.setInterval(tick, 1000)
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', handleVisibilityChange)
    }
  }

  function stop() {
    if (tickerId) {
      window.clearInterval(tickerId)
      tickerId = null
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }

  watch(intervalSec, (nextValue) => {
    countdown.value = nextValue
  })

  watch(enabled, (nextValue) => {
    countdown.value = intervalSec.value
    if (nextValue) {
      refreshNow(true)
      return
    }
    lastUpdatedAt.value = lastUpdatedAt.value || ''
  })

  onMounted(() => {
    start()
  })

  onUnmounted(() => {
    stop()
  })

  return {
    enabled,
    intervalSec,
    countdown,
    lastUpdatedAt,
    isRefreshing,
    refreshNow,
    start,
    stop
  }
}

