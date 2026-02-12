import customtkinter as ctk
import tkinter as tk
import os
import sys

# ------------------------------------------------------------------------------
# Configuration & Vibe
# ------------------------------------------------------------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PaigeApp(ctk.CTk):
    def __init__(self):
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
        self.current_file_path = None
        
        # Keybindings
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as_file())
        self.bind("<Control-f>", lambda e: self.toggle_find_bar())
        self.bind("<Control-h>", lambda e: self.open_find_replace_dialog())
        
        # Zoom Keybindings
        self.bind("<Control-plus>", lambda e: self.update_font_size(self.font_size + 1))
        self.bind("<Control-equal>", lambda e: self.update_font_size(self.font_size + 1))  # For keyboards without numpad
        self.bind("<Control-minus>", lambda e: self.update_font_size(self.font_size - 1))
        self.textbox.bind("<Control-MouseWheel>", self._on_mouse_wheel_zoom)
        
        # Status Bar Updates
        self.textbox.bind("<KeyRelease>", lambda e: self.update_status_bar())
        self.textbox.bind("<ButtonRelease>", lambda e: self.update_status_bar())

    def toggle_word_wrap(self):
        """Toggles line wrapping."""
        mode = "word" if self.wrap_var.get() else "none"
        self.textbox.configure(wrap=mode)

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
            # Standard popup for not found
            from tkinter import messagebox
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
                from tkinter import messagebox
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
        
        # Reset search position
        dialog.last_search_pos = "1.0"
        
        # Show confirmation
        from tkinter import messagebox
        if count > 0:
            messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).", parent=dialog)
        else:
            messagebox.showinfo("Replace All", f"No matches found for '{query}'.", parent=dialog)

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

    # --------------------------------------------------------------------------
    # File Operations
    # --------------------------------------------------------------------------
    def open_file(self):
        """Opens a file and loads content into the textbox."""
        file_path = ctk.filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            
            self.current_file_path = file_path
            self.title(f"Paige - {os.path.basename(file_path)}")
            
        except UnicodeDecodeError:
            self._show_error("Encoding Error", "Could not decode file with UTF-8. Binary or legacy format suspected.")
        except Exception as e:
            self._show_error("Open Error", f"Could not open file:\n{str(e)}")

    def save_file(self):
        """Saves the current file. Defaults to Save As if new."""
        if self.current_file_path:
            self._write_to_file(self.current_file_path)
        else:
            self.save_as_file()

    def save_as_file(self):
        """Opens prompt to save file as new path."""
        file_path = ctk.filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            self._write_to_file(file_path)

    def _write_to_file(self, file_path):
        """Internal method to write content to disk safely."""
        try:
            content = self.textbox.get("1.0", "end-1c")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.current_file_path = file_path
            self.title(f"Paige - {os.path.basename(file_path)}")
            
        except Exception as e:
            self._show_error("Save Error", f"Could not save file:\n{str(e)}")

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
        return "break"

    def _show_error(self, title, message):
        """Displays error using standard tkinter messagebox."""
        from tkinter import messagebox
        messagebox.showerror(title, message)

if __name__ == "__main__":
    app = PaigeApp()
    app.mainloop()
