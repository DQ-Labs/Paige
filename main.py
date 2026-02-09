import customtkinter as ctk
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
        
        # Configure Highlighting Tag
        self.textbox._textbox.tag_config("search", background="orange", foreground="black")
        
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
        
        # Status Bar Updates
        self.textbox.bind("<KeyRelease>", lambda e: self.update_status_bar())
        self.textbox.bind("<ButtonRelease>", lambda e: self.update_status_bar())

    def toggle_word_wrap(self):
        """Toggles line wrapping."""
        mode = "word" if self.wrap_var.get() else "none"
        self.textbox.configure(wrap=mode)

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

    def _show_error(self, title, message):
        """Displays error using standard tkinter messagebox."""
        from tkinter import messagebox
        messagebox.showerror(title, message)

if __name__ == "__main__":
    app = PaigeApp()
    app.mainloop()
