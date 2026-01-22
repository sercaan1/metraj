"""
API Configuration
Settings for FastAPI application and JWT authentication
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class JWTSettings:
    """JWT Authentication settings - compatible with .NET JWT"""
    # Secret key - MUST match your .NET CRM's JWT secret
    secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-min-32-characters-long!")
    
    # Algorithm - HS256 is most common and compatible with .NET
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Token expiration in minutes
    access_token_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    # Issuer - should match your .NET CRM's issuer
    issuer: str = os.getenv("JWT_ISSUER", "your-crm-app")
    
    # Audience - should match your .NET CRM's audience
    audience: str = os.getenv("JWT_AUDIENCE", "steel-takeoff-api")
    
    # If True, validates issuer and audience from token
    validate_issuer: bool = os.getenv("JWT_VALIDATE_ISSUER", "false").lower() == "true"
    validate_audience: bool = os.getenv("JWT_VALIDATE_AUDIENCE", "false").lower() == "true"


@dataclass
class CORSSettings:
    """CORS settings for cross-origin requests from CRM"""
    # Origins allowed to make requests (your CRM URLs)
    allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173",
        "https://your-crm-domain.com",
        "*"  # Remove in production!
    ])
    
    allow_credentials: bool = True
    allowed_methods: List[str] = field(default_factory=lambda: ["*"])
    allowed_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class StorageSettings:
    """File storage settings"""
    # Directory to store uploaded files
    upload_dir: Path = field(default_factory=lambda: Path("uploads"))
    
    # Directory for generated exports
    export_dir: Path = field(default_factory=lambda: Path("exports"))
    
    # Maximum file size in MB
    max_file_size_mb: int = 50
    
    # Allowed file extensions
    allowed_extensions: List[str] = field(default_factory=lambda: [".dxf", ".DXF"])
    
    def __post_init__(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class APISettings:
    """Main API settings"""
    # API Info
    title: str = "Steel Quantity Takeoff API"
    description: str = "REST API for extracting rebar quantities from DXF construction drawings"
    version: str = "1.0.0"
    
    # Server
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("API_DEBUG", "true").lower() == "true"
    
    # Sub-settings
    jwt: JWTSettings = field(default_factory=JWTSettings)
    cors: CORSSettings = field(default_factory=CORSSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    
    # API prefix
    api_prefix: str = "/api/v1"
    
    @classmethod
    def from_env(cls) -> 'APISettings':
        """Create settings from environment variables"""
        return cls()


# Global settings instance
settings = APISettings.from_env()
