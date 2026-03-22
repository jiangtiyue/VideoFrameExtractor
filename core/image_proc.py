"""图像处理模块 - 使用 OpenCV 进行帧处理和智能过滤"""

import cv2
import numpy as np
from typing import Tuple, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class FrameProcessor:
    """帧处理器 - 对单帧图像进行处理"""
    
    def __init__(self):
        self.black_threshold = 30  # 黑屏检测阈值
        self.blur_threshold = 100   # 模糊检测阈值
    
    def is_black_frame(self, frame: np.ndarray, threshold: int = None) -> bool:
        """
        检测是否为黑屏帧
        
        Args:
            frame: BGR格式的图像数组
            threshold: 亮度阈值，平均亮度低于此值认为是黑屏
        
        Returns:
            bool: 是否为黑屏
        """
        if threshold is None:
            threshold = self.black_threshold
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算平均亮度
        mean_brightness = np.mean(gray)
        
        return mean_brightness < threshold
    
    def is_blurry_frame(self, frame: np.ndarray, threshold: int = None) -> bool:
        """
        检测是否为模糊帧（基于拉普拉斯方差）
        
        Args:
            frame: BGR格式的图像数组
            threshold: 模糊阈值，方差低于此值认为是模糊
        
        Returns:
            bool: 是否模糊
        """
        if threshold is None:
            threshold = self.blur_threshold
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算拉普拉斯方差
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        return laplacian_var < threshold
    
    def preprocess_frame(
        self, 
        frame: np.ndarray,
        scale: Optional[Tuple[int, int]] = None,
        crop: Optional[Tuple[int, int, int, int]] = None,
        grayscale: bool = False,
        auto_rotate: bool = False
    ) -> np.ndarray:
        """
        预处理帧
        
        Args:
            frame: 输入帧
            scale: (width, height) 缩放尺寸
            crop: (x, y, w, h) 裁剪区域
            grayscale: 是否转为灰度图
            auto_rotate: 是否自动旋转（需要EXIF信息，视频帧通常不需要）
        
        Returns:
            np.ndarray: 处理后的帧
        """
        processed = frame.copy()
        
        # 裁剪
        if crop:
            x, y, w, h = crop
            h_orig, w_orig = processed.shape[:2]
            # 确保裁剪区域在图像范围内
            x = max(0, min(x, w_orig - 1))
            y = max(0, min(y, h_orig - 1))
            w = max(1, min(w, w_orig - x))
            h = max(1, min(h, h_orig - y))
            processed = processed[y:y+h, x:x+w]
        
        # 缩放
        if scale:
            target_w, target_h = scale
            processed = cv2.resize(processed, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        # 灰度化
        if grayscale:
            if len(processed.shape) == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)  # 保持3通道以便统一保存
        
        return processed


class VideoFrameExtractor:
    """视频帧提取器 - 使用 OpenCV 逐帧读取和处理"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.frame_processor = FrameProcessor()
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        self._open_video()
    
    def _open_video(self):
        """打开视频文件"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件: {self.video_path}")
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        logger.info(f"视频打开成功: {self.video_path}, 总帧数: {self.total_frames}, FPS: {self.fps}")
    
    def extract_frames(
        self,
        output_pattern: str,
        frame_rate: Optional[float] = None,
        start_time: float = 0,
        end_time: Optional[float] = None,
        scale: Optional[Tuple[int, int]] = None,
        crop: Optional[Tuple[int, int, int, int]] = None,
        grayscale: bool = False,
        skip_black: bool = False,
        skip_blurry: bool = False,
        quality: int = 95,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[bool, str]:
        """
        提取帧并保存
        
        Args:
            output_pattern: 输出文件名模板，如 output_%04d.png
            frame_rate: 目标帧率，None 表示使用原始帧率
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），None 表示到视频结尾
            scale: 缩放尺寸 (width, height)
            crop: 裁剪区域 (x, y, w, h)
            grayscale: 是否灰度化
            skip_black: 是否跳过黑屏帧
            skip_blurry: 是否跳过模糊帧
            quality: 图像质量（JPEG: 0-100，PNG: 压缩级别）
            progress_callback: 进度回调函数
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 计算帧间隔
            if frame_rate and self.fps > 0:
                frame_interval = int(self.fps / frame_rate)
                frame_interval = max(1, frame_interval)
            else:
                frame_interval = 1
            
            # 计算起始和结束帧
            start_frame = int(start_time * self.fps)
            end_frame = self.total_frames
            if end_time:
                end_frame = min(end_frame, int(end_time * self.fps))
            
            # 跳转到起始帧
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = 0
            saved_count = 0
            current_frame = start_frame
            
            while current_frame < end_frame:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # 只处理指定间隔的帧
                if frame_count % frame_interval == 0:
                    # 预处理
                    processed_frame = self.frame_processor.preprocess_frame(
                        frame, scale=scale, crop=crop, grayscale=grayscale
                    )
                    
                    # 智能过滤
                    should_skip = False
                    if skip_black and self.frame_processor.is_black_frame(processed_frame):
                        should_skip = True
                    
                    if skip_blurry and self.frame_processor.is_blurry_frame(processed_frame):
                        should_skip = True
                    
                    if not should_skip:
                        # 保存帧
                        output_path = output_pattern % saved_count
                        if output_pattern.endswith(('.jpg', '.jpeg')):
                            cv2.imwrite(output_path, processed_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        elif output_pattern.endswith('.png'):
                            cv2.imwrite(output_path, processed_frame, [cv2.IMWRITE_PNG_COMPRESSION, int((100 - quality) / 10)])
                        else:
                            cv2.imwrite(output_path, processed_frame)
                        
                        saved_count += 1
                
                frame_count += 1
                current_frame += 1
                
                # 进度回调
                if progress_callback and frame_count % 30 == 0:  # 每30帧更新一次，避免过于频繁
                    progress = int((current_frame - start_frame) / (end_frame - start_frame) * 100)
                    progress_callback(min(100, progress))
            
            logger.info(f"帧提取完成: 共处理 {frame_count} 帧，保存 {saved_count} 帧")
            return True, f"成功提取 {saved_count} 帧"
        
        except Exception as e:
            logger.error(f"帧提取失败: {e}")
            return False, str(e)
    
    def close(self):
        """关闭视频文件"""
        if self.cap:
            self.cap.release()
            logger.info("视频文件已关闭")


if __name__ == '__main__':
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python image_proc.py <视频路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    try:
        extractor = VideoFrameExtractor(video_path)
        print(f"视频信息: 总帧数={extractor.total_frames}, FPS={extractor.fps:.2f}, 时长={extractor.duration:.2f}s")
        
        def progress_callback(progress):
            print(f"\r进度: {progress}%", end='', flush=True)
        
        output_pattern = "test_frame_%04d.png"
        success, msg = extractor.extract_frames(
            output_pattern=output_pattern,
            frame_rate=1,  # 每秒1帧
            progress_callback=progress_callback
        )
        print(f"\n{msg}")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'extractor' in locals():
            extractor.close()
