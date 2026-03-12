/**
 * 路由配置
 * 定义应用的路由结构
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    redirect: '/chat',
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('@/views/Chat.vue'),
    meta: { title: '聊天', icon: 'chat' },
  },
  {
    path: '/overview',
    name: 'overview',
    component: () => import('@/views/Overview.vue'),
    meta: { title: '概览', icon: 'dashboard' },
  },
  {
    path: '/channels',
    name: 'channels',
    component: () => import('@/views/Channels.vue'),
    meta: { title: '通道', icon: 'channel' },
  },
  {
    path: '/sessions',
    name: 'sessions',
    component: () => import('@/views/Sessions.vue'),
    meta: { title: '会话', icon: 'session' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - MyClaw`
  }
  next()
})

export default router
