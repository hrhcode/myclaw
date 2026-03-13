<script setup lang="ts">
/**
 * CustomSelect 自定义下拉选择组件
 * 使用 div 模拟下拉菜单，支持完全自定义样式
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue?: string
  options: { value: string; label: string }[]
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isOpen = ref(false)
const selectRef = ref<HTMLElement | null>(null)

const selectedLabel = computed(() => {
  const option = props.options.find(o => o.value === props.modelValue)
  return option?.label || props.placeholder || ''
})

function toggleDropdown() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function selectOption(value: string) {
  emit('update:modelValue', value)
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (selectRef.value && !selectRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div
    ref="selectRef"
    class="custom-select"
    :class="{ disabled, open: isOpen }"
  >
    <div
      class="select-trigger"
      @click="toggleDropdown"
    >
      <span class="select-value">{{ selectedLabel }}</span>
      <svg
        class="select-arrow"
        :class="{ rotated: isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    
    <Transition name="dropdown">
      <div v-if="isOpen" class="select-dropdown">
        <div
          v-for="option in options"
          :key="option.value"
          class="select-option"
          :class="{ selected: option.value === modelValue }"
          @click="selectOption(option.value)"
        >
          {{ option.label }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.custom-select {
  position: relative;
  min-width: 100px;
}

.custom-select.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  background: hsl(var(--muted) / 0.5);
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  font-size: 0.8125rem;
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.custom-select:not(.disabled) .select-trigger:hover {
  border-color: hsl(var(--primary) / 0.5);
  background: hsl(var(--muted) / 0.7);
}

.custom-select.open .select-trigger {
  border-color: hsl(var(--primary));
  box-shadow: 0 0 0 2px hsl(var(--primary) / 0.2);
}

.select-value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.select-arrow {
  width: 1rem;
  height: 1rem;
  color: hsl(var(--muted-foreground));
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.select-arrow.rotated {
  transform: rotate(180deg);
}

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 50;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  max-height: 200px;
  overflow-y: auto;
}

.select-option {
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  color: hsl(var(--foreground));
  cursor: pointer;
  transition: all 0.15s ease;
}

.select-option:hover {
  background: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

.select-option.selected {
  background: hsl(var(--primary) / 0.1);
  color: hsl(var(--primary));
  font-weight: 500;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
