"""
Email service — sends verification and password reset emails.
Falls back to logging when SMTP is not configured.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
VERIFY_TOKEN_EXPIRE_HOURS = 24
RESET_TOKEN_EXPIRE_HOURS = 1


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not settings.SMTP_HOST:
        logger.info(
            "SMTP not configured — email would be sent to %s: %s",
            to_email,
            subject,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.SMTP_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def create_verification_token(user_id: str, email: str) -> str:
    """Create a JWT token for email verification."""
    expire = datetime.now(timezone.utc) + timedelta(hours=VERIFY_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "email": email, "exp": expire, "type": "email_verify"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user_id: str, email: str) -> str:
    """Create a JWT token for password reset."""
    expire = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "email": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_verification_token(token: str) -> dict | None:
    """Decode and validate an email verification token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verify":
            return None
        return {"user_id": payload["sub"], "email": payload["email"]}
    except Exception:
        return None


def decode_reset_token(token: str) -> dict | None:
    """Decode and validate a password reset token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return {"user_id": payload["sub"], "email": payload["email"]}
    except Exception:
        return None


def send_verification_email(email: str, token: str) -> bool:
    """Send email verification link."""
    verify_url = f"http://localhost:3000/verify-email?token={token}"
    html = f"""
    <h2>Verify your AI Film Studio account</h2>
    <p>Click the link below to verify your email address:</p>
    <p><a href="{verify_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background: #7c3aed;
        color: white;
        text-decoration: none;
        border-radius: 8px;
    ">Verify Email</a></p>
    <p>Or copy this link: {verify_url}</p>
    <p>This link expires in {VERIFY_TOKEN_EXPIRE_HOURS} hours.</p>
    """
    return _send_email(email, "Verify your AI Film Studio account", html)


def send_password_reset_email(email: str, token: str) -> bool:
    """Send password reset link."""
    reset_url = f"http://localhost:3000/reset-password?token={token}"
    html = f"""
    <h2>Reset your AI Film Studio password</h2>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background: #7c3aed;
        color: white;
        text-decoration: none;
        border-radius: 8px;
    ">Reset Password</a></p>
    <p>Or copy this link: {reset_url}</p>
    <p>This link expires in {RESET_TOKEN_EXPIRE_HOURS} hour(s). If you didn't request this, ignore this email.</p>
    """
    return _send_email(email, "Reset your AI Film Studio password", html)
