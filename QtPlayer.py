import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PyQt6.QtMultimediaWidgets import QVideoWidget

from VideoPlayer import *


class QtPlayer(VideoPlayer):
    def __init__(self, mainWindow: QWidget, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.mainWindow = mainWindow
        
        # Create and add QVideoWidget to the main window
        self.videoPanel = QVideoWidget(self.mainWindow.videoPanel)
        self.mainWindow.ui.gridLayout.addWidget(self.videoPanel, 1, 1, 1, 1)
        
        self.InitPlayer()    
        
        # Init Signals
        self.player.durationChanged.connect(self.PlayerDurationChanged)
        self.player.positionChanged.connect(self.PlayerPositionChanged)
        self.player.playbackStateChanged.connect(self.PlaybackStateChanged)
        
        
    def InitPlayer(self):
        self.player = QMediaPlayer()
        self.audioOutput = QAudioOutput()
        self.player.setAudioOutput(self.audioOutput)
        self.player.setVideoOutput(self.videoPanel)
        
        
    def SetVideoSource(self, videoSource: str):  
        self.source = videoSource
        
    def RefreshVideoSource(self):
        self.player.setSource(QUrl(''))
        time.sleep(1)
        self.player.setSource(QUrl(self.source))
    
    def Play(self):
        try:
            self.RefreshVideoSource()
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
        
    def PlaybackStateChanged(self, state):
        mediaState = self.player.mediaStatus
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.currentState = ENUM_PLAYER_STATE.PLAYING
                       
            if mediaState == QMediaPlayer.MediaStatus.BufferedMedia:
                self.currentState = ENUM_PLAYER_STATE.LOADING
            elif mediaState == QMediaPlayer.MediaStatus.LoadingMedia:
                self.currentState = ENUM_PLAYER_STATE.LOADING
            elif mediaState == QMediaPlayer.MediaStatus.InvalidMedia:
                self.currentState = ENUM_PLAYER_STATE.STALLED
            elif mediaState == QMediaPlayer.MediaStatus.EndOfMedia:
                self.currentState = ENUM_PLAYER_STATE.STOPPED
            elif mediaState == QMediaPlayer.MediaStatus.NoMedia:
                self.currentState = ENUM_PLAYER_STATE.IDLE
            elif mediaState == QMediaPlayer.MediaStatus.StalledMedia:
                self.currentState = ENUM_PLAYER_STATE.STALLED
                         
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.currentState = ENUM_PLAYER_STATE.PAUSED
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.currentState = ENUM_PLAYER_STATE.STOPPED
            
        self.UpdatePlayerState(self.currentState)