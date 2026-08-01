import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db
from app.services.report_service import ReportService
from app.repositories.case_repository import CaseRepository
from app.schemas.response import APIResponse

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportResponse(BaseModel):
    message: str
    report_path: str


@router.post("/{case_id}/generate", response_model=APIResponse[ReportResponse])
def generate_report(
    case_id: int, report_type: str = "full", db: Session = Depends(get_db)
):
    """Generate a PDF investigation report for the specified case."""
    try:
        report_path = ReportService.generate_pdf_report(db, case_id, report_type)
        return APIResponse(
            success=True,
            data=ReportResponse(
                message="Report generated successfully", report_path=report_path
            ),
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/{case_id}/download")
def download_report(case_id: int, db: Session = Depends(get_db)):
    """Download the latest generated PDF report for the case."""
    # Ensure case exists
    case = CaseRepository.get(db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    report_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "data", "reports"
        )
    )
    if not os.path.exists(report_dir):
        raise HTTPException(status_code=404, detail="No reports found")

    # Find the latest report for this case
    case_reports = [
        f
        for f in os.listdir(report_dir)
        if f.startswith(f"report_case_{case_id}_") and f.endswith(".pdf")
    ]

    if not case_reports:
        raise HTTPException(
            status_code=404,
            detail="Report not found for this case. Generate one first.",
        )

    # Sort to get the most recent one (using modification time)
    case_reports.sort(
        key=lambda f: os.path.getmtime(os.path.join(report_dir, f)), reverse=True
    )
    latest_report = case_reports[0]

    report_path = os.path.join(report_dir, latest_report)

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"asterion_investigation_report_case_{case_id}.pdf",
    )
