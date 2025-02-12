<div align="center">
  <img src="image\Designer.jpeg" alt="Project Icon" width="200" height="200">
</div>

# MultiAnnEditor
多模态数据标签可视化， Multimodal annotation viewer/editor. Specialized for LLaMA-Factory. 
# News

2025/2/12 MultiAnnEditor Supports [_.exe_](https://github.com/likaiucas/MultiAnnEditor/blob/master/dist/annotation_editor.exe) for windows. 


# Image-Text Annotation Editor / 图片-文本标注编辑器



[English Version](#english-version) | [中文版](#中文说明)

---

## English Version

### Overview
Image-Text Annotation Editor is a GUI application built with Python and PyQt5 for browsing, editing, and visualizing annotation data stored in JSON format. The tool supports:
- **Image and Text Display:** View images and corresponding text annotations.
- **Multi-Format Image Support:** The `image` field may be a string or a list; users can easily switch between images.
- **Bounding Box Visualization:** Overlay bounding boxes in various formats (e.g., `cxcywh`, `xyxy`, `xywh` and their normalized versions). If multiple bounding boxes exist, navigation buttons allow switching between them.
- **Search Navigation:** A search bar lets you choose a key and input a value to jump to matching annotation records.
- **Layout Adjustment:** Resizable split views for image and text areas.
- **Language Switching:** Toggle between English and Chinese interfaces.
- **Additional Options:** Set an image prefix to recover image paths, define custom image fields, etc.
<div align="center">
  <img src="image\feature.png" alt="Project Feature" width="800" height="400">
</div>
### Features
- **Load JSON Annotations:** Easily open and browse JSON files containing annotations.
- **Edit Annotations:** Modify text fields and update annotation data on the fly.
- **Overlay Settings:** Configure how bounding boxes are displayed via the "Overlay Options" dock.
- **Search & Jump:** Use the top search bar to select a field, enter a value, and click "Go" to jump to a matching record.
- **Responsive UI:** Drag and adjust layout areas as needed.

### Installation
1. **Prerequisites:** Python 3.6 or higher.
2. **Install Dependencies:**
    ```bash
    pip install PyQt5
    ```
3. **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/annotation-editor.git
    cd annotation-editor
    ```
4. **Run the Application:**
    ```bash
    python annotation_editor.py
    ```

### Usage
- **Loading Annotations:** Open a JSON file via the "File" menu.
- **Editing & Navigation:** Edit text fields; use the "Previous"/"Next" buttons to switch records.
- **Overlay Settings:** Configure bounding box display in the "Overlay Options" dock.
- **Search:** Use the top search bar to select a field, enter a value, and click "Go" to jump to a matching record.
- **Language Switch:** Use the language buttons to toggle between English and Chinese.

### Contributing
Contributions are welcome! Please submit issues or pull requests for improvements.

### License
This project is licensed under the MIT License.

---

## 中文说明

### 概述
图片-文本标注编辑器是一个基于 Python 和 PyQt5 开发的图形界面应用，用于浏览、编辑和可视化存储在 JSON 格式中的标注数据。该软件支持：
- **图片与文本显示：** 显示图片及其对应的文本标注。
- **多格式图片支持：** `image` 字段可以为字符串或列表，支持通过下拉框切换多图显示。
- **bbox 可视化：** 支持以不同格式（如 `cxcywh`、`xyxy`、`xywh` 及其归一化版本）叠加显示 bounding box。若存在多个 bbox，可通过按钮切换显示。
- **搜索跳转：** 顶部搜索栏允许选择字段并输入查询值，快速跳转到匹配的标注记录。
- **布局调整：** 左右区域支持拖拽调整显示比例。
- **语言切换：** 支持中英文界面切换。
- **其他选项：** 可设置图片前缀以补救无效的图片路径，可手动定义图片字段等。

### 功能
- **加载 JSON 标注：** 通过“文件”菜单打开 JSON 标注文件。
- **编辑标注：** 修改文本标注并实时保存。
- **叠加设置：** 在“叠加选项”区域配置 bbox 显示格式及多个 bbox 之间的切换。
- **搜索跳转：** 使用顶部搜索栏，根据指定字段和值快速跳转到匹配记录。
- **响应式界面：** 支持左右区域拖拽调整布局。

### 安装步骤
1. **前提条件：** Python 3.6 及以上版本。
2. **安装依赖：**
    ```bash
    pip install PyQt5
    ```
3. **克隆仓库：**
    ```bash
    git clone https://github.com/yourusername/annotation-editor.git
    cd annotation-editor
    ```
4. **运行软件：**
    ```bash
    python annotation_editor.py
    ```

### 使用方法
- **加载标注数据：** 通过“文件 → 打开 JSON”加载标注文件。
- **编辑与翻页：** 在右侧编辑区域修改标注数据，并使用“上一条/下一条”按钮切换记录。
- **叠加设置：** 在“叠加选项”中配置 bbox 显示方式，如选择格式（cxcywh, xyxy, xywh 等）及切换多个 bbox。
- **搜索跳转：** 顶部搜索栏允许选择字段并输入查询值，点击“跳转”按钮即可跳转到匹配记录。
- **语言切换：** 使用右上角的语言按钮在中英文之间切换。

### 贡献
欢迎开发者提交 issue 和 pull request，共同改进此项目。

### 许可证
本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE)。

---

## How to Switch README Languages

This README includes both English and Chinese sections. You can simply scroll down to view the version you need. Alternatively, you may create separate files (e.g., `README.en.md` and `README.zh.md`) if preferred.

---

Happy coding! / 编程愉快！
