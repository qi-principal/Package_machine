"""
设置对话框模块
提供系统配置管理界面
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QCheckBox,
    QSpinBox, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QWidget, QInputDialog, QGroupBox
)
from PyQt5.QtCore import Qt
from src.config.config_manager import ConfigManager

class SettingsDialog(QDialog):
    """设置对话框类"""
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(500)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 添加各个设置页面
        tab_widget.addTab(self.create_general_tab(), "常规")
        tab_widget.addTab(self.create_file_types_tab(), "文件类型")
        tab_widget.addTab(self.create_ai_tab(), "AI设置")
        tab_widget.addTab(self.create_backup_tab(), "备份")
        
        # 创建按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self) -> QWidget:
        """创建常规设置页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 目标目录设置
        target_group = QGroupBox("目标目录设置")
        target_layout = QVBoxLayout()
        
        target_dir_layout = QHBoxLayout()
        self.target_dir_input = QLineEdit()
        self.target_dir_input.setPlaceholderText("选择分类文件的目标目录")
        self.target_dir_input.setText(
            self.config_manager.get_config("target_directory", "")
        )
        
        select_dir_btn = QPushButton("选择目录")
        select_dir_btn.clicked.connect(self.select_target_directory)
        
        target_dir_layout.addWidget(self.target_dir_input)
        target_dir_layout.addWidget(select_dir_btn)
        
        target_layout.addLayout(target_dir_layout)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 语言设置
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("界面语言:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)
        
        # 主题设置
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("界面主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # 自动保存设置
        self.auto_save_check = QCheckBox("自动保存分类结果")
        layout.addWidget(self.auto_save_check)
        
        layout.addStretch()
        return widget
        
    def create_file_types_tab(self) -> QWidget:
        """创建文件类型设置页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文件类型列表
        self.file_types_list = QListWidget()
        layout.addWidget(QLabel("允许的文件类型:"))
        layout.addWidget(self.file_types_list)
        
        # 添加和删除按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        remove_btn = QPushButton("删除")
        
        add_btn.clicked.connect(self.add_file_type)
        remove_btn.clicked.connect(self.remove_file_type)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        return widget
        
    def create_ai_tab(self) -> QWidget:
        """创建AI设置页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API密钥设置
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("DeepSeek API密钥:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.api_key_input)
        layout.addLayout(key_layout)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-chat", "deepseek-coder"])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)
        
        # API服务器设置
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("API服务器:"))
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("https://api.deepseek.com")
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        # 分类设置
        layout.addWidget(QLabel("分类设置:"))
        self.min_categories = QSpinBox()
        self.min_categories.setRange(1, 10)
        self.max_categories = QSpinBox()
        self.max_categories.setRange(1, 20)
        
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("每个文件的分类数量范围:"))
        cat_layout.addWidget(self.min_categories)
        cat_layout.addWidget(QLabel("到"))
        cat_layout.addWidget(self.max_categories)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)
        
        # 添加说明文本
        info_label = QLabel(
            "注意：DeepSeek API密钥用于文件分类功能。\n"
            "如果您还没有API密钥，请访问DeepSeek官网申请。"
        )
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
        
    def create_backup_tab(self) -> QWidget:
        """创建备份设置页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 启用备份
        self.backup_enabled = QCheckBox("启用文件备份")
        layout.addWidget(self.backup_enabled)
        
        # 备份目录
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("备份目录:"))
        self.backup_path = QLineEdit()
        self.backup_path.setReadOnly(True)
        backup_layout.addWidget(self.backup_path)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_backup_dir)
        backup_layout.addWidget(browse_btn)
        
        layout.addLayout(backup_layout)
        
        # 自动清理
        self.auto_cleanup = QCheckBox("自动清理无效的分类记录")
        layout.addWidget(self.auto_cleanup)
        
        layout.addStretch()
        return widget
        
    def load_settings(self):
        """加载设置"""
        try:
            # 加载目标目录
            target_directory = self.config_manager.get_config("target_directory", "")
            self.target_dir_input.setText(target_directory)
            
            # 加载常规设置
            language = self.config_manager.get_config("ui.language", "zh_CN")
            self.language_combo.setCurrentText(
                "简体中文" if language == "zh_CN" else "English"
            )
            
            theme = self.config_manager.get_config("ui.theme", "light")
            self.theme_combo.setCurrentText("浅色" if theme == "light" else "深色")
            
            self.auto_save_check.setChecked(
                self.config_manager.get_config("auto_save", True)
            )
            
            # 加载文件类型
            extensions = self.config_manager.get_allowed_extensions()
            self.file_types_list.clear()
            for ext in extensions:
                self.file_types_list.addItem(ext)
            
            # 加载AI设置
            self.api_key_input.setText(
                self.config_manager.get_config("deepseek.api_key", "")
            )
            
            model = self.config_manager.get_config("deepseek.model", "deepseek-chat")
            self.model_combo.setCurrentText(model)
            
            server = self.config_manager.get_config("deepseek.base_url", "https://api.deepseek.com")
            self.server_input.setText(server)
            
            self.min_categories.setValue(
                self.config_manager.get_config("classification.min_categories", 2)
            )
            self.max_categories.setValue(
                self.config_manager.get_config("classification.max_categories", 5)
            )
            
            # 加载备份设置
            self.backup_enabled.setChecked(
                self.config_manager.get_config("backup_enabled", True)
            )
            self.backup_path.setText(
                self.config_manager.get_config("backup_dir", "backups")
            )
            self.auto_cleanup.setChecked(
                self.config_manager.get_config("auto_cleanup", True)
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置时出错：{str(e)}")
            
    def save_settings(self):
        """保存设置"""
        try:
            # 保存目标目录
            target_directory = self.target_dir_input.text().strip()
            if target_directory:
                self.config_manager.set_config("target_directory", target_directory)
            
            # 保存常规设置
            self.config_manager.set_config(
                "ui.language",
                "zh_CN" if self.language_combo.currentText() == "简体中文" else "en"
            )
            self.config_manager.set_config(
                "ui.theme",
                "light" if self.theme_combo.currentText() == "浅色" else "dark"
            )
            self.config_manager.set_config(
                "auto_save",
                self.auto_save_check.isChecked()
            )
            
            # 保存文件类型
            extensions = []
            for i in range(self.file_types_list.count()):
                extensions.append(self.file_types_list.item(i).text())
            self.config_manager.set_config("allowed_extensions", extensions)
            
            # 保存AI设置
            self.config_manager.set_config(
                "deepseek.api_key",
                self.api_key_input.text()
            )
            self.config_manager.set_config(
                "deepseek.model",
                self.model_combo.currentText()
            )
            self.config_manager.set_config(
                "deepseek.base_url",
                self.server_input.text() or "https://api.deepseek.com"
            )
            self.config_manager.set_config(
                "classification.min_categories",
                self.min_categories.value()
            )
            self.config_manager.set_config(
                "classification.max_categories",
                self.max_categories.value()
            )
            
            # 保存备份设置
            self.config_manager.set_config(
                "backup_enabled",
                self.backup_enabled.isChecked()
            )
            self.config_manager.set_config(
                "backup_dir",
                self.backup_path.text()
            )
            self.config_manager.set_config(
                "auto_cleanup",
                self.auto_cleanup.isChecked()
            )
            
            # 保存到文件
            if self.config_manager.save_config():
                QMessageBox.information(self, "成功", "设置已保存")
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "保存设置失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置时发生错误：{str(e)}")
            
    def add_file_type(self):
        """添加文件类型"""
        extension, ok = QInputDialog.getText(
            self, "添加文件类型", "请输入文件扩展名（如 .txt）:"
        )
        if ok and extension:
            if not extension.startswith('.'):
                extension = f'.{extension}'
            self.file_types_list.addItem(extension.lower())
            
    def remove_file_type(self):
        """删除文件类型"""
        current_item = self.file_types_list.currentItem()
        if current_item:
            self.file_types_list.takeItem(self.file_types_list.row(current_item))
            
    def browse_backup_dir(self):
        """浏览备份目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择备份目录", self.backup_path.text()
        )
        if directory:
            self.backup_path.setText(directory)
            
    def select_target_directory(self):
        """选择目标目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择目标目录",
            self.target_dir_input.text()
        )
        if directory:
            self.target_dir_input.setText(directory) 