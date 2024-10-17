import sys
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QStackedWidget, QWidget, QTableWidgetItem, QTableWidget, QMessageBox
from DraggableWidget import DraggableWidget
from enum import Enum
from AppData import * 

class ENUM_SettingsViews(Enum):
    INTRO = 0
    PLAYLIST = 1 
    LIBRARY  = 2
    PLAYLIST_EDITOR = 3
    LIBRARY_EDITOR = 4
    
    
class SettingsIntro(DraggableWidget):
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        self.ui = uic.loadUi("assets/Settings.ui", self)
        
        self.ui.Close_button.clicked.connect(self.CloseButtonClicked)
        self.ui.PlayList_button.clicked.connect(self.PlayListButtonClicked)
        self.ui.Library_button.clicked.connect(self.LibraryButtonClicked)
        self.ui.HotKeys_button.clicked.connect(self.HotKeysButtonClicked)
        
    def CloseButtonClicked(self):
        self.settingsManager.HideSettings()
        
    def PlayListButtonClicked(self):
        self.settingsManager.ShowPlayListSettings()
        
    def LibraryButtonClicked(self):
        self.settingsManager.ShowLibrarySettings()
        
    def HotKeysButtonClicked(self):
        #self.SettingsManager.ShowHotKeySettings()
        pass
        
class PlayListSettings(DraggableWidget):
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        
        self.ui = uic.loadUi("assets/PlayListSettings.ui", self)
        self.ui.Titlebar_label.setText("PlayList Settings")
        self.ui.Back_button.clicked.connect(self.BackButtonClicked) 
        
        self.UpdateTable()
        
    def BackButtonClicked(self):
        self.settingsManager.ShowSettings()
        
    def UpdateTable(self):
        playLists = self.settingsManager.appData.PlayLists
        
        # Update the table row count
        self.ui.PlayList_table.setRowCount(len(playLists)) 
        
        # Update the table contents
        row = 0
        for item in playLists:
            #print(keys.name, keys.hotkey)
            name = QTableWidgetItem(item.name)
            source = QTableWidgetItem(item.source)
            name.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            source.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.PlayList_table.setItem(row, 0, name)
            self.ui.PlayList_table.setItem(row, 1, source)
            row += 1
            

class LibrarySettings(DraggableWidget):
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        
        self.ui = uic.loadUi("assets/PlayListSettings.ui", self)
        self.ui.Titlebar_label.setText("Library Settings")
        
        self.ui.Back_button.clicked.connect(self.BackButtonClicked) 
        
        self.UpdateTable()
        
    def BackButtonClicked(self):
        self.settingsManager.ShowSettings()
        
    def UpdateTable(self):
        library = self.settingsManager.appData.Library
        
        # Update the table row count
        self.ui.PlayList_table.setRowCount(len(library)) 
        
        # Update the table contents
        row = 0
        for item in library:
            #print(keys.name, keys.hotkey)
            name = QTableWidgetItem(item.name)
            source = QTableWidgetItem(item.source)
            name.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            source.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.ui.PlayList_table.setItem(row, 0, name)
            self.ui.PlayList_table.setItem(row, 1, source)
            row += 1
        
class EntryEditor(DraggableWidget):
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        
        self.ui = uic.loadUi("assets/EntryEditor.ui", self)
        
        
class SettingsManager():
    def __init__(self, appData: AppData):
        self.appData = appData
        
        self.settingStack = QStackedWidget()
        
        self.SettingsIntro = SettingsIntro(self)
        self.PlayListSettings = PlayListSettings(self)
        self.LibrarySettings = LibrarySettings(self)
        self.PlayListEditor = EntryEditor(self)
        self.LibraryEditor = EntryEditor(self)
        
        self.settingStack.addWidget(self.SettingsIntro)
        self.settingStack.addWidget(self.PlayListSettings)
        self.settingStack.addWidget(self.LibrarySettings)
        self.settingStack.addWidget(self.PlayListEditor)
        self.settingStack.addWidget(self.LibraryEditor)
        
        self.settingStack.setFixedWidth(678)
        self.settingStack.setFixedHeight(320) 
        
        self.settingStack.setWindowFlags(Qt.WindowType.FramelessWindowHint)  
        self.settingStack.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        
        
    def ShowSettings(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.INTRO.value)
        self.settingStack.show()
        
    def HideSettings(self):
        self.settingStack.hide()
        
    def ShowPlayListSettings(self):
        
        # Load the Table with the playlist
        
        
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST.value)
        
    def ShowLibrarySettings(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY.value)
        
    def ShowPlayListEditor(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST_EDITOR.value)
        
    def ShowLibraryEditor(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_EDITOR.value)
        
        