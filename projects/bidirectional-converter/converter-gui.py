#!/usr/bin/env python3
"""
Bidirectional Converter GUI
--------------------------
A comprehensive GUI for text-to-code and code-to-text conversion using Claude API.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import asyncio
import threading
import json
import os
from datetime import datetime
from pathlib import Path
import configparser
from typing import Optional, Dict, Any

# Import the converter module
from bidirectional_converter import (
    BidirectionalConverter, ConversionConfig, DetailLevel,
    ConversionDirection, ConversionResult
)


class ConverterGUI:
    """Main GUI application for bidirectional conversion"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bidirectional Code Converter - Powered by Claude")
        self.root.geometry("1200x800")
        
        # Initialize converter (will be set up after API key is provided)
        self.converter: Optional[BidirectionalConverter] = None
        self.current_mode = ConversionDirection.TEXT_TO_CODE
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Setup GUI
        self._setup_styles()
        self._create_menu()
        self._create_main_interface()
        self._create_status_bar()
        
        # Initialize API if key is available
        self._initialize_api()
        
        # Bind keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load application configuration"""
        config_path = Path.home() / ".bidirectional_converter" / "config.ini"
        config = configparser.ConfigParser()
        
        if config_path.exists():
            config.read(config_path)
        else:
            # Create default configuration
            config['API'] = {
                'model': 'claude-3-opus-20240229',
                'temperature': '0.3',
                'max_tokens': '4096'
            }
            config['UI'] = {
                'theme': 'default',
                'font_size': '11',
                'auto_convert': 'false'
            }
            config['Cache'] = {
                'enabled': 'true',
                'ttl_hours': '24'
            }
            
            # Save default config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                config.write(f)
        
        return config
    
    def _setup_styles(self):
        """Configure GUI styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'background': '#f8fafc',
            'surface': '#ffffff',
            'text': '#1e293b'
        }
        
        # Configure styles
        style.configure('Primary.TButton', background=self.colors['primary'])
        style.configure('Secondary.TButton', background=self.colors['secondary'])
        
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_conversion, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Output...", command=self._save_output, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export History...", command=self._export_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy Output", command=self._copy_output, accelerator="Ctrl+C")
        edit_menu.add_command(label="Clear All", command=self._clear_all, accelerator="Ctrl+L")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="API Settings...", command=self._show_api_settings)
        tools_menu.add_command(label="Clear Cache", command=self._clear_cache)
        tools_menu.add_command(label="View Statistics", command=self._show_statistics)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_command(label="Examples", command=self._show_examples)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_main_interface(self):
        """Create the main interface"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Mode selector
        mode_frame = ttk.LabelFrame(toolbar, text="Conversion Mode")
        mode_frame.pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="text_to_code")
        ttk.Radiobutton(
            mode_frame, text="Text → Code", 
            variable=self.mode_var, value="text_to_code",
            command=self._switch_mode
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            mode_frame, text="Code → Text", 
            variable=self.mode_var, value="code_to_text",
            command=self._switch_mode
        ).pack(side=tk.LEFT, padx=5)
        
        # Language selector
        lang_frame = ttk.LabelFrame(toolbar, text="Language")
        lang_frame.pack(side=tk.LEFT, padx=5)
        
        self.language_var = tk.StringVar(value="python")
        self.language_combo = ttk.Combobox(
            lang_frame, textvariable=self.language_var, width=15,
            values=["python", "javascript", "java", "cpp", "csharp", "go", "rust", "sql", "html", "css", "vml"]
        )
        self.language_combo.pack(padx=5, pady=5)
        
        # Options button
        ttk.Button(
            toolbar, text="Options", command=self._show_options,
            style='Secondary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        # Convert button
        self.convert_btn = ttk.Button(
            toolbar, text="Convert", command=self._perform_conversion,
            style='Primary.TButton'
        )
        self.convert_btn.pack(side=tk.RIGHT, padx=5)
        
        # Main content area
        content = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input panel
        input_frame = ttk.LabelFrame(content, text="Input")
        content.add(input_frame, weight=1)
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, font=("Consolas", 11)
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input controls
        input_controls = ttk.Frame(input_frame)
        input_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            input_controls, text="Load File", command=self._load_input_file
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            input_controls, text="Load Example", command=self._load_example
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            input_controls, text="Clear", command=lambda: self.input_text.delete("1.0", tk.END)
        ).pack(side=tk.LEFT, padx=2)
        
        # Output panel
        output_frame = ttk.LabelFrame(content, text="Output")
        content.add(output_frame, weight=1)
        
        # Output notebook for multiple views
        self.output_notebook = ttk.Notebook(output_frame)
        self.output_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Main output tab
        output_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(output_tab, text="Output")
        
        self.output_text = scrolledtext.ScrolledText(
            output_tab, wrap=tk.WORD, font=("Consolas", 11)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Metadata tab
        metadata_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(metadata_tab, text="Metadata")
        
        self.metadata_text = scrolledtext.ScrolledText(
            metadata_tab, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        
        # History tab
        history_tab = ttk.Frame(self.output_notebook)
        self.output_notebook.add(history_tab, text="History")
        
        # History treeview
        self.history_tree = ttk.Treeview(
            history_tab, columns=("time", "direction", "tokens", "cached"),
            show="tree headings"
        )
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("direction", text="Direction")
        self.history_tree.heading("tokens", text="Tokens")
        self.history_tree.heading("cached", text="Cached")
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        
        # Output controls
        output_controls = ttk.Frame(output_frame)
        output_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            output_controls, text="Copy", command=self._copy_output
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            output_controls, text="Save", command=self._save_output
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            output_controls, text="Format", command=self._format_output
        ).pack(side=tk.LEFT, padx=2)
        
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self.status_bar, textvariable=self.status_var
        )
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # API status
        self.api_status_var = tk.StringVar(value="API: Not initialized")
        self.api_status_label = ttk.Label(
            self.status_bar, textvariable=self.api_status_var
        )
        self.api_status_label.pack(side=tk.RIGHT, padx=5)
        
        # Token counter
        self.token_var = tk.StringVar(value="Tokens: 0")
        self.token_label = ttk.Label(
            self.status_bar, textvariable=self.token_var
        )
        self.token_label.pack(side=tk.RIGHT, padx=5)
        
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Control-n>", lambda e: self._new_conversion())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_output())
        self.root.bind("<Control-c>", lambda e: self._copy_output())
        self.root.bind("<Control-l>", lambda e: self._clear_all())
        self.root.bind("<F5>", lambda e: self._perform_conversion())
        
    def _initialize_api(self):
        """Initialize the API connection"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Try to load from config file
            key_file = Path.home() / ".bidirectional_converter" / "api_key.txt"
            if key_file.exists():
                api_key = key_file.read_text().strip()
        
        if api_key:
            try:
                config = ConversionConfig(
                    model=self.config['API']['model'],
                    temperature=float(self.config['API']['temperature']),
                    max_tokens=int(self.config['API']['max_tokens']),
                    cache_enabled=self.config['Cache'].getboolean('enabled')
                )
                self.converter = BidirectionalConverter(api_key, config)
                self.api_status_var.set("API: Connected")
                self.convert_btn.config(state=tk.NORMAL)
            except Exception as e:
                self.api_status_var.set("API: Error")
                messagebox.showerror("API Error", f"Failed to initialize API: {str(e)}")
                self.convert_btn.config(state=tk.DISABLED)
        else:
            self.api_status_var.set("API: No key")
            self.convert_btn.config(state=tk.DISABLED)
            # Prompt for API key
            self.root.after(100, self._prompt_for_api_key)
    
    def _prompt_for_api_key(self):
        """Prompt user for API key"""
        dialog = tk.Toplevel(self.root)
        dialog.title("API Configuration")
        dialog.geometry("500x250")
        dialog.transient(self.root)
        
        # Instructions
        instructions = ttk.Label(
            dialog,
            text="Please enter your Anthropic API key to enable conversions.\n" +
                 "Your key will be stored securely for future sessions.",
            wraplength=450
        )
        instructions.pack(pady=20)
        
        # API key entry
        key_frame = ttk.Frame(dialog)
        key_frame.pack(pady=10)
        
        ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        key_var = tk.StringVar()
        key_entry = ttk.Entry(key_frame, textvariable=key_var, width=50, show="*")
        key_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_key():
            api_key = key_var.get().strip()
            if api_key:
                # Save key
                key_file = Path.home() / ".bidirectional_converter" / "api_key.txt"
                key_file.parent.mkdir(parents=True, exist_ok=True)
                key_file.write_text(api_key)
                
                # Reinitialize API
                os.environ["ANTHROPIC_API_KEY"] = api_key
                self._initialize_api()
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Key", "Please enter a valid API key.")
        
        ttk.Button(button_frame, text="Save", command=save_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Focus on entry
        key_entry.focus_set()
        dialog.bind("<Return>", lambda e: save_key())
    
    def _switch_mode(self):
        """Switch between conversion modes"""
        mode = self.mode_var.get()
        self.current_mode = ConversionDirection.TEXT_TO_CODE if mode == "text_to_code" else ConversionDirection.CODE_TO_TEXT
        
        # Update UI labels
        if self.current_mode == ConversionDirection.TEXT_TO_CODE:
            self.root.title("Text to Code Converter - Powered by Claude")
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", "Enter natural language description here...")
        else:
            self.root.title("Code to Text Converter - Powered by Claude")
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", "Enter code here...")
    
    def _perform_conversion(self):
        """Perform the conversion"""
        if not self.converter:
            messagebox.showerror("API Error", "API not initialized. Please configure your API key.")
            return
        
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Empty Input", "Please enter some text to convert.")
            return
        
        # Clear output
        self.output_text.delete("1.0", tk.END)
        self.metadata_text.delete("1.0", tk.END)
        
        # Update status
        self.status_var.set("Converting...")
        self.convert_btn.config(state=tk.DISABLED)
        
        # Run conversion in background thread
        thread = threading.Thread(
            target=self._run_conversion_async,
            args=(input_text,)
        )
        thread.start()
    
    def _run_conversion_async(self, input_text: str):
        """Run conversion in async context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if self.current_mode == ConversionDirection.TEXT_TO_CODE:
                result = loop.run_until_complete(
                    self.converter.convert_text_to_code(
                        text=input_text,
                        target_language=self.language_var.get()
                    )
                )
            else:
                result = loop.run_until_complete(
                    self.converter.convert_code_to_text(
                        code=input_text,
                        source_language=self.language_var.get()
                    )
                )
            
            # Update UI in main thread
            self.root.after(0, self._update_ui_with_result, result)
            
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            loop.close()
    
    def _update_ui_with_result(self, result: ConversionResult):
        """Update UI with conversion result"""
        if result.success:
            # Update output
            self.output_text.insert("1.0", result.output)
            
            # Update metadata
            metadata = {
                "Tokens Used": result.tokens_used,
                "Processing Time": f"{result.processing_time:.2f}s",
                "Cached": "Yes" if result.cached else "No",
                "Model": result.metadata.get("model", "Unknown"),
                "Timestamp": result.metadata.get("timestamp", "Unknown")
            }
            
            metadata_text = json.dumps(metadata, indent=2)
            self.metadata_text.insert("1.0", metadata_text)
            
            # Update history
            self.history_tree.insert(
                "", 0,
                text=f"Conversion {self.history_tree.get_children().__len__() + 1}",
                values=(
                    datetime.now().strftime("%H:%M:%S"),
                    self.current_mode.value,
                    result.tokens_used,
                    "Yes" if result.cached else "No"
                )
            )
            
            # Update status
            self.status_var.set("Conversion successful")
            self.token_var.set(f"Tokens: {result.tokens_used}")
            
            # Show suggestions if any
            if result.suggestions:
                suggestions_text = "\n\nSuggestions:\n" + "\n".join(f"• {s}" for s in result.suggestions)
                self.output_text.insert(tk.END, suggestions_text)
        else:
            self.status_var.set("Conversion failed")
            messagebox.showerror("Conversion Error", result.error)
        
        self.convert_btn.config(state=tk.NORMAL)
    
    def _show_error(self, error_message: str):
        """Show error message"""
        self.status_var.set("Error occurred")
        self.convert_btn.config(state=tk.NORMAL)
        messagebox.showerror("Conversion Error", error_message)
    
    def _new_conversion(self):
        """Start a new conversion"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.metadata_text.delete("1.0", tk.END)
        self.status_var.set("Ready")
        self.token_var.set("Tokens: 0")
    
    def _open_file(self):
        """Open a file for conversion"""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All Files", "*.*"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("Text Files", "*.txt"),
                ("Markdown Files", "*.md")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)
                self.status_var.set(f"Loaded: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to load file: {str(e)}")
    
    def _save_output(self):
        """Save the output to a file"""
        output = self.output_text.get("1.0", tk.END).strip()
        if not output:
            messagebox.showwarning("Empty Output", "No output to save.")
            return
        
        # Determine file extension based on mode and language
        if self.current_mode == ConversionDirection.TEXT_TO_CODE:
            extensions = {
                "python": ".py",
                "javascript": ".js",
                "java": ".java",
                "cpp": ".cpp",
                "csharp": ".cs",
                "go": ".go",
                "rust": ".rs",
                "sql": ".sql",
                "html": ".html",
                "css": ".css",
                "vml": ".vml"
            }
            default_ext = extensions.get(self.language_var.get(), ".txt")
        else:
            default_ext = ".md"
        
        file_path = filedialog.asksaveasfilename(
            title="Save Output",
            defaultextension=default_ext,
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Markdown Files", "*.md")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                self.status_var.set(f"Saved: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
    
    def _copy_output(self):
        """Copy output to clipboard"""
        output = self.output_text.get("1.0", tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_var.set("Output copied to clipboard")
        else:
            messagebox.showwarning("Empty Output", "No output to copy.")
    
    def _clear_all(self):
        """Clear all text areas"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.metadata_text.delete("1.0", tk.END)
        self.status_var.set("Cleared")
    
    def _load_example(self):
        """Load an example based on current mode"""
        examples = {
            ConversionDirection.TEXT_TO_CODE: {
                "python": "Create a function that validates email addresses using regex. "
                         "It should check for proper format and return True if valid, False otherwise.",
                "javascript": "Create a React component for a todo list with add, delete, and toggle complete functionality.",
                "sql": "Create a query that finds the top 5 customers by total purchase amount in the last 30 days."
            },
            ConversionDirection.CODE_TO_TEXT: {
                "python": """def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)""",
                "javascript": """const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};"""
            }
        }
        
        example = examples.get(self.current_mode, {}).get(self.language_var.get(), "")
        if example:
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", example)
            self.status_var.set("Example loaded")
    
    def _format_output(self):
        """Format the output code (if applicable)"""
        # This would integrate with language-specific formatters
        # For now, just a placeholder
        messagebox.showinfo("Format", "Code formatting would be applied here based on language.")
    
    def _show_options(self):
        """Show conversion options dialog"""
        dialog = OptionsDialog(self.root, self.converter)
        dialog.show()
    
    def _show_api_settings(self):
        """Show API settings dialog"""
        dialog = APISettingsDialog(self.root, self.config)
        if dialog.show():
            # Reload configuration and reinitialize API
            self.config = self._load_configuration()
            self._initialize_api()
    
    def _clear_cache(self):
        """Clear the conversion cache"""
        if self.converter and self.converter.cache:
            if messagebox.askyesno("Clear Cache", "Are you sure you want to clear the conversion cache?"):
                # Clear cache implementation
                cache_path = Path("conversion_cache.db")
                if cache_path.exists():
                    cache_path.unlink()
                self._initialize_api()  # Reinitialize to create new cache
                self.status_var.set("Cache cleared")
    
    def _show_statistics(self):
        """Show usage statistics"""
        # This would show conversion statistics from the cache
        messagebox.showinfo("Statistics", "Conversion statistics would be displayed here.")
    
    def _export_history(self):
        """Export conversion history"""
        # Export history to CSV or JSON
        messagebox.showinfo("Export", "History export functionality would be implemented here.")
    
    def _show_documentation(self):
        """Show documentation"""
        # Open documentation in browser
        import webbrowser
        webbrowser.open("https://github.com/yourusername/bidirectional-converter/wiki")
    
    def _show_examples(self):
        """Show examples window"""
        ExamplesWindow(self.root).show()
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Bidirectional Code Converter\n\n"
            "Version 1.0.0\n"
            "Powered by Claude API\n\n"
            "Convert between natural language and code with AI assistance."
        )
    
    def _load_input_file(self):
        """Load a file into the input area"""
        self._open_file()


class OptionsDialog:
    """Options dialog for conversion settings"""
    
    def __init__(self, parent, converter):
        self.parent = parent
        self.converter = converter
        self.dialog = None
        
    def show(self):
        """Show the options dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Conversion Options")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        
        # Create notebook for different option categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text-to-Code options
        t2c_frame = ttk.Frame(notebook)
        notebook.add(t2c_frame, text="Text to Code")
        self._create_text_to_code_options(t2c_frame)
        
        # Code-to-Text options
        c2t_frame = ttk.Frame(notebook)
        notebook.add(c2t_frame, text="Code to Text")
        self._create_code_to_text_options(c2t_frame)
        
        # General options
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self._create_general_options(general_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Apply", command=self._apply_options).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
    def _create_text_to_code_options(self, parent):
        """Create text-to-code options"""
        # Include comments
        self.include_comments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text="Include comments",
            variable=self.include_comments_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Include docstrings
        self.include_docstrings_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text="Include docstrings",
            variable=self.include_docstrings_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Use type hints
        self.use_type_hints_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text="Use type hints (Python)",
            variable=self.use_type_hints_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Follow conventions
        self.follow_conventions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text="Follow language conventions",
            variable=self.follow_conventions_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
    def _create_code_to_text_options(self, parent):
        """Create code-to-text options"""
        # Detail level
        detail_frame = ttk.LabelFrame(parent, text="Detail Level")
        detail_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.detail_level_var = tk.StringVar(value="standard")
        ttk.Radiobutton(
            detail_frame, text="Summary",
            variable=self.detail_level_var, value="summary"
        ).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(
            detail_frame, text="Standard",
            variable=self.detail_level_var, value="standard"
        ).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(
            detail_frame, text="Detailed",
            variable=self.detail_level_var, value="detailed"
        ).pack(anchor=tk.W, padx=5, pady=2)
        
        # Include examples
        self.include_examples_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            parent, text="Include usage examples",
            variable=self.include_examples_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Technical level
        tech_frame = ttk.LabelFrame(parent, text="Technical Level")
        tech_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.technical_level_var = tk.StringVar(value="intermediate")
        ttk.Radiobutton(
            tech_frame, text="Beginner",
            variable=self.technical_level_var, value="beginner"
        ).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(
            tech_frame, text="Intermediate",
            variable=self.technical_level_var, value="intermediate"
        ).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(
            tech_frame, text="Advanced",
            variable=self.technical_level_var, value="advanced"
        ).pack(anchor=tk.W, padx=5, pady=2)
        
    def _create_general_options(self, parent):
        """Create general options"""
        # Temperature
        temp_frame = ttk.LabelFrame(parent, text="Temperature (Creativity)")
        temp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.temperature_var = tk.DoubleVar(value=0.3)
        temp_scale = ttk.Scale(
            temp_frame, from_=0.0, to=1.0,
            variable=self.temperature_var, orient=tk.HORIZONTAL
        )
        temp_scale.pack(fill=tk.X, padx=10, pady=5)
        
        temp_label = ttk.Label(temp_frame, text="0.3")
        temp_label.pack()
        
        def update_temp_label(value):
            temp_label.config(text=f"{float(value):.1f}")
        
        temp_scale.config(command=update_temp_label)
        
        # Max tokens
        tokens_frame = ttk.LabelFrame(parent, text="Max Tokens")
        tokens_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.max_tokens_var = tk.IntVar(value=4096)
        ttk.Spinbox(
            tokens_frame, from_=100, to=8192, increment=100,
            textvariable=self.max_tokens_var, width=10
        ).pack(padx=10, pady=5)
        
    def _apply_options(self):
        """Apply the selected options"""
        if self.converter:
            # Update converter configuration
            self.converter.config.include_comments = self.include_comments_var.get()
            self.converter.config.include_docstrings = self.include_docstrings_var.get()
            self.converter.config.use_type_hints = self.use_type_hints_var.get()
            self.converter.config.follow_conventions = self.follow_conventions_var.get()
            self.converter.config.detail_level = DetailLevel(self.detail_level_var.get())
            self.converter.config.include_examples = self.include_examples_var.get()
            self.converter.config.technical_level = self.technical_level_var.get()
            self.converter.config.temperature = self.temperature_var.get()
            self.converter.config.max_tokens = self.max_tokens_var.get()
        
        self.dialog.destroy()


class APISettingsDialog:
    """API settings dialog"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.dialog = None
        self.result = False
        
    def show(self):
        """Show the API settings dialog and return True if settings were changed"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API Settings")
        self.dialog.geometry("500x300")
        self.dialog.transient(self.parent)
        
        # Model selection
        model_frame = ttk.LabelFrame(self.dialog, text="Model")
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.model_var = tk.StringVar(value=self.config['API']['model'])
        model_combo = ttk.Combobox(
            model_frame, textvariable=self.model_var,
            values=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            state="readonly", width=30
        )
        model_combo.pack(padx=10, pady=5)
        
        # Temperature
        temp_frame = ttk.LabelFrame(self.dialog, text="Default Temperature")
        temp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.temp_var = tk.StringVar(value=self.config['API']['temperature'])
        ttk.Entry(temp_frame, textvariable=self.temp_var, width=10).pack(padx=10, pady=5)
        
        # Max tokens
        tokens_frame = ttk.LabelFrame(self.dialog, text="Default Max Tokens")
        tokens_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.tokens_var = tk.StringVar(value=self.config['API']['max_tokens'])
        ttk.Entry(tokens_frame, textvariable=self.tokens_var, width=10).pack(padx=10, pady=5)
        
        # Cache settings
        cache_frame = ttk.LabelFrame(self.dialog, text="Cache")
        cache_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.cache_enabled_var = tk.BooleanVar(value=self.config['Cache'].getboolean('enabled'))
        ttk.Checkbutton(
            cache_frame, text="Enable cache",
            variable=self.cache_enabled_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result
        
    def _save_settings(self):
        """Save the API settings"""
        self.config['API']['model'] = self.model_var.get()
        self.config['API']['temperature'] = self.temp_var.get()
        self.config['API']['max_tokens'] = self.tokens_var.get()
        self.config['Cache']['enabled'] = str(self.cache_enabled_var.get())
        
        # Save to file
        config_path = Path.home() / ".bidirectional_converter" / "config.ini"
        with open(config_path, 'w') as f:
            self.config.write(f)
        
        self.result = True
        self.dialog.destroy()


class ExamplesWindow:
    """Examples window showing various conversion examples"""
    
    def __init__(self, parent):
        self.parent = parent
        
    def show(self):
        """Show the examples window"""
        window = tk.Toplevel(self.parent)
        window.title("Conversion Examples")
        window.geometry("800x600")
        window.transient(self.parent)
        
        # Create notebook for different example categories
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add example tabs
        self._add_text_to_code_examples(notebook)
        self._add_code_to_text_examples(notebook)
        
    def _add_text_to_code_examples(self, notebook):
        """Add text-to-code examples tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Text → Code")
        
        # Example content would go here
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        examples = """
Text-to-Code Examples
====================

Example 1: Python Function
--------------------------
Input: "Create a function that calculates the factorial of a number using recursion"

Output:
def factorial(n):
    '''Calculate the factorial of a number using recursion.
    
    Args:
        n (int): The number to calculate factorial for
        
    Returns:
        int: The factorial of n
        
    Raises:
        ValueError: If n is negative
    '''
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)

Example 2: JavaScript Class
---------------------------
Input: "Create a JavaScript class for a shopping cart with methods to add items, remove items, and calculate total"

Output:
class ShoppingCart {
    constructor() {
        this.items = [];
    }
    
    addItem(item, quantity = 1, price) {
        const existingItem = this.items.find(i => i.item === item);
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({ item, quantity, price });
        }
    }
    
    removeItem(item) {
        this.items = this.items.filter(i => i.item !== item);
    }
    
    calculateTotal() {
        return this.items.reduce((total, item) => {
            return total + (item.quantity * item.price);
        }, 0);
    }
}
"""
        text.insert("1.0", examples)
        text.config(state=tk.DISABLED)
    
    def _add_code_to_text_examples(self, notebook):
        """Add code-to-text examples tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Code → Text")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        examples = """
Code-to-Text Examples
====================

Example 1: Algorithm Explanation
--------------------------------
Input:
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

Output:
This function implements the binary search algorithm to find a target value in a sorted array.

The algorithm works by:
1. Initializing two pointers: 'left' at the start (0) and 'right' at the end of the array
2. Repeatedly dividing the search space in half by calculating the middle index
3. Comparing the middle element with the target value
4. If they match, returning the index
5. If the middle element is less than the target, searching the right half
6. If the middle element is greater than the target, searching the left half
7. Continuing until the element is found or the search space is empty

Time Complexity: O(log n)
Space Complexity: O(1)

Example usage:
numbers = [1, 3, 5, 7, 9, 11, 13]
index = binary_search(numbers, 7)  # Returns 3
"""
        text.insert("1.0", examples)
        text.config(state=tk.DISABLED)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
