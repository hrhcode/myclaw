import { ref, watch, readonly } from 'vue'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'myclaw_theme'

/**
 * 主题切换composable
 * 支持浅色、深色两种模式
 */
export function useTheme() {
  const theme = ref<Theme>(getStoredTheme())
  const isDark = ref(false)

  function getStoredTheme(): Theme {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark') {
      return 'dark'
    }
    return 'light'
  }

  function updateTheme() {
    const dark = theme.value === 'dark'
    isDark.value = dark
    
    if (dark) {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }

  function setTheme(newTheme: Theme) {
    theme.value = newTheme
    localStorage.setItem(STORAGE_KEY, newTheme)
    updateTheme()
  }

  function toggleTheme() {
    setTheme(theme.value === 'light' ? 'dark' : 'light')
  }

  watch(theme, updateTheme, { immediate: true })

  return {
    theme: readonly(theme),
    isDark: readonly(isDark),
    setTheme,
    toggleTheme
  }
}
