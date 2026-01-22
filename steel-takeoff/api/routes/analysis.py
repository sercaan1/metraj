"""
Analysis Routes
Endpoints for DXF file analysis and rebar quantity extraction
"""

import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form, Query
from fastapi.responses import FileResponse

from api.config import settings
from api.middleware.auth import get_current_user, get_current_user_optional, UserInfo
from api.schemas import (
    AnalysisResponse,
    AnalysisSummaryResponse,
    FileInfoResponse,
    ErrorResponse,
    AnalysisOptions,
    RebarItemResponse,
    DiameterSummary,
)

# Import our domain services
from services import TakeoffService, CalculationService
from exporters import ExcelExporter
from config import AppSettings


router = APIRouter(prefix="/analysis", tags=["Analysis"])


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    ext = Path(file.filename).suffix.lower()
    if ext not in [e.lower() for e in settings.storage.allowed_extensions]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.storage.allowed_extensions)}"
        )


async def save_upload(file: UploadFile, job_id: str) -> Path:
    """Save uploaded file and return path"""
    ext = Path(file.filename).suffix
    file_path = settings.storage.upload_dir / f"{job_id}{ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Analysis failed"}
    },
    summary="Analyze DXF file",
    description="Upload a DXF file and extract rebar quantities. Returns detailed breakdown by position and diameter."
)
async def analyze_dxf(
    file: UploadFile = File(..., description="DXF file to analyze"),
    analyze_poz_blocks: bool = Form(True, description="Extract from POZ block attributes"),
    analyze_text_annotations: bool = Form(True, description="Extract from text annotations"),
    analyze_geometry: bool = Form(False, description="Analyze geometric entities on rebar layers"),
    merge_duplicates: bool = Form(True, description="Merge items with same position/diameter/length"),
    export_excel: bool = Form(False, description="Generate Excel export"),
    user: Optional[UserInfo] = Depends(get_current_user_optional)
):
    """
    Analyze a DXF file and extract rebar quantities.
    
    This endpoint:
    1. Uploads and validates the DXF file
    2. Extracts rebar information from POZ blocks and/or text annotations
    3. Calculates weights and lengths
    4. Optionally generates an Excel export
    
    Returns detailed breakdown including:
    - Total weight (kg and tons)
    - Total length (meters)
    - Breakdown by diameter
    - All individual items with quantities
    """
    # Validate file
    validate_file(file)
    
    # Generate job ID
    job_id = str(uuid.uuid4())[:8]
    
    try:
        # Save uploaded file
        file_path = await save_upload(file, job_id)
        
        # Configure analysis settings
        app_settings = AppSettings()
        app_settings.analyzer.analyze_poz_blocks = analyze_poz_blocks
        app_settings.analyzer.analyze_text = analyze_text_annotations
        app_settings.analyzer.analyze_geometry = analyze_geometry
        app_settings.analyzer.merge_duplicates = merge_duplicates
        
        # Run analysis
        service = TakeoffService(app_settings)
        schedule = service.process_file(file_path)
        
        # Calculate summaries
        calculator = CalculationService()
        diameter_breakdown = calculator.get_diameter_breakdown(schedule)
        position_breakdown = calculator.get_position_breakdown(schedule)
        
        # Generate Excel if requested
        excel_url = None
        if export_excel:
            excel_exporter = ExcelExporter()
            excel_path = settings.storage.export_dir / f"{job_id}_schedule.xlsx"
            excel_exporter.export(schedule, excel_path)
            excel_url = f"/api/v1/analysis/download/{job_id}/excel"
        
        # Build response
        items = [
            RebarItemResponse(
                position=item['position'],
                diameter=item['diameter'],
                quantity=item['quantity'],
                length_mm=item['length_mm'],
                length_cm=item['length_cm'],
                total_length_m=item['total_length_m'],
                unit_weight=item['unit_weight_kg_m'],
                weight_kg=item['total_weight_kg'],
                shape=item.get('shape', 'STRAIGHT'),
                rebar_type=item.get('rebar_type', 'MAIN'),
                location=item.get('location', ''),
                spacing=item.get('spacing'),
                source=item.get('source', 'unknown')
            )
            for item in position_breakdown
        ]
        
        by_diameter = [
            DiameterSummary(
                diameter=d['diameter'],
                diameter_str=d['diameter_str'],
                total_quantity=d['total_quantity'],
                total_length_m=d['total_length_m'],
                unit_weight_kg_m=d['unit_weight_kg_m'],
                total_weight_kg=d['total_weight_kg']
            )
            for d in diameter_breakdown
        ]
        
        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            job_id=job_id,
            file_name=file.filename,
            analyzed_at=datetime.now(timezone.utc),
            total_weight_kg=round(schedule.total_weight_kg, 2),
            total_weight_ton=round(schedule.total_weight_kg / 1000, 3),
            total_length_m=round(schedule.total_length_m, 2),
            item_count=len(schedule.items),
            position_count=len(schedule.by_position()),
            by_diameter=by_diameter,
            items=items,
            excel_download_url=excel_url
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File processing error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    finally:
        # Cleanup uploaded file (keep exports)
        try:
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)
        except:
            pass


@router.post(
    "/info",
    response_model=FileInfoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
    },
    summary="Get DXF file information",
    description="Get information about a DXF file without full analysis"
)
async def get_file_info(
    file: UploadFile = File(..., description="DXF file to inspect"),
    user: Optional[UserInfo] = Depends(get_current_user_optional)
):
    """
    Get information about a DXF file without running full analysis.
    
    Useful for:
    - Checking if file is valid
    - Seeing entity types and counts
    - Determining which analysis method to use
    """
    validate_file(file)
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        file_path = await save_upload(file, job_id)
        file_size = file_path.stat().st_size
        
        service = TakeoffService()
        info = service.get_file_info(file_path)
        
        # Determine recommended method
        if info['poz_block_count'] > 0:
            if info['text_entity_count'] > info['poz_block_count'] * 2:
                recommended = "full"
            else:
                recommended = "poz_blocks"
        elif info['text_entity_count'] > 0:
            recommended = "text_annotations"
        else:
            recommended = "full"
        
        return FileInfoResponse(
            success=True,
            file_name=file.filename,
            file_size_bytes=file_size,
            total_entities=info['total_entities'],
            entity_counts=info['entity_counts'],
            layers=info['layers'],
            rebar_layers=info['rebar_layers'],
            blocks=info['blocks'],
            poz_block_count=info['poz_block_count'],
            text_entity_count=info['text_entity_count'],
            recommended_method=recommended
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file info: {str(e)}"
        )
    finally:
        try:
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)
        except:
            pass


@router.get(
    "/download/{job_id}/excel",
    response_class=FileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Export not found"}
    },
    summary="Download Excel export",
    description="Download the Excel file generated from analysis"
)
async def download_excel(
    job_id: str,
    user: Optional[UserInfo] = Depends(get_current_user_optional)
):
    """Download Excel export for a completed analysis job"""
    excel_path = settings.storage.export_dir / f"{job_id}_schedule.xlsx"
    
    if not excel_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Excel export not found for job {job_id}"
        )
    
    return FileResponse(
        path=excel_path,
        filename=f"rebar_schedule_{job_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post(
    "/export/excel",
    response_class=FileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
    },
    summary="Analyze and download Excel",
    description="One-step endpoint: analyze DXF and return Excel file directly"
)
async def analyze_and_export_excel(
    file: UploadFile = File(..., description="DXF file to analyze"),
    user: Optional[UserInfo] = Depends(get_current_user_optional)
):
    """
    Analyze DXF file and immediately return Excel export.
    
    This is a convenience endpoint that combines analysis and export in one call.
    """
    validate_file(file)
    
    job_id = str(uuid.uuid4())[:8]
    
    try:
        file_path = await save_upload(file, job_id)
        
        # Run analysis with default settings
        service = TakeoffService()
        schedule = service.process_file(file_path)
        
        # Generate Excel
        excel_exporter = ExcelExporter()
        excel_path = settings.storage.export_dir / f"{job_id}_schedule.xlsx"
        excel_exporter.export(schedule, excel_path)
        
        return FileResponse(
            path=excel_path,
            filename=f"rebar_schedule_{Path(file.filename).stem}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    finally:
        try:
            if 'file_path' in locals():
                file_path.unlink(missing_ok=True)
        except:
            pass
