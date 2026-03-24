import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSize
# Third-party imports
import trimesh
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QDialog,
    QScrollArea,
    QColorDialog,
    QComboBox,
)

# Local module imports
import mini_indexer
import downloads_organizer

# Configuration & Constants
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DOWNLOADS = Path.home() / "Downloads"
DEFAULT_LIBRARY = Path.home() / "MiniLibrary"
DEFAULT_DB = DEFAULT_LIBRARY / "mini_index.db"
DEFAULT_LOG = DEFAULT_LIBRARY / "organize_log.txt"
DEFAULT_SLICER = "/opt/LycheeSlicer/lycheeslicer"

DEFAULT_EXTS = ".stl,.3mf,.obj"


# --- Helper Functions ---

def human_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n or 0)
    for u in units:
        if f < 1024.0:
            return f"{f:.1f}{u}"
        f /= 1024.0
    return f"{f:.1f}PB"


def open_path(path_str: str) -> None:
    p = Path(path_str).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {p}")

    if sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", str(p)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    elif os.name == "nt":
        os.startfile(str(p))  # type: ignore[attr-defined]
    else:
        raise RuntimeError("Unsupported platform for opening paths")


# --- Stylesheets ---

def dark_stylesheet(accent: str) -> str:
    return f"""
    QWidget {{ background-color: #2b2b2b; color: #e8e8e8; font-size: 13px; }}
    QMainWindow {{ background-color: #2b2b2b; }}
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QTableWidget {{
        background-color: #232323; color: #f0f0f0; border: 1px solid #444; border-radius: 6px; padding: 4px;
    }}
    QPushButton {{
        background-color: #343434; color: #f5f5f5; border: 1px solid #555; border-radius: 6px; padding: 6px 10px;
    }}
    QPushButton:hover {{ border: 1px solid {accent}; background-color: #3b3b3b; }}
    QPushButton:pressed {{ background-color: {accent}; color: #111; }}
    QGroupBox {{ border: 1px solid #444; border-radius: 8px; margin-top: 10px; padding-top: 10px; font-weight: bold; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px 0 6px; }}
    QHeaderView::section {{ background-color: #333; color: #f0f0f0; border: 1px solid #444; padding: 4px; }}
    QTableWidget {{ gridline-color: #444; selection-background-color: {accent}; selection-color: #111; }}
    QMenuBar {{ background-color: #2b2b2b; color: #f0f0f0; }}
    QMenuBar::item:selected {{ background-color: #3a3a3a; }}
    QMenu {{ background-color: #2b2b2b; color: #f0f0f0; border: 1px solid #444; }}
    QMenu::item:selected {{ background-color: {accent}; color: #111; }}
    QCheckBox {{ spacing: 6px; }}
    """


def light_stylesheet(accent: str) -> str:
    return f"""
    QWidget {{ background-color: #f4f5f7; color: #1f2328; font-size: 13px; }}
    QMainWindow {{ background-color: #f4f5f7; }}
    QLabel {{ background: transparent; color: #1f2328; }}
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QTableWidget {{
        background-color: #ffffff; color: #1f2328; border: 1px solid #c8ccd1; border-radius: 6px; padding: 4px;
    }}
    QPushButton {{
        background-color: #ffffff; color: #1f2328; border: 1px solid #bcc2c9; border-radius: 6px; padding: 6px 10px; min-height: 28px; font-weight: 600;
    }}
    QPushButton:hover {{ border: 1px solid {accent}; background-color: #f0f3f6; }}
    QPushButton:pressed {{ background-color: {accent}; color: #111111; }}
    QGroupBox {{ border: 1px solid #c8ccd1; border-radius: 8px; margin-top: 10px; padding-top: 12px; font-weight: 700; background-color: #f7f8fa; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px 0 6px; color: #1f2328; }}
    QHeaderView::section {{ background-color: #e9edf2; color: #1f2328; border: 1px solid #cfd4da; padding: 6px; font-weight: 700; }}
    QTableWidget {{ gridline-color: #d7dbe0; alternate-background-color: #f8fafc; selection-background-color: {accent}; selection-color: #111111; }}
    QMenuBar {{ background-color: #f4f5f7; color: #1f2328; }}
    QMenuBar::item:selected {{ background-color: #e9edf2; }}
    QMenu {{ background-color: #ffffff; color: #1f2328; border: 1px solid #c8ccd1; }}
    QMenu::item:selected {{ background-color: {accent}; color: #111111; }}
    QCheckBox {{ spacing: 6px; color: #1f2328; }}
    QScrollBar:vertical {{ background: #eef1f4; width: 12px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: #c0c6ce; min-height: 24px; border-radius: 5px; }}
    QScrollBar::handle:vertical:hover {{ background: #aeb6bf; }}
    """


# --- Custom Widgets & Dialogs ---

class SortableTableWidgetItem(QTableWidgetItem):
    """
    A custom QTableWidgetItem that allows sorting by a hidden value.
    Essential for properly sorting file sizes and dates numerically 
    rather than alphabetically.
    """
    def __init__(self, display_text, sort_val=None):
        super().__init__(display_text)
        # If a sort value is provided (like raw bytes), use it. Otherwise, use text.
        self.sort_val = sort_val if sort_val is not None else display_text

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            try:
                return self.sort_val < other.sort_val
            except TypeError:
                # Fallback to standard string comparison if types are mismatched
                return str(self.sort_val) < str(other.sort_val)
        return super().__lt__(other)


class HelpDialog(QDialog):
    def __init__(self, title: str, body: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 500)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(body)
        layout.addWidget(text)


class SettingsDialog(QDialog):
    def __init__(self, theme_name: str, accent_color: str, slicer_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(520, 220)
        self.selected_accent = accent_color
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(theme_name)
        self.accent_button = QPushButton(f"Accent Color: {accent_color}")
        self.accent_button.clicked.connect(self.pick_accent)
        self.slicer_edit = QLineEdit(slicer_path)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Accent", self.accent_button)
        form.addRow("Slicer path", self.slicer_edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def pick_accent(self):
        color = QColorDialog.getColor(QColor(self.selected_accent), self, "Choose Accent Color")
        if color.isValid():
            self.selected_accent = color.name()
            self.accent_button.setText(f"Accent Color: {self.selected_accent}")

    def values(self):
        return {
            "theme": self.theme_combo.currentText(),
            "accent": self.selected_accent,
            "slicer_path": self.slicer_edit.text().strip(),
        }


# --- Main Application Window ---
class IndexerWorker(QThread):
    log_line = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, db_path: str, library_path: str, exts_csv: str):
        super().__init__()
        self.db_path = db_path
        self.library_path = library_path
        self.exts_csv = exts_csv

    def run(self):
        try:
            db_path = str(Path(self.db_path).expanduser())
            library_path = str(Path(self.library_path).expanduser())

            exts = {e.strip().lower() for e in self.exts_csv.split(",") if e.strip()}
            exts = {e if e.startswith(".") else "." + e for e in exts}

            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            self.log_line.emit(f"[Indexer] Starting scan of {library_path}")

            conn = sqlite3.connect(db_path)
            mini_indexer.init_db(conn)
            mini_indexer.scan(conn, library_path, exts=exts, compute_hash=False)
            conn.close()

            self.log_line.emit("[Indexer] Finished successfully.")
            self.finished_ok.emit()

        except Exception as e:
            self.failed.emit(str(e))


class OrganizerWorker(QThread):
    log_line = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(
        self,
        downloads_path: str,
        library_path: str,
        log_path: str,
        copy_mode: bool,
        dry_run: bool,
        extract_zips: bool,
        delete_empty: bool,
    ):
        super().__init__()
        self.downloads_path = downloads_path
        self.library_path = library_path
        self.log_path = log_path
        self.copy_mode = copy_mode
        self.dry_run = dry_run
        self.extract_zips = extract_zips
        self.delete_empty = delete_empty

    def run(self):
        try:
            source = Path(self.downloads_path).expanduser().resolve()
            dest_root = Path(self.library_path).expanduser().resolve()
            mode = "copy" if self.copy_mode else "move"

            if not source.exists() or not source.is_dir():
                raise RuntimeError(f"Source folder not found: {source}")

            dest_root.mkdir(parents=True, exist_ok=True)
            extract_root = dest_root / "_extracted"

            skip_exts = {".exe", ".msi", ".bat", ".cmd", ".ps1", ".reg"}
            min_bytes = 0

            log_lines = [
                f"Source: {source}",
                f"Dest:   {dest_root}",
                f"Mode:   {mode}",
                f"Dry:    {self.dry_run}",
                f"Extract ZIPs: {self.extract_zips}",
                f"Extract root: {extract_root}",
                f"Delete empty folders: {self.delete_empty}",
                "",
            ]

            considered = 0
            skipped = 0
            processed = 0
            zip_count = 0

            self.log_line.emit(f"[Organizer] Scanning {source}")

            initial_files = list(downloads_organizer.iter_files(source))

            for p in initial_files:
                considered += 1

                if considered % 25 == 0:
                    self.log_line.emit(
                        f"[Organizer] Progress: considered={considered}, processed={processed}, skipped={skipped}"
                    )

                if downloads_organizer.is_temp_or_partial(p):
                    skipped += 1
                    continue

                ext = p.suffix.lower()

                if ext in skip_exts:
                    skipped += 1
                    continue

                try:
                    st = p.stat()
                except FileNotFoundError:
                    skipped += 1
                    continue

                if st.st_size < min_bytes:
                    skipped += 1
                    continue

                if ext == ".zip" and self.extract_zips:
                    extracted_dir = downloads_organizer.extract_zip(
                        p, extract_root, self.dry_run, log_lines
                    )
                    zip_count += 1

                    if downloads_organizer.process_file(
                        p, dest_root, mode, self.dry_run, log_lines
                    ):
                        processed += 1

                    if extracted_dir is not None and extracted_dir.exists():
                        for extracted_file in downloads_organizer.iter_files(extracted_dir):
                            if downloads_organizer.is_temp_or_partial(extracted_file):
                                continue
                            if extracted_file.suffix.lower() in skip_exts:
                                continue
                            try:
                                if extracted_file.stat().st_size < min_bytes:
                                    continue
                            except FileNotFoundError:
                                continue

                            if downloads_organizer.process_file(
                                extracted_file, dest_root, mode, self.dry_run, log_lines
                            ):
                                processed += 1
                    continue

                if downloads_organizer.process_file(
                    p, dest_root, mode, self.dry_run, log_lines
                ):
                    processed += 1

            empty_removed = 0
            if self.delete_empty:
                empty_removed = downloads_organizer.delete_empty_folders(
                    source, self.dry_run, log_lines
                )

            self.log_line.emit(
                f"[Organizer] Done. considered={considered}, processed={processed}, skipped={skipped}, zips={zip_count}"
            )
            if self.delete_empty:
                self.log_line.emit(f"[Organizer] Empty folders removed: {empty_removed}")

            log_path = Path(self.log_path).expanduser().resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("\n".join(log_lines), encoding="utf-8")

            self.finished_ok.emit()

        except Exception as e:
            self.failed.emit(str(e))
    def on_organizer_finished(self):
        self.set_busy(False)
        self._info("Organizer finished.")

    def on_organizer_failed(self, message: str):
        self.set_busy(False)
        self._error(f"Organizer failed: {message}")            

class MiniLibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Library")
        self.resize(1600, 900)
        self.setMinimumSize(1200, 700)

        self.downloads_path = str(DEFAULT_DOWNLOADS)
        self.library_path = str(DEFAULT_LIBRARY)
        self.db_path = str(DEFAULT_DB)
        self.log_path = str(DEFAULT_LOG)
        self.slicer_path = DEFAULT_SLICER if Path(DEFAULT_SLICER).exists() else ""

        self.theme_name = "dark"
        self.accent_color = "#ff6b35"
        self.current_selected_path = None

        self._build_ui()
        self.apply_theme()
        self.refresh_status()
        self.refresh_stats()
        self.search_files()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search keywords like: orc blitzer blood bowl")
        self.ext_input = QLineEdit(".stl")
        self.ext_input.setMaximumWidth(120)
        self.search_input.returnPressed.connect(self.search_files)
        self.ext_input.returnPressed.connect(self.search_files)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 5000)
        self.limit_spin.setValue(50)
        self.limit_spin.setMaximumWidth(90)

        btn_search = QPushButton("Search")
        btn_search.clicked.connect(self.search_files)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_all)

        top_bar.addWidget(QLabel("Search"))
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(QLabel("Ext"))
        top_bar.addWidget(self.ext_input)
        top_bar.addWidget(QLabel("Limit"))
        top_bar.addWidget(self.limit_spin)
        top_bar.addWidget(btn_search)
        top_bar.addWidget(btn_refresh)
        root.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # LEFT PANEL
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["Name", "Ext", "Size", "Modified", "Path"])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)
        
        # Enable column sorting by clicking on headers
        self.results_table.setSortingEnabled(True)
        
        left_layout.addWidget(self.results_table)
        

        # RIGHT PANEL
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QScrollArea.NoFrame)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 0, 5, 0)

        path_box = QGroupBox("Paths")
        path_form = QFormLayout(path_box)
        self.downloads_edit = QLineEdit(self.downloads_path)
        self.library_edit = QLineEdit(self.library_path)
        self.db_edit = QLineEdit(self.db_path)
        self.log_edit = QLineEdit(self.log_path)
        self.slicer_edit = QLineEdit(self.slicer_path)

        btn_browse_downloads = QPushButton("...")
        btn_browse_downloads.clicked.connect(lambda: self.pick_directory(self.downloads_edit))
        btn_browse_library = QPushButton("...")
        btn_browse_library.clicked.connect(lambda: self.pick_directory(self.library_edit))
        btn_browse_db = QPushButton("...")
        btn_browse_db.clicked.connect(lambda: self.pick_file(self.db_edit, save_mode=True))
        btn_browse_log = QPushButton("...")
        btn_browse_log.clicked.connect(lambda: self.pick_file(self.log_edit, save_mode=True))
        btn_browse_slicer = QPushButton("...")
        btn_browse_slicer.clicked.connect(lambda: self.pick_file(self.slicer_edit, save_mode=False))

        path_form.addRow("Downloads", self._with_button(self.downloads_edit, btn_browse_downloads))
        path_form.addRow("Library", self._with_button(self.library_edit, btn_browse_library))
        path_form.addRow("Database", self._with_button(self.db_edit, btn_browse_db))
        path_form.addRow("Log", self._with_button(self.log_edit, btn_browse_log))
        path_form.addRow("Slicer", self._with_button(self.slicer_edit, btn_browse_slicer))

        btn_apply_paths = QPushButton("Apply Paths")
        btn_apply_paths.clicked.connect(self.apply_paths)
        path_form.addRow(btn_apply_paths)
        right_layout.addWidget(path_box)

        status_box = QGroupBox("Status")
        status_layout = QVBoxLayout(status_box)
        self.status_label = QLabel("Status")
        self.stats_label = QLabel("Indexed files: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.stats_label)
        right_layout.addWidget(status_box)

        actions_box = QGroupBox("Actions")
        actions_layout = QGridLayout(actions_box)
        btn_open_file = QPushButton("Open File")
        btn_open_file.clicked.connect(self.open_selected_file)
        btn_open_folder = QPushButton("Open Folder")
        btn_open_folder.clicked.connect(self.open_selected_folder)
        btn_launch_slicer = QPushButton("Launch in Slicer")
        btn_launch_slicer.clicked.connect(self.launch_selected_in_slicer)
        btn_organize = QPushButton("Run Organizer")
        btn_organize.clicked.connect(self.run_organizer)
        btn_index = QPushButton("Rebuild Index")
        btn_index.clicked.connect(self.run_indexer)

        self.dry_run_check = QCheckBox("Dry run")
        self.dry_run_check.setChecked(True)
        self.copy_mode_check = QCheckBox("Use copy instead of move")
        self.copy_mode_check.setChecked(True)
        self.extract_zip_check = QCheckBox("Extract ZIPs")
        self.extract_zip_check.setChecked(True)
        self.delete_empty_check = QCheckBox("Delete empty folders")

        actions_layout.addWidget(btn_open_file, 0, 0)
        actions_layout.addWidget(btn_open_folder, 0, 1)
        actions_layout.addWidget(btn_launch_slicer, 1, 0)
        actions_layout.addWidget(btn_organize, 1, 1)
        actions_layout.addWidget(btn_index, 2, 0, 1, 2)
        actions_layout.addWidget(self.dry_run_check, 3, 0)
        actions_layout.addWidget(self.copy_mode_check, 3, 1)
        actions_layout.addWidget(self.extract_zip_check, 4, 0)
        actions_layout.addWidget(self.delete_empty_check, 4, 1)
        right_layout.addWidget(actions_box)

        preview_box = QGroupBox("3D Preview")
        preview_layout = QVBoxLayout(preview_box)
        
        self.preview_info_label = QLabel("Select a file to view.")
        self.preview_info_label.setAlignment(Qt.AlignCenter)
        self.preview_info_label.setMinimumHeight(40)
        
        self.btn_open_3d = QPushButton("Open Interactive 3D Viewer")
        self.btn_open_3d.clicked.connect(self.open_3d_viewer)
        self.btn_open_3d.setEnabled(False) # Disabled by default until a file is selected

        preview_layout.addWidget(self.preview_info_label)
        preview_layout.addWidget(self.btn_open_3d)
        right_layout.addWidget(preview_box)

        meta_box = QGroupBox("Details")
        meta_layout = QVBoxLayout(meta_box)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(100)
        meta_layout.addWidget(self.details_text)
        right_layout.addWidget(meta_box)

        output_box = QGroupBox("Command Output")
        output_layout = QVBoxLayout(output_box)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(100)
        output_layout.addWidget(self.output_text)
        right_layout.addWidget(output_box)
        right_layout.addStretch(1)

        self.right_scroll.setWidget(right_panel)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_scroll)
        splitter.setSizes([1000, 600])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self._build_menu()

    def _build_menu(self):
        bar = self.menuBar()
        file_menu = bar.addMenu("File")
        file_menu.addAction("Open Library", lambda: self.try_open_path(self.library_path))
        file_menu.addAction("Open Downloads", lambda: self.try_open_path(self.downloads_path))
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)

        view_menu = bar.addMenu("View")
        view_menu.addAction("Dark Theme", lambda: self.set_theme("dark"))
        view_menu.addAction("Light Theme", lambda: self.set_theme("light"))
        view_menu.addSeparator()
        view_menu.addAction("Choose Accent Color", self.pick_accent_color)
        view_menu.addAction("Settings", self.open_settings_dialog)

        help_menu = bar.addMenu("Help")
        help_menu.addAction("Quick Start", self.show_quick_start)
        help_menu.addAction("Controls", self.show_controls_help)
        help_menu.addSeparator()
        help_menu.addAction("About Mini Library", self.show_about_dialog)

    def apply_theme(self):
        stylesheet = light_stylesheet(self.accent_color) if self.theme_name == "light" else dark_stylesheet(self.accent_color)
        self.setStyleSheet(stylesheet)

    def set_theme(self, theme_name: str):
        self.theme_name = theme_name
        self.apply_theme()
        self._info(f"Theme set to {theme_name}")

    def pick_accent_color(self):
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Choose Accent Color")
        if color.isValid():
            self.accent_color = color.name()
            self.apply_theme()
            self._info(f"Accent color set to {self.accent_color}")

    def open_settings_dialog(self):
        dlg = SettingsDialog(self.theme_name, self.accent_color, self.slicer_path, self)
        if dlg.exec():
            vals = dlg.values()
            self.theme_name, self.accent_color = vals["theme"], vals["accent"]
            self.slicer_path = vals["slicer_path"] or self.slicer_path
            self.slicer_edit.setText(self.slicer_path)
            self.apply_theme()
            self.refresh_status()
            self._info("Settings updated.")

    def show_quick_start(self):
        body = ("Mini Library Quick Start\n\n1. Set paths.\n2. Click 'Apply Paths'.\n"
                "3. Rebuild Index.\n4. Search your files.\n5. Click 'Open Interactive 3D Viewer' to inspect a model.")
        HelpDialog("Quick Start", body, self).exec()

    def show_controls_help(self):
        body = ("- Search: local database query.\n- Open File: system default.\n"
                "- Launch in Slicer: user defined path.\n- Open Interactive 3D Viewer: opens a dedicated window to inspect the 3D model.")
        HelpDialog("Controls", body, self).exec()

    def show_about_dialog(self):
        QMessageBox.about(self, "About Mini Library", "Local miniature STL organizer.\nFor questions or donations send inquiries to \nRebelcoreclassnova@gmail.com.")

    def _with_button(self, widget, button):
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(widget, 1)
        lay.addWidget(button, 0)
        return row

    def pick_directory(self, target: QLineEdit):
        start = str(Path(target.text()).expanduser().parent) if target.text().strip() else str(Path.home())
        path = QFileDialog.getExistingDirectory(self, "Choose Directory", start)
        if path: target.setText(path)

    def pick_file(self, target: QLineEdit, save_mode: bool = False):
        start = str(Path(target.text()).expanduser().parent) if target.text().strip() else str(Path.home())
        func = QFileDialog.getSaveFileName if save_mode else QFileDialog.getOpenFileName
        path, _ = func(self, "Choose File", start)
        if path: target.setText(path)

    def apply_paths(self):
        self.downloads_path = self.downloads_edit.text().strip()
        self.library_path = self.library_edit.text().strip()
        self.db_path = self.db_edit.text().strip()
        self.log_path = self.log_edit.text().strip()
        self.slicer_path = self.slicer_edit.text().strip()
        self.refresh_all()
        self._info("Paths updated.")

    def refresh_status(self):
        d_ok = Path(self.downloads_path).expanduser().exists()
        l_ok = Path(self.library_path).expanduser().exists()
        db_ok = Path(self.db_path).expanduser().exists()
        s_ok = bool(self.slicer_path.strip()) and Path(self.slicer_path).expanduser().exists()
        self.status_label.setText(f"Downloads: {'✅' if d_ok else '❌'}  Library: {'✅' if l_ok else '❌'}  "
                                  f"Database: {'✅' if db_ok else '❌'}  Slicer: {'✅' if s_ok else '⚪'}")

    def refresh_stats(self):
        db = Path(self.db_path).expanduser()
        if not db.exists():
            self.stats_label.setText("Indexed files: 0")
            return
        try:
            conn = sqlite3.connect(str(db))
            total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            conn.close()
            self.stats_label.setText(f"Indexed files: {total}")
        except Exception as e:
            self.stats_label.setText(f"Stats error: {e}")

    def refresh_all(self):
        self.refresh_status()
        self.refresh_stats()
        self.search_files()

    def search_files(self):
        db = Path(self.db_path).expanduser()
        
        # Disable sorting temporarily while loading data for massive performance boost
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        
        if not db.exists(): 
            self.results_table.setSortingEnabled(True)
            return

        query = self.search_input.text().strip().lower()
        ext = self.ext_input.text().strip().lower()
        limit = int(self.limit_spin.value())
        words = query.split()
        where, params = [], []

        for w in words:
            like = f"%{w}%"
            where.append("(LOWER(name) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(path) LIKE ?)")
            params.extend([like, like, like])

        if ext:
            if not ext.startswith("."): ext = "." + ext
            where.append("ext = ?")
            params.append(ext)

        where_sql = " AND ".join(where) if where else "1=1"
        params.append(limit)

        try:
            conn = sqlite3.connect(str(db))
            rows = conn.execute(f"SELECT name, ext, size_bytes, mtime_utc, path, tags FROM files WHERE {where_sql} "
                                f"ORDER BY mtime_utc DESC LIMIT ?", params).fetchall()
            conn.close()
            
            self.results_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                name, ext_v, size, mtime, path, _ = row
                size_int = int(size or 0)
                
                # Use our custom sortable items. 
                # Strings are set to sort case-insensitively using `.lower()`.
                self.results_table.setItem(r, 0, SortableTableWidgetItem(str(name), str(name).lower()))
                self.results_table.setItem(r, 1, SortableTableWidgetItem(str(ext_v), str(ext_v).lower()))
                self.results_table.setItem(r, 2, SortableTableWidgetItem(human_size(size_int), size_int))
                self.results_table.setItem(r, 3, SortableTableWidgetItem(str(mtime)))
                self.results_table.setItem(r, 4, SortableTableWidgetItem(str(path), str(path).lower()))
                
            # Re-enable sorting once all data is loaded
            self.results_table.setSortingEnabled(True)
            
            if rows: self.results_table.selectRow(0)
            self._info(f"Loaded {len(rows)} result(s).")
        except Exception as e:
            self.results_table.setSortingEnabled(True)
            self._error(f"Search failed: {e}")

    def on_result_selected(self):
        row = self.results_table.currentRow()
        if row < 0: return
        path_item = self.results_table.item(row, 4)
        if not path_item: return
        
        self.current_selected_path = path_item.text()
        p = Path(self.current_selected_path)
        
        # Update metadata details
        details = [f"Name: {p.name}", f"Path: {p}", f"Parent: {p.parent}"]
        if p.exists():
            details.append(f"Size: {human_size(p.stat().st_size)}")
        self.details_text.setPlainText("\n".join(details))
        
        # Update Preview Box State
        if p.suffix.lower() in [".stl", ".obj", ".3mf"]:
            self.preview_info_label.setText(f"Ready to view:\n{p.name}")
            self.btn_open_3d.setEnabled(True)
        else:
            self.preview_info_label.setText(f"Cannot preview {p.suffix} files.")
            self.btn_open_3d.setEnabled(False)

    def open_3d_viewer(self):
        if not self.current_selected_path:
            self._warn("Select a file first.")
            return
            
        p = Path(self.current_selected_path)
        
        self._info(f"Opening 3D viewer for {p.name}...")
        self.btn_open_3d.setEnabled(False)
        QApplication.processEvents() # Ensure the UI updates before the blocking call
        
        try:
            mesh = trimesh.load(str(p), force="mesh")
            if isinstance(mesh, trimesh.Scene):
                mesh.show(title=f"3D Preview: {p.name}")
            else:
                scene = trimesh.Scene(mesh)
                scene.show(title=f"3D Preview: {p.name}")
                
            self._info("3D viewer closed.")
        except Exception as e:
            self._error(f"Could not open 3D viewer: {e}")
        finally:
            self.btn_open_3d.setEnabled(True)

    def open_selected_file(self):
        if self.current_selected_path: self.try_open_path(self.current_selected_path)

    def open_selected_folder(self):
        if self.current_selected_path: self.try_open_path(str(Path(self.current_selected_path).parent))

    def launch_selected_in_slicer(self):
        if not self.current_selected_path or not self.slicer_path.strip(): return
        slicer = Path(self.slicer_path).expanduser()
        if not slicer.exists(): return
        try:
            subprocess.Popen([str(slicer), "--no-sandbox", str(Path(self.current_selected_path).expanduser())])
        except Exception as e:
            self._error(f"Slicer error: {e}")

    def run_organizer(self):
        try:
            source = Path(self.downloads_path).expanduser().resolve()
            dest_root = Path(self.library_path).expanduser().resolve()
            mode = "copy" if self.copy_mode_check.isChecked() else "move"
            dry_run = self.dry_run_check.isChecked()
            extract_zips = self.extract_zip_check.isChecked()
            delete_empty = self.delete_empty_check.isChecked()

            if not source.exists(): return
            dest_root.mkdir(parents=True, exist_ok=True)
            log_lines = [f"Source: {source}", f"Dest: {dest_root}", f"Mode: {mode}", f"Dry: {dry_run}"]
            
            self.output_text.clear()
            self.output_text.append(f"[Organizer] Scanning {source}")
            initial_files = list(downloads_organizer.iter_files(source))
            processed = 0

            for p in initial_files:
                if downloads_organizer.is_temp_or_partial(p): continue
                if p.suffix.lower() == ".zip" and extract_zips:
                    downloads_organizer.extract_zip(p, dest_root / "_extracted", dry_run, log_lines)
                if downloads_organizer.process_file(p, dest_root, mode, dry_run, log_lines):
                    processed += 1

            if delete_empty: downloads_organizer.delete_empty_folders(source, dry_run, log_lines)
            self.output_text.append(f"\n[done] processed: {processed}")
            self._info("Organizer finished.")
        except Exception as e:
            self._error(f"Organizer failed: {e}")

    def run_indexer(self):
        try:
            db_p = str(Path(self.db_path).expanduser())
            lib_p = str(Path(self.library_path).expanduser())
            exts = {e.strip().lower() for e in DEFAULT_EXTS.split(",") if e.strip()}
            exts = {e if e.startswith(".") else "." + e for e in exts}
            Path(db_p).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(db_p)
            mini_indexer.init_db(conn)
            mini_indexer.scan(conn, lib_p, exts=exts, compute_hash=False)
            conn.close()
            self.output_text.append("[Indexer] Finished.")
            self.refresh_all()
        except Exception as e:
            self._error(f"Indexer failed: {e}")

    def append_output_line(self, text): self.output_text.append(text)

    def try_open_path(self, path_str: str):
        try: open_path(path_str)
        except Exception as e: self._error(str(e))

    def _info(self, msg: str): self.statusBar().showMessage(msg, 5000)
    def _warn(self, msg: str): QMessageBox.warning(self, "Mini Library", msg)
    def _error(self, msg: str): QMessageBox.critical(self, "Mini Library", msg)


def main():
    app = QApplication(sys.argv)
    window = MiniLibraryApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
