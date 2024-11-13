import re, os
from PyQt6 import uic, QtCore
from PyQt6.QtGui import QCursor, QIcon, QMouseEvent
from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer, QPoint, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QStyleFactory
from VideoPlayer import *
from VLCPlayer import VLCPlayer
from QtPlayer import QtPlayer
from PlaylistManager import PlayListManager
from ScreensaverInhibitor import ScreensaverInhibitor
from SettingsManager import SettingsManager
from AppData import * 
import platform
from pathlib import Path
import sys
import time

# Import Converted UI Classes
from resources_rc import *    
from UI_SplashScreen import Ui_SplashScreen 
from UI_VideoControlPanel import Ui_VideoControlPanel   
from UI_PlayerMainWindow import Ui_PlayerMainWindow
from UI_Overlay import Ui_Overlay     
                        
class VideoControlPannel(QWidget):     
    def __init__(self, parent=None):

        super().__init__(parent)
        self.SpyderPlayer = parent
        
        self.ui = Ui_VideoControlPanel()
        self.ui.setupUi(self)
        
        # Make sure the control panel is frameless and transparent
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                           
class VideoOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent) 
        self.SpyderPlayer = parent
        self.videoPanel = self.SpyderPlayer.videoPanel
        
        self.ui = Ui_Overlay()
        self.ui.setupUi(self)   
        self.overlayLabel = self.ui.Overlay_label
        
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.ui.Overlay_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 2); font:30pt; border: none;") #border: none;
        
        self.overlayTxt = ""
        self.ui.Overlay_label.setText(self.overlayTxt)
        self.overlayLabel.setMouseTracking(True)
 
        
    def event(self, event):
        QApplication.sendEvent(self.SpyderPlayer, event)
        return True
        
    def Resize(self):
        #screen = QApplication.primaryScreen()  # Get primary screen
        #screen_geometry = screen.geometry()  # Get screen geometry
        #screenWidth = screen.size().width()        
        panel = self.SpyderPlayer.videoPanel
        panel_width = self.SpyderPlayer.ui.ShowControlPanel_top_label.width() - 4
        panel_height = self.SpyderPlayer.ui.ShowControlPanel_left_label.height() - 4
        new_x =  panel.x() + 1
        new_y =  panel.y() + 1

        #print(f"Coordinates: {new_x}, {new_y}")
        #print(f"Width: {panel_width}, Height: {panel_height}")
        self.setFixedWidth(panel_width)
        self.setFixedHeight(panel_height) 
        #self.move(new_x, new_y)
        global_pos = panel.mapToGlobal(QPoint(new_x, new_y))
        self.move(global_pos)

                                   
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
    videoPosition: int = 0
    isFullScreen: bool = False
    controlPanelPosition: QPoint = QPoint(0, 0)
    dataFilePath: str = "appdata.json"
    overlay: VideoOverlay = None
    player = None
    playerType: ENUM_PLAYER_TYPE = ENUM_PLAYER_TYPE.VLC
    
    def __init__(self, parent=None):

        super().__init__(parent)
        self.splashScreen = SplashScreen()
        self.splashScreen.ui.Status_label.setText("Initializing ...")
        self.splashScreen.ui.Version_label.setText("Version: 1.0.0 Beta")
        
        self.mousePressPos = None
        self.mouseMoveActive = False
        self.isFullScreen = False
                
        #---------------------------        
        # Load Screensaver Inhibitor
        #---------------------------
        self.screensaverInhibitor = ScreensaverInhibitor()
        self.screensaverInhibitor.uninhibit()
     
        #---------------------------
        # Load UI Files
        #---------------------------    
        self.ui = Ui_PlayerMainWindow()
        self.ui.setupUi(self)   
            
        
        self.statusLabel = self.ui.Status_label
        self.statusLabel.setText("")
        self.setWindowOpacity(0)
        
        #---------------------------
        # Load AppData from file
        #---------------------------
        self.dataFilePath = os.path.join(self.GetUserAppDataDirectory("SpyderPlayer"), self.dataFilePath)
        self.appData = AppData.load(self.dataFilePath)
        
        #---------------------------
        # Setup Playlist Manager
        #---------------------------
        self.playlistmanager = PlayListManager(self.ui.PlayList_tree, self.appData, self)
        #self.playlistmanager.installEventFilter(self)
                
        #---------------------------
        # Setup Control Panels
        #---------------------------
        self.controlPanelFS = VideoControlPannel(self)  
        self.controlPanelFS.setWindowOpacity(0.8)
        self.controlPanelFS.hide() 
        self.controlPanelFS.installEventFilter(self)
        self.controlPanel = VideoControlPannel(self)
        self.ui.Bottom_widget = self.controlPanel

        #---------------------------
        # Setup Layout
        #---------------------------
        self.ui.botomverticalLayout.addWidget(self.controlPanel)
        self.controlPanel.show()   
        self.ui.Horizontal_splitter.setSizes([400, 1000])
        self.ui.Vertical_splitter.setSizes([800, 1])   
        self.ui.Horizontal_splitter.installEventFilter(self)
        self.ui.Vertical_splitter.installEventFilter(self)
        
        self.ui.ShowControlPanel_top_label.installEventFilter(self)
        self.ui.ShowControlPanel_top_label.setMouseTracking(True)
        self.ui.ShowControlPanel_bottom_label.installEventFilter(self)
        self.ui.ShowControlPanel_bottom_label.setMouseTracking(True)
        self.ui.ShowControlPanel_right_label.installEventFilter(self)
        self.ui.ShowControlPanel_right_label.setMouseTracking(True)
        self.ui.ShowControlPanel_left_label.installEventFilter(self)
        self.ui.ShowControlPanel_left_label.setMouseTracking(True)
        
        #---------------------------           
        # Setup player      
        #---------------------------               
        self.videoPanel = self.ui.VideoView_widget 
        self.LoadPlayer()
        
        print("PlayerType: ", self.playerType)        
        
            
        #self.player.installEventFilter(self) 
        self.videoPanel.installEventFilter(self)
                                
        # Install event filter to detect window state changes
        self.setMouseTracking(True)
        #self.videoWidget.setMouseTracking(True)
        #self.videoPanel.setMouseTracking(True)
        #self.ui.Channels_table.setMouseTracking(True)
        self.installEventFilter(self)
        #self.videoStack.installEventFilter(self)
        #self.ui.Channels_table.installEventFilter(self)   
        
        # Create Settings Manager
        self.settingsManager = SettingsManager(self.appData)
        
        #---------------------------
        # Setup Video Overlay
        #---------------------------
        self.overlay = VideoOverlay(self)
        self.overlay.installEventFilter(self)
                
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
        
        self.player.SetVolume(100)
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
        
        # Next Channel Button
        self.controlPanelFS.ui.Next_button.clicked.connect(self.PlayNextChannel)
        self.controlPanel.ui.Next_button.clicked.connect(self.PlayNextChannel)
        
        # Previous Channel Button
        self.controlPanelFS.ui.Previous_button.clicked.connect(self.PlayPreviousChannel)
        self.controlPanel.ui.Previous_button.clicked.connect(self.PlayPreviousChannel)
        
        # Last Channel Button
        self.controlPanelFS.ui.Last_button.clicked.connect(self.PlayLastChannel)
        self.controlPanel.ui.Last_button.clicked.connect(self.PlayLastChannel) 
        
        # Search button
        self.ui.Search_button.clicked.connect(self.SearchChannels)
        
        
        
        #self.ui.Settings_button.setEnabled(True)
        self.ui.Settings_button.clicked.connect(self.ShowSettings)
        self.settingsManager.reLoadAllPlayListsSignal.connect(self.InitializePlayLists)
        self.settingsManager.loadMediaFileSignal.connect(self.LoadSessionMediaFile)
        self.settingsManager.loadPlayListSignal.connect(self.LoadSessionPlayList)
        
        # Set up a timer to detect inactivity
        self.inactivityTimer = QTimer(self)
        self.inactivityTimer.setInterval(3000)  # 3000ms = 3 seconds
        self.inactivityTimer.timeout.connect(self.InactivityDetected)
        
        self.stalledVideoTimer = QTimer(self)
        self.stalledVideoTimer.setInterval(5000) 
        #self.stalledVideoTimer.timeout.connect(self.StalledVideoDetected) 

        # Connect the player signals
        self.player.updatePosition.connect(self.VideoTimePositionChanged)
        self.player.playerStateChanged.connect(self.PlaybackStateChanged)
        self.player.errorOccured.connect(self.PlayerError)
        
        
        '''self.player.durationChanged.connect(self.PlayerDurationChanged)
        self.player.mediaStatusChanged.connect(self.OnMediaStatusChanged)
        self.player.positionChanged.connect(self.VideoTimePositionChanged)
        self.player.playbackStateChanged.connect(self.PlaybackStateChanged)'''
        
        # Connect the slider signals   
        self.controlPanel.ui.VideoPosition_slider.sliderPressed.connect(self.OnSliderPressed)
        self.controlPanelFS.ui.VideoPosition_slider.sliderPressed.connect(self.OnSliderPressed)    
        self.controlPanel.ui.VideoPosition_slider.sliderMoved.connect(self.ChangeVideoPosition) 
        self.controlPanelFS.ui.VideoPosition_slider.sliderMoved.connect(self.ChangeVideoPosition) 
        self.controlPanel.ui.VideoPosition_slider.sliderReleased.connect(self.OnSliderReleased)
        self.controlPanelFS.ui.VideoPosition_slider.sliderReleased.connect(self.OnSliderReleased)
        
            
        self.controlPanelFS.ui.VideoPosition_slider.setEnabled(False)
        self.controlPanel.ui.VideoPosition_slider.setEnabled(False)

        self.ui.Horizontal_splitter.splitterMoved.connect(self.OnHSplitterResized)
        
        #self.player.audioOutputChanged.connect(self.ResetAudioOutput)
        #self.audioOutput..connect(self.AudioOutputError)
        #self.player.bufferProgressChanged.connect(self.PlayerBufferProgressChanged)
        #self.player.errorChanged.connect(self.PlayerError)
        #self.player.errorOccurred.connect(self.PlayerError)
        #self.player.hasVideoChanged.connect(self.HasVideoChanged)   
        
        
        # Get the current font
        font = self.font()

        # Get the font family and size
        font_family = font.family()
        font_size = font.pointSize()
        print("Window Font: " + font_family + " " + str(font_size))
        
        # Check if the point size is smaller than 11 and increase it if necessary
        if font.pointSize() < 11:
            self.setStyleSheet("color: white; font:11pt;")
            #font.setPointSize(10)  # Set the font size to 12
            #self.setFont(font)  # Set the font for the widget'''
    
        #-----------------------------------------
        # Show Splash Screen and Load Playlists
        #-----------------------------------------
        self.InitializePlayLists()
        
        #print("User App Data Directory: " + str(self.GetUserAppDataDirectory("SpyderPlayer"))) 
        
    def InitializePlayLists(self):
        # Reload Spyder Player if the player type has changed
        if self.playerType != self.appData.PlayerType:
            self.ReloadSpyderPlayer()
        
        # Show Splash Screen
        self.overlay.hide()
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
        
        # ReAdd all Session Playlists
        self.splashScreen.UpdateStatus("Adding Session Playlists ....")
        self.splashScreen.UpdateStatus("Adding Session Playlists ....")
        self.playlistmanager.ReAddOpenFilesList()
        self.playlistmanager.ReAddOpenSessionPlayLists()
        
        self.splashScreen.UpdateStatus("Initialization Complete", 0.5)
        self.splashScreen.UpdateStatus("Initialization Complete", 0.5)
        
        # Make sure Splash Screen is shown a minimum amount of time
        while self.splashScreen.splashTimerCompleted == False:
            QApplication.processEvents()
        
        self.splashScreen.hide()
        self.setWindowOpacity(1.0)
        self.ActivateControlPanel()   
        self.overlay.show() 
        self.OnHSplitterResized(0, 0)
        self.overlay.Resize() 
    
                 
    def eventFilter(self, obj, event):
        #print("Event Filter: ", event.type().name )
        self.KeepSettingsOnTopIfVisible()
    
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowFullScreen or self.windowState() == Qt.WindowState.WindowMaximized:
                if QApplication.focusObject() != None and not self.settingsManager.settingStack.isVisible():
                    self.PlayerFullScreen()
                print("Full Screen: ", QEvent.Type.WindowStateChange.name)
                
            elif self.windowState() == Qt.WindowState.WindowMinimized:
                pass  # Do nothing
            else:
                #print("Focused object: ", str(QApplication.focusObject()) )
                if QApplication.focusObject() != None and not self.settingsManager.settingStack.isVisible():
                    self.PlayerNormalScreen()
                                      
                print("Normal Screen: ", QEvent.Type.WindowStateChange.name)
                
        elif event.type() == QEvent.Type.KeyRelease:   
            self.UserActivityDetected()
            #print("Key Press: ", QEvent.Type.KeyPress.name)
            if not self.ui.Query_input.hasFocus():
                if event.key() == self.appData.HotKeys.escapeFullscreen and self.isFullScreen:  
                    self.PlayerNormalScreen()
                    #print("Key Press: esc")
                    return True
                elif event.key() == self.appData.HotKeys.toggleFullscreen: 
                    if self.isFullScreen:
                        self.PlayerNormalScreen()
                        #print("Key Press: F")
                        return True
                    else:
                        self.PlayerFullScreen()
                        return True
                    
                elif event.key() == self.appData.HotKeys.playpause: 
                    self.PlayPausePlayer()
                    return True
                elif event.key() == self.appData.HotKeys.playpauseAlt and not self.playlistmanager.playlistTree.hasFocus():
                    self.PlayPausePlayer()
                    return True
                elif event.key() == self.appData.HotKeys.volumeMute:
                    self.MutePlayer()
                    return True
                elif event.key() == self.appData.HotKeys.showOptions: 
                    #print("Key Press: Q")
                    self.settingsManager.ShowSettings()
                    return True
                elif event.key() == self.appData.HotKeys.togglePlaylist: 
                    #print("Key Press: P")
                    self.TogglePlaylistView()
                    return True
                elif event.key() == self.appData.HotKeys.gotoLast: #Qt.Key.Key_Backspace:
                    self.PlayLastChannel()
                    return True
                elif event.key() == self.appData.HotKeys.volumeUp and not self.playlistmanager.playlistTree.hasFocus(): 
                    self.IncreaseVolume()
                    return True
                elif event.key() ==  self.appData.HotKeys.volumeDown and not self.playlistmanager.playlistTree.hasFocus():
                    self.DecreaseVolume()
                    return True
                elif event.key() == self.appData.HotKeys.seekBackward: 
                    self.SkipBackward()
                    return True
                elif event.key() == self.appData.HotKeys.seekForward:
                    self.SkipForward()
                    return True
                    
                #elif event.key() == Qt.Key.Key_C:
                    #if self.playlistmanager.isVisible():
                        #self.playlistmanager.CollapseCurrentPlaylist()
                elif event.key() == self.appData.HotKeys.collapseAllLists: 
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.CollapseAllPlaylists()
                    return True
                elif event.key() == self.appData.HotKeys.gotoTopofList: 
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.GotoTopOfList()
                    return True
                elif event.key() == self.appData.HotKeys.gotoBottomofList: 
                    if self.playlistmanager.isVisible():
                        #print("Key Press: B")
                        self.playlistmanager.GotoBottomOfList()
                    return True
                        
                elif event.key() == self.appData.HotKeys.sortListDescending:
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.SortSearchResultsDescending()
                    return True
                elif event.key() == self.appData.HotKeys.sortListAscending: 
                    if self.playlistmanager.isVisible():
                        self.playlistmanager.SortSearchResultsAscending()                       
                    return True
                elif event.key() == Qt.Key.Key_Return and self.playlistmanager.playlistTree.hasFocus():
                    self.playlistmanager.ItemManuallyEntered()
                    return True
                elif event.key() == self.appData.HotKeys.playNext:  
                    self.PlayNextChannel()
                    return True
                elif event.key() == self.appData.HotKeys.playPrevious:
                    self.PlayPreviousChannel()
                    return True
                else:   
                    return True
                
            elif event.key() == Qt.Key.Key_Return:
                self.SearchChannels()
                return True
            
            elif event.key() == Qt.Key.Key_Escape:
                self.ui.Query_input.setText('')
                return True
                       
            else:
                pass
                
                
        elif event.type() in [QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel]:
            #print("Event Filter: ", QEvent.Type.MouseMove.name)
            self.UserActivityDetected()
                       
        return super().eventFilter(obj, event)

    def LoadPlayer(self):
        if self.player != None:
            self.player.Stop()
            #self.player.destroy()
           # self.player = None
            
        if self.appData.PlayerType == ENUM_PLAYER_TYPE.VLC:
            self.player = VLCPlayer(self)
        elif self.appData.PlayerType == ENUM_PLAYER_TYPE.QTMEDIA:
            self.player = QtPlayer(self)
            
        self.playerType = self.appData.PlayerType
        self.ui.Status_label.setText("Player: " + self.playerType.name)
        
            
    def KeepSettingsOnTopIfVisible(self):
        try:
            if self.settingsManager.settingStack.isVisible():
                self.settingsManager.settingStack.setFocus()
        except:
            pass
        
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
        videoLength = self.Format_ms_to_Time(duration)
        
        #print("Video Length Changed: ", videoLength)
        #print("Duration Changed: ", duration)
        
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
            self.videoChangesPosition = True

    def VideoTimePositionChanged(self, position):         
        self.videoPosition = position

        if self.videoChangesPosition == True:
            videoTime = self.Format_ms_to_Time(position)
            self.controlPanelFS.ui.CurrentTime_label.setText(videoTime)
            self.controlPanel.ui.CurrentTime_label.setText(videoTime)
            self.controlPanelFS.ui.VideoPosition_slider.setValue(position)
            self.controlPanel.ui.VideoPosition_slider.setValue(position)

            
    def OnSliderPressed(self):
        self.videoPlaying = self.player.GetPlayerState() == ENUM_PLAYER_STATE.PLAYING
        self.player.OnChangingPosition(self.videoPlaying)
        
        
    def ChangeVideoPosition(self):             
        self.videoChangesPosition = False      
        slider = self.sender()
        position = slider.value()
        
        self.player.SetPosition(position) 
        self.videoPosition = position   
        
        self.videoChangesPosition = True

    def OnSliderReleased(self):
        self.VideoTimePositionChanged(self.videoPosition)
        self.player.OnChangedPosition(self.videoPlaying)
        
            
                
    '''def OnMediaStatusChanged(self, status):
        message = str(status).split('.')[1]
        codec_info = self.player.metaData().value(QMediaMetaData.Key.AudioCodec)
        if codec_info:
            print(f"Audio codec: {codec_info}")
        else:
            print("Audio codec information not available")

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

        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.RetryPlaying()
            
        # IF stream video unexpectedly ends, try and restart it (EndOfMedia ... Message)
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.videoDuration == 0:
            self.StalledVideoDetected()
             
    def StalledVideoDetected(self):
        if self.retryPlaying:
            self.stalledVideoTimer.stop()
            print("Stalled Video - Resetting")
            self.statusLabel.setText("Stalled Video - Resetting")
            self.player.stop()
            #time.sleep(1)
            self.PlayVideo()
            self.retryPlaying = False  
            if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.ChangePlayingUIStates(False)
        else:
            self.ChangePlayingUIStates(False)
            
    def RetryPlaying(self):
        if self.retryPlaying:
            print("Retrying Playback")
            self.player.stop()
            #time.sleep(1)
            self.PlayVideo()
            self.retryPlaying = False
            if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                self.ChangePlayingUIStates(False)
            #print("Playback Retry State: ", self.player.playbackState())
        else:
            self.ChangePlayingUIStates(False)'''
             
    def StalledVideoDetected(self):
        if self.retryPlaying:
            self.stalledVideoTimer.stop()
            print("Stalled Video - Resetting")
            self.statusLabel.setText("Stalled Video - Resetting")
            self.player.Stop()
            time.sleep(2)
            self.player.RefreshVideoSource()
            self.player.Play()
            self.retryPlaying = False  
            #if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                #self.ChangePlayingUIStates(False)
        else:
            self.ChangePlayingUIStates(False)
                               
    def PlaybackStateChanged(self, state: ENUM_PLAYER_STATE):
        print("Playback State Changed: ", str(state.name))
        
        if state == ENUM_PLAYER_STATE.PLAYING:
            self.ShowCursorNormal()
            self.PlayerDurationChanged(self.player.GetVideoDuration())
            self.ChangePlayingUIStates(True)
            self.screensaverInhibitor.inhibit()
            self.retryPlaying = True
            self.statusLabel.setText("")
        elif state == ENUM_PLAYER_STATE.LOADING:
            self.ShowCursorBusy()
            self.statusLabel.setText("Buffering .....")
        elif state == ENUM_PLAYER_STATE.STALLED and self.videoDuration == 0:
            if self.retryPlaying:
                self.ShowCursorBusy()
                self.StalledVideoDetected()
            else:
                self.statusLabel.setText("Invalid Media or Source")
                self.screensaverInhibitor.uninhibit()
                self.ShowCursorNormal()
        else:
            self.ShowCursorNormal()
            self.stalledVideoTimer.stop()
            self.ChangePlayingUIStates(False)
            self.screensaverInhibitor.uninhibit()
            self.statusLabel.setText("")
           
            
    def PlayerFullScreen(self):
        self.ui.Horizontal_splitter.setSizes([0, 800])  # Hide left side    
        self.ui.Vertical_splitter.setSizes([800, 0])  
        self.playListVisible = False
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.ShowControlPanel()
        self.videoPanel.showFullScreen()
        self.videoPanel.setFocus()
        self.isFullScreen = True  
        self.ui.Horizontal_splitter.setHandleWidth(1)
        #self.ui.Vertical_splitter.setFocus()
        self.overlay.Resize()
        self.overlay.setFocus()
        
        if self.platform == "Linux":
            # Initial postion is off when going to fullscreen in linux, so just hide it initially
            self.controlPanelFS.hide()
            
        self.inactivityTimer.start() 


            
    def PlayerNormalScreen(self):
        self.controlPanelFS.hide()
        self.setWindowState(Qt.WindowState.WindowNoState)
        #self.ui.VideoView_widget.showNormal()  # Ensure the widget is visible
        self.ui.Horizontal_splitter.setSizes([400, 1000])  # Restore left side
        self.ui.Vertical_splitter.setSizes([800, 1])
        self.ui.Horizontal_splitter.setHandleWidth(4)
        self.videoPanel.showNormal()
        self.playListVisible = True
        self.inactivityTimer.stop()
        self.setFocus()
        self.videoPanel.activateWindow()
        self.isFullScreen = False
        self.ShowControlPanel()
        self.overlay.Resize()
            
    def TogglePlaylistView(self):
        if self.playListVisible:
            self.ui.Horizontal_splitter.setSizes([0, 1000])  # Hide left side 
            self.ui.Horizontal_splitter.setHandleWidth(1)
            self.playListVisible = False
            self.overlay.setFocus()
            self.overlay.Resize()
        else:
            self.ui.Horizontal_splitter.setSizes([400, 1000])
            self.ui.Horizontal_splitter.setHandleWidth(4)
            self.playListVisible = True
            self.overlay.Resize()
                   
        if self.isFullScreen:
            self.ShowControlPanel()

            
    def MutePlayer(self):            
        self.volume = self.player.GetVolume()
        
        if self.player.IsMuted():
            self.UpdateVolumeSlider(self.volume)
            self.controlPanelFS.ui.Volume_slider.setEnabled(True)
            self.controlPanel.ui.Volume_slider.setEnabled(True)
            self.controlPanel.ui.FullVolume_button.setEnabled(True)
            self.controlPanelFS.ui.FullVolume_button.setEnabled(True) 
            self.player.Mute(False)           
        else:
            self.UpdateVolumeSlider(0)  
            self.controlPanelFS.ui.Volume_slider.setEnabled(False)
            self.controlPanel.ui.Volume_slider.setEnabled(False)
            self.controlPanel.ui.FullVolume_button.setEnabled(False)
            self.controlPanelFS.ui.FullVolume_button.setEnabled(False)
            self.player.Mute(True)         
             
    def StopPlayer(self):
        self.player.Stop()
        self.statusLabel.setText('')
  
    
    def FullVolumePlayer(self):
        self.player.SetVolume(100)
        self.UpdateVolumeSlider(100)
                
    def ChangeVolume(self):
        slider = self.sender()
        volume = slider.value()
        print(f"Volume: {volume}")

        self.player.SetVolume(volume)
        self.UpdateVolumeSlider(volume)
        self.player.Mute(False)
        
    def UpdateVolumeSlider(self, volume: int):
        self.controlPanelFS.ui.Volume_slider.setValue(volume)
        self.controlPanel.ui.Volume_slider.setValue(volume)
                
    def IncreaseVolume(self):
        volume = self.player.GetVolume()          
        volume = volume + 10
        if volume > 100:
            volume = 100

        self.player.SetVolume(volume)
        self.UpdateVolumeSlider(volume)
        
    def DecreaseVolume(self):
        volume = self.player.GetVolume()            
        volume = volume - 10
        if volume < 0:
            volume = 0

        self.player.SetVolume(volume)
        self.UpdateVolumeSlider(volume)
        
      
    def SkipForward(self):
        if self.videoDuration > 0:
            self.player.SetPosition(self.player.GetPosition() + 10000)
        
    def SkipBackward(self):
        if self.videoDuration > 0:
            self.player.SetPosition(self.player.GetPosition() - 10000)
            
    def PlayNextChannel(self):
        channelName, source = self.playlistmanager.GoToAdjacentItem(True)
        self.PlaySelectedChannel(channelName, source)
        
    def PlayPreviousChannel(self):
        channelName, source = self.playlistmanager.GoToAdjacentItem(False)
        self.PlaySelectedChannel(channelName, source)
                
    def WindowChanged(self):
        if self.windowState() == QWidget.WindowState.WindowMaximized or self.windowState() == QWidget.WindowState.WindowFullScreen:
            self.showNormal()
            self.ui.Horizontal_splitter.setSizes([400, 1000])
            self.ui.Vertical_splitter.setSizes([800, 1])
            self.controlPanel.setFocus()
            self.overlay.Resize()
            self.player.ChangeUpdateTimerInterval(False)

        elif self.windowState() == QWidget.WindowState.WindowMinimized:
            self.player.ChangeUpdateTimerInterval(False)
            self.overlay.showMinimized()
            pass  # Do nothing
        else:
            self.ui.splitter.Horizontal_splitter.setSizes([0, 500])
            self.ui.splitter.Vertical_splitter.setSizes([500, 0])
            self.overlay.Resize()
            self.showFullScreen()
            self.overlay.setFocus()
            self.inactivityTimer.start()
            self.player.ChangeUpdateTimerInterval(True)
            
           
    def PlaySelectedChannel(self, channel_name, source):
        self.retryPlaying = True
        self.player.Stop()
        self.setWindowTitle("SPYDER Player - " + channel_name)
        self.currentSource = source
        self.player.SetVideoSource(source)
        self.player.Play()
        self.ChangePlayingUIStates(True)
            
    def LoadSessionMediaFile(self, fileEntry: PlayListEntry):
        print("Received file entry: " + fileEntry.name)
        self.playlistmanager.AddSessionFile(fileEntry)
        
    def LoadSessionPlayList(self, fileEntry: PlayListEntry):
        self.ShowCursorBusy()
        print("Received playlist entry: " + fileEntry.name)
        self.playlistmanager.LoadPlayList(fileEntry, False)
        self.ShowCursorNormal()
              
    def ChangePlayingUIStates(self, playing: bool):
        if playing:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon(":icons/icons/pause.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon(":icons/icons/pause.png"))
        else:
            self.controlPanelFS.ui.Play_button.setIcon(QIcon(":icons/icons/play.png"))
            self.controlPanel.ui.Play_button.setIcon(QIcon(":icons/icons/play.png"))
            
        self.controlPanelFS.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)
        self.controlPanel.ui.VideoPosition_slider.setEnabled(self.videoChangesPosition)            
                
    def PlayPausePlayer(self):
        state = self.player.GetPlayerState()
        
        if state == ENUM_PLAYER_STATE.PLAYING:
            self.player.Pause()    
        else:   
            # Check if video reached end, if so stop and restart at beginning
            if self.player.GetPlayerState() == ENUM_PLAYER_STATE.ENDED:
                self.videoPosition = 0
                self.player.Stop()
                self.player.Play()
            else:
                self.player.Play()


    def PlayLastChannel(self):
        channel_name, stream_url = self.playlistmanager.GoToLastSelectedItem()
        
        if channel_name is None or stream_url is None:
            return
        
        self.setWindowTitle("SPYDER Player - " + channel_name)
        self.PlaySelectedChannel(channel_name, stream_url)
        
  
    def ShowControlPanel(self):
        panel_width = self.controlPanelFS.width()
        panel_height = self.controlPanelFS.height()
        
        if self.windowState() == self.isFullScreen:  
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
            
        if self.isFullScreen:
            self.controlPanelFS.show()
        else:
            self.controlPanelFS.hide()
                    

    def SearchChannels(self):
        searchText = self.ui.Query_input.text()
        self.playlistmanager.SearchChannels(searchText)
        self.playlistmanager.playlistTree.setFocus()
        '''if self.isFullScreen:
            self.controlPanelFS.setFocus()
        else:
            self.controlPanel.setFocus()'''
    
    def ResetAudioOutput(self, error):
        print("Audio device error: " + error)
        #self.audioOutput = QAudioOutput()

                
    def PlayerError(self, error: str):
        print("[Player Error] -- " + error)
    
        self.statusLabel.setText("Error: " + error)
        
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
                self.overlay.hide()

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
            self.overlay.show()
            self.overlay.Resize()    
        return super().mouseReleaseEvent(event)
    
    def moveEvent(self, event):
        # Update position of the other widget
        if self.overlay:
            self.overlay.Resize()  
        super().moveEvent(event)
        
    def UserActivityDetected(self):
        if self.isFullScreen:
            QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                    
            self.inactivityTimer.start()
            if not self.controlPanelFS.isVisible():
                self.ShowControlPanel()
                    
                if self.playListVisible:
                    self.playlistmanager.activateWindow()
                else:
                    self.overlay.setFocus()
                
                
    def InactivityDetected(self):
        if self.isFullScreen and not self.controlPanelFS.hasFocus():
            self.controlPanelFS.hide()
            self.overlay.setFocus()
            
            if not self.playListVisible and not self.settingsManager.settingStack.isVisible():
                QApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            
    def ShowSettings(self):
        print("Show Settings Button Pressed")
        self.settingsManager.ShowSettingsFirst()        
            
    def GetUserAppDataDirectory(self, app_name):
        if self.platform == 'Windows':  
            settings_dir = Path(os.getenv('APPDATA')) / app_name
        elif self.platform  == 'Linux':  
            settings_dir = Path.home() / '.config' / app_name
        elif self.platform == 'Darwin': 
            settings_dir = Path.home() / 'Library' / 'Application Support' / app_name

        # Create the directory if it doesn't exist
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir        
            
    def __del__(self):
        self.screensaverInhibitor.uninhibit()
      
    def ActivateControlPanel(self):
        if self.isFullScreen:
            pass
            #self.controlPanelFS.setFocus()
        else:
            self.controlPanel.setFocus()
       
    def OnHSplitterResized(self, pos, index):
        self.overlay.Resize()
        
    def ReloadSpyderPlayer(self):
        global spyderPlayer
        self.player.Stop()
        spyderPlayer.close()        # Close the current instance
        spyderPlayer.deleteLater()   # Schedule it for deletion

        # Create a new instance of MainWidget
        spyderPlayer = SpyderPlayer()
        spyderPlayer.show()       
        
          
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion')) # Setting this fixes the odd scroll bar color in Windows
    
    spyderPlayer = SpyderPlayer()
    spyderPlayer.show()
    spyderPlayer.OnHSplitterResized(0, 0)
    
    app.exec()

            