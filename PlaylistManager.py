from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import QSize, Qt, pyqtSignal
import re
import os
import json

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
        
class VideoInfo:    
    def __init__(self, channelName: str, source: str, playListName: str, treeItem: TreeStandardItem = None):
        self.channelName = channelName
        self.source = source
        self.playListName = playListName
        self.treeItem = treeItem
    
    def GetDict(self):
        # Convert the ChannelInfo object to a dictionary
        return {
            "channelName": self.channelName,
            "source": self.source,
            "playListName": self.playListName,
            # Exclude treeItem as it's not JSON serializable
        }
        
class PlaylistManager(QWidget):
    treeItemSelectedSignal: pyqtSignal = pyqtSignal(str, str)
    currentSelectedItem: QStandardItem = None
    lastSelectedItem: QStandardItem = None
    favoritesInfo = []
    
    def __init__(self, playlistTreefromUI: QTreeView, parent=None):
        super().__init__(parent)
        
        self.playlistTree = playlistTreefromUI
        self.CustomizeTree()
        
        iconPath = os.getcwd() + "/assets/icons/"
        
        icon_star_trans = os.path.join(iconPath, 'star-trans.png')
        icon_star_full = os.path.join(iconPath, 'star-full.png')
        icon_star_empty = os.path.join(iconPath, 'star-empty.png')      
          
        print(f"icon_star_trans: {icon_star_trans}")
        print(f"icon_star_full: {icon_star_full}")
        print(f"icon_star_empty: {icon_star_empty}")
        
        
        # Create a stylesheet with the dynamically constructed paths
        stylesheet = f"""
        QTreeView::indicator:indeterminate {{
            image: url("{icon_star_trans}");
        }}

        QTreeView::indicator:checked {{
            image: url("{icon_star_full}");
        }}

        QTreeView::indicator:unchecked {{
        image: url("{icon_star_empty}");
        }}
        
        background-color: rgb(15, 15, 15);
        """  
        self.playlistTree.setStyleSheet(stylesheet)
        
        # Create the model once and use it for both playlists
        self.model = QStandardItemModel()
        self.rootItem = self.model.invisibleRootItem()
        self.model.setHorizontalHeaderLabels(["Channels"])
        self.playlistTree.setModel(self.model)  # Set model initially

        # Add Standard playlists
        #rows = ["Search Results", "Favorites", "Library"]
        self.textPadding = "    "
        self.playListHeaderColor = QColor(28, 9, 50)
        
        self.searchList = TreeStandardItem(self.textPadding +"Search Results", self.playListHeaderColor)
        self.model.appendRow(self.searchList)
        
        self.favoritesList = TreeStandardItem(self.textPadding +"Favorites", self.playListHeaderColor)
        self.model.appendRow(self.favoritesList)
        
        self.libraryList = TreeStandardItem(self.textPadding +"Library", self.playListHeaderColor)
        self.model.appendRow(self.libraryList)
         
        # Create Event Connections
        self.playlistTree.doubleClicked.connect(self.ChannelDoubleClicked) 
        self.playlistTree.clicked.connect(self.RowClicked)
        # Connect signal for item changed
        self.model.itemChanged.connect(self.FavoriteClicked)
         
        # Load Custom playlists
        self.LoadPlayList("us.m3u")
        self.LoadPlayList("playlist_usa.m3u8")
        self.LoadFavorites()
        
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
        playlistTreeItem = TreeStandardItem(self.textPadding + playlistName, self.playListHeaderColor)
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
            
            print(f"channelName:{channelName}, channelSource{channelSource}, channelPlaylist: {channelPlaylist}")
            
            index = -1
            for i, info in enumerate(self.favoritesInfo):
                if info.channelName == channelName and info.source == channelSource:
                    index = i
                    break
             
            if index != -1:
                print("Item already in favorites list")
                return
               
            self.favoritesInfo.append(VideoInfo(channelName, channelSource, channelPlaylist, item))
            print(f"favoritesInfo size: {len(self.favoritesInfo)}")
            
            self.model.blockSignals(True)
            favoriteChannel = TreeStandardItem(channelName)
            favoriteChannel.setCheckable(True)
            favoriteChannel.setData(channelSource, Qt.ItemDataRole.UserRole)
            favoriteChannel.setCheckState(Qt.CheckState.Checked)
            self.favoritesList.appendRow(favoriteChannel)
            self.UpdateHeaderCount(self.favoritesList)
            self.model.blockSignals(False)
            #count = self.favoriteList.rowCount()
            #self.favoriteList.setText(self.textPadding + self.favoriteList.itemName + "  (" + str(count) + ")")
            
            self.SaveFavorites()
            self.model.layoutChanged.emit()
            
        elif item.checkState() == Qt.CheckState.Unchecked:
            channelName = item.text()
            channelSource = item.data(Qt.ItemDataRole.UserRole)
            
            if len(self.favoritesInfo) == 0: 
                print("No items in favorites list")
                return 
            
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

            '''print(f"favoritesInfo size: {len(self.favoritesInfo)}")
            name = favoriteItem.text()
            source = favoriteItem.data(Qt.ItemDataRole.UserRole)
            playlist = favoriteItem.GetParentName()
            print(f"channelName: {name}, source: {source}, playlist: {playlist}")'''
            
            
            # Search Favorites list for item with name and source
            favoriteIndex = -1
            for i in range(self.favoritesList.rowCount()):
                row = self.favoritesList.child(i)
                
                if row.itemName == channelName and row.data(Qt.ItemDataRole.UserRole) == channelSource:
                    favoriteIndex = i
                    break
            
            if favoriteIndex == -1:
                print("Channel not found in favorites list")
                return
            
            # Ensure the item is unchecked in both the playlist and Favorites list
            self.model.blockSignals(True)
            channelPlaylist = item.GetParentName()
            # If Item deselected from Favorites list, then uncheck corresponding playlist item
            if(channelPlaylist == "Favorites"):
                favoriteItem.setCheckState(Qt.CheckState.Unchecked)
                
            self.model.blockSignals(False)
            
            # Remove the item from the favorites list
            self.favoritesList.removeRow(favoriteIndex)
                   
            # Remove the item from favoritesInfo
            self.favoritesInfo.pop(index)
                    
            # Update the header count
            self.UpdateHeaderCount(self.favoritesList)   
            
            self.SaveFavorites()
            self.model.layoutChanged.emit()         

    def SaveFavorites(self):
        with open("favorites.json", "w") as f:
            json.dump([channel.GetDict() for channel in self.favoritesInfo], f, indent=4)

        print("Favorites saved successfully")
        
    def LoadFavorites(self):
        # Get Favorites from File
        with open("favorites.json", "r") as f:
            self.favoritesInfo = [VideoInfo(**channel) for channel in json.load(f)]
            
        self.model.blockSignals(True)    
        # Find Corresponding Playlist Items
        for item in self.favoritesInfo:
            # Find the item.playListName in the model
            item.treeItem = self.GetChannelFromTree(item.playListName, item.channelName, item.source)
            
            if item.treeItem:
                item.treeItem.setCheckState(Qt.CheckState.Checked)   
                
            # Add the item to the favorites list
            favoriteItem = TreeStandardItem(item.channelName)
            favoriteItem.setCheckable(True)
            favoriteItem.setData(item.source, Qt.ItemDataRole.UserRole)
            favoriteItem.setCheckState(Qt.CheckState.Checked)
            self.favoritesList.appendRow(favoriteItem)
              
        self.UpdateHeaderCount(self.favoritesList)    
        self.model.blockSignals(False)
            
        self.model.layoutChanged.emit()    
            
        print("Favorites loaded successfully")
    
    def GetChannelFromTree(self, playlistName: str, channelName: str, source: str):
        model = self.playlistTree.model()
        
        print(f"playlistName: {playlistName}, channelName: {channelName}, source: {source}")
        print(f"model.rowCount(): {model.rowCount()}")
        
        # Traverse the top-level items (playlists)
        for row in range(model.rowCount()):
            playlist = model.item(row)  # Get the playlist item (QStandardItem)
            print(f"---->playlist: {playlist.text()}")
            
            if playlist.itemName == playlistName:  # Match the playlist name
                print(f"Playlist: {playlist.text()}")
                # Traverse the children (channels)
                for childRow in range(playlist.rowCount()):
                    channelItem = playlist.child(childRow)  # Get the channel item
                    
                    if channelItem.itemName == channelName and channelItem.data(Qt.ItemDataRole.UserRole) == source:  # Match the channel name
                        return channelItem  # Return the matching QStandardItem (channel)

        return None  # Return None if the playlist or channel wasn't found