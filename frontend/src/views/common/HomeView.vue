<script setup>
import { computed } from 'vue'

import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

const welcomeTitle = computed(() => {
  if (authStore.role === 'merchant') {
    return '商家工作台'
  }

  if (authStore.role === 'customer') {
    return '用户推荐首页'
  }

  if (authStore.role === 'admin') {
    return '管理员控制台'
  }

  return '基础路由壳子'
})
</script>

<template>
  <section class="workspace-view">
    <header class="workspace-view__hero">
      <p class="workspace-view__eyebrow">Workspace</p>
      <h2>{{ welcomeTitle }}</h2>
      <p>任务7已接通统一布局、登录流程、路由守卫和基于角色的入口占位。</p>
    </header>

    <div class="workspace-grid">
      <article class="workspace-card">
        <h3>认证状态</h3>
        <p>当前角色：{{ authStore.role || '未识别' }}</p>
      </article>

      <article class="workspace-card">
        <h3>路由结构</h3>
        <p>已提供登录页、根布局页和三类角色入口占位。</p>
      </article>

      <article class="workspace-card">
        <h3>下一步</h3>
        <p>后续任务可以直接在这个壳子上接入商家、用户和管理员视图。</p>
      </article>
    </div>
  </section>
</template>
