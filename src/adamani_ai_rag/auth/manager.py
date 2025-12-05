from typing import Optional
import uuid

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from ..config import get_settings
from ..database import User
from ..database.session import get_async_session
from ..utils.logger import get_logger

settings = get_settings()
logger = get_logger()

# Custom password context with Argon2
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager with custom logic."""

    reset_password_token_secret = settings.jwt_secret_key
    verification_token_secret = settings.jwt_secret_key

    def __init__(self, user_db: SQLAlchemyUserDatabase):
        super().__init__(user_db)
        # Override password helper to use Argon2
        self.password_helper = PasswordHelper(pwd_context)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after user registration - create default organization."""
        logger.info(f"User {user.id} has registered.")

        # Import here to avoid circular imports
        from ..services.organization_service import OrganizationService
        from ..database.session import async_session_maker

        # Create default organization for new user
        async with async_session_maker() as session:
            org_service = OrganizationService(session)
            org_name = user.full_name or user.email.split('@')[0]
            await org_service.create_organization(
                name=f"{org_name}'s Workspace",
                owner_id=user.id,
                plan_tier="free"
            )
            logger.success(f"Created default organization for user {user.id}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after forgot password request."""
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after verification request."""
        logger.info(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Get user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get user manager instance."""
    yield UserManager(user_db)