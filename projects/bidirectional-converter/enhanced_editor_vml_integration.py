#!/usr/bin/env python3
"""
Enhanced Editor Integration for VML Support
------------------------------------------
Extends the enhanced editor with VML-specific markup types and features.
"""

from enhanced_editor import MarkupDefinition, MarkupManager

def create_vml_markup_definitions():
    """Create VML-specific markup definitions for the enhanced editor"""
    
    vml_markups = [
        # VML-specific markup types
        MarkupDefinition(
            name="vml_directive",
            start_delimiter="@",
            end_delimiter="",
            description="VML directive (e.g., @include, @macro, @if)",
            color="#0066CC",
            font_style="bold",
            example="@directive[params] content"
        ),
        
        MarkupDefinition(
            name="vml_variable",
            start_delimiter="${",
            end_delimiter="}",
            description="VML variable placeholder",
            color="#9C27B0",
            background="#F3E5F5",
            example="${variable_name}"
        ),
        
        MarkupDefinition(
            name="vml_template",
            start_delimiter="%{",
            end_delimiter="}",
            description="VML template reference",
            color="#00897B",
            background="#E0F2F1",
            example="%{template_name}"
        ),
        
        MarkupDefinition(
            name="vml_section",
            start_delimiter="::",
            end_delimiter="",
            description="VML section marker",
            color="#E65100",
            font_style="bold",
            example=":: section_name[params]"
        ),
        
        MarkupDefinition(
            name="vml_emphasis",
            start_delimiter="!!",
            end_delimiter="!!",
            description="VML emphasis markup",
            color="#D32F2F",
            font_style="bold",
            example="!!important text!!"
        ),
        
        MarkupDefinition(
            name="vml_context",
            start_delimiter="<~",
            end_delimiter="~>",
            description="VML context information",
            color="#1976D2",
            background="#E3F2FD",
            example="<~background info~>"
        ),
        
        MarkupDefinition(
            name="vml_note",
            start_delimiter="(*",
            end_delimiter="*)",
            description="VML side note",
            color="#616161",
            font_style="italic",
            example="(*side note*)"
        ),
        
        MarkupDefinition(
            name="vml_warning",
            start_delimiter="/!",
            end_delimiter="!/",
            description="VML warning message",
            color="#FF6F00",
            background="#FFF3E0",
            font_style="bold",
            example="/!warning text!/"
        ),
        
        MarkupDefinition(
            name="vml_success",
            start_delimiter="/+",
            end_delimiter="+/",
            description="VML success message",
            color="#2E7D32",
            background="#E8F5E9",
            example="/+success message+/"
        ),
        
        MarkupDefinition(
            name="vml_coderef",
            start_delimiter="@[",
            end_delimiter="]@",
            description="VML code reference",
            color="#311B92",
            background="#EDE7F6",
            font_style="italic",
            example="@[function_name]@"
        ),
        
        MarkupDefinition(
            name="vml_annotation",
            start_delimiter="[[",
            end_delimiter="]]",
            description="VML annotation",
            color="#004D40",
            background="#E0F2F1",
            example="[[annotation text]]"
        ),
        
        MarkupDefinition(
            name="vml_metadata",
            start_delimiter="---",
            end_delimiter="---",
            description="VML metadata block",
            color="#37474F",
            background="#ECEFF1",
            example="---\nkey: value\n---"
        )
    ]
    
    return vml_markups


def integrate_vml_with_enhanced_editor(editor_instance, markup_manager):
    """Integrate VML markup types with an existing enhanced editor instance"""
    
    # Add VML-specific markups
    vml_markups = create_vml_markup_definitions()
    for markup in vml_markups:
        markup_manager.add_markup(markup)
    
    # Update the editor's tag configuration
    editor_instance._setup_tags()
    
    # Add VML-specific context menu items
    original_show_context_menu = editor_instance._show_context_menu
    
    def enhanced_show_context_menu(event):
        """Enhanced context menu with VML-specific options"""
        # Call original method
        original_show_context_menu(event)
        
        # Add VML-specific menu items if text is selected
        if editor_instance.context_menu and editor_instance.get_selection():
            # Add separator
            editor_instance.context_menu.add_separator()
            
            # Add VML quick actions submenu
            vml_menu = tk.Menu(editor_instance.context_menu, tearoff=0)
            
            # Quick VML conversions
            selection = editor_instance.get_selection()
            if selection:
                vml_menu.add_command(
                    label="Convert to VML Variable",
                    command=lambda: editor_instance._apply_markup_to_selection("vml_variable")
                )
                vml_menu.add_command(
                    label="Convert to VML Template",
                    command=lambda: editor_instance._apply_markup_to_selection("vml_template")
                )
                vml_menu.add_command(
                    label="Mark as VML Annotation",
                    command=lambda: editor_instance._apply_markup_to_selection("vml_annotation")
                )
                
            editor_instance.context_menu.add_cascade(label="VML Quick Actions", menu=vml_menu)
    
    # Replace the context menu method
    editor_instance._show_context_menu = enhanced_show_context_menu
    
    return editor_instance


def create_vml_enhanced_editor(parent, **kwargs):
    """Create a new enhanced editor with VML support built-in"""
    from enhanced_editor import EnhancedTextEditor
    import tkinter as tk
    
    # Create markup manager with VML definitions
    markup_manager = MarkupManager()
    
    # Add VML markups
    vml_markups = create_vml_markup_definitions()
    for markup in vml_markups:
        markup_manager.add_markup(markup)
    
    # Create enhanced editor
    editor = EnhancedTextEditor(parent, markup_manager, **kwargs)
    
    # Add VML-specific keyboard shortcuts
    editor.bind("<Control-d>", lambda e: _insert_vml_directive(editor))
    editor.bind("<Control-v>", lambda e: _insert_vml_variable(editor))
    editor.bind("<Control-t>", lambda e: _insert_vml_template(editor))
    
    return editor, markup_manager


def _insert_vml_directive(editor):
    """Insert a VML directive at cursor position"""
    editor.insert(tk.INSERT, "@directive[params] ")
    # Move cursor back to edit directive name
    editor.mark_set(tk.INSERT, f"{tk.INSERT}-16c")


def _insert_vml_variable(editor):
    """Insert a VML variable at cursor position"""
    editor.insert(tk.INSERT, "${}")
    # Move cursor inside braces
    editor.mark_set(tk.INSERT, f"{tk.INSERT}-1c")


def _insert_vml_template(editor):
    """Insert a VML template at cursor position"""
    editor.insert(tk.INSERT, "%{}")
    # Move cursor inside braces
    editor.mark_set(tk.INSERT, f"{tk.INSERT}-1c")


# VML syntax highlighting patterns
VML_SYNTAX_PATTERNS = {
    'directive': r'@\w+(?:\[[^\]]*\])?',
    'variable': r'\$\{[^}]+\}',
    'template': r'%\{[^}]+\}',
    'section_start': r'^::\s*\w+(?:\[[^\]]*\])?',
    'section_end': r'^::\s*/\w+',
    'annotation': r'\[\[[^\]]+\]\]',
    'emphasis': r'!![^!]+!!',
    'context': r'<~[^~]+~>',
    'note': r'\(\*[^*]+\*\)',
    'warning': r'/![^!]+!/',
    'success': r'/\+[^+]+\+/',
    'coderef': r'@\[[^\]]+\]@',
    'heading': r'^#{1,6}\s+.+$',
    'metadata': r'^---\s*$',
}


def apply_vml_syntax_highlighting(text_widget):
    """Apply VML-specific syntax highlighting to a text widget"""
    import re
    
    # Define tag configurations for VML syntax
    syntax_tags = {
        'directive': {'foreground': '#0066CC', 'font': ('Consolas', 11, 'bold')},
        'variable': {'foreground': '#9C27B0', 'background': '#F3E5F5'},
        'template': {'foreground': '#00897B', 'background': '#E0F2F1'},
        'section_start': {'foreground': '#E65100', 'font': ('Consolas', 11, 'bold')},
        'section_end': {'foreground': '#E65100', 'font': ('Consolas', 11, 'bold')},
        'annotation': {'foreground': '#004D40', 'background': '#E0F2F1'},
        'heading': {'foreground': '#1A237E', 'font': ('Consolas', 14, 'bold')},
    }
    
    # Configure tags
    for tag_name, config in syntax_tags.items():
        text_widget.tag_configure(f"vml_{tag_name}", **config)
    
    # Apply highlighting
    content = text_widget.get("1.0", tk.END)
    
    for pattern_name, pattern in VML_SYNTAX_PATTERNS.items():
        for match in re.finditer(pattern, content, re.MULTILINE):
            start_idx = text_widget.index(f"1.0 + {match.start()} chars")
            end_idx = text_widget.index(f"1.0 + {match.end()} chars")
            text_widget.tag_add(f"vml_{pattern_name}", start_idx, end_idx)


# Example usage
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk
    
    # Create demo window
    root = tk.Tk()
    root.title("VML Enhanced Editor Demo")
    root.geometry("900x700")
    
    # Create toolbar
    toolbar = ttk.Frame(root)
    toolbar.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(toolbar, text="VML Enhanced Editor with Custom Markup Support").pack(side=tk.LEFT, padx=10)
    
    # Create VML enhanced editor
    editor, markup_manager = create_vml_enhanced_editor(
        root,
        wrap=tk.WORD,
        font=("Consolas", 11)
    )
    editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Add sample VML content
    sample_vml = """---
title: VML Enhanced Editor Demo
author: AI Assistant
version: 1.0
---

# VML Document with Enhanced Markup

This editor supports all VML features with !!visual highlighting!! and <~contextual information~>.

## Features Demonstration

@directive[type=demo, style=enhanced]
The editor recognizes VML directives and highlights them appropriately.

### Variables and Templates

- Variables: ${user_name}, ${current_date}
- Templates: %{header_template}, %{footer_template}
- Code references: @[main_function]@, @[helper_module]@

:: section[class=example, highlight=true]
## Example Section

This is a [[special section]] with enhanced formatting.

(*Note: All VML syntax is automatically highlighted*)

| Feature | Status | Description |
|---------|:------:|-------------|
| Directives | /+Active+/ | Full support |
| Variables | /+Active+/ | ${var} syntax |
| Sections | /+Active+/ | :: markers |

:: /section

### Markup Types

1. !!Emphasis!! - For important text
2. <~Context~> - For background information
3. (*Notes*) - For side notes
4. /!Warnings!/ - For cautions
5. /+Success+/ - For positive messages
6. [[Annotations]] - For metadata

@include "additional_features.vml"
"""
    
    # Insert sample content
    editor.insert("1.0", sample_vml)
    
    # Apply VML syntax highlighting
    apply_vml_syntax_highlighting(editor)
    
    # Update markup highlighting
    editor._update_markup_highlighting()
    
    # Status bar
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    status_label = ttk.Label(status_frame, text="Ready - VML Enhanced Editor")
    status_label.pack(side=tk.LEFT, padx=5)
    
    # Add buttons for VML actions
    button_frame = ttk.Frame(toolbar)
    button_frame.pack(side=tk.RIGHT, padx=5)
    
    ttk.Button(
        button_frame,
        text="Insert Variable",
        command=lambda: editor.insert(tk.INSERT, "${}")
    ).pack(side=tk.LEFT, padx=2)
    
    ttk.Button(
        button_frame,
        text="Insert Template",
        command=lambda: editor.insert(tk.INSERT, "%{}")
    ).pack(side=tk.LEFT, padx=2)
    
    ttk.Button(
        button_frame,
        text="Insert Section",
        command=lambda: editor.insert(tk.INSERT, ":: section[]\n\n:: /section")
    ).pack(side=tk.LEFT, padx=2)
    
    root.mainloop()