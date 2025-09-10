<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleOverlayClick">
    <div class="dialog-container">
      <div class="dialog-header">
        <h3>{{ title }}</h3>
        <button class="dialog-close" @click="handleClose">×</button>
      </div>
      
      <div class="dialog-content">
        <slot></slot>
      </div>
      
      <div class="dialog-footer">
        <button 
          v-if="showCancel" 
          class="dialog-btn dialog-btn-cancel" 
          @click="handleCancel"
        >
          {{ cancelText }}
        </button>
        <button 
          class="dialog-btn dialog-btn-confirm" 
          @click="handleConfirm"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

const props = withDefaults(defineProps<{
  visible?: boolean,
  title?: string,
  confirmText?: string,
  cancelText?: string,
  showCancel?: boolean,
  closeOnClickOverlay?: boolean
}>(), {
  visible: false,
  title: '提示',
  confirmText: '确认',
  cancelText: '取消',
  showCancel: true,
  closeOnClickOverlay: true
});

const emit = defineEmits(['update:visible', 'confirm', 'cancel', 'close'])

const handleConfirm = () => {
  emit('confirm')
  emit('update:visible', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}

const handleClose = () => {
  emit('close')
  emit('update:visible', false)
}

const handleOverlayClick = () => {
  if (props.closeOnClickOverlay) {
    emit('update:visible', false)
    emit('close')
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.dialog-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 400px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  animation: slideIn 0.3s ease;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.dialog-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.dialog-close:hover {
  background: #f5f5f5;
  color: #666;
}

.dialog-content {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

.dialog-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  min-width: 80px;
}

.dialog-btn-cancel {
  background: #f5f5f5;
  color: #333;
}

.dialog-btn-cancel:hover {
  background: #e8e8e8;
}

.dialog-btn-confirm {
  background: #4caf50;
  color: white;
}

.dialog-btn-confirm:hover {
  background: #45a049;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { 
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>