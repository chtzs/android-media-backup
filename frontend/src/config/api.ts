// API配置
export const API_CONFIG = {
  BASE_URL: 'http://localhost:5050',
  ENDPOINTS: {
    CHECK_DEVICE: '/api/check-device',
    SCAN_MEDIA: '/api/scan-media',
    BACKUP: '/api/backup',
    PREVIEW_BACKUP: '/api/preview-backup',
    DELETE_REMOTE_FILES: '/api/delete-remote-files',
    DELETE_LOCAL_FILES: '/api/delete-local-files',
    GET_MEDIA_FILE: '/api/get-media-file'
  }
}

export const getApiUrl = (endpoint: keyof typeof API_CONFIG.ENDPOINTS) => {
  return API_CONFIG.BASE_URL + API_CONFIG.ENDPOINTS[endpoint]
}