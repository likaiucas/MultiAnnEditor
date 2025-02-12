import sys
import os
import json
import ast
from functools import partial
from PyQt5 import QtWidgets, QtGui, QtCore

# --------------------------------------------------------------------
# 针对 image 字段的编辑器（支持 str 与 list 两种形式）
# --------------------------------------------------------------------
class ImageFieldEditor(QtWidgets.QWidget):
    imageIndexChanged = QtCore.pyqtSignal(int)  # 当下拉框选项变化时发出信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = 'str'  # 'str' 或 'list'
        self.value = None
        self.value_list = []
        self.current_index = 0
        self.current_lang = 'zh'
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QtWidgets.QLineEdit()
        layout.addWidget(self.lineEdit)
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.currentIndexChanged.connect(self.onIndexChanged)
        layout.addWidget(self.comboBox)
        self.comboBox.hide()  # 默认隐藏，下拉框仅在 value 为 list 时显示

    def onIndexChanged(self, index):
        self.current_index = index
        if self.mode == 'list':
            if 0 <= index < len(self.value_list):
                self.lineEdit.setText(self.value_list[index])
        self.imageIndexChanged.emit(index)

    def updateValue(self, value):
        self.value = value
        if isinstance(value, list):
            self.mode = 'list'
            self.value_list = value
            self.comboBox.show()
            self.populateComboBox()
            self.comboBox.setCurrentIndex(0)
            if value:
                self.lineEdit.setText(value[0])
            self.lineEdit.setReadOnly(True)
        elif isinstance(value, str):
            self.mode = 'str'
            self.comboBox.hide()
            self.lineEdit.setReadOnly(False)
            self.lineEdit.setText(value)
        else:
            self.mode = 'str'
            self.comboBox.hide()
            self.lineEdit.setReadOnly(False)
            self.lineEdit.setText(str(value))

    def getText(self):
        return self.lineEdit.text()

    def populateComboBox(self):
        self.comboBox.clear()
        for i in range(len(self.value_list)):
            if self.current_lang == 'zh':
                item = f"图片 {i+1}"
            else:
                item = f"Image {i+1}"
            self.comboBox.addItem(item)

    def setLanguage(self, lang):
        self.current_lang = lang
        if self.mode == 'list':
            self.populateComboBox()

# --------------------------------------------------------------------
# 主编辑器窗口（支持图片-文本编辑、图片前缀补救、语言切换、bbox叠加显示以及标签跳转功能）
# --------------------------------------------------------------------
class AnnotationEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片-文本标注编辑器")
        self.annotations = []         # 标注数据列表
        self.current_index = 0        # 当前显示的标注索引
        self.field_widgets = {}       # 各字段对应的编辑器控件（对于 image 字段使用 ImageFieldEditor）
        self.field_checkboxes = {}    # 任务栏中各字段对应的复选框
        self.available_fields = set() # 所有标注中出现的字段集合
        self.image_fields = set()     # 默认自动识别 image 字段（key=="image"），若无则可通过“定义图片字段”来指定
        self.json_path = None         # 当前打开的 JSON 文件路径
        self.current_lang = 'zh'      # 当前界面语言，默认为中文
        self.image_prefix = ""        # 用户手工设置的图片前缀（用于查找不存在的绝对路径图片）
        # 保存 bbox 叠加显示的配置信息，键为字段名（例如 "bbox", "zoom_bbox"）
        # 值为字典，记录 "enabled"、"format"、"index" 和 "max_index"
        self.overlay_configs = {}

        self.translations = {
            'window_title': {'en': 'Image-Text Annotation Editor', 'zh': '图片-文本标注编辑器'},
            'file': {'en': 'File', 'zh': '文件'},
            'open_json': {'en': 'Open JSON', 'zh': '打开 JSON'},
            'save_json': {'en': 'Save JSON', 'zh': '保存 JSON'},
            'exit': {'en': 'Exit', 'zh': '退出'},
            'prev': {'en': 'Previous', 'zh': '上一条'},
            'next': {'en': 'Next', 'zh': '下一条'},
            'image_area_default': {'en': 'Image Display Area', 'zh': '图片显示区域'},
            'click_to_show_image': {'en': 'Click to show image', 'zh': '点击显示图片'},
            'ready': {'en': 'Ready', 'zh': '就绪'},
            'loaded': {'en': 'Loaded {} annotations', 'zh': '加载了 {} 条标注数据'},
            'image_not_exist': {'en': 'Image file does not exist', 'zh': '图片文件不存在'},
            'load_image_fail': {'en': 'Failed to load image', 'zh': '加载图片失败'},
            'no_image_data': {'en': 'No image data', 'zh': '无图片数据'},
            'save_success': {'en': 'Saved successfully: {}', 'zh': '保存成功：{}'},
            'save_fail': {'en': 'Failed to save JSON file:\n{}', 'zh': '保存 JSON 文件失败：\n{}'},
            'open_fail': {'en': 'Failed to load JSON file:\n{}', 'zh': '加载 JSON 文件失败：\n{}'},
            'set_image_prefix': {'en': 'Set Image Prefix', 'zh': '设置图片文件夹'},
            'define_image_field': {'en': 'Define Image Field', 'zh': '定义图片字段'},
            'image_prefix_set': {'en': 'Image folder set to: {}', 'zh': '图片文件夹设置为：{}'},
            'select_image_field': {'en': 'Select a field to use as image field:', 'zh': '选择一个字段作为图片字段：'},
            'options': {'en': 'Options', 'zh': '选项'},
            'no_available_field': {'en': 'No available field to define as image field', 'zh': '没有可用的字段来定义为图片字段'},
            # bbox叠加相关
            'overlay_options': {'en': 'Overlay Options', 'zh': '叠加选项'},
            'show': {'en': 'Show', 'zh': '显示'},
            'prev_item': {'en': 'Prev', 'zh': '上一项'},
            'next_item': {'en': 'Next', 'zh': '下一项'},
            # 搜索相关（搜索栏中的标签文本）
            'search': {'en': 'Search', 'zh': '搜索'},
            'search_key': {'en': 'Key', 'zh': '字段'},
            'search_value': {'en': 'Value', 'zh': '值'},
            'go': {'en': 'Go', 'zh': '跳转'},
            'no_match': {'en': 'No matching record found!', 'zh': '未找到匹配记录！'},
        }
        self.initUI()

    def translate(self, key):
        return self.translations.get(key, {}).get(self.current_lang, key)

    def initUI(self):
        self.createMenu()
        self.createSearchBar()  # 新增搜索工具栏
        self.createNavigationBar()
        self.createCentralWidget()
        self.createOverlayDock()
        self.statusBar().showMessage(self.translate('ready'))

    def createMenu(self):
        menubar = self.menuBar()
        # 文件菜单
        self.fileMenu = menubar.addMenu(self.translate('file'))
        self.openAct = QtWidgets.QAction(self.translate('open_json'), self)
        self.openAct.triggered.connect(self.openJson)
        self.fileMenu.addAction(self.openAct)
        self.saveAct = QtWidgets.QAction(self.translate('save_json'), self)
        self.saveAct.triggered.connect(self.saveJson)
        self.fileMenu.addAction(self.saveAct)
        self.exitAct = QtWidgets.QAction(self.translate('exit'), self)
        self.exitAct.triggered.connect(self.close)
        self.fileMenu.addAction(self.exitAct)
        # 选项菜单
        self.optionsMenu = menubar.addMenu(self.translate('options'))
        self.setImagePrefixAct = QtWidgets.QAction(self.translate('set_image_prefix'), self)
        self.setImagePrefixAct.triggered.connect(self.setImagePrefix)
        self.optionsMenu.addAction(self.setImagePrefixAct)
        self.defineImageFieldAct = QtWidgets.QAction(self.translate('define_image_field'), self)
        self.defineImageFieldAct.triggered.connect(self.defineImageField)
        self.optionsMenu.addAction(self.defineImageFieldAct)

    def createSearchBar(self):
        """在窗口上方创建搜索工具栏，用于标签跳转功能。"""
        self.searchToolBar = QtWidgets.QToolBar(self.translate('search'))
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.searchToolBar)

        label_key = QtWidgets.QLabel(self.translate('search_key') + ":")
        self.searchToolBar.addWidget(label_key)

        self.searchFieldCombo = QtWidgets.QComboBox()
        self.searchToolBar.addWidget(self.searchFieldCombo)

        label_value = QtWidgets.QLabel(self.translate('search_value') + ":")
        self.searchToolBar.addWidget(label_value)

        self.searchLineEdit = QtWidgets.QLineEdit()
        self.searchToolBar.addWidget(self.searchLineEdit)

        self.searchButton = QtWidgets.QPushButton(self.translate('go'))
        self.searchButton.clicked.connect(self.searchAnnotations)
        self.searchToolBar.addWidget(self.searchButton)

    def updateSearchFields(self):
        """更新搜索下拉框，使用当前所有的字段作为候选key。"""
        if hasattr(self, "searchFieldCombo"):
            self.searchFieldCombo.clear()
            for field in sorted(self.available_fields):
                self.searchFieldCombo.addItem(field)

    def searchAnnotations(self):
        """根据搜索栏中的字段和查询内容，在整个标注数据中查找匹配的记录，并跳转到该记录。"""
        key = self.searchFieldCombo.currentText()
        query = self.searchLineEdit.text().strip()
        if not key or not query:
            return
        n = len(self.annotations)
        start = (self.current_index + 1) % n  # 从下一条开始查找
        found = False
        # 先查找从当前记录到末尾的记录
        for i in range(start, n):
            if key in self.annotations[i]:
                val_str = str(self.annotations[i][key])
                if query in val_str:
                    self.current_index = i
                    self.updateUI()
                    found = True
                    break
        # 如未找到，再查找从头到当前记录
        if not found:
            for i in range(0, start):
                if key in self.annotations[i]:
                    val_str = str(self.annotations[i][key])
                    if query in val_str:
                        self.current_index = i
                        self.updateUI()
                        found = True
                        break
        if not found:
            QtWidgets.QMessageBox.information(self, self.translate('search'), self.translate('no_match'))

    def createNavigationBar(self):
        navWidget = QtWidgets.QWidget()
        navLayout = QtWidgets.QHBoxLayout()
        self.prevButton = QtWidgets.QPushButton(self.translate('prev'))
        self.prevButton.clicked.connect(self.showPrevious)
        self.nextButton = QtWidgets.QPushButton(self.translate('next'))
        self.nextButton.clicked.connect(self.showNext)
        self.pageLabel = QtWidgets.QLabel("0/0")
        navLayout.addWidget(self.prevButton)
        navLayout.addStretch()
        navLayout.addWidget(self.pageLabel)
        navLayout.addStretch()
        navLayout.addWidget(self.nextButton)
        navWidget.setLayout(navLayout)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.createToolBarFromWidget(navWidget))

    def createToolBarFromWidget(self, widget):
        toolbar = QtWidgets.QToolBar()
        toolbar.addWidget(widget)
        return toolbar

    def createCentralWidget(self):
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        # 左侧：图片显示区域
        self.imageLabel = QtWidgets.QLabel(self.translate('image_area_default'))
        self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.imageLabel.setMinimumSize(400, 400)
        splitter.addWidget(self.imageLabel)
        # 右侧：字段编辑区域
        rightWidget = QtWidgets.QWidget()
        rightLayout = QtWidgets.QVBoxLayout()
        # 上部任务栏：包含字段复选框和语言切换按钮
        self.fieldTaskBar = QtWidgets.QWidget()
        fieldTaskBarLayout = QtWidgets.QHBoxLayout(self.fieldTaskBar)
        # 放置字段复选框的区域
        self.checkboxesWidget = QtWidgets.QWidget()
        self.checkboxesLayout = QtWidgets.QHBoxLayout(self.checkboxesWidget)
        self.checkboxesWidget.setLayout(self.checkboxesLayout)
        fieldTaskBarLayout.addWidget(self.checkboxesWidget)
        fieldTaskBarLayout.addStretch()
        # 语言切换按钮
        self.langZhButton = QtWidgets.QPushButton("中文")
        self.langEnButton = QtWidgets.QPushButton("English")
        self.langZhButton.clicked.connect(lambda: self.switchLanguage('zh'))
        self.langEnButton.clicked.connect(lambda: self.switchLanguage('en'))
        fieldTaskBarLayout.addWidget(self.langZhButton)
        fieldTaskBarLayout.addWidget(self.langEnButton)
        rightLayout.addWidget(self.fieldTaskBar)
        # 中部：滚动区域，包含各字段编辑器
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollAreaWidget = QtWidgets.QWidget()
        self.fieldsLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidget)
        self.scrollAreaWidget.setLayout(self.fieldsLayout)
        self.scrollArea.setWidget(self.scrollAreaWidget)
        self.scrollArea.setWidgetResizable(True)
        rightLayout.addWidget(self.scrollArea)
        rightWidget.setLayout(rightLayout)
        splitter.addWidget(rightWidget)
        splitter.setStretchFactor(1, 1)
        layout = QtWidgets.QHBoxLayout(centralWidget)
        layout.addWidget(splitter)

    def createOverlayDock(self):
        # 创建用于设置 bbox 叠加可视化的 Dock Widget
        self.overlayDock = QtWidgets.QDockWidget(self.translate('overlay_options'), self)
        self.overlayWidget = QtWidgets.QWidget()
        self.overlayLayout = QtWidgets.QVBoxLayout(self.overlayWidget)
        self.overlayWidget.setLayout(self.overlayLayout)
        self.overlayDock.setWidget(self.overlayWidget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.overlayDock)

    def openJson(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, self.translate('open_json'), "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.annotations = json.load(f)
                self.json_path = path
                self.current_index = 0
                self.collectFields()
                self.buildFieldEditors()
                self.updateUI()
                self.statusBar().showMessage(self.translate('loaded').format(len(self.annotations)))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, self.translate('open_json'),
                                               self.translate('open_fail').format(str(e)))

    def saveJson(self):
        if not self.annotations:
            return
        self.saveCurrentAnnotation()  # 保存当前编辑内容
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, self.translate('save_json'),
                                                          self.json_path if self.json_path else "",
                                                          "JSON Files (*.json)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.annotations, f, indent=4, ensure_ascii=False)
                self.statusBar().showMessage(self.translate('save_success').format(path))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, self.translate('save_json'),
                                               self.translate('save_fail').format(str(e)))

    def collectFields(self):
        """
        遍历所有标注，收集所有出现的字段。
        若 key 为 "image" 则自动识别为图片字段；其他字段照原样收集。
        同时刷新右侧任务栏中的复选框。
        """
        self.available_fields = set()
        self.image_fields = set()
        for ann in self.annotations:
            for key, value in ann.items():
                self.available_fields.add(key)
                if key == "image":
                    if (isinstance(value, str) and self.isImageFile(value)) or (isinstance(value, list) and len(value) > 0):
                        self.image_fields.add(key)
        # 更新搜索下拉框
        self.updateSearchFields()
        # 清空复选框区域（保留语言按钮）
        for i in reversed(range(self.checkboxesLayout.count())):
            widget = self.checkboxesLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.field_checkboxes.clear()
        for field in sorted(self.available_fields):
            checkbox = QtWidgets.QCheckBox(field)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, f=field: self.toggleFieldEditor(f, state))
            self.checkboxesLayout.addWidget(checkbox)
            self.field_checkboxes[field] = checkbox

    def updateSearchFields(self):
        """更新搜索栏下拉框中的 key 选项。"""
        if hasattr(self, "searchFieldCombo"):
            self.searchFieldCombo.clear()
            for field in sorted(self.available_fields):
                self.searchFieldCombo.addItem(field)

    def buildFieldEditors(self):
        """
        为每个字段创建编辑器：
          - 对于 image 字段采用 ImageFieldEditor；
          - 其他字段使用 QTextEdit，若数据非字符串则以 json.dumps 显示。
        """
        for i in reversed(range(self.fieldsLayout.count())):
            item = self.fieldsLayout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.field_widgets.clear()
        for field in sorted(self.available_fields):
            label = QtWidgets.QLabel(field)
            if field in self.image_fields:
                editor = ImageFieldEditor()
                # 点击文本框或下拉框时更新左侧图片显示
                editor.lineEdit.mousePressEvent = lambda event, f=field: self.displayImageField(f)
                editor.imageIndexChanged.connect(lambda idx, f=field: self.displayImageField(f))
            else:
                editor = QtWidgets.QTextEdit()
                editor.setMinimumHeight(50)
                editor.textChanged.connect(lambda f=field, ed=editor: self.onTextChanged(f, ed))
            container = QtWidgets.QWidget()
            containerLayout = QtWidgets.QVBoxLayout()
            containerLayout.addWidget(label)
            containerLayout.addWidget(editor)
            container.setLayout(containerLayout)
            self.fieldsLayout.addWidget(container)
            self.field_widgets[field] = editor
        self.fieldsLayout.addStretch()

    def toggleFieldEditor(self, field, state):
        if field in self.field_widgets:
            widget = self.field_widgets[field]
            widget.parentWidget().setVisible(state == QtCore.Qt.Checked)
        if field in self.image_fields and state == QtCore.Qt.Checked:
            self.displayImageField(field)

    def displayImageField(self, field):
        """
        根据当前标注中指定字段的值加载图片：
          - 当字段值为字符串时直接作为图片路径；
          - 当为 list 时，根据 ImageFieldEditor 当前选择的索引获取图片路径；
        若文件不存在且已设置 image_prefix，则尝试使用前缀与文件名拼接后的路径加载。
        加载后调用 drawOverlays() 在图片上绘制 bbox 叠加信息。
        """
        if not self.annotations:
            return
        ann = self.annotations[self.current_index]
        if field not in ann:
            self.imageLabel.setText(self.translate('no_image_data'))
            return
        value = ann[field]
        image_path = None
        if field in self.image_fields:
            editor = self.field_widgets.get(field)
            if isinstance(value, list):
                if isinstance(editor, ImageFieldEditor):
                    idx = editor.current_index
                    if idx < len(value):
                        image_path = value[idx]
            elif isinstance(value, str):
                image_path = value
        if image_path:
            if not os.path.isfile(image_path) and self.image_prefix:
                alt_path = os.path.join(self.image_prefix, os.path.basename(image_path))
                if os.path.isfile(alt_path):
                    image_path = alt_path
            if os.path.isfile(image_path):
                pixmap = QtGui.QPixmap(image_path)
                if not pixmap.isNull():
                    # 绘制 bbox 叠加信息（若有设置）
                    pixmap = self.drawOverlays(pixmap, ann)
                    scaled_pixmap = pixmap.scaled(self.imageLabel.size(), QtCore.Qt.KeepAspectRatio,
                                                    QtCore.Qt.SmoothTransformation)
                    self.imageLabel.setPixmap(scaled_pixmap)
                else:
                    self.imageLabel.setText(self.translate('load_image_fail'))
            else:
                self.imageLabel.setText(self.translate('image_not_exist'))
        else:
            self.imageLabel.setText(self.translate('no_image_data'))

    def resizeEvent(self, event):
        for field in self.image_fields:
            if self.field_checkboxes.get(field) and self.field_checkboxes[field].isChecked():
                self.displayImageField(field)
                break
        super().resizeEvent(event)

    def onTextChanged(self, field, editor):
        if not self.annotations:
            return
        text = editor.toPlainText()
        orig_value = self.annotations[self.current_index].get(field)
        if isinstance(orig_value, str):
            new_value = text
        else:
            try:
                new_value = ast.literal_eval(text)
            except Exception:
                new_value = text
        self.annotations[self.current_index][field] = new_value

    def saveCurrentAnnotation(self):
        if not self.annotations:
            return
        ann = self.annotations[self.current_index]
        for field in self.available_fields:
            if field in self.image_fields:
                editor = self.field_widgets.get(field)
                if isinstance(editor, ImageFieldEditor):
                    if editor.mode == 'str':
                        text = editor.getText()
                        ann[field] = text
                continue
            editor = self.field_widgets.get(field)
            if editor:
                text = editor.toPlainText()
                orig_value = ann.get(field)
                if isinstance(orig_value, str):
                    new_value = text
                else:
                    try:
                        new_value = ast.literal_eval(text)
                    except Exception:
                        new_value = text
                ann[field] = new_value

    def updateUI(self):
        if not self.annotations:
            return
        ann = self.annotations[self.current_index]
        for field in self.available_fields:
            if field in self.image_fields:
                editor = self.field_widgets.get(field)
                if isinstance(editor, ImageFieldEditor):
                    editor.updateValue(ann.get(field, ""))
            else:
                editor = self.field_widgets.get(field)
                if editor:
                    editor.blockSignals(True)
                    value = ann.get(field, "")
                    if isinstance(value, str):
                        editor.setPlainText(value)
                    else:
                        editor.setPlainText(json.dumps(value, ensure_ascii=False))
                    editor.blockSignals(False)
        # 更新 bbox 叠加选项区域（保留用户的选择）
        self.updateOverlayOptions()
        # 更新搜索栏选项
        self.updateSearchFields()
        # 更新左侧图片显示（显示第一个被选中的 image 字段）
        for field in self.image_fields:
            if self.field_checkboxes.get(field) and self.field_checkboxes[field].isChecked():
                self.displayImageField(field)
                break
        self.pageLabel.setText(f"{self.current_index + 1}/{len(self.annotations)}")

    # -------------------- bbox 叠加（Overlay）相关函数 --------------------
    def updateOverlayOptions(self):
        """
        遍历当前标注（除 image 外）的所有字段，检查是否存在 bbox 数据。
        若某字段的值为：
          - 一组数字（长度==4且全部为数字）：视为单个 bbox；
          - 或为列表且其首元素为列表（且每个子列表为4个数字）：视为包含多个 bbox。
        对于符合条件的字段，如果该字段已有配置则保留，否则建立默认配置。
        然后根据配置生成对应的设置面板。
        """
        # 清空之前的 Overlay 控件
        for i in reversed(range(self.overlayLayout.count())):
            widget = self.overlayLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        ann = self.annotations[self.current_index]
        # 遍历除 image 外的字段
        for field, value in ann.items():
            if field == "image":
                continue
            bbox_data = None
            max_index = 0
            if isinstance(value, list):
                # 单个 bbox
                if len(value) == 4 and all(isinstance(x, (int, float)) for x in value):
                    bbox_data = value
                    max_index = 0
                # 多个 bbox
                elif len(value) > 0 and isinstance(value[0], list) and all(isinstance(x, (int, float)) for x in value[0]):
                    bbox_data = value
                    max_index = len(value) - 1
            if bbox_data is None:
                continue
            # 如果该字段已有配置则保留，否则建立默认配置
            if field not in self.overlay_configs:
                self.overlay_configs[field] = {
                    "enabled": False,
                    "format": "xyxy",  # 默认格式
                    "index": 0,
                    "max_index": max_index,
                }
            else:
                self.overlay_configs[field]["max_index"] = max_index
            config = self.overlay_configs[field]
            # 创建 UI 控件
            group = QtWidgets.QGroupBox(f"{field} (bbox)")
            layout = QtWidgets.QHBoxLayout()
            # 复选框：是否显示该 bbox 叠加
            cb = QtWidgets.QCheckBox(self.translate('show'))
            cb.setChecked(config["enabled"])
            cb.stateChanged.connect(partial(self.setOverlayEnabled, field))
            layout.addWidget(cb)
            # 格式选择下拉框
            fmt_combo = QtWidgets.QComboBox()
            fmt_options = ["cxcywh", "xyxy", "xywh", "normalized cxcywh", "normalized xyxy", "normalized xywh"]
            fmt_combo.addItems(fmt_options)
            fmt_combo.setCurrentText(config["format"])
            fmt_combo.currentTextChanged.connect(partial(self.setOverlayFormat, field))
            layout.addWidget(fmt_combo)
            # 若存在多个 bbox，则添加 Prev/Next 按钮与索引标签
            if max_index > 0:
                prev_btn = QtWidgets.QPushButton(self.translate('prev_item'))
                next_btn = QtWidgets.QPushButton(self.translate('next_item'))
                idx_label = QtWidgets.QLabel(f"{config['index']} / {max_index}")
                prev_btn.clicked.connect(partial(self.prevOverlayIndex, field, idx_label))
                next_btn.clicked.connect(partial(self.nextOverlayIndex, field, idx_label))
                layout.addWidget(prev_btn)
                layout.addWidget(next_btn)
                layout.addWidget(idx_label)
            group.setLayout(layout)
            self.overlayLayout.addWidget(group)
        self.overlayLayout.addStretch()

    def setOverlayEnabled(self, field, state):
        config = self.overlay_configs.get(field)
        if config is not None:
            config["enabled"] = (state == QtCore.Qt.Checked)
            self.updateUI()

    def setOverlayFormat(self, field, text):
        config = self.overlay_configs.get(field)
        if config is not None:
            config["format"] = text
            self.updateUI()

    def prevOverlayIndex(self, field, label):
        config = self.overlay_configs.get(field)
        if config is not None and config["index"] > 0:
            config["index"] -= 1
            label.setText(f"{config['index']} / {config['max_index']}")
            self.updateUI()

    def nextOverlayIndex(self, field, label):
        config = self.overlay_configs.get(field)
        if config is not None and config["index"] < config["max_index"]:
            config["index"] += 1
            label.setText(f"{config['index']} / {config['max_index']}")
            self.updateUI()

    def convertBBox(self, bbox, fmt, img_width, img_height):
        """
        将 bbox 数据转换为 QRectF 对象以便绘制。
        支持格式：cxcywh, xyxy, xywh 及其归一化版本（归一化时数值在0~1之间）。
        """
        try:
            coords = list(map(float, bbox))
        except Exception:
            return None
        normalized = "normalized" in fmt
        if normalized:
            mult_x = img_width
            mult_y = img_height
            fmt = fmt.replace("normalized ", "")
        else:
            mult_x = 1
            mult_y = 1
        if fmt == "xyxy":
            if len(coords) < 4:
                return None
            x1, y1, x2, y2 = coords[:4]
            return QtCore.QRectF(x1 * mult_x, y1 * mult_y, (x2 - x1) * mult_x, (y2 - y1) * mult_y)
        elif fmt == "xywh":
            if len(coords) < 4:
                return None
            x, y, w, h = coords[:4]
            return QtCore.QRectF(x * mult_x, y * mult_y, w * mult_x, h * mult_y)
        elif fmt == "cxcywh":
            if len(coords) < 4:
                return None
            cx, cy, w, h = coords[:4]
            return QtCore.QRectF((cx - w / 2) * mult_x, (cy - h / 2) * mult_y, w * mult_x, h * mult_y)
        else:
            return None

    def getOverlayColors(self, field, overlay_type):
        """
        根据 (field, overlay_type) 自动分配一个半透明颜色。
        边框颜色 alpha=200，填充颜色 alpha=100。
        """
        base_colors = [
            QtGui.QColor(255, 0, 0, 128),    # 红
            QtGui.QColor(0, 255, 0, 128),    # 绿
            QtGui.QColor(0, 0, 255, 128),    # 蓝
            QtGui.QColor(255, 255, 0, 128),  # 黄
            QtGui.QColor(255, 0, 255, 128),  # 品红
            QtGui.QColor(0, 255, 255, 128),  # 青
            QtGui.QColor(128, 0, 128, 128),  # 紫
        ]
        key = (field, overlay_type)
        index = abs(hash(key)) % len(base_colors)
        border = QtGui.QColor(base_colors[index].red(), base_colors[index].green(), base_colors[index].blue(), 200)
        fill = QtGui.QColor(base_colors[index].red(), base_colors[index].green(), base_colors[index].blue(), 100)
        return border, fill

    def drawOverlays(self, pixmap, ann):
        """
        在给定的 pixmap 上绘制各字段的 bbox 叠加信息。
        若某字段中为多个 bbox（list of list），则按照配置中 index 指定的实例进行显示；否则直接显示。
        根据用户选择的格式转换坐标后绘制半透明矩形。
        """
        painter = QtGui.QPainter(pixmap)
        for field, config in self.overlay_configs.items():
            if not config["enabled"]:
                continue
            raw_data = ann.get(field, None)
            if raw_data is None:
                continue
            # 判断数据格式
            if isinstance(raw_data, list):
                if len(raw_data) == 4 and all(isinstance(x, (int, float)) for x in raw_data):
                    data_to_draw = raw_data
                elif len(raw_data) > 0 and isinstance(raw_data[0], list) and all(isinstance(x, (int, float)) for x in raw_data[0]):
                    total = len(raw_data)
                    idx = config["index"]
                    if idx < total:
                        data_to_draw = raw_data[idx]
                    else:
                        data_to_draw = raw_data[0]
                else:
                    continue
            else:
                continue
            rect = self.convertBBox(data_to_draw, config["format"], pixmap.width(), pixmap.height())
            if rect is not None:
                border, fill = self.getOverlayColors(field, "bbox")
                pen = QtGui.QPen(border, 2)
                painter.setPen(pen)
                brush = QtGui.QBrush(fill)
                painter.setBrush(brush)
                painter.drawRect(rect)
        painter.end()
        return pixmap

    # -------------------- 导航与语言切换 --------------------
    def showPrevious(self):
        if self.current_index > 0:
            self.saveCurrentAnnotation()
            self.current_index -= 1
            self.updateUI()

    def showNext(self):
        if self.current_index < len(self.annotations) - 1:
            self.saveCurrentAnnotation()
            self.current_index += 1
            self.updateUI()

    def isImageFile(self, path):
        lower = path.lower()
        return (lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg") or
                lower.endswith(".bmp") or lower.endswith(".gif"))

    def switchLanguage(self, lang):
        self.current_lang = lang
        self.updateLanguage()

    def updateLanguage(self):
        self.setWindowTitle(self.translate('window_title'))
        self.fileMenu.setTitle(self.translate('file'))
        self.openAct.setText(self.translate('open_json'))
        self.saveAct.setText(self.translate('save_json'))
        self.exitAct.setText(self.translate('exit'))
        self.optionsMenu.setTitle(self.translate('options'))
        self.setImagePrefixAct.setText(self.translate('set_image_prefix'))
        self.defineImageFieldAct.setText(self.translate('define_image_field'))
        self.prevButton.setText(self.translate('prev'))
        self.nextButton.setText(self.translate('next'))
        if not self.imageLabel.pixmap():
            self.imageLabel.setText(self.translate('image_area_default'))
        self.statusBar().showMessage(self.translate('ready'))
        for field in self.image_fields:
            editor = self.field_widgets.get(field)
            if isinstance(editor, ImageFieldEditor):
                editor.setLanguage(self.current_lang)
        self.overlayDock.setWindowTitle(self.translate('overlay_options'))
        # 同步更新搜索栏中的标签
        if hasattr(self, "searchToolBar"):
            # 更新搜索工具栏各控件文本
            self.searchToolBar.setWindowTitle(self.translate('search'))
            # 这里简单地更新按钮文字
            self.searchButton.setText(self.translate('go'))

    def setImagePrefix(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, self.translate('set_image_prefix'), "")
        if folder:
            self.image_prefix = folder
            self.statusBar().showMessage(self.translate('image_prefix_set').format(folder))
            # 刷新当前图片显示（立刻调用显示函数）
            for field in self.image_fields:
                if self.field_checkboxes.get(field) and self.field_checkboxes[field].isChecked():
                    self.displayImageField(field)
                    break

    def defineImageField(self):
        candidates = [field for field in self.available_fields if field not in self.image_fields]
        if not candidates:
            QtWidgets.QMessageBox.information(self, self.translate('define_image_field'),
                                              self.translate('no_available_field'))
            return
        field, ok = QtWidgets.QInputDialog.getItem(self, self.translate('define_image_field'),
                                                   self.translate('select_image_field'),
                                                   candidates, 0, False)
        if ok and field:
            self.image_fields.add(field)
            self.buildFieldEditors()
            self.updateUI()
            self.statusBar().showMessage(f"{self.translate('define_image_field')}: {field}")

    # -------------------- 搜索（标签跳转）相关函数 --------------------
    def updateSearchFields(self):
        """更新搜索栏下拉框中的 key 选项。"""
        if hasattr(self, "searchFieldCombo"):
            self.searchFieldCombo.clear()
            for field in sorted(self.available_fields):
                self.searchFieldCombo.addItem(field)

    def searchAnnotations(self):
        """根据搜索栏中的字段和查询内容，在整个标注数据中查找匹配的记录，并跳转到该记录。"""
        key = self.searchFieldCombo.currentText()
        query = self.searchLineEdit.text().strip()
        if not key or not query:
            return
        n = len(self.annotations)
        start = (self.current_index + 1) % n  # 从下一条开始查找
        found = False
        # 先查找从当前记录到末尾的记录
        for i in range(start, n):
            if key in self.annotations[i]:
                val_str = str(self.annotations[i][key])
                if query in val_str:
                    self.current_index = i
                    self.updateUI()
                    found = True
                    break
        # 如未找到，再查找从头到当前记录
        if not found:
            for i in range(0, start):
                if key in self.annotations[i]:
                    val_str = str(self.annotations[i][key])
                    if query in val_str:
                        self.current_index = i
                        self.updateUI()
                        found = True
                        break
        if not found:
            QtWidgets.QMessageBox.information(self, self.translate('search'), self.translate('no_match'))

    # -------------------- 导航与语言切换 --------------------
    def showPrevious(self):
        if self.current_index > 0:
            self.saveCurrentAnnotation()
            self.current_index -= 1
            self.updateUI()

    def showNext(self):
        if self.current_index < len(self.annotations) - 1:
            self.saveCurrentAnnotation()
            self.current_index += 1
            self.updateUI()

    def isImageFile(self, path):
        lower = path.lower()
        return (lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg") or
                lower.endswith(".bmp") or lower.endswith(".gif"))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    editor = AnnotationEditor()
    editor.resize(1000, 700)
    editor.show()
    sys.exit(app.exec_())
