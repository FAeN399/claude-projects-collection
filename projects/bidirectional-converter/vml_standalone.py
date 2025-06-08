#!/usr/bin/env python3
"""
VML Standalone System - Works without anthropic package
======================================================
This version includes all VML functionality without the Claude API integration.
"""

import os
import re
import json
import yaml
import sqlite3
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, font as tkfont
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib

# ============================================================================
# PART 1: VML LANGUAGE DEFINITION AND PARSER
# ============================================================================

class VMLElementType(Enum):
    """Types of elements in VML"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    LINK = "link"
    IMAGE = "image"
    TABLE = "table"
    METADATA = "metadata"
    DIRECTIVE = "directive"
    VARIABLE = "variable"
    TEMPLATE = "template"
    ANNOTATION = "annotation"
    SECTION = "section"
    EMPHASIS = "emphasis"
    CUSTOM = "custom"


@dataclass
class VMLElement:
    """Represents a VML element"""
    type: VMLElementType
    content: str
    attributes: Dict[str, Any]
    children: List['VMLElement'] = None
    line_number: int = 0


class VMLSyntax:
    """Defines the VML syntax rules"""
    
    # Basic markdown-like elements
    HEADING_PATTERN = r'^(#{1,6})\s+(.+)$'
    BOLD_PATTERN = r'\*\*(.+?)\*\*'
    ITALIC_PATTERN = r'\*(.+?)\*'
    CODE_INLINE_PATTERN = r'`(.+?)`'
    
    # Enhanced elements
    DIRECTIVE_PATTERN = r'^@(\w+)(?:\[([^\]]*)\])?\s*(.*)$'
    VARIABLE_PATTERN = r'\$\{([^}]+)\}'
    TEMPLATE_PATTERN = r'%\{([^}]+)\}'
    ANNOTATION_PATTERN = r'\[\[([^\]]+)\]\]'
    METADATA_PATTERN = r'^---\s*$'
    
    # Custom section markers
    SECTION_START_PATTERN = r'^::\s*(\w+)(?:\[([^\]]*)\])?\s*$'
    SECTION_END_PATTERN = r'^::\s*/(\w+)\s*$'
    
    # Advanced features
    INCLUDE_PATTERN = r'^@include\s+"([^"]+)"$'
    MACRO_PATTERN = r'^@macro\s+(\w+)\((.*?)\)\s*{$'
    CONDITION_PATTERN = r'^@if\s+(.+)\s*{$'
    LOOP_PATTERN = r'^@for\s+(\w+)\s+in\s+(.+)\s*{$'
    
    # Table syntax
    TABLE_SEPARATOR = r'^\|[\s\-:|]+\|$'
    TABLE_ROW = r'^\|(.+)\|$'
    
    # Custom markup delimiters
    CUSTOM_MARKUP = {
        'emphasis': ('!!', '!!'),
        'context': ('<~', '~>'),
        'note': ('(*', '*)'),
        'warning': ('/!', '!/'),
        'success': ('/+', '+/'),
        'code_ref': ('@[', ']@'),
    }


class VMLParser:
    """Parser for VML format"""
    
    def __init__(self):
        self.syntax = VMLSyntax()
        self.elements = []
        self.metadata = {}
        self.variables = {}
        self.templates = {}
        
    def parse(self, content: str) -> List[VMLElement]:
        """Parse VML content into elements"""
        lines = content.split('\n')
        self.elements = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            element = None
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Check for metadata block
            if re.match(self.syntax.METADATA_PATTERN, line):
                i = self._parse_metadata_block(lines, i + 1)
                continue
            
            # Check for directives
            directive_match = re.match(self.syntax.DIRECTIVE_PATTERN, line)
            if directive_match:
                element = self._parse_directive(directive_match, i)
                i += 1
            
            # Check for section start
            elif re.match(self.syntax.SECTION_START_PATTERN, line):
                element, i = self._parse_section(lines, i)
            
            # Check for headings
            elif re.match(self.syntax.HEADING_PATTERN, line):
                element = self._parse_heading(line, i)
                i += 1
            
            # Check for table
            elif i + 1 < len(lines) and re.match(self.syntax.TABLE_SEPARATOR, lines[i + 1]):
                element, i = self._parse_table(lines, i)
            
            # Default to paragraph
            else:
                element = self._parse_paragraph(line, i)
                i += 1
            
            if element:
                self.elements.append(element)
        
        return self.elements
    
    def _parse_metadata_block(self, lines: List[str], start_idx: int) -> int:
        """Parse YAML-style metadata block"""
        i = start_idx
        metadata_lines = []
        
        while i < len(lines):
            if re.match(self.syntax.METADATA_PATTERN, lines[i]):
                self._process_metadata(metadata_lines)
                return i + 1
            metadata_lines.append(lines[i])
            i += 1
        
        return i
    
    def _parse_directive(self, match: re.Match, line_num: int) -> VMLElement:
        """Parse a directive element"""
        directive_name = match.group(1)
        params = match.group(2) or ""
        content = match.group(3) or ""
        
        attributes = self._parse_attributes(params)
        
        return VMLElement(
            type=VMLElementType.DIRECTIVE,
            content=content,
            attributes={
                'directive': directive_name,
                'params': attributes
            },
            line_number=line_num
        )
    
    def _parse_section(self, lines: List[str], start_idx: int) -> Tuple[VMLElement, int]:
        """Parse a section with start and end markers"""
        match = re.match(self.syntax.SECTION_START_PATTERN, lines[start_idx])
        section_name = match.group(1)
        params = match.group(2) or ""
        
        attributes = self._parse_attributes(params)
        attributes['name'] = section_name
        
        # Find section content
        content_lines = []
        i = start_idx + 1
        nesting_level = 1
        
        while i < len(lines) and nesting_level > 0:
            if re.match(self.syntax.SECTION_START_PATTERN, lines[i]):
                nesting_level += 1
            elif re.match(self.syntax.SECTION_END_PATTERN, lines[i]):
                end_match = re.match(self.syntax.SECTION_END_PATTERN, lines[i])
                if end_match.group(1) == section_name:
                    nesting_level -= 1
                    if nesting_level == 0:
                        break
            
            content_lines.append(lines[i])
            i += 1
        
        # Parse section content recursively
        section_parser = VMLParser()
        children = section_parser.parse('\n'.join(content_lines))
        
        element = VMLElement(
            type=VMLElementType.SECTION,
            content=section_name,
            attributes=attributes,
            children=children,
            line_number=start_idx
        )
        
        return element, i + 1
    
    def _parse_heading(self, line: str, line_num: int) -> VMLElement:
        """Parse a heading element"""
        match = re.match(self.syntax.HEADING_PATTERN, line)
        level = len(match.group(1))
        content = match.group(2)
        
        # Process inline elements
        content = self._process_inline_elements(content)
        
        return VMLElement(
            type=VMLElementType.HEADING,
            content=content,
            attributes={'level': level},
            line_number=line_num
        )
    
    def _parse_table(self, lines: List[str], start_idx: int) -> Tuple[VMLElement, int]:
        """Parse a table element"""
        headers = self._parse_table_row(lines[start_idx])
        alignment = self._parse_table_alignment(lines[start_idx + 1])
        
        rows = []
        i = start_idx + 2
        
        while i < len(lines) and re.match(self.syntax.TABLE_ROW, lines[i]):
            row = self._parse_table_row(lines[i])
            rows.append(row)
            i += 1
        
        return VMLElement(
            type=VMLElementType.TABLE,
            content="",
            attributes={
                'headers': headers,
                'alignment': alignment,
                'rows': rows
            },
            line_number=start_idx
        ), i
    
    def _parse_paragraph(self, line: str, line_num: int) -> VMLElement:
        """Parse a paragraph element"""
        content = self._process_inline_elements(line)
        
        return VMLElement(
            type=VMLElementType.PARAGRAPH,
            content=content,
            attributes={},
            line_number=line_num
        )
    
    def _process_inline_elements(self, text: str) -> str:
        """Process inline elements like bold, italic, variables, etc."""
        # Process variables
        text = re.sub(self.syntax.VARIABLE_PATTERN, 
                     lambda m: f'<var>{m.group(1)}</var>', text)
        
        # Process templates
        text = re.sub(self.syntax.TEMPLATE_PATTERN,
                     lambda m: f'<template>{m.group(1)}</template>', text)
        
        # Process annotations
        text = re.sub(self.syntax.ANNOTATION_PATTERN,
                     lambda m: f'<annotation>{m.group(1)}</annotation>', text)
        
        # Process custom markup
        for markup_type, (start, end) in self.syntax.CUSTOM_MARKUP.items():
            pattern = f'{re.escape(start)}(.+?){re.escape(end)}'
            text = re.sub(pattern, 
                         lambda m: f'<{markup_type}>{m.group(1)}</{markup_type}>', text)
        
        # Process standard markdown
        text = re.sub(self.syntax.BOLD_PATTERN, r'<b>\1</b>', text)
        text = re.sub(self.syntax.ITALIC_PATTERN, r'<i>\1</i>', text)
        text = re.sub(self.syntax.CODE_INLINE_PATTERN, r'<code>\1</code>', text)
        
        return text
    
    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """Parse attribute string like 'key1=value1, key2=value2'"""
        attributes = {}
        if not attr_string:
            return attributes
        
        pairs = attr_string.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                attributes[key.strip()] = value.strip().strip('"\'')
            else:
                attributes[pair.strip()] = True
        
        return attributes
    
    def _parse_table_row(self, line: str) -> List[str]:
        """Parse a table row"""
        line = line.strip('|')
        return [cell.strip() for cell in line.split('|')]
    
    def _parse_table_alignment(self, line: str) -> List[str]:
        """Parse table alignment row"""
        cells = self._parse_table_row(line)
        alignment = []
        
        for cell in cells:
            if cell.startswith(':') and cell.endswith(':'):
                alignment.append('center')
            elif cell.endswith(':'):
                alignment.append('right')
            else:
                alignment.append('left')
        
        return alignment
    
    def _process_metadata(self, lines: List[str]):
        """Process metadata lines"""
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                self.metadata[key.strip()] = value.strip()


class VMLConverter:
    """Converter for VML format"""
    
    def __init__(self):
        self.parser = VMLParser()
    
    def vml_to_html(self, vml_content: str) -> str:
        """Convert VML to HTML"""
        elements = self.parser.parse(vml_content)
        html_parts = ['<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n']
        
        # Add metadata if present
        if self.parser.metadata:
            if 'title' in self.parser.metadata:
                html_parts.append(f"<title>{self.parser.metadata['title']}</title>\n")
        
        html_parts.append('</head>\n<body>\n')
        
        # Convert elements
        for element in elements:
            html_parts.append(self._element_to_html(element))
        
        html_parts.append('\n</body>\n</html>')
        return ''.join(html_parts)
    
    def _element_to_html(self, element: VMLElement) -> str:
        """Convert a VML element to HTML"""
        if element.type == VMLElementType.HEADING:
            level = element.attributes.get('level', 1)
            return f"<h{level}>{element.content}</h{level}>\n"
        
        elif element.type == VMLElementType.PARAGRAPH:
            return f"<p>{element.content}</p>\n"
        
        elif element.type == VMLElementType.SECTION:
            html = f'<section class="{element.content}">\n'
            if element.children:
                for child in element.children:
                    html += self._element_to_html(child)
            html += '</section>\n'
            return html
        
        elif element.type == VMLElementType.TABLE:
            html = '<table>\n<thead>\n<tr>\n'
            # Headers
            for i, header in enumerate(element.attributes['headers']):
                align = element.attributes['alignment'][i]
                html += f'<th style="text-align: {align}">{header}</th>\n'
            html += '</tr>\n</thead>\n<tbody>\n'
            # Rows
            for row in element.attributes['rows']:
                html += '<tr>\n'
                for i, cell in enumerate(row):
                    align = element.attributes['alignment'][i] if i < len(element.attributes['alignment']) else 'left'
                    html += f'<td style="text-align: {align}">{cell}</td>\n'
                html += '</tr>\n'
            html += '</tbody>\n</table>\n'
            return html
        
        elif element.type == VMLElementType.DIRECTIVE:
            directive = element.attributes['directive']
            if directive == 'include':
                return f'<!-- Include: {element.content} -->\n'
            else:
                return f'<!-- Directive: {directive} -->\n'
        
        else:
            return f"<!-- Unsupported element type: {element.type} -->\n"
    
    def vml_to_markdown(self, vml_content: str) -> str:
        """Convert VML to standard Markdown"""
        elements = self.parser.parse(vml_content)
        md_parts = []
        
        # Add metadata as YAML front matter if present
        if self.parser.metadata:
            md_parts.append('---\n')
            for key, value in self.parser.metadata.items():
                md_parts.append(f"{key}: {value}\n")
            md_parts.append('---\n\n')
        
        # Convert elements
        for element in elements:
            md_parts.append(self._element_to_markdown(element))
        
        return ''.join(md_parts)
    
    def _element_to_markdown(self, element: VMLElement) -> str:
        """Convert a VML element to Markdown"""
        if element.type == VMLElementType.HEADING:
            level = element.attributes.get('level', 1)
            return f"{'#' * level} {element.content}\n\n"
        
        elif element.type == VMLElementType.PARAGRAPH:
            # Convert inline HTML-like tags back to markdown
            content = element.content
            content = re.sub(r'<b>(.+?)</b>', r'**\1**', content)
            content = re.sub(r'<i>(.+?)</i>', r'*\1*', content)
            content = re.sub(r'<code>(.+?)</code>', r'`\1`', content)
            return f"{content}\n\n"
        
        elif element.type == VMLElementType.TABLE:
            md = '| ' + ' | '.join(element.attributes['headers']) + ' |\n'
            md += '| ' + ' | '.join(['---' if align == 'left' else 
                                    ':---:' if align == 'center' else 
                                    '---:' for align in element.attributes['alignment']]) + ' |\n'
            for row in element.attributes['rows']:
                md += '| ' + ' | '.join(row) + ' |\n'
            return md + '\n'
        
        else:
            return f"<!-- {element.type}: {element.content} -->\n\n"


class VMLLanguageHandler:
    """Handler for VML in the bidirectional converter"""
    
    def __init__(self):
        self.parser = VMLParser()
        self.converter = VMLConverter()
    
    def validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """Validate VML syntax"""
        errors = []
        
        try:
            elements = self.parser.parse(code)
            
            # Check for basic syntax issues
            lines = code.split('\n')
            open_sections = []
            
            for i, line in enumerate(lines):
                # Check section matching
                if match := re.match(r'^::\s*(\w+)', line):
                    if match.group(0).endswith('/'):
                        # Closing tag
                        section_name = match.group(1)
                        if not open_sections or open_sections[-1] != section_name:
                            errors.append(f"Line {i+1}: Unmatched section closing tag: {section_name}")
                        else:
                            open_sections.pop()
                    else:
                        # Opening tag
                        open_sections.append(match.group(1))
                
                # Check for unclosed markup
                for markup_type, (start, end) in VMLSyntax.CUSTOM_MARKUP.items():
                    if line.count(start) != line.count(end):
                        errors.append(f"Line {i+1}: Unclosed {markup_type} markup")
            
            if open_sections:
                errors.append(f"Unclosed sections: {', '.join(open_sections)}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Parser error: {str(e)}")
            return False, errors
    
    def format_code(self, code: str) -> str:
        """Format VML code for consistency"""
        try:
            elements = self.parser.parse(code)
            formatted_lines = []
            
            # Add metadata if present
            if self.parser.metadata:
                formatted_lines.append('---')
                for key, value in self.parser.metadata.items():
                    formatted_lines.append(f"{key}: {value}")
                formatted_lines.append('---\n')
            
            # Format elements (simplified)
            lines = code.split('\n')
            for line in lines:
                # Skip metadata block
                if line.strip() == '---':
                    continue
                # Ensure consistent spacing around headers
                if re.match(r'^#{1,6}\s+', line):
                    formatted_lines.append(line.strip())
                    formatted_lines.append('')  # Empty line after headers
                else:
                    formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except:
            # If parsing fails, return original
            return code


# ============================================================================
# PART 2: STANDALONE GUI APPLICATION
# ============================================================================

class VMLStandaloneGUI:
    """Standalone GUI for VML without API dependencies"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VML Editor and Converter")
        self.root.geometry("1200x800")
        
        self.vml_handler = VMLLanguageHandler()
        
        # Setup GUI
        self._setup_styles()
        self._create_menu()
        self._create_main_interface()
        self._create_status_bar()
        
        # Bind keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
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
        
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_document, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save...", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy", command=self._copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._paste_text, accelerator="Ctrl+V")
        edit_menu.add_command(label="Clear All", command=self._clear_all, accelerator="Ctrl+L")
        
        # VML menu
        vml_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="VML", menu=vml_menu)
        vml_menu.add_command(label="Validate", command=self._validate_vml)
        vml_menu.add_command(label="Format", command=self._format_vml)
        vml_menu.add_separator()
        vml_menu.add_command(label="Convert to HTML", command=lambda: self._convert_vml("html"))
        vml_menu.add_command(label="Convert to Markdown", command=lambda: self._convert_vml("markdown"))
        
        # Insert menu
        insert_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Insert", menu=insert_menu)
        insert_menu.add_command(label="Variable ${}", command=lambda: self._insert_text("${}"))
        insert_menu.add_command(label="Template %{}", command=lambda: self._insert_text("%{}"))
        insert_menu.add_command(label="Section", command=self._insert_section)
        insert_menu.add_command(label="Table", command=self._insert_table)
        insert_menu.add_separator()
        insert_menu.add_command(label="Emphasis !!", command=lambda: self._wrap_text("!!", "!!"))
        insert_menu.add_command(label="Context <~", command=lambda: self._wrap_text("<~", "~>"))
        insert_menu.add_command(label="Note (*", command=lambda: self._wrap_text("(*", "*)"))
        insert_menu.add_command(label="Warning /!", command=lambda: self._wrap_text("/!", "!/"))
        insert_menu.add_command(label="Success /+", command=lambda: self._wrap_text("/+", "+/"))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="VML Syntax Guide", command=self._show_syntax_guide)
        help_menu.add_command(label="Examples", command=self._show_examples)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_main_interface(self):
        """Create the main interface"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick action buttons
        ttk.Button(toolbar, text="Validate", command=self._validate_vml).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Format", command=self._format_vml).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="→ HTML", command=lambda: self._convert_vml("html")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="→ Markdown", command=lambda: self._convert_vml("markdown")).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Quick insert buttons
        ttk.Button(toolbar, text="${}", command=lambda: self._insert_text("${}")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="%{}", command=lambda: self._insert_text("%{}")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="!!", command=lambda: self._wrap_text("!!", "!!")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="<~", command=lambda: self._wrap_text("<~", "~>")).pack(side=tk.LEFT, padx=2)
        
        # Main content area
        content = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Editor panel
        editor_frame = ttk.LabelFrame(content, text="VML Editor")
        content.add(editor_frame, weight=2)
        
        # Editor text area
        self.editor_text = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.WORD, font=("Consolas", 11),
            undo=True, maxundo=-1
        )
        self.editor_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Apply syntax highlighting
        self._setup_syntax_highlighting()
        
        # Preview panel
        preview_frame = ttk.LabelFrame(content, text="Preview / Output")
        content.add(preview_frame, weight=1)
        
        # Preview notebook
        self.preview_notebook = ttk.Notebook(preview_frame)
        self.preview_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Parsed structure tab
        structure_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(structure_tab, text="Structure")
        
        self.structure_tree = ttk.Treeview(structure_tab, show="tree")
        structure_scroll = ttk.Scrollbar(structure_tab, orient=tk.VERTICAL, command=self.structure_tree.yview)
        self.structure_tree.configure(yscrollcommand=structure_scroll.set)
        self.structure_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        structure_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # HTML output tab
        html_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(html_tab, text="HTML")
        
        self.html_text = scrolledtext.ScrolledText(
            html_tab, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.html_text.pack(fill=tk.BOTH, expand=True)
        
        # Markdown output tab
        md_tab = ttk.Frame(self.preview_notebook)
        self.preview_notebook.add(md_tab, text="Markdown")
        
        self.md_text = scrolledtext.ScrolledText(
            md_tab, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.md_text.pack(fill=tk.BOTH, expand=True)
        
        # Load example content
        self._load_example_content()
        
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
        
        # Cursor position
        self.position_var = tk.StringVar(value="Line 1, Col 1")
        self.position_label = ttk.Label(
            self.status_bar, textvariable=self.position_var
        )
        self.position_label.pack(side=tk.RIGHT, padx=5)
        
        # Update cursor position
        self.editor_text.bind("<KeyRelease>", self._update_cursor_position)
        self.editor_text.bind("<ButtonRelease>", self._update_cursor_position)
        
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Control-n>", lambda e: self._new_document())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-l>", lambda e: self._clear_all())
        self.root.bind("<F5>", lambda e: self._validate_vml())
        self.root.bind("<F6>", lambda e: self._format_vml())
        
    def _setup_syntax_highlighting(self):
        """Setup basic syntax highlighting for VML"""
        # Define tag styles
        self.editor_text.tag_config("heading", foreground="#1976D2", font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("directive", foreground="#0066CC", font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("variable", foreground="#9C27B0", background="#F3E5F5")
        self.editor_text.tag_config("template", foreground="#00897B", background="#E0F2F1")
        self.editor_text.tag_config("section", foreground="#E65100", font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("emphasis", foreground="#D32F2F", font=("Consolas", 11, "bold"))
        self.editor_text.tag_config("context", foreground="#1976D2", background="#E3F2FD")
        self.editor_text.tag_config("warning", foreground="#FF6F00", background="#FFF3E0")
        self.editor_text.tag_config("success", foreground="#2E7D32", background="#E8F5E9")
        
        # Bind highlighting to text changes
        self.editor_text.bind("<KeyRelease>", self._apply_syntax_highlighting)
        
    def _apply_syntax_highlighting(self, event=None):
        """Apply syntax highlighting to the text"""
        # Remove all existing tags
        for tag in ["heading", "directive", "variable", "template", "section", 
                   "emphasis", "context", "warning", "success"]:
            self.editor_text.tag_remove(tag, "1.0", tk.END)
        
        content = self.editor_text.get("1.0", tk.END)
        
        # Highlight patterns
        patterns = {
            "heading": r'^#{1,6}\s+.+$',
            "directive": r'@\w+(?:\[[^\]]*\])?',
            "variable": r'\$\{[^}]+\}',
            "template": r'%\{[^}]+\}',
            "section": r'^::\s*/?\\w+(?:\[[^\]]*\])?',
            "emphasis": r'!![^!]+!!',
            "context": r'<~[^~]+~>',
            "warning": r'/![^!]+!/',
            "success": r'/\+[^+]+\+/',
        }
        
        for tag_name, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                self.editor_text.tag_add(tag_name, start_idx, end_idx)
        
        # Also update the structure view
        self._update_structure_view()
    
    def _update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        position = self.editor_text.index(tk.INSERT)
        line, col = position.split('.')
        self.position_var.set(f"Line {line}, Col {int(col) + 1}")
    
    def _update_structure_view(self):
        """Update the structure tree view"""
        # Clear existing items
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        # Parse VML content
        content = self.editor_text.get("1.0", tk.END)
        try:
            elements = self.vml_handler.parser.parse(content)
            
            # Add metadata if present
            if self.vml_handler.parser.metadata:
                meta_node = self.structure_tree.insert("", "end", text="Metadata", open=True)
                for key, value in self.vml_handler.parser.metadata.items():
                    self.structure_tree.insert(meta_node, "end", text=f"{key}: {value}")
            
            # Add elements
            for element in elements:
                self._add_element_to_tree("", element)
                
        except Exception as e:
            self.structure_tree.insert("", "end", text=f"Parse error: {str(e)}")
    
    def _add_element_to_tree(self, parent: str, element: VMLElement):
        """Add an element to the structure tree"""
        # Create node text
        if element.type == VMLElementType.HEADING:
            text = f"H{element.attributes.get('level', 1)}: {element.content[:50]}"
        elif element.type == VMLElementType.SECTION:
            text = f"Section: {element.content}"
        elif element.type == VMLElementType.DIRECTIVE:
            text = f"@{element.attributes['directive']}"
        else:
            text = f"{element.type.value}: {element.content[:50]}"
        
        # Insert node
        node = self.structure_tree.insert(parent, "end", text=text, open=True)
        
        # Add children if any
        if element.children:
            for child in element.children:
                self._add_element_to_tree(node, child)
    
    def _new_document(self):
        """Create a new document"""
        self.editor_text.delete("1.0", tk.END)
        self.html_text.delete("1.0", tk.END)
        self.md_text.delete("1.0", tk.END)
        self.status_var.set("New document")
    
    def _open_file(self):
        """Open a VML file"""
        file_path = filedialog.askopenfilename(
            title="Open VML File",
            filetypes=[("VML Files", "*.vml"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor_text.delete("1.0", tk.END)
                self.editor_text.insert("1.0", content)
                self.status_var.set(f"Opened: {Path(file_path).name}")
                self._apply_syntax_highlighting()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {str(e)}")
    
    def _save_file(self):
        """Save the current document"""
        file_path = filedialog.asksaveasfilename(
            title="Save VML File",
            defaultextension=".vml",
            filetypes=[("VML Files", "*.vml"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                content = self.editor_text.get("1.0", tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_var.set(f"Saved: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def _clear_all(self):
        """Clear all text areas"""
        self.editor_text.delete("1.0", tk.END)
        self.html_text.delete("1.0", tk.END)
        self.md_text.delete("1.0", tk.END)
        self.status_var.set("Cleared")
    
    def _copy_text(self):
        """Copy selected text"""
        try:
            text = self.editor_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Copied to clipboard")
        except tk.TclError:
            pass
    
    def _paste_text(self):
        """Paste from clipboard"""
        try:
            text = self.root.clipboard_get()
            self.editor_text.insert(tk.INSERT, text)
        except tk.TclError:
            pass
    
    def _validate_vml(self):
        """Validate VML syntax"""
        content = self.editor_text.get("1.0", tk.END)
        is_valid, errors = self.vml_handler.validate_syntax(content)
        
        if is_valid:
            self.status_var.set("✓ Valid VML syntax")
            messagebox.showinfo("Validation", "VML syntax is valid!")
        else:
            self.status_var.set("✗ Invalid VML syntax")
            error_msg = "Validation errors:\n\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n\n... and {len(errors) - 10} more errors"
            messagebox.showerror("Validation Error", error_msg)
    
    def _format_vml(self):
        """Format VML code"""
        content = self.editor_text.get("1.0", tk.END)
        formatted = self.vml_handler.format_code(content)
        
        self.editor_text.delete("1.0", tk.END)
        self.editor_text.insert("1.0", formatted)
        self._apply_syntax_highlighting()
        self.status_var.set("Formatted VML")
    
    def _convert_vml(self, target_format: str):
        """Convert VML to specified format"""
        content = self.editor_text.get("1.0", tk.END)
        
        try:
            if target_format == "html":
                result = self.vml_handler.converter.vml_to_html(content)
                self.html_text.delete("1.0", tk.END)
                self.html_text.insert("1.0", result)
                self.preview_notebook.select(1)  # Switch to HTML tab
                self.status_var.set("Converted to HTML")
            
            elif target_format == "markdown":
                result = self.vml_handler.converter.vml_to_markdown(content)
                self.md_text.delete("1.0", tk.END)
                self.md_text.insert("1.0", result)
                self.preview_notebook.select(2)  # Switch to Markdown tab
                self.status_var.set("Converted to Markdown")
                
        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to convert: {str(e)}")
    
    def _insert_text(self, text: str):
        """Insert text at cursor position"""
        self.editor_text.insert(tk.INSERT, text)
        # Move cursor inside braces if applicable
        if text.endswith("}"):
            pos = self.editor_text.index(tk.INSERT)
            self.editor_text.mark_set(tk.INSERT, f"{pos}-1c")
    
    def _wrap_text(self, start: str, end: str):
        """Wrap selected text with markers"""
        try:
            sel_text = self.editor_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.editor_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.editor_text.insert(tk.INSERT, f"{start}{sel_text}{end}")
        except tk.TclError:
            # No selection, just insert markers
            self.editor_text.insert(tk.INSERT, f"{start}{end}")
            pos = self.editor_text.index(tk.INSERT)
            self.editor_text.mark_set(tk.INSERT, f"{pos}-{len(end)}c")
    
    def _insert_section(self):
        """Insert a section template"""
        template = ":: section[name=example]\n\nSection content here\n\n:: /section"
        self.editor_text.insert(tk.INSERT, template)
    
    def _insert_table(self):
        """Insert a table template"""
        template = """| Header 1 | Header 2 | Header 3 |
|----------|:--------:|---------:|
| Left     | Center   | Right    |
| Data 1   | Data 2   | Data 3   |"""
        self.editor_text.insert(tk.INSERT, template)
    
    def _load_example_content(self):
        """Load example VML content"""
        example = """---
title: VML Example Document
author: VML Editor
version: 1.0
date: 2024-01-20
---

# Welcome to VML Editor

This is an example of **VML** (Versatile Markup Language) with !!live editing!! and <~syntax highlighting~>.

## Features

VML supports various markup elements:

- **Standard Markdown**: Bold, *italic*, `code`
- **Variables**: ${user_name}, ${current_date}
- **Templates**: %{header_template}, %{footer_template}
- **Custom Markup**: 
  - !!Emphasis!! for important text
  - <~Context~> for background info
  - (*Notes*) for side comments
  - /!Warnings!/ for cautions
  - /+Success+/ for positive messages

:: section[type=example, id=demo]
### Example Section

This is a [[structured section]] with special properties.

@directive[type=highlight, color=blue]
This content is marked with a directive.

| Feature | Status | Notes |
|---------|:------:|-------|
| Parser | /+Complete+/ | Full VML syntax support |
| Converter | /+Complete+/ | HTML and Markdown output |
| Validator | /+Complete+/ | Syntax checking |
| Editor | /+Active+/ | With syntax highlighting |

:: /section

## Code Examples

@code[lang=python]
```python
def greet(name):
    return f"Hello, {name}!"
```

## Try It Yourself!

1. Edit this document
2. Click **Validate** to check syntax
3. Click **Format** to clean up formatting
4. Convert to **HTML** or **Markdown**
5. Use the **Insert** menu for quick markup

/+Have fun exploring VML!+/"""
        
        self.editor_text.insert("1.0", example)
        self._apply_syntax_highlighting()
    
    def _show_syntax_guide(self):
        """Show VML syntax guide"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("VML Syntax Guide")
        guide_window.geometry("600x500")
        
        guide_text = scrolledtext.ScrolledText(
            guide_window, wrap=tk.WORD, font=("Consolas", 10)
        )
        guide_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        guide_content = """VML SYNTAX GUIDE
================

BASIC ELEMENTS
--------------
# Heading 1
## Heading 2
### Heading 3

**Bold text**
*Italic text*
`inline code`

CUSTOM MARKUP
-------------
!!Emphasis!! - Important text
<~Context~> - Background information
(*Note*) - Side notes
/!Warning!/ - Cautions
/+Success+/ - Positive messages
@[Code Ref]@ - Code references
[[Annotation]] - Metadata annotations

VARIABLES & TEMPLATES
--------------------
${variable_name} - Variable placeholder
%{template_name} - Template reference

DIRECTIVES
----------
@directive[param1=value1, param2=value2]
Content affected by directive

SECTIONS
--------
:: section[type=example, id=unique]
Section content here
:: /section

METADATA
--------
---
title: Document Title
author: Your Name
version: 1.0
---

TABLES
------
| Column 1 | Column 2 | Column 3 |
|----------|:--------:|---------:|
| Left     | Center   | Right    |

ADVANCED
--------
@if condition {
  Conditional content
}

@for item in list {
  Repeated content
}

@include "filename.vml"
"""
        
        guide_text.insert("1.0", guide_content)
        guide_text.config(state=tk.DISABLED)
    
    def _show_examples(self):
        """Show VML examples"""
        examples_window = tk.Toplevel(self.root)
        examples_window.title("VML Examples")
        examples_window.geometry("700x500")
        
        notebook = ttk.Notebook(examples_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Example 1: Documentation
        doc_frame = ttk.Frame(notebook)
        notebook.add(doc_frame, text="Documentation")
        
        doc_text = scrolledtext.ScrolledText(doc_frame, wrap=tk.WORD, font=("Consolas", 9))
        doc_text.pack(fill=tk.BOTH, expand=True)
        doc_text.insert("1.0", """---
title: API Documentation
version: 2.0
---

# REST API Reference

## Authentication

All endpoints require [[Bearer token]] authentication.

:: section[type=endpoint]
### GET /api/users/{id}

Retrieves user information.

**Parameters:**
- `id` - User ID (required)

**Response** /+200 OK+/:
```json
{
  "id": "${user_id}",
  "name": "${user_name}",
  "email": "${user_email}"
}
```

**Errors:**
- /!401 Unauthorized!/ - Invalid token
- /!404 Not Found!/ - User not found
:: /section""")
        
        # Example 2: Tutorial
        tutorial_frame = ttk.Frame(notebook)
        notebook.add(tutorial_frame, text="Tutorial")
        
        tutorial_text = scrolledtext.ScrolledText(tutorial_frame, wrap=tk.WORD, font=("Consolas", 9))
        tutorial_text.pack(fill=tk.BOTH, expand=True)
        tutorial_text.insert("1.0", """---
title: VML Tutorial
type: tutorial
---

# Learning VML

:: section[class=lesson, number=1]
## Lesson 1: Basic Syntax

VML combines !!simplicity!! with <~powerful features~>.

### Try This:

1. Create a heading with `#`
2. Add **bold** and *italic* text
3. Insert a ${variable}
4. Create a (*note*)

@task[difficulty=easy]
Write a paragraph using all basic elements.
:: /section

/+Continue to Lesson 2 when ready!+/""")
        
        # Example 3: Configuration
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        
        config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.WORD, font=("Consolas", 9))
        config_text.pack(fill=tk.BOTH, expand=True)
        config_text.insert("1.0", """---
application: MyApp
environment: production
---

# Application Configuration

:: section[type=database]
## Database Settings

- Host: ${DB_HOST}
- Port: ${DB_PORT}
- Database: ${DB_NAME}

<~Connection pooling is enabled by default~>

/!Warning: Ensure credentials are secure!/
:: /section

:: section[type=cache]
## Cache Configuration

@config[component=redis]
%{redis_config_template}

(*Note: Cache TTL is set to 1 hour*)
:: /section""")
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About VML Editor",
            "VML Editor and Converter\n" +
            "Version 1.0.0\n\n" +
            "A standalone editor for VML (Versatile Markup Language)\n" +
            "with syntax highlighting, validation, and conversion features.\n\n" +
            "No API dependencies required!"
        )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    root = tk.Tk()
    app = VMLStandaloneGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()