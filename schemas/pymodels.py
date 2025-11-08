from uuid import UUID,uuid4
from datetime import datetime
from enum import Enum
from typing import Optional,Dict,List,Union,Literal 
from pydantic import BaseModel, EmailStr, field_validator,Field






class LocationType(str, Enum):
    SOURCE = "source"
    DESTINATION = "destination"


class AccessRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer" 

#-----------------------

class AuthBase(BaseModel):
    type: Optional[str] = None
    accessKey: Optional[str] = None
    secretAccessKey: Optional[str] = None
    arn: Optional[str] = None
    consumerArn: Optional[str] = None
    serviceAccountToImpersonate: Optional[str] = None
    accessIdentifiers: Optional[Union[List[Dict], Dict]] = None
    accounts: Optional[List[Dict]] = None


class BucketInfoUpdate(BaseModel):
    region: Optional[str] = None
    bucket_name: Optional[str] = None
    path: Optional[str] = None
    is_external: Optional[bool] = None



#---------------



class LocationBase(BaseModel):
    cloud: str
    product: str
    auth: Dict
    bucket_info: Dict
    location_type: str

    class Config:
        from_attributes = True  


class LocationCreate(LocationBase):
    pass


class LocationResponse(BaseModel):
    cloud: str
    product: str
    auth: Dict
    bucket_info: Dict
    location_type: str
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class LocationUpdate(BaseModel):
    cloud: Optional[str] = None
    product: Optional[str] = None
    auth: Optional[AuthBase] = None
    bucket_info: Optional[BucketInfoUpdate] = None
    location_type: Optional[str] = None

    class Config:
        from_attributes = True

# ---------------------- Destination Models ----------------------
class DestinationBase(BaseModel):
    name: str = Field(..., description="Name of the destination")
    description: Optional[str] = Field(None, description="Description of this destination")
    status: Literal["Active", "Inactive"] = Field("Active", description="Destination status")

    @field_validator("name")
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Destination name cannot be empty.")
        return value

    @field_validator("status")
    def validate_status(cls, value):
        allowed = ["Active", "Inactive"]
        if value not in allowed:
            raise ValueError(f"Invalid status '{value}'. Allowed values: {allowed}")
        return value


class DestinationCreate(DestinationBase):
    location: "LocationCreate" = Field(..., description="Associated location for this destination")

    @field_validator("location")
    def validate_location_type(cls, value):
        if value.location_type.lower() != "destination":
            raise ValueError("Location type must be 'destination' for Destination creation.")
        return value


class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["Active", "Inactive"]] = None
    location: Optional["LocationUpdate"] = None  #  Use partial model

    @field_validator("name")
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Destination name cannot be empty.")
        return value

    @field_validator("location")
    def validate_location_type(cls, value):
        """
        Validate location_type *only if provided*.
        Allow partial updates like bucket_info.region without it.
        """
        if value is None:
            return value

        # Handle both dicts and Pydantic models
        if isinstance(value, dict):
            location_type = value.get("location_type")
        else:
            location_type = getattr(value, "location_type", None)

        #  Only validate if provided
        if location_type is not None:
            if location_type.lower() != "destination":
                raise ValueError("Location type must be 'destination' for Destination update.")

        return value




class DestinationResponse(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: str
    status: str
    id: str
    created_at: datetime
    updated_at: datetime
    location_uuid: Optional[str]
    location: Optional[LocationResponse] = None 

    class Config:
        from_attributes = True


class DestinationUpdateResponse(BaseModel):
    message: str
    destination: DestinationResponse


#------------------------------------------------------




# =====================
# 🔹 Source Models
# =====================
class SourceBase(BaseModel):
    name: str = Field(..., description="Name of the source")
    description: Optional[str] = Field(None, description="Description of this source")
    status: Literal["Active", "Inactive"] = Field(
        "Active", description="Source status"
    )

    @field_validator("name")
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError("Source name cannot be empty.")
        return value

    @field_validator("status")
    def validate_status(cls, value):
        allowed = ["Active", "Inactive"]
        if value not in allowed:
            raise ValueError(f"Invalid status '{value}'. Allowed values: {allowed}")
        return value


class SourceCreate(SourceBase):
    location: "LocationCreate" = Field(
        ..., description="Associated location for this source"
    )

    @field_validator("location")
    def validate_location_type(cls, value):
        if value.location_type.lower() != "source":
            raise ValueError("Location type must be 'source' for Source creation.")
        return value


class SourceUpdate(SourceBase):
   
    organization_id: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    location_uuid: Optional[str] = None
    location: Optional["LocationResponse"] = None  # 

    class Config:
        from_attributes = True



class SourceResponse(SourceBase):
    id: str
    created_at: datetime
    updated_at: datetime
    location_uuid: str
    organization_id: str
    location: Optional["LocationResponse"] = None

    class Config:
        from_attributes = True



class SourceUpdateResponse(BaseModel):
    message: str
    destination: DestinationResponse

class SourcePatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["Active", "Inactive"]] = None
    location: Optional[LocationUpdate] = None  

    class Config:
        from_attributes = True

    @field_validator("name")
    def validate_name(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Source name cannot be empty.")
        return value



#----------------------------------------------


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    organization_name: str

    @field_validator("first_name", "last_name", "organization_name")
    def validate_non_empty(cls, value: str, field):
        """
        Ensure no empty.
        """
        if not value.strip():
            raise ValueError(f"{field.name.replace('_', ' ').title()} cannot be empty.")
        return value.strip().title() 


class SignupResponse(BaseModel):
    status: Literal["success", "error"] = "success"
    message: str
    organization_id: str
    user_id: str


class SetPasswordRequest(BaseModel):
    user_id: str
    password: str


class UserSignupRequest(BaseModel):
    user_id: UUID  
    email: EmailStr
    password: str
    confirm_password: str

class UserSignupResponse(BaseModel):
    status: str = "success"
    message: str




class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str





class ResetPasswordRequest(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str
    confirm_password: str

class ResetPasswordResponse(BaseModel):
    message: str



class InviteUserRequest(BaseModel):
    emails: list[EmailStr]
    access: AccessRole = Field(default=AccessRole.VIEWER)
    organization_id: str
    invited_by: str  

class InviteUserResponse(BaseModel):
    message: str
    user_ids: list[UUID]  







   