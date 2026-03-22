"""主窗口模块 - PyQt6 主界面"""

import sys
import os
from pathlib import Path
from typing import List, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QLabel,
    QProgressBar, QStatusBar, QFileDialog, QMessageBox,
    QCheckBox, QSlider, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.worker import ConvertTask, BatchConvertWorker
from core import ffmpeg_utils


class VideoListTable(QTableWidget):
    """视频文件列表表格"""
    
    def __init__(self):
        super().__init__(0, 5)  # 行数动态，5列
        self._setup_ui()
        self.video_files: List[Dict] = []
    
    def _setup_ui(self):
        """设置表格UI"""
        headers = ["文件名", "时长", "分辨率", "状态", "输出目录"]
        self.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 时长
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 分辨率
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 输出目录
        
        # 设置选择行为
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    
    def add_video(self, file_path: str, output_dir: str = ""):
        """添加视频文件到列表"""
        if file_path in [f['path'] for f in self.video_files]:
            return  # 已存在
        
        # 获取视频信息
        video_info = ffmpeg_utils.get_video_info(file_path)
        
        file_name = Path(file_path).name
        duration = "未知"
        resolution = "未知"
        
        if video_info:
            if 'duration' in video_info:
                dur = video_info['duration']
                hours = int(dur // 3600)
                minutes = int((dur % 3600) // 60)
                seconds = int(dur % 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            if 'width' in video_info and 'height' in video_info:
                resolution = f"{video_info['width']}x{video_info['height']}"
        else:
            # 显示警告
            self.status_bar.showMessage(f"警告: 无法读取 {file_name} 的视频信息", 5000)
        
        # 添加到列表
        self.video_files.append({
            'path': file_path,
            'output_dir': output_dir or str(Path(file_path).parent / f"{Path(file_path).stem}_frames"),
            'info': video_info
        })
        
        # 添加到表格
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(file_name))
        self.setItem(row, 1, QTableWidgetItem(duration))
        self.setItem(row, 2, QTableWidgetItem(resolution))
        self.setItem(row, 3, QTableWidgetItem("等待"))
        self.setItem(row, 4, QTableWidgetItem(self.video_files[-1]['output_dir']))
    
    def remove_selected(self):
        """移除选中的视频"""
        selected_rows = sorted(set(item.row() for item in self.selectedItems()), reverse=True)
        for row in selected_rows:
            self.removeRow(row)
            del self.video_files[row]
    
    def clear_all(self):
        """清空所有视频"""
        self.setRowCount(0)
        self.video_files.clear()
    
    def update_status(self, row: int, status: str):
        """更新状态"""
        self.setItem(row, 3, QTableWidgetItem(status))
    
    def get_all_tasks(self, global_settings: dict) -> List[ConvertTask]:
        """获取所有转换任务"""
        tasks = []
        for i, video in enumerate(self.video_files):
            task = ConvertTask(
                video_path=video['path'],
                output_dir=video['output_dir'],
                output_format=global_settings['format'],
                quality=global_settings['quality'],
                frame_rate=global_settings['frame_rate'],
                use_opencv=global_settings['use_opencv']
            )
            tasks.append(task)
        return tasks


class DragDropFrame(QFrame):
    """拖拽区域框架"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("拖拽视频文件到此处\n或点击添加按钮")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; color: #666;")
        
        layout.addWidget(self.label)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoFrameExtractor - 视频转图片工具")
        self.setMinimumSize(900, 600)
        
        self.worker = None
        self.is_converting = False
        
        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
    
    def _setup_ui(self):
        """设置主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 拖拽区域
        self.drag_frame = DragDropFrame()
        self.drag_frame.setMaximumHeight(100)
        main_layout.addWidget(self.drag_frame)
        
        # 文件列表
        self.video_table = VideoListTable()
        main_layout.addWidget(self.video_table)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加视频")
        self.remove_btn = QPushButton("移除选中")
        self.clear_btn = QPushButton("清空列表")
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        main_layout.addLayout(btn_layout)
        
        # 设置区域
        settings_group = QGroupBox("转换设置")
        settings_layout = QGridLayout()
        
        # 输出格式
        settings_layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WebP"])
        settings_layout.addWidget(self.format_combo, 0, 1)
        
        # 图像质量
        settings_layout.addWidget(QLabel("图像质量:"), 0, 2)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(95)
        self.quality_label = QLabel("95")
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_label)
        settings_layout.addLayout(quality_layout, 0, 3)
        
        # 抽帧率
        settings_layout.addWidget(QLabel("抽帧率:"), 1, 0)
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setRange(0.1, 60.0)
        self.fps_spin.setValue(1.0)
        self.fps_spin.setSuffix(" fps")
        settings_layout.addWidget(self.fps_spin, 1, 1)
        
        # 使用 OpenCV 精细模式
        self.opencv_check = QCheckBox("使用 OpenCV 精细模式（支持智能过滤）")
        settings_layout.addWidget(self.opencv_check, 1, 2, 1, 2)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 转换按钮和进度条
        convert_layout = QHBoxLayout()
        
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        
        convert_layout.addWidget(self.convert_btn)
        convert_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(convert_layout)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_action = file_menu.addAction("添加视频")
        add_action.triggered.connect(self._add_videos)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self._show_about)
    
    def _setup_connections(self):
        """设置信号连接"""
        self.add_btn.clicked.connect(self._add_videos)
        self.remove_btn.clicked.connect(self.video_table.remove_selected)
        self.clear_btn.clicked.connect(self.video_table.clear_all)
        self.convert_btn.clicked.connect(self._toggle_conversion)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        
        if files:
            self._add_video_files(files)
    
    def _add_videos(self):
        """添加视频文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.flv *.wmv);;所有文件 (*.*)"
        )
        
        if files:
            self._add_video_files(files)
    
    def _add_video_files(self, file_paths: List[str]):
        """添加视频文件到列表"""
        for file_path in file_paths:
            self.video_table.add_video(file_path)
        
        self.status_bar.showMessage(f"已添加 {len(file_paths)} 个视频文件")
    
    def _toggle_conversion(self):
        """切换转换状态"""
        if self.is_converting:
            self._stop_conversion()
        else:
            self._start_conversion()
    
    def _start_conversion(self):
        """开始转换"""
        if not self.video_table.video_files:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return
        
        # 获取全局设置
        global_settings = {
            'format': self.format_combo.currentText().lower(),
            'quality': self.quality_slider.value(),
            'frame_rate': self.fps_spin.value(),
            'use_opencv': self.opencv_check.isChecked()
        }
        
        # 获取所有任务
        tasks = self.video_table.get_all_tasks(global_settings)
        if not tasks:
            return
        
        # 创建批量转换工作线程
        self.worker = BatchConvertWorker(tasks)
        
        # 连接信号
        self.worker.task_started.connect(self._on_task_started)
        self.worker.task_progress.connect(self._on_task_progress)
        self.worker.task_finished.connect(self._on_task_finished)
        self.worker.overall_progress.connect(self._on_overall_progress)
        
        # 更新UI
        self.is_converting = True
        self.convert_btn.setText("停止转换")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        self.status_bar.showMessage("正在转换...")
        
        # 启动转换
        self.worker.start()
    
    def _stop_conversion(self):
        """停止转换"""
        if self.worker:
            self.worker.stop()
            self.status_bar.showMessage("正在停止转换...")
    
    def _on_task_started(self, video_path: str):
        """任务开始"""
        file_name = Path(video_path).name
        self.status_bar.showMessage(f"正在转换: {file_name}")
        
        # 更新表格状态
        for i, video in enumerate(self.video_table.video_files):
            if video['path'] == video_path:
                self.video_table.update_status(i, "转换中...")
                break
    
    def _on_task_progress(self, video_path: str, progress: int):
        """任务进度更新"""
        self.progress_bar.setValue(progress)
    
    def _on_task_finished(self, video_path: str, success: bool, message: str):
        """任务完成"""
        # 更新表格状态
        for i, video in enumerate(self.video_table.video_files):
            if video['path'] == video_path:
                status = "完成" if success else "失败"
                self.video_table.update_status(i, status)
                break
        
        if not success:
            QMessageBox.warning(self, "转换警告", f"{Path(video_path).name}\n{message}")
    
    def _on_overall_progress(self, progress: int):
        """总体进度更新"""
        self.progress_bar.setValue(progress)
        
        if progress >= 100:
            self._on_all_tasks_finished()
    
    def _on_all_tasks_finished(self):
        """所有任务完成"""
        self.is_converting = False
        self.convert_btn.setText("开始转换")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        self.status_bar.showMessage("转换完成")
        QMessageBox.information(self, "完成", "所有视频转换完成！")
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 VideoFrameExtractor",
            "VideoFrameExtractor\n\n"
            "作者：江岫白\n\n"
            "博客：www.jiangxiubai.me\n\n"
            "软件版本: v1.0\n\n"
            "组件版本：Python(3.13) + FFmpeg(n8.0.1-76-gfa4ee7ab3c-win64-gpl-8.0)\n\n"
            "说明：一个基于 Python + FFmpeg 的视频转图片工具\n\n"
            "技术栈: PyQt6 + FFmpeg + OpenCV"
        )
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.is_converting:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "转换正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.worker:
                    self.worker.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
