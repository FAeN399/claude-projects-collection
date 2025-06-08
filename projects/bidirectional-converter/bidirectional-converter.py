#!/usr/bin/env python3
"""
Bidirectional Converter with Claude API Integration
--------------------------------------------------
Converts between natural language and code using Claude's intelligence.
Supports multiple programming languages and documentation formats.
"""

import os
import json
import yaml
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import anthropic
from anthropic import AsyncAnthropic
import hashlib
import sqlite3
from enum import Enum


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
    technical_level: str = "intermediate"  # beginner, intermediate, advanced


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
        
        # Import VML handler
        from vml_language_handler import VMLLanguageHandler
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
        import re
        
        # Try to find code within backticks
        code_pattern = rf"```{language}?\n(.*?)```"
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the entire response
        # (Claude might have returned code without fence markers)
        return response.strip()
    
    async def _python_specific_handling(self, code: str) -> str:
        """Apply Python-specific formatting and validation"""
        # This is a placeholder for Python-specific processing
        # In a real implementation, you might:
        # - Run black formatter
        # - Add type hints
        # - Validate syntax
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


# Example usage and testing
async def main():
    # Initialize converter
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    converter = BidirectionalConverter(api_key)
    
    # Example 1: Text to Code
    print("=== Text to Code Example ===")
    text_input = """
    Create a function that calculates compound interest.
    It should take principal amount, annual interest rate (as a percentage),
    time period in years, and number of times interest is compounded per year.
    Include error handling for invalid inputs.
    """
    
    result = await converter.convert_text_to_code(
        text=text_input,
        target_language="python",
        context={"style": "functional", "include_tests": True}
    )
    
    if result.success:
        print(f"Generated Python code:")
        print(result.output)
        print(f"\nTokens used: {result.tokens_used}")
        print(f"Processing time: {result.processing_time:.2f}s")
    else:
        print(f"Error: {result.error}")
    
    # Example 2: Code to Text
    print("\n=== Code to Text Example ===")
    code_input = """
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
    """
    
    result = await converter.convert_code_to_text(
        code=code_input,
        source_language="python"
    )
    
    if result.success:
        print(f"Explanation:")
        print(result.output)
        print(f"\nTokens used: {result.tokens_used}")
        print(f"Cached: {result.cached}")
    else:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
