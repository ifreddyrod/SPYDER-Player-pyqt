import re, os
from PyQt6 import uic
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer
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
        self.setMouseTracking(True)
        self.videoWidget.setMouseTracking(True)
        self.ui.Channels_table.setMouseTracking(True)
        self.installEventFilter(self)
        self.ui.VideoView_widget.installEventFilter(self)
        self.ui.Channels_table.installEventFilter(self)   
        self.player.installEventFilter(self) 
        
        # Connect signal to when cell is hovered show tooltip
        self.ui.Channels_table.cellClicked.connect(self.ShowFullChannelName)
              
        self.Channels_table.cellDoubleClicked.connect(self.PlayChannel)
        self.ui.Play_button.clicked.connect(self.PlayStopSream)
        self.LoadPlayList('us.m3u')
        self.SelectedRow = -1
        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.HideCursor)
        self.inactivityTimer.start()        
        
    '''def mouseMoveEvent(self, event):
        print("Mouse move event")
        return super().mouseMoveEvent(event)'''
        
             
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowStateChange:
            #print("Window state changed: ", self.windowState() )
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                '''self.ui.splitter.setSizes([0, 500])  # Hide left side    
                self.ui.splitter_2.setSizes([500, 0])            
                self.setWindowState(Qt.WindowState.WindowFullScreen)'''
                self.PlayerFullScreen()
                
            else:
                '''self.setWindowState(Qt.WindowState.WindowNoState)
                self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
                self.ui.splitter.setSizes([200, 500])  # Restore left side
                self.ui.splitter_2.setSizes([500, 1])'''
                self.PlayerNormalScreen()
                
        elif (event.type() == QEvent.Type.MouseMove or event.type() == QEvent.Type.MouseButtonPress) and self.windowState() == Qt.WindowState.WindowFullScreen:
            #print("Mouse move")
            # Mouse moved, show the cursor and reset the inactivity timer
            self.ShowCursor()
        elif event.type() == QEvent.Type.KeyPress:   
            if event.key() == Qt.Key.Key_Escape and self.windowState() == Qt.WindowState.WindowFullScreen:
                self.PlayerNormalScreen()
            elif event.key() == Qt.Key.Key_F:
                self.PlayerFullScreen()
            elif event.key() == Qt.Key.Key_K or event.key() == Qt.Key.Key_Space:
                self.PlayStopSream()
                
            self.ShowCursor()
                
        return super().eventFilter(obj, event)
     
    def PlayerFullScreen(self):
        #if self.windowState() != Qt.WindowState.WindowFullScreen:
        self.ui.splitter.setSizes([0, 500])  # Hide left side    
        self.ui.splitter_2.setSizes([500, 0])            
        self.setWindowState(Qt.WindowState.WindowFullScreen)
            
    def PlayerNormalScreen(self):
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.splitter.setSizes([200, 500])  # Restore left side
        self.ui.splitter_2.setSizes([500, 1])
            
                
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

    def HideCursor(self):
        if self.windowState() != Qt.WindowState.WindowFullScreen:
            return
        
        # Hide the mouse cursor
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        #self.hideCursor()
  
    def ShowCursor(self):

        print("Show cursor")
        # Show the mouse cursor
        #if self.getCursor().shape() == QCursor(Qt.CursorShape.ArrowCursor): 
            #return 
        
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        #self.ShowCursor()
        # Restart the inactivity timer
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.inactivityTimer.start()       
        

if __name__ == "__main__":
    app = QApplication([])
    spyderApp = SpyderPlayer()
    spyderApp.show()
    app.exec()