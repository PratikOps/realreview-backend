from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from uuid import uuid4
from typing import List
import os
from . import models, schemas, database

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

# 🖼 Upload endpoint
@app.post("/upload", response_model=schemas.ImageOut)
def upload_image(
    uploader: str = Form(...),
    location: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Create a unique filename
    file_ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid4()}.{file_ext}"
    file_path = os.path.join("images", unique_filename)

    # Save the file locally
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

    return image

# 🔍 Get all images
@app.get("/images", response_model=List[schemas.ImageOut])
def get_all_images(db: Session = Depends(get_db)):
    images = db.query(models.Image).all()

    # Add a dynamic 'url' field to each image
    for image in images:
        image.url = f"http://127.0.0.1:8000/files/{image.filename}"

    return images


# 🔍 Get a specific image by ID
@app.get("/image/{image_id}", response_model=schemas.ImageOut)
def get_image(image_id: int = Path(...), db: Session = Depends(get_db)):
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Add 'url' to the returned object
    image.url = f"http://127.0.0.1:8000/files/{image.filename}"
    return image


# 🏠 Welcome route
@app.get("/")
def read_root():
    return {"message": "Welcome to RealReview!"}

from fastapi.responses import FileResponse

# 📂 Serve uploaded image files
@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join("images", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

