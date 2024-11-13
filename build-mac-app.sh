#!/bin/bash

# Set variables
APP_NAME="SpyderPlayer"
EXECUTABLE_PATH="./dist/SpyderPlayer"  
ICON_PATH="./assets/icons/spider_dark_icon.icns"
APP_BUNDLE_PATH="./dist/${APP_NAME}.app"

# Create app bundle structure
mkdir -p "${APP_BUNDLE_PATH}/Contents/"{MacOS,Resources}

# Create Info.plist
cat > "${APP_BUNDLE_PATH}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>spider_dark_icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.fredrodriguez.spyderplayer</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Copy executable
cp "$EXECUTABLE_PATH" "${APP_BUNDLE_PATH}/Contents/MacOS/${APP_NAME}"

# Copy icon if it exists
if [ -f "$ICON_PATH" ]; then
    cp "$ICON_PATH" "${APP_BUNDLE_PATH}/Contents/Resources/"
fi

# Make app bundle executable
chmod +x "${APP_BUNDLE_PATH}/Contents/MacOS/${APP_NAME}"

echo "App bundle created at ${APP_BUNDLE_PATH}"