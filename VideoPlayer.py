import vlc
import re, os
import platform
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget


class VideoPlayer(QWidget):
    platform: str = platform.system()
    updatePosition = pyqtSignal(int)
    playerStateChanged = pyqtSignal(vlc.State)
    errorOccured = pyqtSignal(str)
    
    def __init__(self, videoPanel: QWidget, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.videoPanel = videoPanel    
        
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(250)
        self.updateTimer.timeout.connect(self.UpdatePlayerStatus)
        
        # Get the video widget's window handle
        if self.platform.startswith('Linux'): 
            self.instance = vlc.Instance("--avcodec-hw=vaapi")
            self.player = self.instance.media_player_new()
            self.player.set_xwindow(int(self.videoPanel.winId()))
        elif self.platform.startswith('Windows'): 
            self.instance = vlc.Instance("--avcodec-hw=dxva2")  #d3d11va
            self.player = self.instance.media_player_new()
            self.player.set_hwnd(int(self.videoPanel.winId()))
        elif self.platform.startswith('Darwin'):
            self.instance = vlc.Instance("--avcodec-hw=videotoolbox")
            self.player = self.instance.media_player_new()
            self.player.set_nsobject(int(self.videoPanel.winId()))   
            
          
        self.source = ""
        self.duration = 0
        self.position = 0
        self.currentState = vlc.State.Stopped
        self.previousState = vlc.State.NothingSpecial
        self.Mute(False) 
           
    def SetVideoSource(self, videoSource: str):     
        self.source = videoSource
        self.player.set_media(self.instance.media_new(self.source))
        
    def Play(self):
        self.previousState = vlc.State.NothingSpecial
        
        try:
            self.player.play()
            self.updateTimer.start()
        except Exception as e:
            self.updateTimer.stop()
            self.errorOccured.emit(str(e))
            
        self.EmitCurrentPlayerState()
        
        
    def Pause(self):
        try:
            self.player.pause()
        except Exception as e:
            self.errorOccured.emit(str(e))
            
        self.updateTimer.stop()
        self.EmitCurrentPlayerState()
        
    def Stop(self):
        try:
            self.player.stop()
        except Exception as e:
            self.errorOccured.emit(str(e))
            
        self.updateTimer.stop()
        self.EmitCurrentPlayerState()
        
    def SetPosition(self, position: int):
        self.player.set_time(position)
        self.position = position
        
    def GetPosition(self):
        self.position = self.player.get_time()
        return self.position
    
    def GetVideoDuration(self):
        self.duration = self.player.get_length()
        return self.duration
    
    def SetVolume(self, volume: int):
        self.player.audio_set_volume(volume)
        
    def GetVolume(self):
        return self.player.audio_get_volume()
        
    def ToggleMute(self):
        self.player.audio_set_mute(not self.IsMuted())
        
    def IsMuted(self):
        return self.player.audio_get_mute()
    
    def Mute(self, mute: bool):
        self.player.audio_set_mute(mute)
    
    def GetPlayerState(self):
        self.currentState = self.player.get_state()
        return self.currentState

    def EmitCurrentPlayerState(self):
        self.currentState = self.GetPlayerState()
        self.playerStateChanged.emit(self.currentState)
    
    def UpdatePlayerStatus(self):
        state = self.GetPlayerState()
        
        if state == vlc.State.Playing:
            videoTimePosition = self.GetPosition()
            duration = self.GetVideoDuration()
            
            if duration > 0:
                self.updatePosition.emit(videoTimePosition)
        elif state == vlc.State.Ended:
            self.updatePosition.emit(self.duration)
            self.updateTimer.stop()        
        elif state == vlc.State.Error:
            self.updateTimer.stop()
            self.errorOccured.emit(str(self.player.get_error()))
        elif state == vlc.State.Stopped or state == vlc.State.Paused:
            self.updateTimer.stop()
        
        if self.currentState != self.previousState:
            self.playerStateChanged.emit(self.currentState)
            self.previousState = self.currentState
        