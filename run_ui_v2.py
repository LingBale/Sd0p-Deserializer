#!/usr/bin/env python3
"""
Sd0p-v3.0 V2 UI 独立启动入口 (PyQt6)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
    from ui_v2.main_window import V2MainWindow

    def main():
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = V2MainWindow()
        window.show()
        
        sys.exit(app.exec())

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Error: {e}")
    print("Please install PyQt6: pip install PyQt6")
