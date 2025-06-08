#!/usr/bin/env python3
"""
Combined VML Bidirectional Converter System
==========================================
All components in one file for easy reference and use.
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
import anthropic
from anthropic import AsyncAnthropic
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
    
    def get_language_info(self) -> Dict[str, Any]:
        """Get language information for registration"""
        return {
            'name': 'VML',
            'full_name': 'Versatile Markup Language',
            'extensions': ['.vml', '.vmark'],
            'description': 'A versatile markup language combining Markdown, AML, and custom features',
            'example': self.get_example_code()
        }
    
    def get_example_code(self) -> str:
        """Get example VML code"""
        return """---
title: VML Example Document
author: Your Name
version: 1.0
---

# Welcome to VML

VML is a **versatile markup language** that combines the best of various formats.

## Features

@directive[type=list, style=bullet]
- Easy to read and write
- Supports ${variables} and %{templates}
- Custom markup: !!important!!, <~context~>, (*notes*)
- Advanced sections and directives

:: section[class=example, id=demo]
### Example Section

This is a [[annotated]] section with special properties.

| Feature | Support | Notes |
|---------|:-------:|-------|
| Markdown | Yes | Full support |
| Variables | Yes | ${var_name} |
| Templates | Yes | %{template} |
| Custom | Yes | Multiple types |
:: /section

@if has_feature("advanced") {
  This content only appears if advanced features are enabled.
}

/!Warning: This is experimental!/
/+Success: But it works great!+/
"""
    
    def get_text_to_code_prompt(self, text: str, context: Dict[str, Any]) -> str:
        """Get prompt for converting text to VML"""
        return f"""Convert the following natural language description into VML (Versatile Markup Language) format.

VML combines features from Markdown, AML, and other markup languages with these key elements:
- Markdown-style headers, lists, and formatting
- Directives using @directive[params] syntax
- Variables using ${{name}} syntax
- Templates using %{{template}} syntax
- Sections using :: section_name[params] ... :: /section_name
- Custom markup for emphasis (!!text!!), context (<~text~>), notes ((*text*)), warnings (/!text!/), and success (/+text+/)
- Metadata blocks using --- YAML --- syntax
- Tables with alignment support
- Annotations using [[text]] syntax

Input text:
{text}

Generate well-structured VML that effectively represents the content with appropriate use of its features."""
    
    def get_code_to_text_prompt(self, code: str, context: Dict[str, Any]) -> str:
        """Get prompt for converting VML to text"""
        detail_level = context.get('detail_level', 'standard')
        
        return f"""Analyze and explain the following VML (Versatile Markup Language) code.

VML Code:
{code}

Provide a {detail_level} explanation that covers:
1. The document structure and organization
2. Key content and sections
3. Special directives and their purposes
4. Use of variables, templates, and annotations
5. Any custom markup and its significance

Focus on explaining what the document conveys and how its various features are used."""
    
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
            # This is a simplified version - full implementation would preserve more structure
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
# PART 2: CORE CONVERTER CLASSES
# ============================================================================

class ConversionDirection(Enum):
    TEXT_TO_CODE = "text_to_code"
    CODE_TO_TEXT = "code_to_text"


class DetailLevel(Enum):
    SUMMARY = "summary"
    STANDARD = "standard"
    DETAILED = "detailed"


@dataclass
class ConversionConfig:
    """Configuration for conversion operations"""
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.3
    max_tokens: int = 4096
    system_prompt_override: Optional[str] = None
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    
    # Text-to-Code specific
    include_comments: bool = True
    include_docstrings: bool = True
    use_type_hints: bool = True
    follow_conventions: bool = True
    
    # Code-to-Text specific
    detail_level: DetailLevel = DetailLevel.STANDARD
    include_examples: bool = True
    technical_level: str = "intermediate"


@dataclass
class ConversionResult:
    """Result of a conversion operation"""
    success: bool
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    processing_time: float = 0.0
    cached: bool = False
    error: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


class ConversionCache:
    """SQLite-based cache for conversion results"""
    
    def __init__(self, cache_path: str = "conversion_cache.db"):
        self.cache_path = cache_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the cache database"""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversions (
                    hash TEXT PRIMARY KEY,
                    direction TEXT,
                    input_text TEXT,
                    output_text TEXT,
                    metadata TEXT,
                    timestamp REAL,
                    tokens_used INTEGER
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversions(timestamp)")
    
    def _compute_hash(self, text: str, config: ConversionConfig, direction: str) -> str:
        """Compute hash for cache key"""
        cache_key = f"{direction}:{text}:{config.model}:{config.temperature}"
        return hashlib.sha256(cache_key.encode()).hexdigest()
    
    def get(self, text: str, config: ConversionConfig, direction: str) -> Optional[ConversionResult]:
        """Retrieve cached conversion if available"""
        hash_key = self._compute_hash(text, config, direction)
        
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT output_text, metadata, tokens_used FROM conversions WHERE hash = ?",
                (hash_key,)
            )
            row = cursor.fetchone()
            
            if row:
                return ConversionResult(
                    success=True,
                    output=row[0],
                    metadata=json.loads(row[1]),
                    tokens_used=row[2],
                    cached=True
                )
        return None
    
    def set(self, text: str, config: ConversionConfig, direction: str, result: ConversionResult):
        """Store conversion result in cache"""
        hash_key = self._compute_hash(text, config, direction)
        
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO conversions 
                (hash, direction, input_text, output_text, metadata, timestamp, tokens_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                hash_key,
                direction,
                text,
                result.output,
                json.dumps(result.metadata),
                datetime.now().timestamp(),
                result.tokens_used
            ))


class PromptBuilder:
    """Builds optimized prompts for different conversion scenarios"""
    
    @staticmethod
    def build_text_to_code_prompt(
        text: str,
        target_language: str,
        config: ConversionConfig,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for text-to-code conversion"""
        
        # Special handling for VML
        if target_language.lower() == "vml":
            prompt = f"""Convert the following natural language description into VML (Versatile Markup Language) format.

VML is a powerful markup language that combines features from Markdown, AML, and other formats with these key elements:
- Markdown-style headers (# ## ###), lists, and basic formatting (**bold**, *italic*, `code`)
- Directives using @directive[params] syntax for special instructions
- Variables using ${{name}} syntax for dynamic content
- Templates using %{{template}} syntax for reusable components
- Sections using :: section_name[params] ... :: /section_name for structured content
- Custom markup: !!emphasis!!, <~context~>, (*notes*), /!warnings!/, /+success+/
- Metadata blocks using --- YAML --- syntax
- Tables with alignment support
- Annotations using [[text]] syntax

<requirements>
- Use appropriate VML features based on the content type
- Structure the document logically with sections and headings
- Apply custom markup where it adds semantic value
- Include metadata when document properties are mentioned
- Use directives for special behaviors or instructions
- Make the markup clean and readable
</requirements>

<input>
{text}
</input>

<context>
{json.dumps(context, indent=2) if context else "No additional context provided"}
</context>

Generate the VML markup:"""
        else:
            prompt = f"""Convert the following natural language description into {target_language} code.

<requirements>
- Generate clean, idiomatic {target_language} code
- Follow {target_language} best practices and conventions
{"- Include comprehensive docstrings and comments" if config.include_comments else "- Minimize comments"}
{"- Use type hints/annotations where applicable" if config.use_type_hints else ""}
- Handle edge cases and errors appropriately
- Make the code production-ready
</requirements>

<input>
{text}
</input>

<context>
{json.dumps(context, indent=2) if context else "No additional context provided"}
</context>

Generate the {target_language} code:"""
        
        return prompt
    
    @staticmethod
    def build_code_to_text_prompt(
        code: str,
        source_language: str,
        config: ConversionConfig
    ) -> str:
        """Build prompt for code-to-text conversion"""
        
        detail_instructions = {
            DetailLevel.SUMMARY: "Provide a high-level overview of what the code does",
            DetailLevel.STANDARD: "Explain the code's functionality, key components, and logic flow",
            DetailLevel.DETAILED: "Provide a comprehensive analysis including line-by-line explanation"
        }
        
        # Special handling for VML
        if source_language.lower() == "vml":
            prompt = f"""Analyze and explain the following VML (Versatile Markup Language) document.

VML is a markup language that combines features from Markdown, AML, and other formats. Key elements include:
- Directives (@directive[params])
- Variables (${{name}}) and Templates (%{{template}})
- Sections (:: section_name ... :: /section_name)
- Custom markup: !!emphasis!!, <~context~>, (*notes*), /!warnings!/, /+success+/
- Metadata blocks (--- YAML ---)
- Annotations ([[text]])

<requirements>
- {detail_instructions[config.detail_level]}
- Target audience: {config.technical_level} level
{"- Include usage examples" if config.include_examples else ""}
- Explain the document structure and organization
- Identify special directives and their purposes
- Note the use of variables, templates, and custom markup
- Explain any metadata and its significance
</requirements>

<code language="vml">
{code}
</code>

Provide your explanation:"""
        else:
            prompt = f"""Analyze and explain the following {source_language} code.

<requirements>
- {detail_instructions[config.detail_level]}
- Target audience: {config.technical_level} level
{"- Include usage examples" if config.include_examples else ""}
- Identify key algorithms, patterns, or techniques used
- Note any potential issues or improvements
</requirements>

<code language="{source_language}">
{code}
</code>

Provide your explanation:"""
        
        return prompt


class BidirectionalConverter:
    """Main converter class with Claude API integration"""
    
    def __init__(self, api_key: str, config: Optional[ConversionConfig] = None):
        self.api_key = api_key
        self.config = config or ConversionConfig()
        self.client = AsyncAnthropic(api_key=api_key)
        self.cache = ConversionCache() if self.config.cache_enabled else None
        self.prompt_builder = PromptBuilder()
        
        # Initialize VML handler
        self.vml_handler = VMLLanguageHandler()
        
        # Language-specific handlers
        self.language_handlers = {
            "python": self._python_specific_handling,
            "javascript": self._javascript_specific_handling,
            "java": self._java_specific_handling,
            "cpp": self._cpp_specific_handling,
            "sql": self._sql_specific_handling,
            "vml": self._vml_specific_handling,
        }
    
    async def convert_text_to_code(
        self,
        text: str,
        target_language: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversionResult:
        """Convert natural language to code"""
        
        start_time = datetime.now()
        
        # Check cache
        if self.cache:
            cached_result = self.cache.get(text, self.config, ConversionDirection.TEXT_TO_CODE.value)
            if cached_result:
                return cached_result
        
        try:
            # Build prompt
            prompt = self.prompt_builder.build_text_to_code_prompt(
                text, target_language, self.config, context
            )
            
            # Call Claude API
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.config.system_prompt_override or self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract code from response
            code_output = self._extract_code_from_response(response.content[0].text, target_language)
            
            # Apply language-specific post-processing
            if target_language.lower() in self.language_handlers:
                code_output = await self.language_handlers[target_language.lower()](code_output)
            
            # Create result
            result = ConversionResult(
                success=True,
                output=code_output,
                metadata={
                    "target_language": target_language,
                    "model": self.config.model,
                    "timestamp": datetime.now().isoformat()
                },
                tokens_used=response.usage.total_tokens,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache result
            if self.cache:
                self.cache.set(text, self.config, ConversionDirection.TEXT_TO_CODE.value, result)
            
            return result
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output="",
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def convert_code_to_text(
        self,
        code: str,
        source_language: str,
        config_override: Optional[ConversionConfig] = None
    ) -> ConversionResult:
        """Convert code to natural language explanation"""
        
        start_time = datetime.now()
        config = config_override or self.config
        
        # Check cache
        if self.cache:
            cached_result = self.cache.get(code, config, ConversionDirection.CODE_TO_TEXT.value)
            if cached_result:
                return cached_result
        
        try:
            # Build prompt
            prompt = self.prompt_builder.build_code_to_text_prompt(
                code, source_language, config
            )
            
            # Call Claude API
            response = await self.client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=self.config.system_prompt_override or self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Create result
            result = ConversionResult(
                success=True,
                output=response.content[0].text,
                metadata={
                    "source_language": source_language,
                    "detail_level": config.detail_level.value,
                    "model": config.model,
                    "timestamp": datetime.now().isoformat()
                },
                tokens_used=response.usage.total_tokens,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Cache result
            if self.cache:
                self.cache.set(code, config, ConversionDirection.CODE_TO_TEXT.value, result)
            
            return result
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output="",
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _get_system_prompt(self) -> str:
        """Get the default system prompt"""
        return """You are an expert programmer and technical writer. 
Your role is to perform high-quality conversions between natural language and code.
Always prioritize clarity, correctness, and best practices.
When generating code, ensure it is production-ready and well-documented.
When explaining code, tailor your explanation to the specified audience level."""
    
    def _extract_code_from_response(self, response: str, language: str) -> str:
        """Extract code from Claude's response"""
        # Look for code blocks
        code_pattern = rf"```{language}?\n(.*?)```"
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the entire response
        return response.strip()
    
    async def _python_specific_handling(self, code: str) -> str:
        """Apply Python-specific formatting and validation"""
        return code
    
    async def _javascript_specific_handling(self, code: str) -> str:
        """Apply JavaScript-specific formatting and validation"""
        return code
    
    async def _java_specific_handling(self, code: str) -> str:
        """Apply Java-specific formatting and validation"""
        return code
    
    async def _cpp_specific_handling(self, code: str) -> str:
        """Apply C++-specific formatting and validation"""
        return code
    
    async def _sql_specific_handling(self, code: str) -> str:
        """Apply SQL-specific formatting and validation"""
        return code
    
    async def _vml_specific_handling(self, code: str) -> str:
        """Apply VML-specific formatting and validation"""
        # Validate VML syntax
        is_valid, errors = self.vml_handler.validate_syntax(code)
        if not is_valid:
            # Add validation errors as comments
            error_comments = "\n".join([f"<!-- Validation Error: {error} -->" for error in errors])
            code = f"{error_comments}\n\n{code}"
        
        # Format the code
        formatted_code = self.vml_handler.format_code(code)
        return formatted_code


# ============================================================================
# PART 3: GUI APPLICATION
# ============================================================================

class ConverterGUI:
    """Main GUI application for bidirectional conversion"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bidirectional Code Converter with VML Support")
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
        # For simplicity, using a dictionary instead of configparser
        return {
            'API': {
                'model': 'claude-3-opus-20240229',
                'temperature': '0.3',
                'max_tokens': '4096'
            },
            'UI': {
                'theme': 'default',
                'font_size': '11',
                'auto_convert': 'false'
            },
            'Cache': {
                'enabled': 'true',
                'ttl_hours': '24'
            }
        }
    
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
        tools_menu.add_command(label="VML Editor", command=self._show_vml_editor)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="VML Documentation", command=self._show_vml_docs)
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
        
        # VML specific buttons
        if self.language_var.get() == "vml":
            vml_frame = ttk.Frame(toolbar)
            vml_frame.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                vml_frame, text="Insert Variable",
                command=lambda: self.input_text.insert(tk.INSERT, "${}")
            ).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(
                vml_frame, text="Insert Section",
                command=lambda: self.input_text.insert(tk.INSERT, ":: section[]\n\n:: /section")
            ).pack(side=tk.LEFT, padx=2)
        
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
        
        # Output controls
        output_controls = ttk.Frame(output_frame)
        output_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            output_controls, text="Copy", command=self._copy_output
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            output_controls, text="Save", command=self._save_output
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
        
        if api_key:
            try:
                config = ConversionConfig(
                    model=self.config['API']['model'],
                    temperature=float(self.config['API']['temperature']),
                    max_tokens=int(self.config['API']['max_tokens']),
                    cache_enabled=self.config['Cache']['enabled'] == 'true'
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
        dialog.geometry("500x200")
        dialog.transient(self.root)
        
        # Instructions
        instructions = ttk.Label(
            dialog,
            text="Please enter your Anthropic API key to enable conversions.\n" +
                 "Set ANTHROPIC_API_KEY environment variable to avoid this prompt.",
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
            self.root.title("Text to Code Converter with VML Support")
        else:
            self.root.title("Code to Text Converter with VML Support")
    
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
            
            # Update status
            self.status_var.set("Conversion successful")
            self.token_var.set(f"Tokens: {result.tokens_used}")
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
                ("VML Files", "*.vml"),
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
                ("VML Files", "*.vml"),
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
        if self.language_var.get() == "vml":
            if self.current_mode == ConversionDirection.TEXT_TO_CODE:
                example = """Create a technical documentation page for a REST API.
Include:
- API overview and authentication
- Endpoint documentation with examples
- Error handling information
- Rate limiting details
Make it well-structured with proper sections and include both success and error response examples."""
            else:
                example = """---
title: REST API Documentation
version: 2.0
---

# API Reference

## Authentication

All requests require [[Bearer token authentication]].

:: section[type=endpoint]
### Get User Profile

@endpoint[method=GET, path=/api/users/{id}]

Retrieves user profile information.

**Parameters:**
- `id` (required): User ID

**Success Response** /+200 OK+/:
```json
{
  "id": "${user_id}",
  "name": "${user_name}",
  "email": "${user_email}"
}
```

**Error Response** /!401 Unauthorized!/:
```json
{
  "error": "Invalid token"
}
```
:: /section"""
        else:
            # Default examples for other languages
            examples = {
                ConversionDirection.TEXT_TO_CODE: {
                    "python": "Create a function that validates email addresses using regex.",
                    "javascript": "Create a React component for a todo list.",
                    "sql": "Create a query to find top 5 customers by purchase amount."
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
    
    def _show_api_settings(self):
        """Show API settings dialog"""
        messagebox.showinfo("API Settings", 
                           "API settings would be shown here.\n" +
                           "Currently using model: " + self.config['API']['model'])
    
    def _show_vml_editor(self):
        """Show VML editor window"""
        vml_window = tk.Toplevel(self.root)
        vml_window.title("VML Editor")
        vml_window.geometry("800x600")
        
        # Create VML-specific editor
        editor_frame = ttk.Frame(vml_window)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vml_text = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.WORD, font=("Consolas", 11)
        )
        vml_text.pack(fill=tk.BOTH, expand=True)
        
        # Add sample VML content
        vml_text.insert("1.0", self.vml_handler.get_example_code())
        
        # Add toolbar
        toolbar = ttk.Frame(vml_window)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            toolbar, text="Validate",
            command=lambda: self._validate_vml(vml_text.get("1.0", tk.END))
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, text="Format",
            command=lambda: vml_text.replace("1.0", tk.END, 
                                           self.vml_handler.format_code(vml_text.get("1.0", tk.END)))
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, text="Convert to HTML",
            command=lambda: self._show_vml_conversion(
                vml_text.get("1.0", tk.END), "html"
            )
        ).pack(side=tk.LEFT, padx=5)
    
    def _validate_vml(self, code: str):
        """Validate VML code"""
        is_valid, errors = self.vml_handler.validate_syntax(code)
        if is_valid:
            messagebox.showinfo("Validation", "VML syntax is valid!")
        else:
            error_msg = "VML validation errors:\n\n" + "\n".join(errors)
            messagebox.showerror("Validation Error", error_msg)
    
    def _show_vml_conversion(self, vml_code: str, target_format: str):
        """Show VML conversion result"""
        converter = VMLConverter()
        
        if target_format == "html":
            result = converter.vml_to_html(vml_code)
        else:
            result = converter.vml_to_markdown(vml_code)
        
        # Show result in new window
        result_window = tk.Toplevel(self.root)
        result_window.title(f"VML to {target_format.upper()}")
        result_window.geometry("600x400")
        
        result_text = scrolledtext.ScrolledText(
            result_window, wrap=tk.WORD, font=("Consolas", 10)
        )
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        result_text.insert("1.0", result)
    
    def _show_vml_docs(self):
        """Show VML documentation"""
        docs_window = tk.Toplevel(self.root)
        docs_window.title("VML Documentation")
        docs_window.geometry("800x600")
        
        docs_text = scrolledtext.ScrolledText(
            docs_window, wrap=tk.WORD, font=("Consolas", 10)
        )
        docs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        docs_content = """VML (Versatile Markup Language) Documentation
=============================================

VML is a powerful markup language that combines features from Markdown, AML, and other formats.

## Basic Syntax

### Headers
# H1 Header
## H2 Header
### H3 Header

### Text Formatting
**Bold text**
*Italic text*
`inline code`

### Custom Markup
!!Emphasis!! - For important text
<~Context~> - For background information
(*Notes*) - For side notes
/!Warnings!/ - For cautions
/+Success+/ - For positive messages
@[Code Ref]@ - For code references
[[Annotations]] - For metadata

### Variables and Templates
${variable_name} - Variable placeholder
%{template_name} - Template reference

### Directives
@directive[param1=value1, param2=value2]
Content

### Sections
:: section[type=example]
Section content here
:: /section

### Metadata
---
title: Document Title
author: Author Name
version: 1.0
---

### Tables
| Column 1 | Column 2 | Column 3 |
|----------|:--------:|---------:|
| Left     | Center   | Right    |

## Advanced Features

### Conditional Content
@if condition {
  Conditional content
}

### Loops
@for item in list {
  Repeated content with ${item}
}

### File Includes
@include "filename.vml"

### Macros
@macro button(text, action) {
  <button onclick="${action}">${text}</button>
}
"""
        
        docs_text.insert("1.0", docs_content)
        docs_text.config(state=tk.DISABLED)
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Bidirectional Code Converter with VML Support\n\n" +
            "Version 1.0.0\n" +
            "Powered by Claude API\n\n" +
            "Convert between natural language and code,\n" +
            "including support for VML (Versatile Markup Language)."
        )


# ============================================================================
# PART 4: MAIN ENTRY POINT AND TESTING
# ============================================================================

def test_vml_system():
    """Test VML system components"""
    print("Testing VML System...")
    print("=" * 50)
    
    # Test 1: VML Parser
    print("\n1. Testing VML Parser:")
    vml_content = """---
title: Test Document
---

# Test Heading

This is a paragraph with ${variable} and %{template}.

:: section[type=test]
## Section Content
- Item with !!emphasis!!
- Item with <~context~>
:: /section
"""
    
    parser = VMLParser()
    elements = parser.parse(vml_content)
    print(f"   Parsed {len(elements)} elements successfully")
    
    # Test 2: VML Converter
    print("\n2. Testing VML Converter:")
    converter = VMLConverter()
    html_output = converter.vml_to_html(vml_content)
    print(f"   HTML conversion successful ({len(html_output)} chars)")
    
    # Test 3: VML Handler
    print("\n3. Testing VML Language Handler:")
    handler = VMLLanguageHandler()
    is_valid, errors = handler.validate_syntax(vml_content)
    print(f"   Validation: {'Passed' if is_valid else 'Failed'}")
    
    print("\nAll tests completed!")
    print("=" * 50)


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run tests
        test_vml_system()
    else:
        # Run GUI application
        root = tk.Tk()
        app = ConverterGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()