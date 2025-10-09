from db import engine, get_db
from models import Base, CVFile
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import os
import psycopg2


app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.on_event("startup")
def preload_resume():
    db: Session = next(get_db())
    if not db.query(CVFile).first():
        print("Preloading resume into database...")
        pdf_path = "data/English_CV_2025.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            resume = CVFile(filename="English_CV_2025.pdf", filedata=pdf_bytes)
            db.add(resume)
            db.commit()
    else:
        print("Resume already exists in database, skipping preload.")
    db.close()

@app.get("/api/cv")
def get_cv(db: Session = Depends(get_db)):
    resume = db.query(CVFile).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Curriculum Vitae not found")
    temp_path = f"/tmp/{resume.filename}"
    with open(temp_path, "wb") as f:
        f.write(resume.filedata)
    return FileResponse(temp_path, filename=resume.filename)

# DB health check endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Healthcheck endpoint : check database connection."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
