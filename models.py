from schemas.pymodels import LocationType,AccessRole , ShareStatus ,SourceStatus,DestinationStatus
from sqlmodel import SQLModel, Field, Column, JSON,Relationship
from datetime import datetime
from typing import Optional, Dict ,List 
from uuid import uuid4
import uuid
from sqlalchemy import Enum as SQLAlchemyEnum




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
    location_type: LocationType = Field(..., description="Specifies whether this location is used for source or destination")

    destinations: List["Destination"] = Relationship(back_populates="location")
    sources: List["Source"] = Relationship(back_populates="location")



class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the source") # ..., means required field,If the value is not passed, a validation error will be thrown
    description: Optional[str] = Field(default=None, description="Description of this source")
    status: SourceStatus = Field(default=SourceStatus.CONNECTED,sa_column=Column(SQLAlchemyEnum(SourceStatus, native_enum=False, validate_strings=True)),description="Source connection status (connected/error)")
    error_message: Optional[str] = Field(default=None, description="Error message if connection fails")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(foreign_key="users.id")
    location_uuid: str = Field(foreign_key="locations.id", description="UUID of related location")
    organization_id: str = Field(foreign_key="organizations.id")

    location: Optional[Location] = Relationship(back_populates="sources")



class Destination(SQLModel, table=True):
    __tablename__ = "destinations"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the destination") # required field
    description: Optional[str] = Field(default=None, description="Description of this destination")
    status: DestinationStatus = Field(default=DestinationStatus.CONNECTED,sa_column=Column(SQLAlchemyEnum(DestinationStatus, native_enum=False, validate_strings=True)),description="Destination connection status (connected/error)")
    error_message: Optional[str] = Field(default=None, description="Error message if destination connection fails")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(foreign_key="users.id")
    location_uuid: str = Field(foreign_key="locations.id", description="UUID of related location")
    organization_id: str = Field(foreign_key="organizations.id")

    location: Optional[Location] = Relationship(back_populates="destinations")




class DataShare(SQLModel, table=True):
    __tablename__ = "datashares"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    name: str = Field(..., description="Name of the data share job")
    description: Optional[str] = Field(default=None, description="Optional description of the share")
    source_id: str = Field(..., foreign_key="sources.id", description="Linked source ID")
    destination_id: str = Field(..., foreign_key="destinations.id", description="Linked destination ID")
    schedule: str = Field(default=None, description="Type of schedule, e.g. daily/weekly")
    cronjob_text: Optional[str] = Field(default=None, description="Cronjob expression for scheduled runs")
    data_transferred: Optional[float] = Field(default=0.0, description="Amount of data transferred in MB")
    status: Optional[ShareStatus] = Field(default=ShareStatus.ACTIVE,sa_column=Column(SQLAlchemyEnum(ShareStatus, native_enum=False, validate_strings=True)),description="Current status of the share")
    error_message: Optional[str] = Field(default=None, description="Last error message if status=error")
    is_active: bool = Field(default=True, description="Indicates if the share is active or soft-deleted")


    


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
    invited_by : str =Field(foreign_key = "users.id")
    
    inviter: Optional["User"] = Relationship(back_populates="invited_users", sa_relationship_kwargs={"remote_side": "User.id"})
    invited_users: list["User"] = Relationship(back_populates="inviter")

