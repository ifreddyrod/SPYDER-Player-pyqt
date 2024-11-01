import vlc
import re, os
import platform
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QApplication
from VideoPlayer import VideoPlayer

class VLCPlayer(VideoPlayer):
    def __init__(self, mainWindow: QWidget, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.mainWindow = mainWindow
        self.videoPanel = self.mainWindow.videoPanel  
        
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(100)
        self.updateTimer.timeout.connect(self.UpdatePlayerStatus)
        
        self.InitPlayer()
        
        # Register events
        '''self.eventManager = self.player.event_manager()
        #print(dir(vlc.EventType))
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.OnPositionChanged)
        self.eventManager.event_attach(vlc.EventType.MediaStateChanged, self.OnPlayerStateChanged)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.OnErrorOccured)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.OnPlayerLengthChanged)'''
        
        self.source = ""
        self.duration = 0
        self.position = 0
        self.currentState = vlc.State.Stopped
        self.previousState = vlc.State.NothingSpecial
        self.Mute(False) 
           
    def InitPlayer(self):
        # Get the video widget's window handle
        if self.platform.startswith('Linux'): 
            self.instance = vlc.Instance("--avcodec-hw=vaapi")
            self.player = self.instance.media_player_new()
            self.player.set_xwindow(int(self.videoPanel.winId()))
        elif self.platform.startswith('Windows'): 
            self.instance = vlc.Instance("--avcodec-hw=d3d11va")  #d3d11va #dxva2
            self.player = self.instance.media_player_new()
            self.player.set_hwnd(int(self.videoPanel.winId()))
        elif self.platform.startswith('Darwin'):
            self.instance = vlc.Instance("--avcodec-hw=videotoolbox")
            self.player = self.instance.media_player_new()
            self.player.set_nsobject(int(self.videoPanel.winId()))           
        
               
    def SetVideoSource(self, videoSource: str):    
        self.source = videoSource
        self.player.set_media(self.instance.media_new(self.source))
        
    def RefreshVideoSource(self):
        self.player.set_media(self.instance.media_new(""))
        self.player.set_media(self.instance.media_new(self.source))
        
    def Play(self):
        self.previousState = vlc.State.NothingSpecial
        
        try:
            self.player.play()
            self.updateTimer.start()
        except Exception as e:
            self.updateTimer.stop()
            self.ErrorOccured(str(e))
            
        self.EmitCurrentPlayerState()
        
        
    def Pause(self):
        try:
            self.player.pause()
        except Exception as e:
            self.ErrorOccured(str(e))
            
        self.updateTimer.stop()
        self.EmitCurrentPlayerState()
        
    def Stop(self):
        try:
            self.player.stop()
        except Exception as e:
            self.ErrorOccured(str(e))
            
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
        self.UpdatePlayerState(self.currentState)
    
    def UpdatePlayerStatus(self):
        state = self.GetPlayerState()
        
        if state == vlc.State.Playing:
            videoTimePosition = self.GetPosition()
            duration = self.GetVideoDuration()
            
            if duration > 0:
                self.UpdatePosition(videoTimePosition)
        elif state == vlc.State.Ended:
            self.UpdatePosition(self.duration)
            self.updateTimer.stop()        
        elif state == vlc.State.Error:
            self.updateTimer.stop()
            self.ErrorOccured(str(self.player.get_error()))
        elif state == vlc.State.Stopped or state == vlc.State.Paused:
            self.updateTimer.stop()
        
        if self.currentState != self.previousState:
            self.UpdatePlayerState(self.currentState)
            self.previousState = self.currentState
        
    def UserActivity(self, event):
        self.mainWindow.ActivateControlPanel()
        self.mainWindow.event(event)
    
    def OnPositionChanged(self, event):
        self.position = self.GetPosition()
        self.UpdatePosition(self.position)
        
    def OnPlayerStateChanged(self, event):
        self.currentState = self.GetPlayerState()
        if self.currentState != self.previousState:
            self.previousState = self.currentState
            self.UpdatePlayerState(self.currentState)           
        
    def OnErrorOccured(self, event):
        self.ErrorOccured(str(self.player.get_error()))
        
    def OnPlayerLengthChanged(self, event):
        self.duration = self.GetVideoDuration()
        self.UpdatePosition(self.duration)
        
    '''def event(self, event):
        QApplication.sendEvent(self.mainWindow, event)
        return True'''

        