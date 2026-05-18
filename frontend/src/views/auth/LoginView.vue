<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({
  username: 'merchant_demo',
  password: 'demo123'
})

const isSubmitting = ref(false)
const errorMessage = ref('')

async function submitLogin() {
  isSubmitting.value = true
  errorMessage.value = ''

  try {
    await authStore.login({
      username: form.username,
      password: form.password
    })

    const redirectTarget =
      typeof route.query.redirect === 'string' && route.query.redirect ? route.query.redirect : '/'

    await router.push(redirectTarget)
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '登录失败，请检查账号与密码'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-panel">
      <div>
        <p class="login-panel__eyebrow">Task 7</p>
        <h1>登录系统</h1>
        <p class="login-panel__description">
          这里先提供最小可运行的认证入口、统一路由壳子和后续角色页面占位。
        </p>
      </div>

      <form class="login-form" @submit.prevent="submitLogin">
        <label class="field">
          <span>用户名</span>
          <input v-model.trim="form.username" type="text" placeholder="请输入用户名" />
        </label>

        <label class="field">
          <span>密码</span>
          <input v-model="form.password" type="password" placeholder="请输入密码" />
        </label>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '登录中...' : '登录并进入工作台' }}
        </button>
      </form>

      <div class="demo-accounts">
        <p>演示账号</p>
        <ul>
          <li>商家：merchant_demo / demo123</li>
          <li>用户：customer_demo / demo123</li>
          <li>管理员：admin_demo / demo123</li>
        </ul>
      </div>
    </section>
  </div>
</template>
