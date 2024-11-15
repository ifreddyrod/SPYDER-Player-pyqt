import sys
from PyQt6 import uic
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QComboBox, QTableWidgetItem, QTableWidget, QMessageBox, QFileDialog, QStyledItemDelegate
from PyQt6.QtGui import QFont, QIcon
from DraggableWidget import DraggableWidget
from enum import Enum
from AppData import * 
import platform
import copy
import os

# Import Converted UI Files
from UI_Settings import Ui_SettingsMain
from UI_PlayListSettings import Ui_PlayListSettings
from UI_EntryEditor import Ui_EntryEditor
from UI_OpenFileSelection import Ui_OpenFileSelection
from UI_PlayerSettings import Ui_PlayerSettings
from UI_HotkeySettings import Ui_HotKeySettings

class ENUM_SettingsViews(Enum):
    INTRO = 0
    PLAYLIST = 1 
    LIBRARY  = 2
    FAVORITES = 3
    PLAYLIST_ENTRY = 4
    LIBRARY_ENTRY = 5
    FAVORITES_ENTRY = 6
    OPEN_PLAYLIST = 7
    OPEN_FILE = 8
    APPSETTINGS = 9
    HOTKEYS = 10
    
    
class SettingsIntro(DraggableWidget):
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        self.ui = Ui_SettingsMain()
        self.ui.setupUi(self)
        
        self.ui.Close_button.clicked.connect(self.settingsManager.HideSettings)
        self.ui.PlayList_button.clicked.connect(self.settingsManager.ShowPlayListSettings)
        self.ui.Library_button.clicked.connect(self.settingsManager.ShowLibrarySettings)
        self.ui.Favorites_button.clicked.connect(self.settingsManager.ShowFavoritesSettings)
        self.ui.HotKeys_button.clicked.connect(self.HotKeysButtonClicked)
        self.ui.OpenMediaFile_button.clicked.connect(self.settingsManager.ShowOpenFileSelector)
        self.ui.OpenPlayList_button.clicked.connect(self.settingsManager.ShowOpenPlayListSelector)
        self.ui.PlayerSettings_button.clicked.connect(self.settingsManager.ShowPlayerSettings)
        self.ui.HotKeys_button.clicked.connect(self.settingsManager.ShowHotKeySettings)
  
    def HotKeysButtonClicked(self):
        #self.SettingsManager.ShowHotKeySettings()
        pass
        
 
class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.enabled = True
        
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        editor.setEnabled(self.enabled)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        
    def set_enabled(self, enabled):
        self.enabled = enabled
   
class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return None
                   
class HotkeySettings(DraggableWidget):  
    hotkeyList = []
    
    def __init__(self, SettingsManager):
        super().__init__()
        self.settingsManager = SettingsManager
        self.appHotKeys = SettingsManager.appData.HotKeys
        self.ui = Ui_HotKeySettings()
        self.ui.setupUi(self)
        
        # Set Column Settings 
        self.ui.HotKeys_table.setColumnWidth(0, 250)
        self.ui.HotKeys_table.setColumnWidth(1, 350)
        self.ui.HotKeys_table.setWordWrap(True)
        #self.ui.HotKeys_table.set
        
        self.LoadHotkeyList()
         
        self.ui.Apply_button.hide()
        self.ui.Cancel_button.hide()
         
        self.ui.Back_button.clicked.connect(self.BackButtonClicked) 
        self.ui.Apply_button.clicked.connect(self.ApplyChanges)
        self.ui.Cancel_button.clicked.connect(self.CancelChanges)
        self.ui.Edit_button.clicked.connect(self.EditButtonClicked)
        self.ui.HotKeys_table.itemChanged.connect(self.HotkeyChanged)
        
    def BackButtonClicked(self):
        self.settingsManager.ShowSettings()
                
    def LoadHotkeyList(self):
        self.ui.HotKeys_table.clearContents() 
        self.hotkeyList.clear()
        
        #for name, hotkey in self.settingsManager.appData.HotKeys.__dict__.items():
            #print(name + ": " + Qt.Key(hotkey).name)
        #self.appHotKeys = self.settingsManager.appData.HotKeys
                
        # Get Hotkeys from AppData
        for name, hotkey in self.appHotKeys.__dict__.items():   
            self.hotkeyList.append([name, Qt.Key(hotkey).name, Qt.Key(hotkey)])  
               
       
        self.ui.HotKeys_table.setRowCount(len(self.hotkeyList))
        hkItems = Qt.Key._member_names_ 
        self.hkComboBox = ComboBoxDelegate(hkItems) 
        self.playerAction = ReadOnlyDelegate()
        self.ui.HotKeys_table.setItemDelegateForColumn(0, self.playerAction)
        self.ui.HotKeys_table.setItemDelegateForColumn(1, self.hkComboBox)
         
        # Update Table with Hotkeys      
        for idx, item in enumerate(self.hotkeyList): 
            action = item[0]
            hotkeyname = item[1]
            hotkey = item[2]
                  
            hkIndex = hkItems.index(hotkeyname) 
            actionItem = QTableWidgetItem(action)
            actionItem.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            hotkeyItem = QTableWidgetItem(hkItems[hkIndex])
            hotkeyItem.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            
            self.ui.HotKeys_table.setItem(idx, 0, actionItem)  
            self.ui.HotKeys_table.setItem(idx, 1, hotkeyItem)
            
        self.hkComboBox.set_enabled(False)    
            
    def EditButtonClicked(self):
        self.hkComboBox.set_enabled(True)
        
        self.ui.Apply_button.show()
        self.ui.Cancel_button.show()
        self.ui.Edit_button.hide()
        self.ui.Back_button.hide()
        self.changed = False
        
    def CancelChanges(self):
        self.hkComboBox.set_enabled(False)
        self.ui.Apply_button.hide()
        self.ui.Cancel_button.hide()
        self.ui.Edit_button.show()
        self.ui.Back_button.show()
        self.LoadHotkeyList()
        self.changed = False
        
    def ApplyChanges(self):
        if self.changed:
            # Check for duplicate hotkey names
            if self.CheckForDuplicateHotkeys():
                QMessageBox.warning(self, "Hotkey Error", "Duplicate hotkey detected!  Please select unique hotkeys.", QMessageBox.StandardButton.Ok)
                return
            
            for row in range(self.ui.HotKeys_table.rowCount()):
                self.settingsManager.appData.HotKeys.__dict__[self.ui.HotKeys_table.item(row, 0).text()] = getattr(Qt.Key, self.ui.HotKeys_table.item(row, 1).text())
            
            self.settingsManager.appData.save()
            #self.appHotKeys = self.settingsManager.appData.HotKeys
            #self.settingsManager = self.settingsManager.SaveRefresh()
            
            #for name, hotkey in self.settingsManager.appData.HotKeys.__dict__.items():
                #print(name + ": " + str(hotkey))

        #self.LoadHotkeyList()
        self.CancelChanges()
        
    def CheckForDuplicateHotkeys(self) -> bool:
        tableList = []
        # Convert table keys to list
        for row in range(self.ui.HotKeys_table.rowCount()):
            tableList.append(self.ui.HotKeys_table.item(row, 1).text())
            
        # Compare Sizes of Lists
        if len(tableList) != len(set(tableList)):
            return True
        else:
            return False
        
        
    def HotkeyChanged(self, item):
        row = self.ui.HotKeys_table.currentRow()
        
        #if self.ui.HotKeys_table.item(row, 1).text() != self.hotkeyList[row][1]:  
        if item.text() != self.hotkeyList[row][1]:
            self.changed = True
                        
                
class ListSettings(DraggableWidget):
    entryRow = -1
    editList: List[PlayListEntry] = []
    tempList: List[PlayListEntry] = []
    reordering: bool = False
    
    def __init__(self, SettingsManager, ListType: ENUM_SettingsViews):
        super().__init__()
        self.listType = ListType
        self.settingsManager = SettingsManager
        
        self.ui = Ui_PlayListSettings()
        self.ui.setupUi(self)
        
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.ui.Titlebar_label.setText("PlayLists Editor")
            self.editList = self.settingsManager.appData.PlayLists
        elif self.listType == ENUM_SettingsViews.LIBRARY:
            self.ui.Titlebar_label.setText("Library Editor")
            self.editList = self.settingsManager.appData.Library
            columnFont = QFont()
            columnFont.setPointSize(14)
            column0 = QTableWidgetItem("Library Entry Name")
            column0.setFont(columnFont)
            self.ui.PlayList_table.setHorizontalHeaderItem(0, column0)
        elif self.listType == ENUM_SettingsViews.FAVORITES:
            self.ui.Titlebar_label.setText("Favorites Editor")
            self.editList = self.settingsManager.appData.Favorites
            columnFont = QFont()
            columnFont.setPointSize(14)
            column0 = QTableWidgetItem("Favorite Name")
            column0.setFont(columnFont)
            self.ui.PlayList_table.setHorizontalHeaderItem(0, column0)  
            self.ui.AddNew_button.hide()  
            self.ui.Edit_button.setIcon(QIcon(":/icons/icons/white-diskette.png"))
            self.ui.Edit_button.setText(" Save as...")
            self.ui.Edit_button.setEnabled(True)
            
        # Set Column Settings 
        self.ui.PlayList_table.setColumnWidth(0, 250)
        self.ui.PlayList_table.setColumnWidth(1, 360)
        self.ui.PlayList_table.setWordWrap(True)
        self.columns = ReadOnlyDelegate()
        self.ui.PlayList_table.setItemDelegateForColumn(0, self.columns)
        self.ui.PlayList_table.setItemDelegateForColumn(1, self.columns)
        
        # Setup Slots
        self.ui.Back_button.clicked.connect(self.BackButtonClicked) 
        self.ui.AddNew_button.clicked.connect(self.AddNewEntry)
        self.ui.Edit_button.clicked.connect(self.EditEntry)
        self.ui.Delete_button.clicked.connect(self.DeleteEntry)
        self.ui.PlayList_table.cellClicked.connect(self.RowSelected)
        self.ui.Reorder_button.clicked.connect(self.Reorder)
        self.ui.Apply_button.clicked.connect(self.ApplyChanges)
        self.ui.Cancel_button.clicked.connect(self.CancelChanges)
        
        self.ui.PlayList_table.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.ui.PlayList_table.setDragEnabled(False)
        self.ui.PlayList_table.setAcceptDrops(False)     

        self.ui.Apply_button.hide()
        self.ui.Cancel_button.hide()           
        self.ui.PlayList_table.dropEvent = self.dropEvent
       
    def ResetList(self, entryList: List[PlayListEntry]):
        self.editList = entryList
         
    def dropEvent(self, event):
        if event.source() == self.ui.PlayList_table and self.reordering:
            # Get the row being dragged
            selected_row = self.ui.PlayList_table.selectedItems()[0].row()
            
            # Get the target row
            drop_row = self.ui.PlayList_table.rowAt(event.position().toPoint().y())
            
            # If dropping below the last row, move to the end
            if drop_row == -1:
                drop_row = len(self.tempList)
                
            # Prevent dropping on itself
            if selected_row == drop_row:
                event.ignore()
                return
                
            # Get all data from the row being moved
            moving_item = self.tempList.pop(selected_row)
            
            # Insert the item at the new position
            self.tempList.insert(drop_row if drop_row < selected_row else drop_row, moving_item)
            
            # Select the moved row
            self.ui.PlayList_table.selectRow(drop_row if drop_row < selected_row else drop_row)
            
            self.UpdateTable()
            event.accept()
        else:
            event.ignore()
            
    def Reorder(self):
        self.ui.PlayList_table.setDragEnabled(True)
        self.ui.PlayList_table.setAcceptDrops(True)
        self.ui.AddNew_button.setEnabled(False)
        self.ui.Delete_button.setEnabled(False)
        self.ui.Reorder_button.setEnabled(False)
        self.ui.Back_button.setEnabled(False)     
        if self.listType == ENUM_SettingsViews.FAVORITES: 
            self.ui.Edit_button.setEnabled(False)
            self.ui.Edit_button.setIcon(QIcon(":/icons/icons/white-diskette-disabled.png")) 
        else:
            self.ui.Edit_button.setEnabled(False)  
        self.ui.Apply_button.show()
        self.ui.Cancel_button.show()
        self.reordering = True
        self.tempList = copy.deepcopy(self.editList)
        
    def ApplyChanges(self):
        self.ui.PlayList_table.setDragEnabled(False)
        self.ui.PlayList_table.setAcceptDrops(False)
        self.ui.Apply_button.hide()
        self.ui.Cancel_button.hide()
        self.reordering = False
        
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.settingsManager.appData.PlayLists = copy.deepcopy(self.tempList)
        elif self.listType == ENUM_SettingsViews.LIBRARY:
            self.settingsManager.appData.Library = copy.deepcopy(self.tempList)
        elif self.listType == ENUM_SettingsViews.FAVORITES:
            self.settingsManager.appData.Favorites = copy.deepcopy(self.tempList)
            
        self.settingsManager.changesMade = True
        self.SaveData()
        
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.editList = self.settingsManager.appData.PlayLists
        elif self.listType == ENUM_SettingsViews.LIBRARY:
            self.editList = self.settingsManager.appData.Library
        elif self.listType == ENUM_SettingsViews.FAVORITES:
            self.editList = self.settingsManager.appData.Favorites
        
        self.UpdateTable()  
        
        
    def CancelChanges(self):
        self.ui.PlayList_table.setDragEnabled(False)
        self.ui.PlayList_table.setAcceptDrops(False)
        self.ui.Apply_button.hide()
        self.ui.Cancel_button.hide()  
        self.reordering = False
        self.UpdateTable()       
        
                
    def BackButtonClicked(self):
        self.settingsManager.ShowSettings()
        
    def UpdateTable(self):               
        # Clear the table
        self.ui.PlayList_table.clearContents()   
          
        # Update the table row count
        if self.reordering:
            displayList = self.tempList
        else:
            displayList = self.editList
        
        self.ui.PlayList_table.setRowCount(len(displayList)) 
        
        # Update the table
        for row, item in enumerate(displayList):
            name = QTableWidgetItem(item.name)
            source = QTableWidgetItem(item.source)
            name.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            source.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            self.ui.PlayList_table.setItem(row, 0, name)
            self.ui.PlayList_table.setItem(row, 1, source)
            self.ui.PlayList_table.setRowHeight(row, 50)
            row += 1
         
        # Enable buttons if not currently reordering
        if not self.reordering:    
            self.ui.PlayList_table.setCurrentCell(-1,-1)
            
            self.ui.AddNew_button.setEnabled(True)
            
            if len(displayList) > 0:
                self.ui.Delete_button.setEnabled(False)                
                self.ui.Reorder_button.setEnabled(True)                
                if self.listType == ENUM_SettingsViews.FAVORITES: 
                    self.ui.Edit_button.setEnabled(True)
                    self.ui.Edit_button.setIcon(QIcon(":/icons/icons/white-diskette.png"))
                else:
                    self.ui.Edit_button.setEnabled(False)
            else:
                self.ui.Delete_button.setEnabled(False)
                self.ui.Reorder_button.setEnabled(False)
                self.ui.Edit_button.setEnabled(False)
                if self.listType == ENUM_SettingsViews.FAVORITES: 
                    self.ui.Edit_button.setIcon(QIcon(":/icons/icons/white-diskette-disabled.png"))
                    self.ui.Edit_button.setEnabled(False)
            self.ui.Back_button.setEnabled(True) 
    
    def UnselectRows(self):
        self.ui.PlayList_table.setCurrentCell(-1,-1)
        self.RowSelected(-1, -1)
        
        
    def RowSelected(self, row, column):
        if row >= 0:
            self.ui.Edit_button.setEnabled(True)
            self.ui.Delete_button.setEnabled(True)
        elif self.listType != ENUM_SettingsViews.FAVORITES:
            self.ui.Edit_button.setEnabled(False)
            self.ui.Delete_button.setEnabled(False)

    def AddNewEntry(self):
        if self.listType == ENUM_SettingsViews.PLAYLIST:
            self.settingsManager.ShowNewPlayListEditor(self.editList)
            
        elif self.listType == ENUM_SettingsViews.LIBRARY:   
            self.settingsManager.ShowNewLibraryEditor(self.editList)
        
    def EditEntry(self):
        if self.listType == ENUM_SettingsViews.FAVORITES:
            self.settingsManager.ShowSaveFavoritesAsEditor(self.editList)
        else:
            self.entryRow = self.ui.PlayList_table.currentRow()
            #selectedEntry = self.editList[self.entryRow]
            
            if self.listType == ENUM_SettingsViews.PLAYLIST:
                self.settingsManager.ShowEditPlayListEditor(self.editList, self.entryRow)
                
            elif self.listType == ENUM_SettingsViews.LIBRARY:   
                self.settingsManager.ShowEditLibraryEditor(self.editList, self.entryRow)           
    
    def DeleteEntry(self): 
        if len(self.editList) == 0:
            return
        
        self.entryRow = self.ui.PlayList_table.currentRow()
        
        self.editList.pop(self.entryRow)
        self.settingsManager.changesMade = True
        self.SaveData()
        self.UpdateTable()
    
    def SaveData(self):
        self.settingsManager.appData.save()
        
        
class PlayerSettings(DraggableWidget):
    def __init__(self, SettingsManager, EntryType: ENUM_SettingsViews):
        super().__init__()
        
        self.settingsManager = SettingsManager
        self.entryType = EntryType
        
        self.ui = Ui_PlayerSettings()
        self.ui.setupUi(self)
        
        self.ui.Back_button.clicked.connect(self.BackButtonClicked)
        self.ui.PlayerType_combobox.currentIndexChanged.connect(self.PlayerTypeChanged)
        
    def ShowPlayerSettings(self):
        self.ui.PlayerType_combobox.setCurrentText(self.settingsManager.appData.PlayerType.name)
        
    def BackButtonClicked(self):
        self.settingsManager.SaveSettings()
        self.settingsManager.ShowSettings()
        
    def PlayerTypeChanged(self):
        self.settingsManager.changesMade = True
        self.settingsManager.appData.PlayerType = ENUM_PLAYER_TYPE(self.ui.PlayerType_combobox.currentText())
        print("New Player Type: " + self.settingsManager.appData.PlayerType.name)
 
                    
class EntryEditor(DraggableWidget):
    entryChanged = False
    newEntry = False
    editEntry: PlayListEntry = None
    editList: List[PlayListEntry] = []
    editListIndex: int = -1
    
    def __init__(self, SettingsManager, EntryType: ENUM_SettingsViews):
        super().__init__()
        self.entryType = EntryType
        self.settingsManager = SettingsManager
        
        self.ui = Ui_EntryEditor()
        self.ui.setupUi(self)
        
        
        #self.ui.SourceType_combobox.currentIndexChanged.connect(self.SourceTypeChanged)
        self.ui.Back_button.clicked.connect(self.BackButtonClicked)
        self.ui.OpenFiles_button.clicked.connect(self.OpenFilesButtonClicked)
        self.ui.Save_button.clicked.connect(self.SaveButtonClicked)
        
        # Detect Input Changes 
        self.ui.Name_textedit.textChanged.connect(self.EntryChanged)
        self.ui.Source_textedit.textChanged.connect(self.EntryChanged)
        self.ui.SourceType_combobox.currentIndexChanged.connect(self.EntryChanged)
        
        
    def LoadNewEntry(self, editList: List[PlayListEntry]):
        # Create new entry
        self.blockSignals(True)
        self.editList = editList
        
        self.editEntry = PlayListEntry(
                name='',
                parentName='',
                sourceType='file',
                source='')
        
        if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
            self.ui.Titlebar_label.setText("PlayList Add New Entry")
            self.ui.EntryName_label.setText("New PlayList Name:")
            
        elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
            self.ui.Titlebar_label.setText("Library Add New Entry")
            self.ui.EntryName_label.setText("New Entry Name:")
        
        elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
            self.ui.Titlebar_label.setText("Save Favorites As New List")
            self.ui.EntryName_label.setText("New PlayList Name:") 
            self.ui.SourceType_combobox.setEnabled(False)
            self.ui.Name_textedit.setPlaceholderText("Enter a unique name for your new list")   
            self.ui.Source_label.setText("File Path:")  
            self.ui.Source_textedit.setPlaceholderText("Enter file name and path")  

     
        self.ui.Name_textedit.setText("")
        self.ui.SourceType_combobox.setCurrentIndex(0)
        self.ui.Source_textedit.setText("")
        self.ui.OpenFiles_button.setEnabled(True)
        self.ui.OpenFiles_button.show()
        self.blockSignals(False)
        
        self.newEntry = True
        self.entryChanged = False

        
    def LoadEntry(self, editList: List[PlayListEntry], index):
        if editList == None or index < 0:
            return
        
        entry = editList[index]
        self.editList = editList
        self.editListIndex = index
        
        if entry == None:
            self.LoadNewEntry()
            return
        
        self.blockSignals(True)
        self.editEntry = entry
        
        if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
            self.ui.Titlebar_label.setText("PlayList Edit Entry")
            self.ui.EntryName_label.setText("PlayList Name:")
            
        elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
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
                
            elif ret == QMessageBox.StandardButton.No:
                # Delete edit entry
                if self.newEntry:
                    del self.editEntry
                    self.editEntry = None
                    
                if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
                    self.settingsManager.ShowPlayListSettings(False)
                elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
                    self.settingsManager.ShowLibrarySettings(False)
                elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
                    self.settingsManager.ShowFavoritesSettings(False)
                
            elif ret == QMessageBox.StandardButton.Cancel:
                # Do nothing stay on current window
                pass 
        else:
            if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
                self.settingsManager.ShowPlayListSettings()
            elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
                self.settingsManager.ShowLibrarySettings()
            elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
                self.settingsManager.ShowFavoritesSettings()
                    
    def SaveButtonClicked(self):
        if self.newEntry:
            self.editEntry.name = self.ui.Name_textedit.text()
            self.editEntry.sourceType = self.ui.SourceType_combobox.currentText()
            self.editEntry.source = self.ui.Source_textedit.toPlainText()
            
            if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
                parentName = '' 
                self.editEntry.parentName = parentName
                self.editList.append(self.editEntry)
            elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
                parentName = 'Library'
                self.editEntry.parentName = parentName
                self.editList.append(self.editEntry)
            elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
                self.editEntry.parentName = ''
             
                # Save Favorites List to m3u file
                SavePlayListToFile(self.editList, self.editEntry.source)
                
                if os.path.exists(self.editEntry.source):
                    print(f"Favorites List saved to {self.editEntry.source}")
                    # Add entry to AppData PlayLists
                    self.settingsManager.appData.PlayLists.append(self.editEntry)
                    # Remove all items from favorites list
                    self.settingsManager.appData.Favorites = []         

        else:
            self.editList[self.editListIndex].name = self.ui.Name_textedit.text()
            self.editList[self.editListIndex].sourceType = self.ui.SourceType_combobox.currentText()
            self.editList[self.editListIndex].source = self.ui.Source_textedit.toPlainText()
        
        # Save Changes to AppData
        self.settingsManager.changesMade = True
        self.settingsManager.SaveSettings()
        
        # Go back to previous window
        if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
            self.settingsManager.ShowPlayListSettings(True)
        elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
            self.settingsManager.ShowLibrarySettings(True)
        elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
            self.settingsManager.ShowFavoritesSettings(True)
            
            
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
        if self.entryType == ENUM_SettingsViews.PLAYLIST_ENTRY:
            filename, _ = QFileDialog.getOpenFileName(self, "Select PlayList File", "", "PlayList Files (*.m3u *.m3u8)")
        elif self.entryType == ENUM_SettingsViews.LIBRARY_ENTRY:
            filename, _ = QFileDialog.getOpenFileName(self, "Select a Media File", "", "Media Files (*.mkv *.mp4 *.avi *.mov *.mp3 *.wmv *.wav *.mpg, *.mpeg *.m4v)")
        elif self.entryType == ENUM_SettingsViews.FAVORITES_ENTRY:
            filename, _ = QFileDialog.getSaveFileName(self, "Enter new Playlist File", "", "PlayList File (*.m3u)")
            
            '''if os.path.exists(filename):  
                # Warn user of duplicate file 
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("File already in use")
                msg.setInformativeText("File already exists. Do you want to overwrite it?")
                msg.setWindowTitle("Duplicate File")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes| QMessageBox.StandardButton.No)
                ret = msg.exec()
            
                if ret == QMessageBox.StandardButton.Yes:
                    pass
                else: 
                    # Reshow Open Files Dialog
                    self.OpenFilesButtonClicked() 
                    return'''
            
        if filename:
            self.ui.Source_textedit.setPlainText(filename)             


class OpenFileSelection(DraggableWidget):
    entryChanged = False
    newEntry: PlayListEntry = None
        
    def __init__(self, SettingsManager, EntryType: ENUM_SettingsViews):
        super().__init__()
        self.entryType = EntryType
        self.settingsManager = SettingsManager
        
        self.ui = Ui_OpenFileSelection()
        self.ui.setupUi(self)
        
        self.ui.Open_button.setEnabled(False)    
        
        self.ui.Back_button.clicked.connect(self.BackButtonClicked)
        self.ui.Open_button.clicked.connect(self.OpenButtonClicked)
        self.ui.OpenFiles_button.clicked.connect(self.OpenFilesButtonClicked)
        self.ui.Source_textedit.textChanged.connect(self.EntryChanged)
        self.ui.SourceType_combobox.currentIndexChanged.connect(self.EntryChanged)
        
    def ShowEmptyFileSelection(self):  
        # Create new entry
        self.blockSignals(True)
        
        self.newEntry = PlayListEntry(
                name='',
                parentName='',
                sourceType='file',
                source='')
        
        if self.entryType == ENUM_SettingsViews.OPEN_FILE:
            self.ui.Titlebar_label.setText("Open Local File or Paste URL")  
             
        elif self.entryType == ENUM_SettingsViews.OPEN_PLAYLIST:
            self.ui.Titlebar_label.setText("Enter a PlayList File or Paste URL")

        self.ui.SourceType_combobox.setCurrentIndex(0)
        self.ui.Source_textedit.setText("")
        self.ui.OpenFiles_button.setEnabled(True)
        self.ui.OpenFiles_button.show()
        self.blockSignals(False)
        self.entryChanged = False
        
    def BackButtonClicked(self):    
        if self.newEntry != None:
            del self.newEntry
            
        self.settingsManager.ShowSettings()
             
    def EntryChanged(self):
        if  self.ui.SourceType_combobox.currentText() != self.newEntry.sourceType or self.ui.Source_textedit.toPlainText() != self.newEntry.source:
            self.entryChanged = True
            self.SourceTypeChanged()
            self.ui.Open_button.setEnabled(True)
        else:
            self.entryChanged = False
            self.ui.Open_button.setEnabled(False)    
    
    def SourceTypeChanged(self):
        if self.ui.SourceType_combobox.currentIndex() == 0:
            self.ui.OpenFiles_button.setEnabled(True)
            self.ui.OpenFiles_button.show()
        elif self.ui.SourceType_combobox.currentIndex() == 1:
            self.ui.OpenFiles_button.setEnabled(False)
            self.ui.OpenFiles_button.hide()
                
    def OpenFilesButtonClicked(self):
         # Open File Dialog
        if self.entryType == ENUM_SettingsViews.OPEN_PLAYLIST:
            filename, _ = QFileDialog.getOpenFileName(self, "Select PlayList File", "", "PlayList Files (*.m3u *.m3u8)")
        elif self.entryType == ENUM_SettingsViews.OPEN_FILE:
            filename, _ = QFileDialog.getOpenFileName(self, "Select a Media File", "", "Media Files (*.mkv *.mp4 *.avi *.mov *.mp3 *.wmv *.wav *.mpg, *.mpeg *.m4v)")
        
        if filename:
            self.ui.Source_textedit.setPlainText(filename)   
            self.ui.Open_button.setEnabled(True)   
            
    def OpenButtonClicked(self):
        if self.entryChanged == True and self.entryType == ENUM_SettingsViews.OPEN_FILE:             
            self.newEntry.parentName = "Opened Files"
            self.newEntry.sourceType = self.ui.SourceType_combobox.currentText()
            self.newEntry.source = self.ui.Source_textedit.toPlainText()
            
            if self.newEntry.sourceType == 'file':
                name, extension = os.path.splitext(os.path.basename(self.newEntry.source))
                self.newEntry.name = name + extension
            elif self.newEntry.sourceType == 'url':
                if self.newEntry.source.startswith('http://'):
                    name = self.newEntry.source.split('http://')[1]  
                    self.newEntry.name = name
                elif self.newEntry.source.startswith('https://'):
                    name = self.newEntry.source.split('https://')[1]  
                    self.newEntry.name = name
                else:
                    self.newEntry.name = self.newEntry.source

            self.settingsManager.LoadMediaFile(self.newEntry)
        elif self.entryChanged == True and self.entryType == ENUM_SettingsViews.OPEN_PLAYLIST:
            
            self.newEntry.sourceType = self.ui.SourceType_combobox.currentText()
            self.newEntry.source = self.ui.Source_textedit.toPlainText()
            
            if self.newEntry.sourceType == 'file':
                name, extension = os.path.splitext(os.path.basename(self.newEntry.source))
                self.newEntry.name = name
                self.newEntry.parentName = name
            elif self.newEntry.sourceType == 'url':
                if self.newEntry.source.startswith('http://'):
                    name = self.newEntry.source.split('http://')[1]  
                    name = name.split('/')
                    if len(name) > 0:
                        name = name[len(name)-1]
                    else:
                        name = name[0]
                    self.newEntry.name = name
                    self.newEntry.parentName = name
                elif self.newEntry.source.startswith('https://'):
                    name = self.newEntry.source.split('https://')[1]  
                    name = name.split('/')
                    if len(name) > 0:
                        name = name[len(name)-1]
                    else:
                        name = name[0]
                    self.newEntry.name = name
                    self.newEntry.parentName = name
                else:
                    self.newEntry.name = self.newEntry.source
                    self.newEntry.parentName = self.newEntry.name
            self.settingsManager.LoadPlayList(self.newEntry)
              
        
class SettingsManager(QObject):
    platform = platform.system()
    changesMade = False
    reLoadAllPlayListsSignal = pyqtSignal()
    loadMediaFileSignal = pyqtSignal(PlayListEntry)
    loadPlayListSignal = pyqtSignal(PlayListEntry)
    
    def __init__(self, appData: AppData):
        super().__init__()
        
        self.appData = appData
        
        self.settingStack = QStackedWidget()
        
        self.SettingsIntro = SettingsIntro(self)
        self.PlayListSettings = ListSettings(self, ENUM_SettingsViews.PLAYLIST)
        self.LibrarySettings = ListSettings(self, ENUM_SettingsViews.LIBRARY)
        self.FavoritesSettings = ListSettings(self, ENUM_SettingsViews.FAVORITES)
        self.PlayListEditor = EntryEditor(self, ENUM_SettingsViews.PLAYLIST_ENTRY)
        self.LibraryEditor = EntryEditor(self, ENUM_SettingsViews.LIBRARY_ENTRY)
        self.FavoritesEditor = EntryEditor(self, ENUM_SettingsViews.FAVORITES_ENTRY)
        self.OpenFileSelector = OpenFileSelection(self, ENUM_SettingsViews.OPEN_FILE)
        self.OpenPlayListSelector = OpenFileSelection(self, ENUM_SettingsViews.OPEN_PLAYLIST)
        self.PlayerSettings = PlayerSettings(self, ENUM_SettingsViews.APPSETTINGS)
        self.HotKeySettings = HotkeySettings(self)
        
        
        self.settingStack.addWidget(self.SettingsIntro)
        self.settingStack.addWidget(self.PlayListSettings)
        self.settingStack.addWidget(self.LibrarySettings)
        self.settingStack.addWidget(self.FavoritesSettings)
        self.settingStack.addWidget(self.PlayListEditor)
        self.settingStack.addWidget(self.LibraryEditor)
        self.settingStack.addWidget(self.FavoritesEditor)
        self.settingStack.addWidget(self.OpenPlayListSelector)
        self.settingStack.addWidget(self.OpenFileSelector)
        self.settingStack.addWidget(self.PlayerSettings)
        self.settingStack.addWidget(self.HotKeySettings)
        
        self.settingStack.setFixedWidth(780)
        self.settingStack.setFixedHeight(430) 
        
        self.settingStack.setWindowFlags(Qt.WindowType.FramelessWindowHint) # | Qt.WindowType.WindowStaysOnTopHint) 
        
        #if self.platform == "Linux": 
        self.settingStack.setWindowModality(Qt.WindowModality.ApplicationModal)
        
      
    def ShowSettingsFirst(self):
        self.changesMade = False
        self.ShowSettings()
            
    def ShowSettings(self):
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.INTRO.value)
        self.settingStack.show()
        
    def HideSettings(self):
        self.settingStack.hide()
        if self.changesMade:
            self.reLoadAllPlayListsSignal.emit()
            
    def ShowOpenFileSelector(self):
        self.OpenFileSelector.ShowEmptyFileSelection()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.OPEN_FILE.value)
        
    def ShowOpenPlayListSelector(self):
        self.OpenPlayListSelector.ShowEmptyFileSelection()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.OPEN_PLAYLIST.value)
        
    def ShowPlayListSettings(self, changesMade: bool = False):
        self.changesMade |= changesMade
        if self.changesMade:
            self.PlayListSettings.ResetList(self.appData.PlayLists)
        self.PlayListSettings.UpdateTable()
        self.PlayListSettings.UnselectRows()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST.value)
        
    def ShowLibrarySettings(self, changesMade: bool = False):
        self.changesMade |= changesMade
        if self.changesMade:
            self.LibrarySettings.ResetList(self.appData.Library)
        self.LibrarySettings.UpdateTable()
        self.LibrarySettings.UnselectRows()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY.value)
        
    def ShowFavoritesSettings(self, changesMade: bool = False):
        self.changesMade |= changesMade
        if self.changesMade:
            self.FavoritesSettings.ResetList(self.appData.Favorites)
        self.FavoritesSettings.UpdateTable()
        self.FavoritesSettings.UnselectRows()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.FAVORITES.value)
        
    def ShowNewLibraryEditor(self, editList: List[PlayListEntry]):
        self.LibraryEditor.LoadNewEntry(editList)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_ENTRY.value)  
       
    def ShowNewPlayListEditor(self, editList: List[PlayListEntry]):
        self.PlayListEditor.LoadNewEntry(editList)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST_ENTRY.value)
                
    def ShowEditLibraryEditor(self, editList: List[PlayListEntry], row):
        self.LibraryEditor.LoadEntry(editList, row)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.LIBRARY_ENTRY.value)  
        
    def ShowEditPlayListEditor(self, editList: List[PlayListEntry], row):
        self.PlayListEditor.LoadEntry(editList, row)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.PLAYLIST_ENTRY.value)
     
    def ShowSaveFavoritesAsEditor(self, editList: List[PlayListEntry]):
        self.FavoritesEditor.LoadNewEntry(editList)
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.FAVORITES_ENTRY.value)
              
    def SaveSettings(self):
        if self.changesMade:
            self.appData.save()
                 
    def LoadMediaFile(self, fileEntry: PlayListEntry):
        self.settingStack.hide()
        self.loadMediaFileSignal.emit(fileEntry)
        
    def LoadPlayList(self, playListEntry: PlayListEntry):
        self.settingStack.hide()
        self.loadPlayListSignal.emit(playListEntry)
    
    def ShowPlayerSettings(self):
        self.PlayerSettings.ShowPlayerSettings()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.APPSETTINGS.value)   
        
    def ShowHotKeySettings(self):
        #self.HotKeySettings.ShowHotKeySettings()
        self.settingStack.setCurrentIndex(ENUM_SettingsViews.HOTKEYS.value)        
