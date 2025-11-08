from fastapi import APIRouter, Depends, HTTPException , status
from typing import List 
from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from models import Destination,Location,User
from database import get_session
from validations import validate_location_data
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from schemas.pymodels import *
from auth_utils import get_current_user




router = APIRouter(prefix="/destinations", tags=["Destinations"])






@router.post("/", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_destination(payload: DestinationCreate,session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    """
    Create a Destination along with its associated Location.
    Validates both literal + nested Location fields.
    """

   
    validate_location_data(payload.location.model_dump())

    
    location = Location(
        cloud=payload.location.cloud.lower(),
        product=payload.location.product.lower(),
        auth=payload.location.auth,
        bucket_info=payload.location.bucket_info,
        location_type=payload.location.location_type.lower(),
        created_by=current_user.id,  
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    session.add(location)
    session.commit()
    session.refresh(location)

    
    destination = Destination(
        name=payload.name.strip(),
        description=payload.description,
        status=payload.status,
        created_by=current_user.id,
        location_uuid=location.id,
        organization_id=current_user.organization_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(destination)
    session.commit()
    session.refresh(destination)

    
    return DestinationResponse(
        id=destination.id,
        name=destination.name,
        description=destination.description,
        status=destination.status,
        created_at=destination.created_at,
        updated_at=destination.updated_at,
        organization_id=destination.organization_id,
        location_uuid=location.id,
        location=location,
    )



@router.get("", response_model=List[DestinationResponse])
def get_all_destinations(session: Session = Depends(get_session)):
    """
    Fetch all destinations with nested location details.
    """
    destinations = session.exec(select(Destination).options(selectinload(Destination.location))).all()

    if not destinations:
        raise HTTPException(status_code=404, detail="No destinations found")

    return destinations





@router.get("/{destination_id}", response_model=DestinationResponse)
def get_single_destination(destination_id: str, session: Session = Depends(get_session)):
    stmt = (
        select(Destination)
        .where(Destination.id == destination_id)
        .options(selectinload(Destination.location))  
    )
    dest = session.exec(stmt).first()

    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")

    return dest



@router.put("/{destination_id}", response_model=DestinationUpdateResponse)
def update_destination(destination_id: str, payload: DestinationCreate, session: Session = Depends(get_session)):
    # 1. Fetch destination
    destination = session.get(Destination, destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    # 2. Validate location payload
    validated_data = validate_location_data(payload.location.model_dump(), partial=False)

    # 3. Update destination fields
    destination.name = payload.name
    destination.description = payload.description
    destination.status = payload.status
    destination.updated_at = datetime.utcnow()

    # 4. Fetch the location linked to this destination
    location = session.get(Location, destination.location_uuid)
    if not location:
        raise HTTPException(status_code=404, detail=f"Linked location not found for UUID: {destination.location_uuid}")

    # 5. Update location fields
    for key, value in validated_data.model_dump().items():
        if hasattr(location, key):
            current_val = getattr(location, key)
            if isinstance(current_val, dict) and isinstance(value, dict):
                current_val.update(value)
                setattr(location, key, current_val)
                flag_modified(location, key)
            else:
                setattr(location, key, value)
                if key in ["auth", "bucket_info"]:
                    flag_modified(location, key)

    location.updated_at = datetime.utcnow()
    
    destination.location_uuid = location.id

    session.add(destination)
    session.add(location)
    session.commit()
    session.refresh(destination)
    session.refresh(location)

    destination.location = location
    response_data = DestinationResponse.model_validate(destination, from_attributes=True)

    return {
        "message": "Destination updated successfully",
        "destination": response_data
    }




   
@router.patch("/{destination_id}", response_model=DestinationUpdateResponse)
def patch_destination(destination_id: str,payload: DestinationUpdate,session: Session = Depends(get_session)):
    
    destination = session.get(Destination, destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    update_fields = payload.model_dump(exclude_unset=True)

    if "name" in update_fields:
        destination.name = payload.name.strip()
    if "description" in update_fields:
        destination.description = payload.description
    if "status" in update_fields:
        destination.status = payload.status

    destination.updated_at = datetime.utcnow()

    # --- Patch Location ---
    if payload.location:
        location_data = (
            payload.location.model_dump(exclude_unset=True)
            if not isinstance(payload.location, dict)
            else payload.location
        )

        validate_location_data(location_data, partial=True)

        location = session.get(Location, destination.location_uuid)
        if not location:
            raise HTTPException(404, f"Linked location not found for UUID {destination.location_uuid}")

        for key, value in location_data.items():
            if hasattr(location, key):
                current_val = getattr(location, key)
                if isinstance(current_val, dict) and isinstance(value, dict):
                    current_val.update(value)
                    setattr(location, key, current_val)
                    flag_modified(location, key)
                else:
                    setattr(location, key, value)
                    if key in ["auth", "bucket_info"]:
                        flag_modified(location, key)

        location.updated_at = datetime.utcnow()
        session.add(location)

    session.add(destination)
    session.commit()

    stmt = (
        select(Destination)
        .where(Destination.id == destination_id)
        .options(selectinload(Destination.location))
    )
    destination = session.exec(stmt).first()

    return {
        "message": "Destination updated successfully",
        "destination": DestinationResponse.model_validate(destination, from_attributes=True),
    }



@router.delete("/{destination_id}")
def delete_destination(destination_id: str, session: Session = Depends(get_session)):
    """
    Delete a destination and its associated location.
    """
    destination = session.get(Destination, destination_id)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")

    location = session.get(Location, destination.location_uuid)

    session.delete(destination)
    if location:
        session.delete(location)
    session.commit()

    return {"message": "Destination deleted successfully"}
