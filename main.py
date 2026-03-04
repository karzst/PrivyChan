import sys
import winreg
import json
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QMenu, QSystemTrayIcon
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon

class PrivyChanFloating(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.load_config()
        
        self.current_corner = self.config.get("position", "bottom-right")
        self.current_opacity = self.config.get("opacity", 1.0)
        self.current_movable = self.config.get("movable", False)
        self.current_reset_trigger = self.config.get("reset_trigger", 0) # ذاكرة للـ Reset

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        if not self.current_movable:
            flags |= Qt.WindowType.WindowTransparentForInput 
        
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self.current_opacity)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.mic_label = QLabel("🎤")
        self.cam_label = QLabel("📷")
        
        self.style_inactive = "color: white; background-color: rgba(0, 0, 0, 100); padding: 5px; border-radius: 10px; font-size: 18px;"
        self.style_active = "color: #ff4d4d; background-color: rgba(150, 0, 0, 180); padding: 5px; border-radius: 10px; font-size: 18px; border: 1px solid red;"
        
        self.mic_label.setStyleSheet(self.style_inactive)
        self.cam_label.setStyleSheet(self.style_inactive)
        
        layout.addWidget(self.mic_label)
        layout.addWidget(self.cam_label)
        self.setLayout(layout)

        self.update_position()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(1000)

        self.create_tray_icon()
        self.oldPos = QPoint()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists("icon.png"):
            self.tray_icon.setIcon(QIcon("icon.png"))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
        tray_menu = QMenu()
        exit_action = tray_menu.addAction("Exit PrivyChan")
        exit_action.triggered.connect(self.exit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def exit_app(self):
        self.load_config()
        self.config["active"] = False
        with open(self.settings_file, "w") as f:
            json.dump(self.config, f, indent=4)
        QApplication.quit()

    def load_config(self):
        try:
            with open(self.settings_file, "r") as f:
                self.config = json.load(f)
        except:
            self.config = {"active": True, "movable": False, "position": "bottom-right", "opacity": 1.0, "reset_trigger": 0}

    def update_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        pos = self.config.get("position", "bottom-right")
        margin = 50
        x, y = 0, 0

        if "top-right" in pos: x, y = screen.width() - 120, margin
        elif "bottom-right" in pos: x, y = screen.width() - 120, screen.height() - margin
        elif "top-left" in pos: x, y = margin, margin
        elif "bottom-left" in pos: x, y = margin, screen.height() - margin
        self.move(x, y)

    def mousePressEvent(self, event):
        if self.current_movable and event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.current_movable and not self.oldPos.isNull():
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = QPoint()

    def is_hardware_in_use(self, type_path):
        paths = [
            f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\{type_path}",
            f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\{type_path}\\NonPackaged"
        ]
        for path in paths:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                    info = winreg.QueryInfoKey(key)
                    for i in range(info[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                value, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                                if value == 0: return True
                            except: pass
            except: pass
        return False

    def update_loop(self):
        self.load_config()
        
        if not self.config.get("active", True):
            QApplication.quit()
            return

        new_corner = self.config.get("position", "bottom-right")
        if new_corner != self.current_corner:
            self.current_corner = new_corner
            self.update_position()
            
        new_reset_trigger = self.config.get("reset_trigger", 0)
        if new_reset_trigger != self.current_reset_trigger:
            self.current_reset_trigger = new_reset_trigger
            self.update_position()

        new_opacity = self.config.get("opacity", 1.0)
        if new_opacity != self.current_opacity:
            self.current_opacity = new_opacity
            self.setWindowOpacity(self.current_opacity)

        new_movable = self.config.get("movable", False)
        if new_movable != self.current_movable:
            self.current_movable = new_movable
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not self.current_movable)
            self.show() 
        
        mic_on = self.is_hardware_in_use("microphone")
        cam_on = self.is_hardware_in_use("webcam")
        self.mic_label.setStyleSheet(self.style_active if mic_on else self.style_inactive)
        self.cam_label.setStyleSheet(self.style_active if cam_on else self.style_inactive)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = PrivyChanFloating()
    window.show()
    sys.exit(app.exec())