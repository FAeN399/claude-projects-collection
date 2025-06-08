#!/usr/bin/env python3
"""
VML (Versatile Markup Language) Handler
---------------------------------------
A custom markup language that combines the best of Markdown, AML, and other formats
with enhanced flexibility and AI-friendly structures.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


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
    DIRECTIVE_PATTERN = r'^@(\w+)(?:\[([^\]]*)\])?\s*(.*)$'  # @directive[params] content
    VARIABLE_PATTERN = r'\$\{([^}]+)\}'  # ${variable_name}
    TEMPLATE_PATTERN = r'%\{([^}]+)\}'  # %{template_name}
    ANNOTATION_PATTERN = r'\[\[([^\]]+)\]\]'  # [[annotation]]
    METADATA_PATTERN = r'^---\s*$'  # YAML-style metadata blocks
    
    # Custom section markers
    SECTION_START_PATTERN = r'^::\s*(\w+)(?:\[([^\]]*)\])?\s*$'  # :: section_name[params]
    SECTION_END_PATTERN = r'^::\s*/(\w+)\s*$'  # :: /section_name
    
    # Advanced features
    INCLUDE_PATTERN = r'^@include\s+"([^"]+)"$'  # @include "filename"
    MACRO_PATTERN = r'^@macro\s+(\w+)\((.*?)\)\s*{$'  # @macro name(params) {
    CONDITION_PATTERN = r'^@if\s+(.+)\s*{$'  # @if condition {
    LOOP_PATTERN = r'^@for\s+(\w+)\s+in\s+(.+)\s*{$'  # @for item in list {
    
    # Table syntax (similar to markdown but enhanced)
    TABLE_SEPARATOR = r'^\|[\s\-:|]+\|$'
    TABLE_ROW = r'^\|(.+)\|$'
    
    # Custom markup delimiters
    CUSTOM_MARKUP = {
        'emphasis': ('!!', '!!'),  # !!important text!!
        'context': ('<~', '~>'),   # <~background info~>
        'note': ('(*', '*)'),      # (*side note*)
        'warning': ('/!', '!/'),   # /!warning text!/
        'success': ('/+', '+/'),   # /+success message+/
        'code_ref': ('@[', ']@'),  # @[function_name]@
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
                # End of metadata block
                # Parse YAML content here
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
            # Check for nested sections
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
        # This is a simplified version - in production, you'd want proper parsing
        
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
        
        # Simple attribute parsing - can be enhanced
        pairs = attr_string.split(',')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                attributes[key.strip()] = value.strip().strip('"\'')
            else:
                # Boolean attribute
                attributes[pair.strip()] = True
        
        return attributes
    
    def _parse_table_row(self, line: str) -> List[str]:
        """Parse a table row"""
        # Remove leading and trailing pipes
        line = line.strip('|')
        # Split by pipe and strip whitespace
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
        """Process metadata lines (simplified YAML parsing)"""
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
            # Handle directives - this is where custom processing happens
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


# Integration with the bidirectional converter
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
        # Parse and reconstruct for consistent formatting
        try:
            elements = self.parser.parse(code)
            # Reconstruct with consistent formatting
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


# Example usage and testing
if __name__ == "__main__":
    # Test VML parser and converter
    vml_content = """---
title: Test Document
author: AI Assistant
---

# VML Test Document

This is a test of the **Versatile Markup Language** with ${dynamic_content}.

## Features Demo

:: section[type=features, style=grid]
### Basic Formatting

- **Bold text**
- *Italic text*
- `inline code`
- !!Important information!!
- <~Background context~>
- (*Side note*)
- /!Warning message!/
- /+Success notification+/

### Advanced Elements

@directive[name=example, param=value]
This is a directive with parameters.

Using ${variables} and %{templates} for dynamic content.

| Column 1 | Column 2 | Column 3 |
|----------|:--------:|---------:|
| Left     | Center   | Right    |
| Data 1   | Data 2   | Data 3   |

:: /section

[[This is an annotation that provides additional context]]
"""
    
    # Test parsing
    handler = VMLLanguageHandler()
    parser = VMLParser()
    elements = parser.parse(vml_content)
    
    print("Parsed Elements:")
    for elem in elements:
        print(f"- {elem.type}: {elem.content[:50]}...")
    
    # Test conversion to HTML
    converter = VMLConverter()
    html = converter.vml_to_html(vml_content)
    print("\nHTML Output Preview:")
    print(html[:500] + "...")
    
    # Test validation
    is_valid, errors = handler.validate_syntax(vml_content)
    print(f"\nValidation: {'Passed' if is_valid else 'Failed'}")
    if errors:
        for error in errors:
            print(f"  - {error}")