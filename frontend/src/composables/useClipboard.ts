import { ref, readonly } from 'vue'

/**
 * 剪贴板操作composable
 * 提供复制文本到剪贴板的功能
 */
export function useClipboard() {
  const isSupported = ref('clipboard' in navigator)
  const copiedText = ref('')
  const error = ref<string | null>(null)

  async function copy(text: string): Promise<boolean> {
    error.value = null
    
    if (!isSupported.value) {
      fallbackCopy(text)
      copiedText.value = text
      return true
    }

    try {
      await navigator.clipboard.writeText(text)
      copiedText.value = text
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '复制失败'
      fallbackCopy(text)
      copiedText.value = text
      return true
    }
  }

  function fallbackCopy(text: string) {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }

  return {
    isSupported: readonly(isSupported),
    copiedText: readonly(copiedText),
    error: readonly(error),
    copy
  }
}
