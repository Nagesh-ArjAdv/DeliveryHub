from fastapi import FastAPI, APIRouter, Depends, HTTPException , status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from datetime import datetime
import uuid
from schemas.pymodels import *
from database import init_database, get_session
from destination import destinations
from source import source
from models import User, Organization
from auth_utils import hash_password, verify_password, create_access_token,get_current_user




app = FastAPI(title="Delivery Hub API", version="2.0.0")


app.include_router(destinations.router)
app.include_router(source.router)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])



@app.on_event("startup")
async def on_startup():
    init_database()

@app.get("/")
async def read_root():
    return {"message": "Welcome to DeliveryHub FastAPI application!"}



@auth_router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    
    first_name = payload.first_name
    last_name = payload.last_name
    email = payload.email
    organization_name = payload.organization_name

    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    org = Organization(
        id=str(uuid.uuid4()),
        name=organization_name,
        description=f"Organization for {first_name} {last_name}",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(org)
    session.commit()
    session.refresh(org)

    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password="",
        access=AccessRole.ADMIN,
        is_active=False,
        created_at=datetime.utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return SignupResponse(
        message="Signup successful. Please complete your registration to activate your account.",
        organization_id=org.id,
        user_id=user.id,
    )





@auth_router.post("/set-password")
async def set_password(payload: SetPasswordRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == payload.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active:
        raise HTTPException(status_code=400, detail="User is already active")

    # Hash and set password
    user.hashed_password = hash_password(payload.password)
    user.is_active = True
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"status": "success",
        "message": "Password set successfully. You can now log in."}



@auth_router.post("/login",response_model=LoginResponse)
async def login(payload: LoginRequest, session: Session = Depends(get_session)):
    
    email = payload.email
    password = payload.password

    if not all([email, password]):
        raise HTTPException(status_code=400, detail="Email and password required")

    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    access_token = create_access_token({"sub": user.email})
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()

    return {"access_token": access_token, "token_type": "bearer"}



@auth_router.post("/inviteUser", response_model=InviteUserResponse)
async def invite_user( payload: InviteUserRequest,current_user: User = Depends(get_current_user),session: Session = Depends(get_session)):
   
    if current_user.access not in [AccessRole.ADMIN, AccessRole.DEVELOPER]:
        raise HTTPException(status_code=403, detail="You don't have permission for this action")

    org = session.get(Organization, payload.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    
    invited_by_id = None
    invited_by = payload.invited_by
    if "@" in invited_by:
        inviter = session.exec(select(User).where(User.email == invited_by.lower())).first()
    elif invited_by.isdigit():
        inviter = session.get(User, int(invited_by))
    else:
        inviter = session.exec(select(User).where(User.first_name == invited_by)).first()
    if inviter:
        invited_by_id = inviter.id

    created_user_ids = []

    for email in payload.emails:
        email = email.lower()
        existing_user = session.exec(select(User).where(User.email == email)).first()
        if existing_user:
            continue  

        user = User(
            organization_id=payload.organization_id,
            first_name="",
            last_name="",
            email=email,
            access=payload.access,
            is_active=False,
            hashed_password=hash_password(str(uuid.uuid4())),
            invited_by=invited_by_id
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        created_user_ids.append(user.id)

    if not created_user_ids:
        raise HTTPException(status_code=400, detail="All users already exist")

    return InviteUserResponse(
    message=f"{len(created_user_ids)} user(s) invited successfully",
    user_ids=created_user_ids 
)



@auth_router.post("/userSignup", response_model=UserSignupResponse)
async def user_signup(payload: UserSignupRequest, session: Session = Depends(get_session)):

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = session.get(User, str(payload.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation link")

    if user.is_active:
        raise HTTPException(status_code=400, detail="User already activated")

    if user.email.lower() != payload.email.lower():
        raise HTTPException(status_code=400, detail="Email does not match the invited user")

    # Activate the user
    user.hashed_password = hash_password(payload.password)
    user.is_active = True

    session.add(user)
    session.commit()

    return UserSignupResponse(message="User signup completed successfully")



@auth_router.post("/resetPassword",response_model=ResetPasswordResponse)
async def reset_password(payload: ResetPasswordRequest, session: Session = Depends(get_session)):
 
    email = payload.email
    password = payload.old_password
    new_password = payload.new_password
    confirm_password = payload.confirm_password

    if not all([email, new_password, confirm_password]):
        raise HTTPException(status_code=400, detail="All fields are required")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(password)
    session.add(user)
    session.commit()

    return JSONResponse({"message": "Password successfully reset"}, status_code=200)

app.include_router(auth_router)