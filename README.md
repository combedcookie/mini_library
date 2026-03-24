📚 Mini Library
Mini Library is a fast, local desktop utility designed to help 3D printing enthusiasts organize, index, and inspect their miniature files (.stl, .obj, .3mf).
Built with Python, PySide6, and trimesh, it bridges the gap between a cluttered downloads folder and a curated 3D model library—without relying on external servers or cloud services.
✨ Features
Interactive 3D Preview
Inspect your models directly within the app. Select a file and launch the built-in 3D viewer to rotate, pan, and zoom the mesh in real time.
Smart Organization
Automatically process your Downloads folder. Mini Library can extract ZIP files, ignore temp and partial downloads, move or copy valid 3D models into your main Library, and clean up empty folders afterward.
Instant Search
Uses a lightweight local SQLite database to quickly search your library by filename, path, or extension.
Slicer Integration
Launch your selected model directly into your preferred slicer, such as Lychee, Chitubox, or PrusaSlicer, with a single click.
Customizable UI
Switch between Dark and Light themes and choose custom accent colors to match your desktop setup.
🚀 Installation & Running
Mini Library is available as both a Linux AppImage and a Windows .exe.
Option 1: Linux AppImage
Download the latest MiniLibrary-x86_64.AppImage release.
Make the file executable:
Bash
chmod +x MiniLibrary-x86_64.AppImage
Run it:
Bash
./MiniLibrary-x86_64.AppImage
You can also double-click it from your file manager after enabling executable permissions.
Option 2: Windows .exe
Download the latest Windows release.
Extract the ZIP if needed, then open the MiniLibrary folder and run:
Plain text
MiniLibrary.exe
No Python installation is required for the packaged Windows release.
Option 3: Run from Source
If you want to run the app directly from source instead of a packaged build:
Clone or download this repository.
Install the required dependencies:
Bash
pip install PySide6 trimesh matplotlib numpy pillow "pyglet<2"
Run the application:
Bash
python mini_library_app.py
📖 Quick Start Guide
1. Configure Paths
When you first open the app, use the Paths section to point Mini Library to your:
Downloads folder
Library folder
Database file
Log file
Slicer executable
2. Apply Paths
Click Apply Paths to save your settings.
3. Organize
Click Run Organizer to scan your Downloads folder, extract archives, and move or copy your 3D files into your Library.
4. Index
Click Rebuild Index to scan your Library and build the local search database.
5. Search and View
Type a keyword into the search bar, press Enter or click Search, then select a file from the results.
6. Inspect and Launch
Use the built-in viewer to inspect the model, or launch it directly in your slicer.
🐧 Linux Desktop Integration
To make the AppImage appear in your system application menu like a native app, you can use AppImageLauncher or manually create a .desktop file in:
Bash
~/.local/share/applications/
🪟 Windows Notes
On Windows, Mini Library is distributed as a packaged .exe build.
That means:
no separate Python install is required for the release build
the app runs locally on your machine
your STL library, previews, and database stay on your system
🔒 Local-First Design
Mini Library is designed to stay local.
Your files are:
not uploaded
not synced to a server
not processed in the cloud
Everything happens on your own machine.
🛠 Built With
Python
PySide6
trimesh
SQLite
