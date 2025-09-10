import os
import sys
import subprocess
import threading
import time
from backend import app
from http_server import start_frontend
def start_backend():
    """启动后端服务"""
    print("启动后端服务...")
    app.run(debug=True, port=5050, use_reloader=False)

def main():
    """主函数"""
    print("Android Media Backup 应用启动中...")
    
    # 检查ADB是否可用
    adb_path = os.path.join(os.path.dirname(__file__), 'adb', 'adb')
    if not os.path.exists(adb_path):
        print("错误: 未找到ADB工具，请确保adb文件夹存在")
        return
    
    # 在后台线程中启动后端
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # 等待后端启动
    time.sleep(2)
    
    # 启动前端
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动前端时发生错误: {e}")

if __name__ == "__main__":
    main()