from urllib.parse import unquote_plus

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..utils import templates, validate_turnstile

__all__ = ("session_router",)

session_router = APIRouter()


@session_router.get("/")
async def login_page(request: Request, redirect: str | None = None):
    uid = request.session.get("user_id")
    if uid and await request.app.state.database.users.get_user(uid):
        return RedirectResponse(unquote_plus(redirect) if redirect else "/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


@session_router.post("/")
async def login_submit(request: Request, redirect: str | None = None):
    # skip if already logged in
    uid = request.session.get("user_id")
    if uid and await request.app.state.database.users.get_user(uid):
        return RedirectResponse(unquote_plus(redirect) if redirect else "/dashboard")

    # parse form data
    data = await request.form()

    # validate CAPTCHA
    if not await validate_turnstile(request.app.state, data.get("cf-turnstile-response")):
        return templates.TemplateResponse("index.html", {"request": request, "alert": "CAPTCHA verification failed."})

    action = data.get("submit", "").lower()
    if action not in ("login", "register"):
        raise HTTPException(status_code=400, detail="Invalid form submission.")

    # get credentials
    email = data.get("email", "")
    password = data.get("password", "")

    # Login flow
    if action == "login":
        try:
            email_info = validate_email(email, check_deliverability=False)
            user_id = await request.app.state.database.users.verify_user_credentials(email_info.normalized, password)
        except (EmailNotValidError, ValueError):
            return templates.TemplateResponse("index.html", {"request": request, "alert": "Invalid credentials."})
        request.session["user_id"] = user_id
        return RedirectResponse(unquote_plus(redirect) if redirect else "/dashboard")

    # Registration flow
    if action == "register":
        try:
            email_info = validate_email(email)
        except EmailNotValidError:
            return templates.TemplateResponse("index.html", {"request": request, "alert": "Invalid email address."})
        if await request.app.state.database.users.get_user_by_email(email_info.normalized):
            return templates.TemplateResponse("index.html", {"request": request, "alert": "Email already registered."})
        user_id = await request.app.state.database.users.create_user(email_info.normalized, password)
        token = await request.app.state.database.users.create_token(user_id, "email")
        await request.app.state.mailer.send_email_verification(email_info.normalized, token)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "alert": "Registration successful! Please check your email to verify your account."},
        )


@session_router.get("/recover")
async def recover_page(): ...


@session_router.post("/recover")
async def recover_submit(): ...
