from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select
from datetime import datetime
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from models import Source,Location,User
from database import get_session
from validations import validate_location_data
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from schemas.pymodels import *
from auth_utils import get_current_user



router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("/", response_model=SourceResponse)
def create_source(payload: SourceCreate,current_user: User = Depends(get_current_user),session: Session = Depends(get_session)):
    
    validate_location_data(payload.location.dict())

    location = Location(**payload.location.model_dump())
    location.created_by = current_user.id  
    session.add(location)
    session.commit()
    session.refresh(location)

    source = Source(
        name=payload.name,
        description=payload.description,
        status=payload.status,
        location_uuid=location.id,  
        organization_id=current_user.organization_id,  
        created_by=current_user.id
    )

    session.add(source)
    session.commit()
    session.refresh(source)

    return SourceResponse.model_validate(source, from_attributes=True)



@router.get("/", response_model=List[SourceResponse])
def get_all_sources(session: Session = Depends(get_session)):

    sources = session.exec(select(Source)).all()

    if not sources:
      raise HTTPException(status_code=404, detail="No destinations found")

    return sources



@router.get("/{source_id}", response_model=SourceResponse)
def get_source_by_id(source_id: str, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.put("/{source_id}", response_model=SourceUpdateResponse)
def update_source(source_id: str, payload: SourceCreate, session: Session = Depends(get_session)):

    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in payload.dict(exclude_unset=True, exclude={"location"}).items():
        setattr(source, key, value)

    if payload.location:
        validate_location_data(payload.location.dict(), partial=True)
        location = session.get(Location, source.location_uuid)
        if not location:
            raise HTTPException(status_code=404, detail="Linked location not found")

        for key, value in payload.location.dict(exclude_unset=True).items():
            setattr(location, key, value)
        session.add(location)

    source.updated_at = datetime.utcnow()
    session.add(source)
    session.commit()
    session.refresh(source)
    
    return SourceUpdateResponse(
    message="Source updated successfully",
    source=SourceResponse.model_validate(source, from_attributes=True)
)


@router.patch("/{source_id}", response_model=SourceUpdateResponse)
def patch_source(source_id: str,payload: SourceUpdate,session: Session = Depends(get_session)):

    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    for key, value in payload.model_dump(exclude_unset=True, exclude={"location"}).items():
        setattr(source, key, value)

    if payload.location:
        location = session.get(Location, source.location_uuid)
        if not location:
            raise HTTPException(status_code=404, detail="Linked location not found")

        
        validate_location_data(
        payload.location.model_dump(exclude_unset=True),
        partial=True
    )

        updates = payload.location.model_dump(exclude_unset=True)

        for field, value in updates.items():
            current = getattr(location, field)

            if isinstance(current, dict) and isinstance(value, dict):
                merged = {**current, **value}  
                setattr(location, field, merged)
            else:
                setattr(location, field, value)


        session.add(location)

    source.updated_at = datetime.utcnow()
    session.add(source)
    session.commit()
    session.refresh(source)

    return SourceUpdateResponse(
    message="Source updated successfully",
    source=SourceResponse.model_validate(source, from_attributes=True)
)




@router.delete("/{source_id}")
def delete_source(source_id: str, session: Session = Depends(get_session)):
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    session.delete(source)
    session.commit()
    return {"message": "Source deleted successfully"}
