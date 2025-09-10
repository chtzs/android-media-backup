
from pathlib import Path
from datetime import datetime

IMAGE_EXTS  = {"jpg", "jpeg", "png", "heic", "gif"}
VIDEO_EXTS  = {"mp4", "mov"}

class MediaInfo:
    supported_types = {'IMG', "VID"}
    def __init__(self, path: str, size: int):
        self.path = path
        self.name = Path(path).name
        self.year = 2001
        self.month = 6
        self.day = 18
        self.hour = 7
        self.minute = 0
        self.second = 0
        self.extra = 0
        self.ext = "Unknown"
        self.size = size
        self.size_str = ""
        one_gigabyte = 1024 ** 3
        one_megabyte = 1024 ** 2
        if size >= one_gigabyte:
            self.size_str = f'{size / one_gigabyte:.2f} GB'
        else:
            self.size_str =  f'{size / one_megabyte:.2f} MB'
            
        format_func = [self._try_parse_format1, self._try_parse_format2, self._try_parse_format3, self._parse_any]
        success = False
        for func in format_func:
            self.extra = 0
            if func():
                success = True
                break
        if not success:
            raise ValueError(f'Unsupported file format: {path}')
    
    def modified_time(self):
        return datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)
        
    def assign_date(self, date: datetime):
        self.year = date.year
        self.month = date.month
        self.day = date.day
        self.hour = date.hour
        self.minute = date.minute
        self.second = date.second
        
    # ('IMG' or 'VID')YYmmddHHMMSS[_num].jpg
    def _try_parse_format1(self):
        filename, ext = self.name.split('.')
        self.ext = ext
        self.media_type = filename[:3]
        if not self.media_type in self.supported_types:
            return False
        filename = filename.removeprefix(self.media_type)
        
        res = filename.split('_')
        filename = res[0]
        if len(res) == 1:
            pass
        elif len(res) == 2:
            try:
                self.extra = int(res[1])
            except ValueError:
                return False
        else:
            return False
        
        try:
            date = datetime.strptime(filename, "%Y%m%d%H%M%S")
        except ValueError:
            return False
        
        self.assign_date(date)
        return True
    
    # ('IMG' or 'VID')_YYmmdd_HHMMSS[_num].jpg
    def _try_parse_format2(self):
        filename, ext = self.name.split('.')
        self.ext = ext
        self.media_type = filename[:3]
        if not self.media_type in self.supported_types:
            return False
        filename = filename.removeprefix(f'{self.media_type}_')
        
        res = filename.split('_')
        if len(res) == 2:
            pass
        elif len(res) == 3:
            try:
                self.extra = int(res[2])
            except ValueError:
                return False
        else:
            return False
        
        filename = f'{res[0]}_{res[1]}'
        
        try:
            date = datetime.strptime(filename, "%Y%m%d_%H%M%S")
        except ValueError:
            return False
        
        self.assign_date(date)
        return True
    
    # ('IMG' or 'VID')_YYmmddHHMMSS[_num].jpg
    def _try_parse_format3(self):
        filename, ext = self.name.split('.')
        self.ext = ext
        self.media_type = filename[:3]
        if not self.media_type in self.supported_types:
            return False
        filename = filename.removeprefix(f'{self.media_type}_')
        
        res = filename.split('_')
        filename = res[0]
        if len(res) == 1:
            pass
        elif len(res) == 2:
            try:
                self.extra = int(res[1])
            except ValueError:
                return False
        else:
            return False
        
        try:
            date = datetime.strptime(filename, "%Y%m%d%H%M%S")
        except ValueError:
            return False
        
        self.assign_date(date)
        return True
    
    def _parse_any(self):
        _, ext = self.name.split('.')
        self.ext = ext
        if ext in IMAGE_EXTS:
            self.media_type = 'IMG'
        elif ext in VIDEO_EXTS:
            self.media_type = 'VID'
        else:
            return False
        return True
    
    def __str__(self):
        return f'{self.name}: {self.media_type}, {self.size_str}'