import os
import sys
import shutil
from datetime import datetime
from PyInstaller.__main__ import run as pyinstaller_run

def clean_build():
    """清理构建文件夹"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # 清理 .spec 文件
    spec_file = 'package_machine.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)

def create_version_file():
    """创建版本信息文件"""
    version = '1.0.0'  # 你可以根据需要修改版本号
    build_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    version_info = f"""
VERSION = '{version}'
BUILD_TIME = '{build_time}'
"""
    
    with open('src/version.py', 'w', encoding='utf-8') as f:
        f.write(version_info)

def create_default_config():
    """创建默认配置文件（不包含敏感信息）"""
    default_config = {
        "app_name": "Package Machine",
        "language": "zh_CN",
        "theme": "light",
        "max_recent_files": 10,
        "auto_save": True,
        "save_interval": 300,
        "log_level": "INFO"
    }
    
    import json
    with open('src/default_config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)

def build():
    """打包应用程序"""
    try:
        # 清理旧的构建文件
        clean_build()
        
        # 创建版本信息
        create_version_file()
        
        # 创建默认配置文件
        create_default_config()
        
        # PyInstaller 参数
        pyinstaller_args = [
            'src/main.py',  # 主程序入口
            '--name=package_machine',
            '--windowed',  # 使用 GUI 模式
            '--add-data=src/default_config.json;src/default_config.json',  # 只添加默认配置
            '--noconfirm',
            '--clean',
            '--hidden-import=PyQt5',
            '--hidden-import=PyQt5.QtChart',  # 修正 PyQtChart 的导入
            '--hidden-import=src'
        ]
        
        # 执行打包
        pyinstaller_run(pyinstaller_args)
        
        print("打包完成！输出文件在 dist/package_machine 目录下")
        print("注意：用户配置文件将在程序首次运行时在用户目录下创建")
        
    except Exception as e:
        print(f"打包过程中出错: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build() 