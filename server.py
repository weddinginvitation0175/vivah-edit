import os
import re
import socket
import io
import json
import base64
import urllib.parse
import hmac
import hashlib
import time
import shutil
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends, Header
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import qrcode

from xml_engine import generate_wedding_xml, generate_wedding_package, get_or_create_template_map
from ai_scanner import scan_wedding_card, get_demo_sample_data, process_card_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
SCANNED_CARDS_DIR = os.path.join(BASE_DIR, "scanned_shadi_cards")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(SCANNED_CARDS_DIR, exist_ok=True)

def cleanup_old_scans(max_age_days: int = 7):
    """Automatically deletes scanned card folders older than 7 days (1 week)."""
    try:
        if not os.path.exists(SCANNED_CARDS_DIR):
            return
        now = time.time()
        cutoff = now - (max_age_days * 86400)
        for entry in os.scandir(SCANNED_CARDS_DIR):
            if entry.is_dir():
                try:
                    if entry.stat().st_mtime < cutoff:
                        shutil.rmtree(entry.path, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        print(f"Cleanup error: {e}")

def save_scanned_card_record(extracted_data: dict, pages_list: list) -> str:
    """Saves extracted JSON and first page thumbnail into scanned_shadi_cards folder."""
    try:
        cleanup_old_scans(7)
        now = time.time()
        dt_str = time.strftime("%Y%m%d_%H%M%S")
        groom = (extracted_data.get("groom_name") or "Groom").strip().replace(" ", "_")
        bride = (extracted_data.get("bride_name") or "Bride").strip().replace(" ", "_")
        folder_name = f"{dt_str}_{groom}_{bride}"
        scan_folder = os.path.join(SCANNED_CARDS_DIR, folder_name)
        os.makedirs(scan_folder, exist_ok=True)

        meta = {
            "scan_id": folder_name,
            "timestamp": now,
            "date_formatted": time.strftime("%d %b %Y, %I:%M %p"),
            "data": extracted_data,
            "num_pages": len(pages_list)
        }
        with open(os.path.join(scan_folder, "data.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        if pages_list and len(pages_list) > 0:
            try:
                from PIL import Image, ImageOps
                first_bytes = pages_list[0].get("bytes")
                if first_bytes:
                    img = Image.open(io.BytesIO(first_bytes))
                    img = ImageOps.exif_transpose(img)
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.thumbnail((320, 320))
                    img.save(os.path.join(scan_folder, "thumbnail.jpg"), "JPEG", quality=75)
            except Exception as e:
                print(f"Thumbnail generation error: {e}")
        return folder_name
    except Exception as e:
        print(f"Error saving scanned card record: {e}")
        return ""

# Copy sample_template.xml to templates dir if not exists
sample_src = os.path.join(BASE_DIR, "sample_template.xml")
sample_dst = os.path.join(TEMPLATES_DIR, "Green_Pink_2027_Final.xml")
if os.path.exists(sample_src) and not os.path.exists(sample_dst):
    with open(sample_src, "r", encoding="utf-8") as f_in, open(sample_dst, "w", encoding="utf-8") as f_out:
        f_out.write(f_in.read())

app = FastAPI(title="VivahEdit AI - After Motion Z XML Automation", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
PORT = int(os.environ.get("PORT", 8000))
MOBILE_URL = f"http://{LOCAL_IP}:{PORT}"

# ==================== GATEKEEPER SECURITY SHIELD ====================
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
_CONFIG_CACHE = None

def get_config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    default_cfg = {
        "admin_password": "7067",
        "editor_password": "7067",
        "secret_key": os.urandom(32).hex()
    }
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_cfg, f, indent=2)
        except Exception:
            pass
        _CONFIG_CACHE = default_cfg
        return _CONFIG_CACHE
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if "secret_key" not in cfg:
                cfg["secret_key"] = os.urandom(32).hex()
                save_config(cfg)
            _CONFIG_CACHE = cfg
            return _CONFIG_CACHE
    except Exception:
        _CONFIG_CACHE = default_cfg
        return _CONFIG_CACHE

def save_config(cfg: dict):
    global _CONFIG_CACHE
    _CONFIG_CACHE = cfg
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_editor_password() -> str:
    return str(get_config().get("editor_password", "7067")).strip()

def get_admin_password() -> str:
    return str(get_config().get("admin_password", "7067")).strip()

def get_secret_key() -> bytes:
    key_hex = get_config().get("secret_key", "default_secret_key_vivahedit")
    return key_hex.encode("utf-8")

def create_auth_token(password: str) -> str:
    ts = str(int(time.time()))
    sig = hmac.new(get_secret_key(), f"{ts}:{password}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"

def verify_auth_token(token: str, password: str, max_age_days: int = 30) -> bool:
    try:
        if not token or "." not in token:
            return False
        ts_str, sig = token.split(".", 1)
        ts = int(ts_str)
        if time.time() - ts > max_age_days * 86400:
            return False
        expected_sig = hmac.new(get_secret_key(), f"{ts_str}:{password}".encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

# ==================== MULTI-EDITOR PROFILES & ISOLATION ====================
EDITORS_CONFIG_PATH = os.path.join(BASE_DIR, "editors.json")
_EDITORS_CACHE = None
_EDITORS_MTIME = 0

def get_editors_data() -> dict:
    global _EDITORS_CACHE, _EDITORS_MTIME
    if os.path.exists(EDITORS_CONFIG_PATH):
        try:
            current_mtime = os.path.getmtime(EDITORS_CONFIG_PATH)
            if _EDITORS_CACHE is not None and current_mtime == _EDITORS_MTIME:
                return _EDITORS_CACHE
            with open(EDITORS_CONFIG_PATH, "r", encoding="utf-8") as f:
                _EDITORS_CACHE = json.load(f)
                _EDITORS_MTIME = current_mtime
                return _EDITORS_CACHE
        except Exception:
            pass
    if _EDITORS_CACHE is not None:
        return _EDITORS_CACHE
    
    default_editors = {
        "active_default_editor": "amar",
        "editors": [
            {
                "id": "amar",
                "name": "Amar",
                "role": "Lead Editor",
                "avatar": "fa-crown",
                "color": "from-amber-500 to-rose-600",
                "templates": [
                    "Blue Yellow Design 2027 final Copy.xml",
                    "Green_Pink_2027_Final.xml",
                    "White Yellow Design Final.xml"
                ],
                "default_template": "Blue Yellow Design 2027 final Copy.xml"
            },
            {
                "id": "sunil",
                "name": "Sunil",
                "role": "Editor",
                "avatar": "fa-video",
                "color": "from-blue-500 to-cyan-500",
                "templates": [],
                "default_template": ""
            },
            {
                "id": "ajay",
                "name": "Ajay",
                "role": "Editor",
                "avatar": "fa-wand-magic-sparkles",
                "color": "from-emerald-500 to-teal-500",
                "templates": [],
                "default_template": ""
            }
        ]
    }
    if not os.path.exists(EDITORS_CONFIG_PATH):
        try:
            with open(EDITORS_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_editors, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        _EDITORS_CACHE = default_editors
        return _EDITORS_CACHE
    
    try:
        with open(EDITORS_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _EDITORS_CACHE = data
            return _EDITORS_CACHE
    except Exception:
        _EDITORS_CACHE = default_editors
        return _EDITORS_CACHE

def save_editors_data(data: dict):
    global _EDITORS_CACHE
    _EDITORS_CACHE = data
    try:
        with open(EDITORS_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving editors.json: {e}")

def create_editor_token(editor_id: str) -> str:
    ts = str(int(time.time()))
    payload = f"{ts}:editor:{editor_id.lower()}"
    sig = hmac.new(get_secret_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{ts}.{editor_id.lower()}.{sig}"

def verify_editor_token(token: str, max_age_days: int = 90) -> Optional[str]:
    try:
        if not token or token.count(".") != 2:
            return None
        parts = token.split(".", 2)
        ts_str, editor_id, sig = parts[0], parts[1], parts[2]
        ts = int(ts_str)
        if time.time() - ts > max_age_days * 86400:
            return None
        payload = f"{ts_str}:editor:{editor_id.lower()}"
        expected_sig = hmac.new(get_secret_key(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return editor_id.lower()
        return None
    except Exception:
        return None

# Brute-force protection: IP -> list of failed attempt timestamps
FAILED_LOGINS: dict[str, list[float]] = {}
LOCKOUT_SECONDS = 900  # 15 minutes lockout
MAX_FAILED_ATTEMPTS = 5

def check_ip_rate_limit(ip: str) -> tuple[bool, int]:
    now = time.time()
    attempts = [t for t in FAILED_LOGINS.get(ip, []) if now - t < LOCKOUT_SECONDS]
    FAILED_LOGINS[ip] = attempts
    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        oldest = attempts[0]
        remaining = int(LOCKOUT_SECONDS - (now - oldest))
        return True, max(1, remaining)
    return False, 0

def record_failed_attempt(ip: str):
    now = time.time()
    attempts = [t for t in FAILED_LOGINS.get(ip, []) if now - t < LOCKOUT_SECONDS]
    attempts.append(now)
    FAILED_LOGINS[ip] = attempts

def clear_failed_attempts(ip: str):
    FAILED_LOGINS.pop(ip, None)

async def require_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_access_token: Optional[str] = Header(None),
    x_editor_id: Optional[str] = Header(None)
) -> dict:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif x_access_token:
        token = x_access_token.strip()

    editor_pwd = get_editor_password()
    # 1. Editor session token?
    ed_id = verify_editor_token(token) if token else None
    if ed_id:
        return {"authenticated": True, "editor_id": ed_id, "is_admin": (ed_id == "amar")}

    # 2. Master studio passcode token?
    if token and verify_auth_token(token, editor_pwd):
        chosen_editor = (x_editor_id or "amar").strip().lower()
        return {"authenticated": True, "editor_id": chosen_editor, "is_admin": True}

    raise HTTPException(
        status_code=401,
        detail="Access denied. Please choose an editor profile or enter passcode."
    )

# ==================== AUTH ROUTES ====================
@app.post("/api/auth/verify")
async def verify_auth(request: Request):
    ip = request.client.host if request.client else "unknown"
    is_locked, remaining_sec = check_ip_rate_limit(ip)
    if is_locked:
        mins = (remaining_sec + 59) // 60
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": f"Too many failed attempts! Security lockout active for {mins} minute(s).",
                "locked": True,
                "remaining_seconds": remaining_sec
            }
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    passcode = str(body.get("password", "")).strip()
    editor_pwd = get_editor_password()

    if passcode == editor_pwd:
        clear_failed_attempts(ip)
        token = create_auth_token(editor_pwd)
        return {
            "success": True,
            "token": token,
            "message": "Workspace unlocked!"
        }
    else:
        record_failed_attempt(ip)
        attempts_left = MAX_FAILED_ATTEMPTS - len(FAILED_LOGINS.get(ip, []))
        if attempts_left <= 0:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Security Alert: Account temporarily locked for 15 minutes due to multiple failed attempts.",
                    "locked": True
                }
            )
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": f"Incorrect passcode! {attempts_left} attempt(s) remaining.",
                "attempts_remaining": attempts_left
            }
        )

@app.get("/api/auth/check")
async def check_auth(
    authorization: Optional[str] = Header(None),
    x_access_token: Optional[str] = Header(None)
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif x_access_token:
        token = x_access_token.strip()

    editor_pwd = get_editor_password()
    ed_id = verify_editor_token(token) if token else None
    is_master = bool(token and verify_auth_token(token, editor_pwd))
    is_valid = bool(ed_id or is_master)

    editor_obj = None
    if is_valid:
        ed_data = get_editors_data()
        effective_id = ed_id or "amar"
        target = next((e for e in ed_data.get("editors", []) if e.get("id", "").lower() == effective_id), None)
        if target:
            editor_obj = {
                "id": target["id"],
                "name": target["name"],
                "role": target.get("role", "Editor"),
                "avatar": target.get("avatar", "fa-user"),
                "color": target.get("color", "from-amber-500 to-rose-600"),
                "default_template": target.get("default_template", "")
            }

    return {"authenticated": is_valid, "editor_id": ed_id or ("amar" if is_master else None), "editor": editor_obj}

# ==================== MULTI-EDITOR API ROUTES ====================
@app.get("/api/editors")
def list_editors():
    ed_data = get_editors_data()
    editors = ed_data.get("editors", [])
    result = []
    for ed in editors:
        tpls = ed.get("templates", [])
        existing = [t for t in tpls if os.path.exists(os.path.join(TEMPLATES_DIR, t))]
        result.append({
            "id": ed.get("id"),
            "name": ed.get("name"),
            "role": ed.get("role", "Editor"),
            "avatar": ed.get("avatar", "fa-user"),
            "color": ed.get("color", "from-amber-500 to-rose-600"),
            "templates_count": len(existing),
            "default_template": ed.get("default_template", "")
        })
    return {
        "success": True,
        "editors": result,
        "active_default_editor": ed_data.get("active_default_editor", "amar")
    }

@app.post("/api/editors/select")
async def select_editor(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    editor_id = str(body.get("editor_id", "")).strip().lower()
    if not editor_id:
        raise HTTPException(status_code=400, detail="editor_id is required")

    ed_data = get_editors_data()
    editors = ed_data.get("editors", [])
    target = next((e for e in editors if e.get("id", "").lower() == editor_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Editor '{editor_id}' not found")

    token = create_editor_token(target["id"])
    return {
        "success": True,
        "token": token,
        "editor": {
            "id": target["id"],
            "name": target["name"],
            "role": target.get("role", "Editor"),
            "avatar": target.get("avatar", "fa-user"),
            "color": target.get("color", "from-amber-500 to-rose-600"),
            "default_template": target.get("default_template", "")
        }
    }

@app.post("/api/editors/add")
async def add_editor(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    name = str(body.get("name", "")).strip()
    if not name or len(name) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")

    ed_data = get_editors_data()
    editors = ed_data.setdefault("editors", [])

    base_id = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    if not base_id:
        base_id = f"editor_{len(editors)+1}"
    ed_id = base_id
    idx = 2
    while any(e.get("id") == ed_id for e in editors):
        ed_id = f"{base_id}_{idx}"
        idx += 1

    colors = [
        "from-purple-500 to-indigo-600",
        "from-teal-500 to-emerald-600",
        "from-rose-500 to-pink-600",
        "from-cyan-500 to-blue-600",
        "from-amber-500 to-orange-600"
    ]
    avatars = ["fa-wand-magic-sparkles", "fa-video", "fa-palette", "fa-clapperboard", "fa-user-pen"]

    new_ed = {
        "id": ed_id,
        "name": name,
        "role": body.get("role", "Editor"),
        "avatar": avatars[len(editors) % len(avatars)],
        "color": colors[len(editors) % len(colors)],
        "templates": [],
        "default_template": ""
    }
    editors.append(new_ed)
    save_editors_data(ed_data)

    token = create_editor_token(ed_id)
    return {
        "success": True,
        "editor": new_ed,
        "token": token,
        "message": f"Editor '{name}' created successfully!"
    }

@app.post("/api/auth/change-password")
async def change_password(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    admin_pass = str(body.get("admin_password", "")).strip()
    new_editor_pass = str(body.get("new_editor_password", "")).strip()

    if admin_pass != get_admin_password():
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Incorrect Admin Password! Access denied."}
        )

    if not new_editor_pass or len(new_editor_pass) < 4:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "New passcode must be at least 4 characters long."}
        )

    cfg = get_config()
    cfg["editor_password"] = new_editor_pass
    # Rotating secret_key invalidates all previously issued tokens
    cfg["secret_key"] = os.urandom(32).hex()
    save_config(cfg)

    new_token = create_auth_token(new_editor_pass)
    return {
        "success": True,
        "message": "Editor passcode updated! All older active sessions revoked.",
        "new_token": new_token
    }

@app.get("/api/info")
def get_info():
    return {
        "ip": LOCAL_IP,
        "port": PORT,
        "mobile_url": MOBILE_URL,
        "local_url": f"http://localhost:{PORT}"
    }

@app.get("/api/qr")
def get_qr_code():
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(MOBILE_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2b003b", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/api/templates")
def list_templates(
    editor_id: Optional[str] = None,
    x_editor_id: Optional[str] = Header(None),
    auth: dict = Depends(require_auth)
):
    target_id = (editor_id or x_editor_id or auth.get("editor_id") or "amar").strip().lower()
    ed_data = get_editors_data()
    editors = ed_data.get("editors", [])
    target_ed = next((e for e in editors if e.get("id", "").lower() == target_id), None)
    if not target_ed:
        target_ed = next((e for e in editors if e.get("id") == "amar"), None)

    ed_tpl_names = target_ed.get("templates", []) if target_ed else []
    default_tpl = target_ed.get("default_template", "") if target_ed else ""

    templates = []
    for f in ed_tpl_names:
        full_p = os.path.join(TEMPLATES_DIR, f)
        if os.path.exists(full_p):
            clean_name = f[:-4]
            if clean_name.lower().startswith(f"{target_id}_"):
                clean_name = clean_name[len(target_id)+1:]
            clean_name = clean_name.replace("_", " ").strip()
            size_kb = round(os.path.getsize(full_p) / 1024, 1)
            templates.append({
                "id": f,
                "name": clean_name,
                "is_default": (f == default_tpl),
                "is_system": (f == "Green_Pink_2027_Final.xml"),
                "size_kb": size_kb,
                "path": full_p
            })

    if templates and not any(t["is_default"] for t in templates):
        templates[0]["is_default"] = True
        default_tpl = templates[0]["id"]
        if target_ed:
            target_ed["default_template"] = default_tpl
            save_editors_data(ed_data)

    return {
        "templates": templates,
        "default_template": default_tpl,
        "editor_id": target_id,
        "editor_name": target_ed.get("name", target_id) if target_ed else target_id
    }

@app.post("/api/templates/set-default")
async def set_default_template(
    request: Request,
    x_editor_id: Optional[str] = Header(None),
    auth: dict = Depends(require_auth)
):
    try:
        body = await request.json()
        template_id = body.get("template_id", "").strip()
        if not template_id:
            raise HTTPException(status_code=400, detail="template_id is required")
        target_id = (body.get("editor_id") or x_editor_id or auth.get("editor_id") or "amar").strip().lower()

        target_path = os.path.join(TEMPLATES_DIR, template_id)
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="Template file not found")

        ed_data = get_editors_data()
        target_ed = next((e for e in ed_data.get("editors", []) if e.get("id", "").lower() == target_id), None)
        if target_ed:
            target_ed["default_template"] = template_id
            save_editors_data(ed_data)

        cfg = get_config()
        cfg["default_template"] = template_id
        save_config(cfg)
        return {
            "success": True,
            "default_template": template_id,
            "editor_id": target_id,
            "message": f"Template {template_id} permanently saved as default for {target_ed.get('name', target_id)}!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/templates/{template_id}")
def delete_template(
    template_id: str,
    editor_id: Optional[str] = None,
    x_editor_id: Optional[str] = Header(None),
    auth: dict = Depends(require_auth)
):
    try:
        safe_id = os.path.basename(template_id)
        if safe_id == "Green_Pink_2027_Final.xml":
            raise HTTPException(status_code=400, detail="Default system template cannot be deleted.")

        target_id = (editor_id or x_editor_id or auth.get("editor_id") or "amar").strip().lower()
        ed_data = get_editors_data()
        target_ed = next((e for e in ed_data.get("editors", []) if e.get("id", "").lower() == target_id), None)

        if target_ed and safe_id in target_ed.get("templates", []):
            target_ed["templates"].remove(safe_id)
            if target_ed.get("default_template") == safe_id:
                target_ed["default_template"] = target_ed["templates"][0] if target_ed["templates"] else ""
            save_editors_data(ed_data)

        # Check if any other editor still uses this file
        other_using = any(safe_id in e.get("templates", []) for e in ed_data.get("editors", []))
        target_path = os.path.join(TEMPLATES_DIR, safe_id)
        if not other_using and os.path.exists(target_path):
            os.remove(target_path)

        cfg = get_config()
        if cfg.get("default_template") == safe_id:
            cfg["default_template"] = "Green_Pink_2027_Final.xml"
            save_config(cfg)

        return {
            "success": True,
            "message": f"Template {safe_id} removed from {target_ed.get('name', target_id) if target_ed else target_id}'s workspace."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/templates/upload")
@app.post("/api/upload-template")
async def upload_template(
    file: UploadFile = File(...),
    editor_id: Optional[str] = Form(None),
    x_editor_id: Optional[str] = Header(None),
    auth: dict = Depends(require_auth)
):
    try:
        raw_name = os.path.basename(file.filename or "").strip()
        contents = await file.read()
        if not contents or len(contents.strip()) == 0:
            raise HTTPException(status_code=400, detail="फाइल खाली है (Uploaded file is empty)")

        target_id = (editor_id or x_editor_id or auth.get("editor_id") or "amar").strip().lower()
        ed_data = get_editors_data()
        editors = ed_data.get("editors", [])
        target_ed = next((e for e in editors if e.get("id", "").lower() == target_id), None)
        if not target_ed:
            target_ed = next((e for e in editors if e.get("id") == "amar"), None)
            target_id = target_ed["id"]

        # 1. Handle .amzip or .zip packages automatically
        if raw_name.lower().endswith((".amzip", ".zip")):
            try:
                with zipfile.ZipFile(io.BytesIO(contents)) as zf:
                    xml_candidates = [n for n in zf.namelist() if n.lower().endswith(".xml")]
                    if not xml_candidates:
                        raise HTTPException(status_code=400, detail="इस .amzip पैकेज में कोई .xml फाइल नहीं मिली")
                    target_name = "project.xml" if "project.xml" in xml_candidates else xml_candidates[0]
                    contents = zf.read(target_name)
                    base_name = raw_name.rsplit(".", 1)[0]
                    raw_name = f"{base_name}.xml"
            except zipfile.BadZipFile:
                raise HTTPException(status_code=400, detail="अमान्य ZIP/AMZIP फाइल")

        # 2. Handle WhatsApp / Android .xml.txt renaming
        if raw_name.lower().endswith(".xml.txt"):
            raw_name = raw_name[:-4]
        elif raw_name.lower().endswith(".txt"):
            raw_name = raw_name[:-4] + ".xml"

        # 3. Check if contents are XML even if extension was missing
        contents_peek = contents[:2048].decode("utf-8", errors="ignore")
        is_xml_by_content = any(tag in contents_peek for tag in ["<scene", "<project", "<alight", "<?xml"])
        
        if not raw_name.lower().endswith(".xml"):
            if is_xml_by_content:
                raw_name = f"{raw_name}.xml"
            else:
                raise HTTPException(status_code=400, detail="कृपया केवल .xml या .amzip फाइल ही चुनें (Only .xml or .amzip supported)")

        # Clean filename while preserving Hindi and international characters
        cleaned_name = re.sub(r'[\\/*?:"<>|]', '_', raw_name).strip()
        if not cleaned_name.lower().endswith(".xml"):
            cleaned_name += ".xml"

        # Safe XML syntax verification (handle BOM and strict entities)
        contents_to_parse = contents[3:] if contents.startswith(b'\xef\xbb\xbf') else contents
        try:
            ET.fromstring(contents_to_parse)
        except ET.ParseError as pe:
            if not is_xml_by_content:
                raise HTTPException(status_code=400, detail=f"अमान्य XML फाइल (Invalid XML file: {pe})")

        # Disambiguate if owned by another editor
        is_owned_by_other = any(
            cleaned_name in e.get("templates", []) for e in editors if e.get("id") != target_id
        )
        save_filename = f"{target_id}_{cleaned_name}" if is_owned_by_other else cleaned_name

        dest_path = os.path.join(TEMPLATES_DIR, save_filename)
        with open(dest_path, "wb") as f:
            f.write(contents)

        # Automatically auto-analyze semantic layers and build mapping JSON
        try:
            tmap = get_or_create_template_map(dest_path)
            mapped_count = len(tmap.get("layers", {}))
        except Exception:
            mapped_count = 0

        # Register template for this editor
        if save_filename not in target_ed.get("templates", []):
            target_ed.setdefault("templates", []).append(save_filename)
        target_ed["default_template"] = save_filename
        save_editors_data(ed_data)

        # Also update root config default
        cfg = get_config()
        cfg["default_template"] = save_filename
        save_config(cfg)

        display_name = cleaned_name[:-4].replace("_", " ").strip()
        return {
            "success": True,
            "filename": save_filename,
            "name": display_name,
            "is_default": True,
            "editor_id": target_id,
            "mapped_layers": mapped_count,
            "message": f"Template {display_name} permanently saved for {target_ed['name']} and set as default!"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/demo-data")
def get_demo(auth: bool = Depends(require_auth)):
    return get_demo_sample_data()

@app.post("/api/scan")
async def scan_card(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    api_key: Optional[str] = Form(None),
    auth: bool = Depends(require_auth)
):
    try:
        all_uploads = []
        if files:
            all_uploads.extend(files)
        if file and file not in all_uploads:
            all_uploads.append(file)

        if not all_uploads:
            raise HTTPException(status_code=400, detail="No files uploaded")

        processed_pages = []
        for upload in all_uploads:
            content = await upload.read()
            fname = upload.filename or "card.jpg"
            ctype = upload.content_type or "image/jpeg"
            pages = process_card_file(content, filename=fname, content_type=ctype)
            processed_pages.extend(pages)

        if not processed_pages:
            raise HTTPException(status_code=400, detail="Could not process uploaded files or pages")

        extracted = scan_wedding_card(processed_pages, api_key=api_key)
        # Store scanned record into scanned_shadi_cards (with 7-day auto-expiry)
        saved_id = save_scanned_card_record(extracted, processed_pages)
        return {
            "success": True,
            "data": extracted,
            "pages_count": len(processed_pages),
            "scan_id": saved_id
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/scanned-cards")
async def get_scanned_cards_list(auth: bool = Depends(require_auth)):
    cleanup_old_scans(7)
    records = []
    if os.path.exists(SCANNED_CARDS_DIR):
        entries = [e for e in os.scandir(SCANNED_CARDS_DIR) if e.is_dir()]
        entries.sort(key=lambda e: e.stat().st_mtime, reverse=True)
        for entry in entries:
            json_file = os.path.join(entry.path, "data.json")
            if os.path.exists(json_file):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    has_thumb = os.path.exists(os.path.join(entry.path, "thumbnail.jpg"))
                    d = meta.get("data", {})
                    records.append({
                        "scan_id": meta.get("scan_id", entry.name),
                        "timestamp": meta.get("timestamp", entry.stat().st_mtime),
                        "date_formatted": meta.get("date_formatted", ""),
                        "groom_name": d.get("groom_name", ""),
                        "bride_name": d.get("bride_name", ""),
                        "pariwar_name": d.get("pariwar_name", ""),
                        "card_side": d.get("card_side", "groom"),
                        "num_pages": meta.get("num_pages", 1),
                        "has_thumbnail": has_thumb,
                        "data": d
                    })
                except Exception:
                    pass
    return {"success": True, "cards": records}

@app.get("/api/scanned-cards/{scan_id}/thumbnail")
async def get_scanned_card_thumbnail(scan_id: str):
    scan_id = os.path.basename(scan_id)
    thumb_path = os.path.join(SCANNED_CARDS_DIR, scan_id, "thumbnail.jpg")
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Thumbnail not found")

@app.delete("/api/scanned-cards/{scan_id}")
async def delete_scanned_card(scan_id: str, auth: bool = Depends(require_auth)):
    scan_id = os.path.basename(scan_id)
    folder_path = os.path.join(SCANNED_CARDS_DIR, scan_id)
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path, ignore_errors=True)
            return {"success": True, "message": "Scanned card removed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=404, detail="Card record not found")

@app.post("/api/generate")
async def generate_xml(
    data: str = Form(...),
    font_mode: str = Form("hybrid"),
    template_name: str = Form("Green_Pink_2027_Final.xml"),
    export_format: str = Form("auto"),
    editor_id: Optional[str] = Form(None),
    groom_photo: Optional[UploadFile] = File(None),
    bride_photo: Optional[UploadFile] = File(None),
    auth: dict = Depends(require_auth)
):
    try:
        parsed_data = json.loads(data)
        side = parsed_data.get("card_side", "groom")
        g_name = parsed_data.get("groom_name", "")
        b_name = parsed_data.get("bride_name", "")
        print(f"🎬 [API Generate] Template: {template_name} | Side: {side} | Groom: {g_name} | Bride: {b_name} | FontMode: {font_mode}")
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            target_id = (editor_id or (auth.get("editor_id") if isinstance(auth, dict) else None) or "amar").strip().lower()
            alt_path = os.path.join(TEMPLATES_DIR, f"{target_id}_{template_name}")
            if os.path.exists(alt_path):
                template_path = alt_path
            else:
                all_t = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".xml")]
                if all_t:
                    template_path = os.path.join(TEMPLATES_DIR, all_t[0])
                else:
                    template_path = os.path.join(BASE_DIR, "sample_template.xml")

        groom_bytes = await groom_photo.read() if groom_photo else None
        bride_bytes = await bride_photo.read() if bride_photo else None

        # Determine whether to return .amzip package or pure .xml
        use_amzip = (export_format == "amzip") or (export_format == "auto" and bool(groom_bytes or bride_bytes))

        if use_amzip:
            package_bytes, filename, mime_type = generate_wedding_package(
                template_path,
                parsed_data,
                font_mode=font_mode,
                groom_photo_bytes=groom_bytes,
                bride_photo_bytes=bride_bytes
            )
            encoded_filename = urllib.parse.quote(filename)
            return Response(
                content=package_bytes,
                media_type=mime_type,
                headers={
                    "Content-Disposition": f'attachment; filename="wedding_project.amzip"; filename*=UTF-8\'\'{encoded_filename}'
                }
            )
        else:
            generated_xml = generate_wedding_xml(template_path, parsed_data, font_mode=font_mode)
            
            groom = parsed_data.get("groom_name", "Groom").strip().replace(" ", "_")
            bride = parsed_data.get("bride_name", "Bride").strip().replace(" ", "_")
            card_side = parsed_data.get("card_side", "groom").strip().lower()
            if card_side == "bride":
                filename = f"{bride}.xml" if bride else "Vivah_Bride.xml"
            else:
                filename = f"{groom}.xml" if groom else "Vivah_Groom.xml"
            encoded_filename = urllib.parse.quote(filename)

            return Response(
                content=generated_xml.encode("utf-8"),
                media_type="application/xml; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="wedding_project.xml"; filename*=UTF-8\'\'{encoded_filename}'
                }
            )
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})



# Mount static files
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 VivahEdit AI Server Starting...")
    print(f"📱 Mobile URL: {MOBILE_URL}")
    print(f"💻 Local PC URL: http://localhost:{PORT}")
    print("="*50 + "\n")
    print("📲 Mobile par kholne ke liye ye QR code scan karein:\n")
    qr = qrcode.QRCode()
    qr.add_data(MOBILE_URL)
    try:
        qr.print_ascii(invert=True)
    except Exception:
        pass
    print("\n" + "="*50 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
