<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const navigationItems = computed(() => {
  const role = authStore.role

  if (role === 'merchant') {
    return [
      { label: '经营总览', to: { path: '/merchant/dashboard', query: { section: 'overview' } } },
      { label: '核心业务', to: { path: '/merchant/dashboard', query: { section: 'core' } } },
      { label: '辅助分析', to: { path: '/merchant/dashboard', query: { section: 'analysis' } } },
      { label: '详细分析', to: { path: '/merchant/dashboard', query: { section: 'detail' } } }
    ]
  }

  if (role === 'customer') {
    return [
      { label: '推荐首页', to: '/customer/home' },
      { label: '推荐中心', to: '/customer/recommendations' },
      { label: '个人画像', to: '/customer/profile' }
    ]
  }

  if (role === 'admin') {
    return [
      { label: '系统总览', to: '/admin/overview' },
      { label: '任务管理', to: '/admin/tasks' },
      { label: '日志预览', to: '/admin/logs' },
      { label: '用户管理', to: '/admin/users' }
    ]
  }

  return [{ label: '工作台', to: '/' }]
})

const navClassName = computed(() => ({
  'app-shell__nav--merchant': authStore.role === 'merchant'
}))

const sidebarClassName = computed(() => ({
  'app-shell__sidebar--merchant': authStore.role === 'merchant'
}))

function logout() {
  authStore.clearSession()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="app-shell__sidebar" :class="sidebarClassName">
      <div>
        <p class="app-shell__eyebrow">E-commerce</p>
        <h1 class="app-shell__title">智能分析系统</h1>
        <p class="app-shell__subtitle">多角色联动的电商经营分析与决策工作台</p>
      </div>

      <nav class="app-shell__nav" :class="navClassName">
        <router-link
          v-for="item in navigationItems"
          :key="item.label"
          :to="item.to"
          class="app-shell__nav-link"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </aside>

    <section class="app-shell__content">
      <header class="app-shell__header">
        <div>
          <p class="app-shell__header-label">当前登录</p>
          <strong>{{ authStore.user?.nickname || authStore.user?.username || '未登录' }}</strong>
        </div>

        <button class="ghost-button" type="button" @click="logout">退出登录</button>
      </header>

      <main class="app-shell__main">
        <router-view />
      </main>
    </section>
  </div>
</template>
