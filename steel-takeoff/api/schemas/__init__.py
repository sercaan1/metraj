"""
API Schemas
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Rebar Schemas
# ============================================================================

class RebarItemResponse(BaseModel):
    """Single rebar item in response"""
    position: Optional[str] = None
    diameter: int = Field(..., description="Diameter in mm")
    quantity: int = Field(..., description="Number of bars")
    length_mm: float = Field(..., description="Length in mm")
    length_cm: float = Field(..., description="Length in cm")
    total_length_m: float = Field(..., description="Total length in meters")
    unit_weight: float = Field(..., description="Unit weight in kg/m")
    weight_kg: float = Field(..., description="Total weight in kg")
    shape: str = "STRAIGHT"
    rebar_type: str = "MAIN"
    location: Optional[str] = None
    spacing: Optional[int] = None
    source: str = "unknown"

    class Config:
        json_schema_extra = {
            "example": {
                "position": "1",
                "diameter": 12,
                "quantity": 10,
                "length_mm": 800,
                "length_cm": 80,
                "total_length_m": 8.0,
                "unit_weight": 0.888,
                "weight_kg": 7.1,
                "shape": "STRAIGHT",
                "rebar_type": "MAIN",
                "location": "Kiriş",
                "spacing": None,
                "source": "poz_block"
            }
        }


class DiameterSummary(BaseModel):
    """Summary for a specific diameter"""
    diameter: int
    diameter_str: str = Field(..., description="Display string like 'ø12'")
    total_quantity: int
    total_length_m: float
    unit_weight_kg_m: float
    total_weight_kg: float


class AnalysisResponse(BaseModel):
    """Response for DXF analysis"""
    success: bool = True
    message: str = "Analysis completed successfully"
    
    # Job info
    job_id: str
    file_name: str
    analyzed_at: datetime
    
    # Summary
    total_weight_kg: float
    total_weight_ton: float
    total_length_m: float
    item_count: int
    position_count: int
    
    # Detailed breakdown
    by_diameter: List[DiameterSummary]
    items: List[RebarItemResponse]
    
    # Export URLs
    excel_download_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "job_id": "abc123",
                "file_name": "drawing.dxf",
                "analyzed_at": "2025-01-22T12:00:00Z",
                "total_weight_kg": 1250.50,
                "total_weight_ton": 1.25,
                "total_length_m": 850.25,
                "item_count": 45,
                "position_count": 15,
                "by_diameter": [],
                "items": []
            }
        }


class AnalysisSummaryResponse(BaseModel):
    """Lightweight response with just summary (no item details)"""
    success: bool = True
    job_id: str
    file_name: str
    analyzed_at: datetime
    total_weight_kg: float
    total_weight_ton: float
    total_length_m: float
    item_count: int
    by_diameter: List[DiameterSummary]


# ============================================================================
# File Info Schemas
# ============================================================================

class FileInfoResponse(BaseModel):
    """Response for file information endpoint"""
    success: bool = True
    file_name: str
    file_size_bytes: int
    total_entities: int
    entity_counts: Dict[str, int]
    layers: List[str]
    rebar_layers: List[str]
    blocks: List[str]
    poz_block_count: int
    text_entity_count: int
    
    # Recommendation
    recommended_method: str = Field(
        ..., 
        description="Recommended analysis method: 'poz_blocks', 'text_annotations', or 'full'"
    )


# ============================================================================
# Job Schemas
# ============================================================================

class JobStatus(BaseModel):
    """Status of an analysis job"""
    job_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    excel_url: Optional[str] = None


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "File not found",
                "detail": "The specified file does not exist",
                "error_code": "FILE_NOT_FOUND"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    success: bool = False
    error: str = "Validation Error"
    detail: List[Dict[str, Any]]


# ============================================================================
# Request Schemas
# ============================================================================

class AnalysisOptions(BaseModel):
    """Options for analysis request"""
    analyze_poz_blocks: bool = True
    analyze_text_annotations: bool = True
    analyze_geometry: bool = False
    merge_duplicates: bool = True
    export_excel: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "analyze_poz_blocks": True,
                "analyze_text_annotations": True,
                "analyze_geometry": False,
                "merge_duplicates": True,
                "export_excel": True
            }
        }


# ============================================================================
# Health Check
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    timestamp: datetime
