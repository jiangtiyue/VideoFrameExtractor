"""自定义组件模块 - 可复用的 UI 组件"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, 
    QSpinBox, QComboBox, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LabeledSlider(QWidget):
    """带标签的滑块组件"""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, label: str, min_val: int, max_val: int, default_val: int, parent=None):
        super().__init__(parent)
        self.label = label
        self._setup_ui(min_val, max_val, default_val)
    
    def _setup_ui(self, min_val: int, max_val: int, default_val: int):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签和值显示
        header_layout = QHBoxLayout()
        self.label_widget = QLabel(self.label)
        self.value_label = QLabel(str(default_val))
        self.value_label.setMinimumWidth(30)
        
        header_layout.addWidget(self.label_widget)
        header_layout.addStretch()
        header_layout.addWidget(self.value_label)
        
        layout.addLayout(header_layout)
        
        # 滑块
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        self.slider.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(self.slider)
    
    def _on_value_changed(self, value: int):
        """值改变处理"""
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)
    
    def value(self) -> int:
        """获取当前值"""
        return self.slider.value()
    
    def setValue(self, value: int):
        """设置值"""
        self.slider.setValue(value)


class QualitySelector(QWidget):
    """质量选择器组件"""
    
    qualityChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("质量:"))
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(95)
        self.slider.setMinimumWidth(150)
        self.slider.valueChanged.connect(self._on_quality_changed)
        
        self.value_label = QLabel("95")
        self.value_label.setMinimumWidth(30)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def _on_quality_changed(self, value: int):
        """质量值改变"""
        self.value_label.setText(str(value))
        self.qualityChanged.emit(value)
    
    def get_quality(self) -> int:
        """获取当前质量值"""
        return self.slider.value()
    
    def set_quality(self, value: int):
        """设置质量值"""
        self.slider.setValue(value)


class FrameRateSelector(QWidget):
    """帧率选择器组件"""
    
    frameRateChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("抽帧率:"))
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0.1, 60.0)
        self.spinbox.setValue(1.0)
        self.spinbox.setSingleStep(0.1)
        self.spinbox.setSuffix(" fps")
        self.spinbox.valueChanged.connect(self._on_frame_rate_changed)
        
        layout.addWidget(self.spinbox)
        layout.addStretch()
    
    def _on_frame_rate_changed(self, value: float):
        """帧率改变"""
        self.frameRateChanged.emit(value)
    
    def get_frame_rate(self) -> float:
        """获取当前帧率"""
        return self.spinbox.value()
    
    def set_frame_rate(self, value: float):
        """设置帧率"""
        self.spinbox.setValue(value)


class OutputFormatSelector(QWidget):
    """输出格式选择器组件"""
    
    formatChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("输出格式:"))
        
        self.combo = QComboBox()
        self.combo.addItems(["PNG", "JPG", "WebP"])
        self.combo.currentTextChanged.connect(self._on_format_changed)
        
        layout.addWidget(self.combo)
        layout.addStretch()
    
    def _on_format_changed(self, text: str):
        """格式改变"""
        self.formatChanged.emit(text.lower())
    
    def get_format(self) -> str:
        """获取当前格式"""
        return self.combo.currentText().lower()
    
    def set_format(self, fmt: str):
        """设置格式"""
        index = self.combo.findText(fmt.upper())
        if index >= 0:
            self.combo.setCurrentIndex(index)


class HSeparator(QFrame):
    """水平分隔线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class VSeparator(QFrame):
    """垂直分隔线"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class ToggleButton(QPushButton):
    """切换按钮（开始/停止）"""
    
    def __init__(self, parent=None):
        super().__init__("开始", parent)
        self._is_active = False
        self._setup_styles()
    
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton[active="true"] {
                background-color: #f44336;
            }
            QPushButton[active="true"]:hover {
                background-color: #da190b;
            }
            QPushButton[active="true"]:pressed {
                background-color: #c41e3a;
            }
        """)
    
    def set_active(self, active: bool):
        """设置激活状态"""
        self._is_active = active
        self.setProperty("active", active)
        self.setText("停止" if active else "开始")
        self.style().unpolish(self)
        self.style().polish(self)
    
    def is_active(self) -> bool:
        """获取激活状态"""
        return self._is_active


class StatusWidget(QWidget):
    """状态显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("就绪")
        self.status_label.setMinimumWidth(100)
        
        self.progress_label = QLabel("")
        self.progress_label.setMinimumWidth(80)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.progress_label)
    
    def set_status(self, status: str):
        """设置状态文本"""
        self.status_label.setText(status)
    
    def set_progress(self, progress: int):
        """设置进度文本"""
        self.progress_label.setText(f"{progress}%")
    
    def clear_progress(self):
        """清除进度文本"""
        self.progress_label.setText("")
