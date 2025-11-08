from schemas.pymodels import LocationType,AccessRole
from sqlmodel import SQLModel, Field, Column, JSON,Relationship
from datetime import datetime
from typing import Optional, Dict ,List
from uuid import uuid4
import uuid 




class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(foreign_key="users.id")
    cloud: str = Field(..., description="Cloud provider, e.g., aws, gcp, azure")
    product: str = Field(..., description="Product under the cloud, e.g., s3, gcs, bigquery")
    auth: Dict = Field(default_factory=dict, sa_column=Column(JSON), description="Authentication details")
    bucket_info: Dict = Field(default_factory=dict, sa_column=Column(JSON), description="Contains region, bucket_name, and path info")
    location_type: str = Field(..., description="Specifies whether this location is used for source or destination")

    destinations: List["Destination"] = Relationship(back_populates="location")
    sources: List["Source"] = Relationship(back_populates="location")



class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the source")
    description: Optional[str] = Field(default=None, description="Description of this source")
    status: str = Field(default="Active", description="source location status is Active/Inactive")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(foreign_key="users.id")
    location_uuid: str = Field(foreign_key="locations.id", description="UUID of related location")
    organization_id: str = Field(foreign_key="organizations.id")

    location: Optional[Location] = Relationship(back_populates="sources")



class Destination(SQLModel, table=True):
    __tablename__ = "destinations"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the destination")
    description: Optional[str] = Field(default=None, description="Description of this destination")
    status: str = Field(default="Active", description="Destination location status is Active/Inactive")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(foreign_key="users.id")
    location_uuid: str = Field(foreign_key="locations.id", description="UUID of related location")
    organization_id: str = Field(foreign_key="organizations.id")

    location: Optional[Location] = Relationship(back_populates="destinations")





class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the organization")
    description: Optional[str] = Field(default=None, description="Optional description about the organization")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Whether the organization is currently active")



class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    organization_id: str = Field(foreign_key="organizations.id")

    first_name: str = Field(..., description="First name of the user")
    last_name: str = Field(..., description="Last name of the user")
    email: str = Field(..., unique=True, index=True, description="Email address of the user")
    access: AccessRole = Field(default=AccessRole.VIEWER, description="User access role: admin, developer, or viewer")
    is_active: bool = Field(default=False, description="Whether the user is active")
    hashed_password: str = Field(..., description="User password (hashed)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    

