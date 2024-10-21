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
        self.ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    def reset_screensaver(self):
        self.ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)

class LinuxInhibitor:
    def __init__(self):
        import dbus
        self.bus = dbus.SessionBus()
        try:
            self.saver = self.bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
            self.iface = dbus.Interface(self.saver, 'org.freedesktop.ScreenSaver')
            self.cookie = None
        except dbus.DBusException as e:
            print(f"Error initializing screensaver inhibitor: {e}")
            self.saver = None

    def inhibit(self):
        if self.saver and self.cookie is None:
            try:
                self.cookie = self.iface.Inhibit("VideoPlayer", "Playing video")
                print(f"Screensaver inhibited with cookie {self.cookie}")
            except dbus.DBusException as e:
                print(f"Error inhibiting screensaver: {e}")

    def uninhibit(self):
        if self.saver and self.cookie is not None:
            try:
                self.iface.UnInhibit(self.cookie)
                print(f"Screensaver uninhibited, cookie {self.cookie} released")
                self.cookie = None
            except dbus.DBusException as e:
                print(f"Error uninhibiting screensaver: {e}")


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
