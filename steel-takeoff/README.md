# Steel Quantity Takeoff API

A FastAPI-based REST API for extracting rebar quantities from DXF construction drawings. Designed to integrate with .NET CRM applications using shared JWT authentication.

## Features

- **REST API**: FastAPI with automatic Swagger/OpenAPI documentation
- **JWT Authentication**: Compatible with .NET Core JWT tokens
- **File Upload**: Upload DXF files for analysis
- **Excel Export**: Generate professional Excel reports
- **CORS Support**: Cross-origin requests from your CRM frontend

## Quick Start

### 1. Install Dependencies

```bash
cd steel-takeoff
pip install -r requirements.txt
```

### 2. Configure JWT (Match with your .NET CRM)

Edit `.env` file:
```env
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long!
JWT_ALGORITHM=HS256
```

### 3. Run the API

```bash
# Using the batch file (Windows)
run_api.bat

# Or using Python directly
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Or run app.py directly
python app.py
```

### 4. Access the API

- **API Root**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token` | Generate test JWT token |
| GET | `/api/v1/auth/validate` | Validate current token |
| GET | `/api/v1/auth/me` | Get current user info |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analysis/analyze` | Analyze DXF file |
| POST | `/api/v1/analysis/info` | Get file information |
| POST | `/api/v1/analysis/export/excel` | Analyze and download Excel |
| GET | `/api/v1/analysis/download/{job_id}/excel` | Download Excel export |

## Usage Examples

### Postman

#### 1. Generate a Test Token

```
POST http://localhost:8000/api/v1/auth/token
Content-Type: application/json

{
    "user_id": "user123",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user", "analyzer"],
    "expires_in_minutes": 60
}
```

Response:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

#### 2. Analyze a DXF File

```
POST http://localhost:8000/api/v1/analysis/analyze
Authorization: Bearer <your_token>
Content-Type: multipart/form-data

file: <your_drawing.dxf>
analyze_poz_blocks: true
analyze_text_annotations: true
export_excel: true
```

Response:
```json
{
    "success": true,
    "job_id": "abc12345",
    "file_name": "drawing.dxf",
    "total_weight_kg": 1250.50,
    "total_weight_ton": 1.25,
    "total_length_m": 850.25,
    "item_count": 45,
    "by_diameter": [...],
    "items": [...],
    "excel_download_url": "/api/v1/analysis/download/abc12345/excel"
}
```

### cURL

```bash
# Generate token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "name": "Test User"}'

# Analyze file
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Authorization: Bearer <token>" \
  -F "file=@drawing.dxf" \
  -F "export_excel=true"
```

### C# / .NET Integration

```csharp
using System.Net.Http.Headers;

// Your CRM already has a JWT token for the user
var token = GetUserJwtToken(); // From your authentication

var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = 
    new AuthenticationHeaderValue("Bearer", token);

// Analyze a file
using var content = new MultipartFormDataContent();
content.Add(new StreamContent(fileStream), "file", "drawing.dxf");
content.Add(new StringContent("true"), "export_excel");

var response = await client.PostAsync(
    "http://localhost:8000/api/v1/analysis/analyze", 
    content
);

var result = await response.Content.ReadFromJsonAsync<AnalysisResponse>();
Console.WriteLine($"Total Weight: {result.TotalWeightKg} kg");
```

## JWT Configuration for .NET CRM

To share JWT tokens between your .NET CRM and this API, configure both to use the same secret key:

### .NET appsettings.json

```json
{
  "Jwt": {
    "Key": "your-super-secret-key-min-32-characters-long!",
    "Issuer": "your-crm-app",
    "Audience": "steel-takeoff-api",
    "ExpireMinutes": 60
  }
}
```

### .NET Program.cs

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),
            ValidateIssuer = false,
            ValidateAudience = false,
            ClockSkew = TimeSpan.Zero
        };
    });
```

### Python .env

```env
JWT_SECRET_KEY=your-super-secret-key-min-32-characters-long!
JWT_ALGORITHM=HS256
JWT_ISSUER=your-crm-app
JWT_AUDIENCE=steel-takeoff-api
```

## Project Structure

```
steel-takeoff/
├── api/                    # API Layer
│   ├── __init__.py
│   ├── config.py           # API & JWT settings
│   ├── middleware/         # Authentication middleware
│   │   ├── __init__.py
│   │   └── auth.py         # JWT authentication
│   ├── routes/             # API endpoints (controllers)
│   │   ├── __init__.py
│   │   ├── analysis.py     # DXF analysis endpoints
│   │   ├── auth.py         # Authentication endpoints
│   │   └── health.py       # Health check endpoints
│   └── schemas/            # Pydantic models
│       └── __init__.py     # Request/Response models
│
├── domain/                 # Core business models
├── config/                 # Application configuration
├── parsers/                # DXF file parsers
├── analyzers/              # Analysis logic
├── services/               # Business services
├── exporters/              # Export functionality
├── cli/                    # Command-line interface
├── utils/                  # Utilities
├── tests/                  # Unit tests
│
├── app.py                  # FastAPI application entry
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── run_api.bat            # Windows API runner
└── .env                    # Environment configuration
```

## CLI Usage (Still Available)

The CLI is still available for direct usage:

```bash
# Analyze a DXF file
python main.py analyze drawing.dxf

# Analyze with Excel export
python main.py analyze drawing.dxf --excel

# Get file info
python main.py info drawing.dxf

# Batch process directory
python main.py batch ./drawings --excel
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Server host | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `API_DEBUG` | Debug mode | `true` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiration | `60` |
| `JWT_ISSUER` | Token issuer | `your-crm-app` |
| `JWT_AUDIENCE` | Token audience | `steel-takeoff-api` |

## License

MIT License
