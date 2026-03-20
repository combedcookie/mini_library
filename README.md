📚 Mini Library
Mini Library is a fast, local desktop utility designed to help 3D printing enthusiasts organize, index, and inspect their miniature files (STL, OBJ, 3MF).

Built with Python, PySide6, and trimesh, it bridges the gap between a cluttered downloads folder and a perfectly curated 3D model library—without relying on external servers or heavy background processing.

✨ Features
Interactive 3D Preview: Inspect your models directly within the app. Select a file and launch the built-in 3D viewer to rotate, pan, and zoom the actual mesh in real-time.

Smart Organization: Automatically process your Downloads folder. The app can extract ZIP files, ignore temp/partial downloads, move or copy valid 3D models into your main Library, and clean up empty folders behind itself.

Instant Search: Uses a lightweight local SQLite database to quickly query your library by filename, path, or extension.

Slicer Integration: Launch your selected model directly into your preferred slicing software (e.g., Lychee, Chitubox, PrusaSlicer) with a single click.

Customizable UI: Switch between Dark and Light themes and select custom accent colors to match your desktop environment.

🚀 Installation & Running
Mini Library is packaged as a portable AppImage, making it incredibly easy to run on almost any Linux distribution without installing dependencies.

Option 1: Using the AppImage (Recommended for Linux)
Download the latest MiniLibrary-x86_64.AppImage release.

Make the file executable. You can do this by right-clicking the file -> Properties -> Permissions -> "Allow executing file as program", or via the terminal:

Bash
chmod +x MiniLibrary-x86_64.AppImage
Double-click the AppImage to run it, or execute it from the terminal:

Bash
./MiniLibrary-x86_64.AppImage
Option 2: Running from Source
If you prefer to run the app directly from the Python script:

Clone or download this repository.

Install the required dependencies (Python 3.8+ recommended):

Bash
pip install PySide6 trimesh
Run the application:

Bash
python mini_library_app.py
📖 Quick Start Guide
Configure Paths: When you first open the app, look at the Paths section on the right. Point the app to your Downloads folder, your Library folder, your Database file, and the executable path for your Slicer.

Apply Paths: Click the Apply Paths button to lock in your settings.

Organize: Click Run Organizer to scan your Downloads folder, extract archives, and move/copy your 3D files into your Library.

Index: Click Rebuild Index to scan your Library and build the local search database.

Search & View: Type a keyword into the search bar. Select a file from the results and click Open Interactive 3D Viewer to inspect the 3D mesh!

🐧 Desktop Integration (Linux)
To make the AppImage appear in your system's application menu like a natively installed app, you can use a tool like AppImageLauncher, or manually create a .desktop file in ~/.local/share/applications/.
