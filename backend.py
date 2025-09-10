import os
import json
import subprocess
import time
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from adb import exec, pull, devices, scan_media_files_and_sort, md5_checksum, IMAGE_EXTS, VIDEO_EXTS

from typing import Dict, List

app = Flask(__name__)
CORS(app)

# 配置
LOG_FILE = "backup_log.json"

# 初始化日志文件
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        json.dump([], f)

def md5(file_path: str) -> str:
    # Calculate the MD5 hash of a file.
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def local_md5_checksum(files: List[str]):
    return [md5(file) for file in files]

def is_device_connected():
    """检查设备是否连接"""
    result = devices()
    if result and 'device' in result:
        lines = result.split('\n')
        return len(lines) > 1 and 'device' in lines[1]
    return False

def scan_media_files(path="/sdcard/"):
    """扫描指定路径下的媒体文件"""
    if not is_device_connected():
        return []
    
    scaned_media_files = scan_media_files_and_sort(path)
    media_files = [ {
                        'path': file_info.path,
                        'size': file_info.size,
                        'modified_time': int(file_info.modified_time().timestamp() + file_info.extra),
                        'selected': False
                    }
                   for file_info in scaned_media_files]
    
    return media_files

def backup_files(selected_files, backup_dir):
    """备份选中的文件"""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    results = []
    total_size = sum(f['size'] for f in selected_files)
    copied_size = 0
    counter_success = 0
    
    for file_info in selected_files:
        remote_source_path = file_info['path']
        filename = os.path.basename(remote_source_path)
        dest_path = os.path.join(backup_dir, filename)
        
        # 处理重名文件
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(dest_path):
            dest_path = os.path.join(backup_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        # 使用ADB pull复制文件
        pull(remote_source_path, dest_path)
        
        success = os.path.exists(dest_path)
        file_info['backup_path'] = os.path.abspath(dest_path) if success else None
        file_info['backup_success'] = success
        file_info['backup_time'] = datetime.now().isoformat()
        
        if success:
            copied_size += file_info['size']
            counter_success += 1
        
        results.append(file_info)
        
        # 更新进度
        progress = (copied_size / total_size * 100) if total_size > 0 else 100
        yield {
            'progress': progress,
            'current_file': filename,
            'copied_size': copied_size,
            'total_size': total_size,
            'count_success': counter_success
        }
    
    # 记录备份日志
    log_backup(results)

def log_backup(backup_results):
    """记录备份操作到日志文件"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        logs = []
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'backup_results': backup_results
    }
    logs.append(log_entry)
    
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

def delete_files(files_to_delete):
    """删除手机上的文件"""
    results = []
    for file in files_to_delete:
        file_path = file['remote_path']
        success = True
        try:
            exec(['rm', file_path])
        except RuntimeError:
            success = False
        
        results.append({
            'path': file_path,
            'delete_success': success,
            'delete_time': datetime.now().isoformat()
        })
    
    return results

def get_success_backup_files():
    """获取成功备份的文件"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
    except:
        logs = []
    
    latest = logs[-1]
    success_files = []
    for file_info in latest['backup_results']:
        if file_info['backup_success']:
            success_files.append(file_info)
    
    return success_files

def double_check(files: Dict[str, str]) -> bool:
    local_files = [file['local_path'] for file in files]
    remote_files = [file['remote_path'] for file in files]
    local_md5 = local_md5_checksum(local_files)
    remote_md5 = [res.split()[0].strip() for res in md5_checksum(remote_files)]
    if len(local_md5) != len(remote_md5): return False
    for local, remote in zip(local_md5, remote_md5):
        if local != remote: return False
    return True

@app.route('/api/check-device', methods=['GET'])
def check_device():
    """检查设备连接状态"""
    connected = is_device_connected()
    return jsonify({'connected': connected})

@app.route('/api/scan-media', methods=['POST'])
def scan_media():
    """扫描媒体文件"""
    data = request.json
    path = data.get('path', '/sdcard/')
    
    media_files = scan_media_files(path)
    return jsonify({'files': media_files})

@app.route('/api/backup', methods=['POST'])
def backup():
    """备份文件"""
    data = request.json
    selected_files = data.get('files', [])
    backup_dir = data.get('backup_dir', 'backup')
    
    def generate():
        for file_info in backup_files(selected_files, backup_dir):
            yield f'{json.dumps(file_info)}' + '\n\n'
    
    return app.response_class(generate(), mimetype='text/event-stream')

@app.route('/api/get-media-file', methods=['GET'])
def get_media_file():
    file_path = request.args.get('file_path', '')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    _, ext = os.path.splitext(file_path)
    ext = ext.removeprefix('.')
    if ext.lower() in VIDEO_EXTS:
        return send_file(file_path, mimetype='video/mp4')
    elif ext.lower() in IMAGE_EXTS:
        return send_file(file_path, mimetype='image/jpeg')
    else:
        return jsonify({'error': f'Unsupported file type: {ext}'}), 400

@app.route('/api/preview-backup', methods=['GET'])
def preview_backup():
    """预览备份的文件"""
    backup_dir = request.args.get('backup_dir', 'backup')
    
    if not os.path.exists(backup_dir):
        return jsonify({'files': []})
    
    backup_files = []
    success_files = get_success_backup_files()
    for file in success_files:
        stat = os.stat(file['backup_path'])
        file_info = {
            'name': os.path.basename(file['backup_path']),
            'remote_path': file['path'],
            'local_path': file['backup_path'],
            'size': stat.st_size,
            'modified_time': stat.st_mtime,
            'selected': False
        }
        backup_files.append(file_info)
    
    return jsonify({'files': backup_files})

@app.route('/api/delete-remote-files', methods=['POST'])
def delete_remote_files():
    """删除文件"""
    data = request.json
    files_to_delete = data.get('files', [])
    
    # Double check
    if not double_check(files_to_delete):
        return jsonify({'results': 'Double check failed'}), 500
    results = delete_files(files_to_delete)
    return jsonify({'results': results})

@app.route('/api/delete-local-files', methods=['POST'])
def delete_local_files():
    data = request.json
    files_to_delete = data.get('files', [])
    
    count = 0
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            os.remove(file_path)
            count += 1
            
    return jsonify({'count': count})
    
@app.route('/api/get-logs', methods=['GET'])
def get_logs():
    """获取备份日志"""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        return jsonify({'logs': logs})
    except:
        return jsonify({'logs': []})

if __name__ == '__main__':
    app.run(debug=True, port=5050)