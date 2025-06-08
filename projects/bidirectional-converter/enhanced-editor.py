#!/usr/bin/env python3
"""
Enhanced Editor Component with Custom Markup Support
---------------------------------------------------
Provides advanced text editing capabilities with custom markup,
context menus, and dynamic prompt generation.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import json
from datetime import datetime


@dataclass
class MarkupDefinition:
    """Defines a custom markup pattern"""
    name: str
    start_delimiter: str
    end_delimiter: str
    description: str
    color: str = "#000000"
    background: Optional[str] = None
    font_style: Optional[str] = None  # bold, italic, underline
    example: Optional[str] = None
    

@dataclass
class TextSelection:
    """Represents a text selection in the editor"""
    start_index: str
    end_index: str
    text: str
    

class MarkupManager:
    """Manages custom markup definitions and applications"""
    
    def __init__(self):
        self.markups: Dict[str, MarkupDefinition] = {}
        self._load_default_markups()
        
    def _load_default_markups(self):
        """Load default markup definitions"""
        defaults = [
            MarkupDefinition(
                name="emphasis",
                start_delimiter="///",
                end_delimiter="\\\\\\",
                description="Emphasizes important text",
                color="#D32F2F",
                font_style="bold",
                example="///IMPORTANT\\\\\\"
            ),
            MarkupDefinition(
                name="context",
                start_delimiter="<<<",
                end_delimiter=">>>",
                description="Provides contextual information",
                color="#1976D2",
                background="#E3F2FD",
                example="<<<context: technical>>>>"
            ),
            MarkupDefinition(
                name="instruction",
                start_delimiter="{{",
                end_delimiter="}}",
                description="Special instruction for AI",
                color="#388E3C",
                font_style="italic",
                example="{{treat as code}}"
            ),
            MarkupDefinition(
                name="variable",
                start_delimiter="[[",
                end_delimiter="]]",
                description="Variable placeholder",
                color="#7B1FA2",
                background="#F3E5F5",
                example="[[user_name]]"
            ),
            MarkupDefinition(
                name="warning",
                start_delimiter="!!!",
                end_delimiter="!!!",
                description="Warning or caution",
                color="#F57C00",
                font_style="bold",
                example="!!!CAUTION!!!"
            )
        ]
        
        for markup in defaults:
            self.markups[markup.name] = markup
    
    def add_markup(self, markup: MarkupDefinition):
        """Add a new markup definition"""
        self.markups[markup.name] = markup
    
    def remove_markup(self, name: str):
        """Remove a markup definition"""
        if name in self.markups:
            del self.markups[name]
    
    def get_markup_key(self) -> str:
        """Generate a markup key/legend for prompts"""
        key_lines = ["MARKUP KEY:"]
        key_lines.append("=" * 40)
        
        for name, markup in self.markups.items():
            key_lines.append(f"\n{markup.name.upper()}:")
            key_lines.append(f"  Format: {markup.start_delimiter}text{markup.end_delimiter}")
            key_lines.append(f"  Purpose: {markup.description}")
            if markup.example:
                key_lines.append(f"  Example: {markup.example}")
        
        key_lines.append("\n" + "=" * 40)
        return "\n".join(key_lines)
    
    def apply_markup(self, text: str, markup_name: str) -> str:
        """Apply markup to text"""
        if markup_name not in self.markups:
            return text
        
        markup = self.markups[markup_name]
        return f"{markup.start_delimiter}{text}{markup.end_delimiter}"
    
    def find_all_markup(self, text: str) -> List[Tuple[str, int, int, str]]:
        """Find all markup instances in text"""
        results = []
        
        for name, markup in self.markups.items():
            # Escape special regex characters
            start = re.escape(markup.start_delimiter)
            end = re.escape(markup.end_delimiter)
            
            # Find all matches
            pattern = f"{start}(.*?){end}"
            for match in re.finditer(pattern, text):
                results.append((
                    name,
                    match.start(),
                    match.end(),
                    match.group(1)
                ))
        
        return sorted(results, key=lambda x: x[1])


class EnhancedTextEditor(tk.Text):
    """Enhanced text editor with custom markup support"""
    
    def __init__(self, parent, markup_manager: MarkupManager, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.markup_manager = markup_manager
        self.context_menu = None
        self._setup_tags()
        self._setup_bindings()
        self._word_occurrences: Dict[str, List[Tuple[str, str]]] = {}
        
    def _setup_tags(self):
        """Configure text tags for markup display"""
        for name, markup in self.markup_manager.markups.items():
            tag_config = {"foreground": markup.color}
            
            if markup.background:
                tag_config["background"] = markup.background
                
            if markup.font_style:
                current_font = tkfont.Font(font=self['font'])
                if markup.font_style == "bold":
                    tag_config["font"] = current_font.copy()
                    tag_config["font"].configure(weight="bold")
                elif markup.font_style == "italic":
                    tag_config["font"] = current_font.copy()
                    tag_config["font"].configure(slant="italic")
                elif markup.font_style == "underline":
                    tag_config["underline"] = True
            
            self.tag_configure(f"markup_{name}", **tag_config)
    
    def _setup_bindings(self):
        """Set up event bindings"""
        self.bind("<Button-3>", self._show_context_menu)  # Right-click
        self.bind("<Control-m>", self._quick_markup)  # Ctrl+M for quick markup
        self.bind("<KeyRelease>", self._on_text_change)
        self.bind("<<Selection>>", self._on_selection_change)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click"""
        # Destroy existing menu if any
        if self.context_menu:
            self.context_menu.destroy()
        
        # Create new context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        
        # Get current selection
        try:
            selection = self.get_selection()
            if selection:
                selected_text = selection.text
                
                # Add markup options
                markup_menu = tk.Menu(self.context_menu, tearoff=0)
                for name, markup in self.markup_manager.markups.items():
                    markup_menu.add_command(
                        label=f"{markup.name} ({markup.start_delimiter}...{markup.end_delimiter})",
                        command=lambda n=name: self._apply_markup_to_selection(n)
                    )
                self.context_menu.add_cascade(label="Apply Markup", menu=markup_menu)
                
                # Add "Apply to All" option
                self.context_menu.add_separator()
                apply_all_menu = tk.Menu(self.context_menu, tearoff=0)
                for name, markup in self.markup_manager.markups.items():
                    apply_all_menu.add_command(
                        label=f"{markup.name} to all '{selected_text}'",
                        command=lambda n=name, t=selected_text: self._apply_markup_to_all(n, t)
                    )
                self.context_menu.add_cascade(label="Apply to All Occurrences", menu=apply_all_menu)
                
                # Add remove markup option
                self.context_menu.add_separator()
                self.context_menu.add_command(
                    label="Remove Markup",
                    command=self._remove_markup_from_selection
                )
                self.context_menu.add_command(
                    label="Remove All Markup",
                    command=self._remove_all_markup
                )
            
            # Standard edit options
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Cut", command=self._cut)
            self.context_menu.add_command(label="Copy", command=self._copy)
            self.context_menu.add_command(label="Paste", command=self._paste)
            
            # Show menu
            self.context_menu.post(event.x_root, event.y_root)
            
        except tk.TclError:
            pass
    
    def get_selection(self) -> Optional[TextSelection]:
        """Get current text selection"""
        try:
            start = self.index(tk.SEL_FIRST)
            end = self.index(tk.SEL_LAST)
            text = self.get(start, end)
            return TextSelection(start, end, text)
        except tk.TclError:
            return None
    
    def _apply_markup_to_selection(self, markup_name: str):
        """Apply markup to selected text"""
        selection = self.get_selection()
        if not selection:
            return
        
        # Get the markup
        markup = self.markup_manager.markups.get(markup_name)
        if not markup:
            return
        
        # Apply markup
        marked_text = self.markup_manager.apply_markup(selection.text, markup_name)
        
        # Replace selection
        self.delete(selection.start_index, selection.end_index)
        self.insert(selection.start_index, marked_text)
        
        # Update highlighting
        self._update_markup_highlighting()
    
    def _apply_markup_to_all(self, markup_name: str, target_text: str):
        """Apply markup to all occurrences of text"""
        content = self.get("1.0", tk.END)
        
        # Find all occurrences
        occurrences = []
        start_pos = 0
        while True:
            pos = content.find(target_text, start_pos)
            if pos == -1:
                break
            occurrences.append(pos)
            start_pos = pos + 1
        
        # Apply markup to each occurrence (in reverse order to maintain positions)
        markup = self.markup_manager.markups.get(markup_name)
        if not markup:
            return
        
        marked_text = self.markup_manager.apply_markup(target_text, markup_name)
        offset = 0
        
        for pos in occurrences:
            # Calculate text widget index
            start_index = self.index(f"1.0 + {pos + offset} chars")
            end_index = self.index(f"1.0 + {pos + offset + len(target_text)} chars")
            
            # Replace text
            self.delete(start_index, end_index)
            self.insert(start_index, marked_text)
            
            # Update offset for next replacement
            offset += len(marked_text) - len(target_text)
        
        # Update highlighting
        self._update_markup_highlighting()
    
    def _remove_markup_from_selection(self):
        """Remove markup from selected text"""
        selection = self.get_selection()
        if not selection:
            return
        
        # Check if selection contains markup
        text = selection.text
        for name, markup in self.markup_manager.markups.items():
            if text.startswith(markup.start_delimiter) and text.endswith(markup.end_delimiter):
                # Extract inner text
                inner_text = text[len(markup.start_delimiter):-len(markup.end_delimiter)]
                
                # Replace selection
                self.delete(selection.start_index, selection.end_index)
                self.insert(selection.start_index, inner_text)
                
                # Update highlighting
                self._update_markup_highlighting()
                break
    
    def _remove_all_markup(self):
        """Remove all markup from the entire document"""
        content = self.get("1.0", tk.END)
        
        # Remove all markup patterns
        for name, markup in self.markup_manager.markups.items():
            start = re.escape(markup.start_delimiter)
            end = re.escape(markup.end_delimiter)
            pattern = f"{start}(.*?){end}"
            content = re.sub(pattern, r"\1", content)
        
        # Replace content
        self.delete("1.0", tk.END)
        self.insert("1.0", content)
        
        # Update highlighting
        self._update_markup_highlighting()
    
    def _update_markup_highlighting(self):
        """Update syntax highlighting for markup"""
        # Remove all existing markup tags
        for name in self.markup_manager.markups:
            self.tag_remove(f"markup_{name}", "1.0", tk.END)
        
        # Find and highlight all markup
        content = self.get("1.0", tk.END)
        markup_instances = self.markup_manager.find_all_markup(content)
        
        for name, start_pos, end_pos, inner_text in markup_instances:
            start_index = self.index(f"1.0 + {start_pos} chars")
            end_index = self.index(f"1.0 + {end_pos} chars")
            self.tag_add(f"markup_{name}", start_index, end_index)
    
    def _on_text_change(self, event=None):
        """Handle text change events"""
        self._update_markup_highlighting()
        self._update_word_index()
    
    def _on_selection_change(self, event=None):
        """Handle selection change events"""
        # Could be used to show selection-specific information
        pass
    
    def _update_word_index(self):
        """Update index of word occurrences for quick searching"""
        content = self.get("1.0", tk.END)
        self._word_occurrences.clear()
        
        # Simple word tokenization (could be improved)
        words = re.findall(r'\b\w+\b', content)
        
        for word in set(words):
            occurrences = []
            start_pos = 0
            while True:
                pos = content.find(word, start_pos)
                if pos == -1:
                    break
                # Check if it's a whole word
                if (pos == 0 or not content[pos-1].isalnum()) and \
                   (pos + len(word) >= len(content) or not content[pos + len(word)].isalnum()):
                    start_index = self.index(f"1.0 + {pos} chars")
                    end_index = self.index(f"1.0 + {pos + len(word)} chars")
                    occurrences.append((start_index, end_index))
                start_pos = pos + 1
            
            if occurrences:
                self._word_occurrences[word] = occurrences
    
    def _quick_markup(self, event=None):
        """Quick markup shortcut (Ctrl+M)"""
        selection = self.get_selection()
        if selection:
            # Show quick markup dialog
            self._show_quick_markup_dialog()
    
    def _show_quick_markup_dialog(self):
        """Show a quick dialog for applying markup"""
        dialog = tk.Toplevel(self)
        dialog.title("Quick Markup")
        dialog.geometry("300x200")
        dialog.transient(self)
        
        # Markup selection
        ttk.Label(dialog, text="Select markup type:").pack(pady=10)
        
        markup_var = tk.StringVar(value=list(self.markup_manager.markups.keys())[0])
        for name, markup in self.markup_manager.markups.items():
            ttk.Radiobutton(
                dialog,
                text=f"{name} ({markup.start_delimiter}...{markup.end_delimiter})",
                variable=markup_var,
                value=name
            ).pack(anchor=tk.W, padx=20)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=lambda: [
                self._apply_markup_to_selection(markup_var.get()),
                dialog.destroy()
            ]
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Focus on dialog
        dialog.focus_set()
    
    def _cut(self):
        """Cut selected text"""
        self.event_generate("<<Cut>>")
    
    def _copy(self):
        """Copy selected text"""
        self.event_generate("<<Copy>>")
    
    def _paste(self):
        """Paste from clipboard"""
        self.event_generate("<<Paste>>")
    
    def get_content_with_markup(self) -> str:
        """Get the full content including markup"""
        return self.get("1.0", tk.END).strip()
    
    def get_markup_statistics(self) -> Dict[str, int]:
        """Get statistics about markup usage"""
        content = self.get("1.0", tk.END)
        stats = {}
        
        for name, markup in self.markup_manager.markups.items():
            start = re.escape(markup.start_delimiter)
            end = re.escape(markup.end_delimiter)
            pattern = f"{start}(.*?){end}"
            matches = re.findall(pattern, content)
            stats[name] = len(matches)
        
        return stats


class PromptBuilder:
    """Enhanced prompt builder that includes markup documentation"""
    
    def __init__(self, markup_manager: MarkupManager):
        self.markup_manager = markup_manager
    
    def build_prompt_with_context(
        self,
        content: str,
        mode: str,
        language: str,
        additional_context: Optional[Dict[str, str]] = None
    ) -> str:
        """Build a prompt that includes markup key and context"""
        
        # Start with markup key
        prompt_parts = [
            "DOCUMENT WITH CUSTOM MARKUP",
            "=" * 50,
            "",
            self.markup_manager.get_markup_key(),
            "",
            "INSTRUCTIONS:",
            "The following document contains custom markup as defined above.",
            "Please interpret the markup according to its purpose when processing the text.",
            "",
            "=" * 50,
            ""
        ]
        
        # Add mode-specific instructions
        if mode == "text-to-code":
            prompt_parts.extend([
                f"Convert the following marked-up text to {language} code.",
                "Pay special attention to:",
                "- Text marked with EMPHASIS should be implemented as critical features",
                "- CONTEXT markup provides domain-specific information",
                "- INSTRUCTION markup contains specific implementation requirements",
                "- VARIABLE markup indicates placeholders that should become parameters",
                "- WARNING markup highlights potential issues or edge cases",
                ""
            ])
        else:  # code-to-text
            prompt_parts.extend([
                f"Explain the following {language} code, using the markup to guide your explanation.",
                "When explaining:",
                "- EMPHASIS markup indicates parts requiring detailed explanation",
                "- CONTEXT markup provides background information",
                "- INSTRUCTION markup specifies how to structure the explanation",
                "- VARIABLE markup shows elements to pay special attention to",
                "- WARNING markup indicates critical issues to highlight",
                ""
            ])
        
        # Add additional context if provided
        if additional_context:
            prompt_parts.extend([
                "ADDITIONAL CONTEXT:",
                "=" * 30,
                ""
            ])
            for key, value in additional_context.items():
                prompt_parts.append(f"{key}: {value}")
            prompt_parts.append("")
        
        # Add the actual content
        prompt_parts.extend([
            "CONTENT:",
            "=" * 50,
            "",
            content,
            "",
            "=" * 50
        ])
        
        return "\n".join(prompt_parts)


class MarkupEditorDialog:
    """Dialog for managing custom markup definitions"""
    
    def __init__(self, parent, markup_manager: MarkupManager):
        self.parent = parent
        self.markup_manager = markup_manager
        self.dialog = None
        
    def show(self):
        """Show the markup editor dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Markup Editor")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Existing markups tab
        existing_frame = ttk.Frame(notebook)
        notebook.add(existing_frame, text="Existing Markups")
        self._create_existing_markups_tab(existing_frame)
        
        # New markup tab
        new_frame = ttk.Frame(notebook)
        notebook.add(new_frame, text="Create New")
        self._create_new_markup_tab(new_frame)
        
        # Import/Export tab
        io_frame = ttk.Frame(notebook)
        notebook.add(io_frame, text="Import/Export")
        self._create_import_export_tab(io_frame)
        
        # Close button
        ttk.Button(
            self.dialog,
            text="Close",
            command=self.dialog.destroy
        ).pack(pady=10)
    
    def _create_existing_markups_tab(self, parent):
        """Create tab for managing existing markups"""
        # Listbox for markups
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.markup_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.markup_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.markup_listbox.yview)
        
        # Populate listbox
        self._refresh_markup_list()
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="Edit",
            command=self._edit_selected_markup
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Delete",
            command=self._delete_selected_markup
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Duplicate",
            command=self._duplicate_selected_markup
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_new_markup_tab(self, parent):
        """Create tab for adding new markup"""
        # Form fields
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)
        
        # Start delimiter
        ttk.Label(form_frame, text="Start Delimiter:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_entry = ttk.Entry(form_frame, width=30)
        self.start_entry.grid(row=1, column=1, pady=5)
        
        # End delimiter
        ttk.Label(form_frame, text="End Delimiter:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_entry = ttk.Entry(form_frame, width=30)
        self.end_entry.grid(row=2, column=1, pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(form_frame, width=30)
        self.desc_entry.grid(row=3, column=1, pady=5)
        
        # Color
        ttk.Label(form_frame, text="Text Color:").grid(row=4, column=0, sticky=tk.W, pady=5)
        color_frame = ttk.Frame(form_frame)
        color_frame.grid(row=4, column=1, pady=5, sticky=tk.W)
        
        self.color_var = tk.StringVar(value="#000000")
        self.color_entry = ttk.Entry(color_frame, textvariable=self.color_var, width=10)
        self.color_entry.pack(side=tk.LEFT)
        
        self.color_button = tk.Button(
            color_frame,
            text="    ",
            bg=self.color_var.get(),
            command=self._choose_color
        )
        self.color_button.pack(side=tk.LEFT, padx=5)
        
        # Background color
        ttk.Label(form_frame, text="Background Color:").grid(row=5, column=0, sticky=tk.W, pady=5)
        bg_frame = ttk.Frame(form_frame)
        bg_frame.grid(row=5, column=1, pady=5, sticky=tk.W)
        
        self.bg_var = tk.StringVar(value="")
        self.bg_entry = ttk.Entry(bg_frame, textvariable=self.bg_var, width=10)
        self.bg_entry.pack(side=tk.LEFT)
        
        self.bg_button = tk.Button(
            bg_frame,
            text="    ",
            command=self._choose_bg_color
        )
        self.bg_button.pack(side=tk.LEFT, padx=5)
        
        # Font style
        ttk.Label(form_frame, text="Font Style:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.style_var = tk.StringVar(value="normal")
        style_combo = ttk.Combobox(
            form_frame,
            textvariable=self.style_var,
            values=["normal", "bold", "italic", "underline"],
            width=27
        )
        style_combo.grid(row=6, column=1, pady=5)
        
        # Example
        ttk.Label(form_frame, text="Example:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.example_entry = ttk.Entry(form_frame, width=30)
        self.example_entry.grid(row=7, column=1, pady=5)
        
        # Create button
        ttk.Button(
            form_frame,
            text="Create Markup",
            command=self._create_new_markup
        ).grid(row=8, column=0, columnspan=2, pady=20)
    
    def _create_import_export_tab(self, parent):
        """Create tab for import/export functionality"""
        # Export section
        export_frame = ttk.LabelFrame(parent, text="Export Markups")
        export_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            export_frame,
            text="Export current markup definitions to a JSON file for sharing or backup."
        ).pack(padx=10, pady=10)
        
        ttk.Button(
            export_frame,
            text="Export to JSON",
            command=self._export_markups
        ).pack(pady=10)
        
        # Import section
        import_frame = ttk.LabelFrame(parent, text="Import Markups")
        import_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            import_frame,
            text="Import markup definitions from a JSON file."
        ).pack(padx=10, pady=10)
        
        ttk.Button(
            import_frame,
            text="Import from JSON",
            command=self._import_markups
        ).pack(pady=10)
        
        # Reset section
        reset_frame = ttk.LabelFrame(parent, text="Reset")
        reset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            reset_frame,
            text="Reset all markups to default definitions."
        ).pack(padx=10, pady=10)
        
        ttk.Button(
            reset_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        ).pack(pady=10)
    
    def _refresh_markup_list(self):
        """Refresh the markup listbox"""
        self.markup_listbox.delete(0, tk.END)
        for name, markup in self.markup_manager.markups.items():
            display_text = f"{name}: {markup.start_delimiter}...{markup.end_delimiter}"
            self.markup_listbox.insert(tk.END, display_text)
    
    def _choose_color(self):
        """Open color chooser for text color"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_button.config(bg=color[1])
    
    def _choose_bg_color(self):
        """Open color chooser for background color"""
        from tkinter import colorchooser
        color = colorchooser.askcolor()
        if color[1]:
            self.bg_var.set(color[1])
            self.bg_button.config(bg=color[1])
    
    def _create_new_markup(self):
        """Create a new markup from form data"""
        name = self.name_entry.get().strip()
        if not name:
            tk.messagebox.showwarning("Invalid Input", "Please enter a markup name.")
            return
        
        if name in self.markup_manager.markups:
            tk.messagebox.showwarning("Duplicate Name", "A markup with this name already exists.")
            return
        
        markup = MarkupDefinition(
            name=name,
            start_delimiter=self.start_entry.get() or f"<{name}>",
            end_delimiter=self.end_entry.get() or f"</{name}>",
            description=self.desc_entry.get() or f"Custom {name} markup",
            color=self.color_var.get(),
            background=self.bg_var.get() if self.bg_var.get() else None,
            font_style=self.style_var.get() if self.style_var.get() != "normal" else None,
            example=self.example_entry.get() if self.example_entry.get() else None
        )
        
        self.markup_manager.add_markup(markup)
        tk.messagebox.showinfo("Success", f"Markup '{name}' created successfully.")
        
        # Clear form
        self.name_entry.delete(0, tk.END)
        self.start_entry.delete(0, tk.END)
        self.end_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.example_entry.delete(0, tk.END)
        self.color_var.set("#000000")
        self.bg_var.set("")
        self.style_var.set("normal")
        
        # Refresh list if on that tab
        if hasattr(self, 'markup_listbox'):
            self._refresh_markup_list()
    
    def _edit_selected_markup(self):
        """Edit the selected markup"""
        selection = self.markup_listbox.curselection()
        if not selection:
            return
        
        # Get selected markup name
        selected_text = self.markup_listbox.get(selection[0])
        name = selected_text.split(":")[0]
        
        # TODO: Implement edit dialog
        tk.messagebox.showinfo("Edit", f"Edit functionality for '{name}' would be implemented here.")
    
    def _delete_selected_markup(self):
        """Delete the selected markup"""
        selection = self.markup_listbox.curselection()
        if not selection:
            return
        
        # Get selected markup name
        selected_text = self.markup_listbox.get(selection[0])
        name = selected_text.split(":")[0]
        
        if tk.messagebox.askyesno("Confirm Delete", f"Delete markup '{name}'?"):
            self.markup_manager.remove_markup(name)
            self._refresh_markup_list()
    
    def _duplicate_selected_markup(self):
        """Duplicate the selected markup"""
        selection = self.markup_listbox.curselection()
        if not selection:
            return
        
        # Get selected markup
        selected_text = self.markup_listbox.get(selection[0])
        name = selected_text.split(":")[0]
        original = self.markup_manager.markups.get(name)
        
        if original:
            # Create duplicate with new name
            new_name = f"{name}_copy"
            counter = 1
            while new_name in self.markup_manager.markups:
                new_name = f"{name}_copy{counter}"
                counter += 1
            
            duplicate = MarkupDefinition(
                name=new_name,
                start_delimiter=original.start_delimiter,
                end_delimiter=original.end_delimiter,
                description=f"Copy of {original.description}",
                color=original.color,
                background=original.background,
                font_style=original.font_style,
                example=original.example
            )
            
            self.markup_manager.add_markup(duplicate)
            self._refresh_markup_list()
    
    def _export_markups(self):
        """Export markups to JSON file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            markups_data = {}
            for name, markup in self.markup_manager.markups.items():
                markups_data[name] = {
                    "start_delimiter": markup.start_delimiter,
                    "end_delimiter": markup.end_delimiter,
                    "description": markup.description,
                    "color": markup.color,
                    "background": markup.background,
                    "font_style": markup.font_style,
                    "example": markup.example
                }
            
            with open(filename, 'w') as f:
                json.dump(markups_data, f, indent=2)
            
            tk.messagebox.showinfo("Export Complete", f"Markups exported to {filename}")
    
    def _import_markups(self):
        """Import markups from JSON file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    markups_data = json.load(f)
                
                imported_count = 0
                for name, data in markups_data.items():
                    markup = MarkupDefinition(
                        name=name,
                        start_delimiter=data["start_delimiter"],
                        end_delimiter=data["end_delimiter"],
                        description=data["description"],
                        color=data.get("color", "#000000"),
                        background=data.get("background"),
                        font_style=data.get("font_style"),
                        example=data.get("example")
                    )
                    self.markup_manager.add_markup(markup)
                    imported_count += 1
                
                self._refresh_markup_list()
                tk.messagebox.showinfo(
                    "Import Complete",
                    f"Successfully imported {imported_count} markups."
                )
                
            except Exception as e:
                tk.messagebox.showerror("Import Error", f"Failed to import markups: {str(e)}")
    
    def _reset_to_defaults(self):
        """Reset markups to defaults"""
        if tk.messagebox.askyesno(
            "Confirm Reset",
            "This will remove all custom markups and restore defaults. Continue?"
        ):
            self.markup_manager.markups.clear()
            self.markup_manager._load_default_markups()
            self._refresh_markup_list()


# Integration with the main converter GUI
def integrate_enhanced_editor(converter_gui_instance):
    """Integrate the enhanced editor into the existing converter GUI"""
    
    # Replace the standard text widgets with enhanced editors
    markup_manager = MarkupManager()
    
    # Replace input text widget
    old_input = converter_gui_instance.input_text
    parent = old_input.master
    
    enhanced_input = EnhancedTextEditor(
        parent,
        markup_manager,
        wrap=tk.WORD,
        font=("Consolas", 11)
    )
    enhanced_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    old_input.destroy()
    converter_gui_instance.input_text = enhanced_input
    
    # Add markup editor button to toolbar
    markup_btn = ttk.Button(
        converter_gui_instance.toolbar,
        text="Markup Editor",
        command=lambda: MarkupEditorDialog(
            converter_gui_instance.root,
            markup_manager
        ).show()
    )
    markup_btn.pack(side=tk.LEFT, padx=5)
    
    # Enhance the prompt builder
    enhanced_prompt_builder = PromptBuilder(markup_manager)
    
    # Override the conversion method to use enhanced prompts
    original_perform_conversion = converter_gui_instance._perform_conversion
    
    def enhanced_perform_conversion():
        """Enhanced conversion that includes markup context"""
        # Get content with markup
        input_content = enhanced_input.get_content_with_markup()
        
        # Build enhanced prompt
        mode = converter_gui_instance.current_mode.value
        language = converter_gui_instance.language_var.get()
        
        # Get any additional context from UI
        additional_context = {
            "timestamp": datetime.now().isoformat(),
            "editor_mode": mode,
            "target_language": language,
            "markup_stats": str(enhanced_input.get_markup_statistics())
        }
        
        # Build the full prompt
        full_prompt = enhanced_prompt_builder.build_prompt_with_context(
            input_content,
            mode,
            language,
            additional_context
        )
        
        # Temporarily replace the input text with the enhanced prompt
        original_get = converter_gui_instance.input_text.get
        converter_gui_instance.input_text.get = lambda *args: full_prompt
        
        # Call original conversion
        result = original_perform_conversion()
        
        # Restore original get method
        converter_gui_instance.input_text.get = original_get
        
        return result
    
    converter_gui_instance._perform_conversion = enhanced_perform_conversion
    
    return enhanced_input, markup_manager


# Example usage
if __name__ == "__main__":
    # Demo window
    root = tk.Tk()
    root.title("Enhanced Text Editor Demo")
    root.geometry("800x600")
    
    # Create markup manager and editor
    markup_manager = MarkupManager()
    
    # Add toolbar
    toolbar = ttk.Frame(root)
    toolbar.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Button(
        toolbar,
        text="Markup Editor",
        command=lambda: MarkupEditorDialog(root, markup_manager).show()
    ).pack(side=tk.LEFT, padx=5)
    
    # Create enhanced editor
    editor = EnhancedTextEditor(
        root,
        markup_manager,
        wrap=tk.WORD,
        font=("Consolas", 12)
    )
    editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Add sample text
    sample_text = """Welcome to the Enhanced Editor!

Try right-clicking on any text to apply markup. For example:
- Select this text and apply ///EMPHASIS\\\\\ markup
- Or use <<<CONTEXT>>> markup for background information
- {{INSTRUCTION}} markup for specific requirements
- [[VARIABLES]] for placeholders
- !!!WARNINGS!!! for important notes

You can also:
1. Select a word and apply markup to all occurrences
2. Use Ctrl+M for quick markup
3. Create custom markup types in the Markup Editor
4. Export/import markup definitions

The markup key is automatically included in prompts sent to the AI!"""
    
    editor.insert("1.0", sample_text)
    editor._update_markup_highlighting()
    
    root.mainloop()
