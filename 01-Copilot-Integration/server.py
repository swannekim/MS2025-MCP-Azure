# server.py
import os
import time
import json
import logging
import contextvars
import asyncio
import typing as t
import functools
import inspect
from dataclasses import dataclass
from typing import Optional, List
import json

import jwt
from jwt.algorithms import RSAAlgorithm
from jwt import decode as jwt_decode, PyJWKClient, get_unverified_header
import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from mcp.server.fastmcp import FastMCP, Context
from prompt_shields_foundry import check_prompt_attack
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# 환경설정
# ----------------------------
AUTH_MODE = os.getenv("AUTH_MODE", "api-key").lower()
API_KEY = os.getenv("API_KEY", "")
DEFAULT_ROLES = [r.strip() for r in os.getenv("DEFAULT_ROLES", "user").split(",") if r.strip()]

TENANT_ID = os.getenv("TENANT_ID", "")
AAD_AUDIENCE = os.getenv("AAD_AUDIENCE", "")
AAD_ISSUER = os.getenv("AAD_ISSUER", f"https://login.microsoftonline.com/{TENANT_ID}/v2.0")

CS_ENDPOINT = os.getenv("CS_ENDPOINT", "").rstrip("/")
CS_KEY = os.getenv("CS_KEY", "")
CS_API_VERSION = os.getenv("CS_API_VERSION", "")  # per docs

PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp-secure")

# === helpers: stdio 감지 ===
def _is_stdio() -> bool:
    return os.getenv("MCP_TRANSPORT", "stdio").lower() == "stdio"

def _safe_client_id(ctx: Context) -> str:
    cid = getattr(ctx, "client_id", None)
    if not cid:
        cid = getattr(getattr(ctx, "session", None), "client_id", None)
    if not cid:
        cid = f"stdio-{os.getpid()}"
    return cid


# ----------------------------
# Principal & 컨텍스트 보관
# ----------------------------
@dataclass
class Principal:
    sub: str
    roles: list[str]

_current_principal: contextvars.ContextVar[Principal | None] = contextvars.ContextVar(
    "principal", default=None
)

def get_principal() -> Principal | None:
    p = _current_principal.get()
    if p is None and _is_stdio():
        # stdio 경로는 HTTP 미들웨어를 안 타므로, 기본 롤로 가짜 주체 부여
        return Principal(sub="stdio-user", roles=DEFAULT_ROLES or ["user"])
    return p

# ----------------------------
# AAD(JWT) 검증 유틸
# ----------------------------
_jwks_cache: dict[str, t.Any] = {}
_jwks_cache_exp: float = 0

async def _get_jwks(client: httpx.AsyncClient) -> dict:
    """OIDC 설정에서 JWKS를 가져오고 캐시합니다."""
    global _jwks_cache, _jwks_cache_exp
    now = time.time()
    if now < _jwks_cache_exp and _jwks_cache:
        return _jwks_cache

    # OpenID configuration → jwks_uri
    resp = await client.get(
        f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration",
        timeout=10,
    )
    resp.raise_for_status()
    oidc = resp.json()
    jwks_uri = oidc["jwks_uri"]

    r2 = await client.get(jwks_uri, timeout=10)
    r2.raise_for_status()
    jwks = r2.json()

    _jwks_cache = jwks
    _jwks_cache_exp = now + 3600
    return jwks

from jwt import decode as jwt_decode, PyJWKClient, get_unverified_header

async def validate_jwt(token: str, client: httpx.AsyncClient) -> dict:
    # OIDC에서 jwks_uri만 비동기로 가져오기
    resp = await client.get(
        f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration",
        timeout=10,
    )
    resp.raise_for_status()
    jwks_uri = resp.json()["jwks_uri"]

    jwk_client = PyJWKClient(jwks_uri)
    signing_key = await asyncio.to_thread(jwk_client.get_signing_key_from_jwt, token)

    claims = jwt_decode(
        token,
        key=signing_key.key, # PublicKey 타입으로 보장
        algorithms=["RS256"],
        audience=AAD_AUDIENCE,
        issuer=AAD_ISSUER,
        options={"require": ["exp", "iat", "iss", "aud"]},
    )
    return claims

# async def validate_jwt(token: str, client: httpx.AsyncClient) -> dict:
#     header = jwt.get_unverified_header(token)
#     jwks = await _get_jwks(client)
#     key = None
#     for k in jwks.get("keys", []):
#         if k.get("kid") == header.get("kid"):
#             key = RSAAlgorithm.from_jwk(json.dumps(k))
#             break

#     if not key:
#         raise ValueError("JWK not found")

#     claims = jwt.decode(
#         token,
#         key=key,
#         algorithms=["RS256"],
#         audience=AAD_AUDIENCE,
#         issuer=AAD_ISSUER,
#         options={"require": ["exp", "iat", "iss", "aud"]},
#     )
#     return claims

# ----------------------------
# Prompt Shields 연동
# ----------------------------
async def is_prompt_attack(user_prompt: str, documents: list[str] | None) -> bool:
    """Azure AI Content Safety Prompt Shields를 호출해 공격 여부를 판단합니다."""
    if not CS_ENDPOINT or not CS_KEY:
        # 안전 기본값: 미구성 시 검사 스킵(운영에서는 차단 또는 강등 권장)
        log.warning("Content Safety not configured; skipping Prompt Shields check.")
        return False

    # 동기 함수이므로 스레드로 오프로드
    return await asyncio.to_thread(
        check_prompt_attack,
        user_prompt,
        documents or [],
        CS_ENDPOINT,
        CS_KEY,
        CS_API_VERSION,
    )

# ----------------------------
# RBAC 데코레이터
# ----------------------------

def require_roles(allowed: list[str]):
    allowed_set = set(allowed)

    def deco(fn: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
        original_sig = inspect.signature(fn)

        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def _async_wrapped(*args: t.Any, **kwargs: t.Any):
                p = get_principal()
                if p is None or not (set(p.roles) & allowed_set):
                    raise PermissionError("Forbidden by RBAC")
                return await fn(*args, **kwargs)
            # Pylance가 __signature__ 타입을 모른다고 경고하므로 setattr 사용
            setattr(_async_wrapped, "__signature__", original_sig)  # type: ignore[attr-defined]
            return _async_wrapped  # type: ignore[return-value]

        @functools.wraps(fn)
        def _sync_wrapped(*args: t.Any, **kwargs: t.Any):
            p = get_principal()
            if p is None or not (set(p.roles) & allowed_set):
                raise PermissionError("Forbidden by RBAC")
            return fn(*args, **kwargs)
        setattr(_sync_wrapped, "__signature__", original_sig)  # type: ignore[attr-defined]
        return _sync_wrapped  # type: ignore[return-value]

    return deco

# def require_roles(allowed: list[str]):
#     allowed_set = set(allowed)

#     def deco(fn):
#         sig = inspect.signature(fn)  # ← 원본 시그니처 보관

#         if asyncio.iscoroutinefunction(fn):
#             @functools.wraps(fn)
#             async def _async_wrapped(*args, **kwargs):
#                 p = get_principal()
#                 if p is None or not (set(p.roles) & allowed_set):
#                     raise PermissionError("Forbidden by RBAC")
#                 return await fn(*args, **kwargs)
#             _async_wrapped.__signature__ = sig   # ← 시그니처 복원
#             return _async_wrapped

#         @functools.wraps(fn)
#         def _sync_wrapped(*args, **kwargs):
#             p = get_principal()
#             if p is None or not (set(p.roles) & allowed_set):
#                 raise PermissionError("Forbidden by RBAC")
#             return fn(*args, **kwargs)
#         _sync_wrapped.__signature__ = sig       # ← 시그니처 복원
#         return _sync_wrapped

#     return deco

# def require_roles(allowed: list[str]):
#     """요구 역할이 하나라도 일치해야 통과."""
#     allowed_set = set(allowed)

#     def deco(fn):

#         @functools.wraps(fn)
#         async def _async_wrapped(*args, **kwargs):
#             p = get_principal()
#             if p is None or not (set(p.roles) & allowed_set):
#                 raise PermissionError("Forbidden by RBAC")
#             return await fn(*args, **kwargs)

#         @functools.wraps(fn)
#         def _sync_wrapped(*args, **kwargs):
#             p = get_principal()
#             if p is None or not (set(p.roles) & allowed_set):
#                 raise PermissionError("Forbidden by RBAC")
#             return fn(*args, **kwargs)

#         return _async_wrapped if asyncio.iscoroutinefunction(fn) else _sync_wrapped

#     return deco

# ----------------------------
# FastMCP 서버 정의
# ----------------------------
mcp = FastMCP("SecureMCP")

@mcp.tool(title="Who am I?")
def whoami(ctx: Context) -> dict:
    """현재 인증 주체와 역할을 반환합니다."""
    p = get_principal()
    return {
        "client_id": _safe_client_id(ctx),
        "transport": "stdio" if _is_stdio() else "http",
        "principal": None if not p else {"sub": p.sub, "roles": p.roles},
        "effective_roles": [] if not p else p.roles,
    }

@mcp.tool(title="Safe Summarize")
async def summarize(text: str, ctx: Context, documents: Optional[List[str]] | None = None) -> str:
    """Prompt Shields로 입력을 검사한 뒤 간단 요약(데모)."""
    if await is_prompt_attack(text, documents):
        # 경고 로그를 MCP 세션에 전송
        await ctx.session.send_log_message(
            level="warning",
            data="Blocked by Prompt Shields",
            logger="mcp-secure",
            related_request_id=ctx.request_id,
        )
        raise ValueError("Prompt attack detected by Azure Prompt Shields")

    # 데모: 매우 단순한 요약
    return text[:200] + ("..." if len(text) > 200 else "")

# 데코레이터 순서 주의: 역할 검증을 먼저 적용하고, 그 다음 MCP에 등록
@require_roles(["admin"])
@mcp.tool(title="Admin Echo")
def admin_echo(message: str, ctx: Context) -> str:
    """관리자 전용 에코(권한 확인 데모)."""
    return f"[admin] {message}"

# ----------------------------
# 인증 미들웨어 (API Key / AAD)
# ----------------------------
class AuthzMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # MCP 엔드포인트만 보호, /health 등은 통과
        if not request.url.path.startswith("/mcp"):
            return await call_next(request)

        # 1) API Key
        if AUTH_MODE == "api-key":
            key = request.headers.get("x-api-key")
            if not key or key != API_KEY:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            principal = Principal(sub="apikey-user", roles=DEFAULT_ROLES)

        # 2) AAD (Bearer JWT)
        elif AUTH_MODE == "aad":
            authz = request.headers.get("authorization", "")
            if not authz.lower().startswith("bearer "):
                return JSONResponse({"error": "Missing bearer"}, status_code=401)
            token = authz.split(" ", 1)[1]
            async with httpx.AsyncClient() as client:
                try:
                    claims = await validate_jwt(token, client)
                except Exception as e:
                    log.warning("JWT validation failed: %s", e)
                    return JSONResponse({"error": "Invalid token"}, status_code=401)
            roles: list[str] = []
            if "roles" in claims:
                roles = list(claims["roles"])
            elif "scp" in claims:
                roles = claims["scp"].split()
            principal = Principal(
                sub=claims.get("sub") or claims.get("oid", "unknown"),
                roles=roles or DEFAULT_ROLES,
            )

        else:
            return JSONResponse({"error": "Server misconfigured: AUTH_MODE"}, status_code=500)

        # 요청 컨텍스트에 주체 저장
        token = _current_principal.set(principal)
        try:
            resp = await call_next(request)
        finally:
            _current_principal.reset(token)
        return resp

# ----------------------------
# ASGI 앱 구성 (Streamable HTTP)
# ----------------------------
mcp_app = mcp.streamable_http_app()

# 인증 미들웨어 장착
mcp_app.add_middleware(AuthzMiddleware)

# /health 라우트 추가
mcp_app.router.routes.append(Route("/health", lambda request: PlainTextResponse("ok")))

# 최종 app
app = mcp_app

if __name__ == "__main__":
    import uvicorn
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "stdio":
        # ✅ Copilot Chat/VS Code MCP가 요구하는 stdio 서버 실행
        mcp.run()  # FastMCP가 제공 (stdin/stdout)
    else:
        # 여전히 HTTP로도 띄울 수 있게 유지
        uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
