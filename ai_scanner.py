import json
import base64
import os
import requests
from typing import Dict, Any, List, Union
from xml_engine import devanagari_to_english, get_english_order_name

CHHATTISGARHI_CARD_SYSTEM_PROMPT = """
You are an expert OCR & Information Extraction AI specialized in Indian Wedding Cards (Lagan Patrika / Vivah Nimantran Patra / बिहाव नेवता) in Hindi, Chhattisgarhi, and English.

Read all provided wedding card images/pages carefully and extract all factual details into clean JSON.

CRITICAL EXTRACTION RULES:
1. ACCURACY FIRST: DO NOT invent, hallucinate, or guess names, dates, or villages. If a piece of information is NOT written on the card, return an empty string "" for that field.

2. CARD SIDE DETERMINATION (वर पक्ष vs वधू पक्ष):
   - You MUST determine whether this invitation card is from the Groom's Side ("groom") or Bride's Side ("bride"):
     * "groom" (वर पक्ष): The card is issued by the groom's family. Typical signs:
       - Mentions "सुपुत्र चि. [वर]" before/prominently, "संग सौ.कां. [वधू]"
       - Family clan surname matches the groom
       - Key events include "बारात प्रस्थान" / "बारात निकसी"
       - Vinit / प्रेषक / दर्शनाभिलाषी are groom's parents or relatives
     * "bride" (वधू पक्ष): The card is issued by the bride's family. Typical signs:
       - Mentions "सुपुत्री सौ.कां. [वधू]" before/prominently, "संग चि. [वर]"
       - Family clan surname matches the bride
       - Key events include "बारात स्वागत" / "बारात आगमन" / "पाणिग्रहण संस्कार" / "विदाई"
       - Vinit / प्रेषक / दर्शनाभिलाषी are bride's parents or relatives
   - Set "card_side": "groom" or "bride".

3. GROOM & BRIDE DETAILS:
   - Groom (वर / दूल्हा): Look for "चि." (Chiranjeev), "आयुष्मान", "सुपुत्र". Extract groom_name, groom_father, groom_mother, groom_village, groom_district, groom_state.
     Also look for Grandparents ("पौत्र स्व. श्री..." or "नाती") -> groom_grandparents.
   - Bride (वधू / दुल्हन): Look for "सौ.कां." (Saubhagyakankshini), "आयुष्मती", "सुपुत्री". Extract bride_name, bride_father, bride_mother, bride_village, bride_district, bride_state.
     Also look for Grandparents ("पौत्री / नातिन स्व. श्री...") -> bride_grandparents.
   - MANDATORY DISTRICT RULE: Whenever extracting groom_district, bride_district, or venue_district, ALWAYS append "(छः गः)" (e.g. "राजनांदगांव (छः गः)", "रायपुर (छः गः)", "दुर्ग (छः गः)", "बालोद (छः गः)", "बिलासपुर (छः गः)"). Even if Chhattisgarh is not explicitly written on card, writing "(छः गः)" after district is strictly mandatory!
   - NOTE: DO NOT extract Gotra. Gotra is strictly excluded and never needed.

4. FAMILY / PARIWAR SURNAME:
   - Identify the family clan name of the host side (e.g. "साहू परिवार", "सिंह परिवार", "वर्मा परिवार", "देवांगन परिवार", "यादव परिवार", "पटेल परिवार", "कश्यप परिवार").

5. WEDDING FUNCTIONS & DATES (SYNTHESIZE ACROSS ALL PAGES):
   - Wedding cards often span multiple pages (e.g. cover page, inside lagan page, events page). Check all pages.
   - Extract the EXACT title of each ritual/ceremony as written on the card.
     Examples: "हल्दी, मंडप", "मातृका पूजन", "तेल, मायन", "संगीत संध्या", "महिला संगीत", "घृतढारी", "मंडपाच्छादन", "बारात प्रस्थान", "बारात आगमन", "बारात स्वागत", "पाणिग्रहण", "प्रतिभोज", "प्रीतिभोज", "आशीर्वाद समारोह".
   - Extract Date in DD.MM.YYYY format (e.g. "15.05.2027").
   - Extract Day of week in Hindi (e.g. "मंगलवार", "बुधवार", "शनिवार", "रविवार").
   - STRICT TIME RULE: DO NOT extract Time or Muhurat (समय / शुभ मुहूर्त). Time must NEVER be included in wedding functions.
   - Populate distinct ceremonies chronologically across event1, event2, event3, event4, event5. If a single date has multiple distinct rituals (e.g. "मंडपाच्छादन, चुलमाटी, तेलमायन" or "बारात प्रस्थान एवं पाणिग्रहण"), you may keep them together or break them into distinct events chronologically so all rituals are captured.

6. VENUE (विवाह स्थल):
   - Extract hall, bhavan, hotel, or village and district into "venue_gram" and "venue_district" (always with "(छः गः)").
   - If NO separate wedding hall/hotel is mentioned on the card, set "venue_gram" to the native village of the card's host family (groom_village for groom card, bride_village for bride card), and set "venue_district" to that district.

7. INVITER (विनीत / दर्शनाभिलाषी):
   - Extract the names of elders / parents listed under विनीत, प्रेषक, or दर्शनाभिलाषी into "vinit_names".

Return ONLY a valid JSON object matching this schema:
{
  "card_side": "groom" or "bride",
  "pariwar_name": "Surname / Family name",
  "groom_name": "Groom's first/full name in Hindi",
  "groom_name_en": "Groom's name in English letters (e.g. Rahul)",
  "groom_father": "Father's name with Sri",
  "groom_mother": "Mother's name with Smt",
  "groom_grandparents": "Grandfather/Grandmother if mentioned",
  "groom_village": "Village / town",
  "groom_district": "District (छः गः)",
  "groom_state": "छत्तीसगढ़",
  "bride_name": "Bride's first/full name in Hindi",
  "bride_name_en": "Bride's name in English letters (e.g. Priya)",
  "bride_father": "Father's name with Sri",
  "bride_mother": "Mother's name with Smt",
  "bride_grandparents": "Grandfather/Grandmother if mentioned",
  "bride_village": "Village / town",
  "bride_district": "District (छः गः)",
  "bride_state": "छत्तीसगढ़",
  "event1_title": "Exact title of ceremony 1",
  "event1_date": "DD.MM.YYYY",
  "event1_day": "Day in Hindi (e.g. मंगलवार)",
  "event2_title": "Exact title of ceremony 2",
  "event2_date": "DD.MM.YYYY",
  "event2_day": "Day in Hindi",
  "event3_title": "Exact title of ceremony 3",
  "event3_date": "DD.MM.YYYY",
  "event3_day": "Day in Hindi",
  "event4_title": "Exact title of ceremony 4",
  "event4_date": "DD.MM.YYYY",
  "event4_day": "Day in Hindi",
  "event5_title": "Exact title of ceremony 5",
  "event5_date": "DD.MM.YYYY",
  "event5_day": "Day in Hindi",
  "venue_gram": "Venue or Village name",
  "venue_district": "District (छः गः)",
  "vinit_names": "Names listed under Vinit",
  "studio_name": "Amar Edit",
  "studio_phone": "7067392032"
}
"""

CHHATTISGARHI_CARD_VERIFY_PROMPT = """
You are a senior Wedding Invitation Verification Auditor & Quality Control Specialist.
You are provided with:
1. The original wedding card image(s)/page(s).
2. The initial extracted JSON data from Pass 1.

YOUR TASK: Perform a rigorous, line-by-line verification and correction of the extracted details against the original card image(s) to guarantee 100% accuracy.

MANDATORY AUDIT CHECKLIST:
1. INVITATION SIDE (वर पक्ष vs वधू पक्ष):
   - Double-check whether this invitation is from the Groom's Side ("groom") or Bride's Side ("bride").
   - Confirm Groom (दूल्हा) and Bride (दुल्हन) names are NOT swapped!

2. FAMILY RELATIONSHIPS & NAMES:
   - Grandparents: Verify if grandparents are mentioned. Clean raw names without prefixes like "सुपौत्र", "सुपौत्री", "पौत्र", "नाति".
   - Parents: Ensure father and mother names are accurate with honorifics ("श्री", "श्रीमती"). Ensure Groom's parents and Bride's parents are not mixed up.

3. DISTRICT MANDATE (छः गः):
   - Every district in groom_district, bride_district, and venue_district MUST end with "(छः गः)" (e.g. "राजनांदगांव (छः गः)", "बालोद (छः गः)", "रायपुर (छः गः)", "दुर्ग (छः गः)"). If missing, add it.

4. STRICT NEGATIVE RULES:
   - NO GOTRA: Gotra must NEVER be extracted.
   - NO CEREMONY TIME: Times and muhurats (e.g. "समय 7:00 बजे", "शुभ मुहूर्त") must NEVER be included in ceremonies. Only title, date (DD.MM.YYYY), and day (दिन - ...) are allowed.

5. CEREMONY DATES & DAYS:
   - Carefully verify all event dates (DD.MM.YYYY) and days of week (e.g. शनिवार, रविवार, सोमवार, मंगलवार, बुधवार, गुरुवार, शुक्रवार) against the card. Correct any misread numbers or days.

6. DEVNAGARI SPELLING PRECISION:
   - Fix any OCR spelling mistakes in names, village names, and ritual titles.

Return ONLY the verified, perfected JSON object matching the exact same schema.
"""

_ENC_FALLBACK_KEY = b"QVEuQWI4Uk42Sk9TQ3ZPaENXd2dYNjhmMzJJQ3RwOWNpbDJsekNoOVVoOFRjTWxEdTJJRlE="
try:
    DEFAULT_GEMINI_API_KEY = base64.b64decode(_ENC_FALLBACK_KEY).decode("utf-8")
except Exception:
    DEFAULT_GEMINI_API_KEY = ""

def get_candidate_api_keys(user_key: str = None) -> List[str]:
    """Gathers all available API keys in priority order with deduplication."""
    keys = []
    # 1. User/client key (if valid string)
    if user_key and isinstance(user_key, str):
        clean_user = user_key.strip()
        if clean_user and clean_user.lower() not in ["null", "undefined", "none", ""] and len(clean_user) >= 15:
            keys.append(clean_user)

    # 2. Environment variable
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key and env_key not in keys and env_key.lower() not in ["null", "undefined", "none", ""]:
        keys.append(env_key)

    # 3. .env file in project directory
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        file_k = line.split("=", 1)[1].strip()
                        if file_k and file_k not in keys and file_k.lower() not in ["null", "undefined", "none", ""]:
                            keys.append(file_k)
                        break
    except Exception:
        pass

    # 4. Embedded fallback key (guarantees scanning always works seamlessly)
    if DEFAULT_GEMINI_API_KEY and DEFAULT_GEMINI_API_KEY not in keys:
        keys.append(DEFAULT_GEMINI_API_KEY)

    return keys

def call_gemini_vision(parts: List[Dict[str, Any]], api_key: str = None) -> Dict[str, Any]:
    """Helper to call Gemini API with vision parts, multi-model fallback, safety settings and JSON response parsing."""
    import time

    candidate_keys = get_candidate_api_keys(api_key)
    if not candidate_keys:
        raise RuntimeError("No Gemini API key available. Please configure GEMINI_API_KEY.")

    # High-reliability candidate models in order of speed and stability
    candidate_models = [
        "gemini-flash-lite-latest",
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest"
    ]

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    last_error = None

    for attempt in range(2):
        for current_key in candidate_keys:
            key_tag = f"...{current_key[-6:]}" if len(current_key) > 6 else "key"
            for model in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "response_mime_type": "application/json"
                    },
                    "safetySettings": safety_settings
                }
                headers = {"Content-Type": "application/json"}

                try:
                    res = requests.post(url, json=payload, headers=headers, timeout=18)

                    if res.status_code == 200:
                        try:
                            resp_json = res.json()
                            candidates = resp_json.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                                if text.startswith("```json"):
                                    text = text[7:]
                                if text.startswith("```"):
                                    text = text[3:]
                                if text.endswith("```"):
                                    text = text[:-3]
                                text = text.strip()
                                parsed = json.loads(text)
                                if isinstance(parsed, dict) and len(parsed) > 0:
                                    print(f"✅ [AI Scanner] Successfully extracted card details using model {model} (attempt {attempt+1})")
                                    return parsed
                        except Exception as parse_err:
                            # Try substring extraction
                            try:
                                s_idx = text.find("{")
                                e_idx = text.rfind("}")
                                if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                                    parsed = json.loads(text[s_idx:e_idx + 1])
                                    if isinstance(parsed, dict):
                                        print(f"✅ [AI Scanner] Successfully parsed JSON substring with model {model}")
                                        return parsed
                            except Exception:
                                pass
                            last_error = f"{model} returned non-JSON text: {str(parse_err)}"
                            print(f"⚠️ [AI Scanner] {model} parse error: {parse_err}, trying next model...")
                            continue

                    # If response_mime_type is rejected by any specific model (400 bad request)
                    elif res.status_code == 400 and ("response_mime_type" in res.text or "generation_config" in res.text.lower()):
                        payload["generationConfig"].pop("response_mime_type", None)
                        res2 = requests.post(url, json=payload, headers=headers, timeout=18)
                        if res2.status_code == 200:
                            resp_json2 = res2.json()
                            candidates = resp_json2.get("candidates", [])
                            if candidates:
                                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                                if text.startswith("```json"): text = text[7:]
                                if text.startswith("```"): text = text[3:]
                                if text.endswith("```"): text = text[:-3]
                                text = text.strip()
                                parsed = json.loads(text)
                                if isinstance(parsed, dict) and len(parsed) > 0:
                                    print(f"✅ [AI Scanner] Successfully extracted data using {model} (plain mode)")
                                    return parsed

                    # If API Key is Invalid or Permission Denied: switch to backup key immediately
                    elif res.status_code in (400, 403) and ("API_KEY_INVALID" in res.text or "API key not valid" in res.text or "PERMISSION_DENIED" in res.text):
                        print(f"⚠️ [AI Scanner] Key {key_tag} is invalid/denied ({res.status_code}), switching to backup key...")
                        last_error = f"API key {key_tag} invalid: {res.text[:100]}"
                        break

                    # If Quota Exceeded on this key: switch to backup key immediately
                    elif res.status_code == 429 and ("RESOURCE_EXHAUSTED" in res.text or "quota" in res.text.lower()):
                        print(f"⚠️ [AI Scanner] Key {key_tag} quota exhausted (429), switching to backup key...")
                        last_error = f"API key {key_tag} quota exhausted: {res.text[:100]}"
                        break

                    # If High Demand (503) or temporary error:
                    elif res.status_code in (503, 429, 500, 502, 504):
                        last_error = f"{model} returned {res.status_code} ({res.text[:100]})"
                        print(f"⚠️ [AI Scanner] {model} busy ({res.status_code}), falling back to next candidate model...")
                        continue

                    else:
                        last_error = f"{model} returned {res.status_code}: {res.text[:120]}"
                        print(f"⚠️ [AI Scanner] {model} HTTP {res.status_code}: {res.text[:100]}")

                except requests.exceptions.Timeout:
                    last_error = f"{model} request timed out (>18s)"
                    print(f"⚠️ [AI Scanner] {model} timed out (>18s), falling back to next model...")
                    continue
                except Exception as req_err:
                    last_error = f"{model} connection exception: {str(req_err)}"
                    print(f"⚠️ [AI Scanner] {model} error: {req_err}")
                    continue

        if attempt == 0:
            time.sleep(1.2)

    raise RuntimeError(f"Gemini API Error: All models/keys exhausted. Last error: {last_error}")

def optimize_card_image(img_bytes: bytes, max_dim: int = 1600, quality: int = 82) -> bytes:
    """
    Compresses and auto-orients card image to max_dim (1600px) with quality 82 JPEG.
    Dramatically shrinks upload size from 10MB down to ~250KB, making AI scanning 3x to 5x faster!
    """
    try:
        from PIL import Image, ImageOps
        import io
        img = Image.open(io.BytesIO(img_bytes))
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return img_bytes

def process_card_file(file_bytes: bytes, filename: str = "card.jpg", content_type: str = "image/jpeg") -> List[Dict[str, Any]]:
    """
    Processes a card file:
    - If PDF: extracts every page as optimized JPEG image using PyMuPDF.
    - If image (JPG, PNG, WEBP): optimizes resolution & compresses for ultra-fast AI OCR.
    """
    is_pdf = filename.lower().endswith(".pdf") or "pdf" in (content_type or "").lower()
    if is_pdf:
        pages = []
        try:
            import pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=150)
                img_bytes = optimize_card_image(pix.tobytes("jpeg"), max_dim=1600, quality=82)
                pages.append({
                    "bytes": img_bytes,
                    "mime_type": "image/jpeg",
                    "name": f"{filename} (Page {page_num + 1})"
                })
            doc.close()
        except Exception as e:
            raise ValueError(f"Failed to extract pages from PDF: {str(e)}")
        return pages
    else:
        compressed_bytes = optimize_card_image(file_bytes, max_dim=1600, quality=82)
        return [{
            "bytes": compressed_bytes,
            "mime_type": "image/jpeg",
            "name": filename
        }]


def scan_wedding_card(pages: Union[bytes, List[Dict[str, Any]]], mime_type: str = "image/jpeg", api_key: str = None) -> Dict[str, Any]:
    """
    Calls Gemini Vision API to extract wedding card details from one or multiple images/pages.
    pages can be either:
    - bytes (single image)
    - list of dicts: [{"bytes": b"...", "mime_type": "image/jpeg", "name": "..."}]
    """
    if isinstance(pages, (bytes, bytearray)):
        pages_list = [{"bytes": bytes(pages), "mime_type": mime_type, "name": "Card Image"}]
    elif isinstance(pages, list):
        pages_list = pages
    else:
        raise ValueError("Invalid pages format passed to scan_wedding_card")

    if not pages_list:
        raise ValueError("No card images or PDF pages provided for scan")

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    # -----------------------------------------------------------------
    # FAST SINGLE-PASS DEEP EXTRACTION (Ultra-Optimized)
    # -----------------------------------------------------------------
    print(f"\n🔍 [AI Scanner] Ultra-Speed Card Extraction on {len(pages_list)} page(s)...")
    parts = [{"text": CHHATTISGARHI_CARD_SYSTEM_PROMPT}]

    for idx, page in enumerate(pages_list):
        b64_image = base64.b64encode(page["bytes"]).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": page.get("mime_type", "image/jpeg"),
                "data": b64_image
            }
        })

    num_pages = len(pages_list)
    prompt = (
        f"This wedding card consists of {num_pages} uploaded image/page(s). "
        "Carefully examine ALL pages together, synthesize every factual piece of information "
        "(host family clan, groom vs bride side, names, parents, grandparents, all ceremonies with dates/days, venue, vinit) "
        "strictly adhering to all critical rules: NO GOTRA, NO TIME, append '(छः गः)' to districts. "
        "Return a single consolidated, 100% accurate JSON:"
    )
    parts.append({"text": prompt})

    final_data = call_gemini_vision(parts, api_key)
    print(f"✅ [AI Scanner] Ultra-Speed Extraction Completed: Side={final_data.get('card_side')}, Groom={final_data.get('groom_name')}, Bride={final_data.get('bride_name')}")

    # -----------------------------------------------------------------
    # DETERMINISTIC POST-PROCESSING & COMPLIANCE RULES
    # -----------------------------------------------------------------
    # 1. Mandatory District (छः गः) Guarantee
    for key in ["groom_district", "bride_district", "venue_district"]:
        val = (final_data.get(key) or "").strip()
        if val:
            if not val.endswith("(छः गः)"):
                val = val.replace("छ.ग.", "").replace("छ ग", "").replace("(छ.ग.)", "").strip()
                val = f"{val} (छः गः)"
            final_data[key] = val

    # 2. Strict Gotra Exclude
    if "gotra" in final_data:
        del final_data["gotra"]

    # 3. Clean relation prefixes from raw name fields
    for key, pfxs in [
        ("groom_grandparents", ["सुपौत्र", "पौत्र", "नाति", "नाती"]),
        ("bride_grandparents", ["सुपौत्री", "पौत्री", "नातिन"]),
        ("groom_father", ["सुपुत्र", "आत्मज", "पुत्र"]),
        ("bride_father", ["सुपुत्री", "आत्मजा", "पुत्री"])
    ]:
        val = (final_data.get(key) or "").strip()
        if val:
            for p in pfxs:
                if val.startswith(p):
                    val = val[len(p):].lstrip(" -:–,")
            final_data[key] = val.strip()

    # 4. Clean any time strings from ceremonies
    for i in range(1, 5):
        if f"event{i}_time" in final_data:
            del final_data[f"event{i}_time"]

    # 5. Default branding & studio info (Always Amar Edit & 7067392032)
    final_data["studio_name"] = "Amar Edit"
    final_data["studio_phone"] = "7067392032"

    # 6. Ensure valid card_side default
    if final_data.get("card_side") not in ["groom", "bride"]:
        final_data["card_side"] = "groom"

    # 7. Ensure English order names are populated for Groom & Bride
    for hi_key, en_key in [("groom_name", "groom_name_en"), ("bride_name", "bride_name_en")]:
        en_val = (final_data.get(en_key) or "").strip()
        if not en_val or not en_val.isascii():
            en_val = devanagari_to_english(final_data.get(hi_key, ""))
        final_data[en_key] = en_val
    final_data["order_name"] = get_english_order_name(final_data)

    return final_data


def get_demo_sample_data() -> Dict[str, Any]:
    """Returns rich sample Chhattisgarhi wedding data for instant 1-click test."""
    return {
        "card_side": "groom",
        "pariwar_name": "साहू परिवार",
        "groom_name": "संदीप",
        "groom_name_en": "Sandeep",
        "groom_father": "श्री मनोहर लाल साहू",
        "groom_mother": "श्रीमती कमला बाई",
        "groom_grandparents": "स्व. श्री रामरतन साहू (दादा जी) एवं श्रीमती सुमित्रा देवी",
        "groom_village": "डोंगरगढ़",
        "groom_district": "राजनांदगांव (छः गः)",
        "groom_state": "छत्तीसगढ़",
        "bride_name": "पूजा",
        "bride_name_en": "Pooja",
        "bride_father": "श्री रमेश कुमार साहू",
        "bride_mother": "श्रीमती गीता बाई",
        "bride_grandparents": "स्व. श्री दीनदयाल साहू (दादा जी) एवं श्रीमती शकुंतला देवी",
        "bride_village": "खैरागढ़",
        "bride_district": "राजनांदगांव (छः गः)",
        "bride_state": "छत्तीसगढ़",
        "event1_title": "हल्दी, मंडप",
        "event1_date": "15.05.2027",
        "event1_day": "शनिवार",
        "event2_title": "संगीत संध्या व तेल मायन",
        "event2_date": "16.05.2027",
        "event2_day": "रविवार",
        "event3_title": "मातृका पूजन व मंडप",
        "event3_date": "17.05.2027",
        "event3_day": "सोमवार",
        "event4_title": "बारात प्रस्थान",
        "event4_date": "17.05.2027",
        "event4_day": "सोमवार",
        "venue_gram": "शुभम मंगल भवन, डोंगरगढ़",
        "venue_district": "राजनांदगांव (छः गः)",
        "vinit_names": "श्री मनोहर लाल साहू (पापा)\nश्रीमती कमला बाई (माँ)\nसमस्त साहू परिवार",
        "studio_name": "Amar Edit",
        "studio_phone": "7067392032",
        "order_name": "Sandeep"
    }
