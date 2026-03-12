import { ref, onMounted, onUnmounted } from 'vue'

interface KeyboardShortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: () => void
  description: string
}

/**
 * 键盘快捷键composable
 * 支持注册和管理键盘快捷键
 */
export function useKeyboard() {
  const shortcuts = ref<KeyboardShortcut[]>([])

  function registerShortcut(shortcut: KeyboardShortcut) {
    shortcuts.value.push(shortcut)
    return () => {
      const index = shortcuts.value.indexOf(shortcut)
      if (index > -1) {
        shortcuts.value.splice(index, 1)
      }
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    for (const shortcut of shortcuts.value) {
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase()
      const ctrlMatch = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey
      const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey
      const altMatch = shortcut.alt ? event.altKey : !event.altKey

      if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
        event.preventDefault()
        shortcut.handler()
        return
      }
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    shortcuts,
    registerShortcut
  }
}
