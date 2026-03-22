"""工作线程模块 - 在 QThread 中执行视频转换任务"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal
import logging

from . import ffmpeg_utils
from . import image_proc

logger = logging.getLogger(__name__)


class ConvertTask:
    """转换任务配置类"""
    
    def __init__(
        self,
        video_path: str,
        output_dir: str,
        output_format: str = 'png',
        quality: int = 95,
        frame_rate: Optional[float] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        scale: Optional[tuple] = None,
        crop: Optional[tuple] = None,
        grayscale: bool = False,
        skip_black: bool = False,
        skip_blurry: bool = False,
        use_opencv: bool = False  # True=精细处理模式, False=高速直通模式
    ):
        self.video_path = video_path
        self.output_dir = output_dir
        self.output_format = output_format
        self.quality = quality
        self.frame_rate = frame_rate
        self.start_time = start_time
        self.end_time = end_time
        self.scale = scale
        self.crop = crop
        self.grayscale = grayscale
        self.skip_black = skip_black
        self.skip_blurry = skip_blurry
        self.use_opencv = use_opencv
        
        # 生成输出文件名模板
        filename = Path(video_path).stem
        self.output_pattern = str(Path(output_dir) / f"{filename}_%04d.{output_format}")


class ConvertWorker(QThread):
    """转换工作线程 - 在后台执行视频转换任务"""
    
    # 定义信号
    progress_updated = pyqtSignal(int)  # 进度更新 (0-100)
    status_updated = pyqtSignal(str)    # 状态消息
    task_finished = pyqtSignal(bool, str)  # 任务完成 (是否成功, 消息)
    log_message = pyqtSignal(str)       # 日志消息
    
    def __init__(self, task: ConvertTask):
        super().__init__()
        self.task = task
        self.ffmpeg_path = None
        self.is_running = True
        
    def run(self):
        """线程主函数 - 执行转换任务"""
        try:
            # 查找 FFmpeg
            self.ffmpeg_path = ffmpeg_utils.find_ffmpeg()
            if not self.ffmpeg_path:
                self.task_finished.emit(False, "未找到 FFmpeg 可执行文件")
                return
            
            # 创建输出目录
            os.makedirs(self.task.output_dir, exist_ok=True)
            
            # 获取视频信息
            self.status_updated.emit("正在获取视频信息...")
            video_info = ffmpeg_utils.get_video_info(self.task.video_path, self.ffmpeg_path)
            
            if not video_info:
                self.task_finished.emit(False, "无法获取视频信息")
                return
            
            duration = video_info.get('duration', 0)
            self.log_message.emit(f"视频信息: {video_info}")
            
            # 选择处理模式
            if self.task.use_opencv:
                success, message = self._run_opencv_mode()
            else:
                success, message = self._run_ffmpeg_mode(duration)
            
            if success:
                self.status_updated.emit("转换完成")
            else:
                self.status_updated.emit("转换失败")
            
            self.task_finished.emit(success, message)
            
        except Exception as e:
            logger.error(f"转换任务异常: {e}")
            self.status_updated.emit("转换异常")
            self.task_finished.emit(False, f"异常: {str(e)}")
    
    def _run_ffmpeg_mode(self, duration: float) -> tuple:
        """高速直通模式 - 直接调用 FFmpeg"""
        self.status_updated.emit("正在使用 FFmpeg 高速模式转换...")
        
        # 构建 FFmpeg 命令
        # 将时间从秒转换为 HH:MM:SS 格式
        start_time_str = None
        end_time_str = None
        
        if self.task.start_time:
            hours = int(self.task.start_time // 3600)
            minutes = int((self.task.start_time % 3600) // 60)
            seconds = self.task.start_time % 60
            start_time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        if self.task.end_time:
            hours = int(self.task.end_time // 3600)
            minutes = int((self.task.end_time % 3600) // 60)
            seconds = self.task.end_time % 60
            end_time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        # 构建视频滤镜
        vf_filters = []
        if self.task.frame_rate:
            vf_filters.append(f"fps={self.task.frame_rate}")
        
        if self.task.crop:
            x, y, w, h = self.task.crop
            vf_filters.append(f"crop={w}:{h}:{x}:{y}")
        
        if self.task.scale:
            w, h = self.task.scale
            vf_filters.append(f"scale={w}:{h}")
        
        if self.task.grayscale:
            vf_filters.append("format=gray")
        
        vf_str = ",".join(vf_filters) if vf_filters else None
        
        cmd = [
            self.ffmpeg_path,
            '-i', self.task.video_path
        ]
        
        if start_time_str:
            cmd.extend(['-ss', start_time_str])
        
        if end_time_str:
            cmd.extend(['-to', end_time_str])
        
        if vf_str:
            cmd.extend(['-vf', vf_str])
        
        # 质量参数
        if self.task.output_format.lower() in ['jpg', 'jpeg']:
            # JPEG: 1-31, 数值越小质量越好
            quality = max(1, min(31, 32 - self.task.quality // 3))
            cmd.extend(['-q:v', str(quality)])
        else:
            # PNG/WebP: 0-100
            cmd.extend(['-q:v', str(self.task.quality)])
        
        cmd.append(self.task.output_pattern)
        
        self.log_message.emit(f"FFmpeg 命令: {' '.join(cmd)}")
        
        # 执行命令
        def progress_callback(progress):
            self.progress_updated.emit(progress)
        
        def log_callback(message):
            self.log_message.emit(message)
        
        success, message = ffmpeg_utils.run_ffmpeg_command(
            cmd, duration, progress_callback, log_callback
        )
        
        return success, message
    
    def _run_opencv_mode(self) -> tuple:
        """精细处理模式 - 使用 OpenCV 逐帧处理"""
        self.status_updated.emit("正在使用 OpenCV 精细模式转换...")
        
        try:
            # 创建提取器
            extractor = image_proc.VideoFrameExtractor(self.task.video_path)
            
            # 执行提取
            def progress_callback(progress):
                self.progress_updated.emit(progress)
            
            success, message = extractor.extract_frames(
                output_pattern=self.task.output_pattern,
                frame_rate=self.task.frame_rate,
                start_time=self.task.start_time or 0,
                end_time=self.task.end_time,
                scale=self.task.scale,
                crop=self.task.crop,
                grayscale=self.task.grayscale,
                skip_black=self.task.skip_black,
                skip_blurry=self.task.skip_blurry,
                quality=self.task.quality,
                progress_callback=progress_callback
            )
            
            extractor.close()
            return success, message
            
        except Exception as e:
            logger.error(f"OpenCV 模式失败: {e}")
            return False, f"OpenCV 处理失败: {str(e)}"
    
    def stop(self):
        """停止任务"""
        self.is_running = False
        self.status_updated.emit("正在停止任务...")


class BatchConvertWorker(QThread):
    """批量转换工作线程 - 处理多个视频文件"""
    
    task_started = pyqtSignal(str)      # 任务开始 (视频路径)
    task_progress = pyqtSignal(str, int) # 任务进度 (视频路径, 进度)
    task_finished = pyqtSignal(str, bool, str)  # 任务完成 (视频路径, 是否成功, 消息)
    overall_progress = pyqtSignal(int)   # 总体进度
    
    def __init__(self, tasks: list):
        super().__init__()
        self.tasks = tasks
        self.is_running = True
    
    def run(self):
        """执行批量转换"""
        total_tasks = len(self.tasks)
        completed_tasks = 0
        
        for i, task in enumerate(self.tasks):
            if not self.is_running:
                break
            
            video_path = task.video_path
            self.task_started.emit(video_path)
            
            # 创建单个任务工作线程
            worker = ConvertWorker(task)
            
            # 连接信号（使用局部函数捕获当前任务）
            def make_progress_handler(path):
                def handler(progress):
                    self.task_progress.emit(path, progress)
                return handler
            
            def make_finish_handler(path):
                def handler(success, message):
                    nonlocal completed_tasks
                    completed_tasks += 1
                    self.task_finished.emit(path, success, message)
                    
                    # 更新总体进度
                    overall_progress = int((completed_tasks / total_tasks) * 100)
                    self.overall_progress.emit(overall_progress)
                return handler
            
            worker.progress_updated.connect(make_progress_handler(video_path))
            worker.task_finished.connect(make_finish_handler(video_path))
            
            # 执行转换
            worker.run()  # 直接调用，不启动新线程
            
            # 清理
            worker.deleteLater()
    
    def stop(self):
        """停止所有任务"""
        self.is_running = False


if __name__ == '__main__':
    # 测试代码
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建测试任务
    if len(sys.argv) < 2:
        print("用法: python worker.py <视频路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = "output_test"
    
    task = ConvertTask(
        video_path=video_path,
        output_dir=output_dir,
        output_format='png',
        frame_rate=1.0,  # 每秒1帧
        use_opencv=False  # 使用 FFmpeg 高速模式
    )
    
    worker = ConvertWorker(task)
    
    def on_progress(p):
        print(f"\r进度: {p}%", end='', flush=True)
    
    def on_status(s):
        print(f"\n状态: {s}")
    
    def on_finish(success, msg):
        print(f"\n{'成功' if success else '失败'}: {msg}")
        app.quit()
    
    def on_log(msg):
        if 'frame=' in msg:
            print(f"\rFFmpeg: {msg[:80]}", end='', flush=True)
    
    worker.progress_updated.connect(on_progress)
    worker.status_updated.connect(on_status)
    worker.task_finished.connect(on_finish)
    worker.log_message.connect(on_log)
    
    worker.start()
    sys.exit(app.exec())