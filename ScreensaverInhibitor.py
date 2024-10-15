import sys
import subprocess
from PyQt6.QtCore import QTimer
import platform
import os

class ScreensaverInhibitor:
    def __init__(self):
        self.platform = platform.system()
        self.inhibitor = None

        if self.platform.startswith('Windows'):
            self.inhibitor = WindowsInhibitor()
        elif self.platform.startswith('Linux'):
            self.inhibitor = LinuxInhibitor()
        elif self.platform.startswith('Darwin'):
            self.inhibitor = MacOSInhibitor()
        else:
            print("Unsupported platform for screensaver inhibition")

    def inhibit(self):
        if self.inhibitor:
            self.inhibitor.inhibit()

    def uninhibit(self):
        if self.inhibitor:
            self.inhibitor.uninhibit()

class WindowsInhibitor:
    def __init__(self):
        import ctypes
        self.ctypes = ctypes
        self.timer = QTimer()
        self.timer.timeout.connect(self.reset_screensaver)

    def inhibit(self):
        self.timer.start(30000)  # Reset every 30 seconds

    def uninhibit(self):
        self.timer.stop()

    def reset_screensaver(self):
        self.ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)

class LinuxInhibitor:
    def __init__(self):
        import dbus
        self.bus = dbus.SessionBus()
        self.saver = self.bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
        self.cookie = None

    def inhibit(self):
        if self.cookie is None:
            self.cookie = self.saver.Inhibit("VideoPlayer", "Playing video")

    def uninhibit(self):
        if self.cookie is not None:
            self.saver.UnInhibit(self.cookie)
            self.cookie = None

class MacOSInhibitor:
    def __init__(self):
        self.process = None
        # Kill all caffeinate processes if running
        subprocess.Popen(['killall', 'caffeinate'])

    def inhibit(self):
        if self.process is None:
            self.process = subprocess.Popen(['caffeinate', '-d'])

    def uninhibit(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None
