import re, os
from PyQt6 import uic
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer, QPoint
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QToolTip, QWidget, QHeaderView,  QHBoxLayout, QVBoxLayout, QPushButton, QSlider
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import threading


class VideoDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get current directory and append GUI file     
        videoUIPath = os.getcwd() + "/assets/VideoDisplayPanel.ui"

        # Load the UI files
        self.ui = uic.loadUi(videoUIPath, self)          
        self.videoOutput = self.ui.VideoView_widget
        
        self.show()
        
        

class VideoControlPannel(QWidget):     
    def __init__(self, parent=None):
        super().__init__(parent)
        self.SpyderPlayer = parent
        
        controllerUIpath = os.getcwd() + "/assets/VideoControlPanel.ui"
        self.ui = uic.loadUi(controllerUIpath, self)
        
        #self.playerController.setStyleSheet("background-color: transparent;")
        # Make sure the control panel is frameless and transparent
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint ) #| Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        #self.setStyleSheet("background: transparent;") 
        
                
              
class SpyderPlayer(QWidget):
    channelList = []
    def __init__(self):
        super().__init__()
        
        # Get current directory and append GUI file     
        mainUIPath = os.getcwd() + "/assets/PlayerMainWindow.ui"
        
        # Load the UI files
        self.ui = uic.loadUi(mainUIPath, self)  
        
        # Load Stacked Widget
        self.videoStack = self.ui.Stacked_widget
   
        self.videoPanel = VideoDisplay(self)
        self.videoStack.addWidget(self.videoPanel)
        
        self.control_panel = VideoControlPannel(self)  #FloatingControlPanel()
        self.control_panel.hide() 
        #self.control_panel.installEventFilter(self)
                   
        # Set up player      
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        #self.videoWidget = self.ui.VideoView_widget
        
        self.player.setVideoOutput(self.videoPanel.videoOutput)
        
        # Set the Left of vertical splitter to a fixed size
        self.ui.splitter.setSizes([200, 500])
        self.ui.splitter_2.setSizes([500, 1])
        # Set the side of the table column to the width of the horizontal layout
        self.ui.Channels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                
        # Install event filter to detect window state changes
        self.setMouseTracking(True)
        #self.videoWidget.setMouseTracking(True)
        self.ui.Channels_table.setMouseTracking(True)
        self.installEventFilter(self)
        self.videoStack.installEventFilter(self)
        self.ui.Channels_table.installEventFilter(self)   
        self.player.installEventFilter(self) 
        
        # Connect signal to when cell is hovered show tooltip
        self.ui.Channels_table.cellClicked.connect(self.ShowFullChannelName)
              
        self.Channels_table.cellDoubleClicked.connect(self.PlayChannel)
        self.control_panel.ui.Play_button.clicked.connect(self.PlayStopStream)
        self.ui.Play_button.clicked.connect(self.PlayStopStream)
        self.LoadPlayList('us.m3u')
        self.SelectedRow = -1
        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.HideCursor)
        self.inactivityTimer.start()        
        
        self.videoStack.setCurrentWidget(self.videoPanel)

        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.ShowCursor()
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.ShowCursorBusy()
        
    '''def mouseMoveEvent(self, event):
        print("Mouse move event")
        return super().mouseMoveEvent(event)'''
        
             
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowStateChange:
            #print("Window state changed: ", self.windowState() )
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                self.PlayerFullScreen()
            else:
                self.PlayerNormalScreen()
                self.ShowCursor()
                
        elif event.type() == QEvent.Type.KeyPress:   
            if event.key() == Qt.Key.Key_Escape and self.windowState() == Qt.WindowState.WindowFullScreen:
                self.PlayerNormalScreen()
                self.ShowCursor()
                return True
            elif event.key() == Qt.Key.Key_F:
                self.PlayerFullScreen()
            elif event.key() == Qt.Key.Key_K or event.key() == Qt.Key.Key_Space:
                self.PlayStopStream()
                
            self.ShowCursor()
            
        elif (event.type() == QEvent.Type.MouseMove or event.type() == QEvent.Type.MouseButtonPress or event.type() == QEvent.Type.Wheel) and self.windowState() == Qt.WindowState.WindowFullScreen:
            #print("Mouse move")
            # Mouse moved, show the cursor and reset the inactivity timer
            #self.videoController.show()
            self.ShowCursor()       
                    
        #elif event.type() == QEvent.Type.MouseMove and 
        return super().eventFilter(obj, event)
     

            
    def PlayerFullScreen(self):
        #if self.windowState() != Qt.WindowState.WindowFullScreen:
        self.ui.splitter.setSizes([0, 500])  # Hide left side    
        self.ui.splitter_2.setSizes([500, 0])            
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.control_panel.show()
        self.setFocus()
        
            
    def PlayerNormalScreen(self):
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        self.control_panel.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        #self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.splitter.setSizes([200, 500])  # Restore left side
        self.ui.splitter_2.setSizes([500, 1])
        self.setFocus()
        
        #self.playerController.hide()  # Hide control panel in normal screen mode
            
                
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
        #self.player_thread = threading.Thread(target=self.PlayerThread)
        #self.player_thread.start()
        self.PlayerThread()
        
    def PlayerThread(self):
        
        # Get the selected row
        self.SelectedRow = self.ui.Channels_table.currentRow()
        
        # Get the channel name and stream URL
        channel_name, stream_url = self.channelList[self.SelectedRow]   

        # Play the stream
        self.player.setSource(QUrl(stream_url))
        self.player.play()
        
                
            
    def PlayStopStream(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            #self.player_thread.join()
        elif self.SelectedRow >= 0:
            self.setFocus()
            #self.player.setPosition(0)
            self.player.play()
            #self.PlayChannel()

    def HideCursor(self):
        if self.windowState() != Qt.WindowState.WindowFullScreen:
            return
        
        panel_width = self.control_panel.width()
        panel_height = self.control_panel.height()
        new_x = (self.width() - panel_width) // 2
        new_y = self.height() - panel_height - 20  # 20 pixels from bottom
        self.control_panel.move(self.mapToGlobal(QPoint(new_x, new_y)))
        self.control_panel.hide()
                    
        # Hide the mouse cursor
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        #self.controlContainer.hide()
        #self.videoStack.setCurrentWidget(self.videoController)
        #self.hideCursor()
  
    def ShowCursor(self):
        panel_width = self.control_panel.width()
        panel_height = self.control_panel.height()
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            new_x = (self.width() - panel_width) // 2
            new_y = self.height() - panel_height - 20
            global_pos = self.mapToGlobal(QPoint(new_x, new_y))
        else:
            new_x = (self.videoPanel.videoOutput.width() - panel_width) // 2 
            new_y = self.videoPanel.videoOutput.height() - panel_height - 20
            global_pos = self.videoPanel.videoOutput.mapToGlobal(QPoint(new_x, new_y))
        
        self.control_panel.move(global_pos)
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.control_panel.show()
        else:
            self.control_panel.hide()
          
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        #self.controlContainer.show()
        #self.ShowCursor()
        # Restart the inactivity timer
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.inactivityTimer.start()       
    
    def ShowCursorBusy(self):
        self.setCursor(QCursor(Qt.CursorShape.BusyCursor))        

if __name__ == "__main__":
    app = QApplication([])
    spyderApp = SpyderPlayer()
    spyderApp.show()
    app.exec()