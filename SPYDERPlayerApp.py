import re, os
from PyQt6 import uic, QtCore
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QToolTip, QWidget, QHeaderView,  QHBoxLayout, QVBoxLayout, QPushButton, QSlider
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PlaylistManager import PlaylistManager


                
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
        
    '''def ShowCursorBusy(self):
        self.SpyderPlayer.ShowCursorBusy() 
        
    def ShowCursorNormal(self):
        self.SpyderPlayer.ShowCursorNormal()    
        
    def ShowCursorBlank(self):
        self.SpyderPlayer.ShowCursorBlank() '''   
        
    def eventFilter(self, obj, event):
        QApplication.sendEvent(self.SpyderPlayer, event)
                           
              
class SpyderPlayer(QWidget):
    channelList = []
    playListVisible: bool = True
    volume: int = 100
    lastChannelIndex: int = -1
    selectedChannelIndex: int = -1
    cursorVisible: bool = True
    videoChangesPosition: bool = False
    dragging: bool = False
    videoPosition: int = 0
    
    def __init__(self, parent=None):

        super().__init__(parent)
        self.mousePressPos = None
        self.mouseMoveActive = False
        
        # Get current directory and append GUI file     
        mainUIPath = os.getcwd() + "/assets/PlayerMainWindow.ui"
        
        # Load the UI files
        self.ui = uic.loadUi(mainUIPath, self)  
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint )
        self.videoLabel = self.ui.CurrentlyPlaying_label
        self.videoLabel.setText("")
        #---------------------------
        # Setup Playlist Tree
        #---------------------------
        self.playlistmanager = PlaylistManager(self.ui.Playlist_treeview, self)
        self.playlistmanager.installEventFilter(self)
        
        #---------------------------
        # Setup Control Panel
        #---------------------------
        self.controlPanelFS = VideoControlPannel(self)  #FloatingControlPanel()
        self.controlPanelFS.hide() 
        self.controlPanelFS.installEventFilter(self)
        self.controlPanel = VideoControlPannel(self)
        self.ui.Bottom_widget = self.controlPanel
        self.controlPanel.installEventFilter(self)
        

        #---------------------------           
        # Setup player      
        #---------------------------   
        self.videoPanel = self.ui.VideoView_widget 
        self.videoPanel.installEventFilter(self)
        self.player = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)
        self.player.setVideoOutput(self.videoPanel)
        self.player.installEventFilter(self) 
        
        # Set the Left of vertical splitter to a fixed size
        self.ui.Horizontal_splitter.setSizes([400, 1000])
        self.ui.Vertical_splitter.setSizes([800, 1])
        # Set the side of the table column to the width of the horizontal layout
        #self.ui.Channels_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.ui.botomverticalLayout.addWidget(self.controlPanel)
        self.controlPanel.show()        
        
        # Install event filter to detect window state changes
        self.setMouseTracking(True)
        #self.videoWidget.setMouseTracking(True)
        self.videoPanel.setMouseTracking(True)
        #self.ui.Channels_table.setMouseTracking(True)
        self.installEventFilter(self)
        #self.videoStack.installEventFilter(self)
        #self.ui.Channels_table.installEventFilter(self)   
        
        
        #----------------------------------------------------------------------------
        # Connect signals
        #----------------------------------------------------------------------------
        # Connect signal to when cell is hovered show tooltip
        #self.ui.Channels_table.cellClicked.connect(self.ShowFullChannelName)
              
        #self.Channels_table.cellDoubleClicked.connect(self.PlayChannel)
        self.playlistmanager.treeItemSelectedSignal.connect(self.PlaySelectedChannel)
        
        # Play Button
        self.controlPanelFS.ui.Play_button.clicked.connect(self.PlayPausePlayer)
        self.controlPanel.ui.Play_button.clicked.connect(self.PlayPausePlayer)
        
        # Stop Buttos
        self.controlPanelFS.ui.Stop_button.clicked.connect(self.StopPlayer)
        self.controlPanel.ui.Stop_button.clicked.connect(self.StopPlayer)
        
        # Mute Button
        self.controlPanelFS.ui.Mute_button.clicked.connect(self.MutePlayer)
        self.controlPanel.ui.Mute_button.clicked.connect(self.MutePlayer)
        
        # Full Volume Button
        self.controlPanelFS.ui.FullVolume_button.clicked.connect(self.FullVolumePlayer)
        self.controlPanel.ui.FullVolume_button.clicked.connect(self.FullVolumePlayer)
        
        # Volume Slider
        self.controlPanelFS.ui.Volume_slider.sliderReleased.connect(self.ChangeVolume)
        self.controlPanel.ui.Volume_slider.sliderReleased.connect(self.ChangeVolume)
        self.audioOutput.setVolume(100)
        self.controlPanelFS.ui.Volume_slider.setValue(100)
        self.controlPanel.ui.Volume_slider.setValue(100)
        
        # Toggle List Button
        self.controlPanelFS.ui.ToggleList_button.clicked.connect(self.TogglePlaylistView)
        self.controlPanel.ui.ToggleList_button.clicked.connect(self.TogglePlaylistView)
        
        # Skip Forward Button
        self.controlPanelFS.ui.Forward_button.clicked.connect(self.SkipForward)
        self.controlPanel.ui.Forward_button.clicked.connect(self.SkipForward)
        
        # Skip Backwared Button
        self.controlPanelFS.ui.Backward_button.clicked.connect(self.SkipBackward)
        self.controlPanel.ui.Backward_button.clicked.connect(self.SkipBackward)
        
        # Last Channel Button
        self.controlPanelFS.ui.Last_button.clicked.connect(self.PlayLastChannel)
        self.controlPanel.ui.Last_button.clicked.connect(self.PlayLastChannel) 
        
        # Search button
        self.ui.Search_button.clicked.connect(self.SearchChannels)
        
        self.player.durationChanged.connect(self.PlayerDurationChanged)
        
        #self.ui.Play_button.clicked.connect(self.PlayStopStream)
        #self.LoadPlayList('us.m3u')

        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.HideCursor)
        #self.inactivityTimer.start()   
        
        self.ui.Close_button.clicked.connect(self.ExitApp)
        self.ui.Minimize_button.clicked.connect(lambda: self.showMinimized())
        self.ui.Maximize_button.clicked.connect(self.PlayerFullScreen)

        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.positionChanged.connect(self.VideoTimePositionChanged)
        self.controlPanelFS.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        self.controlPanel.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        
        self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
        self.controlPanel.ui.VideoPosition_slider.setEnabled(False)

             
    def eventFilter(self, obj, event):
        #print("Event Filter: ", event.type().name )
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                self.PlayerFullScreen()
                self.ShowCursor()
                print("Full Screen: ", QEvent.Type.WindowStateChange.name)
                
            elif self.windowState() == Qt.WindowState.WindowMinimized:
                pass  # Do nothing
            else:
                self.PlayerNormalScreen()
                print("Normal Screen: ", QEvent.Type.WindowStateChange.name)
                #self.ShowCursor()
                
        elif event.type() == QEvent.Type.KeyRelease:   
            #self.ShowCursor()
            #print("Key Press: ", QEvent.Type.KeyPress.name)
            if self.ui.Query_input.hasFocus() == False:
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
                elif event.key() == Qt.Key.Key_L:
                    self.TogglePlaylistView()
                    return True
                elif event.key() == Qt.Key.Key_L:
                    self.PlayLastChannel()
                    return True
                elif event.key() == Qt.Key.Key_Up:
                    self.IncreaseVolume()
                    return True
                elif event.key() == Qt.Key.Key_Down:
                    self.DecreaseVolume()
                    return True
                elif event.key() == Qt.Key.Key_Left:
                    self.SkipBackward()
                elif event.key() == Qt.Key.Key_Right:
                    self.SkipForward()
                    
                elif event.key() == Qt.Key.Key_C:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.CollapseCurrentPlaylist()
                elif event.key() == Qt.Key.Key_V:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.CollapseAllPlaylists()
                elif event.key() == Qt.Key.Key_T: # or Qt.Key.Key_PageUp:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.GotoTopOfList()
                    return True
                elif event.key() == Qt.Key.Key_B: # or Qt.Key.Key_PageDown:
                    if self.playlistmanager.isVisible():
                        print("Key Press: B")
                        self.playlistmanager.GotoBottomOfList()
                        
                elif event.key() == Qt.Key.Key_D:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.SortSearchResultsDescending()
                elif event.key() == Qt.Key.Key_A:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.SortSearchResultsAscending()                       
                    return True
                else:   
                    self.ShowCursor()
                    return True
                
            elif event.key() == Qt.Key.Key_Return:
                self.SearchChannels()
                self.ui.Playlist_treeview.setFocus()
                return True
            
            elif event.key() == Qt.Key.Key_Escape:
                self.ui.Query_input.setText('')
                #self.ui.Playlist_treeview.setFocus()
                return True
            
            
            else:
                self.ShowCursor()
                
                    
        elif event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel]:
            if self.windowState() == Qt.WindowState.WindowFullScreen:
                
                self.ShowCursor()
                # Restart the timer on mouse move
                #self.inactivityTimer.start()
            elif event.type() == QEvent.Type.MouseButtonPress:
                self.dragging = True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.dragging = False
                        
        return super().eventFilter(obj, event)

    def Format_ms_to_Time(self, ms: int):
        # Convert milliseconds to seconds
        seconds = int(ms / 1000)
        
        # Calculate hours, minutes, and remaining seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
    
        # Format as HH:MM:SS
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
          
      
    def PlayerDurationChanged(self, duration):
        print("Duration type", type(duration))
        
        videoLength = self.Format_ms_to_Time(duration)
        
        print("Duration Changed: ", videoLength)
        
        if duration == 0:
            self.controlPanelFS.ui.Forward_button.setEnabled(False)
            self.controlPanelFS.ui.Backward_button.setEnabled(False)
            self.controlPanelFS.ui.CurrentTime_label.setText("00:00:00")
            self.controlPanelFS.ui.TotalDuration_label.setText("00:00:00")
            self.controlPanel.ui.Forward_button.setEnabled(False)
            self.controlPanel.ui.Backward_button.setEnabled(False)
            self.controlPanel.ui.CurrentTime_label.setText("00:00:00")
            self.controlPanel.ui.TotalDuration_label.setText("00:00:00")
            #self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
            #self.controlPanel.ui.VideoPosition_slider.setEnabled(False)
            self.videoChangesPosition = False
            
        else:
            self.controlPanelFS.ui.Forward_button.setEnabled(True)
            self.controlPanelFS.ui.Backward_button.setEnabled(True)
            self.controlPanel.ui.Forward_button.setEnabled(True)
            self.controlPanel.ui.Backward_button.setEnabled(True)
            self.controlPanel.ui.TotalDuration_label.setText(videoLength)
            self.controlPanelFS.ui.TotalDuration_label.setText(videoLength)
            self.controlPanelFS.ui.VideoPosition_slider.setRange(0, duration)
            self.controlPanel.ui.VideoPosition_slider.setRange(0, duration)
            #self.controlPanelFS.ui.VideoPosition_slider.setEnabled(True)
            #self.controlPanel.ui.VideoPosition_slider.setEnabled(True)
            self.videoChangesPosition = True

    def VideoTimePositionChanged(self, position):
        if self.videoChangesPosition == True:
            self.controlPanelFS.ui.VideoPosition_slider.setValue(position)
            self.controlPanel.ui.VideoPosition_slider.setValue(position)
            self.controlPanelFS.ui.CurrentTime_label.setText(self.Format_ms_to_Time(position))
            self.controlPanel.ui.CurrentTime_label.setText(self.Format_ms_to_Time(position))
        
        
    def ChangeVideoPosition(self):
        self.blockSignals(True) 
        '''self.controlPanelFS.ui.VideoPosition_slider.blockSignals(True)
        self.controlPanel.ui.VideoPosition_slider.blockSignals(True)
        self.controlPanelFS.ui.VideoPosition_slider.sliderReleased.disconnect(self.ChangeVideoPosition)
        self.controlPanel.ui.VideoPosition_slider.sliderReleased.disconnect(self.ChangeVideoPosition)
        self.videoChangesPosition == False'''
        #self.player.pause()
        
        slider = self.sender()
        position = slider.value()
            
        self.player.setPosition(position)
            
        self.videoChangesPosition == True
        print("Slider Position Changed: ", position)
        '''self.controlPanelFS.ui.VideoPosition_slider.blockSignals(False)
        self.controlPanel.ui.VideoPosition_slider.blockSignals(False)        
        self.player.blockSignals(False)
        self.controlPanelFS.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        self.controlPanel.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        #self.player.play()'''
        self.blockSignals(False)
        
    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.ShowCursorNormal()
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.ShowCursorBusy()
        else: #elif status == QMediaPlayer.MediaStatus.NoMedia:
            print("Media Player Status: ", status)
            self.ShowCursorNormal()     

            
    def PlayerFullScreen(self):
        self.ui.Title_frame.hide()
        #if self.windowState() != Qt.WindowState.WindowFullScreen:
        self.ui.Horizontal_splitter.setSizes([0, 500])  # Hide left side    
        self.ui.Vertical_splitter.setSizes([500, 0])  
        self.playListVisible = False
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.controlPanelFS.show()
        self.setFocus()
        
        #self.videoStack.setCurrentWidget(self.videoPanel)
        self.inactivityTimer.start() 
        #self.ui.Playlist_treeview.setFocus()
        #self.ui.Horizontal_splitter.setEnabled(True)
        
            
    def PlayerNormalScreen(self):
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        self.ui.Title_frame.show()
        self.controlPanelFS.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        #self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.Horizontal_splitter.setSizes([400, 1000])  # Restore left side
        self.ui.Vertical_splitter.setSizes([800, 1])
        
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
            self.ui.Horizontal_splitter.setSizes([400, 1000])
            self.playListVisible = True
            
    def MutePlayer(self):
        if self.audioOutput.isMuted():
            self.audioOutput.setMuted(False)
            self.UpdateVolumeSlider(self.volume)
            self.controlPanelFS.ui.Volume_slider.setEnabled(True)
            self.controlPanel.ui.Volume_slider.setEnabled(True)
            self.controlPanel.ui.FullVolume_button.setEnabled(True)
            self.controlPanelFS.ui.FullVolume_button.setEnabled(True)            
        else:
            self.volume = int(self.audioOutput.volume()*100)
            self.audioOutput.setMuted(True)
            self.UpdateVolumeSlider(0)  
            self.controlPanelFS.ui.Volume_slider.setEnabled(False)
            self.controlPanel.ui.Volume_slider.setEnabled(False)
            self.controlPanel.ui.FullVolume_button.setEnabled(False)
            self.controlPanelFS.ui.FullVolume_button.setEnabled(False)

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
        self.controlPanelFS.ui.Volume_slider.setValue(volume)
        self.controlPanel.ui.Volume_slider.setValue(volume)
                
    def IncreaseVolume(self):
        volume = self.audioOutput.volume()            
        volume = volume + 0.1
        if volume > 1.0:
            volume = 1.0
        self.audioOutput.setVolume(volume)
        self.UpdateVolumeSlider(int(volume*100))
        
    def DecreaseVolume(self):
        volume = self.audioOutput.volume()            
        volume = volume - 0.1
        if volume < 0.0:
            volume = 0.0
        self.audioOutput.setVolume(volume)
        self.UpdateVolumeSlider(int(volume*100))
        
      
    def SkipForward(self):
        self.player.setPosition(self.player.position() + 10000)
        
    def SkipBackward(self):
        self.player.setPosition(self.player.position() - 10000)
            
    def WindowChanged(self):
        if self.windowState() == QWidget.WindowState.WindowMaximized or self.windowState() == QWidget.WindowState.WindowFullScreen:
            self.showNormal()
            self.ui.Horizontal_splitter.setSizes([400, 1000])
            self.ui.Vertical_splitter.setSizes([800, 1])
            self.controlPanel.setFocus()
            
            #self.ShowControlPanel()
        elif self.windowState() == QWidget.WindowState.WindowMinimized:
            pass  # Do nothing
        else:
            self.ui.splitter.Horizontal_splitter.setSizes([0, 500])
            self.ui.splitter.Vertical_splitter.setSizes([500, 0])
            self.showFullScreen()
            self.videoPanel.setFocus()
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

        self.videoLabel.setText(channel_name)
        
        # Play the stream
        self.player.setSource(QUrl(stream_url))
        self.player.play()
        
    def PlaySelectedChannel(self, channel_name, stream_url):
        self.player.stop()
        self.videoLabel.setText(channel_name)
        self.player.setSource(QUrl(stream_url))
        try:
            self.player.play()
        except Exception as e:
            print(e)
            self.player.stop()
        #self.player.play()    
        #duration = self.player.duration()
        #position = self.player.position()
        #print(f"Duration: {duration} Position: {position}")
        
        self.ChangePlayingUIStates(True)
            
          
    def ChangePlayingUIStates(self, playing: bool):
        if playing:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon("assets/icons/pause.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon("assets/icons/pause.png"))
            self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
            self.controlPanel.ui.VideoPosition_slider.setEnabled(False)
        else:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon("assets/icons/play.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon("assets/icons/play.png"))
            self.controlPanelFS.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)
            self.controlPanel.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)            
                
    def PlayPausePlayer(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.ChangePlayingUIStates(False)
            #self.player_thread.join()
        else: # self.selectedChannelIndex >= 0:
            self.setFocus()
            #self.player.setPosition(0)
            self.player.play()
            self.ChangePlayingUIStates(True)
            #self.PlayChannel()

    def PlayLastChannel(self):
        channel_name, stream_url = self.playlistmanager.GoToLastSelectedItem()
        
        if channel_name is None or stream_url is None:
            return
        
        self.videoLabel.setText(channel_name)
        self.PlaySelectedChannel(channel_name, stream_url)
        
        
        
    def HideCursor(self):
        #self.inactivityTimer.stop()
        #print(self.windowState())
        
        if self.windowState() != Qt.WindowState.WindowFullScreen: # or self.cursorVisible == False:
            return
        
        #if self.controlPanelFS
        
        '''panel_width = self.controlPanelFullScreen.width()
        panel_height = self.controlPanelFullScreen.height()
        new_x = (self.width() - panel_width) // 2
        new_y = self.height() - panel_height - 20  # 20 pixels from bottom
        self.controlPanelFullScreen.move(self.mapToGlobal(QPoint(new_x, new_y)))'''
        
        #self.videoStack.setCurrentWidget(self.videoPanel)
        #self.ui.Channels_table.setFocus()
        
        # Hide the mouse cursor
        
        self.inactivityTimer.stop()
        #
        # self.controlPanelFS.ShowCursorBlank()
        self.controlPanelFS.hide()
        self.inactivityTimer.start()
        self.videoPanel.setFocus()
        self.ShowCursorBlank()
        #self.cursorVisible = False
        #keyboard.press('q')
        #self.controlContainer.hide()
        #self.videoStack.setCurrentWidget(self.videoController)
        #self.hideCursor()
  
    def ShowControlPanel(self):
        panel_width = self.controlPanelFS.width()
        panel_height = self.controlPanelFS.height()
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            new_x = (self.width() - panel_width) // 2
            new_y = self.height() - panel_height - 20
            global_pos = self.mapToGlobal(QPoint(new_x, new_y))
        else:
            new_x = (self.videoPanel.width() - panel_width) // 2 
            new_y = self.videoPanel.height() - panel_height - 20
            global_pos = self.videoPanel.mapToGlobal(QPoint(new_x, new_y))
        
        self.controlPanelFS.move(global_pos)
        
        if self.windowState() == Qt.WindowState.WindowFullScreen:
            self.controlPanelFS.show()
        else:
            self.controlPanelFS.hide()
                    
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

    def SearchChannels(self):
        searchText = self.ui.Query_input.text()
        self.playlistmanager.SearchChannels(searchText)
    
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