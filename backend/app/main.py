from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.database import engine, Base

# Registar todos os modelos antes de create_all
import app.models.user       # noqa
import app.models.category   # noqa
import app.models.tag        # noqa
import app.models.content    # noqa
import app.models.verbete    # noqa
import app.models.log        # noqa

from app.api.routes import auth, content, verbete, public, admin

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ── Aplicação ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Biblioteca Marxista — API",
    description="API do back-end para a Biblioteca Marxista · Servir ao Povo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting middleware (global)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Criar tabelas ao arrancar (dev) ───────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(verbete.router, prefix="/api/v1")
app.include_router(public.router,  prefix="/api/v1")
app.include_router(admin.router,   prefix="/api/v1")

# ── Rate limit específico no endpoint de login (5/min por IP) ─────────────────
# Aplicado APÓS include_router para que a rota já exista no app
_login_route = next(
    (r for r in app.routes if getattr(r, "path", "") == "/api/v1/auth/login"),
    None,
)
if _login_route:
    # Adiciona o limiter à rota específica
    _login_route.endpoint = limiter.limit("5/minute")(_login_route.endpoint)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "version": "1.0.0"}
