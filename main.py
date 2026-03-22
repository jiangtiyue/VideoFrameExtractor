"""VideoFrameExtractor 主入口文件"""

import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

try:
    from ui.main_window import MainWindow
except ImportError:
    # 处理直接运行的情况
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ui.main_window import MainWindow


def setup_logging():
    """设置日志系统"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志
    log_file = log_dir / "videoframeextractor.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("VideoFrameExtractor 启动")
    logger.info("=" * 60)
    
    return logger


def load_stylesheet(app: QApplication):
    """加载样式表"""
    style_file = Path("ui/styles.qss")
    
    if style_file.exists():
        try:
            with open(style_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                app.setStyleSheet(stylesheet)
                logging.getLogger(__name__).info("样式表加载成功")
        except Exception as e:
            logging.getLogger(__name__).warning(f"加载样式表失败: {e}")
    else:
        logging.getLogger(__name__).warning("样式表文件不存在，使用默认样式")


def check_ffmpeg():
    """检查 FFmpeg 可用性"""
    from core.ffmpeg_utils import find_ffmpeg
    
    ffmpeg_path = find_ffmpeg()
    logger = logging.getLogger(__name__)
    
    if ffmpeg_path:
        logger.info(f"FFmpeg 可用: {ffmpeg_path}")
        return True
    else:
        logger.error("未找到 FFmpeg，请确保 FFmpeg 已安装或在资源目录中")
        return False


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    
    # 检查 FFmpeg
    if not check_ffmpeg():
        # 不退出，让用户有机会手动指定路径
        logger.warning("FFmpeg 未找到，但程序仍将继续启动")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("VideoFrameExtractor")
    app.setOrganizationName("VideoFrameExtractor")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 加载自定义样式
    load_stylesheet(app)
    
    # 创建并显示主窗口
    window = MainWindow()
    
    # 设置窗口图标（如果有的话）
    icon_path = Path("resources/icon.png")
    if icon_path.exists():
        from PyQt6.QtGui import QIcon
        window.setWindowIcon(QIcon(str(icon_path)))
    
    window.show()
    
    # 处理命令行参数（如果有视频文件路径）
    if len(sys.argv) > 1:
        video_files = []
        for arg in sys.argv[1:]:
            path = Path(arg)
            if path.exists() and path.is_file():
                video_files.append(str(path))
        
        if video_files:
            # 延迟添加文件，确保窗口已完全显示
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: window._add_video_files(video_files))
    
    logger.info("主窗口已显示，进入事件循环")
    
    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
