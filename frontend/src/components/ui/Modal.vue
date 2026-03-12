<script setup lang="ts">
/**
 * Modal 弹窗组件
 * 提供统一的弹窗样式，支持多种尺寸
 */
import { watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  closable?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

watch(() => props.modelValue, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

function close() {
  if (props.closable !== false) {
    emit('update:modelValue', false)
  }
}

function onOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    close()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click="onOverlayClick">
        <div class="modal" :class="size">
          <div v-if="title || $slots.header" class="modal-header">
            <div class="modal-header-content">
              <h3 class="modal-title">{{ title }}</h3>
              <slot name="header" />
            </div>
            <button v-if="closable !== false" class="modal-close" @click="close">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: hsl(var(--card));
  border-radius: var(--radius-lg);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl), 0 0 0 1px hsl(var(--border));
  overflow: hidden;
}

.sm {
  width: 100%;
  max-width: 400px;
}

.md {
  width: 100%;
  max-width: 560px;
}

.lg {
  width: 100%;
  max-width: 720px;
}

.xl {
  width: 100%;
  max-width: 960px;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid hsl(var(--border));
  background: linear-gradient(180deg, hsl(var(--muted) / 0.2) 0%, transparent 100%);
}

.modal-header-content {
  flex: 1;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.01em;
}

.modal-close {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: hsl(var(--muted));
  color: hsl(var(--foreground));
}

.modal-close svg {
  width: 1.25rem;
  height: 1.25rem;
}

.modal-body {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid hsl(var(--border));
  background: hsl(var(--muted) / 0.2);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95) translateY(10px);
}
</style>
