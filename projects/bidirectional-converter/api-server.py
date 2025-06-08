#!/usr/bin/env python3
"""
API Server for Bidirectional Code Converter
------------------------------------------
FastAPI-based server providing REST endpoints for code conversion services.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from pathlib import Path
import secrets
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import the converter module
from bidirectional_converter import (
    BidirectionalConverter, ConversionConfig, DetailLevel,
    ConversionDirection, ConversionResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ConversionRequest(BaseModel):
    mode: str = Field(..., description="Conversion mode: 'text-to-code' or 'code-to-text'")
    input: str = Field(..., description="Input text or code to convert")
    language: str = Field(..., description="Programming language")
    detail_level: Optional[str] = Field("standard", description="Detail level for code-to-text")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    options: Optional[Dict[str, Any]] = Field(None, description="Conversion options")


class ConversionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    tokens: Optional[int] = None
    processing_time: Optional[float] = None
    cached: Optional[bool] = None
    model: Optional[str] = None
    suggestions: Optional[List[str]] = None


class APIStatus(BaseModel):
    connected: bool
    version: str
    model: str
    uptime: float


class APIKeyRequest(BaseModel):
    api_key: str = Field(..., description="Anthropic API key")


class UserSession(BaseModel):
    session_id: str
    created_at: datetime
    last_active: datetime
    conversion_count: int = 0
    total_tokens: int = 0


# Session management
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
        self.cleanup_interval = 3600  # 1 hour
        
    async def create_session(self) -> str:
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = UserSession(
            session_id=session_id,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        session = self.sessions.get(session_id)
        if session:
            session.last_active = datetime.now()
        return session
    
    async def update_session(self, session_id: str, tokens: int):
        session = await self.get_session(session_id)
        if session:
            session.conversion_count += 1
            session.total_tokens += tokens
    
    async def cleanup_sessions(self):
        """Remove inactive sessions older than 24 hours"""
        cutoff = datetime.now() - timedelta(hours=24)
        expired = [
            sid for sid, session in self.sessions.items()
            if session.last_active < cutoff
        ]
        for sid in expired:
            del self.sessions[sid]
        logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global instances
session_manager = SessionManager()
converter_instance: Optional[BidirectionalConverter] = None
app_start_time = datetime.now()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting API server...")
    
    # Initialize converter if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        global converter_instance
        try:
            config = ConversionConfig()
            converter_instance = BidirectionalConverter(api_key, config)
            logger.info("Converter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize converter: {e}")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def periodic_cleanup():
    """Periodically clean up expired sessions"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await session_manager.cleanup_sessions()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="Bidirectional Code Converter API",
    description="AI-powered conversion between natural language and code",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security
security = HTTPBearer()


async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserSession:
    """Validate session token and return session"""
    session = await session_manager.get_session(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    return session


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface"""
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>API Server Running</h1>")


@app.get("/api/status", response_model=APIStatus)
async def get_api_status():
    """Get API server status"""
    uptime = (datetime.now() - app_start_time).total_seconds()
    
    return APIStatus(
        connected=converter_instance is not None,
        version="1.0.0",
        model=converter_instance.config.model if converter_instance else "Not configured",
        uptime=uptime
    )


@app.post("/api/session")
async def create_session():
    """Create a new session"""
    session_id = await session_manager.create_session()
    return {"session_id": session_id}


@app.post("/api/convert", response_model=ConversionResponse)
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
async def convert(
    request: Request,
    conversion_request: ConversionRequest,
    session: UserSession = Depends(get_current_session)
):
    """Perform text-to-code or code-to-text conversion"""
    
    if not converter_instance:
        raise HTTPException(
            status_code=503,
            detail="Converter not initialized. Please configure API key."
        )
    
    try:
        # Validate mode
        if conversion_request.mode not in ["text-to-code", "code-to-text"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Must be 'text-to-code' or 'code-to-text'"
            )
        
        # Apply any custom options
        if conversion_request.options:
            # Temporarily override config options
            original_config = converter_instance.config
            temp_config = ConversionConfig(
                **{**original_config.__dict__, **conversion_request.options}
            )
            converter_instance.config = temp_config
        
        # Perform conversion
        if conversion_request.mode == "text-to-code":
            result = await converter_instance.convert_text_to_code(
                text=conversion_request.input,
                target_language=conversion_request.language,
                context=conversion_request.context
            )
        else:
            # Override detail level if specified
            if conversion_request.detail_level:
                converter_instance.config.detail_level = DetailLevel(
                    conversion_request.detail_level
                )
            
            result = await converter_instance.convert_code_to_text(
                code=conversion_request.input,
                source_language=conversion_request.language
            )
        
        # Restore original config if it was modified
        if conversion_request.options:
            converter_instance.config = original_config
        
        # Update session statistics
        await session_manager.update_session(session.session_id, result.tokens_used)
        
        # Prepare response
        return ConversionResponse(
            success=result.success,
            output=result.output,
            error=result.error,
            tokens=result.tokens_used,
            processing_time=result.processing_time,
            cached=result.cached,
            model=result.metadata.get("model"),
            suggestions=result.suggestions
        )
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return ConversionResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/session/{session_id}")
async def get_session_info(
    session_id: str,
    session: UserSession = Depends(get_current_session)
):
    """Get session information"""
    if session.session_id != session_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "conversion_count": session.conversion_count,
        "total_tokens": session.total_tokens
    }


@app.post("/api/configure")
async def configure_api(api_key_request: APIKeyRequest):
    """Configure the API key (admin endpoint)"""
    # In production, this should be properly secured
    global converter_instance
    
    try:
        config = ConversionConfig()
        converter_instance = BidirectionalConverter(api_key_request.api_key, config)
        
        # Optionally save the key
        key_file = Path.home() / ".bidirectional_converter" / "api_key.txt"
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(api_key_request.api_key)
        
        return {"success": True, "message": "API key configured successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {"code": "python", "name": "Python"},
            {"code": "javascript", "name": "JavaScript"},
            {"code": "java", "name": "Java"},
            {"code": "cpp", "name": "C++"},
            {"code": "csharp", "name": "C#"},
            {"code": "go", "name": "Go"},
            {"code": "rust", "name": "Rust"},
            {"code": "sql", "name": "SQL"},
            {"code": "html", "name": "HTML/CSS"},
            {"code": "typescript", "name": "TypeScript"},
            {"code": "swift", "name": "Swift"},
            {"code": "kotlin", "name": "Kotlin"},
            {"code": "ruby", "name": "Ruby"},
            {"code": "php", "name": "PHP"},
            {"code": "r", "name": "R"},
            {"code": "matlab", "name": "MATLAB"},
            {"code": "scala", "name": "Scala"},
            {"code": "perl", "name": "Perl"},
            {"code": "bash", "name": "Bash/Shell"},
            {"code": "powershell", "name": "PowerShell"},
            {"code": "vml", "name": "VML (Versatile Markup Language)"}
        ]
    }


@app.get("/api/examples/{mode}")
async def get_examples(mode: str):
    """Get example conversions for the specified mode"""
    examples = {
        "text-to-code": [
            {
                "title": "Data Validation Function",
                "language": "python",
                "input": "Create a function that validates a US phone number. It should accept formats like (123) 456-7890, 123-456-7890, and 1234567890.",
                "tags": ["validation", "regex", "string-processing"]
            },
            {
                "title": "REST API Endpoint",
                "language": "javascript",
                "input": "Create an Express.js endpoint that handles user registration. It should validate input, hash the password, and store the user in a database.",
                "tags": ["api", "authentication", "backend"]
            },
            {
                "title": "Sorting Algorithm",
                "language": "java",
                "input": "Implement the quicksort algorithm with generics support and proper error handling.",
                "tags": ["algorithm", "sorting", "generics"]
            }
        ],
        "code-to-text": [
            {
                "title": "Algorithm Analysis",
                "language": "python",
                "input": """def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    merged = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged""",
                "tags": ["algorithm", "sorting", "recursion"]
            },
            {
                "title": "Design Pattern",
                "language": "javascript",
                "input": """class EventEmitter {
    constructor() {
        this.events = {};
    }
    
    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
        return this;
    }
    
    emit(event, ...args) {
        if (!this.events[event]) return false;
        
        this.events[event].forEach(listener => {
            listener.apply(this, args);
        });
        return true;
    }
    
    off(event, listenerToRemove) {
        if (!this.events[event]) return this;
        
        this.events[event] = this.events[event].filter(
            listener => listener !== listenerToRemove
        );
        return this;
    }
}""",
                "tags": ["design-pattern", "events", "class"]
            }
        ]
    }
    
    if mode not in examples:
        raise HTTPException(status_code=404, detail="Invalid mode")
    
    return {"examples": examples[mode]}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "converter_status": "ready" if converter_instance else "not_initialized"
    }


@app.post("/api/feedback")
async def submit_feedback(
    feedback: Dict[str, Any],
    session: UserSession = Depends(get_current_session)
):
    """Submit feedback about a conversion"""
    # In a real implementation, this would store feedback for analysis
    logger.info(f"Feedback from session {session.session_id}: {feedback}")
    return {"success": True, "message": "Feedback received"}


# Static file serving (if needed)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }


# CLI for running the server
def main():
    """Run the API server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bidirectional Converter API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # Ensure API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        key_file = Path.home() / ".bidirectional_converter" / "api_key.txt"
        if key_file.exists():
            os.environ["ANTHROPIC_API_KEY"] = key_file.read_text().strip()
        else:
            logger.warning("No API key found. Configure via /api/configure endpoint.")
    
    # Run server
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    main()
