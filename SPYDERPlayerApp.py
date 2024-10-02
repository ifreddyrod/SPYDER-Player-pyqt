import re, os
from PyQt6 import uic
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QUrl, QEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QToolTip, QWidget, QHeaderView
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import threading

class SpyderPlayer(QWidget):
    channelList = []
    def __init__(self):
        super().__init__()
        
        # Get current directory and append GUI file     
        ui_path = os.getcwd() + "/assets/PlayerMainWindow.ui"
        
        # Load the UI file
        print(ui_path)
        self.ui = uic.loadUi(ui_path, self)  
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.videoWidget = self.ui.VideoView_widget
        #self.videoWidget.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        self.player.setVideoOutput(self.videoWidget)
        
        # Set the Left of vertical splitter to a fixed size
        self.ui.splitter.setSizes([200, 500])
        self.ui.splitter_2.setSizes([500, 1])
        # Set the side of the table column to the width of the horizontal layout
        self.ui.Channels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Connect signal if widget changes state to maximize
        #self.window().windowStateChanged.triggered.connect(self.WindowChanged)
        
        # Install event filter to detect window state changes
        self.installEventFilter(self)
        
        # Connect signal to when cell is hovered show tooltip
        self.ui.Channels_table.cellClicked.connect(self.ShowFullChannelName)
              
        self.Channels_table.cellDoubleClicked.connect(self.PlayChannel)
        self.ui.Play_button.clicked.connect(self.PlayStopSream)
        self.LoadPlayList('us.m3u')
        self.SelectedRow = -1
       
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowStateChange:
            #print("Window state changed: ", self.windowState() )
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                self.ui.splitter.setSizes([0, 500])  # Hide left side    
                self.ui.splitter_2.setSizes([500, 0])            
                self.setWindowState(Qt.WindowState.WindowFullScreen)
                # make splitter hidden     
                
                
                #self.ui.horizontalLayout_2.setGeometry(0, 0, 0, 0)
                #self.ui.horizontalLayout_2.
                
                
            else:
                #self.videoWidget.setParent(self.ui.VideoView_widget.parent())  # Reparent back to layout container
                #self.videoWidget.setFullScreen(False)
                #self.videoWidget.showNormal()
                #self.setFullScreen(False)
                self.setWindowState(Qt.WindowState.WindowNoState)
                self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
                self.ui.splitter.setSizes([200, 500])  # Restore left side
                self.ui.splitter_2.setSizes([500, 1])
                
        return super().eventFilter(obj, event)
     
    def LoadPlayList(self, playlistFile):
        
         # Open the file and read it line by line
        with open(playlistFile, 'r') as file:
            lines = file.readlines()

        # Regex to capture EXTINF metadata and URL
        extinf_pattern = re.compile(r'#EXTINF:-1.*?,(.*)')
        stream_url = None

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
                    #self.add_channel_to_table(channel_name, stream_url)    
                    # add the channel to the list
                    self.channelList.append((channel_name, stream_url))
            
        self.UpdateChannelsTable()
        
    def UpdateChannelsTable(self):
        # Clear the table
        self.ui.Channels_table.clearContents()
        self.ui.Channels_table.setRowCount(len(self.channelList))

        # Populate the table
        for i, (channel_name, stream_url) in enumerate(self.channelList):
            self.ui.Channels_table.setItem(i, 0, QTableWidgetItem(channel_name))
            #self.ui.Channels_table.setToolTip(channel_name) 
            
                 
    def ShowFullChannelName(self, row, column):   
        # Ensure we are in the correct column (Channel name column)
        if column != 0:
            return
        
        if row < 0 or len(self.channelList) == 0:
            return
        
        # Get the channel name
        channel_name = self.channelList[row][0]
        
        print("Channel name:", channel_name)
        
        # Show the tooltip at the current cursor position
        self.ui.Channels_table.setToolTip(channel_name)
        #QToolTip.showText(QCursor.pos(), channel_name)
        
    def WindowChanged(self):
        if self.windowState() == QWidget.WindowState.WindowMaximized or self.windowState() == QWidget.WindowState.WindowFullScreen:
            self.showNormal()
            self.ui.splitter.setSizes([200, 500])
        else:
            self.ui.splitter.setSizes([0, 500])
            self.showFullScreen()
            
    def PlayChannel(self):
        # Create Player Thread
        self.player_thread = threading.Thread(target=self.PlayerThread)
        self.player_thread.start()
        
    def PlayerThread(self):
        
        # Get the selected row
        self.SelectedRow = self.ui.Channels_table.currentRow()
        
        # Get the channel name and stream URL
        channel_name, stream_url = self.channelList[self.SelectedRow]   

        # Play the stream
        self.player.setSource(QUrl(stream_url))
        self.player.play()
                
            
    def PlayStopSream(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.stop()
            self.player_thread.join()
        elif self.SelectedRow >= 0:
            self.PlayChannel()



if __name__ == "__main__":
    app = QApplication([])
    spyderApp = SpyderPlayer()
    spyderApp.show()
    app.exec()