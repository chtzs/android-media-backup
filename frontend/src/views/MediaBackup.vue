<script lang="ts">
import Dialog from '@/components/Dialog.vue'
import { getApiUrl } from '@/config/api'
</script>

<template>
  <div class="media-backup">
    <div class="header">
      <h1>Android Media Backup</h1>
      <div class="device-status">
        <span :class="{ connected: deviceConnected }">
          {{ deviceConnected ? '设备已连接' : '设备未连接' }}
        </span>
        <button @click="checkDeviceStatus" class="refresh-btn">刷新状态</button>
      </div>
    </div>

    <div class="steps">
      <div class="step" :class="{ active: currentStep === 1 }">
        <div class="step-number">1</div>
        <div class="step-description">
          <h3>扫描和选择文件</h3>
          <p>扫描设备上的媒体文件并选择要备份的文件</p>
        </div>
      </div>

      <div class="step" :class="{ active: currentStep === 2 }">
        <div class="step-number">2</div>
        <div class="step-description">
          <h3>备份文件</h3>
          <p>将选中的文件备份到本地目录</p>
        </div>
      </div>

      <div class="step" :class="{ active: currentStep === 3 }">
        <div class="step-number">3</div>
        <div class="step-description">
          <h3>预览和确认</h3>
          <p>预览备份的文件，决定这些文件的去留</p>
        </div>
      </div>

      <div class="step" :class="{ active: currentStep === 4 }">
        <div class="step-number">4</div>
        <div class="step-description">
          <h3>完成备份</h3>
          <p>通过删除设备上的原文件来减少存储占用</p>
        </div>
      </div>
    </div>

    <!-- 步骤1: 扫描和选择 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="scan-controls">
        <input v-model="scanPath" placeholder="扫描路径 (默认: /sdcard/DCIM/Camera/)" class="path-input" />
        <button @click="scanMediaFiles" :disabled="!deviceConnected" class="scan-btn">
          扫描媒体文件
        </button>
        <div class="selection-controls">
          <button @click="selectAll" class="select-btn">全选</button>
          <button @click="deselectAll" class="select-btn">全部取消</button>
        </div>
      </div>

      <div class="file-list">
        <div class="file-filters">
          <select v-model="groupBy" class="filter-select">
            <option value="all">不分组</option>
            <option value="year">按年分组</option>
            <option value="month">按月分组</option>
            <option value="day">按日分组</option>
          </select>

          <select v-model="sortBy" class="filter-select">
            <option value="time">按时间排序</option>
            <option value="size">按大小排序</option>
          </select>

          <select v-model="sortOrder" class="filter-select" @change="resetContext">
            <option value="asc">升序</option>
            <option value="desc">降序</option>
          </select>
        </div>

        <div class="file-content" v-if="groupedFiles">
          <div v-for="(files, group) in groupedFiles" :key="group" class="file-group">
            <h4>{{ group }}</h4>
            <div v-for="(file, idx) in files" :key="file.path" :class="['file-item', { selected: file.selected }]">
              <input type="checkbox" :checked="file.selected" @change="toggleFileSelection(file, idx)" />
              <div class="file-info" @click="toggleFileSelection(file, idx)">
                <div class="file-name">{{ getFileName(file.path) }}</div>
                <div class="file-details">
                  {{ formatSize(file.size) }} •
                  {{ formatDate(file.modified_time) }}
                </div>
              </div>
              <button class="file-select-here" v-show="selectFrom !== -1"
                @click="selectRange(selectFrom, idx)">选到这里</button>
            </div>
          </div>
        </div>

        <div v-else class="no-files">
          <p v-if="mediaFiles.length === 0">
            {{ deviceConnected ? '点击"扫描媒体文件"开始扫描' : '请先连接设备' }}
          </p>
          <p v-else>没有匹配的文件</p>
        </div>
      </div>

      <div class="step-actions">
        <button @click="currentStep = 2" :disabled="selectedFiles.length === 0" class="next-btn">
          下一步: 备份文件 ({{ selectedFiles.length }} 个文件选中)
        </button>
      </div>
    </div>

    <!-- 步骤2: 备份文件 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="backup-controls">
        <input v-model="backupDir" placeholder="备份目录 (默认: backup)" class="path-input" />
        <button @click="startBackup" class="backup-btn">开始备份</button>
      </div>

      <div class="backup-progress" v-if="backupInProgress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: backupProgress + '%' }"></div>
        </div>
        <div class="progress-info">
          <div>进度: {{ backupProgress.toFixed(1) }}%</div>
          <div>当前文件: {{ currentBackupFile }}</div>
          <div>
            已复制: {{ formatSize(copiedSize) }} /
            {{ formatSize(totalSize) }}
          </div>
        </div>
      </div>

      <div class="backup-results" v-if="backupCompleted">
        <h3>备份完成</h3>
        <p>成功备份 {{ successfulBackups }} 个文件</p>
        <p v-if="failedBackups > 0">失败 {{ failedBackups }} 个文件</p>
      </div>

      <div class="step-actions">
        <button @click="currentStep = 1" class="prev-btn">上一步</button>
        <button @click="currentStep = 3" :disabled="!backupCompleted" class="next-btn">
          下一步: 预览文件
        </button>
      </div>
    </div>

    <!-- 步骤3: 预览和确认 -->
    <div v-if="currentStep === 3" class="step-content">
      <Dialog v-model:visible="localFileDeleteDialogVisible" title="⚠️ 删除确认" @confirm="deleteLocalFiles"
        @cancel="() => { localFileDeleteDialogVisible = false; }">
        <h3>将会从本地删除所选的文件。</h3>
        <h3>手机端不会受到任何影响。</h3>
      </Dialog>
      <div class="preview-description">
        以下文件已经保存到你的本地文件夹{{ backupDir }}内。请预览并勾选<span style="color: red;">不想保存</span>的文件。被勾选的文件将从你的本地文件夹内删除。
      </div>
      <div class="preview-controls">
        <button @click="loadBackupFiles" class="load-btn">加载备份文件</button>
        <button @click="() => { localFileDeleteDialogVisible = true; console.log('Yes'); }" class="load-btn"
          style="background-color: #f44336;">删除选中的文件 ({{ selectedBackupFiles.length }} 个文件选中)</button>
      </div>

      <div class="preview-list">
        <div v-for="file in backupFiles" :key="file.local_path" class="preview-item">
          <input type="checkbox" v-model="file.selected" class="preview-checkbox" />

          <div class="preview-content">
            <img v-if="isImage(file.name)" :src="getFileUrl(file.local_path)" :alt="file.name" class="preview-image" />
            <video v-else-if="isVideo(file.name)" :src="getFileUrl(file.local_path)" controls
              class="preview-video"></video>
            <div v-else class="preview-icon">📄</div>

            <div class="preview-info">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-details">
                {{ formatSize(file.size) }} •
                {{ formatDate(file.modified_time) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button @click="currentStep = 2" class="prev-btn">上一步</button>
        <button @click="currentStep = 4" class="next-btn">
          下一步: 完成备份
        </button>
      </div>
    </div>

    <!-- 步骤4: 删除文件 -->
    <div v-if="currentStep === 4" class="step-content">
      <Dialog v-model:visible="remoteFileDeleteDialogVisible" title="⚠️ 删除确认" @confirm="deleteRemoteFiles"
        @cancel="() => { remoteFileDeleteDialogVisible = false; }">
        <h3>将会从手机中删除<span style="color: red;">剩余</span>的文件。</h3>
        <h3>软件保证只会删除手机和本地同时拥有的文件，并通过md5校验和确保文件一致。</h3>
        <h3>请仔细检查备份文件夹，确认文件已经备份成功。</h3>
        <h3>此操作不可逆，请谨慎操作！</h3>
        <h3>此操作不可逆，请谨慎操作！</h3>
        <h3>此操作不可逆，请谨慎操作！</h3>
      </Dialog>
      <div class="delete-warning">
        <h3>⚠️ 删除确认</h3>
        <p>您确定要删除设备上的 {{ restBackupFiles.length }} 个文件吗？</p>
        <p>此操作不可逆，请谨慎操作！</p>
      </div>

      <div class="delete-list">
        <div v-for="file in restBackupFiles" :key="file.local_path" class="delete-item">
          {{ getFileName(file.name) }}
        </div>
      </div>

      <div class="step-actions">
        <button @click="currentStep = 3" class="prev-btn">上一步</button>
        <button @click="() => { remoteFileDeleteDialogVisible = true; }" class="delete-btn">确认删除</button>
      </div>

      <div class="delete-results" v-if="deleteCompleted">
        <h3>删除完成</h3>
        <p>成功删除 {{ successfulDeletes }} 个文件</p>
        <p v-if="failedDeletes > 0">失败 {{ failedDeletes }} 个文件</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface MediaFile {
  path: string
  size: number
  modified_time: number
  selected: boolean
  backup_path?: string
  backup_success?: boolean
  backup_time?: string
}

interface BackupFile {
  name: string
  remote_path: string
  local_path: string
  size: number
  modified_time: number
  selected: boolean
}

// 状态管理
const deviceConnected = ref(false)
const currentStep = ref(1)
const scanPath = ref('/sdcard/DCIM/HeyBox')
const mediaFiles = ref<MediaFile[]>([])
const groupBy = ref('all')
const sortBy = ref('time')
const sortOrder = ref('desc') // asc: 升序, desc: 降序
const backupDir = ref('backup')
const backupInProgress = ref(false)
const backupProgress = ref(0)
const currentBackupFile = ref('')
const copiedSize = ref(0)
const totalSize = ref(0)
const backupCompleted = ref(false)
const successfulBackups = ref(0)
const failedBackups = ref(0)
const backupFiles = ref<BackupFile[]>([])
// const filesToDelete = ref<string[]>([])
const deleteCompleted = ref(false)
const successfulDeletes = ref(0)
const failedDeletes = ref(0)
const selectFrom = ref(-1)
const successBackupFiles = ref<MediaFile[]>([])
const localFileDeleteDialogVisible = ref(false)
const remoteFileDeleteDialogVisible = ref(false);

// 计算属性
const selectedFiles = computed(() =>
  mediaFiles.value.filter(file => file.selected)
)

const selectedBackupFiles = computed(() =>
  backupFiles.value.filter(file => file.selected)
)

const restBackupFiles = computed(() =>
  backupFiles.value.filter(file => !file.selected)
)

const groupedFiles = computed(() => {
  if (!groupBy.value) return null

  const groups: { [key: string]: MediaFile[] } = {}

  mediaFiles.value.forEach(file => {
    const date = new Date(file.modified_time * 1000)
    let groupKey = ''

    switch (groupBy.value) {
      case 'all':
        groupKey = '全部'
        break
      case 'year':
        groupKey = date.getFullYear().toString()
        break
      case 'month':
        groupKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`
        break
      case 'day':
        groupKey = date.toISOString().split('T')[0]
        break
    }

    if (!groups[groupKey]) {
      groups[groupKey] = []
    }
    groups[groupKey].push(file)
  })

  // 排序
  Object.keys(groups).forEach(key => {
    groups[key].sort((a, b) => {
      let comparison = 0

      if (sortBy.value === 'size') {
        comparison = a.size - b.size
      } else {
        comparison = a.modified_time - b.modified_time
      }

      // 根据排序方向调整结果
      return sortOrder.value === 'asc' ? comparison : -comparison
    })
  })

  return groups
})

const selectRange = (from: number, to: number) => {
  if (!groupedFiles.value) return;

  let group = groupedFiles.value
  for (let key in group) {
    group[key].forEach((val, idx) => {
      if (from <= idx && idx <= to) {
        val.selected = true
      }
    })
  }
}

const resetContext = () => {
  selectFrom.value = -1;
}

const checkDeviceStatus = async () => {
  try {
    const response = await fetch(getApiUrl('CHECK_DEVICE'))
    const data = await response.json()
    deviceConnected.value = data.connected
  } catch (error) {
    console.error('检查设备状态失败:', error)
    deviceConnected.value = false
  }
}

const scanMediaFiles = async () => {
  try {
    const response = await fetch(getApiUrl('SCAN_MEDIA'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ path: scanPath.value }),
    })

    if (response.ok) {
      const data = await response.json()
      mediaFiles.value = data.files
    }
  } catch (error) {
    console.error('扫描文件失败:', error)
  }
}

const toggleFileSelection = (file: MediaFile, idx: number) => {
  file.selected = !file.selected
  selectFrom.value = idx;
}

const selectAll = () => {
  mediaFiles.value.forEach(file => {
    file.selected = true
  })
}

const deselectAll = () => {
  mediaFiles.value.forEach(file => {
    file.selected = false
  })
}

const startBackup = async () => {
  backupInProgress.value = true
  backupCompleted.value = false
  successfulBackups.value = 0
  failedBackups.value = 0

  totalSize.value = selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
  copiedSize.value = 0

  try {
    const response = await fetch(getApiUrl('BACKUP'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        files: selectedFiles.value,
        backup_dir: backupDir.value,
      }),
    })


    if (response.body) {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      reader.read().then(function processText({ done, value }): any {
        if (done) {
          return;
        }
        // 将读取到的内容转换为字符串
        const progress = JSON.parse(decoder.decode(value))
        backupProgress.value = progress.progress
        currentBackupFile.value = progress.current_file
        copiedSize.value = progress.copied_size

        if (progress.progress === 100) {
          backupInProgress.value = false
          backupCompleted.value = true

          // 统计成功和失败的数量
          successfulBackups.value = progress.count_success
          failedBackups.value = selectedFiles.value.length - successfulBackups.value
          return;
        }
        return reader.read().then(processText);
      });
    }
  } catch (error) {
    console.error('备份失败:', error)
    backupInProgress.value = false
  }
}

const loadBackupFiles = async () => {
  try {
    const response = await fetch(`${getApiUrl('PREVIEW_BACKUP')}?backup_dir=${encodeURIComponent(backupDir.value)}`)
    if (response.ok) {
      const data = await response.json()
      backupFiles.value = data.files.map((file: any) => ({
        ...file,
        selected: false
      }))
    }
  } catch (error) {
    console.error('加载备份文件失败:', error)
  }
}

const deleteLocalFiles = async () => {
  try {
    const response = await fetch(getApiUrl('DELETE_LOCAL_FILES'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ files: selectedBackupFiles.value.map(file => file.local_path) }),
    })

    if (response.ok) {
      const data = await response.json()

      alert(`成功删除 ${data.count} 个本地文件（不影响手机原文件）`)
    }
  } catch (error) {
    console.error('删除文件失败:', error)
  }
}

const deleteRemoteFiles = async () => {
  try {
    const response = await fetch(getApiUrl('DELETE_REMOTE_FILES'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        files: restBackupFiles.value.map(file => {
          return {
            local_path: file.local_path,
            remote_path: file.remote_path
          }
        })
      }),
    })

    if (response.ok) {
      const data = await response.json()
      let count = 0;
      data.results.forEach((re: any) => {
        if (re.delete_success) {
          count++;
        }
      })

      successfulDeletes.value = count;
      deleteCompleted.value = true;
      alert(`成功删除 ${count} 个手机文件`)
    }
  } catch (error) {
    console.error('删除文件失败:', error)
  }
}

// 工具函数
const getFileName = (path: string) => {
  return path.split('/').pop() || path
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString()
}

const isImage = (filename: string) => {
  return /\.(jpg|jpeg|png|gif|bmp)$/i.test(filename)
}

const isVideo = (filename: string) => {
  return /\.(mp4|avi|mov|mkv)$/i.test(filename)
}

const getFileUrl = (path: string) => {
  return `${getApiUrl('GET_MEDIA_FILE')}?file_path=${path}`
}

// 生命周期
onMounted(() => {
  checkDeviceStatus()
})
</script>

<style scoped>
.media-backup {
  height: 100%;
  /* width: 1200px; */
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-status .connected {
  color: #4caf50;
  font-weight: bold;
}

.refresh-btn {
  padding: 5px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
}

.step {
  display: flex;
  align-items: center;
  flex: 1;
  opacity: 0.6;
  transition: opacity 0.3s;
}

.step.active {
  opacity: 1;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  font-weight: bold;
}

.step.active .step-number {
  background: #2196f3;
  color: white;
}

.step-description h3,
.step-content h3 {
  margin: 0;
  font-size: 14px;
}

.step-description p,
.step-content p {
  margin: 0;
  font-size: 12px;
  color: #666;
}

.step-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  /* I spent 3 hours just to find this one line of code. */
  /* And I still don't know why it prevents the flex container from overflowing.  */
  min-height: 0;
}

.step-description {
  width: 220px;
}

.scan-controls,
.backup-controls,
.preview-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: center;
}

.path-input {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  flex: 1;
}

.scan-btn,
.backup-btn,
.load-btn {
  padding: 8px 16px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.scan-btn:disabled,
.backup-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.selection-controls {
  display: flex;
  gap: 10px;
}

.select-btn {
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.file-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.filter-select {
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.file-list {
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-group {
  margin-bottom: 20px;
}

.file-group h4 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #f8f9fa;
}

.file-select-here {
  padding: 8px 16px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  visibility: hidden;
}

.file-item:hover .file-select-here {
  visibility: visible;
}

.file-item.selected {
  background-color: #e3f2fd;
  border-color: #2196f3;
}

.file-info {
  margin-left: 10px;
  flex: 1;
}

.file-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.file-details {
  font-size: 12px;
  color: #666;
}

.no-files {
  text-align: center;
  padding: 40px;
  color: #666;
}

.backup-progress {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #f8f9fa;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: #4caf50;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.backup-results {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #4caf50;
  border-radius: 4px;
  background: #f1f8e9;
}

.preview-description {
  margin: 20px 0;
}

.preview-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin: 20px 0;
}

.preview-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.preview-checkbox {
  margin: 10px;
}

.preview-content {
  padding: 10px;
}

.preview-image,
.preview-video {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
}

.preview-icon {
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  background: #f0f0f0;
  border-radius: 4px;
}

.preview-info {
  margin-top: 10px;
}

.delete-warning {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #ff9800;
  border-radius: 4px;
  background: #fff3e0;
}

.delete-list {
  flex: 1;
  overflow-y: auto;
  margin: 20px 0;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.delete-item {
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.delete-item:last-child {
  border-bottom: none;
}

.delete-results {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #4caf50;
  border-radius: 4px;
  background: #f1f8e9;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.prev-btn,
.next-btn,
.delete-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.prev-btn {
  background: #f5f5f5;
  color: #333;
}

.next-btn {
  background: #2196f3;
  color: white;
}

.next-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.delete-btn {
  background: #f44336;
  color: white;
}

.delete-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>