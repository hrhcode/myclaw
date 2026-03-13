<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  disabled?: boolean
  placeholder?: string
  model?: string
}>()

const emit = defineEmits<{
  (e: 'submit', value: string, image?: string): void
}>()

const input = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isFocused = ref(false)
const selectedImage = ref<string | null>(null)
const imageError = ref<string | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

const MAX_IMAGE_SIZE = 5 * 1024 * 1024

function handleSubmit() {
  const value = input.value.trim()
  if ((!value && !selectedImage.value) || props.disabled) return
  
  emit('submit', value, selectedImage.value || undefined)
  input.value = ''
  selectedImage.value = null
  imageError.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function handleImageSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  if (!file.type.startsWith('image/')) {
    imageError.value = '请选择图片文件'
    return
  }
  
  if (file.size > MAX_IMAGE_SIZE) {
    imageError.value = '图片大小不能超过 5MB'
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    selectedImage.value = e.target?.result as string
    imageError.value = null
  }
  reader.onerror = () => {
    imageError.value = '图片读取失败'
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  selectedImage.value = null
  imageError.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function adjustHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

function focus() {
  textareaRef.value?.focus()
}

function setContent(value: string) {
  input.value = value
  adjustHeight()
}

defineExpose({ focus, setContent })
</script>

<template>
  <form @submit.prevent="handleSubmit" class="message-input">
    <div 
      class="input-wrapper"
      :class="{ focused: isFocused }"
    >
      <div class="input-glow" v-if="isFocused" />
      
      <div class="toolbar">
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          @change="handleImageSelect"
          class="hidden-input"
        />
        <button
          type="button"
          @click="fileInputRef?.click()"
          :disabled="disabled"
          class="toolbar-btn"
          title="上传图片"
        >
          <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      
      <textarea
        ref="textareaRef"
        v-model="input"
        :placeholder="placeholder || '输入消息...'"
        :disabled="disabled"
        @input="adjustHeight"
        @focus="isFocused = true"
        @blur="isFocused = false"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift.exact="() => {}"
        rows="1"
        class="input-field"
      />
      <button
        type="submit"
        :disabled="disabled || (!input.trim() && !selectedImage)"
        class="submit-btn"
      >
        <div class="btn-glow" />
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
    
    <div v-if="selectedImage" class="image-preview">
      <img :src="selectedImage" alt="预览图片" class="preview-image" />
      <button
        type="button"
        @click="removeImage"
        class="remove-image-btn"
        title="删除图片"
      >
        <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div v-if="imageError" class="error-message">
      {{ imageError }}
    </div>
    
    <div class="input-hint">
      <span>Enter 发送 · Shift+Enter 换行</span>
    </div>
  </form>
</template>

<style scoped>
.message-input {
  width: 100%;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.75rem;
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  transition: all 0.3s ease;
  overflow: hidden;
}

.input-wrapper.focused {
  border-color: hsl(var(--primary) / 0.5);
  box-shadow: 0 0 0 3px hsl(var(--primary) / 0.1);
}

.input-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, 
    transparent 0%,
    hsl(var(--primary) / 0.05) 50%,
    transparent 100%
  );
  animation: shimmer 2s linear infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.hidden-input {
  display: none;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding-bottom: 0.25rem;
}

.toolbar-btn {
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--muted-foreground));
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toolbar-btn:hover:not(:disabled) {
  background: hsl(var(--muted) / 0.5);
  color: hsl(var(--foreground));
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-btn .icon {
  width: 1.25rem;
  height: 1.25rem;
}

.input-field {
  flex: 1;
  padding: 0.5rem;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-size: 0.875rem;
  line-height: 1.5;
  color: hsl(var(--foreground));
  max-height: 12.5rem;
  position: relative;
  z-index: 1;
}

.input-field::placeholder {
  color: hsl(var(--muted-foreground));
}

.input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn {
  position: relative;
  padding: 0.625rem;
  background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.8) 100%);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  color: hsl(var(--primary-foreground));
  transition: all 0.3s ease;
  overflow: hidden;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.submit-btn:hover:not(:disabled) .btn-glow {
  transform: translateX(100%);
}

.submit-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 20px -5px hsl(var(--primary) / 0.5);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
  position: relative;
  z-index: 1;
}

.image-preview {
  position: relative;
  display: inline-block;
  margin-top: 0.75rem;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid hsl(var(--border));
}

.preview-image {
  max-width: 200px;
  max-height: 200px;
  display: block;
  object-fit: contain;
}

.remove-image-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.375rem;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-image-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: scale(1.1);
}

.remove-image-btn .icon {
  width: 1rem;
  height: 1rem;
}

.error-message {
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: hsl(var(--destructive) / 0.1);
  border: 1px solid hsl(var(--destructive) / 0.2);
  border-radius: var(--radius);
  color: hsl(var(--destructive));
  font-size: 0.875rem;
}

.input-hint {
  margin-top: 0.5rem;
  text-align: right;
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}
</style>
