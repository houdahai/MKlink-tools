import os
import sys
import ctypes
import ctypes.wintypes
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QFont, QColor, QCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar, QStackedWidget,
    QFileDialog, QMessageBox, QFrame, QTextBrowser, QGraphicsDropShadowEffect
)

import json

# 导入核心逻辑引擎
import mklink_engine

# --- 全局精致 QSS 样式表 ---
STYLESHEET = """
QMainWindow {
    background-color: #121218;
}

QWidget {
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    color: #e2e2e9;
    font-size: 14px;
}

/* 顶部导航条 */
#NavBar {
    background-color: #1a1a24;
    border-bottom: 1px solid #2d2d3d;
    min-height: 55px;
}

#AppTitle {
    font-size: 18px;
    font-weight: bold;
    color: #00a8ff;
    margin-left: 15px;
}

/* 权限角标 */
#AuthBadge {
    font-size: 12px;
    font-weight: bold;
    border-radius: 4px;
    padding: 4px 10px;
    margin-right: 15px;
}

.BadgeAdmin {
    background-color: rgba(46, 204, 113, 0.15);
    color: #2ecc71;
    border: 1px solid rgba(46, 204, 113, 0.3);
}

.BadgeUser {
    background-color: rgba(241, 196, 15, 0.15);
    color: #f1c40f;
    border: 1px solid rgba(241, 196, 15, 0.3);
}

/* 导航按钮 */
.NavButton {
    background-color: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 15px;
    font-weight: bold;
    color: #a0a0b0;
}

.NavButton:hover {
    color: #ffffff;
    background-color: rgba(255, 255, 255, 0.05);
}

.NavButton[active="true"] {
    color: #00a8ff;
    border-bottom: 2px solid #00a8ff;
}

/* 内容卡片 */
.ContentCard {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 8px;
}

/* 输入框 */
QLineEdit {
    background-color: #252535;
    border: 1px solid #3d3d52;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #00a8ff;
}

QLineEdit:focus {
    border: 1px solid #00a8ff;
    background-color: #2b2b3d;
}

/* 浏览按钮 */
.BrowseButton {
    background-color: #2b2b3d;
    border: 1px solid #3d3d52;
    border-radius: 6px;
    padding: 8px 15px;
    color: #e2e2e9;
}

.BrowseButton:hover {
    background-color: #383850;
    border-color: #00a8ff;
}

/* 主操作按钮 */
.PrimaryButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d4, stop:1 #00a8ff);
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    color: #ffffff;
    font-weight: bold;
    font-size: 15px;
}

.PrimaryButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0084ff, stop:1 #33beff);
}

.PrimaryButton:pressed {
    background-color: #005a9e;
}

.PrimaryButton:disabled {
    background-color: #2d2d3d;
    color: #707080;
}

/* 绿色/警告/解绑按钮 */
.DangerButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e67e22, stop:1 #e74c3c);
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    color: #ffffff;
    font-weight: bold;
    font-size: 15px;
}

.DangerButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f39c12, stop:1 #ff7675);
}

.DangerButton:pressed {
    background-color: #c0392b;
}

.GreenButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #27ae60, stop:1 #2ecc71);
    border: none;
    border-radius: 6px;
    padding: 12px 24px;
    color: #ffffff;
    font-weight: bold;
    font-size: 15px;
}

.GreenButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #55efc4);
}

/* 下拉菜单 */
QComboBox {
    background-color: #252535;
    border: 1px solid #3d3d52;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
}

QComboBox:focus {
    border-color: #00a8ff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a24;
    border: 1px solid #3d3d52;
    selection-background-color: #00a8ff;
    selection-color: #ffffff;
}

/* 进度条 */
QProgressBar {
    background-color: #252535;
    border: 1px solid #3d3d52;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
    border-radius: 5px;
}

/* 控制台输出区 */
QTextBrowser {
    background-color: #0c0c10;
    border: 1px solid #232330;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 13px;
    padding: 10px;
    color: #00ff66;
}
"""

# --- 解决管理员权限高特权下拖放过滤(UIPI)的底层消息白名单函数 ---
def exempt_drag_drop_uipi():
    try:
        user32 = ctypes.windll.user32
        user32.ChangeWindowMessageFilter(0x0233, 1)  # WM_DROPFILES
        user32.ChangeWindowMessageFilter(0x004A, 1)  # WM_COPYDATA
        user32.ChangeWindowMessageFilter(0x0049, 1)  # WM_COPYGLOBALMEM
        print("✔ 成功配置全局进程级 UIPI 拖拽豁免过滤器")
    except Exception as e:
        print(f"豁免进程级 UIPI 拖放消息失败: {e}")


# --- 自定义智能拖放输入框控件 ---
class DragDropLineEdit(QLineEdit):
    """
    【高阶交互组件】支持直接拖拽文件或文件夹录入的 LineEdit 输入框。
    在普通权限下以 OLE 拖放工作，在高特权下由 nativeEvent 消息映射机制降级接管。
    """
    path_dropped = Signal(str)

    def __init__(self, parent=None, placeholder=""):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        # 如果是管理员权限运行，禁用 OLE 拖放注册，迫使系统退化降级到物理 WM_DROPFILES
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        self.setAcceptDrops(not is_admin)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                path = os.path.abspath(paths[0])
                self.setText(path)
                self.path_dropped.emit(path)
                event.acceptProposedAction()


# --- 自定义色彩分流拖拽热区卡片 ---
class ColorDragDropFrame(QFrame):
    """
    具有高亮微动画和定制化边框/背景的智能拖放卡片控件，实现无歧义拖放分流。
    """
    path_dropped = Signal(str)

    def __init__(self, parent=None, title="", desc="", color="#00a8ff", bg_rgba="rgba(0, 168, 255, 0.03)", icon="📂"):
        super().__init__(parent)
        self.title_text = title
        self.desc_text = desc
        self.color_hex = color
        self.bg_rgba = bg_rgba
        self.icon_emoji = icon
        
        self.setObjectName("ColorDragZone")
        # 如果是管理员权限运行，禁用 OLE 拖放注册，迫使系统退化降级到物理 WM_DROPFILES
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        self.setAcceptDrops(not is_admin)
        self.setProperty("dragged", "false")
        
        self.update_style()
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel(self.icon_emoji, self)
        self.icon_label.setStyleSheet("font-size: 26px; margin-bottom: 2px;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(self.title_text, self)
        self.title_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {self.color_hex};")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.desc_label = QLabel(self.desc_text, self)
        self.desc_label.setStyleSheet("font-size: 11px; color: #8888a0; margin-top: 1px;")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

    def update_style(self):
        style = f"""
        #ColorDragZone {{
            border: 2px dashed {self.color_hex}aa;
            border-radius: 8px;
            background-color: {self.bg_rgba};
        }}
        #ColorDragZone[dragged="true"] {{
            border: 2px dashed {self.color_hex};
            background-color: {self.color_hex}15;
        }}
        """
        self.setStyleSheet(style)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragged", "true")
            self.update_style()
            self.desc_label.setText("松开鼠标立即录入")
            self.desc_label.setStyleSheet(f"font-size: 11px; color: {self.color_hex}; font-weight: bold;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragged", "false")
        self.update_style()
        self.desc_label.setText(self.desc_text)
        self.desc_label.setStyleSheet("font-size: 11px; color: #8888a0;")

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragged", "false")
        self.update_style()
        self.desc_label.setText(self.desc_text)
        self.desc_label.setStyleSheet("font-size: 11px; color: #8888a0;")
        
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                path = os.path.abspath(paths[0])
                self.path_dropped.emit(path)
                event.acceptProposedAction()


# --- 自定义紧凑级拖放卡片控件 ---
class MiniDragZone(QFrame):
    """
    【高颜值紧凑拖拽热区】
    专为左侧表单输入项定制的微型拖拽辅助卡片，提供显眼的虚线框与悬停高亮动画。
    """
    path_dropped = Signal(str)

    def __init__(self, parent=None, text="拖拽文件夹到此处快速录入", color="#00a8ff", bg_rgba="rgba(0, 168, 255, 0.03)", icon="📥"):
        super().__init__(parent)
        self.text = text
        self.color_hex = color
        self.bg_rgba = bg_rgba
        self.icon_emoji = icon
        
        self.setObjectName("MiniDragZone")
        # 如果是管理员权限运行，禁用 OLE 拖放注册，迫使系统退化降级到物理 WM_DROPFILES
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        self.setAcceptDrops(not is_admin)
        self.setProperty("dragged", "false")
        self.setFixedHeight(40)
        
        self.update_style()
        
        # 水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel(self.icon_emoji, self)
        self.icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.icon_label)
        
        self.text_label = QLabel(self.text, self)
        self.text_label.setStyleSheet(f"font-size: 11px; color: {self.color_hex}; font-weight: 500;")
        layout.addWidget(self.text_label)

    def update_style(self):
        style = f"""
        #MiniDragZone {{
            border: 1.5px dashed {self.color_hex}bb;
            border-radius: 6px;
            background-color: {self.bg_rgba};
        }}
        #MiniDragZone[dragged="true"] {{
            border: 1.5px dashed {self.color_hex};
            background-color: {self.color_hex}18;
        }}
        """
        self.setStyleSheet(style)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragged", "true")
            self.update_style()
            self.text_label.setText("松开鼠标立即录入 ⚡")
            self.text_label.setStyleSheet(f"font-size: 11px; color: {self.color_hex}; font-weight: bold;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragged", "false")
        self.update_style()
        self.text_label.setText(self.text)
        self.text_label.setStyleSheet(f"font-size: 11px; color: {self.color_hex}; font-weight: 500;")

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragged", "false")
        self.update_style()
        self.text_label.setText(self.text)
        self.text_label.setStyleSheet(f"font-size: 11px; color: {self.color_hex}; font-weight: 500;")
        
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
            if paths:
                path = os.path.abspath(paths[0])
                self.path_dropped.emit(path)
                event.acceptProposedAction()


# --- 后台异步“极速搬家”线程类 ---
class MigrationThread(QThread):
    progress_signal = Signal(str, int)
    finished_signal = Signal(bool, str)

    def __init__(self, source, dest):
        super().__init__()
        self.source = source
        self.dest = dest

    def run(self):
        def callback(status_text, percent):
            self.progress_signal.emit(status_text, percent)
            
        success, message = mklink_engine.safe_migrate_and_link(self.source, self.dest, callback)
        self.finished_signal.emit(success, message)


# --- 后台异步“一键彻底还原”线程类 ---
class RestoreThread(QThread):
    progress_signal = Signal(str, int)
    finished_signal = Signal(bool, str)

    def __init__(self, link_path):
        super().__init__()
        self.link_path = link_path

    def run(self):
        def callback(status_text, percent):
            self.progress_signal.emit(status_text, percent)
            
        success, message = mklink_engine.safe_restore_and_remove_link(self.link_path, callback)
        self.finished_signal.emit(success, message)


# --- 界面主窗口类 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows MKlink 极速助手 v1.5 [建立链接持久越狱版]")
        self.resize(800, 600)
        self.setMinimumSize(740, 550)
        self.config_path = os.path.expanduser("~/.mklink_helper_config.json")
        
        # 如果是普通权限运行，必须激活顶级主窗口自身的 OLE 拖放注册，从而让所有子控件的拖拽机制全线激活！
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        self.setAcceptDrops(not is_admin)
        
        self.init_ui()
        self.load_config()
        self.bind_config_signals()
        self.update_admin_status()

    def save_config(self):
        """将当前界面的输入数据和设置实时静默保存至 AppData"""
        try:
            config_data = {
                "mig_src": self.mig_src_input.text(),
                "mig_dst": self.mig_dst_input.text(),
                "adv_link": self.adv_link_input.text(),
                "adv_target": self.adv_target_input.text(),
                "rest_link": self.rest_link_input.text(),
                "adv_type_idx": self.adv_type_combo.currentIndex()
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("保存配置失败:", e)

    def load_config(self):
        """启动时自动加载并恢复上一次录入的数据与设置"""
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 临时阻断信号，防止 setText 触发 save_config 死循环
            self.mig_src_input.blockSignals(True)
            self.mig_dst_input.blockSignals(True)
            self.adv_link_input.blockSignals(True)
            self.adv_target_input.blockSignals(True)
            self.rest_link_input.blockSignals(True)
            self.adv_type_combo.blockSignals(True)
            
            self.mig_src_input.setText(config_data.get("mig_src", ""))
            self.mig_dst_input.setText(config_data.get("mig_dst", ""))
            self.adv_link_input.setText(config_data.get("adv_link", ""))
            self.adv_target_input.setText(config_data.get("adv_target", ""))
            self.rest_link_input.setText(config_data.get("rest_link", ""))
            self.adv_type_combo.setCurrentIndex(config_data.get("adv_type_idx", 0))
            
            # 恢复信号
            self.mig_src_input.blockSignals(False)
            self.mig_dst_input.blockSignals(False)
            self.adv_link_input.blockSignals(False)
            self.adv_target_input.blockSignals(False)
            self.rest_link_input.blockSignals(False)
            self.adv_type_combo.blockSignals(False)
            
            self.log("📂 [数据恢复] 成功恢复上一次录入的数据与设置！", "#f1c40f")
        except Exception as e:
            print("恢复配置失败:", e)

    def bind_config_signals(self):
        """将界面中所有输入和选项的变化信号绑定至实时保存配置"""
        self.mig_src_input.textChanged.connect(self.save_config)
        self.mig_dst_input.textChanged.connect(self.save_config)
        self.adv_link_input.textChanged.connect(self.save_config)
        self.adv_target_input.textChanged.connect(self.save_config)
        self.rest_link_input.textChanged.connect(self.save_config)
        self.adv_type_combo.currentIndexChanged.connect(self.save_config)

    def init_ui(self):
        # 主中心部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 整体纵向布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 顶部状态/导航栏
        self.create_navbar()
        main_layout.addWidget(self.nav_bar)
        
        # 2. 中间主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # 左侧功能卡片区域 (QStackedWidget)
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setStyleSheet("background-color: transparent;")
        
        # 调换顺序，建立链接为首要默认 Tab 页面
        self.create_advanced_tab()
        self.create_migration_tab()
        self.create_restore_tab()
        
        self.stacked_widget.addWidget(self.advanced_widget)
        self.stacked_widget.addWidget(self.migration_widget)
        self.stacked_widget.addWidget(self.restore_widget)
        
        # 右侧拖拽分流及日志面板
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        info_label = QLabel("📚 四种链接核心科普与避坑指南:", self)
        info_label.setStyleSheet("font-weight: bold; color: #00a8ff;")
        right_panel.addWidget(info_label)
        
        self.info_browser = QTextBrowser(self)
        self.info_browser.setStyleSheet(
            "background-color: #161622;"
            "border: 1px solid #2d2d3d;"
            "border-radius: 8px;"
            "padding: 8px;"
        )
        
        info_html = """
        <div style="font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; line-height: 1.5; color: #d0d0e0;">
            <table border="1" cellpadding="5" cellspacing="0" style="border-color: #2d2d3d; width: 100%; border-collapse: collapse; text-align: left; font-size: 11px;">
                <tr style="background-color: #2b2b3d; color: #ffffff;">
                    <th style="padding: 5px;">链接类型</th>
                    <th style="padding: 5px;">对象</th>
                    <th style="padding: 5px;">跨盘</th>
                    <th style="padding: 5px;">管理员</th>
                    <th style="padding: 5px;">经典场景</th>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>目录联接<br>(Junction /J)</b></td>
                    <td style="padding: 5px;">目录</td>
                    <td style="padding: 5px; color: #2ecc71;">✅ 支持</td>
                    <td style="padding: 5px; color: #e74c3c;">❌ 否</td>
                    <td style="padding: 5px; font-size: 10px;">微信数据、游戏迁移 (最实用)</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>目录符号链接<br>(Symlink /D)</b></td>
                    <td style="padding: 5px;">目录</td>
                    <td style="padding: 5px; color: #2ecc71;">✅ 支持</td>
                    <td style="padding: 5px; color: #f1c40f;">⚠️ 是</td>
                    <td style="padding: 5px; font-size: 10px;">局域网共享映射、跨设备链接</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>文件符号链接<br>(Symlink)</b></td>
                    <td style="padding: 5px;">文件</td>
                    <td style="padding: 5px; color: #2ecc71;">✅ 支持</td>
                    <td style="padding: 5px; color: #f1c40f;">⚠️ 是</td>
                    <td style="padding: 5px; font-size: 10px;">配置文件指向、系统级依赖重定向</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>文件硬链接<br>(Hardlink /H)</b></td>
                    <td style="padding: 5px;">文件</td>
                    <td style="padding: 5px; color: #e74c3c;">❌ 否</td>
                    <td style="padding: 5px; color: #e74c3c;">❌ 否</td>
                    <td style="padding: 5px; font-size: 10px;">节省空间的文件多处挂载</td>
                </tr>
            </table>
            <h4 style="color: #00a8ff; margin-top: 10px; margin-bottom: 4px; font-size: 12px;">⚠️ 核心避坑与操作要点</h4>
            <ul style="margin: 0; padding-left: 15px; font-size: 11px; color: #b0b0c0;">
                <li><b>路径不能预先存在:</b> 创建链接时，<b>“生成的链接路径”</b>在命令执行前<b>必须不存在</b>，而<b>“数据目标路径”</b>必须已存在。</li>
                <li><b>就近拖拽智能拼装:</b> 在建立链接模式下，将父目录拖入“生成的链接路径”微型卡片上，工具会自动在尾部智能追加提取的原始文件夹名称！</li>
                <li><b>双保险反向数据还原:</b> 还原页面支持“一键还原反向迁移”功能，采用后台高安全多线程拷回与比对，故障时可自动回滚并重建链接，数据100%安全。</li>
            </ul>
        </div>
        """
        self.info_browser.setHtml(info_html)
        right_panel.addWidget(self.info_browser, stretch=6)
        
        log_label = QLabel("📢 状态与命令日志:", self)
        log_label.setStyleSheet("font-weight: bold; color: #8888a0;")
        right_panel.addWidget(log_label)
        
        self.log_browser = QTextBrowser(self)
        self.log_browser.setHtml(
            "<span style='color: #8888a0;'>[系统就绪]</span> 欢迎使用 MKlink 极速助手！<br>"
            "🛡️ <b>越狱免拦截激活</b>：管理员权限下拖拽已被 100% 内核穿透接管！拖放畅通无阻！<br>"
            "🎯 <b>建立链接智能拼装</b>：把“父文件夹”拖入【生成的链接路径】微型框中，它将自动读取并追加目标文件夹的原始名称！"
        )
        right_panel.addWidget(self.log_browser, stretch=4)
        
        # 将左侧卡片与右侧面板放入内容区
        content_layout.addWidget(self.stacked_widget, stretch=5)
        content_layout.addLayout(right_panel, stretch=4)
        
        main_layout.addLayout(content_layout)

    def create_navbar(self):
        self.nav_bar = QWidget(self)
        self.nav_bar.setObjectName("NavBar")
        
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        
        # 标题
        title_label = QLabel("🔗 MKlink 极速助手", self)
        title_label.setObjectName("AppTitle")
        nav_layout.addWidget(title_label)
        
        nav_layout.addStretch()
        
        # 导航按钮
        self.nav_btn1 = QPushButton("🔗 建立链接模式", self)
        self.nav_btn1.setObjectName("NavBtn1")
        self.nav_btn1.setProperty("active", "true")
        self.nav_btn1.setProperty("class", "NavButton")
        self.nav_btn1.clicked.connect(lambda: self.switch_tab(0))
        nav_layout.addWidget(self.nav_btn1)
        
        self.nav_btn2 = QPushButton("🚀 极速数据搬家", self)
        self.nav_btn2.setObjectName("NavBtn2")
        self.nav_btn2.setProperty("active", "false")
        self.nav_btn2.setProperty("class", "NavButton")
        self.nav_btn2.clicked.connect(lambda: self.switch_tab(1))
        nav_layout.addWidget(self.nav_btn2)
        
        self.nav_btn_restore = QPushButton("🔄 还原与解绑", self)
        self.nav_btn_restore.setObjectName("NavBtnRestore")
        self.nav_btn_restore.setProperty("active", "false")
        self.nav_btn_restore.setProperty("class", "NavButton")
        self.nav_btn_restore.clicked.connect(lambda: self.switch_tab(2))
        nav_layout.addWidget(self.nav_btn_restore)
        
        nav_layout.addStretch()
        
        # 权限角标 (已隐藏，净化主导航栏界面)
        self.auth_badge = QPushButton(self)
        self.auth_badge.setObjectName("AuthBadge")
        self.auth_badge.clicked.connect(self.request_uac)
        self.auth_badge.hide()

    def create_migration_tab(self):
        """创建“极速搬家”功能页面"""
        self.migration_widget = QWidget(self)
        self.migration_widget.setProperty("class", "ContentCard")
        self.migration_widget.setStyleSheet("#MigrationCard { background-color: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; }")
        self.migration_widget.setObjectName("MigrationCard")
        
        layout = QVBoxLayout(self.migration_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("🚀 一键极速迁移并建立链接 (C盘空间终结者)", self)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00a8ff;")
        layout.addWidget(title)
        
        desc = QLabel("用法：自动将C盘或其他盘的【源大文件夹】数据完整剪切移入【目标父文件夹】下，并在原位置创建 Directory Junction 联接。系统、微信、游戏读取路径完全不变！", self)
        desc.setStyleSheet("color: #8888a0; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # 源目录输入区
        layout.addWidget(QLabel("📂 1. 需要搬迁的源大文件夹 (如微信数据目录):", self))
        src_layout = QHBoxLayout()
        self.mig_src_input = DragDropLineEdit(self, "直接将源文件夹拖入此处，或点击浏览...")
        self.mig_src_input.path_dropped.connect(lambda path: self.log(f"📥 [源路径录入] 填入: {path}"))
        self.mig_src_browse = QPushButton("浏览...", self)
        self.mig_src_browse.setProperty("class", "BrowseButton")
        self.mig_src_browse.clicked.connect(self.browse_mig_src)
        src_layout.addWidget(self.mig_src_input)
        src_layout.addWidget(self.mig_src_browse)
        layout.addLayout(src_layout)
        
        # 新增源大文件夹专属微型拖拽虚线卡片
        self.mig_src_drag = MiniDragZone(self, "拖拽 [源大文件夹] 到此处快速录入", "#00a8ff", "rgba(0, 168, 255, 0.03)", "📂")
        self.mig_src_drag.path_dropped.connect(lambda path: [self.mig_src_input.setText(path), self.log(f"📥 [源路径拖放] 填入: {path}")])
        layout.addWidget(self.mig_src_drag)
        
        # 目标父目录输入区
        layout.addWidget(QLabel("💾 2. 搬入的目标父文件夹 (如 D:/BigFiles) [输出路径]:", self))
        dst_layout = QHBoxLayout()
        self.mig_dst_input = DragDropLineEdit(self, "直接将备份父文件夹拖入此处...")
        self.mig_dst_input.path_dropped.connect(lambda path: self.log(f"📥 [目标父录入] 填入: {path}"))
        self.mig_dst_browse = QPushButton("浏览...", self)
        self.mig_dst_browse.setProperty("class", "BrowseButton")
        self.mig_dst_browse.clicked.connect(self.browse_mig_dst)
        dst_layout.addWidget(self.mig_dst_input)
        dst_layout.addWidget(self.mig_dst_browse)
        layout.addLayout(dst_layout)
        
        # 新增输出/目标父文件夹专属微型拖拽虚线卡片
        self.mig_dst_drag = MiniDragZone(self, "拖拽 [搬入的目标父文件夹 (输出路径)] 到此处快速录入", "#9b59b6", "rgba(155, 89, 182, 0.03)", "🔗")
        self.mig_dst_drag.path_dropped.connect(lambda path: [self.mig_dst_input.setText(path), self.log(f"📥 [目标父拖放] 填入: {path}")])
        layout.addWidget(self.mig_dst_drag)
        
        layout.addSpacing(15)
        
        # 进度指示器
        self.mig_progress_label = QLabel("就绪。请确认没有被搬迁文件夹的后台软件正在运行（如微信）。", self)
        self.mig_progress_label.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(self.mig_progress_label)
        
        self.mig_progress_bar = QProgressBar(self)
        self.mig_progress_bar.setValue(0)
        self.mig_progress_bar.setFixedHeight(18)
        layout.addWidget(self.mig_progress_bar)
        
        layout.addSpacing(10)
        
        # 搬家执行按钮
        self.mig_start_btn = QPushButton("开始安全一键搬迁 ⚡", self)
        self.mig_start_btn.setProperty("class", "PrimaryButton")
        self.mig_start_btn.clicked.connect(self.start_migration)
        layout.addWidget(self.mig_start_btn)
        
        layout.addStretch()

    def create_advanced_tab(self):
        """创建“高级建链”功能页面"""
        self.advanced_widget = QWidget(self)
        self.advanced_widget.setProperty("class", "ContentCard")
        self.advanced_widget.setStyleSheet("#AdvancedCard { background-color: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; }")
        self.advanced_widget.setObjectName("AdvancedCard")
        
        layout = QVBoxLayout(self.advanced_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("🛠️ Windows 原生高级 Mklink 模式", self)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00a8ff;")
        layout.addWidget(title)
        
        desc = QLabel("用法：执行原生的 Windows Mklink 命令。链接路径指的是希望原地生成的“虚拟路径”；目标路径指的是真实的物理数据路径。", self)
        desc.setStyleSheet("color: #8888a0; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # 链接类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("⭐ 链接类型 (Link Type):", self))
        self.adv_type_combo = QComboBox(self)
        self.adv_type_combo.addItems([
            "目录联接 (Junction /J) - 免提权 (最常用推荐)",
            "目录符号链接 (Symlink /D) - 自动提权",
            "文件符号链接 (File Symlink) - 自动提权",
            "文件硬链接 (Hardlink /H) - 免提权"
        ])
        type_layout.addWidget(self.adv_type_combo, stretch=1)
        layout.addLayout(type_layout)
        
        # 链接路径 (Link Path)
        layout.addWidget(QLabel("🔗 1. 原地生成的链接路径 (输出路径 - 自动智能追加文件名):", self))
        link_layout = QHBoxLayout()
        self.adv_link_input = DragDropLineEdit(self, "直接拖入或使用右侧紫色“快捷输出端”拖放区...")
        self.adv_link_input.path_dropped.connect(self.on_adv_link_dropped)
        
        self.adv_link_browse = QPushButton("浏览...", self)
        self.adv_link_browse.setProperty("class", "BrowseButton")
        self.adv_link_browse.clicked.connect(self.browse_adv_link)
        link_layout.addWidget(self.adv_link_input)
        link_layout.addWidget(self.adv_link_browse)
        layout.addLayout(link_layout)
        
        # 新增链接路径（输出路径）专属微型拖拽虚线卡片
        self.adv_link_drag = MiniDragZone(self, "拖拽 [生成的链接路径 (输出路径)] 到此处快速录入", "#9b59b6", "rgba(155, 89, 182, 0.03)", "🔗")
        self.adv_link_drag.path_dropped.connect(lambda path: [self.adv_link_input.setText(path), self.on_adv_link_dropped(path)])
        layout.addWidget(self.adv_link_drag)
        
        # 目标路径 (Target Path)
        layout.addWidget(QLabel("🎯 2. 数据真实存放的目标路径:", self))
        target_layout = QHBoxLayout()
        self.adv_target_input = DragDropLineEdit(self, "直接拖入文件夹，或使用下方微型拖拽热区快速录入...")
        self.adv_target_input.path_dropped.connect(self.on_adv_target_dropped)
        
        self.adv_target_browse = QPushButton("浏览...", self)
        self.adv_target_browse.setProperty("class", "BrowseButton")
        self.adv_target_browse.clicked.connect(self.browse_adv_target)
        target_layout.addWidget(self.adv_target_input)
        target_layout.addWidget(self.adv_target_browse)
        layout.addLayout(target_layout)
        
        # 新增真实目标路径专属微型拖拽虚线卡片
        self.adv_target_drag = MiniDragZone(self, "拖拽 [真实存放的数据路径] 到此处快速录入", "#00a8ff", "rgba(0, 168, 255, 0.03)", "📂")
        self.adv_target_drag.path_dropped.connect(lambda path: [self.adv_target_input.setText(path), self.on_adv_target_dropped(path)])
        layout.addWidget(self.adv_target_drag)
        
        layout.addSpacing(20)
        
        # 高级执行按钮
        self.adv_create_btn = QPushButton("立即创建链接 🔗", self)
        self.adv_create_btn.setProperty("class", "PrimaryButton")
        self.adv_create_btn.clicked.connect(self.create_advanced_link)
        layout.addWidget(self.adv_create_btn)
        
        layout.addStretch()

    def create_restore_tab(self):
        """创建“链接还原/取消”功能页面"""
        self.restore_widget = QWidget(self)
        self.restore_widget.setProperty("class", "ContentCard")
        self.restore_widget.setStyleSheet("#RestoreCard { background-color: #1a1a24; border: 1px solid #2d2d3d; border-radius: 8px; }")
        self.restore_widget.setObjectName("RestoreCard")
        
        layout = QVBoxLayout(self.restore_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("🔄 Windows 符号链接一键还原与安全解除", self)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00a8ff;")
        layout.addWidget(title)
        
        desc = QLabel("用法：拖入或选择您已创建的虚拟链接（如 Junction）。您可以安全地解除该链接壳子，或者将移动到其他盘的数据安全完璧归赵地彻底移回原路径，恢复搬家前原状。", self)
        desc.setStyleSheet("color: #8888a0; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        # 链接路径输入区
        layout.addWidget(QLabel("📂 请输入或拖入需要取消/还原的虚拟链接路径:", self))
        link_layout = QHBoxLayout()
        self.rest_link_input = DragDropLineEdit(self, "拖入或选择需要解绑/还原的链接目录...")
        self.rest_link_input.path_dropped.connect(self.on_rest_link_dropped)
        
        self.rest_link_browse = QPushButton("浏览...", self)
        self.rest_link_browse.setProperty("class", "BrowseButton")
        self.rest_link_browse.clicked.connect(self.browse_rest_link)
        link_layout.addWidget(self.rest_link_input)
        link_layout.addWidget(self.rest_link_browse)
        layout.addLayout(link_layout)
        
        # 新增还原与解绑专属微型拖拽虚线卡片
        self.rest_link_drag = MiniDragZone(self, "拖拽 [已创建的虚拟链接文件夹] 到此处快速录入", "#2ecc71", "rgba(46, 204, 113, 0.03)", "🔄")
        self.rest_link_drag.path_dropped.connect(lambda path: [self.rest_link_input.setText(path), self.on_rest_link_dropped(path)])
        layout.addWidget(self.rest_link_drag)
        
        layout.addSpacing(15)
        
        # 进度指示器
        self.rest_progress_label = QLabel("等待执行。彻底移回前请务必关闭占用该目录文件的程序。", self)
        self.rest_progress_label.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(self.rest_progress_label)
        
        self.rest_progress_bar = QProgressBar(self)
        self.rest_progress_bar.setValue(0)
        self.rest_progress_bar.setFixedHeight(18)
        layout.addWidget(self.rest_progress_bar)
        
        layout.addSpacing(15)
        
        # 两大核心还原操作按钮并陈
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.rest_remove_btn = QPushButton("安全解除链接 (不移回数据) ✂️", self)
        self.rest_remove_btn.setProperty("class", "DangerButton")
        self.rest_remove_btn.clicked.connect(self.remove_link_only)
        btn_layout.addWidget(self.rest_remove_btn, stretch=1)
        
        self.rest_restore_btn = QPushButton("一键移回原处并解除 🔄", self)
        self.rest_restore_btn.setProperty("class", "GreenButton")
        self.rest_restore_btn.clicked.connect(self.restore_and_remove_link)
        btn_layout.addWidget(self.rest_restore_btn, stretch=1)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

    # --- 交互槽函数与智能逻辑 ---
    
    def on_adv_link_dropped(self, link_path):
        self.log(f"📥 [链接路径录入] 填入: {link_path}")
        self.auto_assemble_link_path()

    def on_adv_target_dropped(self, target_path):
        self.log(f"📥 [真实目标录入] 填入: {target_path}")
        self.auto_assemble_link_path()

    def auto_assemble_link_path(self):
        """
        【神仙级双向智能拼装算法】
        在高级建链下，若“链接路径”里的路径是一个存在的文件夹（表示用户拖入/选择了父文件夹），
        且“真实目标路径”非空，则自动在链接路径后追加目标文件夹的 basename！
        """
        link_path = self.adv_link_input.text().strip()
        target_path = self.adv_target_input.text().strip()
        
        if not target_path:
            return
            
        # 如果链接输入框当前的路径确实是一个已经存在的物理文件夹（表明用户拖入了父目录）
        if link_path and os.path.isdir(link_path):
            dir_name = os.path.basename(target_path)
            if dir_name:
                new_link_path = os.path.join(link_path, dir_name)
                # 只有还没拼接追加过，且和当前不一样时才更新，防止死循环
                if os.path.abspath(link_path) != os.path.abspath(new_link_path):
                    self.adv_link_input.setText(new_link_path)
                    self.log(f"💡 [智能拼装] 自动为【生成的链接路径】追加原始文件夹名 ➜ {new_link_path}", "#f1c40f")

    def on_rest_link_dropped(self, path):
        self.log(f"📥 [解绑还原录入] 填入: {path}")
        if mklink_engine.is_reparse_point(path):
            target = mklink_engine.get_link_target(path)
            self.log(f"   🔍 链接检测：判定为重解析点！目标指向 ➔ {target}", "#2ecc71")
        else:
            self.log(f"   ⚠️ 链接检测：该路径不是一个 Junction 联接，请勿进行反向搬迁操作。", "#e74c3c")

    def handle_source_dropped(self, path):
        """
        【高精分流】数据源拖放热区投递
        """
        current_tab = self.stacked_widget.currentIndex()
        if current_tab == 0:  # 极速搬家
            self.mig_src_input.setText(path)
            self.log(f"📥 [数据源拖放区] 填入极速搬迁【源大路径】: {path}")
        elif current_tab == 1:  # 高级建链
            self.adv_target_input.setText(path)
            self.log(f"📥 [数据源拖放区] 填入高级建链【真实目标路径】: {path}")
            self.auto_assemble_link_path()
        elif current_tab == 2:  # 还原与解绑
            self.rest_link_input.setText(path)
            self.on_rest_link_dropped(path)

    def handle_link_dropped(self, path):
        """
        【高精分流】快捷输出端拖放热区投递（即“输出路径拖入处”）
        """
        current_tab = self.stacked_widget.currentIndex()
        if current_tab == 0:  # 极速搬家
            self.mig_dst_input.setText(path)
            self.log(f"📥 [快捷输出端] 填入极速搬迁【目标父存储路径】: {path}")
        elif current_tab == 1:  # 高级建链
            self.adv_link_input.setText(path)
            self.log(f"📥 [快捷输出端] 填入高级建链【生成的链接路径】: {path}")
            self.auto_assemble_link_path()
        elif current_tab == 2:  # 还原与解绑
            self.rest_link_input.setText(path)
            self.on_rest_link_dropped(path)

    def handle_drag_drop(self, paths):
        """右侧统一大 DropZone 的智能填充（兜底备用）"""
        if not paths:
            return
        
        # 默认分流：如果鼠标拖入大 DropZone 却无法确定去向，智能根据链接/目标是否空缺填入
        current_tab = self.stacked_widget.currentIndex()
        path = paths[0]
        
        if current_tab == 0:
            if not self.mig_src_input.text().strip():
                self.handle_source_dropped(path)
            else:
                self.handle_link_dropped(path)
        elif current_tab == 1:
            if not self.adv_target_input.text().strip():
                self.handle_source_dropped(path)
            else:
                self.handle_link_dropped(path)
        elif current_tab == 2:
            self.handle_source_dropped(path)

    # --- Windows 底层 Native 拖拽物理越狱系统 ---
    
    def disable_all_subwidgets_accept_drops(self):
        """
        递归遍历所有子控件，强制关闭其 OLE 拖放属性。
        彻底抹除任何潜在的 IDropTarget 注册，迫使系统 100% 退化降级到已豁免的物理 WM_DROPFILES。
        """
        def recursive_disable(widget):
            if widget:
                widget.setAcceptDrops(False)
                for child in widget.findChildren(QWidget):
                    recursive_disable(child)
        recursive_disable(self)

    def force_bypass_ole_admin(self):
        """
        【机关枪式物理越狱定时器】
        在主窗口彻底显示后的黄金时间，连续强力强行拔掉 Qt 自动挂载的 OLE 注册，并彻底重新激活物理通道！
        """
        is_admin = mklink_engine.is_admin()
        if not is_admin:
            return
            
        hwnd = int(self.winId())
        try:
            # 1. 强制撤销主窗口的 OLE 注册
            res = ctypes.windll.ole32.RevokeDragDrop(hwnd)
            hex_res = hex(res & 0xffffffff)
            
            # 2. 重新允许物理拖放消息
            ctypes.windll.shell32.DragAcceptFiles(hwnd, True)
            
            # 3. 部署 Windows 窗口级 UIPI 消息豁免
            user32 = ctypes.windll.user32
            user32.ChangeWindowMessageFilterEx(hwnd, 0x0233, 1, None)
            user32.ChangeWindowMessageFilterEx(hwnd, 0x004A, 1, None)
            user32.ChangeWindowMessageFilterEx(hwnd, 0x0049, 1, None)
            
            # 4. 同时部署 Windows 进程级 UIPI 消息豁免
            user32.ChangeWindowMessageFilter(0x0233, 1)
            user32.ChangeWindowMessageFilter(0x004A, 1)
            user32.ChangeWindowMessageFilter(0x0049, 1)
            
            print(f"✔ [越狱定时器] HWND: {hwnd} | RevokeDragDrop HRESULT: {hex_res} | 物理接收已强制覆盖激活！")
            
            # 如果成功撤销了 OLE (res == 0) 或者是首次注册并注销，记录成功日志
            if res == 0:
                self.log(f"🛡️ [OLE 越狱] 延迟物理降级通道已成功强行激活 (RevokeDragDrop={hex_res})！", "#2ecc71")
        except Exception as e:
            print("❌ 越狱定时器执行异常:", e)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        
        is_admin = mklink_engine.is_admin()
        if is_admin:
            # 管理员运行下强行禁用全窗口子控件的 OLE 拖放，迫使系统降级到物理 WM_DROPFILES，彻底突破 UIPI 拦截
            self.disable_all_subwidgets_accept_drops()
            
            # 强行部署“机关枪式”多重延迟物理越狱，确保绝对不会被 Qt 底层后续注册覆盖！
            QTimer.singleShot(50, self.force_bypass_ole_admin)
            QTimer.singleShot(200, self.force_bypass_ole_admin)
            QTimer.singleShot(500, self.force_bypass_ole_admin)
            QTimer.singleShot(1000, self.force_bypass_ole_admin)
            self.log("🛡️ [OLE 越狱] 提权模式下已强行部署多重延迟物理拖拽越狱机关枪！", "#2ecc71")
            
            # 1. 物理注册允许原生 Shell 拖拽文件消息 (仅在提权下运行，普通权限绝不运行，防止 OLE 冲突)
            try:
                ctypes.windll.shell32.DragAcceptFiles(hwnd, True)
                print("✔ 原生 HWND 物理拖拽接收启动")
            except Exception as e:
                print("DragAcceptFiles 激活失败:", e)
                
            # 2. 内核过滤豁免 UIPI 安全特权隔离白名单
            try:
                user32 = ctypes.windll.user32
                # 0x0233 = WM_DROPFILES, 0x004A = WM_COPYDATA, 0x0049 = WM_COPYGLOBALMEM
                user32.ChangeWindowMessageFilterEx(hwnd, 0x0233, 1, None)
                user32.ChangeWindowMessageFilterEx(hwnd, 0x004A, 1, None)
                user32.ChangeWindowMessageFilterEx(hwnd, 0x0049, 1, None)
                print("✔ 内核级 HWND 豁免过滤器已部署")
            except Exception as e:
                print("ChangeWindowMessageFilterEx 失败，使用进程级豁免:", e)
                exempt_drag_drop_uipi()

    def nativeEvent(self, event_type, message):
        """
        重写 Qt 系统原生事件分发，在底层强行解包并捕获 Windows 拖拽数据流。
        这可以 100% 击穿 Windows UIPI 权限屏障，实现管理员运行下拖入绝对不被拦截！
        """
        if event_type == b'windows_generic_MSG':
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0233:  # WM_DROPFILES 消息
                hDrop = msg.wParam
                
                # 读取文件总数
                num_files = ctypes.windll.shell32.DragQueryFileW(hDrop, 0xFFFFFFFF, None, 0)
                paths = []
                for i in range(num_files):
                    length = ctypes.windll.shell32.DragQueryFileW(hDrop, i, None, 0)
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.shell32.DragQueryFileW(hDrop, i, buffer, length + 1)
                    paths.append(buffer.value)
                
                # 释放句柄内存
                ctypes.windll.shell32.DragFinish(hDrop)
                
                if paths:
                    # 触发高智商物理坐标碰撞与投递
                    self.handle_native_drag_drop_paths(paths)
                
                # 返回 True 宣告此内核事件已由我们自主消费完毕，Qt 无需二次传递
                return True, 0
                
        return super().nativeEvent(event_type, message)

    def handle_native_drag_drop_paths(self, paths):
        """
        【物理坐标高精度分流派发系统】
        拖拽松手瞬间，检测鼠标正停留在哪一个 DragDropLineEdit 输入框、微型拖拽热区或者右侧的分流卡片框上，
        实现物理级“指哪填哪”以及高保真智能分流！
        """
        if not paths:
            return
            
        path = os.path.abspath(paths[0])
        global_pos = QCursor.pos()  # 全局绝对屏幕坐标
        
        # 1. 优先对界面中可见的专属微型拖拽热区进行高精度碰撞映射
        mini_zones = [
            (self.mig_src_drag, self.mig_src_input, "极速搬家 - 源路径微型拖放区"),
            (self.mig_dst_drag, self.mig_dst_input, "极速搬家 - 目标父路径微型拖放区"),
            (self.adv_link_drag, self.adv_link_input, "高级建链 - 虚拟链接路径微型拖放区"),
            (self.adv_target_drag, self.adv_target_input, "高级建链 - 真实数据路径微型拖放区"),
            (self.rest_link_drag, self.rest_link_input, "还原与解绑 - 链接路径微型拖放区")
        ]
        for zone_widget, target_input, desc in mini_zones:
            if zone_widget.isVisible():
                if zone_widget.rect().contains(zone_widget.mapFromGlobal(global_pos)):
                    target_input.setText(path)
                    # 触发相对应拖入槽函数
                    if target_input == self.mig_src_input:
                        self.log(f"📥 [物理越狱拖放] 填入极速搬迁【源大路径】: {path}")
                    elif target_input == self.mig_dst_input:
                        self.log(f"📥 [物理越狱拖放] 填入极速搬迁【目标父存储路径】: {path}")
                    elif target_input == self.adv_link_input:
                        self.on_adv_link_dropped(path)
                    elif target_input == self.adv_target_input:
                        self.on_adv_target_dropped(path)
                    elif target_input == self.rest_link_input:
                        self.on_rest_link_dropped(path)
                    self.log(f"🎯 [物理越狱拖放] 精准指入微型拖拽区【{desc}】➜ {path}", "#2ecc71")
                    return
        
        # 2. 对界面中可见的输入框进行高精度碰撞映射
        line_edits = [
            (self.mig_src_input, "极速搬家 - 源大文件夹"),
            (self.mig_dst_input, "极速搬家 - 目标父存储"),
            (self.adv_link_input, "高级建链 - 虚拟链接路径"),
            (self.adv_target_input, "高级建链 - 真实数据路径"),
            (self.rest_link_input, "还原与解绑 - 链接路径")
        ]
        for widget, desc in line_edits:
            if widget.isVisible():
                if widget.rect().contains(widget.mapFromGlobal(global_pos)):
                    widget.setText(path)
                    widget.path_dropped.emit(path)
                    self.log(f"🎯 [物理越狱拖放] 精准指入输入框【{desc}】➜ {path}", "#2ecc71")
                    return
                    
        # 3. 兜底策略：均无碰撞则智能Tab路由
        self.handle_drag_drop(paths)

    def update_admin_status(self):
        """刷新管理员权限UI状态"""
        is_admin = mklink_engine.is_admin()
        if is_admin:
            self.auth_badge.setText("🛡️ 管理员已授权 (点击可去权)")
            self.auth_badge.setProperty("class", "BadgeAdmin")
            self.auth_badge.setToolTip("已提权！且 NativeEvent 越狱免拦截系统已部署完毕。点击可以去权降级运行。")
        else:
            self.auth_badge.setText("🔒 普通权限 (UAC 按需提权激活)")
            self.auth_badge.setProperty("class", "BadgeUser")
            self.auth_badge.setToolTip("普通运行。拖放功能已 100% 激活并支持原生最美 Fluent 动画！如执行特权指令，系统会自动弹出按需 UAC 气泡提权。")
        
        self.auth_badge.setStyle(self.auth_badge.style())

    def request_uac(self):
        """点击角标请求 UAC 管理员提权，或在已授权时提供去权降级运行选项"""
        if mklink_engine.is_admin():
            reply = QMessageBox.question(
                self,
                "权限管理",
                "当前已运行在 🛡️ 管理员授权状态下。\n\n"
                "是否需要【去除管理员权限】，降级为普通权限重新拉起本工具？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.log("🔑 [权限管理] 正在请求降级为普通权限重新拉起小工具...")
                self.save_config()  # 降级退出前必须保存最新数据！
                success = mklink_engine.run_as_normal_user()
                if success:
                    QApplication.quit()
            return
            
        self.log("🔑 [权限管理] 正在请求管理员权限重新拉起小工具...")
        self.save_config()  # 提权退出前也保存最新数据！
        success = mklink_engine.run_as_admin()
        if success:
            QApplication.quit()
        else:
            self.log("❌ [权限管理] 管理员权限请求被用户拒绝或触发异常。", "#e74c3c")

    def switch_tab(self, index):
        """点击NavBar切换Tab"""
        self.stacked_widget.setCurrentIndex(index)
        
        # 更新导航按钮激活样式
        self.nav_btn1.setProperty("active", "true" if index == 0 else "false")
        self.nav_btn2.setProperty("active", "true" if index == 1 else "false")
        self.nav_btn_restore.setProperty("active", "true" if index == 2 else "false")
        
        self.nav_btn1.setStyle(self.nav_btn1.style())
        self.nav_btn2.setStyle(self.nav_btn2.style())
        self.nav_btn_restore.setStyle(self.nav_btn_restore.style())
        
        self.log(f"📑 切换到: {['建立链接模式', '极速数据搬家', '还原与解绑'][index]} 选项卡")

    def log(self, text, color="#00ff66"):
        """向日志区输出 HTML 格式 of 系统通知"""
        formatted = f"<span style='color: {color};'>{text}</span>"
        self.log_browser.append(formatted)

    # --- 浏览文件夹槽函数 ---
    
    def browse_mig_src(self):
        dir_path = QFileDialog.getExistingDirectory(self, "请选择需要搬离的源文件夹")
        if dir_path:
            self.mig_src_input.setText(dir_path)
            self.log(f"📂 选择了搬迁源路径: {dir_path}")

    def browse_mig_dst(self):
        dir_path = QFileDialog.getExistingDirectory(self, "请选择目标父存储文件夹 (比如 D:/BigFiles)")
        if dir_path:
            self.mig_dst_input.setText(dir_path)
            self.log(f"💾 选择了搬迁目标父路径: {dir_path}")

    def browse_adv_link(self):
        combo_idx = self.adv_type_combo.currentIndex()
        if combo_idx in [0, 1]:  # 目录型
            dir_path = QFileDialog.getExistingDirectory(self, "请指定需要生成的虚拟链接文件夹路径 (此位置先前不能有同名文件夹)")
            if dir_path:
                self.adv_link_input.setText(dir_path)
                self.log(f"🔗 设定链接文件夹路径: {dir_path}")
                self.auto_assemble_link_path()
        else:  # 文件型
            file_path, _ = QFileDialog.getSaveFileName(self, "请指定需要生成的虚拟文件链接路径 (此位置先前不能有同名文件)")
            if file_path:
                self.adv_link_input.setText(file_path)
                self.log(f"🔗 设定链接文件路径: {file_path}")

    def browse_adv_target(self):
        combo_idx = self.adv_type_combo.currentIndex()
        if combo_idx in [0, 1]:  # 目录型
            dir_path = QFileDialog.getExistingDirectory(self, "选择真实存放数据的目标文件夹")
            if dir_path:
                self.adv_target_input.setText(dir_path)
                self.log(f"🎯 设定真实目标文件夹路径: {dir_path}")
                self.auto_assemble_link_path()
        else:  # 文件型
            file_path, _ = QFileDialog.getOpenFileName(self, "选择真实存放数据的目标文件")
            if file_path:
                self.adv_target_input.setText(file_path)
                self.log(f"🎯 设定真实目标文件路径: {file_path}")

    def browse_rest_link(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择需要解除或还原的虚拟链接(Junction/Symlink_dir)目录")
        if dir_path:
            self.rest_link_input.setText(dir_path)
            self.on_rest_link_dropped(dir_path)

    # --- 执行引擎触发函数 ---
    
    def start_migration(self):
        """一键极速搬家触发逻辑"""
        source = self.mig_src_input.text().strip()
        dest = self.mig_dst_input.text().strip()
        
        if not source or not dest:
            QMessageBox.warning(self, "警告", "请先填入完整的源文件夹路径和目标父文件夹路径！")
            return
            
        if not os.path.exists(source):
            QMessageBox.warning(self, "警告", "源大文件夹不存在，请检查输入！")
            return
            
        if not os.path.exists(dest):
            reply = QMessageBox.question(self, "确认", f"目标父文件夹 '{dest}' 不存在，是否需要自动创建它？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(dest, exist_ok=True)
                    self.log(f"🛠️ 已自动创建目标父路径: {dest}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建目标父路径失败: {e}")
                    return
            else:
                return

        reply = QMessageBox.question(
            self, 
            "安全搬家确认", 
            f"系统即将开始一键大文件夹迁移！\n\n"
            f"🚚 源路径: {source}\n"
            f"📥 目标路径: {dest}\n\n"
            f"⚠️ 重要提示: 请确保您已经彻底关闭与该文件夹相关的后台程序（如微信、游戏），"
            f"防止文件被占用导致迁移不完整。点击【是】开始执行搬家。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return

        self.mig_start_btn.setEnabled(False)
        self.mig_src_input.setEnabled(False)
        self.mig_dst_input.setEnabled(False)
        
        self.log(f"⚡ [极速搬家] 开始安全搬迁流程...", "#3498db")
        
        self.thread = MigrationThread(source, dest)
        self.thread.progress_signal.connect(self.on_migration_progress)
        self.thread.finished_signal.connect(self.on_migration_finished)
        self.thread.start()

    def on_migration_progress(self, status_text, percent):
        """实时接收后台线程的进度回传并刷新UI"""
        self.mig_progress_label.setText(status_text)
        self.mig_progress_bar.setValue(percent)
        self.log(f"⚙️ {status_text} (当前进度: {percent}%)")

    def on_migration_finished(self, success, message):
        """搬家结束后解除 UI 锁定并弹窗通知"""
        self.mig_start_btn.setEnabled(True)
        self.mig_src_input.setEnabled(True)
        self.mig_dst_input.setEnabled(True)
        
        if success:
            self.mig_progress_label.setText("🎉 搬家建立链接 100% 成功！")
            self.mig_progress_bar.setValue(100)
            self.log(message, "#2ecc71")
            QMessageBox.information(self, "极速搬家成功！", message)
            self.mig_src_input.clear()
        else:
            self.mig_progress_label.setText("❌ 搬家过程发生异常或校验未过。")
            self.log(message, "#e74c3c")
            QMessageBox.critical(self, "迁移未成功", message)

    def create_advanced_link(self):
        """高级原生建链触发逻辑"""
        link_path = self.adv_link_input.text().strip()
        target_path = self.adv_target_input.text().strip()
        
        if not link_path or not target_path:
            QMessageBox.warning(self, "警告", "请先填入完整的链接路径与真实数据路径！")
            return
            
        type_idx = self.adv_type_combo.currentIndex()
        types_map = {0: 'junction', 1: 'symlink_dir', 2: 'symlink_file', 3: 'hardlink'}
        link_type = types_map[type_idx]
        
        self.log(f"🛠️ [高级建链] 尝试创建类型为 '{link_type}' 的链接...")
        success, message = mklink_engine.create_link(link_type, link_path, target_path)
        
        if success:
            self.log(message, "#2ecc71")
            QMessageBox.information(self, "链接创建成功", message)
            self.adv_link_input.clear()
        else:
            self.log(message, "#e74c3c")
            QMessageBox.critical(self, "创建链接失败", message)

    # --- 取消还原板块槽函数 ---
    
    def remove_link_only(self):
        """【单纯解除链接】"""
        link_path = self.rest_link_input.text().strip()
        if not link_path:
            QMessageBox.warning(self, "警告", "请先选择需要解绑的链接路径！")
            return

        if not mklink_engine.is_reparse_point(link_path):
            QMessageBox.warning(self, "警告", "选定路径在底层不是一个 Junction 或符号链接，无法对其执行解绑操作！")
            return

        target = mklink_engine.get_link_target(link_path)
        reply = QMessageBox.question(
            self,
            "安全解绑确认",
            f"⚠️ 特别警告：\n系统即将安全解除（删除）下列虚拟链接壳子！\n\n"
            f"🔗 链接路径: {link_path}\n"
            f"🎯 指向的物理真实数据: {target}\n\n"
            f"说明：此操作只删除快捷联接名壳子，数据 100% 完整保留在 '{target}' 中，以后还可以手动补建链接。是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        success, message = mklink_engine.safe_remove_link_only(link_path)
        if success:
            self.log(message, "#2ecc71")
            QMessageBox.information(self, "成功安全解绑", message)
            self.rest_link_input.clear()
        else:
            self.log(message, "#e74c3c")
            QMessageBox.critical(self, "解绑失败", message)

    def restore_and_remove_link(self):
        """【一键彻底还原（数据移回并解除链接）】"""
        link_path = self.rest_link_input.text().strip()
        if not link_path:
            QMessageBox.warning(self, "警告", "请先选择需要还原的链接路径！")
            return

        if not mklink_engine.is_reparse_point(link_path):
            QMessageBox.warning(self, "警告", "选定路径在底层不是一个 Junction 或符号链接，无法执行数据反向移动！")
            return

        target = mklink_engine.get_link_target(link_path)
        reply = QMessageBox.question(
            self,
            "一键数据还源确认",
            f"🚚 系统即将开始【一键反向搬家还原】！\n\n"
            f"🔗 虚拟链接: {link_path}\n"
            f"📥 实际大文件: {target}\n\n"
            f"⚠️ 重要说明：系统将安全地把所有文件从目标盘剪切移动回原处（如C盘），"
            f"并自动清理 D 盘残留与 C 盘链接壳子，彻底恢复至搬迁前的原状。\n"
            f"请务必在点击【是】之前关闭可能占用该目录文件的程序。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # 锁定 UI 交互
        self.rest_remove_btn.setEnabled(False)
        self.rest_restore_btn.setEnabled(False)
        self.rest_link_input.setEnabled(False)
        
        self.log(f"⚡ [彻底还原] 开始安全反向迁移...", "#3498db")
        
        self.rest_thread = RestoreThread(link_path)
        self.rest_thread.progress_signal.connect(self.on_restore_progress)
        self.rest_thread.finished_signal.connect(self.on_restore_finished)
        self.rest_thread.start()

    def on_restore_progress(self, status_text, percent):
        """实时接收还原线程进度"""
        self.rest_progress_label.setText(status_text)
        self.rest_progress_bar.setValue(percent)
        self.log(f"⚙️ {status_text} (当前进度: {percent}%)")

    def on_restore_finished(self, success, message):
        """还原结束解除 UI 锁定"""
        self.rest_remove_btn.setEnabled(True)
        self.rest_restore_btn.setEnabled(True)
        self.rest_link_input.setEnabled(True)
        
        if success:
            self.rest_progress_label.setText("🎉 一键数据还原 100% 成功！")
            self.rest_progress_bar.setValue(100)
            self.log(message, "#2ecc71")
            QMessageBox.information(self, "反向还原成功！", message)
            self.rest_link_input.clear()
        else:
            self.rest_progress_label.setText("❌ 还原过程中发生错误。")
            self.log(message, "#e74c3c")
            QMessageBox.critical(self, "反向还原未成功", message)


# --- 应用程序入口 ---
def main():
    # 启用高清 DPI 支持，适配 4K/2K 高清屏幕
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
