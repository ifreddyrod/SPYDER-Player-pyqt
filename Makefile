# Define variables
UI_DIR := assets
RESOURCE_DIR := assets
IMAGE_DIR := assets/icons
BUILD_DIR := build
PYUIC6 := pyuic6
RCC := pyside6-rcc
PYINSTALLER := pyinstaller
MAIN_SCRIPT := SPYDERPlayerApp.py
EXE_NAME := SpyderPlayer
SPEC_NAME := SpyderPlayerVLC


# Convert .qrc resource files to .py and replace import statement
resources:
	@echo "Converting resource files..."
	$(RCC) $(RESOURCE_DIR)/resources.qrc -o resources_rc.py
	@echo "Replacing 'from PySide6 import QtCore' with 'from PyQt6 import QtCore'..."
	@sed -i.bak 's/from PySide6 import QtCore/from PyQt6 import QtCore/' resources_rc.py
	-rm -f resources_rc.py.bak

# Convert .ui files to .py
ui:
	@echo "Converting UI files..."
	@for ui_file in $(UI_DIR)/*.ui; do \
		base_name=$$(basename $$ui_file .ui); \
		$(PYUIC6) $$ui_file -o UI_$$base_name.py; \
	done

# Clean all build directories
clean:
	@echo "Cleaning build directories..."
	-rm -rf __pycache__ 
	-rm -rf build 
	-rm -rf dist	


# Build with the terminal enabled to view debug messages
build-debug: clean
	@echo "Building Debug project with PyInstaller..."
	$(PYINSTALLER) --name $(EXE_NAME) --onefile --icon=$(IMAGE_DIR)/spider_dark_icon.ico $(MAIN_SCRIPT) 

# Build with pyinstaller
build: clean
	@echo "Building project with PyInstaller..."
	$(PYINSTALLER) --name $(EXE_NAME) --onefile --noconsole --icon=$(IMAGE_DIR)/spider_dark_icon.ico $(MAIN_SCRIPT) 

build-vlc: clean
	@echo "Building project with PyInstaller..."
	$(PYINSTALLER) $(SPEC_NAME).spec

# Default target
all: resources ui build

.PHONY: resources ui clean build all
