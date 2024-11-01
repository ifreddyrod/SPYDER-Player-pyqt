import platform
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget
import vlc

from enum import Enum
from abc import abstractmethod

class ENUM_PLAYER_TYPE(Enum):
    VLC = 0
    QTMEDIA = 1 

#------------------------------------------------
# Video Player Base Class
#------------------------------------------------
class VideoPlayer(QWidget):
    platform: str = platform.system()
    updatePosition = pyqtSignal(int)
    updateDuration = pyqtSignal(int)
    playerStateChanged = pyqtSignal(vlc.State)
    errorOccured = pyqtSignal(str)
    mainWindow: QWidget = None
    videoPanel: QWidget = None
    source: str = ""
    duration: int = 0
    position: int = 0
    
    #-----------------------
    # Signal Methods
    #-----------------------
    def UpdatePosition(self, position: int):
        self.position = position
        self.updatePosition.emit(position)
    
    def UpdateDuration(self, duration: int):
        self.duration = duration
        self.updateDuration.emit(duration)
        
    def UpdatePlayerState(self, state: vlc.State):
        self.playerStateChanged.emit(state)
    
    def ErrorOccured(self, error: str):
        self.errorOccured.emit(error)
        
    #-----------------------
    # Abstract Methods
    #-----------------------
    @abstractmethod
    def InitPlayer(self):
        pass
    
    @abstractmethod
    def Play(self):
        pass
    
    @abstractmethod
    def Pause(self):
        pass
    
    @abstractmethod
    def Stop(self):
        pass
    
    @abstractmethod
    def SetPosition(self, position: int):
        pass
    
    @abstractmethod
    def GetPosition(self):
        pass
        
    @abstractmethod
    def SetVolume(self, volume: int):
        pass
    
    @abstractmethod
    def GetVolume(self):
        pass
    
    @abstractmethod
    def Mute(self, mute: bool):
        pass
    
    @abstractmethod
    def IsMuted(self):
        pass
    
    @abstractmethod
    def SetVideoSource(self, videoSource: str):
        pass
    
    @abstractmethod
    def RefreshVideoSource(self):
        pass
    
    @abstractmethod
    def GetVideoDuration(self):
        pass
    