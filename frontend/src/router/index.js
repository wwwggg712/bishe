import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'

import AppLayout from '../layouts/AppLayout.vue'
import LoginView from '../views/auth/LoginView.vue'
import AdminOverview from '../views/admin/AdminOverview.vue'
import AdminLogPreviewPage from '../views/admin/AdminLogPreviewPage.vue'
import AdminTasksPage from '../views/admin/AdminTasksPage.vue'
import AdminUsersPage from '../views/admin/AdminUsersPage.vue'
import HomeView from '../views/common/HomeView.vue'
import CustomerHome from '../views/customer/CustomerHome.vue'
import ProfileView from '../views/customer/ProfileView.vue'
import RecommendationView from '../views/customer/RecommendationView.vue'
import MerchantDashboard from '../views/merchant/MerchantDashboard.vue'
import { useAuthStore } from '../stores/auth'

export const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      guestOnly: true
    }
  },
  {
    path: '/',
    component: AppLayout,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'home',
        component: HomeView
      },
      {
        path: 'merchant/dashboard',
        name: 'merchant-dashboard',
        component: MerchantDashboard,
        meta: {
          roles: ['merchant']
        }
      },
      {
        path: 'customer/home',
        name: 'customer-home',
        component: CustomerHome,
        meta: {
          roles: ['customer']
        }
      },
      {
        path: 'customer/recommendations',
        name: 'customer-recommendations',
        component: RecommendationView,
        meta: {
          roles: ['customer']
        }
      },
      {
        path: 'customer/profile',
        name: 'customer-profile',
        component: ProfileView,
        meta: {
          roles: ['customer']
        }
      },
      {
        path: 'admin/overview',
        name: 'admin-overview',
        component: AdminOverview,
        meta: {
          roles: ['admin']
        }
      },
      {
        path: 'admin/tasks',
        name: 'admin-tasks',
        component: AdminTasksPage,
        meta: {
          roles: ['admin']
        }
      },
      {
        path: 'admin/logs',
        name: 'admin-log-preview',
        component: AdminLogPreviewPage,
        meta: {
          roles: ['admin']
        }
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: AdminUsersPage,
        meta: {
          roles: ['admin']
        }
      }
    ]
  }
]

export function resolveAuthRedirect(to, authStore) {
  if (to.meta?.requiresAuth && !authStore.isAuthenticated) {
    const redirectTarget = encodeURIComponent(to.fullPath || to.path || '/')
    return `/login?redirect=${redirectTarget}`
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    return '/'
  }

  const allowedRoles = to.meta?.roles || []

  if (allowedRoles.length > 0 && authStore.role && !allowedRoles.includes(authStore.role)) {
    return '/'
  }

  return true
}

export function createRouterHistory() {
  return typeof window === 'undefined' ? createMemoryHistory() : createWebHistory()
}

export function createAppRouter() {
  const router = createRouter({
    history: createRouterHistory(),
    routes,
    scrollBehavior(to, from, savedPosition) {
      if (savedPosition) {
        return savedPosition
      }

      if (to.hash) {
        return {
          el: to.hash,
          top: 16,
          behavior: 'smooth'
        }
      }

      return { top: 0 }
    }
  })

  router.beforeEach((to) => {
    const authStore = useAuthStore()
    return resolveAuthRedirect(to, authStore)
  })

  return router
}

const router = createAppRouter()

export default router
