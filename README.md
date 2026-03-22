# VideoFrameExtractor

一款基于 Python + FFmpeg 的 Windows 桌面工具，用于将视频高效转换为图片序列。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-6.0%2B-red)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-orange)

## ✨ 功能特性

- 🎬 **支持多种视频格式**：MP4, AVI, MKV, MOV, FLV, WMV 等
- 🖼️ **多种输出格式**：PNG, JPG, WebP
- ⚡ **双模式转换**：
  - **高速直通模式**：直接调用 FFmpeg，速度最快
  - **精细处理模式**：使用 OpenCV 逐帧处理，支持智能过滤
- 🎯 **智能过滤**：自动跳过黑屏帧和模糊帧
- 📊 **批量处理**：支持同时处理多个视频文件
- 🎨 **现代化界面**：基于 PyQt6 的图形化界面，支持拖拽操作
- 📈 **实时进度**：显示转换进度和剩余时间
- ⚙️ **灵活配置**：可调节图像质量、抽帧率、时间范围等

## 🚀 快速开始

### 环境要求

- Python 3.9 或更高版本
- FFmpeg（目前未捆绑在源码中，但Releases中包含）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 使用步骤

1. **添加视频文件**：
   - 拖拽视频文件到程序窗口
   - 或点击"添加视频"按钮选择文件

2. **设置转换参数**：
   - 选择输出格式（PNG/JPG/WebP）
   - 调整图像质量（1-100）
   - 设置抽帧率（每秒提取多少帧）
   - 可选：启用 OpenCV 精细模式进行智能过滤

3. **开始转换**：
   - 点击"开始转换"按钮
   - 等待转换完成

4. **查看结果**：
   - 转换完成后，图片保存在视频同目录下的 `_frames` 文件夹中

## 📁 项目结构

```
VideoFrameExtractor/
├── core/                    # 核心模块
│   ├── ffmpeg_utils.py     # FFmpeg 工具模块
│   ├── image_proc.py       # OpenCV 图像处理模块
│   └── worker.py           # 多线程工作模块
├── ui/                      # UI 模块
│   ├── main_window.py      # 主窗口
│   ├── widgets.py          # 自定义组件
│   └── styles.qss          # 样式表
├── resources/               # 资源文件
│   └── ffmpeg.exe          # FFmpeg 可执行文件（Windows）
├── main.py                  # 程序入口
├── requirements.txt         # Python 依赖
├── README.md               # 项目说明
└── LICENSE                 # 许可证
```

## 🛠️ 技术栈

| 模块 | 技术 | 说明 |
| :--- | :--- | :--- |
| **GUI 框架** | PyQt6 | Windows 图形界面框架 |
| **视频处理** | FFmpeg | 高性能视频编解码 |
| **图像处理** | OpenCV | 图像预处理与智能分析 |
| **并发处理** | QThread | 防止界面卡顿 |
| **配置管理** | JSON | 保存用户设置 |

## 🔧 高级功能

### 智能过滤

启用 OpenCV 精细模式后，可以：

- **跳过黑屏帧**：自动检测并跳过全黑或接近全黑的画面
- **跳过模糊帧**：基于拉普拉斯方差检测模糊图像

### 自定义输出

- **时间范围**：只转换视频的指定片段
- **图像尺寸**：缩放或裁剪输出图片
- **灰度模式**：转换为黑白图像

## 📦 打包发布

使用 PyInstaller 创建独立可执行文件：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "resources;resources" --add-data "ui/styles.qss;ui" main.py
```

## 🐛 常见问题

### Q: 程序无法读取视频信息？

A: 确保 `resources/ffmpeg.exe` 文件完整（大小约 120-150MB）。如果文件损坏，请重新下载。

### Q: 转换速度慢？

A: 
- 使用默认的 FFmpeg 高速模式（不启用 OpenCV 精细模式）
- 降低抽帧率（fps）
- 使用 JPG 格式代替 PNG 以提高速度

### Q: 支持哪些视频格式？

A: 支持所有 FFmpeg 支持的格式，包括 MP4, AVI, MKV, MOV, FLV, WMV 等。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 Apache 2.0 许可证开源 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FFmpeg](https://ffmpeg.org/) - 强大的多媒体框架
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - Python 的 Qt 绑定
- [OpenCV](https://opencv.org/) - 计算机视觉库

## 📧 联系

如有问题或建议，欢迎提交 Issue，或者在我的博客中评论。
博客：https://www.jiangxiubai.me/

---

**Made with ❤️ and Python**
