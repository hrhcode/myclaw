/**
 * Toast 消息提示 Composable
 * 提供全局消息提示功能
 */
import { ref, createApp, h } from 'vue'
import Toast from '@/components/ui/Toast.vue'

let toastInstance: InstanceType<typeof Toast> | null = null
let toastApp: ReturnType<typeof createApp> | null = null

function getToastInstance() {
  if (!toastInstance) {
    const container = document.createElement('div')
    document.body.appendChild(container)
    toastApp = createApp({
      render() {
        return h(Toast, {
          ref: (el: InstanceType<typeof Toast>) => {
            toastInstance = el
          }
        })
      }
    })
    toastApp.mount(container)
  }
  return toastInstance!
}

export function useToast() {
  return {
    success: (text: string, duration?: number) => getToastInstance().success(text, duration),
    error: (text: string, duration?: number) => getToastInstance().error(text, duration),
    warning: (text: string, duration?: number) => getToastInstance().warning(text, duration),
    info: (text: string, duration?: number) => getToastInstance().info(text, duration),
  }
}
