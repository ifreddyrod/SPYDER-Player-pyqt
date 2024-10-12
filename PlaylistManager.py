from PyQt6 import uic
from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QTreeWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from m3u_parser import M3uParser
import tempfile
import re
import json
import requests
import os


PLAYLIST_COLOR = QColor(20, 6, 36)

def pad(string: str) -> str:
    return "  " + string



class TreeItem(QTreeWidgetItem):
    def __init__(self, nameText, bgColor:QColor = None):
        super().__init__([nameText])
        self.itemName = nameText.lstrip()
        self.playListName = ""
        
        if bgColor != None:
            self.setBackground(0, bgColor)
        
    '''        
    def GetParentName(self) -> str:
        parent = self.parent().text()
        parent = parent.split("  (")[0]
        parent = parent.lstrip()
        return parent'''
        
class VideoInfo:    
    def __init__(self, channelName: str, source: str, playListName: str, treeItem: TreeItem = None):
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
        
class PlayListManager(QWidget):
    treeItemSelectedSignal: pyqtSignal = pyqtSignal(str, str)
    currentSelectedItem: QStandardItem = None
    lastSelectedItem: QStandardItem = None
    favoritesInfo = []
    searchResultsCount = 0
    currentItem = 0
    
    def __init__(self, playlistTreefromUI: QTreeWidget, parent=None):
        super().__init__(parent)
        
        # Setup The Playlist Tree
        self.playlistTree = playlistTreefromUI
        self.playlistTree.setColumnCount(1)
        
        # Load Custom Stylesheet
        self.playlistTree.setStyleSheet(self.load_stylesheet())
        
        
        # Add core Playlists
        self.searchList = TreeItem(pad("Search Results"), PLAYLIST_COLOR)
        self.favoritesList = TreeItem(pad("Favorites"), PLAYLIST_COLOR)
        self.libraryList = TreeItem(pad("Library"), PLAYLIST_COLOR)
        
        self.AppendPlayList(self.searchList)
        self.AppendPlayList(self.favoritesList)
        self.AppendPlayList(self.libraryList)
        
        # Setup Event Handlers
        '''self.playlistTree.itemDoubleClicked.connect(self.ChannelDoubleClicked)
        self.playlistTree.itemClicked.connect(self.PlayListClicked)
        self.playlistTree.itemChanged.connect(self.ChennelCheckBoxChanged)'''
        
        
        # Load playlists
        self.LoadPlayList("us.m3u")
        self.LoadPlayList("us_longlist.m3u")
        self.LoadPlayList("Movies.m3u")
        
        #self.LoadFavorites()
        

    def load_stylesheet(self):
        
        iconPath = os.getcwd() + "/assets/icons/"   #os.getcwd() + "/assets/icons/"  "C:/Temp/icons/" 
        print(iconPath)
        
        icon_star_full = os.path.join(iconPath, 'star-full.png')
        icon_star_empty = os.path.join(iconPath, 'star-empty.png') 
        icon_collapsed = os.path.join(iconPath, 'collapsed.png')
        icon_expanded = os.path.join(iconPath, 'expanded.png')
        
        stylesheet = f"""
        QTreeWidget
        {{
        background-color: rgb(15, 15, 15);
        color: white;
        font: 12pt "Arial";
        }}

        QTreeView::branch:open
        {{
        image: url("{icon_expanded}");
        }}
        QTreeView::branch:closed:has-children
        {{
        image: url("{icon_collapsed}");
        }}

        QTreeWidget::item
        {{
        height: 50px;
        }}

        QTreeWidget::indicator
        {{
        width: 16px;
        height: 16px;
        }}

        QTreeWidgetItem::indicator:enabled
        {{
        padding-right: 10px;
        }}

        QTreeWidget::indicator:checked
        {{
        image: url("{icon_star_full}");
        }}

        QTreeWidget::indicator:unchecked
        {{
        image: url("{icon_star_empty}");
        }}

        QTreeView::item:selected
        {{
        background-color: rgb(35, 11, 63);
        border: 1px solid rgb(82, 26, 149);
        border-left-color: transparent;
        border-right-color: transparent;
        }}
        """
        return stylesheet   
    
    def AppendPlayList(self, newPlayList: TreeItem):
        self.playlistTree.insertTopLevelItem(self.playlistTree.topLevelItemCount(), (newPlayList))
    
    
    def AppendChannel(self, playList: TreeItem, newChannel: TreeItem):
        playList.insertChild(playList.childCount(), newChannel)
    
        
    def UpdatePlayListChannelCount(self, item: TreeItem, count: int = -1):
        if count == -1:
            count = item.childCount()
            
        item.setText(0, pad(item.itemName) + "  (" + str(count) + ")")
                
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
        playlistTreeItem = TreeItem(pad(playlistName), PLAYLIST_COLOR)
        self.AppendPlayList(playlistTreeItem)
                
        #------------------------------
        # Process the parsed entries
        #------------------------------
        for entry in entries:
            channel_name = entry.get('name', 'Unknown') # Get the title from the EXTINF tag
            source = entry.get('url', 'No URL')  # Get the stream URL or file path
            
            if channel_name and source:
                # Create a new item for the channel and add it as a child to the playlist item
                channelItem = QTreeWidgetItem([pad(channel_name)])
                channelItem.setData(0, Qt.ItemDataRole.UserRole, source)

                channelItem.setFlags(channelItem.flags() | Qt.ItemFlag.ItemIsUserCheckable) 
                channelItem.setCheckState(0, Qt.CheckState.Unchecked) 
                
                self.AppendChannel(playlistTreeItem, channelItem) 
                
        # Rename the playlist item
        self.UpdatePlayListChannelCount(playlistTreeItem)
        
        
