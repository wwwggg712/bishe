<script setup>
import { onMounted, ref } from 'vue'

import { fetchAdminUsers } from '../../api/admin.js'
import UserManagerView from './UserManagerView.vue'

const users = ref([])
const errorMessage = ref('')

async function loadUsers() {
  try {
    const payload = await fetchAdminUsers()
    users.value = payload.users || []
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '用户列表加载失败，请稍后重试。'
  }
}

onMounted(async () => {
  await loadUsers()
})
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <div>
        <p class="section-kicker">ADMIN USERS</p>
        <h2>用户管理</h2>
        <p>独立查看管理员、商家与普通用户账户规模和状态。</p>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <UserManagerView :users="users" />
  </section>
</template>
