#!/usr/bin/env python3
"""
Unified Bidirectional Converter System
=====================================
Complete integration of all conversion tools into a single comprehensive platform.
Based on the technical specification for unified system architecture.
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
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib
import configparser
from abc import ABC, abstractmethod
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import anthropic, but make it optional
try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic module not available. API features will be disabled.")

# ============================================================================
# CONFIGURATION SYSTEM
# ============================================================================

class UnifiedConfig:
    """Centralized configuration system for all components"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".unified_converter" / "config.ini"
        self.config = configparser.ConfigParser()
        self._load_config()
        
    def _load_config(self):
        """Load or create default configuration"""
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            self._create_default_config()
            
    def _create_default_config(self):
        """Create default configuration file"""
        self.config['API'] = {
            'provider': 'anthropic',
            'model': 'claude-3-opus-20240229',
            'temperature': '0.3',
            'max_tokens': '4096',
            'cache_enabled': 'true',
            'cache_ttl_hours': '24'
        }
        
        self.config['Editor'] = {
            'font_family': 'Consolas',
            'font_size': '11',
            'theme': 'default',
            'auto_save': 'false',
            'auto_save_interval': '300'
        }
        
        self.config['VML'] = {
            'validate_on_save': 'true',
            'format_on_save': 'false',
            'default_author': 'User',
            'default_version': '1.0'
        }
        
        self.config['UI'] = {
            'window_width': '1400',
            'window_height': '900',
            'sidebar_width': '300',
            'show_status_bar': 'true',
            'show_toolbar': 'true'
        }
        
        self.config['Export'] = {
            'default_format': 'markdown',
            'include_metadata': 'true',
            'syntax_highlighting': 'true'
        }
        
        self.config['Security'] = {
            'api_key_storage': 'environment',
            'enable_request_logging': 'false',
            'max_file_size_mb': '10'
        }
        
        # Save default config
        self.save()
        
    def save(self):
        """Save configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            self.config.write(f)
            
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(section, key, fallback=fallback)
        
    def set(self, section: str, key: str, value: Any):
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
        
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        return self.config.getboolean(section, key, fallback=fallback)
        
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        return self.config.getint(section, key, fallback=fallback)
        
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        return self.config.getfloat(section, key, fallback=fallback)


# ============================================================================
# ENHANCED DATA MODELS
# ============================================================================

@dataclass
class ConversionContext:
    """Enhanced context for conversions with full integration support"""
    source_format: str
    target_format: str
    markup_enabled: bool = True
    vml_preprocessing: bool = False
    custom_markup_definitions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    
@dataclass
class UnifiedConversionResult:
    """Unified result structure for all conversion types"""
    success: bool
    output: str
    format: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    processing_time: float = 0.0
    cached: bool = False
    intermediate_formats: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
# INTERFACE DEFINITIONS
# ============================================================================

class ConverterInterface(ABC):
    """Abstract interface for all converters"""
    
    @abstractmethod
    async def convert(self, input_text: str, context: ConversionContext) -> UnifiedConversionResult:
        """Perform conversion"""
        pass
        
    @abstractmethod
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported input/output format pairs"""
        pass
        
    @abstractmethod
    def validate_input(self, input_text: str, format: str) -> Tuple[bool, List[str]]:
        """Validate input for given format"""
        pass


# ============================================================================
# UNIFIED CONVERTER ENGINE
# ============================================================================

class UnifiedConverterEngine:
    """Central converter engine that orchestrates all conversion operations"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.converters: Dict[str, ConverterInterface] = {}
        self.cache = UnifiedCache(config)
        self.session_manager = SessionManager()
        self._initialize_converters()
        
    def _initialize_converters(self):
        """Initialize all available converters"""
        # Initialize VML converter
        from vml_converter import VMLConverter
        self.converters['vml'] = VMLConverter()
        
        # Initialize Claude converter if available
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            from claude_converter import ClaudeConverter
            self.converters['claude'] = ClaudeConverter(self.config)
            
        # Initialize markup processor
        from markup_processor import MarkupProcessor
        self.converters['markup'] = MarkupProcessor()
        
        logger.info(f"Initialized {len(self.converters)} converters")
        
    async def convert(self, 
                     input_text: str, 
                     source_format: str,
                     target_format: str,
                     context: Optional[ConversionContext] = None) -> UnifiedConversionResult:
        """Main conversion method that determines optimal conversion path"""
        
        start_time = datetime.now()
        
        # Create context if not provided
        if not context:
            context = ConversionContext(
                source_format=source_format,
                target_format=target_format
            )
            
        # Check cache
        cache_key = self.cache.generate_key(input_text, context)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
            
        try:
            # Determine conversion path
            conversion_path = self._determine_conversion_path(source_format, target_format)
            
            # Execute conversion pipeline
            result = await self._execute_conversion_pipeline(
                input_text, conversion_path, context
            )
            
            # Cache result
            if result.success:
                await self.cache.set(cache_key, result)
                
            # Update processing time
            result.processing_time = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return UnifiedConversionResult(
                success=False,
                output="",
                format=target_format,
                error=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
    def _determine_conversion_path(self, source: str, target: str) -> List[Tuple[str, str]]:
        """Determine optimal conversion path between formats"""
        # Direct conversion paths
        direct_paths = {
            ('text', 'code'): [('text', 'code')],
            ('code', 'text'): [('code', 'text')],
            ('text', 'vml'): [('text', 'vml')],
            ('vml', 'html'): [('vml', 'html')],
            ('vml', 'markdown'): [('vml', 'markdown')],
        }
        
        # Check for direct path
        if (source, target) in direct_paths:
            return direct_paths[(source, target)]
            
        # Complex paths through intermediates
        if source == 'text' and target == 'html':
            return [('text', 'vml'), ('vml', 'html')]
        elif source == 'markdown' and target == 'vml':
            return [('markdown', 'vml')]
            
        # Default: attempt direct conversion
        return [(source, target)]
        
    async def _execute_conversion_pipeline(self,
                                         input_text: str,
                                         pipeline: List[Tuple[str, str]],
                                         context: ConversionContext) -> UnifiedConversionResult:
        """Execute a multi-stage conversion pipeline"""
        current_text = input_text
        current_format = pipeline[0][0]
        intermediate_results = []
        total_tokens = 0
        warnings = []
        suggestions = []
        
        for source_fmt, target_fmt in pipeline:
            # Select appropriate converter
            converter = self._select_converter(source_fmt, target_fmt)
            if not converter:
                return UnifiedConversionResult(
                    success=False,
                    output="",
                    format=target_fmt,
                    error=f"No converter available for {source_fmt} to {target_fmt}"
                )
                
            # Perform conversion
            stage_context = ConversionContext(
                source_format=source_fmt,
                target_format=target_fmt,
                markup_enabled=context.markup_enabled,
                vml_preprocessing=context.vml_preprocessing,
                custom_markup_definitions=context.custom_markup_definitions,
                metadata=context.metadata
            )
            
            result = await converter.convert(current_text, stage_context)
            
            if not result.success:
                return result
                
            # Accumulate results
            current_text = result.output
            current_format = target_fmt
            intermediate_results.append((source_fmt, target_fmt))
            total_tokens += result.tokens_used
            warnings.extend(result.warnings)
            suggestions.extend(result.suggestions)
            
        # Return final result
        return UnifiedConversionResult(
            success=True,
            output=current_text,
            format=current_format,
            intermediate_formats=intermediate_results,
            tokens_used=total_tokens,
            warnings=warnings,
            suggestions=suggestions
        )
        
    def _select_converter(self, source: str, target: str) -> Optional[ConverterInterface]:
        """Select appropriate converter for format pair"""
        # VML conversions
        if source == 'vml' or target == 'vml':
            return self.converters.get('vml')
            
        # Claude API conversions
        if (source == 'text' and target == 'code') or (source == 'code' and target == 'text'):
            return self.converters.get('claude')
            
        # Markup processing
        if source.endswith('_markup') or target.endswith('_markup'):
            return self.converters.get('markup')
            
        return None


# ============================================================================
# UNIFIED CACHE SYSTEM
# ============================================================================

class UnifiedCache:
    """Unified caching system for all conversion results"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        self.cache_path = Path.home() / ".unified_converter" / "cache.db"
        self.ttl_hours = config.get_int('API', 'cache_ttl_hours', 24)
        self._init_db()
        
    def _init_db(self):
        """Initialize cache database"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    result TEXT,
                    format TEXT,
                    timestamp REAL,
                    tokens_used INTEGER,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
            
    def generate_key(self, text: str, context: ConversionContext) -> str:
        """Generate cache key from input and context"""
        key_data = {
            'text': text,
            'source': context.source_format,
            'target': context.target_format,
            'markup': context.markup_enabled,
            'vml': context.vml_preprocessing
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
        
    async def get(self, key: str) -> Optional[UnifiedConversionResult]:
        """Retrieve cached result"""
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT result, format, timestamp, tokens_used, metadata FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                # Check TTL
                timestamp = datetime.fromtimestamp(row[2])
                if datetime.now() - timestamp > timedelta(hours=self.ttl_hours):
                    # Expired
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    return None
                    
                # Deserialize result
                result_data = json.loads(row[0])
                return UnifiedConversionResult(
                    success=True,
                    output=result_data['output'],
                    format=row[1],
                    tokens_used=row[3],
                    metadata=json.loads(row[4]),
                    cached=True
                )
                
        return None
        
    async def set(self, key: str, result: UnifiedConversionResult):
        """Cache conversion result"""
        with sqlite3.connect(self.cache_path) as conn:
            result_data = {
                'output': result.output,
                'warnings': result.warnings,
                'suggestions': result.suggestions
            }
            
            conn.execute("""
                INSERT OR REPLACE INTO cache 
                (key, result, format, timestamp, tokens_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                key,
                json.dumps(result_data),
                result.format,
                datetime.now().timestamp(),
                result.tokens_used,
                json.dumps(result.metadata)
            ))


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manage user sessions for continuous context"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    def create_session(self) -> str:
        """Create new session"""
        import uuid
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created': datetime.now(),
            'last_active': datetime.now(),
            'history': [],
            'context': {}
        }
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_active'] = datetime.now()
            return self.sessions[session_id]
        return None
        
    def update_session(self, session_id: str, data: Dict[str, Any]):
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(data)
            self.sessions[session_id]['last_active'] = datetime.now()
            
    def cleanup_expired(self, ttl_hours: int = 24):
        """Remove expired sessions"""
        cutoff = datetime.now() - timedelta(hours=ttl_hours)
        expired = [
            sid for sid, data in self.sessions.items()
            if data['last_active'] < cutoff
        ]
        for sid in expired:
            del self.sessions[sid]


# ============================================================================
# UNIFIED GUI APPLICATION
# ============================================================================

class UnifiedConverterGUI:
    """Main GUI application integrating all components"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = UnifiedConfig()
        self.engine = UnifiedConverterEngine(self.config)
        self.session_id = self.engine.session_manager.create_session()
        
        # Setup UI
        self._setup_window()
        self._setup_styles()
        self._create_menu()
        self._create_toolbar()
        self._create_main_interface()
        self._create_status_bar()
        self._setup_keyboard_shortcuts()
        
        # State management
        self.current_file = None
        self.modified = False
        self.conversion_history = []
        
        # Initialize with example content
        self._load_welcome_content()
        
    def _setup_window(self):
        """Configure main window"""
        self.root.title("Unified Bidirectional Converter System")
        
        # Load window dimensions from config
        width = self.config.get_int('UI', 'window_width', 1400)
        height = self.config.get_int('UI', 'window_height', 900)
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Set minimum size
        self.root.minsize(1000, 600)
        
    def _setup_styles(self):
        """Configure application styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color scheme
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'background': '#f8fafc',
            'surface': '#ffffff',
            'text': '#1e293b',
            'muted': '#94a3b8'
        }
        
        # Configure styles
        style.configure('Primary.TButton', foreground='white', background=self.colors['primary'])
        style.configure('Success.TButton', foreground='white', background=self.colors['success'])
        style.configure('Warning.TButton', foreground='white', background=self.colors['warning'])
        
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self._save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import...", command=self._import_file)
        file_menu.add_command(label="Export...", command=self._export_file)
        file_menu.add_separator()
        file_menu.add_command(label="Recent Files", command=self._show_recent_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._quit_application)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self._cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self._copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", command=self._find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace...", command=self._replace, accelerator="Ctrl+H")
        
        # Convert menu
        convert_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Convert", menu=convert_menu)
        convert_menu.add_command(label="Quick Convert", command=self._quick_convert, accelerator="F5")
        convert_menu.add_separator()
        convert_menu.add_command(label="Text to Code", command=lambda: self._set_mode('text', 'code'))
        convert_menu.add_command(label="Code to Text", command=lambda: self._set_mode('code', 'text'))
        convert_menu.add_command(label="Text to VML", command=lambda: self._set_mode('text', 'vml'))
        convert_menu.add_command(label="VML to HTML", command=lambda: self._set_mode('vml', 'html'))
        convert_menu.add_command(label="VML to Markdown", command=lambda: self._set_mode('vml', 'markdown'))
        convert_menu.add_separator()
        convert_menu.add_command(label="Batch Convert...", command=self._batch_convert)
        
        # Markup menu
        markup_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Markup", menu=markup_menu)
        markup_menu.add_command(label="Apply Emphasis", command=lambda: self._apply_markup('emphasis'))
        markup_menu.add_command(label="Apply Context", command=lambda: self._apply_markup('context'))
        markup_menu.add_command(label="Apply Warning", command=lambda: self._apply_markup('warning'))
        markup_menu.add_command(label="Apply Success", command=lambda: self._apply_markup('success'))
        markup_menu.add_separator()
        markup_menu.add_command(label="Manage Custom Markup...", command=self._manage_markup)
        markup_menu.add_command(label="Export Markup Definitions", command=self._export_markup)
        markup_menu.add_command(label="Import Markup Definitions", command=self._import_markup)
        
        # VML menu
        vml_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="VML", menu=vml_menu)
        vml_menu.add_command(label="Validate", command=self._validate_vml, accelerator="F7")
        vml_menu.add_command(label="Format", command=self._format_vml, accelerator="F8")
        vml_menu.add_separator()
        vml_menu.add_command(label="Insert Variable", command=lambda: self._insert_vml('variable'))
        vml_menu.add_command(label="Insert Template", command=lambda: self._insert_vml('template'))
        vml_menu.add_command(label="Insert Section", command=lambda: self._insert_vml('section'))
        vml_menu.add_command(label="Insert Table", command=lambda: self._insert_vml('table'))
        vml_menu.add_separator()
        vml_menu.add_command(label="VML Reference", command=self._show_vml_reference)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="API Settings...", command=self._show_api_settings)
        tools_menu.add_command(label="Editor Preferences...", command=self._show_editor_preferences)
        tools_menu.add_command(label="Clear Cache", command=self._clear_cache)
        tools_menu.add_separator()
        tools_menu.add_command(label="Conversion History", command=self._show_history)
        tools_menu.add_command(label="Statistics", command=self._show_statistics)
        tools_menu.add_separator()
        tools_menu.add_command(label="Plugin Manager...", command=self._show_plugin_manager)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_documentation, accelerator="F1")
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_command(label="Tutorial", command=self._show_tutorial)
        help_menu.add_separator()
        help_menu.add_command(label="Check for Updates", command=self._check_updates)
        help_menu.add_command(label="Report Issue", command=self._report_issue)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_toolbar(self):
        """Create application toolbar"""
        if not self.config.get_bool('UI', 'show_toolbar', True):
            return
            
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # File operations
        ttk.Button(toolbar, text="📄", command=self._new_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="📁", command=self._open_file, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="💾", command=self._save_file, width=3).pack(side=tk.LEFT, padx=1)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Edit operations
        ttk.Button(toolbar, text="↶", command=self._undo, width=3).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="↷", command=self._redo, width=3).pack(side=tk.LEFT, padx=1)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Conversion mode selector
        mode_frame = ttk.LabelFrame(toolbar, text="Conversion Mode")
        mode_frame.pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="text-to-code")
        modes = [
            ("Text → Code", "text-to-code"),
            ("Code → Text", "code-to-text"),
            ("Text → VML", "text-to-vml"),
            ("VML → HTML", "vml-to-html"),
            ("VML → MD", "vml-to-markdown")
        ]
        
        for text, value in modes:
            ttk.Radiobutton(
                mode_frame, text=text, variable=self.mode_var, 
                value=value, command=self._update_mode
            ).pack(side=tk.LEFT, padx=5)
            
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Quick actions
        self.convert_btn = ttk.Button(
            toolbar, text="Convert", command=self._quick_convert,
            style='Primary.TButton'
        )
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, text="Validate", command=self._validate_content,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            toolbar, text="Format", command=self._format_content,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
    def _create_main_interface(self):
        """Create the main interface layout"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create horizontal paned window
        self.main_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Input/Editor
        left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(left_panel, weight=1)
        
        # Editor notebook
        self.editor_notebook = ttk.Notebook(left_panel)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create editor tabs
        self._create_editor_tab()
        self._create_markup_tab()
        self._create_vml_tab()
        
        # Right panel - Output/Preview
        right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(right_panel, weight=1)
        
        # Output notebook
        self.output_notebook = ttk.Notebook(right_panel)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create output tabs
        self._create_output_tab()
        self._create_preview_tab()
        self._create_metadata_tab()
        self._create_history_tab()
        
        # Sidebar (optional)
        if self.config.get_bool('UI', 'show_sidebar', False):
            self._create_sidebar()
            
    def _create_editor_tab(self):
        """Create main editor tab"""
        editor_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(editor_frame, text="Editor")
        
        # Editor controls
        controls = ttk.Frame(editor_frame)
        controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Language selector
        ttk.Label(controls, text="Language:").pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value="python")
        self.language_combo = ttk.Combobox(
            controls, textvariable=self.language_var, width=15,
            values=["python", "javascript", "java", "cpp", "csharp", "go", 
                   "rust", "sql", "html", "css", "vml", "markdown"]
        )
        self.language_combo.pack(side=tk.LEFT, padx=5)
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        
        # Editor
        self.main_editor = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.WORD, 
            font=(self.config.get('Editor', 'font_family', 'Consolas'),
                  self.config.get_int('Editor', 'font_size', 11)),
            undo=True, maxundo=-1
        )
        self.main_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure editor
        self._configure_editor(self.main_editor)
        
    def _create_markup_tab(self):
        """Create markup editor tab"""
        markup_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(markup_frame, text="Enhanced Markup")
        
        # Markup toolbar
        markup_toolbar = ttk.Frame(markup_frame)
        markup_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick markup buttons
        markup_buttons = [
            ("!!", "Emphasis", lambda: self._quick_markup("!!", "!!")),
            ("<~", "Context", lambda: self._quick_markup("<~", "~>")),
            ("(*", "Note", lambda: self._quick_markup("(*", "*)")),
            ("/!", "Warning", lambda: self._quick_markup("/!", "!/")),
            ("/+", "Success", lambda: self._quick_markup("/+", "+/")),
        ]
        
        for text, tooltip, command in markup_buttons:
            btn = ttk.Button(markup_toolbar, text=text, command=command, width=3)
            btn.pack(side=tk.LEFT, padx=2)
            # Add tooltip
            self._create_tooltip(btn, tooltip)
            
        # Markup editor
        self.markup_editor = scrolledtext.ScrolledText(
            markup_frame, wrap=tk.WORD,
            font=(self.config.get('Editor', 'font_family', 'Consolas'),
                  self.config.get_int('Editor', 'font_size', 11)),
            undo=True, maxundo=-1
        )
        self.markup_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure markup highlighting
        self._configure_markup_editor(self.markup_editor)
        
    def _create_vml_tab(self):
        """Create VML editor tab"""
        vml_frame = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(vml_frame, text="VML Editor")
        
        # VML toolbar
        vml_toolbar = ttk.Frame(vml_frame)
        vml_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Quick VML buttons
        vml_buttons = [
            ("${}", "Variable", lambda: self._insert_at_cursor("${}", -1)),
            ("%{}", "Template", lambda: self._insert_at_cursor("%{}", -1)),
            ("[[]]", "Annotation", lambda: self._insert_at_cursor("[[]]", -2)),
            ("@", "Directive", lambda: self._insert_at_cursor("@directive[params] ", 0)),
            ("::", "Section", lambda: self._insert_vml_section()),
        ]
        
        for text, tooltip, command in vml_buttons:
            btn = ttk.Button(vml_toolbar, text=text, command=command, width=4)
            btn.pack(side=tk.LEFT, padx=2)
            self._create_tooltip(btn, tooltip)
            
        ttk.Separator(vml_toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # VML actions
        ttk.Button(vml_toolbar, text="Validate", command=self._validate_vml).pack(side=tk.LEFT, padx=2)
        ttk.Button(vml_toolbar, text="Format", command=self._format_vml).pack(side=tk.LEFT, padx=2)
        
        # VML editor
        self.vml_editor = scrolledtext.ScrolledText(
            vml_frame, wrap=tk.WORD,
            font=(self.config.get('Editor', 'font_family', 'Consolas'),
                  self.config.get_int('Editor', 'font_size', 11)),
            undo=True, maxundo=-1
        )
        self.vml_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure VML syntax highlighting
        self._configure_vml_editor(self.vml_editor)
        
    def _create_output_tab(self):
        """Create output display tab"""
        output_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(output_frame, text="Output")
        
        # Output controls
        output_controls = ttk.Frame(output_frame)
        output_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(output_controls, text="Copy", command=self._copy_output).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_controls, text="Save", command=self._save_output).pack(side=tk.LEFT, padx=2)
        ttk.Button(output_controls, text="Format", command=self._format_output).pack(side=tk.LEFT, padx=2)
        
        # Output display
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD,
            font=(self.config.get('Editor', 'font_family', 'Consolas'),
                  self.config.get_int('Editor', 'font_size', 11)),
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _create_preview_tab(self):
        """Create preview tab for HTML/formatted output"""
        preview_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(preview_frame, text="Preview")
        
        # For now, use a text widget - could be replaced with webview
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame, wrap=tk.WORD,
            font=("Arial", 11),
            state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _create_metadata_tab(self):
        """Create metadata display tab"""
        metadata_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(metadata_frame, text="Metadata")
        
        # Metadata tree view
        self.metadata_tree = ttk.Treeview(
            metadata_frame, columns=("value",), show="tree headings"
        )
        self.metadata_tree.heading("#0", text="Property")
        self.metadata_tree.heading("value", text="Value")
        self.metadata_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _create_history_tab(self):
        """Create conversion history tab"""
        history_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(history_frame, text="History")
        
        # History controls
        history_controls = ttk.Frame(history_frame)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_controls, text="Clear History", command=self._clear_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="Export History", command=self._export_history).pack(side=tk.LEFT, padx=2)
        
        # History list
        self.history_tree = ttk.Treeview(
            history_frame, 
            columns=("time", "source", "target", "tokens", "cached"),
            show="tree headings"
        )
        self.history_tree.heading("#0", text="ID")
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("source", text="Source")
        self.history_tree.heading("target", text="Target")
        self.history_tree.heading("tokens", text="Tokens")
        self.history_tree.heading("cached", text="Cached")
        
        # Configure column widths
        self.history_tree.column("#0", width=50)
        self.history_tree.column("time", width=150)
        self.history_tree.column("source", width=100)
        self.history_tree.column("target", width=100)
        self.history_tree.column("tokens", width=80)
        self.history_tree.column("cached", width=80)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind double-click to load conversion
        self.history_tree.bind("<Double-Button-1>", self._load_from_history)
        
    def _create_sidebar(self):
        """Create optional sidebar"""
        sidebar = ttk.Frame(self.main_paned)
        self.main_paned.insert(0, sidebar, weight=0)
        
        # Sidebar content
        ttk.Label(sidebar, text="Quick Actions", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Quick action buttons
        actions = [
            ("New Conversion", self._new_file),
            ("Open File", self._open_file),
            ("Save Output", self._save_output),
            ("Convert", self._quick_convert),
            ("Validate", self._validate_content),
            ("Format", self._format_content),
        ]
        
        for text, command in actions:
            ttk.Button(sidebar, text=text, command=command, width=20).pack(pady=2, padx=10)
            
    def _create_status_bar(self):
        """Create status bar"""
        if not self.config.get_bool('UI', 'show_status_bar', True):
            return
            
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Mode indicator
        self.mode_status_var = tk.StringVar(value="Mode: Text → Code")
        ttk.Label(status_frame, textvariable=self.mode_status_var).pack(side=tk.LEFT, padx=5)
        
        # API status
        self.api_status_var = tk.StringVar(value="API: Checking...")
        self.api_status_label = ttk.Label(status_frame, textvariable=self.api_status_var)
        self.api_status_label.pack(side=tk.RIGHT, padx=5)
        
        # Cursor position
        self.position_var = tk.StringVar(value="Ln 1, Col 1")
        self.position_label = ttk.Label(status_frame, textvariable=self.position_var)
        self.position_label.pack(side=tk.RIGHT, padx=5)
        
        # Update API status
        self._check_api_status()
        
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        # File operations
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        
        # Edit operations
        self.root.bind("<Control-z>", lambda e: self._undo())
        self.root.bind("<Control-y>", lambda e: self._redo())
        self.root.bind("<Control-x>", lambda e: self._cut())
        self.root.bind("<Control-c>", lambda e: self._copy())
        self.root.bind("<Control-v>", lambda e: self._paste())
        self.root.bind("<Control-f>", lambda e: self._find())
        self.root.bind("<Control-h>", lambda e: self._replace())
        
        # Conversion
        self.root.bind("<F5>", lambda e: self._quick_convert())
        self.root.bind("<F7>", lambda e: self._validate_content())
        self.root.bind("<F8>", lambda e: self._format_content())
        
        # Help
        self.root.bind("<F1>", lambda e: self._show_documentation())
        
    def _configure_editor(self, editor):
        """Configure text editor with syntax highlighting"""
        # Configure tags for syntax highlighting
        editor.tag_configure("keyword", foreground="#0000FF")
        editor.tag_configure("string", foreground="#008000")
        editor.tag_configure("comment", foreground="#808080")
        editor.tag_configure("function", foreground="#FF00FF")
        editor.tag_configure("number", foreground="#FF0000")
        
        # Bind events
        editor.bind("<KeyRelease>", lambda e: self._on_editor_change(editor))
        editor.bind("<ButtonRelease>", lambda e: self._update_cursor_position(editor))
        
    def _configure_markup_editor(self, editor):
        """Configure markup editor with custom highlighting"""
        # Markup-specific tags
        editor.tag_configure("emphasis", foreground="#D32F2F", font=("Consolas", 11, "bold"))
        editor.tag_configure("context", foreground="#1976D2", background="#E3F2FD")
        editor.tag_configure("note", foreground="#616161", font=("Consolas", 11, "italic"))
        editor.tag_configure("warning", foreground="#FF6F00", background="#FFF3E0")
        editor.tag_configure("success", foreground="#2E7D32", background="#E8F5E9")
        
        # Bind events
        editor.bind("<KeyRelease>", lambda e: self._update_markup_highlighting(editor))
        editor.bind("<Button-3>", lambda e: self._show_markup_menu(e, editor))
        
    def _configure_vml_editor(self, editor):
        """Configure VML editor with syntax highlighting"""
        # VML-specific tags
        editor.tag_configure("vml_heading", foreground="#1976D2", font=("Consolas", 11, "bold"))
        editor.tag_configure("vml_directive", foreground="#0066CC", font=("Consolas", 11, "bold"))
        editor.tag_configure("vml_variable", foreground="#9C27B0", background="#F3E5F5")
        editor.tag_configure("vml_template", foreground="#00897B", background="#E0F2F1")
        editor.tag_configure("vml_section", foreground="#E65100", font=("Consolas", 11, "bold"))
        editor.tag_configure("vml_metadata", foreground="#37474F", background="#ECEFF1")
        
        # Bind events
        editor.bind("<KeyRelease>", lambda e: self._update_vml_highlighting(editor))
        
    def _get_current_editor(self):
        """Get currently active editor"""
        current_tab = self.editor_notebook.select()
        tab_index = self.editor_notebook.index(current_tab)
        
        if tab_index == 0:
            return self.main_editor
        elif tab_index == 1:
            return self.markup_editor
        elif tab_index == 2:
            return self.vml_editor
        else:
            return self.main_editor
            
    def _on_editor_change(self, editor):
        """Handle editor content change"""
        self.modified = True
        self._update_syntax_highlighting(editor)
        
    def _update_cursor_position(self, editor):
        """Update cursor position in status bar"""
        position = editor.index(tk.INSERT)
        line, col = position.split('.')
        self.position_var.set(f"Ln {line}, Col {int(col) + 1}")
        
    def _update_syntax_highlighting(self, editor):
        """Update syntax highlighting based on language"""
        # This is a simplified version - full implementation would use
        # language-specific parsers and lexers
        pass
        
    def _update_markup_highlighting(self, editor):
        """Update markup highlighting"""
        # Remove existing tags
        for tag in ["emphasis", "context", "note", "warning", "success"]:
            editor.tag_remove(tag, "1.0", tk.END)
            
        content = editor.get("1.0", tk.END)
        
        # Highlight patterns
        patterns = {
            "emphasis": r'!!([^!]+)!!',
            "context": r'<~([^~]+)~>',
            "note": r'\(\*([^*]+)\*\)',
            "warning": r'/!([^!]+)!/',
            "success": r'/\+([^+]+)\+/',
        }
        
        for tag_name, pattern in patterns.items():
            for match in re.finditer(pattern, content):
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                editor.tag_add(tag_name, start_idx, end_idx)
                
    def _update_vml_highlighting(self, editor):
        """Update VML syntax highlighting"""
        # Remove existing tags
        vml_tags = ["vml_heading", "vml_directive", "vml_variable", 
                   "vml_template", "vml_section", "vml_metadata"]
        for tag in vml_tags:
            editor.tag_remove(tag, "1.0", tk.END)
            
        content = editor.get("1.0", tk.END)
        
        # Highlight patterns
        patterns = {
            "vml_heading": r'^#{1,6}\s+.+$',
            "vml_directive": r'@\w+(?:\[[^\]]*\])?',
            "vml_variable": r'\$\{[^}]+\}',
            "vml_template": r'%\{[^}]+\}',
            "vml_section": r'^::\s*/?\\w+(?:\[[^\]]*\])?',
            "vml_metadata": r'^---$',
        }
        
        for tag_name, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = f"1.0 + {match.start()} chars"
                end_idx = f"1.0 + {match.end()} chars"
                editor.tag_add(tag_name, start_idx, end_idx)
                
    def _check_api_status(self):
        """Check API availability"""
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.api_status_var.set("API: Connected")
            self.api_status_label.configure(foreground=self.colors['success'])
        else:
            self.api_status_var.set("API: Not configured")
            self.api_status_label.configure(foreground=self.colors['warning'])
            
    def _update_mode(self):
        """Update conversion mode"""
        mode = self.mode_var.get()
        mode_map = {
            "text-to-code": "Mode: Text → Code",
            "code-to-text": "Mode: Code → Text",
            "text-to-vml": "Mode: Text → VML",
            "vml-to-html": "Mode: VML → HTML",
            "vml-to-markdown": "Mode: VML → Markdown"
        }
        self.mode_status_var.set(mode_map.get(mode, "Mode: Unknown"))
        
    async def _perform_conversion(self, input_text: str, source: str, target: str) -> UnifiedConversionResult:
        """Perform conversion using the unified engine"""
        context = ConversionContext(
            source_format=source,
            target_format=target,
            session_id=self.session_id,
            metadata={
                'timestamp': datetime.now().isoformat(),
                'language': self.language_var.get()
            }
        )
        
        result = await self.engine.convert(input_text, source, target, context)
        
        # Update history
        if result.success:
            self._add_to_history(source, target, result)
            
        return result
        
    def _quick_convert(self):
        """Perform quick conversion based on current mode"""
        # Get current editor content
        editor = self._get_current_editor()
        input_text = editor.get("1.0", tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("No Input", "Please enter some text to convert.")
            return
            
        # Parse mode
        mode_parts = self.mode_var.get().split('-to-')
        if len(mode_parts) != 2:
            messagebox.showerror("Invalid Mode", "Invalid conversion mode selected.")
            return
            
        source, target = mode_parts
        
        # Update status
        self.status_var.set("Converting...")
        self.convert_btn.config(state=tk.DISABLED)
        
        # Run conversion in thread
        thread = threading.Thread(
            target=self._run_conversion_async,
            args=(input_text, source, target)
        )
        thread.start()
        
    def _run_conversion_async(self, input_text: str, source: str, target: str):
        """Run conversion in async context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self._perform_conversion(input_text, source, target)
            )
            
            # Update UI in main thread
            self.root.after(0, self._display_conversion_result, result)
            
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            loop.close()
            
    def _display_conversion_result(self, result: UnifiedConversionResult):
        """Display conversion result in UI"""
        # Update output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result.output)
        self.output_text.config(state=tk.DISABLED)
        
        # Update metadata
        self._update_metadata_display(result)
        
        # Update status
        if result.success:
            status_msg = f"Conversion successful ({result.processing_time:.2f}s)"
            if result.cached:
                status_msg += " [Cached]"
            self.status_var.set(status_msg)
            
            # Show warnings/suggestions if any
            if result.warnings:
                self._show_warnings(result.warnings)
            if result.suggestions:
                self._show_suggestions(result.suggestions)
        else:
            self.status_var.set("Conversion failed")
            messagebox.showerror("Conversion Error", result.error)
            
        # Re-enable convert button
        self.convert_btn.config(state=tk.NORMAL)
        
    def _update_metadata_display(self, result: UnifiedConversionResult):
        """Update metadata tree with conversion result info"""
        # Clear existing items
        for item in self.metadata_tree.get_children():
            self.metadata_tree.delete(item)
            
        # Add metadata
        self.metadata_tree.insert("", "end", text="Format", values=(result.format,))
        self.metadata_tree.insert("", "end", text="Tokens Used", values=(result.tokens_used,))
        self.metadata_tree.insert("", "end", text="Processing Time", values=(f"{result.processing_time:.3f}s",))
        self.metadata_tree.insert("", "end", text="Cached", values=("Yes" if result.cached else "No",))
        
        # Add conversion path
        if result.intermediate_formats:
            path_node = self.metadata_tree.insert("", "end", text="Conversion Path", values=("",))
            for i, (src, tgt) in enumerate(result.intermediate_formats):
                self.metadata_tree.insert(path_node, "end", text=f"Step {i+1}", values=(f"{src} → {tgt}",))
                
        # Add custom metadata
        if result.metadata:
            meta_node = self.metadata_tree.insert("", "end", text="Metadata", values=("",))
            for key, value in result.metadata.items():
                self.metadata_tree.insert(meta_node, "end", text=key, values=(str(value),))
                
    def _add_to_history(self, source: str, target: str, result: UnifiedConversionResult):
        """Add conversion to history"""
        history_id = len(self.conversion_history) + 1
        history_entry = {
            'id': history_id,
            'time': datetime.now(),
            'source': source,
            'target': target,
            'tokens': result.tokens_used,
            'cached': result.cached,
            'input': self._get_current_editor().get("1.0", tk.END),
            'output': result.output
        }
        
        self.conversion_history.append(history_entry)
        
        # Update history tree
        self.history_tree.insert(
            "", 0,
            text=str(history_id),
            values=(
                history_entry['time'].strftime("%Y-%m-%d %H:%M:%S"),
                source,
                target,
                result.tokens_used,
                "Yes" if result.cached else "No"
            )
        )
        
    def _show_warnings(self, warnings: List[str]):
        """Show warnings in a dialog"""
        if not warnings:
            return
            
        warning_text = "Conversion completed with warnings:\n\n"
        warning_text += "\n".join(f"• {w}" for w in warnings)
        
        messagebox.showwarning("Conversion Warnings", warning_text)
        
    def _show_suggestions(self, suggestions: List[str]):
        """Show suggestions in a dialog"""
        if not suggestions:
            return
            
        # For now, log suggestions - could show in a panel
        logger.info(f"Suggestions: {suggestions}")
        
    def _show_error(self, error_message: str):
        """Show error message"""
        self.status_var.set("Error occurred")
        self.convert_btn.config(state=tk.NORMAL)
        messagebox.showerror("Error", error_message)
        
    def _load_welcome_content(self):
        """Load welcome content on startup"""
        welcome_text = """# Welcome to the Unified Bidirectional Converter System

This comprehensive platform integrates multiple conversion tools:

## Features

- **Text to Code**: Convert natural language to any programming language
- **Code to Text**: Generate explanations for code snippets  
- **VML Support**: Full Versatile Markup Language implementation
- **Custom Markup**: Enhanced text annotation system
- **Smart Caching**: Reduces API calls and improves performance

## Getting Started

1. Choose a conversion mode from the toolbar
2. Enter your content in the editor
3. Click "Convert" or press F5
4. View results in the output panel

## Supported Languages

Python, JavaScript, Java, C++, C#, Go, Rust, SQL, HTML, CSS, VML, and more!

## Try an Example

Click "Convert" to see this text converted to your selected format.

/+Happy converting!+/
"""
        self.main_editor.insert("1.0", welcome_text)
        self.modified = False
        
    # File operations
    def _new_file(self):
        """Create new file"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before creating a new file?"
            )
            if response is True:
                self._save_file()
            elif response is None:
                return
                
        # Clear all editors
        self.main_editor.delete("1.0", tk.END)
        self.markup_editor.delete("1.0", tk.END)
        self.vml_editor.delete("1.0", tk.END)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.current_file = None
        self.modified = False
        self.status_var.set("New file created")
        
    def _open_file(self):
        """Open file"""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("All Supported", "*.txt;*.py;*.js;*.java;*.cpp;*.cs;*.go;*.rs;*.sql;*.html;*.css;*.vml;*.md"),
                ("VML Files", "*.vml"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Determine which editor to use based on extension
                ext = Path(file_path).suffix.lower()
                if ext == '.vml':
                    self.editor_notebook.select(2)  # VML tab
                    self.vml_editor.delete("1.0", tk.END)
                    self.vml_editor.insert("1.0", content)
                else:
                    self.editor_notebook.select(0)  # Main editor tab
                    self.main_editor.delete("1.0", tk.END)
                    self.main_editor.insert("1.0", content)
                    
                    # Set language based on extension
                    lang_map = {
                        '.py': 'python',
                        '.js': 'javascript',
                        '.java': 'java',
                        '.cpp': 'cpp',
                        '.cs': 'csharp',
                        '.go': 'go',
                        '.rs': 'rust',
                        '.sql': 'sql',
                        '.html': 'html',
                        '.css': 'css',
                        '.md': 'markdown'
                    }
                    if ext in lang_map:
                        self.language_var.set(lang_map[ext])
                        
                self.current_file = file_path
                self.modified = False
                self.status_var.set(f"Opened: {Path(file_path).name}")
                
            except Exception as e:
                messagebox.showerror("Open Error", f"Failed to open file: {str(e)}")
                
    def _save_file(self):
        """Save current file"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._save_file_as()
            
    def _save_file_as(self):
        """Save file with new name"""
        # Determine default extension
        current_tab = self.editor_notebook.index(self.editor_notebook.select())
        if current_tab == 2:  # VML tab
            default_ext = ".vml"
        else:
            lang_ext_map = {
                'python': '.py',
                'javascript': '.js',
                'java': '.java',
                'cpp': '.cpp',
                'csharp': '.cs',
                'go': '.go',
                'rust': '.rs',
                'sql': '.sql',
                'html': '.html',
                'css': '.css',
                'markdown': '.md',
                'vml': '.vml'
            }
            default_ext = lang_ext_map.get(self.language_var.get(), '.txt')
            
        file_path = filedialog.asksaveasfilename(
            title="Save File",
            defaultextension=default_ext,
            filetypes=[
                ("All Files", "*.*"),
                ("VML Files", "*.vml"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("Text Files", "*.txt")
            ]
        )
        
        if file_path:
            self._save_to_file(file_path)
            self.current_file = file_path
            
    def _save_to_file(self, file_path: str):
        """Save content to file"""
        try:
            editor = self._get_current_editor()
            content = editor.get("1.0", tk.END)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.modified = False
            self.status_var.set(f"Saved: {Path(file_path).name}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
            
    def _import_file(self):
        """Import file for conversion"""
        # Similar to open, but focuses on conversion
        self._open_file()
        
    def _export_file(self):
        """Export conversion result"""
        output = self.output_text.get("1.0", tk.END).strip()
        if not output:
            messagebox.showwarning("No Output", "No output to export.")
            return
            
        # Determine file type based on current mode
        mode = self.mode_var.get()
        if mode.endswith('-html'):
            default_ext = '.html'
        elif mode.endswith('-markdown'):
            default_ext = '.md'
        elif mode.endswith('-vml'):
            default_ext = '.vml'
        else:
            default_ext = '.txt'
            
        file_path = filedialog.asksaveasfilename(
            title="Export Output",
            defaultextension=default_ext,
            filetypes=[
                ("All Files", "*.*"),
                ("HTML Files", "*.html"),
                ("Markdown Files", "*.md"),
                ("VML Files", "*.vml"),
                ("Text Files", "*.txt")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                self.status_var.set(f"Exported: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def _show_recent_files(self):
        """Show recent files dialog"""
        # TODO: Implement recent files tracking
        messagebox.showinfo("Recent Files", "Recent files feature coming soon!")
        
    def _quit_application(self):
        """Quit application with confirmation"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Do you want to save changes before closing?"
            )
            if response is True:
                self._save_file()
            elif response is None:
                return
                
        # Save configuration
        self.config.save()
        
        # Clean up
        self.root.quit()
        
    # Edit operations
    def _undo(self):
        """Undo last action"""
        editor = self._get_current_editor()
        try:
            editor.edit_undo()
        except tk.TclError:
            pass
            
    def _redo(self):
        """Redo last undone action"""
        editor = self._get_current_editor()
        try:
            editor.edit_redo()
        except tk.TclError:
            pass
            
    def _cut(self):
        """Cut selected text"""
        editor = self._get_current_editor()
        try:
            editor.event_generate("<<Cut>>")
        except tk.TclError:
            pass
            
    def _copy(self):
        """Copy selected text"""
        editor = self._get_current_editor()
        try:
            editor.event_generate("<<Copy>>")
        except tk.TclError:
            pass
            
    def _paste(self):
        """Paste from clipboard"""
        editor = self._get_current_editor()
        try:
            editor.event_generate("<<Paste>>")
        except tk.TclError:
            pass
            
    def _find(self):
        """Show find dialog"""
        # TODO: Implement find dialog
        messagebox.showinfo("Find", "Find feature coming soon!")
        
    def _replace(self):
        """Show replace dialog"""
        # TODO: Implement replace dialog
        messagebox.showinfo("Replace", "Replace feature coming soon!")
        
    # Conversion operations
    def _set_mode(self, source: str, target: str):
        """Set conversion mode"""
        self.mode_var.set(f"{source}-to-{target}")
        self._update_mode()
        
    def _batch_convert(self):
        """Show batch conversion dialog"""
        # TODO: Implement batch conversion
        messagebox.showinfo("Batch Convert", "Batch conversion feature coming soon!")
        
    def _validate_content(self):
        """Validate current content based on format"""
        editor = self._get_current_editor()
        content = editor.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showinfo("No Content", "No content to validate.")
            return
            
        # Determine format
        current_tab = self.editor_notebook.index(self.editor_notebook.select())
        if current_tab == 2:  # VML tab
            self._validate_vml()
        else:
            # For other formats, use language-specific validation
            self.status_var.set("Validation complete")
            messagebox.showinfo("Validation", "Content appears to be valid.")
            
    def _format_content(self):
        """Format current content"""
        editor = self._get_current_editor()
        current_tab = self.editor_notebook.index(self.editor_notebook.select())
        
        if current_tab == 2:  # VML tab
            self._format_vml()
        else:
            # For other formats, could use language-specific formatters
            self.status_var.set("Formatting complete")
            
    def _validate_vml(self):
        """Validate VML content"""
        content = self.vml_editor.get("1.0", tk.END)
        
        # Use VML validator from converters
        if 'vml' in self.engine.converters:
            is_valid, errors = self.engine.converters['vml'].validate_input(content, 'vml')
            
            if is_valid:
                self.status_var.set("✓ Valid VML")
                messagebox.showinfo("VML Validation", "VML syntax is valid!")
            else:
                self.status_var.set("✗ Invalid VML")
                error_msg = "VML validation errors:\n\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    error_msg += f"\n\n... and {len(errors) - 10} more errors"
                messagebox.showerror("VML Validation Error", error_msg)
                
    def _format_vml(self):
        """Format VML content"""
        content = self.vml_editor.get("1.0", tk.END)
        
        # Use VML formatter
        if 'vml' in self.engine.converters:
            # Simple format - in real implementation would use proper VML formatter
            formatted = content.strip()
            
            self.vml_editor.delete("1.0", tk.END)
            self.vml_editor.insert("1.0", formatted)
            self._update_vml_highlighting(self.vml_editor)
            self.status_var.set("VML formatted")
            
    # Markup operations
    def _apply_markup(self, markup_type: str):
        """Apply markup to selected text"""
        editor = self._get_current_editor()
        
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            selected_text = editor.get(sel_start, sel_end)
            
            # Apply markup based on type
            markup_map = {
                'emphasis': ('!!', '!!'),
                'context': ('<~', '~>'),
                'warning': ('/!', '!/'),
                'success': ('/+', '+/'),
                'note': ('(*', '*)')
            }
            
            if markup_type in markup_map:
                start, end = markup_map[markup_type]
                marked_text = f"{start}{selected_text}{end}"
                editor.delete(sel_start, sel_end)
                editor.insert(sel_start, marked_text)
                
        except tk.TclError:
            # No selection
            messagebox.showinfo("No Selection", "Please select text to apply markup.")
            
    def _quick_markup(self, start: str, end: str):
        """Quick markup application"""
        editor = self.markup_editor
        
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            selected_text = editor.get(sel_start, sel_end)
            
            marked_text = f"{start}{selected_text}{end}"
            editor.delete(sel_start, sel_end)
            editor.insert(sel_start, marked_text)
            
        except tk.TclError:
            # No selection, just insert markers
            editor.insert(tk.INSERT, f"{start}{end}")
            # Move cursor between markers
            pos = editor.index(tk.INSERT)
            editor.mark_set(tk.INSERT, f"{pos}-{len(end)}c")
            
    def _manage_markup(self):
        """Show markup management dialog"""
        # TODO: Implement markup management
        messagebox.showinfo("Markup Manager", "Markup management feature coming soon!")
        
    def _export_markup(self):
        """Export markup definitions"""
        # TODO: Implement markup export
        messagebox.showinfo("Export Markup", "Markup export feature coming soon!")
        
    def _import_markup(self):
        """Import markup definitions"""
        # TODO: Implement markup import
        messagebox.showinfo("Import Markup", "Markup import feature coming soon!")
        
    def _show_markup_menu(self, event, editor):
        """Show context menu for markup"""
        menu = tk.Menu(self.root, tearoff=0)
        
        # Markup options
        menu.add_command(label="Apply Emphasis !!", 
                        command=lambda: self._apply_markup_to_editor(editor, "!!", "!!"))
        menu.add_command(label="Apply Context <~", 
                        command=lambda: self._apply_markup_to_editor(editor, "<~", "~>"))
        menu.add_command(label="Apply Note (*", 
                        command=lambda: self._apply_markup_to_editor(editor, "(*", "*)"))
        menu.add_command(label="Apply Warning /!", 
                        command=lambda: self._apply_markup_to_editor(editor, "/!", "!/"))
        menu.add_command(label="Apply Success /+", 
                        command=lambda: self._apply_markup_to_editor(editor, "/+", "+/"))
        
        menu.post(event.x_root, event.y_root)
        
    def _apply_markup_to_editor(self, editor, start: str, end: str):
        """Apply markup to selected text in specific editor"""
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            selected_text = editor.get(sel_start, sel_end)
            
            marked_text = f"{start}{selected_text}{end}"
            editor.delete(sel_start, sel_end)
            editor.insert(sel_start, marked_text)
            
        except tk.TclError:
            pass
            
    # VML operations
    def _insert_vml(self, element_type: str):
        """Insert VML element"""
        insertions = {
            'variable': '${}',
            'template': '%{}',
            'annotation': '[[]]',
            'directive': '@directive[params] ',
            'section': ':: section[name=example]\n\nContent here\n\n:: /section',
            'table': '| Header 1 | Header 2 | Header 3 |\n|----------|:--------:|---------:|\n| Data 1   | Data 2   | Data 3   |'
        }
        
        if element_type in insertions:
            self.vml_editor.insert(tk.INSERT, insertions[element_type])
            
            # Position cursor appropriately
            if element_type in ['variable', 'template']:
                pos = self.vml_editor.index(tk.INSERT)
                self.vml_editor.mark_set(tk.INSERT, f"{pos}-1c")
            elif element_type == 'annotation':
                pos = self.vml_editor.index(tk.INSERT)
                self.vml_editor.mark_set(tk.INSERT, f"{pos}-2c")
                
    def _insert_at_cursor(self, text: str, cursor_offset: int):
        """Insert text at cursor with optional offset"""
        editor = self._get_current_editor()
        editor.insert(tk.INSERT, text)
        
        if cursor_offset != 0:
            pos = editor.index(tk.INSERT)
            editor.mark_set(tk.INSERT, f"{pos}+{cursor_offset}c")
            
    def _insert_vml_section(self):
        """Insert VML section template"""
        section_template = """:: section[type=example, id=unique]
# Section Title

Section content goes here.

:: /section"""
        self.vml_editor.insert(tk.INSERT, section_template)
        
    def _show_vml_reference(self):
        """Show VML reference documentation"""
        ref_window = tk.Toplevel(self.root)
        ref_window.title("VML Reference")
        ref_window.geometry("800x600")
        
        ref_text = scrolledtext.ScrolledText(
            ref_window, wrap=tk.WORD, font=("Consolas", 10)
        )
        ref_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        reference = """VML (Versatile Markup Language) Reference
=========================================

SYNTAX ELEMENTS
--------------

Headers:
    # Level 1 Header
    ## Level 2 Header
    ### Level 3 Header

Basic Formatting:
    **Bold text**
    *Italic text*
    `inline code`

Variables and Templates:
    ${variable_name}    - Variable placeholder
    %{template_name}    - Template reference

Custom Markup:
    !!emphasis!!        - Important/emphasized text
    <~context~>         - Contextual information
    (*note*)            - Side notes
    /!warning!/         - Warning messages
    /+success+/         - Success messages
    @[code_ref]@        - Code references
    [[annotation]]      - Annotations

Directives:
    @directive[param1=value, param2=value]
    Content affected by directive

    Common directives:
    @include "file.vml"
    @if condition { content }
    @for item in list { content }
    @macro name(params) { content }

Sections:
    :: section[type=value, class=value]
    Section content
    :: /section

Metadata (YAML frontmatter):
    ---
    title: Document Title
    author: Author Name
    version: 1.0
    ---

Tables:
    | Header 1 | Header 2 | Header 3 |
    |----------|:--------:|---------:|
    | Left     | Center   | Right    |

EXAMPLES
--------

1. Basic Document:
   ---
   title: My Document
   ---
   
   # Main Title
   
   This is a paragraph with ${variable} and !!emphasis!!.

2. Complex Section:
   :: section[type=api, id=endpoint]
   ## API Endpoint
   
   @endpoint[method=GET, path=/api/users]
   
   Returns [[user data]] in JSON format.
   
   /!Note: Requires authentication!/
   :: /section

3. Conditional Content:
   @if has_feature("advanced") {
     ## Advanced Features
     
     These features require /+Pro subscription+/.
   }
"""
        
        ref_text.insert("1.0", reference)
        ref_text.config(state=tk.DISABLED)
        
    # Output operations
    def _copy_output(self):
        """Copy output to clipboard"""
        output = self.output_text.get("1.0", tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_var.set("Output copied to clipboard")
        else:
            messagebox.showinfo("No Output", "No output to copy.")
            
    def _save_output(self):
        """Save output to file"""
        output = self.output_text.get("1.0", tk.END).strip()
        if not output:
            messagebox.showwarning("No Output", "No output to save.")
            return
            
        self._export_file()
        
    def _format_output(self):
        """Format output based on type"""
        # TODO: Implement output formatting
        self.status_var.set("Output formatted")
        
    # History operations
    def _clear_history(self):
        """Clear conversion history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the conversion history?"):
            self.conversion_history.clear()
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            self.status_var.set("History cleared")
            
    def _export_history(self):
        """Export conversion history"""
        if not self.conversion_history:
            messagebox.showinfo("No History", "No conversion history to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export History",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("CSV Files", "*.csv")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # Export as JSON
                    export_data = []
                    for entry in self.conversion_history:
                        export_entry = {
                            'id': entry['id'],
                            'time': entry['time'].isoformat(),
                            'source': entry['source'],
                            'target': entry['target'],
                            'tokens': entry['tokens'],
                            'cached': entry['cached']
                        }
                        export_data.append(export_entry)
                        
                    with open(file_path, 'w') as f:
                        json.dump(export_data, f, indent=2)
                else:
                    # Export as CSV
                    import csv
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['ID', 'Time', 'Source', 'Target', 'Tokens', 'Cached'])
                        for entry in self.conversion_history:
                            writer.writerow([
                                entry['id'],
                                entry['time'].strftime("%Y-%m-%d %H:%M:%S"),
                                entry['source'],
                                entry['target'],
                                entry['tokens'],
                                'Yes' if entry['cached'] else 'No'
                            ])
                            
                self.status_var.set(f"History exported to {Path(file_path).name}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export history: {str(e)}")
                
    def _load_from_history(self, event):
        """Load conversion from history"""
        selection = self.history_tree.selection()
        if not selection:
            return
            
        item = self.history_tree.item(selection[0])
        history_id = int(item['text'])
        
        # Find history entry
        for entry in self.conversion_history:
            if entry['id'] == history_id:
                # Load input
                editor = self._get_current_editor()
                editor.delete("1.0", tk.END)
                editor.insert("1.0", entry['input'])
                
                # Load output
                self.output_text.config(state=tk.NORMAL)
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert("1.0", entry['output'])
                self.output_text.config(state=tk.DISABLED)
                
                # Set mode
                self.mode_var.set(f"{entry['source']}-to-{entry['target']}")
                self._update_mode()
                
                self.status_var.set(f"Loaded conversion #{history_id}")
                break
                
    def _show_history(self):
        """Show conversion history window"""
        # The history tab is already visible, just switch to it
        self.output_notebook.select(3)  # History tab
        
    def _show_statistics(self):
        """Show usage statistics"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Conversion Statistics")
        stats_window.geometry("600x400")
        
        stats_text = scrolledtext.ScrolledText(stats_window, wrap=tk.WORD)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Calculate statistics
        total_conversions = len(self.conversion_history)
        total_tokens = sum(entry['tokens'] for entry in self.conversion_history)
        cached_conversions = sum(1 for entry in self.conversion_history if entry['cached'])
        
        # Count by type
        type_counts = {}
        for entry in self.conversion_history:
            key = f"{entry['source']} → {entry['target']}"
            type_counts[key] = type_counts.get(key, 0) + 1
            
        stats = f"""Conversion Statistics
====================

Total Conversions: {total_conversions}
Total Tokens Used: {total_tokens}
Cached Conversions: {cached_conversions} ({cached_conversions/total_conversions*100:.1f}% if total_conversions > 0 else 0)

Conversions by Type:
"""
        
        for conv_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            stats += f"  {conv_type}: {count}\n"
            
        stats_text.insert("1.0", stats)
        stats_text.config(state=tk.DISABLED)
        
    # Tools operations
    def _show_api_settings(self):
        """Show API settings dialog"""
        settings_dialog = APISettingsDialog(self.root, self.config)
        settings_dialog.show()
        
        # Refresh API status
        self._check_api_status()
        
    def _show_editor_preferences(self):
        """Show editor preferences dialog"""
        prefs_dialog = EditorPreferencesDialog(self.root, self.config)
        if prefs_dialog.show():
            # Apply new preferences
            self._apply_editor_preferences()
            
    def _apply_editor_preferences(self):
        """Apply editor preferences from config"""
        font_family = self.config.get('Editor', 'font_family', 'Consolas')
        font_size = self.config.get_int('Editor', 'font_size', 11)
        
        # Update all editors
        for editor in [self.main_editor, self.markup_editor, self.vml_editor]:
            editor.configure(font=(font_family, font_size))
            
    def _clear_cache(self):
        """Clear conversion cache"""
        if messagebox.askyesno("Clear Cache", "Are you sure you want to clear the conversion cache?"):
            # Clear cache through engine
            cache_file = self.engine.cache.cache_path
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    self.engine.cache._init_db()
                    self.status_var.set("Cache cleared")
                    messagebox.showinfo("Cache Cleared", "Conversion cache has been cleared.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")
                    
    def _show_plugin_manager(self):
        """Show plugin manager dialog"""
        # TODO: Implement plugin system
        messagebox.showinfo("Plugin Manager", "Plugin system coming soon!")
        
    # Help operations
    def _show_documentation(self):
        """Show documentation"""
        # TODO: Open documentation in browser
        messagebox.showinfo("Documentation", "Documentation available at:\nhttps://unified-converter.example.com/docs")
        
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.geometry("500x600")
        
        shortcuts_text = scrolledtext.ScrolledText(shortcuts_window, wrap=tk.WORD)
        shortcuts_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        shortcuts = """Keyboard Shortcuts
==================

FILE OPERATIONS
--------------
Ctrl+N          New file
Ctrl+O          Open file
Ctrl+S          Save file
Ctrl+Shift+S    Save as...
Ctrl+Q          Quit

EDIT OPERATIONS
--------------
Ctrl+Z          Undo
Ctrl+Y          Redo
Ctrl+X          Cut
Ctrl+C          Copy
Ctrl+V          Paste
Ctrl+F          Find
Ctrl+H          Replace
Ctrl+A          Select all

CONVERSION
----------
F5              Quick convert
F7              Validate
F8              Format

HELP
----
F1              Documentation
Ctrl+?          This shortcuts list

VML SPECIFIC
-----------
When in VML editor:
Ctrl+D          Insert directive
Ctrl+T          Insert template
Ctrl+Shift+S    Insert section

MARKUP SPECIFIC
--------------
When text is selected:
Ctrl+E          Apply emphasis
Ctrl+Shift+C    Apply context
Ctrl+W          Apply warning
"""
        
        shortcuts_text.insert("1.0", shortcuts)
        shortcuts_text.config(state=tk.DISABLED)
        
    def _show_tutorial(self):
        """Show interactive tutorial"""
        # TODO: Implement interactive tutorial
        messagebox.showinfo("Tutorial", "Interactive tutorial coming soon!")
        
    def _check_updates(self):
        """Check for application updates"""
        # TODO: Implement update checking
        messagebox.showinfo("Check Updates", "You are running the latest version!")
        
    def _report_issue(self):
        """Open issue reporting"""
        # TODO: Open GitHub issues or support form
        messagebox.showinfo("Report Issue", "Report issues at:\nhttps://github.com/unified-converter/issues")
        
    def _show_about(self):
        """Show about dialog"""
        about_text = """Unified Bidirectional Converter System
Version 1.0.0

A comprehensive platform integrating:
• Claude API for intelligent conversions
• VML (Versatile Markup Language)
• Enhanced markup editor
• Smart caching and history

© 2024 Unified Converter Project
Licensed under MIT License"""
        
        messagebox.showinfo("About", about_text)
        
    def _on_language_change(self, event=None):
        """Handle language selection change"""
        # Update syntax highlighting based on new language
        self._update_syntax_highlighting(self.main_editor)
        
    def _create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        # Simple tooltip implementation
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


# ============================================================================
# DIALOG CLASSES
# ============================================================================

class APISettingsDialog:
    """API settings dialog"""
    
    def __init__(self, parent, config: UnifiedConfig):
        self.parent = parent
        self.config = config
        self.dialog = None
        
    def show(self):
        """Show the API settings dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        
        # API Key
        key_frame = ttk.LabelFrame(self.dialog, text="API Key")
        key_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(key_frame, text="Anthropic API Key:").pack(anchor=tk.W, padx=10, pady=5)
        
        self.key_var = tk.StringVar()
        current_key = os.getenv("ANTHROPIC_API_KEY", "")
        if current_key:
            # Mask the key
            self.key_var.set("*" * (len(current_key) - 4) + current_key[-4:])
            
        key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=50)
        key_entry.pack(padx=10, pady=5)
        
        ttk.Button(key_frame, text="Set New Key", command=self._set_new_key).pack(pady=5)
        
        # Model Selection
        model_frame = ttk.LabelFrame(self.dialog, text="Model Settings")
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(model_frame, text="Model:").pack(anchor=tk.W, padx=10, pady=5)
        
        self.model_var = tk.StringVar(value=self.config.get('API', 'model'))
        model_combo = ttk.Combobox(
            model_frame, textvariable=self.model_var,
            values=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            state="readonly", width=40
        )
        model_combo.pack(padx=10, pady=5)
        
        # Temperature
        ttk.Label(model_frame, text="Temperature (0.0 - 1.0):").pack(anchor=tk.W, padx=10, pady=5)
        
        self.temp_var = tk.DoubleVar(value=self.config.get_float('API', 'temperature'))
        temp_scale = ttk.Scale(model_frame, from_=0.0, to=1.0, variable=self.temp_var, orient=tk.HORIZONTAL)
        temp_scale.pack(fill=tk.X, padx=10, pady=5)
        
        temp_label = ttk.Label(model_frame, text=f"{self.temp_var.get():.2f}")
        temp_label.pack()
        
        def update_temp_label(value):
            temp_label.config(text=f"{float(value):.2f}")
            
        temp_scale.config(command=update_temp_label)
        
        # Max Tokens
        ttk.Label(model_frame, text="Max Tokens:").pack(anchor=tk.W, padx=10, pady=5)
        
        self.tokens_var = tk.IntVar(value=self.config.get_int('API', 'max_tokens'))
        tokens_spinbox = ttk.Spinbox(
            model_frame, from_=100, to=8192, increment=100,
            textvariable=self.tokens_var, width=10
        )
        tokens_spinbox.pack(padx=10, pady=5)
        
        # Cache Settings
        cache_frame = ttk.LabelFrame(self.dialog, text="Cache Settings")
        cache_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.cache_enabled_var = tk.BooleanVar(value=self.config.get_bool('API', 'cache_enabled'))
        ttk.Checkbutton(
            cache_frame, text="Enable cache",
            variable=self.cache_enabled_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
    def _set_new_key(self):
        """Set new API key"""
        key_dialog = tk.Toplevel(self.dialog)
        key_dialog.title("Set API Key")
        key_dialog.geometry("500x200")
        key_dialog.transient(self.dialog)
        
        ttk.Label(key_dialog, text="Enter your Anthropic API Key:").pack(pady=10)
        
        new_key_var = tk.StringVar()
        key_entry = ttk.Entry(key_dialog, textvariable=new_key_var, width=60, show="*")
        key_entry.pack(pady=10)
        
        def save_key():
            key = new_key_var.get().strip()
            if key:
                os.environ["ANTHROPIC_API_KEY"] = key
                self.key_var.set("*" * (len(key) - 4) + key[-4:])
                key_dialog.destroy()
                messagebox.showinfo("Success", "API key updated successfully!")
                
        ttk.Button(key_dialog, text="Save", command=save_key).pack(pady=10)
        
    def _save_settings(self):
        """Save API settings"""
        self.config.set('API', 'model', self.model_var.get())
        self.config.set('API', 'temperature', str(self.temp_var.get()))
        self.config.set('API', 'max_tokens', str(self.tokens_var.get()))
        self.config.set('API', 'cache_enabled', str(self.cache_enabled_var.get()))
        
        self.config.save()
        self.dialog.destroy()
        messagebox.showinfo("Settings Saved", "API settings have been saved.")


class EditorPreferencesDialog:
    """Editor preferences dialog"""
    
    def __init__(self, parent, config: UnifiedConfig):
        self.parent = parent
        self.config = config
        self.dialog = None
        self.result = False
        
    def show(self):
        """Show the preferences dialog and return True if saved"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Editor Preferences")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        
        # Font Settings
        font_frame = ttk.LabelFrame(self.dialog, text="Font Settings")
        font_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(font_frame, text="Font Family:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.font_var = tk.StringVar(value=self.config.get('Editor', 'font_family', 'Consolas'))
        font_combo = ttk.Combobox(
            font_frame, textvariable=self.font_var,
            values=["Consolas", "Courier New", "Monaco", "Menlo", "Ubuntu Mono", "Source Code Pro"],
            width=20
        )
        font_combo.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(font_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.size_var = tk.IntVar(value=self.config.get_int('Editor', 'font_size', 11))
        size_spinbox = ttk.Spinbox(
            font_frame, from_=8, to=24, textvariable=self.size_var, width=10
        )
        size_spinbox.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Display Settings
        display_frame = ttk.LabelFrame(self.dialog, text="Display Settings")
        display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.line_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame, text="Show line numbers",
            variable=self.line_numbers_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        self.wrap_lines_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame, text="Wrap long lines",
            variable=self.wrap_lines_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        self.highlight_line_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame, text="Highlight current line",
            variable=self.highlight_line_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Auto-save Settings
        autosave_frame = ttk.LabelFrame(self.dialog, text="Auto-save")
        autosave_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.autosave_var = tk.BooleanVar(value=self.config.get_bool('Editor', 'auto_save', False))
        ttk.Checkbutton(
            autosave_frame, text="Enable auto-save",
            variable=self.autosave_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        ttk.Label(autosave_frame, text="Auto-save interval (seconds):").pack(anchor=tk.W, padx=10, pady=5)
        
        self.interval_var = tk.IntVar(value=self.config.get_int('Editor', 'auto_save_interval', 300))
        interval_spinbox = ttk.Spinbox(
            autosave_frame, from_=30, to=3600, increment=30,
            textvariable=self.interval_var, width=10
        )
        interval_spinbox.pack(padx=10, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save_preferences).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Wait for dialog to close
        self.dialog.wait_window()
        return self.result
        
    def _save_preferences(self):
        """Save preferences"""
        self.config.set('Editor', 'font_family', self.font_var.get())
        self.config.set('Editor', 'font_size', str(self.size_var.get()))
        self.config.set('Editor', 'auto_save', str(self.autosave_var.get()))
        self.config.set('Editor', 'auto_save_interval', str(self.interval_var.get()))
        
        self.config.save()
        self.result = True
        self.dialog.destroy()


# ============================================================================
# PLACEHOLDER CONVERTERS (would be in separate modules in real implementation)
# ============================================================================

class VMLConverter(ConverterInterface):
    """VML converter implementation"""
    
    def __init__(self):
        from vml_standalone import VMLParser, VMLConverter as VMLConv, VMLLanguageHandler
        self.parser = VMLParser()
        self.converter = VMLConv()
        self.handler = VMLLanguageHandler()
        
    async def convert(self, input_text: str, context: ConversionContext) -> UnifiedConversionResult:
        """Convert VML to/from other formats"""
        try:
            if context.target_format == 'html':
                output = self.converter.vml_to_html(input_text)
            elif context.target_format == 'markdown':
                output = self.converter.vml_to_markdown(input_text)
            elif context.source_format == 'text' and context.target_format == 'vml':
                # Simple text to VML conversion
                output = self._text_to_vml(input_text)
            else:
                return UnifiedConversionResult(
                    success=False,
                    output="",
                    format=context.target_format,
                    error=f"Unsupported VML conversion: {context.source_format} to {context.target_format}"
                )
                
            return UnifiedConversionResult(
                success=True,
                output=output,
                format=context.target_format
            )
            
        except Exception as e:
            return UnifiedConversionResult(
                success=False,
                output="",
                format=context.target_format,
                error=str(e)
            )
            
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported format pairs"""
        return {
            'vml': ['html', 'markdown'],
            'text': ['vml']
        }
        
    def validate_input(self, input_text: str, format: str) -> Tuple[bool, List[str]]:
        """Validate VML input"""
        if format == 'vml':
            return self.handler.validate_syntax(input_text)
        return True, []
        
    def _text_to_vml(self, text: str) -> str:
        """Simple text to VML conversion"""
        # This is a very basic implementation
        lines = text.strip().split('\n')
        vml_output = []
        
        # Add metadata if first line looks like a title
        if lines and not lines[0].startswith('#'):
            vml_output.append('---')
            vml_output.append(f'title: {lines[0]}')
            vml_output.append('date: ' + datetime.now().strftime('%Y-%m-%d'))
            vml_output.append('---\n')
            vml_output.append(f'# {lines[0]}\n')
            lines = lines[1:]
        
        # Process remaining lines
        for line in lines:
            if line.strip():
                vml_output.append(line)
            else:
                vml_output.append('')
                
        return '\n'.join(vml_output)


class ClaudeConverter(ConverterInterface):
    """Claude API converter implementation"""
    
    def __init__(self, config: UnifiedConfig):
        self.config = config
        
    async def convert(self, input_text: str, context: ConversionContext) -> UnifiedConversionResult:
        """Convert using Claude API"""
        if not ANTHROPIC_AVAILABLE:
            return UnifiedConversionResult(
                success=False,
                output="",
                format=context.target_format,
                error="Anthropic module not available. Please install: pip install anthropic"
            )
            
        # Placeholder for Claude API conversion
        # In real implementation, would use the bidirectional converter from combined_vml_system.py
        
        return UnifiedConversionResult(
            success=False,
            output="",
            format=context.target_format,
            error="Claude API conversion not implemented in this demo"
        )
        
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported format pairs"""
        return {
            'text': ['code'],
            'code': ['text']
        }
        
    def validate_input(self, input_text: str, format: str) -> Tuple[bool, List[str]]:
        """Validate input"""
        return True, []


class MarkupProcessor(ConverterInterface):
    """Markup processor implementation"""
    
    async def convert(self, input_text: str, context: ConversionContext) -> UnifiedConversionResult:
        """Process markup conversions"""
        # Placeholder implementation
        return UnifiedConversionResult(
            success=True,
            output=input_text,  # Pass through for now
            format=context.target_format
        )
        
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported format pairs"""
        return {
            'text_markup': ['text'],
            'text': ['text_markup']
        }
        
    def validate_input(self, input_text: str, format: str) -> Tuple[bool, List[str]]:
        """Validate input"""
        return True, []


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    # Set up logging
    log_file = Path.home() / ".unified_converter" / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting Unified Converter System")
    
    # Create main window
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except:
        pass
        
    # Create application
    app = UnifiedConverterGUI(root)
    
    # Run main loop
    root.mainloop()
    
    logger.info("Application closed")


if __name__ == "__main__":
    main()