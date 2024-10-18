import sys
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget, QWidget, QTableWidgetItem, QTableWidget, QMessageBox, QFileDialog
from PyQt6.QtGui import QFont
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
         

class ListSettings(DraggableWidget):
    entryRow = -1
    def __init__(self, SettingsManager, ListType: ENUM_SettingsViews):
        super().__init__()
        self.listType = ListType
        self.settingsManager = SettingsManager
        
        self.ui = uic.loadUi("assets/PlayListSettings.ui", self)
        
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.ui.Titlebar_label.setText("PlayList Settings")
            self.editList = self.settingsManager.appData.PlayLists
        elif self.listType == ENUM_SettingsViews.LIBRARY:
            self.ui.Titlebar_label.setText("Library Settings")
            self.editList = self.settingsManager.appData.Library
            columnFont = QFont()
            columnFont.setPointSize(16)
            column0 = QTableWidgetItem("Item Name")
            column0.setFont(columnFont)
            self.ui.PlayList_table.setHorizontalHeaderItem(0, column0)
            
            
        # Set Column Settings 
        self.ui.PlayList_table.setColumnWidth(0, 250)
        self.ui.PlayList_table.setColumnWidth(1, 361)
        self.ui.PlayList_table.setWordWrap(True)
        
        # Setup Slots
        self.ui.Back_button.clicked.connect(self.BackButtonClicked) 
        self.ui.AddNew_button.clicked.connect(self.AddNewEntry)
        self.ui.Edit_button.clicked.connect(self.EditEntry)
        self.ui.Delete_button.clicked.connect(self.DeleteEntry)
        self.ui.PlayList_table.cellClicked.connect(self.RowSelected)
        
        self.UpdateTable()
        
    def BackButtonClicked(self):
        self.settingsManager.ShowSettings()
        
    def UpdateTable(self):        
        # Update the table row count
        self.ui.PlayList_table.setRowCount(len(self.editList)) 
        
        # Update the table contents
        row = 0
        for item in self.editList:
            #print(keys.name, keys.hotkey)
            name = QTableWidgetItem(item.name)
            source = QTableWidgetItem(item.source)
            name.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            source.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.ui.PlayList_table.setItem(row, 0, name)
            self.ui.PlayList_table.setItem(row, 1, source)
            self.ui.PlayList_table.setRowHeight(row, 50)
            row += 1
            
        self.ui.PlayList_table.setCurrentCell(-1,-1)
        
        self.ui.Edit_button.setEnabled(False)
        self.ui.Delete_button.setEnabled(False)
        self.ui.AddNew_button.setEnabled(True)
    
    def UnselectRows(self):
        self.ui.PlayList_table.setCurrentCell(-1,-1)
        self.RowSelected(-1, -1)
        
        
    def RowSelected(self, row, column):
        if row >= 0:
            self.ui.Edit_button.setEnabled(True)
            self.ui.Delete_button.setEnabled(True)
        else:
            self.ui.Edit_button.setEnabled(False)
            self.ui.Delete_button.setEnabled(False)

    def AddNewEntry(self):
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.settingsManager.ShowNewPlayListEditor()
            
        elif self.listType == ENUM_SettingsViews.LIBRARY:   
            self.settingsManager.ShowNewLibraryEditor()
        
    def EditEntry(self):
        self.entryRow = self.ui.PlayList_table.currentRow()
        selectedEntry = self.editList[self.entryRow]
        
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.settingsManager.ShowEditPlayListEditor(selectedEntry)
            
        elif self.listType == ENUM_SettingsViews.LIBRARY:   
            self.settingsManager.ShowEditLibraryEditor(selectedEntry)            
    
    def DeleteEntry(self):
        pass        
        
class EntryEditor(DraggableWidget):
    entryChanged = False
    newEntry = False
    editEntry: PlayListEntry = None
    
    def __init__(self, SettingsManager, EntryType: ENUM_SettingsViews):
        super().__init__()
        self.entryType = EntryType
        self.settingsManager = SettingsManager
        
        self.ui = uic.loadUi("assets/EntryEditor.ui", self)
        
        #self.ui.SourceType_combobox.currentIndexChanged.connect(self.SourceTypeChanged)
        self.ui.Back_button.clicked.connect(self.BackButtonClicked)
        self.ui.OpenFiles_button.clicked.connect(self.OpenFilesButtonClicked)
        
        # Detect Input Changes 
        self.ui.Name_textedit.textChanged.connect(self.EntryChanged)
        self.ui.Source_textedit.textChanged.connect(self.EntryChanged)
        self.ui.SourceType_combobox.currentIndexChanged.connect(self.EntryChanged)
        
        
    def LoadNewEntry(self):
        # Create new entry
        self.blockSignals(True)

        self.editEntry = PlayListEntry(
                name='',
                parentName='',
                sourceType='file',
                source='')
        
        if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
            self.ui.Titlebar_label.setText("PlayList Add New Entry")
            self.ui.EntryName_label.setText("New PlayList Name:")
            
        elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
            self.ui.Titlebar_label.setText("Library Add New Entry")
            self.ui.EntryName_label.setText("New Entry Name:")
            
        self.ui.Name_textedit.setText("")
        self.ui.SourceType_combobox.setCurrentIndex(0)
        self.ui.Source_textedit.setText("")
        self.ui.OpenFiles_button.setEnabled(True)
        self.ui.OpenFiles_button.show()
        self.blockSignals(False)
        
        self.newEntry = True
        self.entryChanged = False

        
    def LoadEntry(self, entry: PlayListEntry):
        if entry == None:
            self.LoadNewEntry()
            return
        
        self.blockSignals(True)
        self.editEntry = entry
        
        if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
            self.ui.Titlebar_label.setText("PlayList Edit Entry")
            self.ui.EntryName_label.setText("PlayList Name:")
            
        elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
            self.ui.Titlebar_label.setText("Library Edit Entry")
            self.ui.EntryName_label.setText("Entry Name:")
            
        self.ui.Name_textedit.setText(entry.name)
        
        if entry.sourceType == 'file':
            self.ui.SourceType_combobox.setCurrentIndex(0)
        elif entry.sourceType == 'url':
            self.ui.SourceType_combobox.setCurrentIndex(1)
            
        self.SourceTypeChanged()
        self.ui.Source_textedit.setText(entry.source)
        self.ui.Save_button.setEnabled(False)
        self.blockSignals(False)
        self.newEntry = False
        self.entryChanged = False
        
    def SourceTypeChanged(self):
        if self.ui.SourceType_combobox.currentIndex() == 0:
            self.ui.OpenFiles_button.setEnabled(True)
            self.ui.OpenFiles_button.show()
        elif self.ui.SourceType_combobox.currentIndex() == 1:
            self.ui.OpenFiles_button.setEnabled(False)
            self.ui.OpenFiles_button.hide()
            
    def BackButtonClicked(self):
        if self.entryChanged:
            # Ask if user wants to save changes in a message box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setText("Do you want to save your changes?")
            msg.setWindowTitle("Save Changes")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes| QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            ret = msg.exec()
            
            if ret == QMessageBox.StandardButton.Yes:
                # Save Changes
                self.SaveButtonClicked()
                if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
                    self.settingsManager.ShowPlayListSettings()
                elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
                    self.settingsManager.ShowLibrarySettings()
                
            elif ret == QMessageBox.StandardButton.No:
                # Delete edit entry
                if self.newEntry:
                    del self.editEntry
                    self.editEntry = None
                    
                if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
                    self.settingsManager.ShowPlayListSettings()
                elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
                    self.settingsManager.ShowLibrarySettings()
                
            elif ret == QMessageBox.StandardButton.Cancel:
                # Do nothing stay on current window
                pass
        else:
            if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
                self.settingsManager.ShowPlayListSettings()
            elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
                self.settingsManager.ShowLibrarySettings()
        
    def SaveButtonClicked(self):
        pass
    
            
    def EntryChanged(self):
        if self.editEntry == None:
            return
        
        if self.ui.Name_textedit.text() != self.editEntry.name or self.ui.SourceType_combobox.currentText() != self.editEntry.sourceType or self.ui.Source_textedit.toPlainText() != self.editEntry.source:
            self.entryChanged = True
            self.SourceTypeChanged()
            self.ui.Save_button.setEnabled(True)
        else:
            self.entryChanged = False
            self.ui.Save_button.setEnabled(False)
    

    def OpenFilesButtonClicked(self):
         # Open File Dialog
        if self.entryType == ENUM_SettingsViews.PLAYLIST_EDITOR:
            filename, _ = QFileDialog.getOpenFileName(self, "Select PlayList File", "", "PlayList Files (*.m3u *.m3u8)")
        elif self.entryType == ENUM_SettingsViews.LIBRARY_EDITOR:
            filename, _ = QFileDialog.getOpenFileName(self, "Select a Media File", "", "Media Files (*.mkv *.mp4 *.avi *.mov *.mp3 *.wmv *.wav *.mpg, *.mpeg *.m4v)")
        
        if filename:
            self.ui.Source_textedit.setPlainText(filename)             

class SettingsManager():
    def __init__(self, appData: AppData):
        self.appData = appData
        
        self.settingStack = QStackedWidget()
        
        self.SettingsIntro = SettingsIntro(self)
        self.PlayListSettings = ListSettings(self, ENUM_SettingsViews.PLAYLIST)
        self.LibrarySettings = ListSettings(self, ENUM_SettingsViews.LIBRARY)
        self.PlayListEditor = EntryEditor(self, ENUM_SettingsViews.PLAYLIST_EDITOR)
        self.LibraryEditor = EntryEditor(self, ENUM_SettingsViews.LIBRARY_EDITOR)
        
        
        
        self.settingStack.addWidget(self.SettingsIntro)
        self.settingStack.addWidget(self.PlayListSettings)
        self.settingStack.addWidget(self.LibrarySettings)
        self.settingStack.addWidget(self.PlayListEditor)
        self.settingStack.addWidget(self.LibraryEditor)
        
        self.settingStack.setFixedWidth(780)
        self.settingStack.setFixedHeight(430) 
        
        self.settingStack.setWindowFlags(Qt.WindowType.FramelessWindowHint)  
        self.settingStack.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        
    def ShowSettings(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.INTRO.value)
        self.settingStack.show()
        
    def HideSettings(self):
        self.settingStack.hide()
        
    def ShowPlayListSettings(self):
        self.PlayListSettings.UnselectRows()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST.value)
        
    def ShowLibrarySettings(self):
        self.LibrarySettings.UnselectRows()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY.value)
        
    def ShowNewLibraryEditor(self):
        self.LibraryEditor.LoadNewEntry()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_EDITOR.value)  
        
    def ShowEditLibraryEditor(self, editEntry: PlayListEntry):
        self.LibraryEditor.LoadEntry(editEntry)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_EDITOR.value)  
        
    def ShowEditPlayListEditor(self, editEntry: PlayListEntry):
        self.PlayListEditor.LoadEntry(editEntry)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST_EDITOR.value)
        
    def ShowNewPlayListEditor(self):
        self.PlayListEditor.LoadNewEntry()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST_EDITOR.value)
        
    def ShowLibraryEditor(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_EDITOR.value)
        
        