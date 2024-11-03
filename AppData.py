from pydantic import BaseModel, ValidationError, Field
from pydantic.fields import PrivateAttr
from typing import List, Literal
import json
import os
from VideoPlayer import ENUM_PLAYER_TYPE
    
class PlayListEntry(BaseModel):
    name: str
    parentName: str
    sourceType: Literal["file", "url"]
    source: str

class AppHotKeys(BaseModel):
    playpause: str = "k"
    playpauseAlt: str = "space"
    toggleFullscreen: str = "f"
    escapeFullscreen: str = "esc"
    togglePlaylist: str = "l"
    volumeMute: str = "m"
    volumeUp: str = "up"
    volumeDown: str = "down"
    seekForward: str = "right"
    seekBackward: str = "left"
    gotoTopofList: str = "t"
    gotoBottomofList: str = "b"
    collapseAllLists: str = "c"
    sortListAscending: str = "a"
    sortListDescending: str = "d"
    gotoLast: str = "backspace"
    showOptions: str = "o"

class AppData(BaseModel):
    PlayerType: ENUM_PLAYER_TYPE = ENUM_PLAYER_TYPE.VLC
    HotKeys: AppHotKeys = AppHotKeys()
    Library: List[PlayListEntry] = []
    Favorites: List[PlayListEntry] = []
    PlayLists: List[PlayListEntry] = []
    
    _dataFile: str = PrivateAttr()
        
    def __init__(self, **data):
        dataFilePath = data.pop('dataFilePath', "")
        super().__init__(**data)
        self._dataFile = dataFilePath

    @classmethod
    def load(cls, file_path: str) -> "AppData":
        """Loads data from a JSON file into an AppData instance. If file doesn't exist, creates one with default values."""
        if not os.path.exists(file_path):
            # Create file with default data
            default_data = cls(dataFilePath=file_path)
            default_data.save()
            return default_data

        try:
            with open(file_path, "r") as file:
                data = json.load(file)
            # Convert the string to enum if needed
            if 'PlayerType' in data and isinstance(data['PlayerType'], str):
                data['PlayerType'] = ENUM_PLAYER_TYPE(data['PlayerType'])
            return cls(dataFilePath=file_path, **data)
        
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Error loading config: {e}. Using default configuration.")
            default_data = cls(dataFilePath=file_path)
            default_data.save()
            return default_data

    def save(self):
        """Saves the current AppData instance to a JSON file."""
        data_to_save = self.dict()  # Get the Pydantic model data
        # Convert enum to string name for JSON serialization
        if 'PlayerType' in data_to_save:
            data_to_save['PlayerType'] = self.PlayerType.name
        with open(self._dataFile, "w") as file:
            json.dump(data_to_save, file, indent=4)
