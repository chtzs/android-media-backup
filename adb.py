import os
import subprocess
import tempfile
import tqdm
from typing import Union, List, Dict, Tuple
from pathlib import Path
from datetime import datetime

from media import MediaInfo, IMAGE_EXTS, VIDEO_EXTS

# TMP = Path(os.environ["TEMP"])          # Windows 临时目录
PHONE_TMP_IN = "/sdcard/.amb_tmp_in.txt"   # 手机临时文件
PHONE_TMP_OUT  = "/sdcard/.amb_tmp_out.txt"     # 手机结果文件


def exec(cmd: Union[str, List[str]]) -> str:
    if isinstance(cmd, str):
        completed = subprocess.run(
            ["adb/adb", "shell", cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
    elif isinstance(cmd, list):
        completed = subprocess.run(
            ["adb/adb", "shell"] + cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
    else:
        raise RuntimeError(f'Invalid command {cmd}')
    if completed.returncode != 0:
        raise RuntimeError(f"Failed to execute adb shell: {cmd}\n{completed.stderr}")
    return completed.stdout

def exec_by_tempfile(cmd: Union[str, List[str]]='') -> str:
    # Write to temp file
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
            f.write(cmd)
        elif isinstance(cmd, str):
            f.write(cmd)
        else:
            raise RuntimeError(f'Invalid command {cmd}')
            
        tmp_local = f.name
        
    try:
        # Push to phone
        push(tmp_local, PHONE_TMP_IN)
        # Run and get output
        out = exec(f'sh "{PHONE_TMP_IN}"')
        return out
    finally:
        # Delete temp files
        os.unlink(tmp_local)
        exec(["rm", "-f", PHONE_TMP_IN])

def push(local: str, dest: str) -> str:
    completed = subprocess.run(
        ["adb/adb", "push", local, dest],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Failed to push: {completed.stderr}")
    return completed.stdout

def pull(remote: str, dest: str) -> str:
    completed = subprocess.run(
        ["adb/adb", "pull", remote, dest],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Failed to pull: {completed.stderr}")
    return completed.stdout

def devices() -> str:    
    completed = subprocess.run(
        ["adb/adb", "devices"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Failed to pull: {completed.stderr}")
    return completed.stdout


def calc_files_size(files: list):
    if not files:
        return {}
    out = exec_by_tempfile(['stat -c "%n %s"'] + [f'"{file}"' for file in files])
    sizes = {}
    for line in out.splitlines():
        if line.strip():
            path, size = line.rsplit(" ", 1)
            sizes[path] = int(size)
    return sizes

def sort_and_format(path_size_dict: Dict[str, int]) -> List[MediaInfo]:
    # Sort by bytes
    sorted_items = sorted(path_size_dict.items(), key=lambda x: x[1], reverse=True)

    formatted = [MediaInfo(path, size) for path, size in sorted_items]
    return formatted

def is_image(file: str):
    _, ext = file.split('.')
    return ext.lower() in IMAGE_EXTS

def is_video(file: str):
    _, ext = file.split('.')
    return ext.lower() in VIDEO_EXTS

def list_media(media_dir: str):
    stdout = exec(f"ls {media_dir}")
    files = stdout.splitlines()
    files = [f'{media_dir}/{file}' for file in files if is_image(file) or is_video(file)]
    return files

def scan_media_files_and_sort(media_dir: str="/sdcard/DCIM/Camera") -> List[MediaInfo]:
    media_files = list_media(media_dir)
    media_files = calc_files_size(media_files)
    media_files = sort_and_format(media_files)
    return media_files

def copy_files(media_files: List[MediaInfo], dest: str):
    if not os.path.exists(dest):
        raise FileNotFoundError(f"Backup directory({dest}) is not exist!")
    
    for file in tqdm.tqdm(media_files, desc="Copying media files"):
        pull(file.path, dest)
        
def md5_checksum(files: List[str]) -> List[str]:
    out = exec_by_tempfile(['md5sum'] + [f'"{file}"' for file in files])
    return out.strip().splitlines()
        
def select_range(media_files: List[MediaInfo], start: datetime, end: datetime) -> List[MediaInfo]:
    selected = []
    for file in media_files:
        file_date = datetime(file.year, file.month, file.day, file.hour, file.minute, file.second)
        if start <= file_date <= end:
            selected.append(file)
    return selected