<script setup>
const props = defineProps({
  users: {
    type: Array,
    default: () => []
  }
})

function summarizeByRole(role) {
  return props.users.filter((item) => item.role === role).length
}
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">USER OPS</p>
        <h3>用户管理</h3>
        <p>快速查看三类角色账户规模和当前状态。</p>
      </div>
      <span class="dashboard-panel__badge">{{ users.length }} 个账号</span>
    </div>

    <div class="profile-grid">
      <div class="profile-grid__item">
        <dt>管理员</dt>
        <dd>{{ summarizeByRole('admin') }}</dd>
      </div>
      <div class="profile-grid__item">
        <dt>商家</dt>
        <dd>{{ summarizeByRole('merchant') }}</dd>
      </div>
      <div class="profile-grid__item">
        <dt>用户</dt>
        <dd>{{ summarizeByRole('customer') }}</dd>
      </div>
      <div class="profile-grid__item">
        <dt>启用账号</dt>
        <dd>{{ users.filter((item) => item.status !== 'disabled').length }}</dd>
      </div>
    </div>
  </article>
</template>
