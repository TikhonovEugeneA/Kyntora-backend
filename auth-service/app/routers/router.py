from fastapi import APIRouter, Depends
from typing import Annotated
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.routers.schemas import (
    RefreshRequest,
    SignInRequest,
    SignUpRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"], route_class=DishkaRoute)
bearer = HTTPBearer()


@router.post("/sign-up", status_code=201, response_model=UserResponse)
async def sign_up(body: SignUpRequest, service: FromDishka[AuthService]):
    return await service.sign_up(
        first_name=body.first_name,
        last_name=body.last_name,
        login=body.login,
        password=body.password.get_secret_value(),
    )


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(body: SignInRequest, service: FromDishka[AuthService]):
    token_pair = await service.sign_in(
        login=body.login, password=body.password.get_secret_value()
    )
    return TokenResponse(
        access_token=token_pair.access_token, refresh_token=token_pair.refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, service: FromDishka[AuthService]):
    pair = await service.update_access_token(body.refresh_token)
    return TokenResponse(
        access_token=pair.access_token, refresh_token=pair.refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def me(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    service: FromDishka[AuthService],
):
    return await service.get_current_user(credentials.credentials)
