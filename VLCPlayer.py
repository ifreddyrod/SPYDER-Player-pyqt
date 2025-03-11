import vlc
import re, os
import platform
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QApplication
from VideoPlayer import *

class VLCPlayer(VideoPlayer):
    def __init__(self, mainWindow: QWidget, parent=None):
        super(VideoPlayer, self).__init__(parent)
        self.mainWindow = mainWindow
        #self.videoPanel = self.mainWindow.videoPanel
        #self.mainWindow.ui.gridLayout.removeWidget(self.mainWindow.videoPanel)
        self.videoPanel = QWidget(self.mainWindow.videoPanel) 
             
        self.mainWindow.ui.gridLayout.addWidget(self.videoPanel, 1, 1, 1, 1)
        self.mainWindow.videoPanel = self.videoPanel
            
        self.updateTimer = QTimer()
        self.updateTimer.setInterval(250)
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
        self.subtitleCount = -1
        self.subtitleList = [] # List of tuples [(-1, b'Disable'), (2, b'English-SRT - [English]'), (3, b'Track 2'), (4, b'Track 3'), (5, b'Track 4'), (6, b'Track 5')]
        self.subtitleIndex = -1
           
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
        self.subtitleCount =  -1
        self.subtitleList = []
        self.subtitleIndex = -1
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
            self.UpdatePosition(0)
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
        self.currentState = self.TranslateState(self.player.get_state())
        return self.currentState
    
    def TranslateState(self, state: vlc.State) -> ENUM_PLAYER_STATE:
        playerState = ENUM_PLAYER_STATE.IDLE
        #print("VLC State: " + str(state))
        
        if state == vlc.State.NothingSpecial:
            playerState = ENUM_PLAYER_STATE.IDLE
        elif state == vlc.State.Opening:
            playerState = ENUM_PLAYER_STATE.LOADING
        elif state == vlc.State.Buffering:
            playerState = ENUM_PLAYER_STATE.LOADING
        elif state == vlc.State.Paused:
            playerState = ENUM_PLAYER_STATE.PAUSED
        elif state == vlc.State.Playing:
            playerState = ENUM_PLAYER_STATE.PLAYING
        elif state == vlc.State.Stopped:
            playerState = ENUM_PLAYER_STATE.STOPPED
        elif state == vlc.State.Ended:
            if self.duration > 0:
                playerState = ENUM_PLAYER_STATE.ENDED
                self.UpdatePosition(self.duration)
            else:
                playerState = ENUM_PLAYER_STATE.STALLED
        elif state == vlc.State.Error:
            playerState = ENUM_PLAYER_STATE.ERROR
            
        return playerState
        

    def EmitCurrentPlayerState(self):
        self.currentState = self.TranslateState(self.GetPlayerState())
        self.UpdatePlayerState(self.currentState)
    
    def UpdatePlayerStatus(self):
        state = self.GetPlayerState()
        #print("Update Player State: " + str(state)) 
           
        if state == ENUM_PLAYER_STATE.PLAYING:
            videoTimePosition = self.GetPosition()
            duration = self.GetVideoDuration()
            #print("Duration: " + str(duration) + " Position: " + str(videoTimePosition))
            
            if duration > 0:
                self.UpdatePosition(videoTimePosition)
                
            subtitleCount = self.player.video_get_spu_count()
            if self.subtitleCount != subtitleCount:
                self.subtitleCount = subtitleCount
                subtitleList = self.player.video_get_spu_description()
                
                print("Subtitle Count: " + str(subtitleCount))
                self.subtitleList.clear()
                for index, description in subtitleList:
                    # Create track list as strings not utf-8 encoding
                    if isinstance(description, bytes):
                        try:
                            description = description.decode('utf-8')
                        except UnicodeDecodeError:
                            description = description.decode('latin-1')  # fallback encoding
                    
                    self.subtitleList.append((index, description))
                
                if subtitleCount > 0:
                    self.mainWindow.subtitlesEnabled = True
                    self.player.video_set_spu(self.subtitleIndex)
                else:
                    self.mainWindow.subtitlesEnabled = False
                
        elif state == ENUM_PLAYER_STATE.STALLED:
            #self.UpdatePosition(self.duration)
            self.updateTimer.stop()        
        elif state == ENUM_PLAYER_STATE.ERROR:
            self.updateTimer.stop()
            self.ErrorOccured(str(self.player.get_error()))
        elif state == ENUM_PLAYER_STATE.STOPPED or state == ENUM_PLAYER_STATE.PAUSED:
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
        self.currentState = ENUM_PLAYER_STATE.ERROR
        self.UpdatePlayerState(self.currentState)
        self.ErrorOccured(str(self.player.get_error()))
        
    def OnPlayerLengthChanged(self, event):
        self.duration = self.GetVideoDuration()
        self.UpdatePosition(self.duration)
        
    def OnChangingPosition(self, isPlaying):
        if isPlaying:
            self.player.pause()
            
    def OnChangedPosition(self, isPlaying):
        if isPlaying:
            self.player.play()
            self.previousState = ENUM_PLAYER_STATE.PAUSED
            self.currentState = ENUM_PLAYER_STATE.PLAYING
            #self.UpdatePlayerState(self.currentState)
            self.updateTimer.start()
            
    def ChangeUpdateTimerInterval(self, isFullScreen: bool):
        if isFullScreen:
            self.updateTimer.setInterval(1000)
        else:
            self.updateTimer.setInterval(250)
            
    def GetSubtitleTracks(self):
        return self.subtitleList
        
    def SetSubtitleTrack(self, index):
        self.subtitleIndex = index
        self.player.video_set_spu(index)
        
    def GetVideoResolution(self):        
        media = self.player.get_media()
        res_str = "Unknown"
        
        if media:
            # Parse media to get stats
            media.parse_with_options(1, 0)
            
            # Parse media if not already parsed
            if media.get_parsed_status() != vlc.MediaParsedStatus.done:
                media.parse_with_options(vlc.MediaParseFlag.network, 0)
                        
            highest_resolution = (0, 0)
            highest_resolution_index = -1        
            trackCnt = self.player.video_get_track_count()  
            print("Track Count: " + str(trackCnt))              

            # Get track resolutions
            for i in range(trackCnt+1):
                width, height = self.player.video_get_size(i)
                if width > 0 and height > 0:
                    res_str = f"{width}x{height}"
                    print("Track " + str(i) + " Resolution: " + res_str)
                    if width * height > highest_resolution[0] * highest_resolution[1]:
                            highest_resolution = (width, height)
                            highest_resolution_index = i        
            
            if highest_resolution_index >= 0:
                res_str = f"{highest_resolution[0]}x{highest_resolution[1]}"
                       
        return res_str
    