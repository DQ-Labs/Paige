import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import sys
import tempfile

__version__ = "0.8"

# ------------------------------------------------------------------------------
# Configuration & Vibe
# ------------------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PaigeApp(ctk.CTk):
    def __init__(self, initial_file=None):
        super().__init__()

        # Window Setup
        self.title("Paige")
        self.geometry("900x700")

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

        # Menu Buttons
        self.btn_open = self._create_menu_button("Open", self.open_file)
        self.btn_save = self._create_menu_button("Save", self.save_file)
        self.btn_save_as = self._create_menu_button("Save As", self.save_as_file)
        self.btn_find_replace = self._create_menu_button("Find/Replace", self.open_find_replace_dialog)
        self.btn_toggle_theme = self._create_menu_button("Toggle Theme", self.toggle_theme)
        self.btn_about = self._create_menu_button("About", self.show_about)

        # Text Size Controls
        self.font_size = 14  # Default font size
        
        self.zoom_label = ctk.CTkLabel(self.menu_bar, text="Text Size:", font=("Segoe UI", 11))
        self.zoom_label.pack(side="right", padx=(10, 5))
        
        self.btn_zoom_out = ctk.CTkButton(
            self.menu_bar, text="-", width=30, 
            command=lambda: self.update_font_size(self.font_size - 1)
        )
        self.btn_zoom_out.pack(side="right", padx=2)
        
        self.zoom_size_label = ctk.CTkLabel(self.menu_bar, text="14", font=("Segoe UI", 11), width=30)
        self.zoom_size_label.pack(side="right", padx=2)
        
        self.btn_zoom_in = ctk.CTkButton(
            self.menu_bar, text="+", width=30,
            command=lambda: self.update_font_size(self.font_size + 1)
        )
        self.btn_zoom_in.pack(side="right", padx=2)

        # Word Wrap Toggle
        self.wrap_var = ctk.BooleanVar(value=False)
        self.wrap_check = ctk.CTkCheckBox(
            self.menu_bar, text="Word Wrap", 
            variable=self.wrap_var, 
            command=self.toggle_word_wrap,
            width=100
        )
        self.wrap_check.pack(side="right", padx=10)

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
        self.textbox = ctk.CTkTextbox(
            self, 
            font=("Consolas", 14), 
            undo=True,
            corner_radius=0,
            wrap="none"
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
        self.appearance_mode = "Dark"  # Track current theme
        self.file_newline = os.linesep  # Preserve original line endings on round-trip
        
        # Keybindings
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as_file())
        self.bind("<Control-f>", lambda e: self.toggle_find_bar())
        self.bind("<Control-h>", lambda e: self.open_find_replace_dialog())
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
            return self.save_file()
        else:
            return True

    def on_closing(self):
        """Called when the user clicks the window close (X) button."""
        if self.check_unsaved_changes():
            self.destroy()

    def update_font_size(self, new_size):
        """Updates the font size of the text area."""
        # Clamp the font size between 10 and 30
        new_size = max(10, min(30, new_size))
        
        if new_size != self.font_size:
            self.font_size = new_size
            self.textbox.configure(font=("Consolas", self.font_size))
            self.zoom_size_label.configure(text=str(self.font_size))

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
            self.title(f"Paige - {os.path.basename(self.current_file)}")
        else:
            self.title("Paige")

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
            # newline="" disables universal-newline translation so we can
            # detect the file's original line ending and preserve it on save.
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                raw = f.read()

            if "\r\n" in raw:
                self.file_newline = "\r\n"
            elif "\r" in raw:
                self.file_newline = "\r"
            else:
                self.file_newline = "\n"

            # Normalize to \n for the Tk widget (it works in \n internally).
            content = raw.replace("\r\n", "\n").replace("\r", "\n")

            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)

            self.current_file = file_path
            self.text_modified = False
            self.update_title()

        except UnicodeDecodeError:
            self._show_error("Encoding Error", "Could not decode file with UTF-8. Binary or legacy format suspected.")
        except Exception as e:
            self._show_error("Open Error", f"Could not open file:\n{str(e)}")

    def save_file(self):
        """Saves the current file. Defaults to Save As if new. Returns True on success."""
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
        # Write to a sibling temp file and os.replace() into place so a crash
        # mid-write can never leave the user with a truncated original.
        content = self.textbox.get("1.0", "end-1c")
        if self.file_newline != "\n":
            content = content.replace("\n", self.file_newline)

        target_dir = os.path.dirname(os.path.abspath(file_path)) or "."
        tmp_fd = None
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix=".paige-", suffix=".tmp", dir=target_dir
            )
            with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as f:
                tmp_fd = None  # fdopen now owns the descriptor
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, file_path)
            tmp_path = None

            self.current_file = file_path
            self.text_modified = False
            self.update_title()
            return True

        except Exception as e:
            self._show_error("Save Error", f"Could not save file:\n{str(e)}")
            return False
        finally:
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass
            if tmp_path is not None and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

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


def _parse_cli_args(argv):
    """Returns the file path passed on the command line, if any.

    Intentionally minimal: we take the first positional argument and ignore
    the rest. No flag parsing — this is a windowed binary, so stdout/stderr
    aren't visible, and --help / --version can't usefully report anything.
    Anyone who needs the version can use the About dialog (F1).
    """
    for arg in argv[1:]:
        # Skip anything that looks like a flag so PyInstaller / shell
        # internal args don't get treated as a filename.
        if arg.startswith("-"):
            continue
        return arg
    return None


if __name__ == "__main__":
    initial_file = _parse_cli_args(sys.argv)
    app = PaigeApp(initial_file=initial_file)
    app.mainloop()
