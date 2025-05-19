from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import os
from dotenv import load_dotenv
from typing import List

from . import models, schemas, database

# Load environment variables from .env file
load_dotenv()

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Dependency to get a DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

#  Upload endpoint
@app.post("/upload", response_model=schemas.ImageOut)
def upload_image(
    uploader: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid4()}.{file_ext}"
    file_path = os.path.join("images", unique_filename)

    # Save the image locally
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Save metadata in DB
    image = models.Image(
        filename=unique_filename,
        uploader=uploader,
        location=location,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    # Generate public URL
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    return schemas.ImageOut(
        id=image.id,
        filename=image.filename,
        uploader=image.uploader,
        location=image.location,
        timestamp=image.timestamp,
        url=f"{base_url}/files/{image.filename}"
    )

#  Welcome route
@app.get("/")
def read_root():
    return {"message": "Welcome to RealReview!"}

#  Get all images
@app.get("/images", response_model=List[schemas.ImageOut])
def get_all_images(db: Session = Depends(get_db)):
    images = db.query(models.Image).all()
    base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")

    image_out_list = []
    for image in images:
        image_out = schemas.ImageOut(
            id=image.id,
            filename=image.filename,
            uploader=image.uploader,
            location=image.location,
            timestamp=image.timestamp,
            url=f"{base_url}/files/{image.filename}"
        )
        image_out_list.append(image_out)

    return image_out_list
