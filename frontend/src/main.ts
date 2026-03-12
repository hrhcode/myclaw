/**
 * 应用入口
 * 初始化 Vue 应用和路由
 */
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
