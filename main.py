import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import sys

import paige_core
from paige_core import (
    __version__,
    RECENT_FILES_MAX,
    detect_newline,
    load_settings,
    parse_cli_args,
    read_text_file,
    save_settings,
    stat_for_change_detection,
    validate_settings,
    write_atomic,
)

# ------------------------------------------------------------------------------
# Configuration & Vibe
# ------------------------------------------------------------------------------
ctk.set_default_color_theme("blue")
# Note: ctk.set_appearance_mode() is called in __main__ after loading settings,
# so the saved theme is honored before the first widget is created.

class PaigeApp(ctk.CTk):
    def __init__(self, initial_file=None, settings=None):
        super().__init__()

        # validate_settings applies defaults to every key and coerces types,
        # so we can read these straight without further checks.
        settings = validate_settings(settings or {})
        font_size = settings["font_size"]
        appearance = settings["appearance_mode"]
        word_wrap = settings["word_wrap"]
        geom = settings["window_geometry"]
        recents = settings["recent_files"]

        # Window Setup
        self.title("Paige")
        self.geometry(geom)
        self._pending_geometry = geom  # snapshot used at close time

        # Set Window Icon (Safe for Windows, ignored on Linux to avoid crashes)
        if os.name == 'nt':
            try:
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                icon_path = os.path.join(base_path, "assets", "icon.ico")
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
            except Exception:
                pass

        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Menu
        self.grid_rowconfigure(1, weight=0)  # Find Bar
        self.grid_rowconfigure(2, weight=1)  # Text area
        self.grid_rowconfigure(3, weight=0)  # Status Bar

        # --------------------------------------------------------------------------
        # UI Components
        # --------------------------------------------------------------------------
        
        # 1. Menu Bar
        self.menu_bar = ctk.CTkFrame(self, corner_radius=0, height=30)
        self.menu_bar.grid(row=0, column=0, sticky="ew")

        # Menu Buttons (grouped into dropdowns to keep the bar uncluttered).
        # Frequently-toggled controls (Word Wrap, Read-Only) stay as visible
        # checkboxes on the right; rarely-used actions live under these menus.
        self.btn_file = self._create_menu_button("File", self._show_file_menu)
        self.btn_edit = self._create_menu_button("Edit", self._show_edit_menu)
        self.btn_view = self._create_menu_button("View", self._show_view_menu)
        self.btn_help = self._create_menu_button("Help", self._show_help_menu)

        # Save now lives inside the File menu rather than as a standalone
        # button; read-only mode disables that menu entry instead (see
        # _apply_read_only_state, which null-guards this attribute).
        self.btn_save = None

        # Text Size Controls
        self.font_size = font_size  # restored from settings

        self.zoom_label = ctk.CTkLabel(self.menu_bar, text="Text Size:", font=("Segoe UI", 11))
        self.zoom_label.pack(side="right", padx=(10, 5))
        
        self.btn_zoom_out = ctk.CTkButton(
            self.menu_bar, text="-", width=30, 
            command=lambda: self.update_font_size(self.font_size - 1)
        )
        self.btn_zoom_out.pack(side="right", padx=2)
        
        self.zoom_size_label = ctk.CTkLabel(self.menu_bar, text=str(font_size), font=("Segoe UI", 11), width=30)
        self.zoom_size_label.pack(side="right", padx=2)
        
        self.btn_zoom_in = ctk.CTkButton(
            self.menu_bar, text="+", width=30,
            command=lambda: self.update_font_size(self.font_size + 1)
        )
        self.btn_zoom_in.pack(side="right", padx=2)

        # Word Wrap Toggle
        self.wrap_var = ctk.BooleanVar(value=word_wrap)
        self.wrap_check = ctk.CTkCheckBox(
            self.menu_bar, text="Word Wrap",
            variable=self.wrap_var,
            command=self.toggle_word_wrap,
            width=100
        )
        self.wrap_check.pack(side="right", padx=10)

        # Read-Only Toggle
        self.read_only_var = ctk.BooleanVar(value=False)
        self.read_only_check = ctk.CTkCheckBox(
            self.menu_bar, text="Read-Only",
            variable=self.read_only_var,
            command=self.toggle_read_only,
            width=100
        )
        self.read_only_check.pack(side="right", padx=10)

        # 2. Find Bar (Hidden by default)
        self.find_bar = ctk.CTkFrame(self, corner_radius=0, height=40)
        # We don't grid it initially
        
        self.find_entry = ctk.CTkEntry(self.find_bar, placeholder_text="Find text...", width=200)
        self.find_entry.pack(side="left", padx=10, pady=5)
        self.find_entry.bind("<Return>", lambda e: self.find_next())

        self.btn_find_next = ctk.CTkButton(self.find_bar, text="Next", width=60, command=self.find_next)
        self.btn_find_next.pack(side="left", padx=5)

        self.btn_close_find = ctk.CTkButton(self.find_bar, text="X", width=30, fg_color="transparent", text_color="red", command=self.toggle_find_bar)
        self.btn_close_find.pack(side="right", padx=10)

        # 3. Main Text Area
        initial_wrap = "word" if word_wrap else "none"
        self.textbox = ctk.CTkTextbox(
            self,
            font=("Consolas", font_size),
            undo=True,
            corner_radius=0,
            wrap=initial_wrap
        )
        self.textbox.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure Highlighting Tags
        self.textbox._textbox.tag_config("search", background="orange", foreground="black")
        self.textbox._textbox.tag_config("search_highlight", background="yellow", foreground="black")
        
        # Right-Click Context Menu
        self.context_menu = tk.Menu(self.textbox._textbox, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self._context_cut)
        self.context_menu.add_command(label="Copy", command=self._context_copy)
        self.context_menu.add_command(label="Paste", command=self._context_paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self._context_select_all)
        
        # Bind right-click to show context menu
        self.textbox._textbox.bind("<Button-3>", self._show_context_menu)
        
        # 4. Status Bar
        self.status_bar = ctk.CTkFrame(self, corner_radius=0, height=20)
        self.status_bar.grid(row=3, column=0, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ln 1, Col 0 | 0 chars", font=("Segoe UI", 11))
        self.status_label.pack(side="right", padx=10)
        
        # Initial Focus
        self.textbox.focus_set()

        # --------------------------------------------------------------------------
        # State & Bindings
        # --------------------------------------------------------------------------
        self.current_file = None
        self.text_modified = False
        self.appearance_mode = appearance  # restored from settings
        self.file_newline = os.linesep  # Preserve original line endings on round-trip
        # Track on-disk file stat to detect external modifications before save.
        # Nanosecond precision avoids false positives from filesystem mtime resolution.
        self.file_mtime_ns = None
        self.file_size = None
        # Recent files (most-recent first). Restored from settings.
        self.recent_files = recents
        
        # Keybindings
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as_file())
        self.bind("<Control-f>", lambda e: self.toggle_find_bar())
        self.bind("<Control-h>", lambda e: self.open_find_replace_dialog())
        self.bind("<Control-g>", lambda e: self.show_goto_line())
        self.bind("<F1>", lambda e: self.show_about())
        
        # Zoom Keybindings
        self.bind("<Control-plus>", lambda e: self.update_font_size(self.font_size + 1))
        self.bind("<Control-equal>", lambda e: self.update_font_size(self.font_size + 1))  # For keyboards without numpad
        self.bind("<Control-minus>", lambda e: self.update_font_size(self.font_size - 1))
        self.textbox.bind("<Control-MouseWheel>", self._on_mouse_wheel_zoom)
        
        # Status Bar & Modified-state Updates
        self.textbox.bind("<KeyRelease>", self._on_text_key_release)
        self.textbox.bind("<ButtonRelease>", lambda e: self.update_status_bar())
        
        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Load a file passed on the command line, if any.
        # If the path exists, open it; if not, behave like Notepad and start
        # an empty buffer pre-bound to that path so Ctrl+S creates the file.
        if initial_file:
            self._open_initial_file(initial_file)

    def toggle_word_wrap(self):
        """Toggles line wrapping."""
        mode = "word" if self.wrap_var.get() else "none"
        self.textbox.configure(wrap=mode)
        self._persist_settings()

    def _on_text_key_release(self, event=None):
        """Handles KeyRelease: updates status bar and marks file as modified."""
        self.text_modified = True
        self.update_status_bar()

    def toggle_theme(self):
        """Switches between Dark and Light appearance modes."""
        if self.appearance_mode == "Dark":
            self.appearance_mode = "Light"
        else:
            self.appearance_mode = "Dark"
        ctk.set_appearance_mode(self.appearance_mode)
        self._persist_settings()

    def check_unsaved_changes(self):
        """Returns True if it is safe to proceed (no unsaved changes, or user chose to handle them)."""
        if not self.text_modified:
            return True

        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before continuing?"
        )

        if response is None:
            return False
        elif response:
            # Only proceed if the save actually succeeded — otherwise the user
            # cancelled the Save As dialog or hit a write error, and proceeding
            # would silently destroy their work.
            #
            # In read-only mode, save_file() always refuses; redirect to Save As
            # so the user has a working path forward instead of a refusal loop.
            if self.read_only_var.get():
                return self.save_as_file()
            return self.save_file()
        else:
            return True

    def on_closing(self):
        """Called when the user clicks the window close (X) button."""
        if self.check_unsaved_changes():
            # Snapshot the current geometry and flush settings to disk.
            try:
                self._pending_geometry = self.geometry()
                self._persist_settings()
            except Exception:
                pass
            self.destroy()

    def update_font_size(self, new_size):
        """Updates the font size of the text area."""
        # Clamp the font size between 10 and 30
        new_size = max(10, min(30, new_size))

        if new_size != self.font_size:
            self.font_size = new_size
            self.textbox.configure(font=("Consolas", self.font_size))
            self.zoom_size_label.configure(text=str(self.font_size))
            self._persist_settings()

    def _on_mouse_wheel_zoom(self, event):
        """Handles Ctrl+MouseWheel for zooming."""
        # event.delta is positive for scroll up, negative for scroll down
        # On Windows, delta is typically 120 or -120
        if event.delta > 0:
            self.update_font_size(self.font_size + 1)
        else:
            self.update_font_size(self.font_size - 1)
        return "break"  # Prevent default scrolling behavior

    def toggle_find_bar(self):
        """Shows/Hides the find bar."""
        if self.find_bar.winfo_ismapped():
            self.find_bar.grid_forget()
            self.textbox._textbox.tag_remove("search", "1.0", "end")
            self.textbox.focus_set()
        else:
            self.find_bar.grid(row=1, column=0, sticky="ew")
            self.find_entry.focus_set()

    def find_next(self):
        """Locates the next occurrence of the search string."""
        query = self.find_entry.get()
        if not query:
            return

        # Clear existing highlights
        text_widget = self.textbox._textbox
        text_widget.tag_remove("search", "1.0", "end")

        start_pos = text_widget.index("insert")
        # Search from cursor
        pos = text_widget.search(query, start_pos, stopindex="end", nocase=True)
        
        if not pos:
            # Wrap around and search from beginning
            pos = text_widget.search(query, "1.0", stopindex="end", nocase=True)

        if pos:
            # Calculate end position
            end_pos = f"{pos}+{len(query)}c"
            text_widget.tag_add("search", pos, end_pos)
            text_widget.mark_set("insert", end_pos)
            text_widget.see(pos)
        else:
            messagebox.showinfo("Find", f"No matches found for '{query}'")

    # --------------------------------------------------------------------------
    # Find/Replace Dialog
    # --------------------------------------------------------------------------
    def open_find_replace_dialog(self):
        """Opens a floating Find/Replace dialog window."""
        # Create toplevel window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Find / Replace")
        dialog.geometry("400x180")
        dialog.attributes('-topmost', True)
        dialog.resizable(False, False)
        
        # Store search state
        dialog.last_search_pos = "1.0"
        
        # Find what label and entry
        find_label = ctk.CTkLabel(dialog, text="Find what:", font=("Segoe UI", 12))
        find_label.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        
        find_entry = ctk.CTkEntry(dialog, width=280, placeholder_text="Enter text to find...")
        find_entry.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="ew")
        find_entry.focus_set()
        
        # Replace with label and entry
        replace_label = ctk.CTkLabel(dialog, text="Replace with:", font=("Segoe UI", 12))
        replace_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        replace_entry = ctk.CTkEntry(dialog, width=280, placeholder_text="Enter replacement text...")
        replace_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=(15, 10))
        
        # Find Next button
        btn_find_next = ctk.CTkButton(
            button_frame, 
            text="Find Next", 
            width=100,
            command=lambda: self._find_next_in_dialog(dialog, find_entry)
        )
        btn_find_next.pack(side="left", padx=5)
        
        # Replace button
        btn_replace = ctk.CTkButton(
            button_frame, 
            text="Replace", 
            width=100,
            command=lambda: self._replace_current(dialog, find_entry, replace_entry)
        )
        btn_replace.pack(side="left", padx=5)
        
        # Replace All button
        btn_replace_all = ctk.CTkButton(
            button_frame, 
            text="Replace All", 
            width=100,
            command=lambda: self._replace_all(dialog, find_entry, replace_entry)
        )
        btn_replace_all.pack(side="left", padx=5)
        
        # Bind Enter key in find entry to Find Next
        find_entry.bind("<Return>", lambda e: self._find_next_in_dialog(dialog, find_entry))
        
        # Bind Enter key in replace entry to Replace
        replace_entry.bind("<Return>", lambda e: self._replace_current(dialog, find_entry, replace_entry))
        
        # Configure grid weights
        dialog.grid_columnconfigure(1, weight=1)

    def _find_next_in_dialog(self, dialog, find_entry):
        """Finds the next occurrence from the Find/Replace dialog."""
        query = find_entry.get()
        if not query:
            return
        
        text_widget = self.textbox._textbox
        
        # Clear existing highlights
        text_widget.tag_remove("search_highlight", "1.0", "end")
        
        # Search from last position
        start_pos = dialog.last_search_pos
        pos = text_widget.search(query, start_pos, stopindex="end", nocase=True)
        
        if not pos:
            # Wrap around to beginning
            pos = text_widget.search(query, "1.0", stopindex="end", nocase=True)
            if not pos:
                messagebox.showinfo("Find", f"No matches found for '{query}'", parent=dialog)
                dialog.last_search_pos = "1.0"
                return
        
        # Highlight the match
        end_pos = f"{pos}+{len(query)}c"
        text_widget.tag_add("search_highlight", pos, end_pos)
        text_widget.mark_set("insert", end_pos)
        text_widget.see(pos)
        
        # Update search position for next search
        dialog.last_search_pos = end_pos

    def _replace_current(self, dialog, find_entry, replace_entry):
        """Replaces the currently highlighted match and finds the next one."""
        if self.read_only_var.get():
            messagebox.showinfo("Read-Only", "Cannot replace: Paige is in read-only mode.", parent=dialog)
            return
        query = find_entry.get()
        replacement = replace_entry.get()

        if not query:
            return
        
        text_widget = self.textbox._textbox
        
        # Check if there's a current highlight
        ranges = text_widget.tag_ranges("search_highlight")
        if ranges:
            # Replace the highlighted text
            start, end = ranges[0], ranges[1]
            text_widget.delete(start, end)
            text_widget.insert(start, replacement)
            self.text_modified = True
            self.update_status_bar()

            # Update search position
            dialog.last_search_pos = f"{start}+{len(replacement)}c"
            
            # Find next occurrence
            self._find_next_in_dialog(dialog, find_entry)
        else:
            # No current highlight, just find the first occurrence
            self._find_next_in_dialog(dialog, find_entry)

    def _replace_all(self, dialog, find_entry, replace_entry):
        """Replaces all occurrences of the search term in the document."""
        if self.read_only_var.get():
            messagebox.showinfo("Read-Only", "Cannot replace: Paige is in read-only mode.", parent=dialog)
            return
        query = find_entry.get()
        replacement = replace_entry.get()

        if not query:
            return
        
        text_widget = self.textbox._textbox
        
        # Clear highlights
        text_widget.tag_remove("search_highlight", "1.0", "end")
        
        # Count replacements
        count = 0
        pos = "1.0"
        
        while True:
            pos = text_widget.search(query, pos, stopindex="end", nocase=True)
            if not pos:
                break
            
            # Replace the text
            end_pos = f"{pos}+{len(query)}c"
            text_widget.delete(pos, end_pos)
            text_widget.insert(pos, replacement)
            
            # Move position forward
            pos = f"{pos}+{len(replacement)}c"
            count += 1

        if count > 0:
            self.text_modified = True
            self.update_status_bar()

        # Reset search position
        dialog.last_search_pos = "1.0"

        if count > 0:
            messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).", parent=dialog)
        else:
            messagebox.showinfo("Replace All", f"No matches found for '{query}'.", parent=dialog)

    def update_title(self):
        """Updates the window title based on current file state."""
        if self.current_file:
            title = f"Paige - {os.path.basename(self.current_file)}"
        else:
            title = "Paige"
        if self.read_only_var.get():
            title += "  [Read-Only]"
        self.title(title)

    def update_status_bar(self):
        """Updates the line/col/char info."""
        # Get cursor position
        idx = self.textbox.index("insert")
        row, col = idx.split(".")
        
        # Get total chars (subtracting 1 for the trailing newline Tkinter adds)
        total_content = self.textbox.get("1.0", "end-1c")
        total_chars = len(total_content)
        
        self.status_label.configure(text=f"Ln {row}, Col {col} | {total_chars} chars")

    def _create_menu_button(self, text, command):
        """Helper to create menu-like buttons."""
        btn = ctk.CTkButton(
            self.menu_bar,
            text=text,
            width=50,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            anchor="center",
            command=command
        )
        btn.pack(side="left", padx=2, pady=2)
        return btn

    def _popup_under(self, menu, button):
        """Pops up a tk.Menu flush below the given menu-bar button."""
        try:
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _show_file_menu(self):
        """Opens the File dropdown."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Open", command=self.open_file)
        menu.add_cascade(label="Recent", menu=self._build_recent_menu(menu))
        menu.add_separator()
        # Save is disabled in read-only mode (mirrors the old Save button).
        save_state = "disabled" if self.read_only_var.get() else "normal"
        menu.add_command(label="Save", command=self.save_file, state=save_state)
        menu.add_command(label="Save As", command=self.save_as_file)
        menu.add_separator()
        menu.add_command(label="File Types...", command=self.show_file_types_dialog)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.on_closing)
        self._popup_under(menu, self.btn_file)

    def _show_edit_menu(self):
        """Opens the Edit dropdown."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Find/Replace", command=self.open_find_replace_dialog)
        self._popup_under(menu, self.btn_edit)

    def _show_view_menu(self):
        """Opens the View dropdown."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        self._popup_under(menu, self.btn_view)

    def _show_help_menu(self):
        """Opens the Help dropdown."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="About", command=self.show_about)
        self._popup_under(menu, self.btn_help)

    # --------------------------------------------------------------------------
    # Read-Only Mode
    # --------------------------------------------------------------------------
    def toggle_read_only(self):
        """Called when the user clicks the Read-Only checkbox."""
        self._apply_read_only_state()
        self.update_title()

    def _apply_read_only_state(self):
        """Applies the current read-only flag to the textbox and Save button.

        Tk's text widget in state="disabled" still allows mouse selection,
        Ctrl+A, and Ctrl+C — which is exactly what we want for log viewing.
        It blocks typing, paste, and programmatic delete/insert.
        """
        if self.read_only_var.get():
            self.textbox._textbox.configure(state="disabled")
            if self.btn_save is not None:
                self.btn_save.configure(state="disabled")
        else:
            self.textbox._textbox.configure(state="normal")
            if self.btn_save is not None:
                self.btn_save.configure(state="normal")

    def _record_file_stat(self, file_path):
        """Records the on-disk file stat for external-change detection."""
        self.file_mtime_ns, self.file_size = stat_for_change_detection(file_path)

    # --------------------------------------------------------------------------
    # File Operations
    # --------------------------------------------------------------------------
    def open_file(self):
        """Opens a file via dialog and loads it into the textbox."""
        # Guard against discarding unsaved work when replacing the buffer.
        if not self.check_unsaved_changes():
            return

        file_path = ctk.filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        self._load_file_from_disk(file_path)

    def _open_initial_file(self, file_path):
        """Handle a file path provided on the command line at startup.

        Existing path → load it. Nonexistent path → start with an empty buffer
        but pre-bind current_file so Ctrl+S creates the file. Matches Notepad.
        """
        abs_path = os.path.abspath(file_path)
        if os.path.exists(abs_path):
            self._load_file_from_disk(abs_path)
        else:
            self.current_file = abs_path
            self.text_modified = False
            self.file_mtime_ns = None
            self.file_size = None
            self.update_title()

    def _load_file_from_disk(self, file_path):
        """Read a file from disk into the textbox, with size warning and
        line-ending preservation. Used by both open_file and CLI startup."""
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        except OSError as e:
            self._show_error("Open Error", f"Could not open file:\n{str(e)}")
            return

        if file_size_mb > 50:
            proceed = messagebox.askyesno(
                "Large File Warning",
                f"The file '{os.path.basename(file_path)}' is {file_size_mb:.1f}MB. "
                f"Opening large files may cause the application to hang. Do you want to continue?"
            )
            if not proceed:
                return

        try:
            content, self.file_newline = read_text_file(file_path)

            # Briefly enable the widget in case we're loading while read-only.
            self.textbox._textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)

            self.current_file = file_path
            self.text_modified = False
            self._record_file_stat(file_path)
            self._add_to_recent(file_path)

            # Auto-enable read-only if the file isn't writable. Saves users
            # from typing into a system log they don't have permission to edit.
            file_is_writable = os.access(file_path, os.W_OK)
            self.read_only_var.set(not file_is_writable)
            self._apply_read_only_state()

            self.update_title()

        except UnicodeDecodeError:
            self._show_error("Encoding Error", "Could not decode file with UTF-8. Binary or legacy format suspected.")
        except Exception as e:
            self._show_error("Open Error", f"Could not open file:\n{str(e)}")

    def save_file(self):
        """Saves the current file. Defaults to Save As if new. Returns True on success."""
        if self.read_only_var.get():
            messagebox.showinfo(
                "Read-Only",
                "Paige is in read-only mode. Toggle Read-Only off to save, "
                "or use Save As to save a copy."
            )
            return False
        if self.current_file:
            return self._write_to_file(self.current_file)
        return self.save_as_file()

    def save_as_file(self):
        """Opens prompt to save file as new path. Returns True on success."""
        file_path = ctk.filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not file_path:
            return False
        return self._write_to_file(file_path)

    def _write_to_file(self, file_path):
        """Atomically write content to disk. Returns True on success."""
        # External-change check: only when overwriting the file we originally
        # loaded. Save As to a new path is intentional — skip the check.
        if (
            file_path == self.current_file
            and self.file_mtime_ns is not None
            and os.path.exists(file_path)
        ):
            try:
                st = os.stat(file_path)
                if st.st_mtime_ns != self.file_mtime_ns or st.st_size != self.file_size:
                    proceed = messagebox.askyesno(
                        "File Changed on Disk",
                        f"'{os.path.basename(file_path)}' has been modified on disk "
                        f"since you opened it.\n\nOverwrite with your version?"
                    )
                    if not proceed:
                        return False
            except OSError:
                # Stat failed for some reason; fall through and let the write
                # itself surface any real error.
                pass

        # Delegate the actual temp-file + fsync + os.replace dance to
        # paige_core.write_atomic so the I/O is testable in isolation.
        content = self.textbox.get("1.0", "end-1c")
        try:
            write_atomic(file_path, content, newline=self.file_newline)
            self.current_file = file_path
            self.text_modified = False
            self._record_file_stat(file_path)
            self.update_title()
            return True
        except Exception as e:
            self._show_error("Save Error", f"Could not save file:\n{str(e)}")
            return False

    # --------------------------------------------------------------------------
    # Context Menu Methods
    # --------------------------------------------------------------------------
    def _show_context_menu(self, event):
        """Displays the right-click context menu at the cursor position."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Ensure the menu closes properly
            self.context_menu.grab_release()
    
    def _context_cut(self):
        """Handles Cut command from context menu."""
        self.textbox._textbox.event_generate("<<Cut>>")
    
    def _context_copy(self):
        """Handles Copy command from context menu."""
        self.textbox._textbox.event_generate("<<Copy>>")
    
    def _context_paste(self):
        """Handles Paste command from context menu."""
        self.textbox._textbox.event_generate("<<Paste>>")
    
    def _context_select_all(self):
        """Handles Select All command from context menu."""
        self.textbox._textbox.tag_add("sel", "1.0", "end")
        self.textbox._textbox.mark_set("insert", "1.0")
        self.textbox._textbox.see("insert")

    def _show_error(self, title, message):
        """Displays error using standard tkinter messagebox."""
        messagebox.showerror(title, message)

    # --------------------------------------------------------------------------
    # Settings persistence
    # --------------------------------------------------------------------------
    def _persist_settings(self):
        """Snapshot current state to settings.json. Best-effort — never
        raises into the UI; a failure to save prefs shouldn't disrupt edits."""
        try:
            save_settings({
                "version": 1,
                "font_size": self.font_size,
                "appearance_mode": self.appearance_mode,
                "word_wrap": bool(self.wrap_var.get()),
                "window_geometry": self._pending_geometry,
                "recent_files": self.recent_files[:RECENT_FILES_MAX],
            })
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # Recent Files
    # --------------------------------------------------------------------------
    def _add_to_recent(self, file_path):
        """Pushes a file path to the top of the recent list, deduped."""
        # Normalize so the same file via different relative paths dedupes.
        abs_path = os.path.abspath(file_path)
        self.recent_files = [p for p in self.recent_files if os.path.abspath(p) != abs_path]
        self.recent_files.insert(0, abs_path)
        del self.recent_files[RECENT_FILES_MAX:]
        self._persist_settings()

    def _format_recent_label(self, path):
        """Human-readable label for the Recent menu: 'filename  —  parent_dir'."""
        name = os.path.basename(path) or path
        parent = os.path.basename(os.path.dirname(path))
        return f"{name}  —  {parent}" if parent else name

    def _build_recent_menu(self, parent):
        """Builds the Recent Files menu (used as a cascade under File)."""
        menu = tk.Menu(parent, tearoff=0)
        if not self.recent_files:
            menu.add_command(label="(no recent files)", state="disabled")
        else:
            for path in self.recent_files:
                menu.add_command(
                    label=self._format_recent_label(path),
                    command=lambda p=path: self._open_from_recent(p),
                )
            menu.add_separator()
            menu.add_command(label="Clear Recent Files", command=self._clear_recent)
        return menu

    def _open_from_recent(self, path):
        """Opens a file selected from the Recent menu, with the usual guard."""
        if not self.check_unsaved_changes():
            return
        if not os.path.exists(path):
            remove = messagebox.askyesno(
                "File Not Found",
                f"'{path}' no longer exists.\n\nRemove it from Recent Files?"
            )
            if remove:
                self.recent_files = [p for p in self.recent_files if p != path]
                self._persist_settings()
            return
        self._load_file_from_disk(path)

    def _clear_recent(self):
        """Empties the Recent Files list."""
        self.recent_files = []
        self._persist_settings()

    # --------------------------------------------------------------------------
    # Go to Line
    # --------------------------------------------------------------------------
    def show_goto_line(self):
        """Small dialog to jump the cursor to a specific line number."""
        text_widget = self.textbox._textbox
        try:
            cur_line = int(text_widget.index("insert").split(".")[0])
            max_line = int(text_widget.index("end-1c").split(".")[0])
        except (ValueError, tk.TclError):
            cur_line, max_line = 1, 1

        dialog = ctk.CTkToplevel(self)
        dialog.title("Go to Line")
        dialog.geometry("300x140")
        dialog.resizable(False, False)
        dialog.transient(self)

        self.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width() // 2) - 150
        py = self.winfo_rooty() + (self.winfo_height() // 2) - 70
        dialog.geometry(f"+{max(0, px)}+{max(0, py)}")

        ctk.CTkLabel(
            dialog,
            text=f"Go to line (1 – {max_line}):",
            font=("Segoe UI", 11),
        ).pack(pady=(15, 6))

        entry = ctk.CTkEntry(dialog, width=140, justify="center")
        entry.pack(pady=2)
        entry.insert(0, str(cur_line))
        entry.select_range(0, "end")
        entry.focus_set()

        status = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 9), text_color="gray")
        status.pack(pady=(2, 0))

        def do_goto(event=None):
            raw = entry.get().strip()
            try:
                line = int(raw)
            except ValueError:
                status.configure(text="Enter a number.")
                return
            if line < 1 or line > max_line:
                status.configure(text=f"Must be between 1 and {max_line}.")
                return
            text_widget.mark_set("insert", f"{line}.0")
            text_widget.see(f"{line}.0")
            self.update_status_bar()
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(6, 10))
        ctk.CTkButton(btn_frame, text="Go", width=70, command=do_goto).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", width=70, command=dialog.destroy).pack(side="left", padx=5)

        entry.bind("<Return>", do_goto)
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.after(50, dialog.grab_set)

    # --------------------------------------------------------------------------
    # File Type Registration (Windows only)
    # --------------------------------------------------------------------------
    # Default set of extensions we offer to register. Conservative — these
    # are formats Paige is well-suited for (configs, logs, plain text) and
    # avoids stepping on richer editors' toes (e.g. no .py / .json by default).
    FILE_TYPES_DEFAULT = [".txt", ".log", ".conf", ".cfg", ".ini", ".env"]
    FILE_TYPES_OPTIONAL = [".md", ".json", ".yaml", ".yml", ".xml"]
    PROGID = "Paige.TextFile"

    def show_file_types_dialog(self):
        """Opens the file-type registration dialog (Windows only)."""
        if os.name != "nt":
            messagebox.showinfo(
                "File Types",
                "File type registration is a Windows-only feature."
            )
            return
        if not getattr(sys, "frozen", False):
            messagebox.showinfo(
                "File Types",
                "File type registration is only available in the built Paige.exe.\n\n"
                "Running from source would register the Python interpreter, "
                "which isn't useful."
            )
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Paige File Type Registration")
        dialog.geometry("440x440")
        dialog.resizable(False, False)
        dialog.transient(self)

        # Header
        ctk.CTkLabel(
            dialog, text="Register Paige with Windows",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(15, 4))

        ctk.CTkLabel(
            dialog,
            text=(
                "Adds Paige to the 'Open With' menu for the selected file types.\n"
                "Changes apply to your user account only — no admin required.\n"
                "After registering, set Paige as default via right-click → "
                "Properties → Change."
            ),
            font=("Segoe UI", 10), justify="left", wraplength=400
        ).pack(pady=(0, 12))

        # Extension checkboxes
        ext_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ext_frame.pack(pady=4, padx=20, fill="x")

        check_vars = {}
        all_exts = self.FILE_TYPES_DEFAULT + self.FILE_TYPES_OPTIONAL
        for i, ext in enumerate(all_exts):
            var = ctk.BooleanVar(value=(ext in self.FILE_TYPES_DEFAULT))
            check_vars[ext] = var
            ctk.CTkCheckBox(
                ext_frame, text=ext, variable=var, width=80
            ).grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=4)

        # Status label
        status_label = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 10))
        status_label.pack(pady=(10, 4))

        # Button frame
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(8, 12))

        def do_register():
            chosen = [ext for ext, v in check_vars.items() if v.get()]
            if not chosen:
                status_label.configure(text="No extensions selected.")
                return
            try:
                self._register_paige_filetypes(chosen)
                self._notify_shell_assoc_changed()
                status_label.configure(
                    text=f"Registered Paige for: {', '.join(chosen)}"
                )
            except OSError as e:
                status_label.configure(text=f"Failed: {e}")

        def do_unregister():
            try:
                removed = self._unregister_paige_filetypes()
                self._notify_shell_assoc_changed()
                if removed:
                    status_label.configure(text="Paige registration removed.")
                else:
                    status_label.configure(text="Nothing to remove.")
            except OSError as e:
                status_label.configure(text=f"Failed: {e}")

        ctk.CTkButton(btn_frame, text="Register Selected", width=140, command=do_register).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Remove All", width=120, command=do_unregister).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Close", width=80, command=dialog.destroy).pack(side="left", padx=6)

        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.after(50, dialog.grab_set)

    def _register_paige_filetypes(self, extensions):
        """Writes per-user registry entries to expose Paige in Open With.

        Uses HKCU\\Software\\Classes so no admin is required and Paige stays
        portable. We register a ProgID and add it to each extension's
        OpenWithProgids list — we deliberately do NOT claim default ownership
        of the extension (Windows blocks programmatic UserChoice manipulation
        anyway; users must pick the default via Explorer's UI).
        """
        import winreg
        exe_path = os.path.abspath(sys.executable)

        # ProgID: Paige.TextFile
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{self.PROGID}") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Paige Text File")
            winreg.SetValueEx(k, "FriendlyTypeName", 0, winreg.REG_SZ, "Paige Text File")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{self.PROGID}\DefaultIcon") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe_path}",0')
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{self.PROGID}\shell\open\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')

        # Also register under Applications\ so we appear in Open With even
        # without ProgID association.
        app_name = os.path.basename(exe_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\Applications\{app_name}") as k:
            winreg.SetValueEx(k, "FriendlyAppName", 0, winreg.REG_SZ, "Paige")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\Applications\{app_name}\shell\open\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')

        # Per-extension: add to OpenWithProgids
        for ext in extensions:
            if not ext.startswith("."):
                ext = "." + ext
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{ext}\OpenWithProgids") as k:
                winreg.SetValueEx(k, self.PROGID, 0, winreg.REG_NONE, b"")

    def _unregister_paige_filetypes(self):
        """Removes all Paige registry entries. Returns True if anything existed."""
        import winreg
        removed_any = False

        # Strip from every extension we might have registered.
        for ext in self.FILE_TYPES_DEFAULT + self.FILE_TYPES_OPTIONAL:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, rf"Software\Classes\{ext}\OpenWithProgids",
                    0, winreg.KEY_SET_VALUE
                ) as k:
                    try:
                        winreg.DeleteValue(k, self.PROGID)
                        removed_any = True
                    except FileNotFoundError:
                        pass
            except FileNotFoundError:
                pass

        # Recursively delete the ProgID tree.
        if self._delete_reg_tree(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{self.PROGID}"):
            removed_any = True

        # And the Applications\ entry.
        exe_name = os.path.basename(os.path.abspath(sys.executable))
        if self._delete_reg_tree(
            winreg.HKEY_CURRENT_USER, rf"Software\Classes\Applications\{exe_name}"
        ):
            removed_any = True

        return removed_any

    @staticmethod
    def _delete_reg_tree(root, path):
        """Recursively delete a registry key. Returns True if it existed."""
        import winreg
        try:
            with winreg.OpenKey(root, path) as k:
                subkeys = []
                i = 0
                while True:
                    try:
                        subkeys.append(winreg.EnumKey(k, i))
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            return False
        for sub in subkeys:
            PaigeApp._delete_reg_tree(root, f"{path}\\{sub}")
        try:
            winreg.DeleteKey(root, path)
        except OSError:
            return False
        return True

    @staticmethod
    def _notify_shell_assoc_changed():
        """Tell Explorer to pick up file-association changes immediately."""
        try:
            import ctypes
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # About Dialog
    # --------------------------------------------------------------------------
    def show_about(self):
        """Displays the About dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("About Paige")
        dialog.geometry("360x240")
        dialog.resizable(False, False)
        dialog.transient(self)

        # Center over parent
        self.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width() // 2) - 180
        py = self.winfo_rooty() + (self.winfo_height() // 2) - 120
        dialog.geometry(f"+{max(0, px)}+{max(0, py)}")

        name_label = ctk.CTkLabel(
            dialog, text="Paige", font=("Segoe UI", 22, "bold")
        )
        name_label.pack(pady=(20, 4))

        version_label = ctk.CTkLabel(
            dialog, text=f"Version {__version__}", font=("Segoe UI", 12)
        )
        version_label.pack()

        tagline_label = ctk.CTkLabel(
            dialog, text="A dumb text editor — that's the point.",
            font=("Segoe UI", 11)
        )
        tagline_label.pack(pady=(12, 4))

        # Plain text, not a clickable link: Paige does not invoke
        # protocol handlers, per the security model in the README.
        repo_label = ctk.CTkLabel(
            dialog, text="github.com/DQ-Labs/Paige",
            font=("Consolas", 10), text_color=("gray30", "gray70")
        )
        repo_label.pack(pady=(0, 12))

        ok_btn = ctk.CTkButton(dialog, text="OK", width=80, command=dialog.destroy)
        ok_btn.pack(pady=(4, 16))

        # Focus + Esc/Enter to close
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.bind("<Return>", lambda e: dialog.destroy())
        # grab_set must come after the window is visible
        dialog.after(50, dialog.grab_set)
        dialog.after(60, ok_btn.focus_set)


if __name__ == "__main__":
    settings = load_settings()
    # Apply the saved theme BEFORE the first widget is created so the
    # initial paint matches the user's choice instead of flashing dark.
    saved_theme = settings.get("appearance_mode", "Dark")
    if saved_theme not in ("Dark", "Light"):
        saved_theme = "Dark"
    ctk.set_appearance_mode(saved_theme)

    initial_file = parse_cli_args(sys.argv)
    app = PaigeApp(initial_file=initial_file, settings=settings)
    app.mainloop()
