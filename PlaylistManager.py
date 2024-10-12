from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QWidget, QTreeView
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from m3u_parser import M3uParser
import tempfile
import re
import json
import requests
import os

class TreeStandardItem(QStandardItem):
    def __init__(self, nameText, bgColor:QColor = None):
        super().__init__(nameText)
        self.itemName = nameText.lstrip()
        self.playListName = ""
        
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
    searchResultsCount = 0
    currentItem = 0
    
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
        QTreeView {{
            background-color: rgb(25, 25, 25);
            color: rgb(255, 255, 255);
            font-size: 14px;
        }}
        
        QTreeView::indicator {{
            width: 16px;
            height: 16px;
        }}
                
        QTreeView::indicator:indeterminate {{
            image: url("{icon_star_trans}");
        }}
                
        QTreeView::indicator:checked {{
            image: url("{icon_star_full}");
        }}

        QTreeView::indicator:unchecked {{
        image: url("{icon_star_empty}");
        }}
        
        """  
        self.playlistTree.setStyleSheet(stylesheet)
        
        # Create the model once and use it for both playlists
        self.model = QStandardItemModel()
        self.rootItem = self.model.invisibleRootItem()
        self.model.setHorizontalHeaderLabels(["Play Lists"])
        self.playlistTree.setModel(self.model)  # Set model initially

        # Add Standard playlists
        #rows = ["Search Results", "Favorites", "Library"]
        self.textPadding = "    "
        self.playListHeaderColor = QColor(28, 9, 50)
        
        self.searchList = TreeStandardItem(self.textPadding + "Search Results", self.playListHeaderColor)
        self.model.appendRow(self.searchList)
        
        self.favoritesList = TreeStandardItem(self.textPadding + "Favorites", self.playListHeaderColor)
        self.model.appendRow(self.favoritesList)
        
        self.libraryList = TreeStandardItem(self.textPadding + "Library", self.playListHeaderColor)
        self.model.appendRow(self.libraryList)
         
        # Create Event Connections
        self.playlistTree.doubleClicked.connect(self.ChannelDoubleClicked) 
        self.playlistTree.clicked.connect(self.RowClicked)
        # Connect signal for item changed
        self.model.itemChanged.connect(self.FavoriteClicked)
         
        # Load Custom playlists
        self.LoadPlayList("us.m3u")
        self.LoadPlayList("us_longlist.m3u")
        self.LoadPlayList("Movies.m3u")

        
        self.LoadFavorites()
        
    def CustomizeTree(self):
        self.playlistTree.setIndentation(25) 
        self.playlistTree.setHeaderHidden(True)
        self.playlistTree.setRootIsDecorated(True)
        
            
    def CustomizeTreeRow(self, treeItem):
        treeItem.setSizeHint(QSize(200, 40)) 
        
    def LoadPlayList(self, playlistPath):
        # Extract the file name without the extension
        playListFile = os.path.basename(playlistPath)

        playlistName, extension = os.path.splitext(os.path.basename(playListFile))

        # Initialize the parser
        parser = M3uParser()
        
        #-----------------------------------------------
        # Attemp to fetch and parse a remote playlist
        #-----------------------------------------------
        if playlistPath.startswith("http"):
            try:
                response = requests.get(playlistPath)
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.m3u') as temp_file:
                    # Write the content to the temporary file
                    temp_file.write(response.text)
                    responseFile = temp_file.name
        
                parser.parse_m3u(responseFile, check_live=False)
                os.remove(responseFile)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching remote playlist: {e}")
                return
        #----------------------------------------
        # Attempt to parse local playlist file   
        #---------------------------------------- 
        else:
            # Attempt to read the playlist file o
            parser.parse_m3u(playlistPath, check_live=False)

        #------------------------------
        # Check if the parser is empty
        #------------------------------
        entries = parser.get_list()
        if not entries:
            print("The playlist is empty.")
            return
        
        # Create a Playlist Entry to the Tree and add it 
        playlistTreeItem = TreeStandardItem(self.textPadding + playlistName, self.playListHeaderColor)
        self.model.appendRow(playlistTreeItem)  # Append the playlist to the model
        
        #------------------------------
        # Process the parsed entries
        #------------------------------
        for entry in entries:
            channel_name = entry.get('name', 'Unknown') # Get the title from the EXTINF tag
            source = entry.get('url', 'No URL')  # Get the stream URL or file path
            
            if channel_name and source:
                # Create a new item for the channel and add it as a child to the playlist item
                channel_item = TreeStandardItem(channel_name)
                channel_item.setEditable(False)
                channel_item.setCheckable(True)
                # Store the URL in the item without displaying it
                channel_item.setData(source, Qt.ItemDataRole.UserRole)
                channel_item.playListName = playlistName
                playlistTreeItem.appendRow(channel_item) 
                
        # Rename the playlist item
        self.UpdateHeaderCount(playlistTreeItem)
        

    def ChannelDoubleClicked(self, index):
        temp = self.currentSelectedItem
        
        """Handle the double-click event to retrieve channel name and URL."""
        # Get the clicked item from the model
        item = self.model.itemFromIndex(index)
        
        # Retrieve the channel name (displayed)
        channel_name = item.text()

        # Retrieve the hidden URL (stored in UserRole)
        stream_url = item.data(Qt.ItemDataRole.UserRole)
        
        # Check if selection is from Search List, Find the Channel from the Tree
        if item.playListName == self.searchList.itemName:
            play_list_name = item.GetParentName()
            # Get the channel from the tree
            item = self.GetChannelFromTree(play_list_name, channel_name, stream_url)
        
        
        self.currentSelectedItem = item
        
        self.lastSelectedItem = temp
        
        self.treeItemSelectedSignal.emit(channel_name, stream_url)
    
    def RowClicked(self, index):
        """Expand or collapse playlist on single click."""
        item = self.model.itemFromIndex(index)
        self.currentItem = item
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
        if self.lastSelectedItem is None:
            return None, None
        
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
    
    def UpdateHeaderCount(self, item: TreeStandardItem, count: int = -1):
        if count == -1:
            count = item.rowCount()
            
        item.setText(self.textPadding + item.itemName + "  (" + str(count) + ")")
    
    def FavoriteClicked(self, item):
        if item.checkState() == Qt.CheckState.Checked:
            
            channelName = item.text()
            channelSource = item.data(Qt.ItemDataRole.UserRole)
            channelPlaylist = item.GetParentName()
            
            #print(f"channelName:{channelName}, channelSource{channelSource}, channelPlaylist: {channelPlaylist}")
            
            index = -1
            for i, info in enumerate(self.favoritesInfo):
                if info.channelName == channelName and info.source == channelSource:
                    index = i
                    break
             
            if index != -1:
                print("Item already in favorites list")
                return
               
            self.favoritesInfo.append(VideoInfo(channelName, channelSource, channelPlaylist, item))
            #print(f"favoritesInfo size: {len(self.favoritesInfo)}")
            
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
            channelPlaylist = item.playListName
            
            if len(self.favoritesInfo) == 0: 
                #print("No items in favorites list")
                pass
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
            
            self.model.blockSignals(True)
            # Search the Search Results for Favorties
            if self.searchResultsCount > 0:
                #searchList =  self.playlistTree.model().item(0) # First item is the Search List list results
                favList = self.searchList.child(0) #searchList.child(0) # First item is the Favorites list
                for i in range(favList.rowCount()):
                    channel = favList.child(i)
                    if channel.itemName == channelName and channel.data(Qt.ItemDataRole.UserRole) == channelSource:
                        favList.removeRow(i)
                        self.searchResultsCount -= 1
                        #channel.setCheckState(Qt.CheckState.Unchecked)
                        break
                self.UpdateHeaderCount(favList)
                self.UpdateHeaderCount(self.searchList, self.searchResultsCount)

            
            # Ensure the item is unchecked in both the playlist and Favorites list
            
            
            # If Item deselected from Favorites list, then uncheck corresponding playlist item
            if(channelPlaylist == "Favorites"):
                favoriteItem.setCheckState(Qt.CheckState.Unchecked)
                
            # Remove the item from the favorites list
            self.favoritesList.removeRow(favoriteIndex)
                   
            # Remove the item from favoritesInfo
            self.favoritesInfo.pop(index)
                
            self.model.blockSignals(False)
                
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
        
        #print(f"playlistName: {playlistName}, channelName: {channelName}, source: {source}")
        #print(f"model.rowCount(): {model.rowCount()}")
        
        # Traverse the top-level items (playlists)
        for row in range(model.rowCount()):
            playlist = model.item(row)  # Get the playlist item (QStandardItem)
            #print(f"---->playlist: {playlist.text()}")
            
            if playlist.itemName == playlistName:  # Match the playlist name
                #print(f"Playlist: {playlist.text()}")
                # Traverse the children (channels)
                for childRow in range(playlist.rowCount()):
                    channelItem = playlist.child(childRow)  # Get the channel item
                    
                    if channelItem.itemName == channelName and channelItem.data(Qt.ItemDataRole.UserRole) == source:  # Match the channel name
                        return channelItem  # Return the matching QStandardItem (channel)

        return None  # Return None if the playlist or channel wasn't found
    
    def SearchChannels(self, searchText: str):
        # Return if search text is empty
        if not searchText:
            return
        
        searchText = searchText.lower()
        searchText = searchText.split('+')
        
        # Clear the search list 
        self.searchList.removeRows(0, self.searchList.rowCount())
        self.searchResultsCount = 0
        
        # Get Playlist Count
        playlistCount = self.playlistTree.model().rowCount()
        
        searchResultsCount = 0
        self.model.blockSignals(True)
        
        # Traverse (playlists) but ignore the Search Playlist
        for playlist in range(1, playlistCount):
            playlistToSearch = self.playlistTree.model().item(playlist)  # Get the playlist item (QStandardItem)
            
            playListResults = TreeStandardItem(playlistToSearch.itemName)
            
            # Traverse (channels)
            for channel in range(playlistToSearch.rowCount()):
                channelToSearch = playlistToSearch.child(channel)  # Get the channel item
                channelName: str = channelToSearch.itemName.lower()
                
                # Search the channel name for seach query
                #searchIndex = channelName.find(searchText)
                
                for searchItem in searchText:
                    searchIndex = channelName.find(searchItem.strip())
                    if searchIndex < 0:
                        break;
                
                if searchIndex != -1:
                    # if search query found, add the channel to the search list
                    foundChannel = TreeStandardItem(channelToSearch.itemName)
                    foundChannel.setData(channelToSearch.data(Qt.ItemDataRole.UserRole), Qt.ItemDataRole.UserRole)
                    foundChannel.playListName = self.searchList.itemName
                    foundChannel.setCheckable(True)
                    foundChannel.setCheckState(channelToSearch.checkState())
                    playListResults.appendRow(foundChannel)
                    searchResultsCount += 1
            
            # Update Channel Count
            self.UpdateHeaderCount(playListResults)
            self.searchList.appendRow(playListResults)
        
        self.searchResultsCount = searchResultsCount
        # Update Search Results Count
        self.UpdateHeaderCount(self.searchList, searchResultsCount)
        #self.model.expandItems(self.searchList)
        self.model.blockSignals(False)
        self.currentItem = self.playlistTree.model().item(0)
        searchIndex = self.model.indexFromItem(self.currentItem)
        self.playlistTree.setCurrentIndex(searchIndex)  
        self.playlistTree.setExpanded(searchIndex, True)
        self.model.layoutChanged.emit()
        
    '''def SortSearchResultsDescending(self):
        self.searchList.sortChildren(0, Qt.SortOrder.DescendingOrder)
        self.model.layoutChanged.emit()
        
    def SortSearchResultsAscending(self):
        self.searchList.sortChildren(0, Qt.SortOrder.AscendingOrder)
        self.model.layoutChanged.emit()'''
        
    def SortSearchResults(self, order=Qt.SortOrder.AscendingOrder):
        for i in range(self.searchList.rowCount()):
            playlist = self.searchList.child(i)
            playlist.sortChildren(0, order)
        self.searchList.sortChildren(0, order)
        self.model.layoutChanged.emit()
            
    def SortSearchResultsDescending(self):
        self.SortSearchResults(Qt.SortOrder.DescendingOrder)

    def SortSearchResultsAscending(self):
        self.SortSearchResults(Qt.SortOrder.AscendingOrder)    
                   
    def CollapseCurrentPlaylist(self):
        current_item = self.currentItem
        
        if current_item.hasChildren():
            index = self.model.indexFromItem(current_item)
        else:
            index = self.model.indexFromItem(current_item.parent())
            
        self.playlistTree.setCurrentIndex(index)  
        self.playlistTree.collapse(index)
        self.currentItem = self.playlistTree.model().itemFromIndex(index)
            
    def CollapseAllPlaylists(self):
        self.playlistTree.collapseAll()
        
    def GotoTopOfList(self):
        #self.playlistTree.scrollToTop()
        current_item = self.currentItem
        
        if current_item.hasChildren():
            index = self.model.indexFromItem(current_item)
        else:
            index = self.model.indexFromItem(current_item.parent())
            
        self.playlistTree.scrollTo(index)
        
    def GotoBottomOfList(self):  
        #self.playlistTree.scrollToBottom()      
        current_item = self.currentItem
        
        if current_item.hasChildren():
            index = self.model.indexFromItem(current_item)
            parent = current_item
        else:
            index = self.model.indexFromItem(current_item.parent())  
            parent = current_item.parent()      

        end_index = parent.rowCount() - 1  #self.GetPlayListLastItem(current_item)
        
        endIndex = self.model.indexFromItem(parent.child(end_index))
        print(f"end_index: {end_index}")
        
        self.playlistTree.scrollTo(endIndex)

        
            