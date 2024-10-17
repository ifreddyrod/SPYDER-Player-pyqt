from pydantic import BaseModel, PrivateAttr
from typing import List, Literal
import json

    
class PlayListEntry(BaseModel):
    name: str
    parentName: str
    sourceType: Literal["file", "url"]
    source: str
        
class HotKeys(BaseModel):
    playpause: str
    playpauseAlt: str
    toggleFullscreen: str
    escapeFullscreen: str
    togglePlaylist: str
    volumeMute: str
    volumeUp: str
    volumeDown: str
    seekForward: str
    seekBackward: str
    gotoTopofList: str
    gotoBottomofList: str
    collapseAllLists: str
    sortListAscending: str
    sortListDescending: str
    gotoLast: str        
        
class AppData(BaseModel):
    HotKeys: HotKeys
    Library: List[PlayListEntry] 
    Favorites: List[PlayListEntry]
    PlayLists: List[PlayListEntry] 
    
    # Private attribute to store file path
    _dataFile: str = PrivateAttr()

    def __init__(self, **data):
        dataFilePath = data.pop('dataFilePath', "")
        super().__init__(**data)
        self._dataFile = dataFilePath

    @classmethod
    def load(cls, file_path: str) -> "AppData":
        """Loads data from a JSON file into an AppData instance."""
        with open(file_path, "r") as file:
            data = json.load(file)
        return cls(dataFilePath=file_path, **data)

    def save(self):
        """Saves the current AppData instance to a JSON file, excluding the _dataFile."""
        data_to_save = self.dict()  # Get the Pydantic model data
        with open(self._dataFile, "w") as file:
            json.dump(data_to_save, file, indent=4)
        
        