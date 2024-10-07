from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import QSize, Qt, pyqtSignal
import re
import os


class TreeStandardItem(QStandardItem):
    def __init__(self, nameText, bgColor:QColor = None):
        super().__init__(nameText)
        self.itemName = nameText.lstrip()

        self.setSizeHint(QSize(200, 40)) 
        self.setEditable(False)
        if bgColor != None:
            self.setBackground(bgColor)
            
    def GetParentName(self) -> str:
        parent = self.parent().text()
        parent = parent.split("  (")[0]
        parent = parent.lstrip()
        return parent
        
class ChannelInfo:    
    def __init__(self, channelName: str, source: str, playListName: str, treeItem: TreeStandardItem):
        self.channelName = channelName
        self.source = source
        self.playListName = playListName
        self.treeItem = treeItem
    
    
class PlaylistManager(QWidget):
    treeItemSelectedSignal: pyqtSignal = pyqtSignal(str, str)
    currentSelectedItem: QStandardItem = None
    lastSelectedItem: QStandardItem = None
    favoritesInfo = []
    
    def __init__(self, playlistTreefromUI: QTreeView, parent=None):
        super().__init__(parent)
        
        self.playlistTree = playlistTreefromUI
        self.CustomizeTree()
        
        #self.playListTree.setStyleSheet("QTreeView::branch {  border-image: url(none.png); }")
        
        # Create the model once and use it for both playlists
        self.model = QStandardItemModel()
        self.rootItem = self.model.invisibleRootItem()
        self.model.setHorizontalHeaderLabels(["Channels"])
        self.playlistTree.setModel(self.model)  # Set model initially

        # Add Standard playlists
        #rows = ["Search Results", "Favorites", "Library"]
        self.textPadding = "    "
        
        self.searchList = TreeStandardItem(self.textPadding +"Search Results", QColor(23, 23, 23))
        self.model.appendRow(self.searchList)
        
        self.favoriteList = TreeStandardItem(self.textPadding +"Favorites", QColor(23, 23, 23))
        self.model.appendRow(self.favoriteList)
        
        self.libraryList = TreeStandardItem(self.textPadding +"Library", QColor(23, 23, 23))
        self.model.appendRow(self.libraryList)
         
        # Create Event Connections
        self.playlistTree.doubleClicked.connect(self.ChannelDoubleClicked) 
        self.playlistTree.clicked.connect(self.RowClicked)
        # Connect signal for item changed
        self.model.itemChanged.connect(self.FavoriteClicked)
         
        # Load Custom playlists
        self.LoadPlayList("us.m3u")
        self.LoadPlayList("playlist_usa.m3u8")
        
    def CustomizeTree(self):
        self.playlistTree.setIndentation(25) 
        self.playlistTree.setHeaderHidden(True)
        self.playlistTree.setRootIsDecorated(False)
        
            
    def CustomizeTreeRow(self, treeItem):
        treeItem.setSizeHint(QSize(200, 40)) 
        
    def LoadPlayList(self, playlistPath):
        # Extract the file name without the extension
        playListFile = os.path.basename(playlistPath)

        playlistName, extension = os.path.splitext(os.path.basename(playListFile))

        # Create a parent item with the name of the playlist file
        playlistTreeItem = TreeStandardItem(self.textPadding + playlistName, QColor(23, 23, 23))
        #playlist_item.setSizeHint(QSize(200, 40))
        #playlist_item.setBackground(QColor(23, 23, 23))
        
        # Remove editability from playlist item
        #playlist_item.setEditable(False)
        #playlist_item.setFlags(playlist_item.flags() | Qt.ItemFlag.ItemNeverHasChildren)
  
        self.model.appendRow(playlistTreeItem)  # Append the playlist to the model

        # Open the file and read it line by line
        with open(playlistPath, 'r') as file:
            lines = file.readlines()

        # Regex to capture EXTINF metadata and URL
        extinf_pattern = re.compile(r'#EXTINF:-1.*?,(.*)')
        stream_url = None
        channel_name = None

        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespace
            if line.startswith("#EXTINF"):
                # Extract the channel name from the EXTINF line
                match = extinf_pattern.match(line)
                if match:
                    channel_name = match.group(1)
            elif line.startswith("http"):
                # The line after EXTINF is the stream URL
                stream_url = line
                if channel_name and stream_url:
                    # Create a new item for the channel and add it as a child to the playlist item
                    channel_item = TreeStandardItem(channel_name)
                    #channel_item = QStandardItem(channel_name)
                    #channel_item.setSizeHint(QSize(200, 40))  
                    channel_item.setEditable(False)
                    channel_item.setCheckable(True)
                    #channel_item.setBackground(Qt.GlobalColor.black)
                    # Store the URL in the item without displaying it
                    channel_item.setData(stream_url, Qt.ItemDataRole.UserRole)
                    playlistTreeItem.appendRow(channel_item)
        
        # Get the playListTree Count
        count = playlistTreeItem.rowCount()
        
        # Rename the playlist item
        self.UpdateHeaderCount(playlistTreeItem)
        #playlistTreeItem.setText(self.textPadding + playlistTreeItem.itemName + "  (" + str(count) + ")")
        

    def ChannelDoubleClicked(self, index):
        temp = self.currentSelectedItem
        
        """Handle the double-click event to retrieve channel name and URL."""
        # Get the clicked item from the model
        item = self.model.itemFromIndex(index)

        # Retrieve the channel name (displayed)
        channel_name = item.text()

        # Retrieve the hidden URL (stored in UserRole)
        stream_url = item.data(Qt.ItemDataRole.UserRole)

        self.currentSelectedItem = item
        
        self.lastSelectedItem = temp
        
        self.treeItemSelectedSignal.emit(channel_name, stream_url)
        # Check if a URL is stored (to ensure it's a channel, not a playlist)
        '''if stream_url:
            # Play the stream or handle it as needed
            print(f"Channel: {channel_name}")
            print(f"URL: {stream_url}")'''
            # Here you can call your player or function to start playing the stream
            #self.play_channel(channel_name, stream_url)
    
    def RowClicked(self, index):
        """Expand or collapse playlist on single click."""
        item = self.model.itemFromIndex(index)
        if item and item.hasChildren():  # Check if it's a parent (playlist)
            # Toggle expand/collapse state
            if self.playlistTree.isExpanded(index):
                self.playlistTree.collapse(index)
            else:
                self.playlistTree.expand(index)     
                
    def GetSelectedItem(self):
        temp = self.currentSelectedItem
        
        item = self.playlistTree.model().itemFromIndex(self.playlistTree.currentIndex())
        #item = self.playlistTree.model().
        
        # Retrieve the channel name (displayed)
        channel_name = item.text()

        # Retrieve the hidden URL (stored in UserRole)
        stream_url = item.data(Qt.ItemDataRole.UserRole)
        
        self.currentSelectedItem = item
        
        self.lastSelectedItem = temp
        
        return channel_name, stream_url
    
    def GoToLastSelectedItem(self):
        temp = self.currentSelectedItem
        self.currentSelectedItem = self.lastSelectedItem
        self.lastSelectedItem = temp
        
        # Retrieve the channel name (displayed)
        channel_name = self.currentSelectedItem.text()

        # Retrieve the hidden URL (stored in UserRole)
        stream_url = self.currentSelectedItem.data(Qt.ItemDataRole.UserRole) 
        
        # Get Current items Index
        index = self.model.indexFromItem(self.currentSelectedItem) 
        
        # Set Tree to Selected Item
        self.playlistTree.setCurrentIndex(index) 
        
        return channel_name, stream_url
    
    def UpdateHeaderCount(self, item: TreeStandardItem):
        count = item.rowCount()
        item.setText(self.textPadding + item.itemName + "  (" + str(count) + ")")
    
    def FavoriteClicked(self, item):
        if item.checkState() == Qt.CheckState.Checked:
            
            channelName = item.text()
            channelSource = item.data(Qt.ItemDataRole.UserRole)
            channelPlaylist = item.GetParentName()
            
            print("Checked - Playlist Name: " + channelPlaylist)
            self.favoritesInfo.append(ChannelInfo(channelName, channelSource, channelPlaylist, item))
            
            favoriteChannel = TreeStandardItem(channelName)
            favoriteChannel.setCheckable(True)
            favoriteChannel.setData(channelSource, Qt.ItemDataRole.UserRole)
            favoriteChannel.setCheckState(Qt.CheckState.Checked)
            self.favoriteList.appendRow(favoriteChannel)
            self.UpdateHeaderCount(self.favoriteList)
            
            #count = self.favoriteList.rowCount()
            #self.favoriteList.setText(self.textPadding + self.favoriteList.itemName + "  (" + str(count) + ")")
            
            #self.model.layoutChanged.emit()
            
        elif item.checkState() == Qt.CheckState.Unchecked:
            channelName = item.text()
            channelSource = item.data(Qt.ItemDataRole.UserRole)
            
            
            # Find the corresponding favorite item in favoritesInfo
            index = -1
            for i, info in enumerate(self.favoritesInfo):
                if info.channelName == channelName and info.source == channelSource:
                    index = i
                    break
            
            if index == -1:
                print("Channel not found in favorites list")
                return    

            # Remove the item from the favorites list
            favoriteItem = self.favoritesInfo[index].treeItem

            # Ensure the item is unchecked in both the playlist and Favorites list
            #self.model.blockSignals(True)
            channelPlaylist = item.GetParentName()
            if(channelPlaylist != "Favorites"):
                favoriteItem.setCheckState(Qt.CheckState.Unchecked)
                
            #self.model.blockSignals(False)
            
            # Remove the item from the model
            self.favoriteList.removeRow(favoriteItem.row())

            # Remove the item from favoritesInfo
            self.favoritesInfo.pop(index)

            # Update the header count
            self.UpdateHeaderCount(self.favoriteList)   
            
            
            self.model.layoutChanged.emit()         
            '''
            print("UNChecked - channel Name: " + channelName)
            # Find the index of the favorite item
            index = 0
            for info in self.favoritesInfo:
                if info.channelName == channelName and info.source == channelSource and info.playListName == channelPlaylist:
                    break
                index += 1
                
            if index >= len(self.favoritesInfo):
                print("Channel not found in favorites list")
                return    
                
            # Get Item to Remove
            itemToUncheck = self.favoritesInfo[index].treeItem
            itemToUncheck.setCheckState(Qt.CheckState.Unchecked)
            
            self.favoritesInfo.pop(index)
            self.favoriteList.removeRow(index)  '''

            
            
            
            
            
    
'''
    def GetPlaylistandChannel(self, item):
        # Find which playlist the original channel belongs to
        for row in range(self.rootItem.rowCount()):
            playlist_item = self.rootItem.child(row)
            if playlist_item.text() != self.textPadding + "Favorites" and playlist_item.indexOfChild(item) != -1:
                return playlist_item.text(), item.text()
        return None, None
        
    def FavoriteClicked(self, item):
        # Check if the item is a channel and its checkbox is checked
        if item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
            # Add to Favorites if it's not already there
            playlist_name, channel_name = self.GetPlaylistandChannel(item)
            if playlist_name and channel_name:  
            #if item not in self.favoriteListObjects:
                favoriteChannel = QStandardItem(item.text())  #TreeItem(item.text())
                favoriteChannel.setCheckable(True)

                # Map original channel to the favorite item
                self.favoriteListObjects[(playlist_name, channel_name)] = favoriteChannel
                self.favoriteList.appendRow(favoriteChannel)

                # Save the updated Favorites list to file
                #self.SaveFavorites()

        elif item.isCheckable() and item.checkState() == Qt.CheckState.Unchecked:
            # Remove from Favorites if unchecked in the original playlist
            playlist_name, channel_name = self.GetPlaylistandChannel(item)
            if playlist_name and channel_name:
            #if item in self.favoriteListObjects:
                if (playlist_name, channel_name) in self.favoriteListObjects:
                    favorite_item = self.favoriteListObjects[(playlist_name, channel_name)]
                    self.RemoveFavoriteItem(favorite_item, playlist_name, channel_name)

                    # Save the updated Favorites list to file
                    #self.save_favorites()           
    
    def RemoveFavoriteItem(self, favorite_item, playlist_name, channel_name):
        # Find the favorite item in the "Favorites" playlist
        for row in range(self.favoriteList.rowCount()):
            if self.favoriteList.child(row) == favorite_item:
                # Uncheck the original channel when it's removed from Favorites
                original_item = None
                for i in range(self.rootItem.rowCount()):
                    playlist_item = self.rootItem.child(i)
                    if playlist_item.text() == playlist_name:
                        for j in range(playlist_item.rowCount()):
                            if playlist_item.child(j).text() == channel_name:
                                original_item = playlist_item.child(j)
                                break
                        break
                if original_item:
                    original_item.setCheckState(Qt.CheckState.Unchecked)  
                      

                # Remove from Favorites
                
                # Remove the mapping
                del self.favoriteListObjects[(playlist_name, channel_name)]

                break       '''             