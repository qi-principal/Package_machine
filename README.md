# 智能文件分类系统

基于DeepSeek AI的智能文件分类系统，能够自动对文件进行分类和管理。本系统采用现代化的iOS风格界面设计，提供直观的用户体验。

## 功能特点

### 核心功能
- 智能文件分类（基于DeepSeek AI）
- 多种文件类型支持和过滤
- 批量文件处理
- 自定义分类规则
- 分类历史记录

### 文件管理
- 安全的文件移动机制
- 自动文件备份
- 文件预览功能
- 重复文件检测
- 文件完整性验证

### 用户界面
- iOS风格的现代化界面
- 深色/浅色主题切换
- 实时进度显示
- 性能监控面板
- API使用统计

### 系统功能
- 完整的配置管理
- 多语言支持
- 错误处理和日志记录
- 性能优化
- 自动更新

## 系统要求

- Python 3.8+
- Windows/Linux/MacOS
- 2GB以上可用内存
- DeepSeek API密钥

## 项目结构

```
project/
├── src/                 # 源代码
│   ├── core/           # 核心功能模块
│   │   ├── ai_classifier.py     # AI分类引擎
│   │   ├── file_system.py      # 文件系统操作
│   │   ├── file_filter.py      # 文件过滤器
│   │   ├── file_mover.py       # 文件移动器
│   │   └── category_storage.py # 分类存储系统
│   ├── ui/             # 界面相关代码
│   │   ├── main_window.py          # 主窗口
│   │   ├── settings_dialog.py      # 设置对话框
│   │   ├── api_monitor_widget.py   # API监控组件
│   │   └── performance_monitor_widget.py # 性能监控组件
│   ├── utils/          # 工具函数
│   │   ├── api_monitor.py    # API监控
│   │   ├── performance.py    # 性能优化
│   │   └── error_handler.py  # 错误处理
│   └── config/         # 配置文件
│       └── config_manager.py # 配置管理器
├── tests/              # 测试代码
├── docs/               # 文档
├── logs/               # 日志文件
├── requirements.txt    # 依赖管理
└── README.md          # 项目说明
```

## 安装说明

1. 克隆项目：
```bash
git clone [项目地址]
cd package_machine
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置DeepSeek API：
   - 在[DeepSeek官网](https://deepseek.com)注册并获取API密钥
   - 在程序设置中配置API密钥

## 使用说明

### 1. 基本使用
1. 启动程序：
```bash
python src/main.py
```

2. 首次使用配置：
   - 点击"工具" -> "设置"
   - 在"AI设置"标签页配置DeepSeek API密钥
   - 在"文件类型"标签页配置需要处理的文件类型

3. 文件分类：
   - 点击"选择文件夹"按钮选择要处理的目录
   - 使用文件类型过滤器筛选文件（可选）
   - 点击"开始分类"按钮开始自动分类
   - 查看分类结果并确认

### 2. 高级功能
- **自定义分类规则**：可以在设置中调整分类数量范围
- **性能监控**：通过右侧面板实时监控系统资源使用情况
- **API使用统计**：查看API调用次数、Token使用量和成本统计
- **文件备份**：可以在设置中启用自动备份功能
- **批量处理**：支持同时处理多个文件，自动进行分类

### 3. 界面说明
- **主界面**：显示文件列表和分类结果
- **工具栏**：提供常用功能快捷访问
- **状态栏**：显示处理进度和系统状态
- **监控面板**：显示系统性能和API使用情况

## 常见问题

1. **API密钥配置**
   - 问题：提示"未设置DeepSeek API密钥"
   - 解决：在设置中配置有效的API密钥

2. **文件类型支持**
   - 问题：某些文件无法分类
   - 解决：检查文件类型是否在支持列表中

3. **性能优化**
   - 问题：处理大量文件时性能下降
   - 解决：调整批处理大小，启用性能优化选项

## 开发说明

1. 运行测试：
```bash
pytest tests/
```

2. 生成测试覆盖率报告：
```bash
pytest --cov=src tests/
```

3. 代码风格检查：
```bash
flake8 src/
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 更新日志

### v1.0.0 (2024-01-04)
- 初始版本发布
- 基本文件分类功能
- iOS风格界面
- DeepSeek AI集成

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者：[维护者姓名]
- 邮箱：[联系邮箱]
- 项目主页：[项目URL]

## 致谢

- DeepSeek AI 提供的强大API支持
- PyQt5 提供的GUI框架支持
- 所有项目贡献者 