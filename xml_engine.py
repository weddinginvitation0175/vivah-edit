import xml.etree.ElementTree as ET
import os
import json
import re
import io
import hashlib
import zipfile
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageOps

# Comprehensive AMS character / transliteration dictionary
AMS_MAP = {
    # Names
    'राम': 'rama',
    'नेहा': 'naeha',
    'सिंह': 'isanha',
    'वर्मा': 'vamaa_',
    'साहू': 'saahU',
    'देवांगन': 'daevaa/gana',
    'यादव': 'yaadava',
    'पटेल': 'pataela',
    'कश्यप': 'kSayapa',
    'चन्द्रकार': 'ca/dXkaara',
    'चंद्राकर': 'ca/dXkaara',
    'संदीप': 'sa/dIpa',
    'पूजा': 'pUjaa',
    'राहुल': 'raahula',
    'प्रिया': 'paXiryaa',
    'अमित': 'Aaimata',
    'सुनीता': 'saunaItaa',
    'मोहन': 'maaoHana',
    'सरिता': 'sairtaa',
    'मनोहर': 'manaaHahr',
    'कमला': 'kmlaa',
    'रमेश': 'rmaaeSa',
    'गीता': 'gaItaa',
    'लखन': 'lKna',
    'लता': 'ltaa',
    'रितेश': 'irtaeSa',
    'बिमलेश्वरी': 'ibamlaeSvarI',
    'विमलेश्वरी': 'ivamlaeSvarI',
    'लोकेश': 'laaekaeSa',
    'यामिनी': 'yaaimanaI',
    'दीपक': 'dIpka',
    'दुर्गेश': 'dugae_Sa',
    'सूरज': 'sUraja',
    'विकास': 'ivakaasa',
    'कविता': 'kivataa',
    'मनीषा': 'manaIYaa',
    'प्रियंका': 'paXirya/kaa',
    'सीमा': 'saImaa',
    'ज्योति': 'jyaaoita',
    'भूपेंद्र': 'BUpae/dX',
    'योगेश': 'yaaaegaeSa',
    'महेश': 'maHaeSa',
    'दिनेश': 'idnaeSa',
    'राकेश': 'raakaeSa',
    'अंजली': 'A/jalaI',
    'पूनम': 'pUnama',
    'आरती': 'AarataI',
    'लक्ष्मी': 'lkSmI',
    'दुर्गा': 'durgaa',
    'संतोष': 'sa/taaoYa',
    'राजेश': 'raajaeSa',
    'प्रकाश': 'paXkaaSa',
    'जितेंद्र': 'jitae/dX',
    'नीलेश': 'naIlaeSa',
    'हेमंत': 'haema/ta',
    'पंकज': 'pa/kja',
    'सोनम': 'saaonama',
    
    # Common ceremony and invitation words
    'परिवार': 'pairvaar',
    'बिहाव नेवता': 'ibahava naevataa',
    'शुभ विवाह': 'SuBa ivavaah',
    'स्नेहिल निमंत्रण': 'sneaihla inama/PaNa',
    'की ओर से': 'ik Aaer sae',
    'आयुष्मान': 'AayauVmaana',
    'आयुष्मती': 'AayauVmataI',
    'चि.': 'ica.',
    'सौ.कां.': 'saaE.ka.',
    'मांगलिक कार्यक्रम': 'maa/gailak kaya_kXma',
    'हल्दी, मंडप': 'hldI, ma/Dpa',
    'हल्दी मंडप': 'hldI, ma/Dpa',
    'हरिद्रालेपन': 'hirdXalaepna',
    'मातृका पूजन': 'maatRkaa pUjana',
    'तेल, मायन': 'taela, maayana',
    'तेल मायन': 'taela, maayana',
    'चूलमाटी': 'cUlamaatI',
    'घृतढारी': 'GRtaQaair',
    'संगीत संध्या': 'sa/gaIta sa/DXyaa',
    'महिला संगीत': 'maihlaa sa/gaIta',
    'मंडप': 'ma/Dpa',
    'मंडप छादन': 'ma/Dpa Caadana',
    'मंडपाच्छादन': 'ma/DpaaCcaadana',
    'बारात प्रस्थान': 'baarata paXsTaana',
    'बारात आगमन': 'baarata Aagamana',
    'बारात स्वागत': 'baarata svaagata',
    'बारात परघनी': 'baarata parGanI',
    'पाणिग्रहण': 'paaNaIgXRhNa',
    'पाणिग्रहण संस्कार': 'paaNaIgXRhNa sa/skaara',
    'हस्त मिलाप': 'hsta imalaapa',
    'प्रतिभोज': 'paXitaBaaoja',
    'प्रीतिभोज': 'paXIitaBaaoja',
    'आशीर्वाद समारोह': 'AaiSaIvaa_da samaaraoh',
    'विवाह स्थल': 'ivavaah sTala',
    'विनीत': 'ivanaIta',
    'दर्शनाभिलाषी': 'dSa_naaiBalaaYaI',
    'आप सभी आमंत्रित हैं': 'Aapa saBaI Aama/i~ata hO',
    'सपरिवार सादर आमंत्रित': 'sapairvaar saadra Aama/i~ata',
    'सपरिवार सादर आमंत्रित हैं': 'sapairvaar saadra Aama/i~ata hO',
}

def devanagari_to_ams(text: str) -> str:
    """Convert common Devanagari words to AMS font format if in dictionary,
    otherwise fallback to cleaned string."""
    cleaned = text.strip()
    if cleaned in AMS_MAP:
        return AMS_MAP[cleaned]
    
    for k, v in AMS_MAP.items():
        if k in cleaned:
            cleaned = cleaned.replace(k, v)
    return cleaned


def adjust_functions_for_4_slots(data: dict) -> list:
    """Wrapper for backward compatibility."""
    return adjust_functions(data, target_slots=4)


def adjust_functions(data: dict, target_slots: int = 4) -> list:
    """
    Intelligently adjusts functions into the template's required slot count (e.g. 4 or 5):
    - If 5 slots: Supports 5 distinct wedding functions without merging.
    - If 4 slots: Merges 5 functions or pads fewer functions cleanly.
    """
    events = []
    
    # Check if raw array was passed from AI or UI
    if "raw_events" in data and isinstance(data["raw_events"], list) and len(data["raw_events"]) > 0:
        for ev in data["raw_events"]:
            if isinstance(ev, dict) and (ev.get("title") or ev.get("name")):
                events.append({
                    "title": ev.get("title") or ev.get("name") or "",
                    "date": ev.get("date") or "",
                    "day": ev.get("day") or "",
                    "time": ev.get("time") or ""
                })

    # Otherwise collect from event1..event5 inputs
    if len(events) == 0:
        for i in range(1, 6):
            t = data.get(f"event{i}_title", "").strip()
            d = data.get(f"event{i}_date", "").strip()
            dy = data.get(f"event{i}_day", "").strip()
            tm = data.get(f"event{i}_time", "").strip()
            if t or d:
                events.append({"title": t, "date": d, "day": dy, "time": tm})

    # Default fallback if nothing found
    if len(events) == 0:
        events = [
            {"title": "हल्दी, मंडप", "date": "10.07.2026", "day": "मंगलवार", "time": ""},
            {"title": "तेल, मायन", "date": "11.07.2026", "day": "बुधवार", "time": ""},
            {"title": "मंडप", "date": "10.07.2026", "day": "मंगलवार", "time": ""},
            {"title": "बारात प्रस्थान", "date": "11.07.2026", "day": "बुधवार", "time": ""},
            {"title": "आशीर्वाद समारोह", "date": "12.07.2026", "day": "गुरुवार", "time": ""}
        ]

    # CASE: 5 target slots (e.g. 5-ceremony templates)
    if target_slots == 5:
        if len(events) >= 5:
            return events[:5]
        
        # If we have fewer than 5 events, smartly split days with multiple rituals to fill 5 slots naturally
        needed = 5 - len(events)
        slots = []
        splits_done = 0

        for ev in events:
            raw_t = ev.get("title", "")
            sub_rituals = [r.strip() for r in re.split(r"[,،/|]\s*|\s+(?:एवं|व|तथा)\s+", raw_t) if r.strip()]
            if len(sub_rituals) >= 2 and splits_done < needed:
                r1 = sub_rituals[0]
                r2 = " व ".join(sub_rituals[1:])
                slots.append({
                    "title": r1,
                    "date": ev.get("date", ""),
                    "day": ev.get("day", ""),
                    "time": ev.get("time", "")
                })
                slots.append({
                    "title": r2,
                    "date": ev.get("date", ""),
                    "day": ev.get("day", ""),
                    "time": ev.get("time", "")
                })
                splits_done += 1
            else:
                slots.append(ev)

        while len(slots) < 5:
            slots.append({
                "title": "स्नेहिल निमंत्रण",
                "date": "सपरिवार सादर आमंत्रित हैं",
                "day": "|| शुभ विवाह ||",
                "time": ""
            })
        return slots[:5]

    # CASE: 4 target slots
    # Sub-case: 5 (or more) events -> Adjust into 4 slots
    if len(events) >= 5:
        slot1 = {
            "title": f"{events[0]['title']} व {events[1]['title']}",
            "date": f"{events[0]['date']} व {events[1]['date']}".strip(" व "),
            "day": f"{events[0]['day']} व {events[1]['day']}".strip(" व "),
            "time": events[0].get("time") or events[1].get("time") or ""
        }
        slot2 = events[2]
        slot3 = events[3]
        slot4 = events[4]
        return [slot1, slot2, slot3, slot4]

    # Sub-case: Exactly 4 events
    if len(events) == 4:
        return events[:4]

    # Sub-case: Fewer than 4 events (e.g. 1, 2, or 3 events) - Smart multi-ritual unpack
    needed = 4 - len(events)
    slots = []
    splits_done = 0

    for ev in events:
        raw_t = ev.get("title", "")
        sub_rituals = [r.strip() for r in re.split(r"[,،/|]\s*|\s+(?:एवं|व|तथा)\s+", raw_t) if r.strip()]
        if len(sub_rituals) >= 2 and splits_done < needed:
            r1 = sub_rituals[0]
            r2 = " व ".join(sub_rituals[1:])
            slots.append({
                "title": r1,
                "date": ev.get("date", ""),
                "day": ev.get("day", ""),
                "time": ev.get("time", "")
            })
            slots.append({
                "title": r2,
                "date": ev.get("date", ""),
                "day": ev.get("day", ""),
                "time": ev.get("time", "")
            })
            splits_done += 1
        else:
            slots.append(ev)

    while len(slots) < 4:
        slots.append({
            "title": "स्नेहिल निमंत्रण",
            "date": "सपरिवार सादर आमंत्रित हैं",
            "day": "|| शुभ विवाह ||",
            "time": ""
        })

    return slots[:4]


def clean_relation_prefix(name_str: str, prefixes: list) -> str:
    """Strips duplicate relation prefixes so standard honorifics can be cleanly formatted."""
    s = (name_str or "").strip()
    for p in prefixes:
        s = re.sub(rf"^{p}\s*[-–:]?\s*", "", s, flags=re.IGNORECASE).strip()
    return s


def format_cg_district(district: str) -> str:
    """Ensures Chhattisgarh districts have mandatory '(छः गः)' short tag."""
    if not district:
        return ""
    d = district.strip()
    if any(tag in d for tag in ["(छः गः)", "(छ.ग.)", "(छ. ग.)", "(छ०ग०)", "(छःगः)"]):
        return d
    d = re.sub(r'[\s,\-]+(छत्तीसगढ़|छ\.ग\.|छत्तीशगढ़)$', '', d).strip()
    return f"{d} (छः गः)"


def format_slot_date(slot: dict) -> str:
    dt = slot.get('date', '').strip()
    if not dt or dt == "सपरिवार सादर आमंत्रित हैं":
        return dt or "सपरिवार सादर आमंत्रित हैं"
    return f"दिनांक - {dt}" if "दिनांक" not in dt else dt


def format_slot_day(slot: dict) -> str:
    """Never includes time. Only format Day."""
    if slot.get('title') == "आप सभी आमंत्रित हैं":
        return "|| स्नेहिल निमंत्रण ||"
    dy = slot.get('day', '').strip()
    if dy:
        return f"दिन - {dy} " if "दिन" not in dy and "||" not in dy else f"{dy} "
    return ""


def get_details_font_size(text: str) -> str:
    """Scales details font size dynamically based on number of lines."""
    lines = [l for l in text.strip().split("\n") if l.strip()]
    num = len(lines)
    if num <= 3:
        return "18.000000"
    elif num <= 4:
        return "15.000000"
    elif num <= 5:
        return "13.500000"
    elif num <= 6:
        return "12.000000"
    else:
        return "10.500000"


MAPS_DIR = os.path.join(os.path.dirname(__file__), "templates", "maps")
os.makedirs(MAPS_DIR, exist_ok=True)


def build_template_map(template_path: str) -> dict:
    """
    Intelligently analyzes any Alight Motion XML template and detects semantic layer roles.
    Works automatically for ANY editor's custom XML template.
    """
    tree = ET.parse(template_path)
    root = tree.getroot()
    elements = []
    for i, t in enumerate(root.iter("text")):
        tid = t.get("id", "")
        font = t.get("font", "")
        label = t.get("label", "") or t.get("name", "")
        st = int(t.get("startTime", "0"))
        c = t.find("content")
        val = c.text if c is not None and c.text else ""

        loc = t.find(".//location")
        x_val, y_val = 0.0, 0.0
        if loc is not None:
            v_str = loc.attrib.get("value", "")
            parts = [p.strip() for p in v_str.split(",") if p.strip()]
            if len(parts) >= 1:
                try: x_val = float(parts[0])
                except ValueError: pass
            if len(parts) >= 2:
                try: y_val = float(parts[1])
                except ValueError: pass

        elements.append({
            "index": i,
            "id": tid,
            "font": font,
            "label": label,
            "startTime": st,
            "text": val,
            "x": x_val,
            "y": y_val
        })

    layers = {}

    # 1. Sang / Weds divider and adjacent Big Names (Visual Screen Coordinate Aware)
    sang_idx = None
    for i, e in enumerate(elements):
        txt_clean = e["text"].strip()
        if txt_clean in ["संग", "sa/ga", "Weds", "weds", "&", "संग "]:
            sang_idx = i
            layers["sang"] = e["id"]
            break

    if sang_idx is not None and sang_idx > 0 and (sang_idx + 1 < len(elements)):
        e_before = elements[sang_idx - 1]
        e_after = elements[sang_idx + 1]
        y_before = e_before.get("y", 0.0)
        y_after = e_after.get("y", 0.0)

        # In 2D screen space: smaller Y is top of screen
        if abs(y_before - y_after) > 20:
            if y_before < y_after:
                top_e, bot_e = e_before, e_after
            else:
                top_e, bot_e = e_after, e_before
        else:
            # Horizontal arrangement: smaller X is left on screen
            if e_before.get("x", 0.0) <= e_after.get("x", 0.0):
                top_e, bot_e = e_before, e_after
            else:
                top_e, bot_e = e_after, e_before

        layers["big_name_top"] = top_e["id"]
        layers["big_name_bottom"] = bot_e["id"]
        layers["big_name_1"] = layers["big_name_top"]
        layers["big_name_2"] = layers["big_name_bottom"]
    elif sang_idx is not None and sang_idx > 0:
        layers["big_name_top"] = elements[sang_idx - 1]["id"]
        layers["big_name_1"] = layers["big_name_top"]

    # 2. Semantic role classification
    for e in elements:
        txt = e["text"]
        tid = e["id"]
        i = e["index"]

        # Grandparents / Parents / Village Details
        if any(k in txt for k in ["सुपौत्री", "पौत्री", "नातिन"]):
            layers["bride_details"] = tid
        elif any(k in txt for k in ["सुपौत्र", "पौत्र", "नाती"]):
            layers["groom_details"] = tid
        elif "सुपुत्री" in txt and "bride_details" not in layers:
            layers["bride_details"] = tid
        elif "सुपुत्र" in txt and "groom_details" not in layers:
            layers["groom_details"] = tid

        # Slide Names with Honorific prefixes
        if any(txt.strip().startswith(p) for p in ["सौ.कां.", "सौ. कां.", "saaE.ka.", "saaE."]) or "सौ.कां." in txt or "saaE.ka." in txt:
            layers["bride_slide_name"] = tid
        elif any(txt.strip().startswith(p) for p in ["चि.", "चि .", "ica.", "ica"]) or "चि." in txt or " ica." in txt:
            layers["groom_slide_name"] = tid

        # Honorifics
        if "AayauVmataI" in txt or "आयुष्मती" in txt:
            layers["bride_honorific"] = tid
        elif "AayauVmaana" in txt or "आयुष्मान" in txt:
            layers["groom_honorific"] = tid

        # Pariwar / Family Clan
        if "pairvaar" in txt.lower() or "परिवार" in txt:
            if len(txt.strip().split()) <= 2:
                layers["pariwar"] = tid
        elif i == 3 and elements[0]["text"] and "नेवता" in elements[0]["text"]:
            layers["pariwar"] = tid

        # Vinit (Inviter)
        if any(k in txt for k in ["(पापा)", "(माँ)", "(पिताजी)", "(भाई)", "(चाचा)"]):
            layers["vinit_details"] = tid
        elif txt.strip() in ["विनीत", "ivanaIta", "दर्शनाभिलाषी"]:
            layers["vinit_header"] = tid

        # Main Date (single date line like 15-11-2026)
        if re.search(r"^\s*\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\s*$", txt):
            layers["main_date"] = tid

        # Branding / Watermark
        if re.search(r"\d{10}", txt) or "Amar" in txt or "7067392032" in txt:
            layers["branding"] = tid

        # Venue (Vivah Sthal)
        if "ivavaah sTala" in txt or "विवाह स्थल" in txt:
            layers["venue_header"] = tid
        elif "ग्राम -" in txt or "ग्राम /" in txt:
            if i not in [elements[j]["index"] for j in range(len(elements)) if elements[j]["id"] in [layers.get("groom_details"), layers.get("bride_details"), layers.get("vinit_details")]]:
                layers["venue_gram"] = tid
        elif "जिला -" in txt:
            if i not in [elements[j]["index"] for j in range(len(elements)) if elements[j]["id"] in [layers.get("groom_details"), layers.get("bride_details"), layers.get("vinit_details")]]:
                layers["venue_district"] = tid

    # 3. Detect Ceremony Slots (Titles + Dates + Days)
    ceremonies = []
    for i, e in enumerate(elements):
        txt = e["text"]
        if re.search(r"\d{1,2}[-./]\d{1,2}[-./]\d{2,4}", txt):
            if len(txt.strip()) <= 12 and not ("दिनांक" in txt or "दिन" in txt):
                continue
            # Pattern A: Combined Date & Day in one layer (e.g. Blue Yellow style)
            if "\n" in txt and ("दिनांक" in txt or "दिन" in txt):
                title_elem = elements[i - 1] if i > 0 else None
                ceremonies.append({
                    "type": "combined_date_day",
                    "title_id": title_elem["id"] if title_elem else None,
                    "date_day_id": e["id"]
                })
            # Pattern B: Separate Date & Day layers (e.g. Green Pink style)
            elif "दिनांक" in txt:
                day_elem = elements[i - 1] if (i > 0 and "दिन" in elements[i - 1]["text"]) else None
                title_elem = elements[i + 1] if (i + 1 < len(elements) and "maa/gailak" not in elements[i + 1]["text"]) else None
                ceremonies.append({
                    "type": "separate",
                    "title_id": title_elem["id"] if title_elem else None,
                    "date_id": e["id"],
                    "day_id": day_elem["id"] if day_elem else None
                })

    # 4. Detect Timeline-Ordered Person Slides (Slide 1 = earlier in video, Slide 2 = later in video)
    person_layers = []
    for e in elements:
        txt = e["text"]
        if any(k in txt for k in ["सुपौत्र", "सुपुत्र", "सुपौत्री", "सुपुत्री", "चि.", "चि .", "सौ.कां.", "सौ. कां.", "AayauVmaana", "AayauVmataI", "ica.", "saaE."]):
            person_layers.append(e)

    groups = {}
    for e in person_layers:
        st = e.get("startTime", 0)
        matched = False
        for g_st in groups:
            if abs(g_st - st) < 1500:
                groups[g_st].append(e)
                matched = True
                break
        if not matched:
            groups[st] = [e]

    sorted_times = sorted(groups.keys())
    person_slides = []
    for st in sorted_times:
        slide_info = {"startTime": st}
        for e in groups[st]:
            txt = e["text"]
            tid = e["id"]
            if "AayauV" in txt or "आयुष्म" in txt:
                slide_info["honorific_id"] = tid
            elif "सुप" in txt or "ग्राम" in txt:
                slide_info["details_id"] = tid
            elif any(p in txt for p in ["चि.", "चि .", "सौ.कां.", "सौ. कां.", "ica.", "saaE."]):
                slide_info["name_id"] = tid
        person_slides.append(slide_info)

    return {"layers": layers, "ceremonies": ceremonies, "person_slides": person_slides}


def get_or_create_template_map(template_path: str) -> dict:
    """Returns cached template map from templates/maps/ or creates and saves a new one."""
    base_name = os.path.splitext(os.path.basename(template_path))[0]
    map_file = os.path.join(MAPS_DIR, f"{base_name}.json")
    if os.path.exists(map_file):
        try:
            with open(map_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    tmap = build_template_map(template_path)
    try:
        with open(map_file, "w", encoding="utf-8") as f:
            json.dump(tmap, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return tmap


def generate_wedding_xml(
    template_path: str,
    data: dict,
    font_mode: str = "hybrid",  # 'hybrid' (AMS + Normal Mixture - preserves video layout), 'unicode', or 'ams'
    groom_photo_info: Optional[Dict[str, Any]] = None,
    bride_photo_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    Incorporate wedding data into Alight Motion XML template with high accuracy.
    Handles Groom vs Bride side precedence, grandparents, editable ceremony titles,
    time/muhurat, and font fixing.
    """
    tree = ET.parse(template_path)
    root = tree.getroot()

    # Universal Template Map: Automatically detects semantic layers of ANY custom XML
    tmap = get_or_create_template_map(template_path)
    layers = tmap.get("layers", {})
    ceremonies = tmap.get("ceremonies", [])
    person_slides = tmap.get("person_slides", [])
    slide1_info = person_slides[0] if len(person_slides) > 0 else {}
    slide2_info = person_slides[1] if len(person_slides) > 1 else {}

    card_side = data.get("card_side", "groom").strip().lower()
    if card_side not in ["groom", "bride"]:
        card_side = "groom"

    groom_name = data.get("groom_name", "राम").strip()
    bride_name = data.get("bride_name", "नेहा").strip()

    # Project Title: reflects primary party first (Groom or Bride name)
    if card_side == "bride":
        root.set("title", f"{bride_name}" if bride_name else "Vivah")
    else:
        root.set("title", f"{groom_name}" if groom_name else "Vivah")

    # 1. Pariwar / Family Clan
    pariwar_raw = data.get("pariwar_name", "साहू परिवार").strip()
    if pariwar_raw and not pariwar_raw.endswith("परिवार"):
        pariwar_display = f"{pariwar_raw} परिवार"
    else:
        pariwar_display = pariwar_raw or "साहू परिवार"

    # 2. Groom Details formatting (Grandparents + Parents + Location)
    groom_father = data.get("groom_father", "श्री मनोहर लाल").strip()
    groom_mother = data.get("groom_mother", "श्रीमती कमला बाई").strip()
    groom_grandparents = data.get("groom_grandparents", "").strip()
    groom_village = data.get("groom_village", "डोंगरगढ़").strip()
    groom_dist = format_cg_district(data.get("groom_district", "राजनांदगांव"))

    groom_lines = []
    if groom_grandparents:
        clean_ggp = clean_relation_prefix(groom_grandparents, ["सुपौत्र", "पौत्र", "नाती"])
        groom_lines.append(f"सुपौत्र - {clean_ggp}")
    if groom_father:
        clean_gf = clean_relation_prefix(groom_father, ["सुपुत्र", "आत्मज", "पुत्र"])
        p_str = f"सुपुत्र - {clean_gf}"
        if groom_mother:
            clean_gm = clean_relation_prefix(groom_mother, ["सुपुत्र", "आत्मज", "पुत्र"])
            p_str += f"\n{clean_gm}"
        groom_lines.append(p_str)
    elif groom_mother:
        clean_gm = clean_relation_prefix(groom_mother, ["सुपुत्र", "आत्मज", "पुत्र"])
        groom_lines.append(f"सुपुत्र - {clean_gm}")

    has_separate_address = bool(
        layers.get("slide1_address") or layers.get("groom_address") or slide1_info.get("address_id")
    )

    g_loc = []
    if groom_village:
        g_loc.append(f"ग्राम - {groom_village}")
    if groom_dist:
        g_loc.append(f"जिला - {groom_dist}")

    groom_address_text = "\n".join(g_loc) if g_loc else ""
    if not has_separate_address and g_loc:
        groom_lines.append(", ".join(g_loc))

    groom_details_text = "\n".join(groom_lines) + "\n"

    # 3. Bride Details formatting (Grandparents + Parents + Location)
    bride_father = data.get("bride_father", "श्री रमेश कुमार").strip()
    bride_mother = data.get("bride_mother", "श्रीमती गीता बाई").strip()
    bride_grandparents = data.get("bride_grandparents", "").strip()
    bride_village = data.get("bride_village", "खैरागढ़").strip()
    bride_dist = format_cg_district(data.get("bride_district", "राजनांदगांव"))

    bride_lines = []
    if bride_grandparents:
        clean_bgp = clean_relation_prefix(bride_grandparents, ["सुपौत्री", "पौत्री", "नातिन"])
        bride_lines.append(f"सुपौत्री - {clean_bgp}")
    if bride_father:
        clean_bf = clean_relation_prefix(bride_father, ["सुपुत्री", "आत्मजा", "पुत्री"])
        p_str = f"सुपुत्री - {clean_bf}"
        if bride_mother:
            clean_bm = clean_relation_prefix(bride_mother, ["सुपुत्री", "आत्मजा", "पुत्री"])
            p_str += f"\n{clean_bm}"
        bride_lines.append(p_str)
    elif bride_mother:
        clean_bm = clean_relation_prefix(bride_mother, ["सुपुत्री", "आत्मजा", "पुत्री"])
        bride_lines.append(f"सुपुत्री - {clean_bm}")

    b_loc = []
    if bride_village:
        b_loc.append(f"ग्राम - {bride_village}")
    if bride_dist:
        b_loc.append(f"जिला - {bride_dist}")

    bride_address_text = "\n".join(b_loc) if b_loc else ""
    if not has_separate_address and b_loc:
        bride_lines.append(", ".join(b_loc))

    bride_details_text = "\n".join(bride_lines) + "\n"

    # 4. Smart Events Adjustment (with editable titles, dates, days & times)
    target_ceremony_count = len(ceremonies) if len(ceremonies) > 0 else 4
    slots = adjust_functions(data, target_slots=target_ceremony_count)
    slot1, slot2, slot3, slot4 = slots[0], slots[1], slots[2], slots[3]

    # 5. Venue (If card does not specify a venue/hall, fallback to host's native village & district)
    venue_gram = data.get("venue_gram", "").strip()
    venue_dist_raw = data.get("venue_district", "").strip()
    if not venue_gram:
        if card_side == "bride":
            venue_gram = bride_village
            venue_dist = bride_dist
        else:
            venue_gram = groom_village
            venue_dist = groom_dist
    else:
        venue_dist = format_cg_district(venue_dist_raw) if venue_dist_raw else (bride_dist if card_side == "bride" else groom_dist)

    # 6. Vinit & Branding (Permanent: Amar Edit 7067392032)
    vinit_names = data.get("vinit_names", "श्री लखन (पापा)\nश्रीमती लता बाई (माँ)").strip()
    studio_name = "Amar Edit"
    studio_phone = "7067392032"

    unicode_devanagari_font = "googlefonts?name=Mukta&amp;weight=700"

    # Count lines in Vinit for Auto-Font Scaling
    vinit_lines = [line.strip() for line in vinit_names.split("\n") if line.strip()]
    num_vinit_lines = len(vinit_lines)
    if num_vinit_lines <= 2:
        vinit_font_size = "18.000000"
    elif num_vinit_lines <= 4:
        vinit_font_size = "15.000000"
    elif num_vinit_lines <= 6:
        vinit_font_size = "13.000000"
    elif num_vinit_lines <= 8:
        vinit_font_size = "11.500000"
    else:
        vinit_font_size = "10.000000"

    # Calculate details font sizes
    groom_details_size = get_details_font_size(groom_details_text)
    bride_details_size = get_details_font_size(bride_details_text)

    # Determine primary and secondary based on card_side
    # If groom side: Primary is Groom, Secondary is Bride
    # If bride side: Primary is Bride, Secondary is Groom
    if card_side == "bride":
        first_big_name = bride_name
        second_big_name = groom_name

        slide1_title_unicode = "आयुष्मती"
        slide1_title_ams = "AayauVmataI"
        slide1_name_unicode = f" सौ.कां. {bride_name}"
        slide1_name_ams = f" saaE.ka.{devanagari_to_ams(bride_name)}"
        slide1_details_text = bride_details_text
        slide1_details_size = bride_details_size
        slide1_address_text = bride_address_text

        slide2_title_unicode = "आयुष्मान"
        slide2_title_ams = "AayauVmaana"
        slide2_name_unicode = f" चि. {groom_name}"
        slide2_name_ams = f" ica. {devanagari_to_ams(groom_name)}"
        slide2_details_text = groom_details_text
        slide2_details_size = groom_details_size
        slide2_address_text = groom_address_text
    else:
        first_big_name = groom_name
        second_big_name = bride_name

        slide1_title_unicode = "आयुष्मान"
        slide1_title_ams = "AayauVmaana"
        slide1_name_unicode = f" चि. {groom_name}"
        slide1_name_ams = f" ica. {devanagari_to_ams(groom_name)}"
        slide1_details_text = groom_details_text
        slide1_details_size = groom_details_size
        slide1_address_text = groom_address_text

        slide2_title_unicode = "आयुष्मती"
        slide2_title_ams = "AayauVmataI"
        slide2_name_unicode = f" सौ.कां. {bride_name}"
        slide2_name_ams = f" saaE.ka.{devanagari_to_ams(bride_name)}"
        slide2_details_text = bride_details_text
        slide2_details_size = bride_details_size
        slide2_address_text = bride_address_text

    # Iterate over text layers and apply updates using Universal Semantic Template Map
    processed_tids = set()
    vhost_raw = layers.get("vinit_host", [])
    vinit_host_ids = vhost_raw if isinstance(vhost_raw, list) else ([vhost_raw] if vhost_raw else [])

    for text_elem in root.iter("text"):
        tid = text_elem.get("id")
        font = text_elem.get("font", "")
        content_elem = text_elem.find("content")
        if content_elem is None:
            continue

        is_ams = ("AMS" in font) and (font_mode != "unicode")
        use_unicode = (font_mode == "unicode")

        # Header / Intro layers
        # 'बिहाव नेवता' layer
        if tid == "102400131":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " बिहाव नेवता"
            else:
                content_elem.text = " ibahava naevataa"

        # Pariwar layer
        elif tid == layers.get("pariwar") or tid == "102400122":
            processed_tids.add(tid)
            p_val = pariwar_raw.replace("परिवार", "").strip() if layers.get("pariwar_name_only") else pariwar_display
            if layers.get("pariwar_suffix"):
                p_val = f"{p_val}{layers['pariwar_suffix']}"
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = f" {p_val} "
            elif is_ams:
                ams_val = devanagari_to_ams(p_val)
                content_elem.text = f" {ams_val} "
            else:
                content_elem.text = f" {p_val} "

        # 'की ओर से' layer
        elif tid == "102400133":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " की ओर से"
            else:
                content_elem.text = " ik Aaer sae"

        # 'स्नेहिल निमंत्रण' layer
        elif tid == "102400458":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " स्नेहिल निमंत्रण"
            else:
                content_elem.text = " sneaihla inama/PaNa"

        # Big Name Top (Primary Person: Groom if groom card, Bride if bride card)
        elif tid in [layers.get("big_name_top"), layers.get("big_name_1"), "102400149"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = first_big_name
            elif is_ams:
                content_elem.text = devanagari_to_ams(first_big_name)
            else:
                content_elem.text = f" {first_big_name} "
            text_elem.set("label", f"{first_big_name}")

        # 'संग' layer
        elif tid == layers.get("sang") or tid == "102400150":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)

        # Big Name Bottom (Secondary Person: Bride if groom card, Groom if bride card)
        elif tid in [layers.get("big_name_bottom"), layers.get("big_name_2"), "102400154"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = f" {second_big_name}"
            elif is_ams:
                content_elem.text = f" {devanagari_to_ams(second_big_name)}"
            else:
                content_elem.text = f" {second_big_name} "
            text_elem.set("label", f"{second_big_name}")

        # Slide 1 (Earlier in video timeline) -> Honorific, Name, Details
        elif tid in [slide1_info.get("honorific_id"), slide1_info.get("honorific_id_alt"), "102400158"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slide1_title_unicode
            elif is_ams:
                content_elem.text = slide1_title_ams
            else:
                content_elem.text = slide1_title_unicode

        elif tid in [slide1_info.get("name_id"), "102400159"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slide1_name_unicode
            elif is_ams:
                content_elem.text = slide1_name_ams
            else:
                content_elem.text = slide1_name_unicode
            text_elem.set("label", f"{first_big_name}")

        elif tid in [slide1_info.get("details_id"), "102400160"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            text_elem.set("size", slide1_details_size)
            content_elem.text = slide1_details_text

        elif tid in [slide1_info.get("address_id"), layers.get("slide1_address"), layers.get("groom_address")]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            content_elem.text = slide1_address_text

        # Slide 2 (Later in video timeline) -> Honorific, Name, Details
        elif tid in [slide2_info.get("honorific_id"), slide2_info.get("honorific_id_alt"), "102400172"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slide2_title_unicode
            elif is_ams:
                content_elem.text = slide2_title_ams
            else:
                content_elem.text = slide2_title_unicode

        elif tid in [slide2_info.get("name_id"), "102400173"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slide2_name_unicode
            elif is_ams:
                content_elem.text = slide2_name_ams
            else:
                content_elem.text = slide2_name_unicode
            text_elem.set("label", f"{second_big_name}")

        elif tid in [slide2_info.get("details_id"), "102400174"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            text_elem.set("size", slide2_details_size)
            content_elem.text = slide2_details_text

        elif tid in [slide2_info.get("address_id"), layers.get("slide2_address"), layers.get("bride_address")]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            content_elem.text = slide2_address_text

        # Venue Header
        elif tid == layers.get("venue_header") or tid == "102400217":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " विवाह स्थल"
            elif is_ams:
                content_elem.text = " ivavaah sTala"
            else:
                content_elem.text = " विवाह स्थल"

        # Venue (Vivah Sthal) Details
        elif tid == layers.get("venue_gram") or tid == "102400216":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            if venue_gram:
                clean_vg = re.sub(r"^ग्राम\s*[-–:]?\s*", "", venue_gram).strip()
                content_elem.text = f"ग्राम - {clean_vg} " if ("भवन" not in clean_vg and "होटल" not in clean_vg and "लॉन" not in clean_vg) else f"स्थल - {venue_gram} "
            else:
                content_elem.text = "विवाह स्थल "
        elif tid == layers.get("venue_district") or tid == "102400215":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            if venue_dist:
                clean_vd = re.sub(r"^जिला\s*[-–:]?\s*", "", venue_dist).strip()
                content_elem.text = f"जिला - {clean_vd} "
            else:
                content_elem.text = "शुभ विवाह "

        # Vinit Header
        elif tid == layers.get("vinit_header") or tid == "102400226":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " विनीत"
            elif is_ams:
                content_elem.text = " ivanaIta"
            else:
                content_elem.text = " विनीत"

        # Vinit Host (Chief inviter / family head above vinit list)
        elif tid in vinit_host_ids:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            v_lines = [line.strip() for line in vinit_names.split("\n") if line.strip()]
            content_elem.text = v_lines[0] if v_lines else vinit_names

        # Vinit Names
        elif tid == layers.get("vinit_details") or tid == "102400225":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
            text_elem.set("size", vinit_font_size)
            v_lines = [line.strip() for line in vinit_names.split("\n") if line.strip()]
            if layers.get("vinit_host") and len(v_lines) > 1:
                details_vinit = "\n".join(v_lines[1:])
            elif layers.get("vinit_host") and len(v_lines) == 1:
                details_vinit = "समस्त परिवार"
            else:
                details_vinit = vinit_names

            # If template has no separate venue layers, include venue lines here
            if not layers.get("venue_gram") and (venue_gram or venue_dist):
                v_loc = []
                if venue_gram:
                    clean_vg = re.sub(r"^ग्राम\s*[-–:]?\s*", "", venue_gram).strip()
                    v_loc.append(f"ग्राम - {clean_vg}")
                if venue_dist:
                    clean_vd = re.sub(r"^जिला\s*[-–:]?\s*", "", venue_dist).strip()
                    v_loc.append(f"जिला - {clean_vd}")
                content_elem.text = f"{details_vinit}\n" + ", \n".join(v_loc)
            else:
                content_elem.text = details_vinit

        # Main Wedding Date layer
        elif tid == layers.get("main_date"):
            processed_tids.add(tid)
            wedding_date = slot4.get("date") or slot1.get("date") or "15-11-2026"
            clean_date = wedding_date.replace("दिनांक - ", "").replace("दिनांक : ", "").strip()
            if re.match(r'^\d{4}-\d{2}-\d{2}$', clean_date):
                parts = clean_date.split("-")
                clean_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
            content_elem.text = clean_date

        # Branding
        elif tid == layers.get("branding") or tid in ["102400234", "102400235"]:
            processed_tids.add(tid)
            if tid == "102400234":
                content_elem.text = f"{studio_phone} "
            elif tid == "102400235":
                content_elem.text = studio_name
            else:
                content_elem.text = f"{studio_name} {studio_phone} "

        # 'मांगलिक कार्यक्रम' recurring subheaders
        elif tid in ["102400183", "102400194", "102400202", "102400210", "102400218"]:
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = " मांगलिक कार्यक्रम"
            else:
                content_elem.text = " maa/gailak kaya_kXma"

        # Slot 1 Title (Green Pink Hardcoded ID)
        elif tid == "102400182":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slot1["title"]
            else:
                content_elem.text = devanagari_to_ams(slot1["title"])
        elif tid == "102400187":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_date(slot1)
        elif tid == "102400188":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_day(slot1)

        # Slot 2 (Green Pink Hardcoded IDs)
        elif tid == "102400193":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = f" {slot2['title']}"
            else:
                content_elem.text = f" {devanagari_to_ams(slot2['title'])}"
        elif tid == "102400192":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_date(slot2)
        elif tid == "102400191":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_day(slot2)

        # Slot 3 (Green Pink Hardcoded IDs)
        elif tid == "102400201":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slot3["title"]
            else:
                content_elem.text = devanagari_to_ams(slot3["title"])
        elif tid == "102400200":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_date(slot3)
        elif tid == "102400199":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_day(slot3)

        # Slot 4 (Green Pink Hardcoded IDs)
        elif tid == "102400209":
            processed_tids.add(tid)
            if use_unicode:
                text_elem.set("font", unicode_devanagari_font)
                content_elem.text = slot4["title"]
            else:
                content_elem.text = devanagari_to_ams(slot4["title"])
        elif tid == "102400208":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_date(slot4)
        elif tid == "102400207":
            processed_tids.add(tid)
            if use_unicode: text_elem.set("font", unicode_devanagari_font)
            content_elem.text = format_slot_day(slot4)

    # Dynamic Ceremony slots updating (for any custom templates with detected ceremony slots)
    for idx, slot_info in enumerate(ceremonies):
        if idx >= len(slots):
            break
        slot = slots[idx]
        title_id = slot_info.get("title_id")
        if title_id and title_id not in processed_tids:
            el = root.find(f".//text[@id='{title_id}']")
            if el is not None and el.find("content") is not None:
                f = el.get("font", "")
                if font_mode == "unicode":
                    el.set("font", unicode_devanagari_font)
                    el.find("content").text = f" {slot['title']} "
                elif "AMS" in f:
                    el.find("content").text = devanagari_to_ams(slot["title"])
                else:
                    el.find("content").text = f" {slot['title']} "

        if slot_info.get("type") == "combined_date_day":
            dd_id = slot_info.get("date_day_id")
            if dd_id and dd_id not in processed_tids:
                el = root.find(f".//text[@id='{dd_id}']")
                if el is not None and el.find("content") is not None:
                    d_str = format_slot_date(slot)
                    day_str = format_slot_day(slot)
                    d_clean = d_str if d_str.startswith("दिनांक") else f"दिनांक - {d_str}"
                    day_clean = day_str if day_str.startswith("दिन") else f"दिन - {day_str}"
                    if font_mode == "unicode":
                        el.set("font", unicode_devanagari_font)
                    el.find("content").text = f"{d_clean}\n{day_clean} "
        elif slot_info.get("type") == "combined_inline":
            dd_id = slot_info.get("date_day_id")
            if dd_id and dd_id not in processed_tids:
                el = root.find(f".//text[@id='{dd_id}']")
                if el is not None and el.find("content") is not None:
                    d_val = slot.get("date", "").strip()
                    for p in ["दिनांक - ", "दिनांक : ", "दिनांक-", "दिनांक"]:
                        d_val = d_val.replace(p, "").strip()
                    day_val = slot.get("day", "").strip()
                    for p in ["दिन - ", "दिन : ", "दिन-", "दिन"]:
                        day_val = day_val.replace(p, "").strip()
                    if font_mode == "unicode":
                        el.set("font", unicode_devanagari_font)
                    if slot_info.get("day_first"):
                        prefix_day = f"दिन- {day_val}" if (day_val and not day_val.startswith("दिन")) else day_val
                        el.find("content").text = f"{prefix_day} {d_val}".strip() if prefix_day else d_val
                    else:
                        el.find("content").text = f"{d_val}, {day_val}"
        elif slot_info.get("type") == "separate":
            d_id = slot_info.get("date_id")
            if d_id and d_id not in processed_tids:
                el = root.find(f".//text[@id='{d_id}']")
                if el is not None and el.find("content") is not None:
                    if font_mode == "unicode":
                        el.set("font", unicode_devanagari_font)
                    if slot_info.get("raw"):
                        d_val = slot.get("date", "").strip()
                        for p in ["दिनांक - ", "दिनांक : ", "दिनांक-", "दिनांक"]:
                            d_val = d_val.replace(p, "").strip()
                        el.find("content").text = d_val
                    else:
                        el.find("content").text = format_slot_date(slot)
            day_id = slot_info.get("day_id")
            if day_id and day_id not in processed_tids:
                el = root.find(f".//text[@id='{day_id}']")
                if el is not None and el.find("content") is not None:
                    if font_mode == "unicode":
                        el.set("font", unicode_devanagari_font)
                    if slot_info.get("raw"):
                        day_val = slot.get("day", "").strip()
                        for p in ["दिन - ", "दिन : ", "दिन-", "दिन"]:
                            day_val = day_val.replace(p, "").strip()
                        el.find("content").text = day_val
                    else:
                        el.find("content").text = format_slot_day(slot)

        time_id = slot_info.get("time_id")
        if time_id and time_id not in processed_tids:
            el = root.find(f".//text[@id='{time_id}']")
            if el is not None and el.find("content") is not None:
                time_val = slot.get("time", "").strip()
                if time_val:
                    if font_mode == "unicode":
                        el.set("font", unicode_devanagari_font)
                    el.find("content").text = time_val if (time_val.startswith("at ") or "बजे" in time_val) else f"at {time_val}"

    # Photo layer handling: Match card_side
    first_label = "📸 BRIDE PHOTO (दुल्हन)" if card_side == "bride" else "📸 GROOM PHOTO (दूल्हा)"
    second_label = "📸 GROOM PHOTO (दूल्हा)" if card_side == "bride" else "📸 BRIDE PHOTO (दुल्हन)"

    slide1_photo = bride_photo_info if card_side == "bride" else groom_photo_info
    slide2_photo = groom_photo_info if card_side == "bride" else bride_photo_info

    # Explicit shape IDs from template map
    s1_shape = layers.get("slide1_photo_shape")
    s2_shape = layers.get("slide2_photo_shape")
    s3_shape = layers.get("slide3_photo_shape")

    for embed in root.iter("embedScene"):
        eid = embed.get("id")
        if eid == "102400169":
            embed.set("label", first_label)
        elif eid == "102400177":
            embed.set("label", second_label)

    for shape in root.iter("shape"):
        sid = shape.get("id")
        if sid in [s1_shape, "102400319"]:
            if slide1_photo:
                shape.set("fillType", "media")
                shape.set("fillImage", f"am:{slide1_photo['filename']}")
                shape.set("label", f"{first_big_name}.jpeg")
            else:
                shape.set("label", f"{first_label} - Color & Fill")
        elif sid in [s2_shape, "102400318"]:
            if slide2_photo:
                shape.set("fillType", "media")
                shape.set("fillImage", f"am:{slide2_photo['filename']}")
                shape.set("label", f"{second_big_name}.jpeg")
            else:
                shape.set("label", f"{second_label} - Color & Fill")
        elif sid == s3_shape:
            couple_ph = slide1_photo or slide2_photo
            if couple_ph:
                shape.set("fillType", "media")
                shape.set("fillImage", f"am:{couple_ph['filename']}")
                shape.set("label", "Couple.jpeg")
            else:
                shape.set("label", "📸 COUPLE PHOTO - Color & Fill")

    # Generic fallback: Also inspect any embedScene with label="Photo" (only if explicit shapes not mapped)
    if not (s1_shape or s2_shape):
        photo_scenes = [es for es in root.iter("embedScene") if (es.get("label") or "").strip().lower() == "photo"]
        if len(photo_scenes) >= 1 and slide1_photo:
            for sh in photo_scenes[0].iter("shape"):
                if sh.get("fillType") == "media" or "fillImage" in sh.attrib:
                    sh.set("fillType", "media")
                    sh.set("fillImage", f"am:{slide1_photo['filename']}")
                    sh.set("label", f"{first_big_name}.jpeg")
                    break
        if len(photo_scenes) >= 2 and slide2_photo:
            for sh in photo_scenes[1].iter("shape"):
                if sh.get("fillType") == "media" or "fillImage" in sh.attrib:
                    sh.set("fillType", "media")
                    sh.set("fillImage", f"am:{slide2_photo['filename']}")
                    sh.set("label", f"{second_big_name}.jpeg")
                    break

    # Sanitize layer labels so old template sample names do not linger in timeline
    for elem in root.iter():
        lbl = elem.get("label", "")
        if lbl:
            if "राहुल" in lbl: elem.set("label", lbl.replace("राहुल", groom_name))
            if "अंजली" in lbl: elem.set("label", lbl.replace("अंजली", bride_name))

    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
    header = "<?xml version='1.0' encoding='UTF-8' ?>\n"
    if not xml_str.startswith("<?xml"):
        xml_str = header + xml_str
    return xml_str


def process_photo_bytes(photo_bytes: bytes, max_dim: int = 1920) -> Tuple[bytes, str]:
    """
    Takes raw image bytes, auto-rotates via EXIF, resizes if larger than max_dim,
    converts to RGB JPEG, and returns (jpeg_bytes, sha1_filename).
    """
    img = Image.open(io.BytesIO(photo_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=90, optimize=True)
    jpeg_bytes = out_buf.getvalue()

    sha1 = hashlib.sha1(jpeg_bytes).hexdigest().upper()
    filename = f"{sha1}.jpeg"
    return jpeg_bytes, filename


def generate_wedding_package(
    template_path: str,
    data: dict,
    font_mode: str = "hybrid",
    groom_photo_bytes: Optional[bytes] = None,
    bride_photo_bytes: Optional[bytes] = None
) -> Tuple[bytes, str, str]:
    """
    Generates an After Motion Z .amzip package containing project.xml and photos.
    Returns: (package_bytes, filename, mime_type)
    """
    groom_info = None
    if groom_photo_bytes:
        try:
            g_bytes, g_name = process_photo_bytes(groom_photo_bytes)
            groom_info = {"bytes": g_bytes, "filename": g_name}
        except Exception as e:
            print(f"Warning: Failed to process groom photo: {e}")

    bride_info = None
    if bride_photo_bytes:
        try:
            b_bytes, b_name = process_photo_bytes(bride_photo_bytes)
            bride_info = {"bytes": b_bytes, "filename": b_name}
        except Exception as e:
            print(f"Warning: Failed to process bride photo: {e}")

    generated_xml = generate_wedding_xml(
        template_path,
        data,
        font_mode=font_mode,
        groom_photo_info=groom_info,
        bride_photo_info=bride_info
    )

    card_side = data.get("card_side", "groom").strip().lower()
    groom_name = data.get("groom_name", "Groom").strip().replace(" ", "_")
    bride_name = data.get("bride_name", "Bride").strip().replace(" ", "_")
    primary_name = bride_name if card_side == "bride" else groom_name
    primary_name = primary_name or "Vivah"

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. Root project.xml
        z.writestr("project.xml", generated_xml.encode("utf-8"))

        # 2. Add media files to both root and media/ for universal compatibility
        added_files = set()
        for info in [groom_info, bride_info]:
            if info and info["filename"] not in added_files:
                z.writestr(info["filename"], info["bytes"])
                z.writestr(f"media/{info['filename']}", info["bytes"])
                added_files.add(info["filename"])

    package_bytes = zip_buf.getvalue()
    filename = f"{primary_name}.amzip"
    return package_bytes, filename, "application/zip"

print("Upgraded XML Engine with Card-Side precedence, dynamic ceremonies & grandparents ready.")
