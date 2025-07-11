#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化打包脚本
一键构建小红书发布工具的可执行文件
"""
import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path
from datetime import datetime

class XhsPublisherBuilder:
    """小红书发布工具构建器"""
    
    def __init__(self, packaging_dir: Path):
        self.packaging_dir = packaging_dir
        self.project_root = packaging_dir.parent
        self.dist_dir = packaging_dir / "dist"
        self.build_dir = packaging_dir / "build"
        self.temp_dir = packaging_dir / "temp"
        
        # 平台信息
        self.platform = platform.system().lower()
        self.is_mac = self.platform == "darwin"
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        
        # 构建配置
        self.spec_file = packaging_dir / "xhs_publisher.spec"
        self.requirements_file = packaging_dir / "build_requirements.txt"
        
    def check_prerequisites(self) -> bool:
        """检查构建前提条件"""
        print("🔍 检查构建前提条件...")
        
        issues = []
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"Python版本过低: {python_version}, 需要3.8+")
        else:
            print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查虚拟环境
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            issues.append("未在虚拟环境中运行，请先激活虚拟环境")
        else:
            print(f"✅ 虚拟环境: {sys.prefix}")
        
        # 检查必要文件
        required_files = [
            self.project_root / "main.py",
            self.project_root / "requirements.txt",
            self.spec_file,
            self.requirements_file
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                issues.append(f"缺少必要文件: {file_path}")
            else:
                print(f"✅ 文件存在: {file_path.name}")
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller: {PyInstaller.__version__}")
        except ImportError:
            issues.append("PyInstaller未安装")
        
        if issues:
            print("\n❌ 发现问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        print("✅ 所有前提条件满足")
        return True
    
    def install_dependencies(self):
        """安装打包依赖"""
        print("📦 安装打包依赖...")
        
        try:
            # 安装PyInstaller（如果还没安装）
            subprocess.run([
                sys.executable, "-m", "pip", "install", "PyInstaller>=6.0.0"
            ], check=True)
            
            # 安装其他打包依赖
            if self.requirements_file.exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
                ], check=True)
            
            # 确保Playwright浏览器已安装
            subprocess.run([
                sys.executable, "-m", "playwright", "install", "firefox"
            ], check=True)
            
            print("✅ 依赖安装完成")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            raise
    
    def clean_build_dirs(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir, self.temp_dir]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  清理: {dir_path}")
        
        # 重新创建目录
        for dir_path in dirs_to_clean:
            dir_path.mkdir(exist_ok=True)
        
        print("✅ 构建目录清理完成")
    
    def prepare_resources(self):
        """准备资源文件"""
        print("📁 准备资源文件...")
        
        # 确保resources目录存在
        resources_dir = self.packaging_dir / "resources"
        resources_dir.mkdir(exist_ok=True)
        
        # 复制示例图片
        images_src = self.project_root / "images"
        images_dst = resources_dir / "images"
        if images_src.exists():
            if images_dst.exists():
                shutil.rmtree(images_dst)
            shutil.copytree(images_src, images_dst)
            print(f"  复制: {images_src} -> {images_dst}")
        
        # 复制配置文件模板
        config_src = self.project_root / "config.json"
        config_dst = resources_dir / "config.json"
        if config_src.exists():
            shutil.copy2(config_src, config_dst)
            print(f"  复制: {config_src} -> {config_dst}")
        
        print("✅ 资源文件准备完成")
    
    def run_pyinstaller(self, debug: bool = False, console: bool = False):
        """运行PyInstaller"""
        print("🔨 开始PyInstaller构建...")
        
        # 如果需要控制台输出，使用特殊的 spec 文件
        if console:
            console_spec = self.spec_file.with_name("xhs_publisher_console.spec")
            if not console_spec.exists():
                # 创建控制台版本的 spec 文件
                self._create_console_spec()
            spec_file = console_spec
        else:
            spec_file = self.spec_file
        
        # 构建命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            str(spec_file),
            "--clean",
            "--noconfirm",
        ]
        
        if debug:
            cmd.extend(["--debug", "all"])
        
        # 设置工作目录
        original_cwd = os.getcwd()
        os.chdir(self.packaging_dir)
        
        try:
            # 运行PyInstaller
            print(f"执行命令: {' '.join(cmd)}")
            print(f"工作目录: {os.getcwd()}")
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print("✅ PyInstaller构建成功")
            if debug and result.stdout:
                print("构建输出:")
                print(result.stdout)
                
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller构建失败: {e}")
            if e.stdout:
                print("标准输出:")
                print(e.stdout)
            if e.stderr:
                print("错误输出:")
                print(e.stderr)
            raise
        finally:
            os.chdir(original_cwd)
    
    def post_build_processing(self):
        """构建后处理"""
        print("🔧 构建后处理...")
        
        # 检查构建结果
        if self.is_mac:
            app_path = self.dist_dir / "XhsPublisher.app"
            if app_path.exists():
                print(f"✅ macOS应用创建成功: {app_path}")
                
                # 设置执行权限
                executable_path = app_path / "Contents" / "MacOS" / "XhsPublisher"
                if executable_path.exists():
                    executable_path.chmod(0o755)
                    print("  设置执行权限")
            else:
                print("❌ macOS应用创建失败")
                
        elif self.is_windows:
            exe_path = self.dist_dir / "XhsPublisher.exe"
            if exe_path.exists():
                print(f"✅ Windows应用创建成功: {exe_path}")
            else:
                print("❌ Windows应用创建失败")
        
        else:  # Linux
            exe_path = self.dist_dir / "XhsPublisher"
            if exe_path.exists():
                print(f"✅ Linux应用创建成功: {exe_path}")
                # 设置执行权限
                exe_path.chmod(0o755)
                print("  设置执行权限")
            else:
                print("❌ Linux应用创建失败")
    
    def _create_console_spec(self):
        """创建控制台版本的 spec 文件"""
        print("📝 创建控制台版本的 spec 文件...")
        
        # 读取原始 spec 文件
        original_spec = self.spec_file.read_text()
        
        # 修改为控制台版本
        console_spec = original_spec.replace('console=False,', 'console=True,')
        console_spec = console_spec.replace('--windows-disable-console', '# --windows-disable-console')
        
        # 写入新文件
        console_spec_file = self.spec_file.with_name("xhs_publisher_console.spec")
        console_spec_file.write_text(console_spec)
        
        print(f"✅ 控制台 spec 文件创建成功: {console_spec_file}")
    
    def create_installer(self):
        """创建安装包（可选）"""
        print("📦 创建安装包...")
        
        if self.is_mac:
            # macOS: 创建DMG（需要额外工具）
            print("💡 macOS DMG创建需要额外工具，跳过")
            
        elif self.is_windows:
            # Windows: 创建安装程序（需要NSIS或Inno Setup）
            print("💡 Windows安装程序创建需要额外工具，跳过")
        
        else:
            # Linux: 创建AppImage或DEB（需要额外工具）
            print("💡 Linux包创建需要额外工具，跳过")
        
        print("💡 提示: 可以手动创建安装包")
    
    def show_build_summary(self):
        """显示构建摘要"""
        print("\n" + "=" * 60)
        print("📋 构建摘要")
        print("=" * 60)
        
        print(f"构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"平台: {platform.platform()}")
        print(f"Python版本: {sys.version}")
        
        # 检查输出文件
        print("\n📁 输出文件:")
        if self.dist_dir.exists():
            for item in self.dist_dir.iterdir():
                size_mb = self._get_size_mb(item)
                print(f"  {item.name} ({size_mb:.1f} MB)")
        
        print(f"\n📍 输出目录: {self.dist_dir}")
        print("\n🎉 构建完成！")
    
    def _get_size_mb(self, path: Path) -> float:
        """获取文件或目录大小（MB）"""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)
        elif path.is_dir():
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            return total_size / (1024 * 1024)
        return 0.0
    
    def build(self, debug: bool = False, clean: bool = True, console: bool = False):
        """执行完整构建流程"""
        print("🚀 开始构建小红书发布工具")
        if console:
            print("🖥️  构建控制台版本（带调试输出）")
        print("=" * 60)
        
        try:
            # 1. 检查前提条件
            if not self.check_prerequisites():
                return False
            
            # 2. 安装依赖
            self.install_dependencies()
            
            # 3. 清理构建目录
            if clean:
                self.clean_build_dirs()
            
            # 4. 准备资源
            self.prepare_resources()
            
            # 5. 运行PyInstaller
            self.run_pyinstaller(debug=debug, console=console)
            
            # 6. 构建后处理
            self.post_build_processing()
            
            # 7. 创建安装包（可选）
            # self.create_installer()
            
            # 8. 显示摘要
            self.show_build_summary()
            
            return True
            
        except Exception as e:
            print(f"\n❌ 构建失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="小红书发布工具构建脚本")
    parser.add_argument("--platform", choices=["mac", "windows", "linux", "all"], 
                      default="current", help="目标平台")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--no-clean", action="store_true", help="不清理构建目录")
    parser.add_argument("--deps-only", action="store_true", help="仅安装依赖")
    parser.add_argument("--console", action="store_true", help="构建控制台版本（带调试输出）")
    
    args = parser.parse_args()
    
    # 获取脚本目录
    script_dir = Path(__file__).parent
    
    # 创建构建器
    builder = XhsPublisherBuilder(script_dir)
    
    if args.deps_only:
        # 仅安装依赖
        print("📦 仅安装依赖模式")
        if builder.check_prerequisites():
            builder.install_dependencies()
            print("✅ 依赖安装完成")
        return
    
    # 执行构建
    success = builder.build(
        debug=args.debug,
        clean=not args.no_clean,
        console=args.console
    )
    
    if success:
        print("\n🎉 构建成功！")
        if args.console:
            print("💡 提示：控制台版本会显示终端窗口，适合调试使用")
        sys.exit(0)
    else:
        print("\n❌ 构建失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()