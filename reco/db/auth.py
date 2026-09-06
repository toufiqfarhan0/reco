"""Supabase GoTrue JWT Authentication and User Identity Extraction (Track 1).

Implements GoTrue JWT verification, header extraction (Authorization: Bearer <token>),
and multi-tenant user isolation context enforcement.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional
import jwt
from pydantic import BaseModel, ConfigDict, Field

from reco.db.models import AuthenticationError

logger = logging.getLogger(__name__)


class UserContext(BaseModel):
    """Authenticated user context derived from GoTrue JWT claims."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(description="Unique GoTrue user UUID (from 'sub' claim)")
    email: Optional[str] = Field(default=None, description="User email address")
    role: str = Field(default="authenticated", description="GoTrue user role (e.g. authenticated)")
    claims: Dict[str, Any] = Field(default_factory=dict, description="Full raw JWT claims payload")


class GoTrueAuthHandler:
    """Handles parsing and verification of Supabase GoTrue JWT tokens."""

    def __init__(self, jwt_secret: Optional[str] = None):
        """Initialize with optional JWT secret for cryptographic verification.

        If jwt_secret is not set, attempts to read SUPABASE_JWT_SECRET from environment.
        In local dev/test mode without a secret, claims (including expiration) are validated.
        """
        self.jwt_secret = jwt_secret or os.getenv("SUPABASE_JWT_SECRET")

    @staticmethod
    def extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
        """Extract the raw JWT from an 'Authorization: Bearer <token>' header string.

        Args:
            auth_header: The Authorization header string.

        Returns:
            The raw token string if present and formatted as Bearer, else None.
        """
        if not auth_header or not isinstance(auth_header, str):
            return None

        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def verify_token(self, token: str, verify_signature: Optional[bool] = None) -> UserContext:
        """Verify and decode a GoTrue JWT token, extracting the UserContext.

        Args:
            token: The raw JWT token string.
            verify_signature: Whether to verify cryptographic signature. Defaults to True
                              if jwt_secret is configured, False otherwise.

        Returns:
            UserContext containing user_id (sub), email, and claims.

        Raises:
            AuthenticationError: If the token is invalid, expired, or missing 'sub'.
        """
        if not token or not isinstance(token, str):
            raise AuthenticationError("JWT token string cannot be empty.")

        should_verify_sig = (
            verify_signature if verify_signature is not None else bool(self.jwt_secret)
        )

        try:
            decode_options = {
                "verify_signature": should_verify_sig,
                "verify_exp": True,
                "verify_aud": False,
                "require": ["sub", "exp"],
            }

            key = self.jwt_secret if should_verify_sig else ""
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["HS256"],
                options=decode_options,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(f"GoTrue JWT token has expired: {exc}") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(f"Invalid GoTrue JWT token: {exc}") from exc
        except Exception as exc:
            raise AuthenticationError(f"Failed to decode GoTrue token: {exc}") from exc

        user_id = claims.get("sub")
        if not user_id or not str(user_id).strip():
            raise AuthenticationError("GoTrue JWT missing required 'sub' (user_id) claim.")

        return UserContext(
            user_id=str(user_id),
            email=claims.get("email"),
            role=claims.get("role", "authenticated"),
            claims=claims,
        )

    def authenticate_header(self, auth_header: Optional[str]) -> UserContext:
        """Convenience method to extract and verify JWT directly from Authorization header.

        Args:
            auth_header: Value of 'Authorization' HTTP header.

        Returns:
            Authenticated UserContext.

        Raises:
            AuthenticationError: If header is missing, malformed, or contains invalid token.
        """
        token = self.extract_bearer_token(auth_header)
        if not token:
            raise AuthenticationError(
                "Missing or malformed Authorization header. Expected: 'Authorization: Bearer <token>'."
            )
        return self.verify_token(token)

    @staticmethod
    def create_test_token(
        user_id: str,
        email: str = "agent_engineer@reco.ai",
        role: str = "authenticated",
        secret: str = "default_test_jwt_secret_key_32_chars_long",
        expires_in_seconds: int = 3600,
        **extra_claims: Any
    ) -> str:
        """Create a cryptographically signed GoTrue-compatible JWT token for testing.

        Args:
            user_id: Target user UUID for 'sub' claim.
            email: User email address.
            role: Auth role (defaults to 'authenticated').
            secret: Secret key for HS256 signing.
            expires_in_seconds: Token TTL in seconds (negative value creates an expired token).
            extra_claims: Additional claims to include in the payload.

        Returns:
            Signed JWT token string.
        """
        now = int(time.time())
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "aud": "authenticated",
            "iss": "supabase-gotrue",
            "iat": now,
            "exp": now + expires_in_seconds,
            "app_metadata": {"provider": "email"},
            "user_metadata": {},
        }
        payload.update(extra_claims)
        return jwt.encode(payload, secret, algorithm="HS256")
