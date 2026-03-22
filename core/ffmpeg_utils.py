"""FFmpeg 工具模块 - 负责 FFmpeg 命令构建、执行和进度解析"""

import sys
import os
import subprocess
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> str:
    """获取资源文件路径，支持 PyInstaller 打包后的路径解析"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def find_ffmpeg() -> Optional[str]:
    """查找 FFmpeg 可执行文件路径"""
    # 1. 检查当前目录（打包后的资源目录）
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    possible_names = ['ffmpeg.exe', 'ffmpeg']
    if sys.platform == 'win32':
        possible_names = ['ffmpeg.exe']
    elif sys.platform == 'darwin':
        possible_names = ['ffmpeg']
    else:
        possible_names = ['ffmpeg']
    
    for name in possible_names:
        bundled_path = os.path.join(current_dir, 'resources', name)
        if os.path.exists(bundled_path):
            logger.info(f"使用 bundled FFmpeg: {bundled_path}")
            return bundled_path
        
        local_path = os.path.join(current_dir, name)
        if os.path.exists(local_path):
            logger.info(f"使用本地 FFmpeg: {local_path}")
            return local_path
    
    # 2. 检查系统 PATH
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("使用系统 FFmpeg")
            return 'ffmpeg'
    except FileNotFoundError:
        pass
    
    logger.error("未找到 FFmpeg 可执行文件")
    return None


def get_video_info(video_path: str, ffmpeg_path: str = None) -> Optional[Dict]:
    """获取视频信息（时长、分辨率、帧率等）"""
    if not ffmpeg_path:
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            logger.error("未找到 FFmpeg 可执行文件")
            return None
    
    logger.info(f"获取视频信息: {video_path}")
    
    try:
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-f', 'null',
            '-'
        ]
        
        logger.debug(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        logger.debug(f"FFmpeg 返回码: {result.returncode}")
        logger.debug(f"FFmpeg stderr 长度: {len(result.stderr)} 字符")
        
        if result.returncode != 0 and result.returncode != 1:
            # FFmpeg 返回码 1 通常是正常的（因为我们没有输出到文件）
            logger.warning(f"FFmpeg 异常返回码: {result.returncode}")
            logger.warning(f"FFmpeg stderr: {result.stderr[:500]}")
        
        info = {}
        stderr = result.stderr
        
        if not stderr:
            logger.error("FFmpeg 没有输出任何信息")
            return None
        
        # 解析时长
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', stderr)
        if duration_match:
            hours, minutes, seconds = duration_match.groups()
            info['duration'] = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            logger.debug(f"解析到时长: {info['duration']} 秒")
        else:
            logger.debug("未找到时长信息")
        
        # 解析分辨率
        resolution_match = re.search(r'(\d{2,5})x(\d{2,5})', stderr)
        if resolution_match:
            info['width'] = int(resolution_match.group(1))
            info['height'] = int(resolution_match.group(2))
            logger.debug(f"解析到分辨率: {info['width']}x{info['height']}")
        else:
            logger.debug("未找到分辨率信息")
        
        # 解析帧率
        fps_match = re.search(r'(\d+(?:\.\d+)?) fps', stderr)
        if fps_match:
            info['fps'] = float(fps_match.group(1))
            logger.debug(f"解析到帧率: {info['fps']} fps")
        else:
            logger.debug("未找到帧率信息")
        
        # 解析视频编码
        codec_match = re.search(r'Video: (\w+)', stderr)
        if codec_match:
            info['codec'] = codec_match.group(1)
            logger.debug(f"解析到编码: {info['codec']}")
        else:
            logger.debug("未找到编码信息")
        
        if info:
            logger.info(f"成功获取视频信息: {info}")
            return info
        else:
            logger.warning(f"未能从 FFmpeg 输出中解析到任何信息。输出前 500 字符:\n{stderr[:500]}")
            return None
        
    except Exception as e:
        logger.error(f"获取视频信息失败: {e}", exc_info=True)
        return None


def build_ffmpeg_command(
    input_path: str,
    output_pattern: str,
    output_format: str = 'png',
    quality: int = 95,
    frame_rate: Optional[float] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    scale: Optional[str] = None,
    crop: Optional[str] = None,
    grayscale: bool = False,
    ffmpeg_path: str = 'ffmpeg'
) -> List[str]:
    """构建 FFmpeg 命令"""
    cmd = [ffmpeg_path, '-i', input_path]
    
    # 时间范围
    if start_time:
        cmd.extend(['-ss', start_time])
    if end_time:
        cmd.extend(['-to', end_time])
    
    # 视频滤镜
    filters = []
    
    if frame_rate:
        filters.append(f'fps={frame_rate}')
    
    if crop:
        filters.append(f'crop={crop}')
    
    if scale:
        filters.append(f'scale={scale}')
    
    if grayscale:
        filters.append('format=gray')
    
    if filters:
        cmd.extend(['-vf', ','.join(filters)])
    
    # 输出格式和质量
    if output_format.lower() in ['jpg', 'jpeg']:
        cmd.extend(['-q:v', str(max(1, min(31, 32 - quality // 3)))])  # JPEG 质量 1-31，数值越小质量越好
    else:
        cmd.extend(['-q:v', str(quality)])  # PNG/WebP 质量 0-100
    
    cmd.append(output_pattern)
    
    return cmd


class FFmpegProgressTracker:
    """FFmpeg 进度追踪器"""
    
    def __init__(self, total_duration: float, progress_callback: Callable[[int], None]):
        self.total_duration = total_duration
        self.progress_callback = progress_callback
        self.current_progress = 0
        
        # FFmpeg 进度输出格式: frame=  123 fps= 45 q=0.0 size=    1024kB time=00:00:05.00 bitrate= 1000.0kbits/s speed= 2.0x
        self.time_pattern = re.compile(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})')
    
    def parse_progress(self, line: str):
        """解析 FFmpeg 输出中的进度信息"""
        if 'time=' in line:
            match = self.time_pattern.search(line)
            if match:
                hours, minutes, seconds = match.groups()
                current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                
                if self.total_duration > 0:
                    progress = int((current_time / self.total_duration) * 100)
                    progress = min(100, max(0, progress))
                    
                    if progress != self.current_progress:
                        self.current_progress = progress
                        if self.progress_callback:
                            self.progress_callback(progress)


def run_ffmpeg_command(
    cmd: List[str],
    total_duration: float = 0,
    progress_callback: Callable[[int], None] = None,
    logger_callback: Callable[[str], None] = None
) -> Tuple[bool, str]:
    """执行 FFmpeg 命令并追踪进度"""
    try:
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        progress_tracker = FFmpegProgressTracker(total_duration, progress_callback)
        
        # 读取 stderr 输出（FFmpeg 进度信息输出到 stderr）
        while True:
            line = process.stderr.readline()
            if not line:
                break
            
            if logger_callback:
                logger_callback(line.strip())
            
            if progress_callback:
                progress_tracker.parse_progress(line)
        
        process.wait()
        
        if process.returncode == 0:
            logger.info("FFmpeg 执行成功")
            return True, "转换成功"
        else:
            error_output = process.stderr.read()
            logger.error(f"FFmpeg 执行失败: {error_output}")
            return False, f"转换失败: {error_output}"
    
    except Exception as e:
        logger.error(f"执行 FFmpeg 命令时出错: {e}")
        return False, str(e)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        print(f"找到 FFmpeg: {ffmpeg}")
    else:
        print("未找到 FFmpeg")
