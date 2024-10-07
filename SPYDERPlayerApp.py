import re, os
from PyQt6 import uic, QtCore
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QToolTip, QWidget, QHeaderView,  QHBoxLayout, QVBoxLayout, QPushButton, QSlider
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PlaylistManager import PlaylistManager

import inspect


                
class VideoControlPannel(QWidget):     
    def __init__(self, parent=None):

        super().__init__(parent)
        self.SpyderPlayer = parent
        
        controllerUIpath = os.getcwd() + "/assets/VideoControlPanel.ui"
        self.ui = uic.loadUi(controllerUIpath, self)
        
        #self.ui.setStyleSheet("background-color: transparent;")
        # Make sure the control panel is frameless and transparent
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        #self.setWindowFlags(Qt.WindowType.FramelessWindowHint ) #| Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
    def ShowCursorBusy(self):
        self.SpyderPlayer.ShowCursorBusy() 
        
    def ShowCursorNormal(self):
        self.SpyderPlayer.ShowCursorNormal()    
        
    def ShowCursorBlank(self):
        self.SpyderPlayer.ShowCursorBlank()                     
              
class SpyderPlayer(QWidget):
    channelList = []
    playListVisible: bool = True
    volume: int = 100
    lastChannelIndex: int = -1
    selectedChannelIndex: int = -1
    cursorVisible: bool = True
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mousePressPos = None
        self.mouseMoveActive = False
        
        # Get current directory and append GUI file     
        mainUIPath = os.getcwd() + "/assets/PlayerMainWindow.ui"
        
        # Load the UI files
        self.ui = uic.loadUi(mainUIPath, self)  
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint )
        
        #---------------------------
        # Setup Playlist Tree
        #---------------------------
        self.playlistmanager = PlaylistManager(self.ui.Playlist_treeview, self)
        
        
        #---------------------------
        # Setup Control Panel
        #---------------------------
        self.controlPanelFullScreen = VideoControlPannel(self)  #FloatingControlPanel()
        self.controlPanelFullScreen.hide() 
        self.controlPanelFullScreen.installEventFilter(self)
        self.controlPanelBottom = VideoControlPannel(self)
        self.ui.Bottom_widget = self.controlPanelBottom
        self.controlPanelBottom.installEventFilter(self)
        

        #---------------------------           
        # Setup player      
        #---------------------------   
        self.videoPanel = self.ui.VideoView_widget 
        self.player = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)
        self.player.setVideoOutput(self.videoPanel)
        
        # Set the Left of vertical splitter to a fixed size
        self.ui.Horizontal_splitter.setSizes([300, 1000])
        self.ui.Vertical_splitter.setSizes([500, 1])
        # Set the side of the table column to the width of the horizontal layout
        #self.ui.Channels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ui.botomverticalLayout.addWidget(self.controlPanelBottom)
        self.controlPanelBottom.show()        
        
        # Install event filter to detect window state changes
        self.setMouseTracking(True)
        #self.videoWidget.setMouseTracking(True)
        self.videoPanel.setMouseTracking(True)
        #self.ui.Channels_table.setMouseTracking(True)
        self.installEventFilter(self)
        #self.videoStack.installEventFilter(self)
        #self.ui.Channels_table.installEventFilter(self)   
        self.player.installEventFilter(self) 
        
        #----------------------------------------------------------------------------
        # Connect signals
        #----------------------------------------------------------------------------
        # Connect signal to when cell is hovered show tooltip
        #self.ui.Channels_table.cellClicked.connect(self.ShowFullChannelName)
              
        #self.Channels_table.cellDoubleClicked.connect(self.PlayChannel)
        self.playlistmanager.treeItemSelectedSignal.connect(self.PlaySelectedChannel)
        
        
        # Play Button
        self.controlPanelFullScreen.ui.Play_button.clicked.connect(self.PlayPausePlayer)
        self.controlPanelBottom.ui.Play_button.clicked.connect(self.PlayPausePlayer)
        
        # Stop Buttos
        self.controlPanelFullScreen.ui.Stop_button.clicked.connect(self.StopPlayer)
        self.controlPanelBottom.ui.Stop_button.clicked.connect(self.StopPlayer)
        
        # Mute Button
        self.controlPanelFullScreen.ui.Mute_button.clicked.connect(self.MutePlayer)
        self.controlPanelBottom.ui.Mute_button.clicked.connect(self.MutePlayer)
        
        # Full Volume Button
        self.controlPanelFullScreen.ui.FullVolume_button.clicked.connect(self.FullVolumePlayer)
        self.controlPanelBottom.ui.FullVolume_button.clicked.connect(self.FullVolumePlayer)
        
        # Volume Slider
        self.controlPanelFullScreen.ui.Volume_slider.sliderReleased.connect(self.ChangeVolume)
        self.controlPanelBottom.ui.Volume_slider.sliderReleased.connect(self.ChangeVolume)
        self.audioOutput.setVolume(100)
        self.controlPanelFullScreen.ui.Volume_slider.setValue(100)
        self.controlPanelBottom.ui.Volume_slider.setValue(100)
        
        # Toggle List Button
        self.controlPanelFullScreen.ui.ToggleList_button.clicked.connect(self.TogglePlaylistView)
        self.controlPanelBottom.ui.ToggleList_button.clicked.connect(self.TogglePlaylistView)
        
        # Last Channel Button
        self.controlPanelFullScreen.ui.Last_button.clicked.connect(self.PlayLastChannel)
        self.controlPanelBottom.ui.Last_button.clicked.connect(self.PlayLastChannel) 
        
        self.ui.Close_button.clicked.connect(self.ExitApp)
        
        #self.ui.Play_button.clicked.connect(self.PlayStopStream)
        #self.LoadPlayList('us.m3u')

        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.HideCursor)
        #self.inactivityTimer.start()        
        

        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.ShowCursorNormal()
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.ShowCursorBusy()
        
    '''def mouseMoveEvent(self, event):
        print("Mouse move event")
        return super().mouseMoveEvent(event)'''
        
             
    def eventFilter(self, obj, event):
        #print("Event Filter: ", event.type().name )
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                self.PlayerFullScreen()
                self.ShowCursor()
                print("Full Screen: ", QEvent.Type.WindowStateChange.name)
                
            else:
                self.PlayerNormalScreen()
                print("Normal Screen: ", QEvent.Type.WindowStateChange.name)
                #self.ShowCursor()
                
        elif event.type() == QEvent.Type.KeyRelease:   
            #self.ShowCursor()
            #print("Key Press: ", QEvent.Type.KeyPress.name)
            if event.key() == Qt.Key.Key_Escape and self.windowState() == Qt.WindowState.WindowFullScreen:
                self.PlayerNormalScreen()
                print("Key Press: esc")
                #return True
            elif event.key() == Qt.Key.Key_F:
                if self.windowState() == Qt.WindowState.WindowFullScreen:
                    self.PlayerNormalScreen()
                    print("Key Press: F")
                    return True
                else:
                    self.PlayerFullScreen()
                    return True
            elif event.key() == Qt.Key.Key_K or event.key() == Qt.Key.Key_Space:
                self.PlayPausePlayer()
            elif event.key() == Qt.Key.Key_M:
                self.MutePlayer()
            elif event.key() == Qt.Key.Key_Q:
                print("Key Press: Q")
                #self.setFocus()
                #self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
                self.HideCursor()
                #print("Hide cursor")
                return True
            elif event.key() == Qt.Key.Key_W:
                print("Key Press: W")
                #self.setFocus()
                #self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                self.ShowCursor()
                #print("Show cursor")
                return True
            else:
                self.ShowCursor()
                
                    
        elif event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel]:
            if self.windowState() == Qt.WindowState.WindowFullScreen:
                
                self.ShowCursor()
                # Restart the timer on mouse move
                #self.inactivityTimer.start()
                        
        return super().eventFilter(obj, event)

     

            
    def PlayerFullScreen(self):
        self.ui.Title_frame.hide()
        #if self.windowState() != Qt.WindowState.WindowFullScreen:
        self.ui.Horizontal_splitter.setSizes([0, 500])  # Hide left side    
        self.ui.Vertical_splitter.setSizes([500, 0])  
        self.playListVisible = False
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.controlPanelFullScreen.show()
        self.setFocus()
        
        #self.videoStack.setCurrentWidget(self.videoPanel)
        self.inactivityTimer.start() 
        #self.ui.Playlist_treeview.setFocus()
        #self.ui.Horizontal_splitter.setEnabled(True)
        
            
    def PlayerNormalScreen(self):
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        self.ui.Title_frame.show()
        self.controlPanelFullScreen.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        #self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.Horizontal_splitter.setSizes([300, 1000])  # Restore left side
        self.ui.Vertical_splitter.setSizes([500, 1])
        
        self.playListVisible = True
        self.inactivityTimer.stop()
        self.setFocus()
        
        #self.playerController.hide()  # Hide control panel in normal screen mode
            
    def TogglePlaylistView(self):
        if self.playListVisible:
            self.ui.Horizontal_splitter.setSizes([0, 1000])  # Hide left side 
            #self.ui.Horizontal_splitter.setEnabled(True)
            self.playListVisible = False
        else:
            self.ui.Horizontal_splitter.setSizes([300, 1000])
            self.playListVisible = True
            
    def MutePlayer(self):
        if self.audioOutput.isMuted():
            self.audioOutput.setMuted(False)
            self.UpdateVolumeSlider(self.volume)
        else:
            self.volume = int(self.audioOutput.volume()*100)
            self.audioOutput.setMuted(True)
            self.UpdateVolumeSlider(0)   

    def StopPlayer(self):
        self.player.stop()
        
    
    def FullVolumePlayer(self):
        self.audioOutput.setVolume(1.0)
        self.audioOutput.setMuted(False)
        self.UpdateVolumeSlider(100)
                
    def ChangeVolume(self):
        slider = self.sender()
        volume = slider.value()
        print(f"Volume: {volume}")
        self.audioOutput.setVolume(volume/100)
        self.UpdateVolumeSlider(volume)
        self.audioOutput.setMuted(False)
        
    def UpdateVolumeSlider(self, volume: int):
        self.controlPanelFullScreen.ui.Volume_slider.setValue(volume)
        self.controlPanelBottom.ui.Volume_slider.setValue(volume)
                
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
            self.ui.Horizontal_splitter.setSizes([200, 500])
            self.ui.Vertical_splitter.setSizes([500, 1])
            
            #self.ShowControlPanel()
        else:
            self.ui.splitter.Horizontal_splitter.setSizes([0, 500])
            self.ui.splitter.Vertical_splitter.setSizes([500, 0])
            self.showFullScreen()
            #self.ui.Channels_table.setFocus()
            self.inactivityTimer.start()
            
    def PlayChannel(self):
        # Create Player Thread
        #self.player_thread = threading.Thread(target=self.PlayerThread)
        #self.player_thread.start()
        self.PlayerThread()
        
    def PlayerThread(self):
        self.lastChannelIndex = self.selectedChannelIndex
        
        # Get the selected row
        self.selectedChannelIndex = self.ui.Channels_table.currentRow()

        # Get the channel name and stream URL
        channel_name, stream_url = self.channelList[self.selectedChannelIndex]   

        # Play the stream
        self.player.setSource(QUrl(stream_url))
        self.player.play()
        
    def PlaySelectedChannel(self, channel_name, stream_url):
        
        self.player.setSource(QUrl(stream_url))
        self.player.play()    
            
    def PlayPausePlayer(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            #self.player_thread.join()
        elif self.selectedChannelIndex >= 0:
            self.setFocus()
            #self.player.setPosition(0)
            self.player.play()
            #self.PlayChannel()

    def PlayLastChannel(self):
        '''tempChannel = self.selectedChannelIndex
        
        self.selectedChannelIndex = self.lastChannelIndex
        self.lastChannelIndex = tempChannel'''
        
        # Get the channel name and stream URL
        #channel_name, stream_url = self.channelList[self.selectedChannelIndex]  
        '''self.playlistmanager.GoToLastSelectedItem() 
        channel_name, stream_url = self.playlistmanager.GetSelectedItem()
        
        # Play the stream
        self.player.setSource(QUrl(stream_url))
        self.player.play()'''
        channel_name, stream_url = self.playlistmanager.GoToLastSelectedItem()
        self.PlaySelectedChannel(channel_name, stream_url)
        
        
        
    def HideCursor(self):
        #self.inactivityTimer.stop()
        #print(self.windowState())
        print(inspect.currentframe().f_code.co_name)
        
        if self.windowState() != Qt.WindowState.WindowFullScreen: # or self.cursorVisible == False:
            return
        
        '''panel_width = self.controlPanelFullScreen.width()
        panel_height = self.controlPanelFullScreen.height()
        new_x = (self.width() - panel_width) // 2
        new_y = self.height() - panel_height - 20  # 20 pixels from bottom
        self.controlPanelFullScreen.move(self.mapToGlobal(QPoint(new_x, new_y)))'''
        
        #self.videoStack.setCurrentWidget(self.videoPanel)
        #self.ui.Channels_table.setFocus()
        
        # Hide the mouse cursor
        
        self.inactivityTimer.stop()
        self.controlPanelFullScreen.ShowCursorBlank()
        self.controlPanelFullScreen.hide()
        self.inactivityTimer.start()
        self.ShowCursorBlank()
        #self.cursorVisible = False
        #keyboard.press('q')
        #self.controlContainer.hide()
        #self.videoStack.setCurrentWidget(self.videoController)
        #self.hideCursor()
  
    def ShowControlPanel(self):
        panel_width = self.controlPanelFullScreen.width()
        panel_height = self.controlPanelFullScreen.height()
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            new_x = (self.width() - panel_width) // 2
            new_y = self.height() - panel_height - 20
            global_pos = self.mapToGlobal(QPoint(new_x, new_y))
        else:
            new_x = (self.videoPanel.width() - panel_width) // 2 
            new_y = self.videoPanel.height() - panel_height - 20
            global_pos = self.videoPanel.mapToGlobal(QPoint(new_x, new_y))
        
        self.controlPanelFullScreen.move(global_pos)
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.controlPanelFullScreen.show()
        else:
            self.controlPanelFullScreen.hide()
                    
    def ShowCursor(self):
        '''panel_width = self.controlPanelFullScreen.width()
        panel_height = self.controlPanelFullScreen.height()
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            new_x = (self.width() - panel_width) // 2
            new_y = self.height() - panel_height - 20
            global_pos = self.mapToGlobal(QPoint(new_x, new_y))
        else:
            new_x = (self.videoPanel.width() - panel_width) // 2 
            new_y = self.videoPanel.height() - panel_height - 20
            global_pos = self.videoPanel.mapToGlobal(QPoint(new_x, new_y))
        
        self.controlPanelFullScreen.move(global_pos)
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.controlPanelFullScreen.show()
        else:
            self.controlPanelFullScreen.hide()'''
            
        print(inspect.currentframe().f_code.co_name)
        
        if self.windowState() != Qt.WindowState.WindowFullScreen:
            return
        
        #self.ShowControlPanel() 
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        #self.controlContainer.show()
        #self.ShowCursor()
        # Restart the inactivity time
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.ShowControlPanel()
            self.inactivityTimer.start()     
        #print("Show cursor")  

    
    def ShowCursorBusy(self):
        self.setCursor(QCursor(Qt.CursorShape.BusyCursor))      
        
    def ShowCursorNormal(self):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  
        
    def ShowCursorBlank(self):
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        
    def ExitApp(self):
        self.close()
        app.exit()
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Capture the global position where the mouse was pressed
            self.mousePressPos = event.globalPosition().toPoint()
            self.mouseMoveActive = True

    def mouseMoveEvent(self, event):
        if self.mouseMoveActive and self.mousePressPos:
            # Calculate how far the mouse moved
            delta = event.globalPosition().toPoint() - self.mousePressPos
            # Move the widget (or window) by the same amount
            self.move(self.pos() + delta)
            # Update the press position for the next movement calculation
            self.mousePressPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Reset when the left mouse button is released
            self.mousePressPos = None
            self.mouseMoveActive = False        

if __name__ == "__main__":
    app = QApplication([])
    spyderApp = SpyderPlayer()
    spyderApp.show()
    app.exec()