import re, os
from PyQt6 import uic, QtCore
from PyQt6.QtGui import QCursor, QIcon, QMouseEvent
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QSizeGrip
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PlaylistManager import PlayListManager
from ScreensaverInhibitor import ScreensaverInhibitor
from SettingsManager import SettingsManager
from AppData import * 
import platform
import sys
import time

# Import Converted UI Classes
from resources_rc import *    
from UI_SplashScreen import Ui_SplashScreen 
from UI_VideoControlPanel import Ui_VideoControlPanel   
from UI_PlayerMainWindow import Ui_PlayerMainWindow
     
                        
class VideoControlPannel(QWidget):     
    def __init__(self, parent=None):

        super().__init__(parent)
        self.SpyderPlayer = parent
        
        self.ui = Ui_VideoControlPanel()
        self.ui.setupUi(self)
        
        # Make sure the control panel is frameless and transparent
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                           
                           
class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the UI file
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)
        
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        
        self.CenterSplashScreen()
        
        self.splashTimer = QTimer()
        self.splashTimerCompleted = False
        self.splashTimer.setInterval(5000)
        self.splashTimer.timeout.connect(self.SetTimeout)
        
    def CenterSplashScreen(self):
        """ Center the splash screen on the primary screen """
        screen = QApplication.primaryScreen()  # Get primary screen
        screen_geometry = screen.geometry()  # Get screen geometry
        splash_size = self.size()  # Get splash screen size

        # Calculate the center position
        x = (screen_geometry.width() - splash_size.width()) // 2
        y = (screen_geometry.height() - splash_size.height()) // 2

        # Move the splash screen to the center
        self.move(x, y)    
        
        
    def UpdateStatus(self, status: str, delay: int = 0.1):  
        self.ui.Status_label.setText(status)
        QApplication.processEvents()
        time.sleep(delay)
        
    def SetTimeout(self):
        self.splashTimerCompleted = True
        
class SpyderPlayer(QWidget):
    platform: str = platform.system()
    channelList = []
    playListVisible: bool = True
    volume: int = 100
    videoChangesPosition: bool = False
    videoDuration: int = 0
    isFullScreen: bool = False
    controlPanelPosition: QPoint = QPoint(0, 0)
    dataFilePath: str = "appdata.json"
    
    def __init__(self, parent=None):

        super().__init__(parent)
        self.splashScreen = SplashScreen()
        self.splashScreen.ui.Status_label.setText("Initializing ...")
        self.splashScreen.ui.Version_label.setText("Version: 1.0.0 Beta")
        
        self.mousePressPos = None
        self.mouseMoveActive = False
        self.isFullScreen = False
                
        # Get Screensaver Inhibitor
        self.screensaverInhibitor = ScreensaverInhibitor()
        self.screensaverInhibitor.uninhibit()
     
        #---------------------------
        # Load UI Files
        #---------------------------    
        self.ui = Ui_PlayerMainWindow()
        self.ui.setupUi(self)    

        if self.platform == "Linux": # or self.platform == "Windows":
            self.ui.Title_frame.hide()
        else: 
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint )
            
            
        self.videoLabel = self.ui.CurrentlyPlaying_label
        self.videoLabel.setText("")
        self.statusLabel = self.ui.Status_label
        self.statusLabel.setText("")
        self.setWindowOpacity(0)
        
        #---------------------------
        # Load AppData from file
        #---------------------------
        self.appData = AppData.load(self.dataFilePath)
        
        #---------------------------
        # Setup Playlist Manager
        #---------------------------
        self.playlistmanager = PlayListManager(self.ui.PlayList_tree, self.appData, self)
        self.playlistmanager.installEventFilter(self)
                
        #---------------------------
        # Setup Control Panels
        #---------------------------
        self.controlPanelFS = VideoControlPannel(self)  
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
        
        # Create Settings Manager
        self.settingsManager = SettingsManager(self.appData)
        
        #----------------------------------------------------------------------------
        # Connect signals
        #----------------------------------------------------------------------------
        
        # Channel Is DoubleClicked
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
        
        #self.ui.Settings_button.setEnabled(True)
        self.ui.Settings_button.clicked.connect(self.ShowSettings)
        self.settingsManager.reLoadAllPlayListsSignal.connect(self.InitializePlayer)
        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.InactivityDetected)
        #self.inactivityTimer.timeout.connect(self.HideCursor)
        #self.inactivityTimer.start()   
        
        self.ui.Close_button.clicked.connect(self.ExitApp)
        self.ui.Minimize_button.clicked.connect(lambda: self.showMinimized())
        self.ui.Maximize_button.clicked.connect(self.PlayerFullScreen)

        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.positionChanged.connect(self.VideoTimePositionChanged)
        self.player.playbackStateChanged.connect(self.PlaybackStateChanged)
        self.controlPanelFS.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        self.controlPanel.ui.VideoPosition_slider.sliderReleased.connect(self.ChangeVideoPosition)
        
        self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
        self.controlPanel.ui.VideoPosition_slider.setEnabled(False)

        #-----------------------------------------
        # Show Splash Screen and Load Playlists
        #-----------------------------------------
        self.InitializePlayer()
        
    def InitializePlayer(self):
        # Show Splash Screen
        self.splashScreen.show()
        self.splashScreen.splashTimer.start()
        self.splashScreen.UpdateStatus("Loading Playlists:", 1)
                
        self.playlistmanager.ResetAllLists()
        
        # Load Playlists and Update Splash Screen        
        for i in range(len(self.appData.PlayLists)):
            self.splashScreen.UpdateStatus("Loading " + self.appData.PlayLists[i].name + " ....")
            self.splashScreen.UpdateStatus("Loading " + self.appData.PlayLists[i].name + " ....")
            self.playlistmanager.LoadPlayList(self.appData.PlayLists[i])
        
        # Load Library Playlist
        self.splashScreen.UpdateStatus("Loading Library ....")
        self.splashScreen.UpdateStatus("Loading Library ....")
        self.playlistmanager.LoadLibrary()
        
        # Load Favorites last to verify that items in other playlists have been loaded
        self.splashScreen.UpdateStatus("Loading Favorites ....")
        self.splashScreen.UpdateStatus("Loading Favorites ....")
        self.playlistmanager.LoadFavorites()
        
        self.splashScreen.UpdateStatus("Initialization Complete", 0.5)
        self.splashScreen.UpdateStatus("Initialization Complete", 0.5)
        
        # Make sure Splash Screen is shown a minimum amount of time
        while self.splashScreen.splashTimerCompleted == False:
            QApplication.processEvents()
        
        self.splashScreen.hide()
        self.setWindowOpacity(1.0)
               
        
                 
    def eventFilter(self, obj, event):
        #print("Event Filter: ", event.type().name )
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                self.PlayerFullScreen()
                print("Full Screen: ", QEvent.Type.WindowStateChange.name)
                
            elif self.windowState() == Qt.WindowState.WindowMinimized:
                pass  # Do nothing
            else:
                self.PlayerNormalScreen()
                print("Normal Screen: ", QEvent.Type.WindowStateChange.name)
                #self.ShowCursor()
            #print("Window State: ", self.windowState())
                
        elif event.type() == QEvent.Type.KeyRelease:   
            self.UserActivityDetected()
            #print("Key Press: ", QEvent.Type.KeyPress.name)
            if self.ui.Query_input.hasFocus() == False:
                if event.key() == Qt.Key.Key_Escape and self.isFullScreen: 
                    self.PlayerNormalScreen()
                    print("Key Press: esc")
                    return True
                elif event.key() == Qt.Key.Key_F:
                    if self.isFullScreen:
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
                elif event.key() == Qt.Key.Key_O:
                    #print("Key Press: Q")
                    self.settingsManager.ShowSettings()
                    return True
                elif event.key() == Qt.Key.Key_W:
                    print("Key Press: W")
                    #self.activateWindow()
                    #self.videoPanel.setFocus()
                    self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                    #self.setFocus()
                    #self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                    #self.ShowCursor()
                    #print("Show cursor")
                    return True
                elif event.key() == Qt.Key.Key_L:
                    #print("Key Press: P")
                    self.TogglePlaylistView()
                    return True
                elif event.key() == Qt.Key.Key_Backspace:
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
                    
                #elif event.key() == Qt.Key.Key_C:
                    #if self.playlistmanager.isVisible():
                        #self.playlistmanager.CollapseCurrentPlaylist()
                elif event.key() == Qt.Key.Key_C:
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
                    #self.ShowCursor()
                    return True
                
            elif event.key() == Qt.Key.Key_Return:
                self.SearchChannels()
                #self.ui.PlayList_tree.setFocus()
                return True
            
            elif event.key() == Qt.Key.Key_Escape:
                self.ui.Query_input.setText('')
                #self.ui.Playlist_treeview.setFocus()
                return True
            
            
            else:
                pass
                #self.ShowCursor()
                
        elif event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel]:
            #print("Event Filter: ", QEvent.Type.MouseMove.name)
            self.UserActivityDetected()
            #self.ShowCursor()  
            '''if self.windowState() == Qt.WindowState.WindowFullScreen:
                pass
                #self.ShowCursor()
                # Restart the timer on mouse move
                #self.inactivityTimer.start()
            elif event.type() == QEvent.Type.MouseButtonPress:
                self.dragging = True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.dragging = False'''
                       
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
        self.videoDuration = duration
        
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
        
        slider = self.sender()
        position = slider.value()
            
        self.player.setPosition(position)
            
        self.videoChangesPosition == True
        #print("Slider Position Changed: ", position)

        self.blockSignals(False)
        
    def on_media_status_changed(self, status):
        message = str(status).split('.')[1]
        
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.statusLabel.setText('')
        else:
            self.statusLabel.setText(message + " .....")
        
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.ShowCursorNormal()
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            self.ShowCursorBusy()
        else: 
            self.ShowCursorNormal()    
             
        
            
    def PlaybackStateChanged(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.ChangePlayingUIStates(True)
            self.screensaverInhibitor.inhibit()
        else:
            self.ChangePlayingUIStates(False)
            self.screensaverInhibitor.uninhibit()
            
            
    def PlayerFullScreen(self):
        self.ui.Title_frame.hide()
        self.ui.Horizontal_splitter.setSizes([0, 500])  # Hide left side    
        self.ui.Vertical_splitter.setSizes([500, 0])  
        self.playListVisible = False
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.ShowControlPanel()
        self.setFocus()
        self.isFullScreen = True  
                    
        if self.platform == "Linux":
            # Initial postion is off when going to fullscreen in linux, so just hide it initially
            self.controlPanelFS.hide()
            
        self.inactivityTimer.start() 


            
    def PlayerNormalScreen(self):
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        if self.platform != "Linux":
            self.ui.Title_frame.show()
        self.controlPanelFS.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        #self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.Horizontal_splitter.setSizes([400, 1000])  # Restore left side
        self.ui.Vertical_splitter.setSizes([800, 1])
        
        self.playListVisible = True
        self.inactivityTimer.stop()
        self.setFocus()
        self.videoPanel.activateWindow()
        self.isFullScreen = False
        #self.playerController.hide()  # Hide control panel in normal screen mode
            
    def TogglePlaylistView(self):
        if self.playListVisible:
            self.ui.Horizontal_splitter.setSizes([0, 1000])  # Hide left side 
            self.playListVisible = False
        else:
            self.ui.Horizontal_splitter.setSizes([300, 1000])
            self.playListVisible = True
            
        if self.isFullScreen:
            self.ShowControlPanel()

            
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
        self.statusLabel.setText('')
        
    
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
        if self.videoDuration > 0:
            self.player.setPosition(self.player.position() + 10000)
        
    def SkipBackward(self):
        if self.videoDuration > 0:
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
            
           
    def PlaySelectedChannel(self, channel_name, stream_url):
        self.player.stop()
        self.videoLabel.setText(channel_name)
        self.setWindowTitle("SPYDER Player - " + channel_name)
        self.player.setSource(QUrl(stream_url))
        try:
            self.player.play()
        except Exception as e:
            print(e)
            self.player.stop()
        
        self.ChangePlayingUIStates(True)
            
          
    def ChangePlayingUIStates(self, playing: bool):
        if playing:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon(":icons/icons/pause.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon(":icons/icons/pause.png"))
            self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
            self.controlPanel.ui.VideoPosition_slider.setEnabled(False)
        else:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon(":icons/icons/play.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon(":icons/icons/play.png"))
            self.controlPanelFS.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)
            self.controlPanel.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)            
                
    def PlayPausePlayer(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            #self.ChangePlayingUIStates(False)
            
        else: 
            self.setFocus()
            #self.player.setPosition(0)
            self.player.play()
            #self.ChangePlayingUIStates(True)
            #self.PlayChannel()

    def PlayLastChannel(self):
        channel_name, stream_url = self.playlistmanager.GoToLastSelectedItem()
        
        if channel_name is None or stream_url is None:
            return
        
        self.videoLabel.setText(channel_name)
        self.setWindowTitle("SPYDER Player - " + channel_name)
        self.PlaySelectedChannel(channel_name, stream_url)
        
  
    def ShowControlPanel(self):
        panel_width = self.controlPanelFS.width()
        panel_height = self.controlPanelFS.height()
        
        if self.windowState() == self.isFullScreen:  #Qt.WindowState.WindowFullScreen:
            new_x = (self.width() - panel_width) // 2
            new_y = self.height() - panel_height - 20
            global_pos = self.mapToGlobal(QPoint(new_x, new_y))
        else:
            new_x = (self.videoPanel.width() - panel_width) // 2 
            new_y = self.videoPanel.height() - panel_height - 20
            global_pos = self.videoPanel.mapToGlobal(QPoint(new_x, new_y))
        
        if self.controlPanelPosition != global_pos:
            self.controlPanelPosition = global_pos
            self.controlPanelFS.move(global_pos)
            
        #if self.windowState() == Qt.WindowState.WindowFullScreen:
        if self.isFullScreen:
            self.controlPanelFS.show()
        else:
            self.controlPanelFS.hide()
                    

    def SearchChannels(self):
        searchText = self.ui.Query_input.text()
        self.playlistmanager.SearchChannels(searchText)
    
    def ShowCursorBusy(self):
        self.setCursor(QCursor(Qt.CursorShape.BusyCursor))      
        
    def ShowCursorNormal(self):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  
        
    def ShowCursorBlank(self):
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        '''if self.platform == "Darwin":
            QCursor.setPos(self.mapToGlobal(QPoint(self.width() + 1, self.height() + 1)))
        
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            #self.setCursor(QCursor(Qt.CursorShape.BlankCursor))'''
        
        
        
    def ExitApp(self):
        self.screensaverInhibitor.uninhibit()
        self.close()
        app.exit()
       
    def mousePressEvent(self, event):
        self.UserActivityDetected()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Capture the global position where the mouse was pressed
            self.mousePressPos = event.globalPosition().toPoint()
            if not self.isFullScreen:
                self.mouseMoveActive = True

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):    
        self.UserActivityDetected()  
        if self.mouseMoveActive and self.mousePressPos:
            # Calculate how far the mouse moved
            delta = event.globalPosition().toPoint() - self.mousePressPos
            # Move the widget (or window) by the same amount
            self.move(self.pos() + delta)
            # Update the press position for the next movement calculation
            self.mousePressPos = event.globalPosition().toPoint()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.UserActivityDetected()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Reset when the left mouse button is released
            self.mousePressPos = None
            self.mouseMoveActive = False      
        return super().mouseReleaseEvent(event)
    
    def UserActivityDetected(self):
        if self.isFullScreen:
            QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
            
            self.inactivityTimer.start()
            if not self.controlPanelFS.isVisible():
                self.ShowControlPanel()
                    
                if self.playListVisible:
                    self.playlistmanager.activateWindow()
                else:
                    self.videoPanel.activateWindow()
                
                
    def InactivityDetected(self):
        if self.isFullScreen:
            self.controlPanelFS.hide()
            self.videoPanel.activateWindow()
            
            if not self.playListVisible and not self.settingsManager.settingStack.isVisible():
                QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            
    def ShowSettings(self):
        print("Show Settings Button Pressed")
        self.settingsManager.ShowSettings()        
            
    def __del__(self):
        self.screensaverInhibitor.uninhibit()
       
       
if __name__ == "__main__":
    app = QApplication(sys.argv)

    spyderPlayer = SpyderPlayer()
    spyderPlayer.show()
    
    app.exec()

            