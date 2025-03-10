import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QSize
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PyQt6.QtMultimediaWidgets import QVideoWidget

from VideoPlayer import *


class QtPlayer(VideoPlayer):
    def __init__(self, mainWindow: QWidget, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.mainWindow = mainWindow
        
        self.subtitleCount = -1
        self.subtitleList = [] # List of tuples
        self.subtitleIndex = -1
        
        # Create and add QVideoWidget to the main window
        #self.mainWindow.ui.gridLayout.removeWidget(self.mainWindow.videoPanel)
        
        self.videoPanel = QVideoWidget(self.mainWindow.videoPanel)
        self.mainWindow.ui.gridLayout.addWidget(self.videoPanel, 1, 1, 1, 1)
            
        self.InitPlayer()    
        
        # Init Signals
        self.player.durationChanged.connect(self.PlayerDurationChanged)
        self.player.positionChanged.connect(self.PlayerPositionChanged)
        self.player.playbackStateChanged.connect(self.PlaybackStateChanged)
        self.player.mediaStatusChanged.connect(self.MediaStatusChanged)
        
    def InitPlayer(self):
        self.player = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)
        self.player.setVideoOutput(self.videoPanel)
        
        
    def SetVideoSource(self, videoSource: str):  
        self.source = videoSource
        self.player.setSource(QUrl(self.source))
        self.subtitleCount = -1
        self.subtitleIndex = -1
        self.subtitleList = []
        
    def RefreshVideoSource(self):
        self.player.setSource(QUrl(''))
        time.sleep(1)
        self.player.setSource(QUrl(self.source))
    
    def Play(self):
        try:
            self.player.play()
        except Exception as e:
            self.player.stop()  
            print(e)
            self.ErrorOccured(str(e))
            
    def Pause(self):
        try:
            self.player.pause()
        except Exception as e:
            print(e)
            self.ErrorOccured(str(e))
            
    def Stop(self):
        try:
            self.player.stop()
        except Exception as e:
            print(e)
            self.ErrorOccured(str(e))
                  
    def SetPosition(self, position: int):
        self.player.setPosition(position)
        self.position = position
        
    def GetPosition(self):
        self.position = self.player.position()
        return self.position
    
    def GetVideoDuration(self):
        return self.duration
    
    def SetVolume(self, volume: int):
        self.audioOutput.setVolume(volume/100)
        
    def GetVolume(self):
        return int(self.audioOutput.volume()*100)
    
    def IsMuted(self):
        return self.audioOutput.isMuted()
    
    def Mute(self, mute: bool): 
        self.audioOutput.setMuted(mute) 
        
    def PlayerDurationChanged(self, duration: int):
        self.duration = duration
        self.UpdateDuration(duration)
        
    def PlayerPositionChanged(self, position: int):
        self.position = position
        self.UpdatePosition(position)                
        
    def GetPlayerState(self) -> ENUM_PLAYER_STATE:
        return self.currentState
        
    def PlaybackStateChanged(self, state):        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.currentState = ENUM_PLAYER_STATE.PLAYING           
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.currentState = ENUM_PLAYER_STATE.PAUSED
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.currentState = ENUM_PLAYER_STATE.STOPPED
            
        self.UpdatePlayerState(self.currentState)
        
    def MediaStatusChanged(self, mediaState):
        print("[Player State] -- ", self.currentState.name)
        print("[Media Status] -- ", mediaState.name)
        
        #if self.currentState == ENUM_PLAYER_STATE.PLAYING or self.currentState == ENUM_PLAYER_STATE.LOADING or self.currentState == ENUM_PLAYER_STATE.IDLE:
        if self.currentState == ENUM_PLAYER_STATE.PAUSED:
            return
            
        if mediaState == QMediaPlayer.MediaStatus.BufferingMedia and self.duration == 0:
            #if self.currentState != ENUM_PLAYER_STATE.PAUSED:
            self.currentState = ENUM_PLAYER_STATE.LOADING
        elif mediaState == QMediaPlayer.MediaStatus.LoadingMedia:
            #if self.currentState != ENUM_PLAYER_STATE.PAUSED:
            self.currentState = ENUM_PLAYER_STATE.LOADING
        elif mediaState == QMediaPlayer.MediaStatus.BufferedMedia:
            self.currentState = ENUM_PLAYER_STATE.PLAYING
            
            # Get Subtitle info
            subtitle_tracks = self.player.subtitleTracks()
            if len(subtitle_tracks) != self.subtitleCount:
                self.subtitleCount = len(subtitle_tracks)
                if len(subtitle_tracks) > 0:  
                    self.mainWindow.subtitlesEnabled = True               
                    self.subtitleList = [(-1, "Disabled")]
                    for index, track in enumerate(subtitle_tracks):
                        language = track.value(QMediaMetaData.Key.Language)
                        if not language:  # Fallback if no language is specified
                            language = f"Track {index + 1}"
                        self.subtitleList.append((index, str(language)))
                else:
                    self.mainWindow.subtitlesEnabled = False
                    
        elif mediaState == QMediaPlayer.MediaStatus.LoadedMedia:
            if self.currentState == ENUM_PLAYER_STATE.PLAYING:
                self.currentState = ENUM_PLAYER_STATE.PLAYING
        elif mediaState == QMediaPlayer.MediaStatus.InvalidMedia:
            self.currentState = ENUM_PLAYER_STATE.STALLED
        elif mediaState == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.duration > 0:
                self.currentState = ENUM_PLAYER_STATE.ENDED
            else:
                self.currentState = ENUM_PLAYER_STATE.STALLED #ENUM_PLAYER_STATE.STOPPED
        elif mediaState == QMediaPlayer.MediaStatus.NoMedia:
            self.currentState = ENUM_PLAYER_STATE.IDLE
        elif mediaState == QMediaPlayer.MediaStatus.StalledMedia:
            self.currentState = ENUM_PLAYER_STATE.STALLED
            
        self.UpdatePlayerState(self.currentState)
        
    def GetSubtitleTracks(self):
        return self.subtitleList
    
    def SetSubtitleTrack(self, index):
        self.subtitleIndex = index
        self.player.setActiveSubtitleTrack(index) 
        
    def GetVideoResolution(self):
        # Get resolution from metadata
        metadata = self.player.metaData()
        resolution = metadata.value(QMediaMetaData.Key.Resolution)
        if isinstance(resolution, QSize) and resolution.isValid():
            res_str = f"{resolution.width()}x{resolution.height()}"
        else:
            res_str = "Unknown"
            
        return res_str