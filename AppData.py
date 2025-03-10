from pydantic import BaseModel, ValidationError, Field, root_validator
from pydantic.fields import PrivateAttr
from typing import List, Literal, Dict, Any
import json
import os
from VideoPlayer import ENUM_PLAYER_TYPE
from PyQt6.QtCore import Qt

class PlayListEntry(BaseModel):
    name: str
    parentName: str
    sourceType: Literal["file", "url"]
    source: str

    @classmethod
    def validate_and_create(cls, data: Dict[str, Any]) -> 'PlayListEntry':
        try:
            return cls(**data)
        except ValidationError:
            return None

class AppHotKeys(BaseModel):
    playpause: int = Qt.Key.Key_K
    playpauseAlt: int = Qt.Key.Key_Space
    toggleFullscreen: int = Qt.Key.Key_F
    escapeFullscreen: int = Qt.Key.Key_Escape
    togglePlaylist: int = Qt.Key.Key_L
    volumeMute: int = Qt.Key.Key_M
    volumeUp: int = Qt.Key.Key_Up
    volumeDown: int = Qt.Key.Key_Down
    seekForward: int = Qt.Key.Key_Right
    seekBackward: int = Qt.Key.Key_Left
    gotoTopofList: int = Qt.Key.Key_T
    gotoBottomofList: int = Qt.Key.Key_B
    collapseAllLists: int = Qt.Key.Key_C
    sortListAscending: int = Qt.Key.Key_A
    sortListDescending: int = Qt.Key.Key_D
    gotoLast: int = Qt.Key.Key_Backspace
    showOptions: int = Qt.Key.Key_O
    playNext: int = Qt.Key.Key_Period
    playPrevious: int = Qt.Key.Key_Comma
    stopVideo: int = Qt.Key.Key_S

    @classmethod
    def validate_and_create(cls, data: Dict[str, Any]) -> 'AppHotKeys':
        """Creates an AppHotKeys instance, falling back to defaults for invalid fields."""
        if not isinstance(data, dict):
            return cls()

        valid_data = {}
        default_instance = cls()

        for field_name, field in cls.__fields__.items():
            try:
                # Try to use the provided value
                if field_name in data:
                    field_value = data[field_name]
                    # Verify the value is an integer
                    if isinstance(field_value, int):
                        valid_data[field_name] = field_value
                    else:
                        valid_data[field_name] = getattr(default_instance, field_name)
                else:
                    valid_data[field_name] = getattr(default_instance, field_name)
            except (ValueError, TypeError):
                # Use default value if validation fails
                valid_data[field_name] = getattr(default_instance, field_name)

        return cls(**valid_data)

class AppData(BaseModel):
    PlayerType: ENUM_PLAYER_TYPE = ENUM_PLAYER_TYPE.VLC
    PlayListPath: str = ""
    HotKeys: AppHotKeys = Field(default_factory=AppHotKeys)
    Library: List[PlayListEntry] = Field(default_factory=list)
    Favorites: List[PlayListEntry] = Field(default_factory=list)
    PlayLists: List[PlayListEntry] = Field(default_factory=list)
    
    _dataFile: str = PrivateAttr()
        
    def __init__(self, **data):
        dataFilePath = data.pop('dataFilePath', "")
        # Pre-process the data before passing it to super().__init__
        processed_data = self._process_input_data(data)
        super().__init__(**processed_data)
        self._dataFile = dataFilePath

    def _process_input_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data to handle validation errors for each field."""
        processed = {}

        # Handle PlayerType
        try:
            if 'PlayerType' in data:
                if isinstance(data['PlayerType'], str):
                    processed['PlayerType'] = ENUM_PLAYER_TYPE(data['PlayerType'])
                else:
                    processed['PlayerType'] = data['PlayerType']
        except (ValueError, KeyError):
            processed['PlayerType'] = ENUM_PLAYER_TYPE.VLC
            
        # Handle PlayListPath    
        try: 
            if 'PlayListPath' in data:
                processed['PlayListPath'] = data['PlayListPath']
        except (ValueError, KeyError):
            processed['PlayListPath'] = ""

        # Handle HotKeys
        if 'HotKeys' in data:
            processed['HotKeys'] = AppHotKeys.validate_and_create(data['HotKeys'])
        else:
            processed['HotKeys'] = AppHotKeys()

        # Handle playlist arrays
        for field in ['Library', 'Favorites', 'PlayLists']:
            if field in data and isinstance(data[field], list):
                processed[field] = [
                    entry for entry in (
                        PlayListEntry.validate_and_create(item)
                        for item in data[field]
                    )
                    if entry is not None
                ]
            else:
                processed[field] = []

        return processed

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
            return cls(dataFilePath=file_path, **data)
        
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading config file: {e}. Using default configuration.")
            default_data = cls(dataFilePath=file_path)
            default_data.save()
            return default_data
        
        except Exception as e:
            print(f"Unexpected error: {e}. Using default configuration.")
            default_data = cls(dataFilePath=file_path)
            default_data.save()
            return default_data

    def save(self):
        """Saves the current AppData instance to a JSON file."""
        try:
            data_to_save = self.dict()  # Get the Pydantic model data
            # Convert enum to string name for JSON serialization
            if 'PlayerType' in data_to_save:
                data_to_save['PlayerType'] = self.PlayerType.name
            with open(self._dataFile, "w") as file:
                json.dump(data_to_save, file, indent=4)
                                
        except Exception as e:
            print(f"Error saving config file: {e}")



def SavePlayListToFile(playlist: List[PlayListEntry], filepath: str):
    """
    Save a list of PlayListEntry objects to an M3U playlist file.
    
    Args:
        playlist_entries: List of PlayListEntry objects containing track information
        filepath: Path where the M3U file should be saved
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        # Write M3U header
        f.write('#EXTM3U\n')
        
        for entry in playlist:
            # Write extended info tag with track name and parent name
            #f.write(f'#EXTINF:-1,{entry.name} - {entry.parentName}\n')
            f.write(f'#EXTINF:-1,{entry.name}\n')
            
            if entry.sourceType == "file":
                # Convert file path to use forward slashes for compatibility
                normalized_path = entry.source.replace('\\', '/')
                f.write(f'{normalized_path}\n')
            else:  # URL
                f.write(f'{entry.source}\n')    
    