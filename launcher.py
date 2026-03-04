import sys
import json
import os
import subprocess
import winreg
import time 
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox, QComboBox, QSlider)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap

class PrivyChanLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PrivyChan - Control Panel")
        self.setFixedSize(600, 360) 
        
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
            
        self.settings_file = "settings.json"
        self.load_settings()

        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_layout = QVBoxLayout()
        self.title_label = QLabel("PrivyChan 🎀")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff4d4d; background: transparent;")
        left_layout.addWidget(self.title_label)

        is_active = self.settings.get("active", False)
        btn_text = "Deactivate Tool" if is_active else "Activate Tool"
        btn_color = "#f44336" if is_active else "#4CAF50"
        
        self.btn_toggle = QPushButton(btn_text)
        self.btn_toggle.setStyleSheet(f"background-color: {btn_color}; color: white; padding: 15px; border-radius: 10px; font-size: 16px; font-weight: bold;")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_tool)
        left_layout.addWidget(self.btn_toggle)

        self.btn_reset = QPushButton("Reset Position ")
        self.btn_reset.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; border-radius: 10px; font-size: 14px; font-weight: bold;")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.clicked.connect(self.trigger_reset)
        left_layout.addWidget(self.btn_reset)

        footer = QLabel("made by karz")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #333; font-size: 11px; font-weight: bold;")
        left_layout.addStretch()
        left_layout.addWidget(footer)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        setting_style = "font-size: 14px; font-weight: bold; color: #222;"
        
        self.check_movable = QCheckBox("Allow Dragging (Movable)")
        self.check_movable.setStyleSheet(setting_style)
        self.check_movable.setChecked(self.settings.get("movable", False))
        self.check_movable.stateChanged.connect(self.save_settings)
        right_layout.addWidget(self.check_movable)

        self.check_startup = QCheckBox("Run on System Startup")
        self.check_startup.setStyleSheet(setting_style)
        self.check_startup.setChecked(self.check_if_startup())
        self.check_startup.stateChanged.connect(self.toggle_startup)
        right_layout.addWidget(self.check_startup)

        right_layout.addSpacing(10)

        self.opacity_label = QLabel(f"Tool Opacity: {int(self.settings.get('opacity', 1.0) * 100)}%")
        self.opacity_label.setStyleSheet(setting_style)
        right_layout.addWidget(self.opacity_label)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(int(self.settings.get("opacity", 1.0) * 100))
        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        right_layout.addWidget(self.opacity_slider)

        right_layout.addSpacing(10)

        pos_label = QLabel("Position on Screen:")
        pos_label.setStyleSheet(setting_style)
        right_layout.addWidget(pos_label)
        
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["Top-Right", "Bottom-Right", "Top-Left", "Bottom-Left"])
        self.combo_pos.setCurrentText(self.settings.get("position", "Bottom-Right").title())
        self.combo_pos.setStyleSheet("padding: 5px; font-size: 13px; border-radius: 5px; background-color: rgba(255, 255, 255, 200);")
        self.combo_pos.currentTextChanged.connect(self.save_settings)
        right_layout.addWidget(self.combo_pos)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

    def trigger_reset(self):
        self.settings["reset_trigger"] = time.time()
        self.save_settings()

    def on_opacity_change(self, value):
        self.opacity_label.setText(f"Tool Opacity: {value}%")
        self.save_settings()

    def check_if_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "PrivyChanTool")
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def toggle_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if self.check_startup.isChecked():
                if getattr(sys, 'frozen', False):
                    target_path = os.path.join(os.path.dirname(sys.executable), "main.exe")
                    cmd = f'"{target_path}"'
                else:
                    cmd = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
                winreg.SetValueEx(key, "PrivyChanTool", 0, winreg.REG_SZ, cmd)
                self.settings["active"] = True
                self.save_settings()
            else:
                try: winreg.DeleteValue(key, "PrivyChanTool")
                except OSError: pass
            winreg.CloseKey(key)
        except Exception as e: print("Error toggling startup:", e)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        if os.path.exists("background.jpg"):
            pixmap = QPixmap("background.jpg")
            painter.setOpacity(0.35) 
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x, y, scaled_pixmap)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {"active": False, "movable": False, "position": "bottom-right", "opacity": 1.0, "reset_trigger": 0}

    def save_settings(self):
        self.settings["movable"] = self.check_movable.isChecked()
        self.settings["position"] = self.combo_pos.currentText().lower()
        self.settings["opacity"] = self.opacity_slider.value() / 100.0
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def toggle_tool(self):
        is_active = self.settings.get("active", False)
        if not is_active:
            self.settings["active"] = True
            self.save_settings()
            
            if getattr(sys, 'frozen', False):
                target_path = os.path.join(os.path.dirname(sys.executable), "main.exe")
                subprocess.Popen([target_path])
            else:
                subprocess.Popen([sys.executable, "main.py"])
            # --------------------------------------------------------
            
            self.btn_toggle.setText("Deactivate Tool")
            self.btn_toggle.setStyleSheet("background-color: #f44336; color: white; padding: 15px; border-radius: 10px; font-size: 16px; font-weight: bold;")
        else:
            self.settings["active"] = False
            self.save_settings()
            self.btn_toggle.setText("Activate Tool")
            self.btn_toggle.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; border-radius: 10px; font-size: 16px; font-weight: bold;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PrivyChanLauncher()
    window.show()
    sys.exit(app.exec())