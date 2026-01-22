"""
Steel Quantity Takeoff API
FastAPI application for extracting rebar quantities from DXF drawings
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.config import settings
from api.routes import analysis_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    print(f"🚀 Starting {settings.title} v{settings.version}")
    print(f"📁 Upload directory: {settings.storage.upload_dir.absolute()}")
    print(f"📊 Export directory: {settings.storage.export_dir.absolute()}")
    print(f"🔐 JWT Algorithm: {settings.jwt.algorithm}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allowed_methods,
    allow_headers=settings.cors.allowed_headers,
)


# Include routers
app.include_router(health_router)
app.include_router(analysis_router, prefix=settings.api_prefix)


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.title,
        version=settings.version,
        description=f"""
{settings.description}

## Authentication

This API uses JWT (JSON Web Token) authentication compatible with .NET Core.
Works just like [Authorize] attribute in .NET - send your CRM token in the Authorization header.

### How to Use

1. Get a JWT token from your .NET CRM application (login)
2. Include the token in requests: `Authorization: Bearer <your-token>`
3. Use the SAME secret key in both .NET CRM and this API's .env file

### .NET Configuration (appsettings.json)
```json
{{
  "Jwt": {{
    "Key": "your-secret-key-here-minimum-32-characters",
    "Issuer": "your-crm"
  }}
}}
```

### Python API Configuration (.env)
```
JWT_SECRET_KEY=your-secret-key-here-minimum-32-characters
JWT_ALGORITHM=HS256
```

## Endpoints

### Analysis
- `POST /api/v1/analysis/analyze` - Analyze DXF file and get rebar quantities
- `POST /api/v1/analysis/info` - Get file info without full analysis
- `POST /api/v1/analysis/export/excel` - Analyze and download Excel directly
- `GET /api/v1/analysis/download/{{job_id}}/excel` - Download Excel export

## Example (C#)

```csharp
var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", userToken);

var content = new MultipartFormDataContent();
content.Add(new StreamContent(fileStream), "file", "drawing.dxf");

var response = await client.PostAsync(
    "http://localhost:8000/api/v1/analysis/analyze", 
    content
);
```
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token from your .NET CRM"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
