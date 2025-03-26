@echo off

REM 1. Upgrade pip and install pip-tools
python.exe -m pip install --upgrade pip
pip install pyinstaller pip-tools

REM 2. Compile dependencies from requirements.in -> requirements.txt (with hashes)
pip-compile --generate-hashes --strip-extras --no-emit-find-links requirements.in

REM 3. Install the pinned dependencies
pip install -r requirements.txt

REM 4. Check if UPX is available at c:\dev\upx\upx.exe
IF EXIST "c:\dev\upx\upx.exe" (
    echo "UPX found. Enabling UPX compression..."
    SET "UPX_FLAG=--upx-dir c:\dev\upx"
) ELSE (
    echo "UPX not found. Skipping UPX compression..."
    SET "UPX_FLAG="
)

REM 5. Build the executable with PyInstaller
echo Building with default PyInstaller flags...
call pyinstaller --onefile --noconsole --strip --clean ^
            %UPX_FLAG% ^
            --name OCIConnectionManager ^
            --add-data "resources;resources" ^
            --icon "resources/green_icon.ico" ^
            main.py

REM 6. Remove the build folder if it exists
IF EXIST build (
    echo "Removing build folder..."
    call rmdir /s /q build
) ELSE (
    echo "build folder not found. Skipping removal..."
)