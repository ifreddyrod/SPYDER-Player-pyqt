SPYDER Player is an easy to use cross-platform media player with a focus on making streaming IPTV channels easier.  Managing playlists from various sources can be cumbersome.  SPYDER Player makes it easy to load, create, and mangage your playlists.

SPYDER Player allows you to load multiple m3u files locally or remotely.  You can easily add and remove channels to your Favorites list by clicking on the star next to the channel.  You can also load local media files.  All playlists can be searched.

The code for this is written in python with Qt and it utilizes 2 media libraries (VLC and QMediaPlayer).  The VLC player is compatible with many media types and can display streamed videos in 4k.  The QMediaPlayer has less media compatiblity, but may perform better on your system.  Either can be selected in the settings.  

Main Window:
<img width="1199" alt="Screenshot 2024-11-15 at 5 59 08 AM" src="https://github.com/user-attachments/assets/990a0407-d298-4071-99a5-acc2cbfb8e41">



Settings Windows:
<img width="782" alt="Screenshot 2024-11-15 at 6 01 17 AM" src="https://github.com/user-attachments/assets/88afc261-89b5-486d-87a0-745055a5c9b7">


Build Requirements:
- `pip install pyqt6`
- `pip install m3u-parser`
- linux:  `pip install dbus-python`
- `pip install pydantic`
- `pip install pyqt6rc` Converts design ui to py - pyuic6
- `pip install python-vlc`
- Install VLC Player (I used version 3.0.14)  https://www.videolan.org/
- `pip install pyinstaller` If you want to build the application as an executable

Build Instructions:
- If you add any new images to the resources.qrc file, you will need to convert them to a py file: `make resources`
- If you make changes to any of the ui files, you will need to convert them to py files: `make ui`
- To build the application library on MacOS: `make build-mac`
- To build the executable on Windows: `make build-win`

ToDo:
- More testing and bug finding
- Create Installers for all Operating Systems
- Release first version
