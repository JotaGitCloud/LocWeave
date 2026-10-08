from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app import models, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LocWeave",
    description="Pipeline de Localización para Videojuegos Indie",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "message": "LocWeave está corriendo",
        "version": "0.1.0",
        "status": "base lista"
    }

@app.post("/projects", response_model=schemas.ProjectOut)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects", response_model=list[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()