"""
AstrBot Block Editor - Scratch风格可视化编辑器桌面应用
使用PyQt5 + QWebEngineView套壳Web界面
"""
import sys
import json
from pathlib import Path
from PyQt5.QtCore import Qt, QUrl, pyqtSlot, QVariant, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QIcon, QPixmap

# 添加编译器路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from compiler import BlockCompiler


class PyBridge(QObject):
    """JavaScript与Python通信桥接"""
    
    resultReady = pyqtSignal(str)
    
    def __init__(self, compiler: BlockCompiler, parent=None):
        super().__init__(parent)
        self.compiler = compiler
        self.window = None
    
    @pyqtSlot(str, result=str)
    def compile(self, workflow_json):
        """编译工作流"""
        try:
            result = self.compiler.compile_string(workflow_json)
            response = {
                'success': result['success'],
                'code': result['files'].get('main.py', ''),
                'errors': result.get('errors', [])
            }
            return json.dumps(response, ensure_ascii=False)
        except Exception as e:
            return json.dumps({'success': False, 'code': '', 'errors': [str(e)]})
    
    @pyqtSlot(str, result=bool)
    def save(self, workflow_json):
        """保存工作流"""
        try:
            data = json.loads(workflow_json)
            name = data.get('metadata', {}).get('name', 'workflow')
            
            path, _ = QFileDialog.getSaveFileName(
                self.window, "保存工作流", f"{name}.json", "JSON Files (*.json)"
            )
            
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(workflow_json)
                return True
            return False
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    @pyqtSlot(result=str)
    def open(self):
        """打开工作流"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.window, "打开工作流", "", "JSON Files (*.json)"
            )
            
            if path:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            print(f"打开失败: {e}")
            return ""
    
    @pyqtSlot(str, result=bool)
    def export(self, workflow_json):
        """导出插件"""
        try:
            path = QFileDialog.getExistingDirectory(self.window, "选择导出目录")
            
            if path:
                # 临时保存工作流
                temp_path = Path(path) / "temp_workflow.json"
                temp_path.write_text(workflow_json, encoding='utf-8')
                
                # 编译
                result = self.compiler.compile_file(str(temp_path), path)
                
                # 删除临时文件
                temp_path.unlink()
                
                if result['success']:
                    QMessageBox.information(self.window, "导出成功", f"插件已导出到: {result['output_dir']}")
                    return True
                else:
                    QMessageBox.critical(self.window, "导出失败", "\n".join(result['errors']))
                    return False
            return False
        except Exception as e:
            print(f"导出失败: {e}")
            QMessageBox.critical(self.window, "导出失败", str(e))
            return False


class BlockEditorWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.compiler = BlockCompiler()
        self.bridge = PyBridge(self.compiler)
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("AstrBot Block Editor - 可视化插件开发工具")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1024, 700)
        
        # 设置窗口图标
        icon_path = Path(__file__).parent / "icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建Web视图
        self.browser = QWebEngineView()
        
        # 设置Web通道
        channel = QWebChannel()
        channel.registerObject('pybridge', self.bridge)
        self.browser.page().setWebChannel(channel)
        
        # 设置桥接窗口引用
        self.bridge.window = self
        
        # 加载本地HTML
        web_path = Path(__file__).parent / "web" / "index.html"
        self.browser.setUrl(QUrl.fromLocalFile(str(web_path)))
        
        # 设置中央部件
        self.setCentralWidget(self.browser)


def main():
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = BlockEditorWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
