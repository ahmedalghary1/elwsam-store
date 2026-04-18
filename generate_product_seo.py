# -*- coding: utf-8 -*-
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / "products_export.csv"
OUTPUT_CSV = ROOT / "docs" / "seo_products_output.csv"
OUTPUT_JSON = ROOT / "docs" / "seo_products_output.json"


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def clean_text(text: str) -> str:
    text = (text or "").replace("\ufeff", "").replace("\u202a", "").replace("\u202c", "")
    text = text.replace("الابيض", "أبيض").replace("الاسود", "أسود")
    text = text.replace("فيشة ثلاثة", "فيشة ثلاثية")
    text = text.replace("1.5متر", "1.5 متر").replace("3متر", "3 متر").replace("6متر", "6 متر")
    return normalize_spaces(text)


def clean_description(text: str) -> str:
    text = (text or "").replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def extract_model(text: str) -> str:
    match = re.search(r"موديل\s*:?\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_voltage(text: str) -> str:
    match = re.search(r"(\d{2,3}(?:-\d{2,3})?V)", text, re.IGNORECASE)
    return match.group(1).upper() if match else ""


def extract_dimensions(text: str) -> str:
    match = re.search(r"الابعاد\s*:\s*\(([^)]+)\)\s*mm", text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} mm"
    return ""


def extract_weight(text: str) -> str:
    match = re.search(r"وزن المنتج\s*:\s*([0-9]+)\s*جرام", text, re.IGNORECASE)
    return f"{match.group(1)} جرام" if match else ""


def extract_materials(text: str) -> list[str]:
    materials = []
    for pattern in [
        r"الخامة\s*:\s*([^\n]+)",
        r"خامة القاعدة\s*:\s*([^\n]+)",
        r"خامة الوش\s*:\s*([^\n]+)",
        r"خامة السلك\s*:\s*([^\n]+)",
        r"خامة الفيشة\s*:\s*([^\n]+)",
    ]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = normalize_spaces(match.group(1).replace("(", "").replace(")", ""))
            if value and value not in materials:
                materials.append(value)
    return materials


def extract_length_from_text(text: str) -> str:
    for pattern in [
        r"(?:السلك|طول السلك)\s*:\s*\(?([0-9]+(?:\.[0-9]+)?)\)?\s*متر",
        r"الطول\s*:\s*\(?([0-9]+(?:\.[0-9]+)?)\)?\s*متر",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def extract_length_from_name(text: str) -> str:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*متر", text)
    return match.group(1) if match else ""


def extract_color(text: str) -> str:
    if "أبيض" in text:
        return "أبيض"
    if "أسود" in text:
        return "أسود"
    return ""


def extract_single_color_from_description(text: str) -> str:
    white = "أبيض" in text
    black = "أسود" in text
    if white and black:
        return ""
    if white:
        return "أبيض"
    if black:
        return "أسود"
    return ""


def extract_plug_type(text: str) -> str:
    if "فيشة ثنائية" in text:
        return "فيشة ثنائية"
    if "فيشة ثلاثية" in text:
        return "فيشة ثلاثية"
    return ""


def extract_wire_size(text: str) -> str:
    match = re.search(r"([0-9]+)\s*مم", text)
    return f"{match.group(1)} مم" if match else ""


def infer_brand(name: str, model: str) -> str:
    if "الوسام" in name or model.startswith("WS"):
        return "الوسام"
    return "غير مذكور"


def detect_family(name: str) -> str:
    normalized = name.lower()
    if "وصلة كهرباء" in name and "16" in name:
        return "extension_16a"
    if "2c+2a" in normalized:
        return "usb_2c2a"
    if "1c+3a" in normalized:
        return "usb_1c3a"
    if re.search(r"\b6a\b", normalized):
        return "usb_6a"
    if "2eu" in normalized and "2uk" in normalized:
        return "socket_2eu_2uk"
    if "4way" in normalized or "رباعي" in name:
        return "socket_4way"
    if "مودرن" in name:
        return "modern_strip"
    if "3s" in normalized:
        return "socket_3s"
    if "ميني ثلاثي" in name:
        return "mini_triple"
    if "ميني eu+uk" in normalized:
        return "mini_eu_uk"
    if "ميني uk" in normalized:
        return "mini_uk"
    if "usb" in normalized:
        return "usb_4usb"
    if "ثلاثي امان" in name:
        return "triple_safe_adapter"
    if "خماسي" in name:
        return "five_way_adapter"
    if "مشترك ثلاثي" in name:
        return "triple_adapter"
    return "power_strip"


FAMILY_CONFIG = {
    "usb_2c2a": {
        "main_type": "مشترك كهرباء USB Type C وUSB A",
        "keyword_base": "مشترك كهرباء 2C+2A",
        "title_base": "مشترك كهرباء 2C+2A",
        "feature_line": "منفذا Type C ومنفذا USB A في جهاز واحد",
        "benefit_line": "يوفر شحنًا عمليًا لعدة أجهزة من نقطة واحدة",
        "use_cases": "مكتب العمل وطاولة الدراسة وغرفة المعيشة وشحن الهواتف والتابلت والإكسسوارات",
        "related": ["مشترك كهرباء 1C+3A", "مشترك كهرباء 6A USB", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "USB", "Type C", "2C+2A", "شحن متعدد", "الوسام"],
        "slug": "moshtrak-kahraba-2c-2a",
    },
    "usb_1c3a": {
        "main_type": "مشترك كهرباء USB بمنفذ Type C و3 USB A",
        "keyword_base": "مشترك كهرباء 1C+3A",
        "title_base": "مشترك كهرباء 1C+3A",
        "feature_line": "منفذ Type C مع 3 منافذ USB A",
        "benefit_line": "يساعد على شحن أكثر من جهاز يومي بسهولة",
        "use_cases": "المكتب المنزلي وشحن الهاتف والسماعات والساعة الذكية والملحقات اليومية",
        "related": ["مشترك كهرباء 2C+2A", "مشترك كهرباء USB 4 منافذ", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "USB", "Type C", "1C+3A", "شحن مكتبي", "الوسام"],
        "slug": "moshtrak-kahraba-1c-3a",
    },
    "usb_6a": {
        "main_type": "مشترك كهرباء USB بعدد 6 منافذ Type A",
        "keyword_base": "مشترك كهرباء 6A USB",
        "title_base": "مشترك كهرباء 6A USB",
        "feature_line": "6 منافذ USB Type A لشحن الأجهزة اليومية",
        "benefit_line": "يقلل الاعتماد على الشواحن المنفصلة ويوفر ترتيبًا أفضل",
        "use_cases": "مكاتب العمل ومحطات الشحن المنزلية والأماكن التي تحتاج أكثر من منفذ USB",
        "related": ["مشترك كهرباء 2C+2A", "مشترك كهرباء 1C+3A", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "USB", "6A", "منافذ USB", "شحن متعدد", "الوسام"],
        "slug": "moshtrak-kahraba-6a-usb",
    },
    "socket_2eu_2uk": {
        "main_type": "مشترك كهرباء 2EU 2UK متعدد المخارج",
        "keyword_base": "مشترك كهرباء 2EU 2UK",
        "title_base": "مشترك كهرباء 2EU 2UK",
        "feature_line": "مخارج 2EU و2UK لتوصيل أكثر من نوع فيش",
        "benefit_line": "يسهّل تشغيل الأجهزة المختلفة من توصيلة واحدة",
        "use_cases": "المنزل والمكتب والأجهزة التي تعمل بفيش EU أو UK داخل نفس المكان",
        "related": ["مشترك كهرباء رباعي 4way", "مشترك ميني EU+UK", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "2EU 2UK", "EU", "UK", "بريزة متعددة", "الوسام"],
        "slug": "moshtrak-kahraba-2eu-2uk",
    },
    "usb_4usb": {
        "main_type": "مشترك كهرباء USB بأربع منافذ شحن",
        "keyword_base": "مشترك كهرباء USB 4 منافذ",
        "title_base": "مشترك كهرباء USB",
        "feature_line": "4 منافذ USB عملية للشحن اليومي",
        "benefit_line": "يجمع منافذ الشحن في مكان واحد بطريقة مرتبة",
        "use_cases": "المكتب وغرف النوم وطاولة المذاكرة وشحن الهاتف والسماعات والملحقات",
        "related": ["مشترك كهرباء 1C+3A", "مشترك كهرباء 6A USB", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "USB", "4USB", "شحن متعدد", "توصيلة USB", "الوسام"],
        "slug": "moshtrak-kahraba-4usb",
    },
    "socket_4way": {
        "main_type": "مشترك كهرباء رباعي 4way",
        "keyword_base": "مشترك كهرباء رباعي 4way",
        "title_base": "مشترك كهرباء رباعي 4way",
        "feature_line": "4 فتحات توصيل مناسبة للاستخدام اليومي",
        "benefit_line": "يساعدك على تنظيم الأجهزة في مكان واحد بدون ازدحام",
        "use_cases": "وحدة التلفزيون ومكتب الكمبيوتر وغرف المعيشة والأجهزة المنزلية الخفيفة",
        "related": ["مشترك كهرباء 2EU 2UK", "مشترك كهرباء مودرن", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "4way", "مشترك رباعي", "4 فتحات", "توصيلة كهرباء", "الوسام"],
        "slug": "moshtrak-kahraba-4way",
    },
    "modern_strip": {
        "main_type": "مشترك كهرباء مودرن",
        "keyword_base": "مشترك كهرباء مودرن",
        "title_base": "مشترك كهرباء مودرن",
        "feature_line": "تصميم عملي مناسب للاستخدام المنزلي أو المكتبي",
        "benefit_line": "يوفر ترتيبًا أفضل للتوصيلات مع شكل أنيق",
        "use_cases": "المكاتب المنزلية وغرف النوم ووحدة التلفزيون والأركان التي تحتاج توصيلة عملية",
        "related": ["مشترك كهرباء رباعي 4way", "مشترك كهرباء 2EU 2UK", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "مشترك مودرن", "توصيلة كهرباء", "مشترك للمكتب", "مشترك للمنزل", "الوسام"],
        "slug": "moshtrak-kahraba-modern",
    },
    "socket_3s": {
        "main_type": "مشترك كهرباء 3S",
        "keyword_base": "مشترك كهرباء 3S",
        "title_base": "مشترك كهرباء 3S",
        "feature_line": "3 منافذ Socket بتصميم عملي",
        "benefit_line": "يناسب الاستخدام اليومي في المساحات التي تحتاج أكثر من مخرج",
        "use_cases": "المنزل والمكتب وتشغيل الأجهزة الصغيرة ومتطلبات التوصيل اليومية",
        "related": ["مشترك كهرباء رباعي 4way", "مشترك كهرباء مودرن", "قسم المشترك"],
        "entities": ["مشترك كهرباء", "3S", "3 Socket", "توصيلة كهرباء", "مشترك للمنزل", "الوسام"],
        "slug": "moshtrak-kahraba-3s",
    },
    "mini_triple": {
        "main_type": "مشترك كهرباء ميني ثلاثي",
        "keyword_base": "مشترك ميني ثلاثي",
        "title_base": "مشترك ميني ثلاثي",
        "feature_line": "حجم صغير مع 3 مخارج عملية",
        "benefit_line": "مناسب للأماكن الضيقة والاستخدام السريع",
        "use_cases": "طاولة المكتب والرحلات الخفيفة والسرير الجانبي والأماكن ذات المساحة المحدودة",
        "related": ["مشترك ميني EU+UK", "مشترك ميني UK", "قسم المشترك"],
        "entities": ["مشترك ميني", "مشترك ثلاثي", "مشترك صغير", "توصيلة صغيرة", "1.5 متر", "الوسام"],
        "slug": "moshtrak-mini-solasy",
    },
    "mini_uk": {
        "main_type": "مشترك كهرباء ميني UK",
        "keyword_base": "مشترك ميني UK",
        "title_base": "مشترك ميني UK",
        "feature_line": "تصميم صغير مع مخارج UK",
        "benefit_line": "يوفر توصيلًا عمليًا في الأماكن الصغيرة",
        "use_cases": "الاستخدام المكتبي الخفيف وغرف النوم والاحتياجات اليومية ذات المساحة المحدودة",
        "related": ["مشترك ميني EU+UK", "مشترك ميني ثلاثي", "قسم المشترك"],
        "entities": ["مشترك ميني", "UK", "مشترك صغير", "توصيلة صغيرة", "مشترك للمكتب", "الوسام"],
        "slug": "moshtrak-mini-uk",
    },
    "mini_eu_uk": {
        "main_type": "مشترك كهرباء ميني EU+UK",
        "keyword_base": "مشترك ميني EU+UK",
        "title_base": "مشترك ميني EU+UK",
        "feature_line": "تصميم صغير مع مخارج EU وUK",
        "benefit_line": "يخدم أكثر من نوع فيشة بدون أن يشغل مساحة كبيرة",
        "use_cases": "المكاتب الصغيرة وغرف السفر والأماكن التي تجمع بين أجهزة بفيش مختلفة",
        "related": ["مشترك كهرباء 2EU 2UK", "مشترك ميني UK", "قسم المشترك"],
        "entities": ["مشترك ميني", "EU+UK", "UK", "EU", "مشترك صغير", "الوسام"],
        "slug": "moshtrak-mini-eu-uk",
    },
    "extension_16a": {
        "main_type": "وصلة كهرباء 16 أمبير",
        "keyword_base": "وصلة كهرباء 16 أمبير",
        "title_base": "وصلة كهرباء 16A",
        "feature_line": "سلك عملي مع فيشة 16A للاستخدام اليومي",
        "benefit_line": "تناسب من يبحث عن وصلة بطول واضح وتركيب بسيط",
        "use_cases": "الاستخدام المنزلي والأجهزة التي تحتاج وصلة 16 أمبير بطول محدد",
        "related": ["مشترك كهرباء رباعي 4way", "مشترك ثلاثي أمان", "قسم المشترك"],
        "entities": ["وصلة كهرباء", "16A", "فيشة 16 أمبير", "سلك كهرباء", "3 متر", "6 متر"],
        "slug": "waslat-kahraba-16a",
    },
    "triple_safe_adapter": {
        "main_type": "مشترك ثلاثي أمان",
        "keyword_base": "مشترك ثلاثي أمان",
        "title_base": "مشترك ثلاثي أمان",
        "feature_line": "تصميم ثلاثي مع عنصر أمان للاستخدام اليومي",
        "benefit_line": "حل مناسب لمن يريد توزيع التوصيل في حجم صغير",
        "use_cases": "المكتب والمنزل والأماكن التي تحتاج مشتركًا صغيرًا وسهل الاستخدام",
        "related": ["مشترك ثلاثي", "مشترك خماسي", "قسم المشترك"],
        "entities": ["مشترك ثلاثي", "مشترك أمان", "بريزة ثلاثية", "توصيلة صغيرة", "أبيض", "أسود"],
        "slug": "moshtrak-solasy-aman",
    },
    "five_way_adapter": {
        "main_type": "مشترك خماسي",
        "keyword_base": "مشترك خماسي",
        "title_base": "مشترك خماسي",
        "feature_line": "5 مخارج في تصميم صغير وسهل الاستخدام",
        "benefit_line": "يمنحك عدد مخارج أكبر عند الحاجة لتوزيع الكهرباء بشكل مرتب",
        "use_cases": "المكاتب وغرف المعيشة والأماكن التي تحتاج أكثر من منفذ في مساحة محدودة",
        "related": ["مشترك ثلاثي", "مشترك ثلاثي أمان", "قسم المشترك"],
        "entities": ["مشترك خماسي", "5 مخارج", "بريزة متعددة", "توصيلة كهرباء", "4 مم", "5 مم"],
        "slug": "moshtrak-khomasy",
    },
    "triple_adapter": {
        "main_type": "مشترك ثلاثي",
        "keyword_base": "مشترك ثلاثي",
        "title_base": "مشترك ثلاثي",
        "feature_line": "3 مخارج عملية في حجم صغير",
        "benefit_line": "يناسب الاستخدام اليومي عندما تحتاج منفذين أو ثلاثة بشكل سريع",
        "use_cases": "المنزل والمكتب والطاولات الجانبية والمساحات التي تحتاج توصيلة صغيرة",
        "related": ["مشترك ثلاثي أمان", "مشترك خماسي", "قسم المشترك"],
        "entities": ["مشترك ثلاثي", "3 مخارج", "بريزة ثلاثية", "توصيلة كهرباء", "4 مم", "5 مم"],
        "slug": "moshtrak-solasy",
    },
    "power_strip": {
        "main_type": "مشترك كهرباء",
        "keyword_base": "مشترك كهرباء",
        "title_base": "مشترك كهرباء",
        "feature_line": "تصميم عملي لتوزيع الكهرباء",
        "benefit_line": "يخدم الاحتياجات اليومية في المنزل أو المكتب",
        "use_cases": "الاستخدام العام للأجهزة اليومية على المكتب أو داخل المنزل",
        "related": ["قسم المشترك"],
        "entities": ["مشترك كهرباء", "توصيلة كهرباء", "بريزة متعددة", "مشترك للمكتب", "مشترك للمنزل"],
        "slug": "moshtrak-kahraba",
    },
}


def build_context(row: dict) -> dict:
    original_name = row["اسم المنتج"]
    name = clean_text(original_name)
    description = clean_description(row["الوصف"])
    family = detect_family(name)
    config = FAMILY_CONFIG[family]

    length = extract_length_from_name(name) or extract_length_from_text(description)
    color = extract_color(name) or extract_single_color_from_description(description)
    plug_type = extract_plug_type(name)
    wire_size = extract_wire_size(name)
    model = extract_model(description)
    brand = infer_brand(name, model)
    voltage = extract_voltage(description)
    dimensions = extract_dimensions(description)
    weight = extract_weight(description)
    materials = extract_materials(description)

    ctx = {
        "original_name": original_name,
        "name": name,
        "description": description,
        "family": family,
        "price": row["السعر"],
        "category": clean_text(row["القسم"]),
        "current_slug": row["Slug"],
        "length": length,
        "color": color,
        "plug_type": plug_type,
        "wire_size": wire_size,
        "model": model,
        "brand": brand,
        "voltage": voltage,
        "dimensions": dimensions,
        "weight": weight,
        "materials": materials,
        **config,
    }
    return ctx


def variant_bits(ctx: dict) -> list[str]:
    bits = []
    if ctx["plug_type"]:
        bits.append(ctx["plug_type"])
    if ctx["color"]:
        bits.append(ctx["color"])
    if ctx["length"]:
        bits.append(f"{ctx['length']} متر")
    if ctx["wire_size"]:
        bits.append(ctx["wire_size"])
    return bits


def unique(items: list[str], limit: int | None = None) -> list[str]:
    seen = set()
    output = []
    for item in items:
        item = normalize_spaces(item)
        if not item or item in seen:
            continue
        seen.add(item)
        output.append(item)
        if limit and len(output) >= limit:
            break
    return output


def primary_keywords(ctx: dict) -> list[str]:
    base = ctx["keyword_base"]
    items = [
        base,
        ctx["main_type"],
        "مشترك كهرباء" if "وصلة" not in base else "وصلة كهرباء",
        "توصيلة كهرباء" if "وصلة" not in base else "سلك كهرباء 16 أمبير",
        "مشترك فيش" if "وصلة" not in base else "فيشة 16 أمبير",
        "بريزة متعددة" if "وصلة" not in base else "وصلة كهرباء للمنزل",
    ]
    if ctx["length"]:
        items.append(f"{base} {ctx['length']} متر")
    if ctx["color"]:
        items.append(f"{base} {ctx['color']}")
    if ctx["plug_type"]:
        items.append(f"{base} {ctx['plug_type']}")
    if "USB" in ctx["main_type"] or "USB" in base:
        items.extend(["مشترك كهرباء USB", "مشترك شحن USB"])
    if "Type C" in ctx["main_type"] or "2C+2A" in base or "1C+3A" in base:
        items.extend(["مشترك Type C", "مشترك كهرباء تايب سي"])
    if "2EU 2UK" in base or "EU+UK" in base:
        items.extend(["مشترك EU UK", "مشترك 2EU 2UK"])
    if "رباعي" in base:
        items.extend(["مشترك رباعي", "مشترك 4way"])
    if "ثلاثي" in base:
        items.append("مشترك ثلاثي")
    if "خماسي" in base:
        items.append("مشترك خماسي")
    return unique(items, 10)


def long_tail_keywords(ctx: dict) -> list[str]:
    base = ctx["keyword_base"]
    variants = []
    if ctx["plug_type"]:
        variants.append(ctx["plug_type"])
    if ctx["color"]:
        variants.append(ctx["color"])
    if ctx["length"]:
        variants.append(f"{ctx['length']} متر")
    if ctx["wire_size"]:
        variants.append(ctx["wire_size"])
    joined_variant = " ".join(variants).strip()

    items = [
        f"شراء {base}",
        f"سعر {base}",
        f"{base} للمنزل",
        f"{base} للمكتب",
        f"{base} للاستخدام اليومي",
        f"{base} في مصر",
        f"{base} اونلاين",
        f"{base} خامة عملية",
    ]
    if joined_variant:
        items.extend(
            [
                f"{base} {joined_variant}",
                f"شراء {base} {joined_variant}",
                f"سعر {base} {joined_variant}",
            ]
        )
    if ctx["plug_type"]:
        items.extend(
            [
                f"{base} {ctx['plug_type']}",
                f"مشترك فيشة {ctx['plug_type'].replace('فيشة ', '')}",
            ]
        )
    if ctx["color"]:
        items.extend(
            [
                f"{base} {ctx['color']}",
                f"مشترك كهرباء {ctx['color']}",
            ]
        )
    if ctx["length"]:
        items.extend(
            [
                f"{base} {ctx['length']} متر",
                f"مشترك كهرباء {ctx['length']} متر",
            ]
        )
    if "USB" in ctx["main_type"] or "USB" in base:
        items.extend(
            [
                f"{base} USB",
                f"مشترك شحن USB {ctx['length']} متر" if ctx["length"] else "مشترك شحن USB",
                "مشترك USB متعدد",
            ]
        )
    if "Type C" in ctx["main_type"] or "2C+2A" in base or "1C+3A" in base:
        items.extend(
            [
                f"{base} Type C",
                "مشترك كهرباء تايب سي للمكتب",
            ]
        )
    if "2EU 2UK" in base or "EU+UK" in base:
        items.extend(
            [
                f"{base} للأجهزة EU وUK",
                "مشترك متعدد EU UK للمنزل",
            ]
        )
    if ctx["family"] == "extension_16a":
        items.extend(
            [
                "وصلة كهرباء 16 امبير 3 متر",
                "وصلة كهرباء 16 امبير 6 متر",
                "سلك كهرباء 16A أبيض",
            ]
        )
    return unique(items, 16)


def synonym_keywords(ctx: dict) -> list[str]:
    items = [
        "مشترك كهرباء",
        "مشترك فيش",
        "توصيلة كهرباء",
        "وصلة كهرباء",
        "بريزة متعددة",
        ctx["keyword_base"],
    ]
    if "USB" in ctx["main_type"] or "USB" in ctx["keyword_base"]:
        items.extend(["مشترك USB", "مشترك شحن"])
    if "Type C" in ctx["main_type"] or "2C+2A" in ctx["keyword_base"] or "1C+3A" in ctx["keyword_base"]:
        items.append("مشترك Type C")
    if ctx["plug_type"]:
        items.append(ctx["plug_type"])
    if "وصلة" in ctx["main_type"]:
        items.extend(["سلك كهرباء", "فيشة 16 أمبير"])
    return unique(items, 10)


def build_title(ctx: dict) -> str:
    attrs = []
    if ctx["color"]:
        attrs.append(ctx["color"])
    if ctx["length"]:
        attrs.append(f"{ctx['length']} متر")
    if ctx["plug_type"]:
        attrs.append("ثنائية" if "ثنائية" in ctx["plug_type"] else "ثلاثية")
    if ctx["wire_size"]:
        attrs.append(ctx["wire_size"])

    base = ctx["title_base"]
    brand_suffix = f" | {ctx['brand']}" if ctx["brand"] != "غير مذكور" else ""
    candidates = [
        f"{base} {' '.join(attrs)}{brand_suffix}",
        f"{base} {' '.join(attrs)}",
        f"{base} {ctx['color']} {ctx['length']} متر" if ctx["color"] and ctx["length"] else "",
        f"{base} {ctx['length']} متر" if ctx["length"] else "",
        f"{base} {ctx['color']}" if ctx["color"] else "",
        base,
    ]
    candidates = [normalize_spaces(candidate) for candidate in candidates if candidate]
    for candidate in candidates:
        if len(candidate) <= 60:
            return candidate
    return candidates[-1][:60].strip()


def build_meta_description(ctx: dict) -> str:
    intro = f"اشترِ {ctx['keyword_base']}"
    if ctx["plug_type"] or ctx["color"] or ctx["length"]:
        intro += " " + " ".join(variant_bits(ctx))
    feature = ctx["feature_line"]
    material = ""
    if any("Anti Fire" in material_name for material_name in ctx["materials"]):
        material = " بخامة مقاومة للحرارة."
    elif ctx["materials"]:
        material = f" بخامات {ctx['materials'][0]} العملية."
    meta = (
        f"{intro} للاستخدام المنزلي والمكتبي. {feature}.{material} "
        f"{'سلك ' + ctx['length'] + ' متر. ' if ctx['length'] else ''}اطلبه الآن بسهولة."
    )
    meta = normalize_spaces(meta)
    if len(meta) < 140:
        for extra in [
            " مناسب للمنزل والمكتب.",
            " اختيار عملي للاستخدام اليومي.",
            " تسوقه الآن بسهولة.",
        ]:
            if len(meta) >= 140:
                break
            meta += extra
    return meta[:158].rstrip(" ،.-") + "."


def build_h1(ctx: dict) -> str:
    parts = [ctx["keyword_base"]]
    if ctx["plug_type"]:
        parts.append(ctx["plug_type"])
    if ctx["color"]:
        parts.append(ctx["color"])
    if ctx["length"]:
        parts.append(f"{ctx['length']} متر")
    if ctx["wire_size"]:
        parts.append(ctx["wire_size"])
    return normalize_spaces(" - ".join(parts))


def build_slug(ctx: dict) -> str:
    parts = [ctx["slug"]]
    if ctx["plug_type"]:
        parts.append("double-plug" if "ثنائية" in ctx["plug_type"] else "triple-plug")
    if ctx["color"]:
        parts.append("white" if ctx["color"] == "أبيض" else "black")
    if ctx["length"]:
        parts.append(f"{ctx['length'].replace('.5', '-5')}m")
    if ctx["wire_size"]:
        parts.append(ctx["wire_size"].replace(" مم", "mm").replace(" ", ""))
    return "-".join(parts)


def material_sentence(ctx: dict) -> str:
    if not ctx["materials"]:
        return ""
    if any("Anti Fire" in material_name for material_name in ctx["materials"]):
        return "ويأتي بخامة P.C Anti Fire المناسبة للاستخدام اليومي مع مقاومة جيدة للحرارة. "
    if "PA + Fiber" in ctx["materials"] or "PA+Fiber" in ctx["materials"]:
        return "كما يعتمد على خامة PA + Fiber العملية التي تناسب الاستخدام المتكرر. "
    if "PA" in ctx["materials"]:
        return "ويعتمد على خامة PA مع سلك PVC عند توفره لتقديم استخدام يومي مريح. "
    return f"كما يأتي بخامة {ctx['materials'][0]} العملية. "


def specs_sentence(ctx: dict) -> str:
    specs = []
    if ctx["feature_line"]:
        specs.append(ctx["feature_line"])
    if ctx["length"]:
        specs.append(f"طول سلك {ctx['length']} متر")
    if ctx["plug_type"]:
        specs.append(ctx["plug_type"])
    if ctx["wire_size"]:
        specs.append(f"مقاس {ctx['wire_size']}")
    if ctx["color"]:
        specs.append(f"اللون {ctx['color']}")
    if ctx["voltage"]:
        specs.append(f"الجهد {ctx['voltage']}")
    if ctx["dimensions"]:
        specs.append(f"الأبعاد {ctx['dimensions']}")
    if ctx["weight"]:
        specs.append(f"الوزن {ctx['weight']}")
    if ctx["model"]:
        specs.append(f"الموديل {ctx['model']}")
    return "، ".join(specs)


def why_choose_line(ctx: dict) -> str:
    reasons = [
        "تركيزه على المواصفات التي يبحث عنها العميل فعليًا مثل نوع المخارج والطول واللون",
        "سهولة دمجه في الاستخدام المنزلي أو المكتبي بدون تعقيد",
        "صياغته مناسبة لمن يبحث عن شراء مباشر وليس مجرد معلومات عامة",
    ]
    if ctx["plug_type"]:
        reasons.insert(0, "وضوح نوع الفيشة في المنتج مما يقلل احتمالات اختيار موديل غير مناسب")
    if ctx["length"]:
        reasons.insert(0, "إبراز طول السلك بوضوح لمن يقارن بين 2 متر و3 متر و6 متر")
    if ctx["wire_size"]:
        reasons.insert(0, f"إظهار مقاس {ctx['wire_size']} لأنه عامل مهم في قرار الشراء")
    return "، ".join(unique(reasons, 3))


def build_description(ctx: dict) -> str:
    intro_variant = " ".join(variant_bits(ctx)).strip()
    intro = (
        f"إذا كنت تبحث عن {ctx['keyword_base']}"
        f"{(' ' + intro_variant) if intro_variant else ''} يوفر لك {ctx['feature_line']} بشكل عملي، "
        f"فهذا المنتج مناسب لمن يريد حلًا واضحًا للاستخدام اليومي داخل المنزل أو المكتب. "
        f"{ctx['benefit_line']}، كما يساعد على ترتيب التوصيلات أو الشحن بدل الاعتماد على أكثر من وصلة أو شاحن منفصل."
    )

    features = (
        f"{material_sentence(ctx)}"
        f"{'ويأتي بطول سلك ' + ctx['length'] + ' متر لمرونة أفضل في التوزيع. ' if ctx['length'] else ''}"
        f"{'كما أنه متوفر بنوع ' + ctx['plug_type'] + ' ليناسب طريقة التوصيل المطلوبة. ' if ctx['plug_type'] else ''}"
        f"{'اللون ' + ctx['color'] + ' يمنحه مظهرًا مناسبًا مع أغلب الديكورات والأجهزة. ' if ctx['color'] else ''}"
        f"{'ويعمل ضمن جهد ' + ctx['voltage'] + '. ' if ctx['voltage'] else ''}"
        "هذه التفاصيل مهمة جدًا للمستخدم الذي يقارن بين أكثر من مشترك قبل اتخاذ قرار الشراء."
    )

    specs = (
        f"أهم المواصفات المتاحة في هذا المنتج تشمل: {specs_sentence(ctx)}. "
        f"{'ظهور الموديل ' + ctx['model'] + ' يسهل عليك مطابقة المنتج عند الطلب أو المراجعة. ' if ctx['model'] else ''}"
        "كما أن دمج الاسم التجاري مع المواصفات الأساسية يجعل صفحة المنتج أوضح في نتائج البحث."
    )

    use_cases = (
        f"في الاستخدام العملي، يناسب هذا المنتج {ctx['use_cases']}. "
        f"{'وجود منافذ USB أو Type C يجعله مناسبًا لشحن الأجهزة الشخصية من نفس المكان. ' if 'USB' in ctx['main_type'] or 'USB' in ctx['keyword_base'] or 'Type C' in ctx['main_type'] else ''}"
        f"{'أما اختلاف نوع EU وUK فيفيد من يتعامل مع أكثر من نوع فيشة داخل المكان نفسه. ' if 'EU' in ctx['main_type'] or 'UK' in ctx['main_type'] else ''}"
        "ولهذا فهو يخاطب نية شراء واضحة عند العميل الذي يبحث عن منتج محدد بالمواصفات وليس مجرد مشترك عام."
    )

    closing = (
        f"يختاره كثير من العملاء لأنهم يبحثون عادة عن {ctx['keyword_base']}"
        f"{(' ' + ctx['length'] + ' متر') if ctx['length'] else ''}"
        f"{(' ' + ctx['plug_type']) if ctx['plug_type'] else ''}"
        f"{(' ' + ctx['color']) if ctx['color'] else ''}، "
        f"أي منتج يجمع بين النوع المناسب والمقاس أو الطول الصحيح وسهولة الاستخدام. "
        f"وباختصار، هذا المنتج مناسب لمن يريد شراءً مباشرًا بمواصفات واضحة، مع {why_choose_line(ctx)}. "
        "كما أن وضوح الاسم والمواصفات داخل صفحة المنتج يساعد العميل على المقارنة السريعة قبل الشراء، "
        "ويجعل الوصول إلى المنتج من نتائج البحث أكثر دقة وارتباطًا بما يكتبه المستخدم فعليًا."
    )

    return "\n\n".join([intro, features, specs, use_cases, closing])


def build_headings(ctx: dict) -> str:
    headings = [
        f"H2: مزايا {ctx['keyword_base']}",
        "H2: أهم المواصفات الفنية",
        "H3: أين يمكن استخدام المنتج؟",
        "H3: لماذا يناسب نية الشراء المباشرة؟",
    ]
    return "\n".join(headings)


def build_entities(ctx: dict) -> list[str]:
    entities = list(ctx["entities"])
    if ctx["length"]:
        entities.append(f"{ctx['length']} متر")
    if ctx["color"]:
        entities.append(ctx["color"])
    if ctx["plug_type"]:
        entities.append(ctx["plug_type"])
    if ctx["model"]:
        entities.append(ctx["model"])
    return unique(entities, 10)


def build_bullets(ctx: dict) -> str:
    bullets = [
        f"- النوع: {ctx['main_type']}",
        f"- الميزة الأساسية: {ctx['feature_line']}",
    ]
    if ctx["length"]:
        bullets.append(f"- طول السلك: {ctx['length']} متر")
    if ctx["plug_type"]:
        bullets.append(f"- نوع الفيشة: {ctx['plug_type']}")
    if ctx["color"]:
        bullets.append(f"- اللون: {ctx['color']}")
    if ctx["wire_size"]:
        bullets.append(f"- المقاس: {ctx['wire_size']}")
    if ctx["voltage"]:
        bullets.append(f"- الجهد: {ctx['voltage']}")
    if ctx["model"]:
        bullets.append(f"- الموديل: {ctx['model']}")
    return "\n".join(bullets)


def build_alt_texts(ctx: dict) -> list[str]:
    alt_parts = [f"صورة {ctx['keyword_base']}"]
    if ctx["color"]:
        alt_parts.append(ctx["color"])
    if ctx["length"]:
        alt_parts.append(f"{ctx['length']} متر")
    alt_one = " ".join(alt_parts).strip()
    alt_two = f"تفاصيل مخارج {ctx['keyword_base']} و{ctx['feature_line']}".replace("  ", " ").strip()
    if ctx["plug_type"]:
        alt_three = f"شكل {ctx['plug_type']} في {ctx['keyword_base']}"
    elif ctx["wire_size"]:
        alt_three = f"تفاصيل مقاس {ctx['wire_size']} في {ctx['keyword_base']}"
    else:
        alt_three = f"تصميم {ctx['keyword_base']} للاستخدام المنزلي والمكتبي"
    return [normalize_spaces(alt_one), normalize_spaces(alt_two), normalize_spaces(alt_three)]


def build_faq(ctx: dict) -> list[dict]:
    faq = [
        {
            "q": f"ما استخدام {ctx['keyword_base']}؟",
            "a": f"يستخدم لتوفير {ctx['feature_line']} بطريقة عملية تناسب الاحتياج اليومي في المنزل أو المكتب.",
        },
        {
            "q": "هل هذا المنتج مناسب للاستخدام المنزلي والمكتبي؟",
            "a": "نعم، صياغة المنتج ومواصفاته تجعله مناسبًا للاستخدامين حسب عدد الأجهزة وطريقة التوصيل المطلوبة.",
        },
    ]
    if ctx["length"]:
        faq.append(
            {
                "q": "كم طول السلك في هذا المنتج؟",
                "a": f"طول السلك {ctx['length']} متر، وهي نقطة مهمة عند اختيار مكان الاستخدام ومسافة التوصيل.",
            }
        )
    if ctx["plug_type"]:
        faq.append(
            {
                "q": "ما نوع الفيشة في هذا الموديل؟",
                "a": f"هذا الموديل يأتي بنوع {ctx['plug_type']}، لذلك يفضل التأكد من توافقه مع نقطة الكهرباء لديك قبل الشراء.",
            }
        )
    elif "EU" in ctx["main_type"] or "UK" in ctx["main_type"]:
        faq.append(
            {
                "q": "هل يدعم أكثر من نوع فيشة؟",
                "a": "نعم، هذا الموديل يركز على توافق EU وUK، وهو مناسب لمن يستخدم أكثر من معيار في مكان واحد.",
            }
        )
    if ctx["color"]:
        faq.append(
            {
                "q": "هل اللون مهم عند اختيار هذا المنتج؟",
                "a": f"اللون {ctx['color']} مهم لمن يهتم بتناسق المنتج مع الديكور أو لون الأجهزة المحيطة، خاصة في المساحات الظاهرة.",
            }
        )
    return faq[:5]


def build_internal_links(ctx: dict) -> list[str]:
    links = list(ctx["related"])
    if "USB" in ctx["main_type"] or "USB" in ctx["keyword_base"]:
        links.append("مشتركات كهرباء USB")
    if ctx["plug_type"]:
        links.append(f"مشتركات {ctx['plug_type']}")
    if ctx["length"]:
        links.append(f"مشتركات {ctx['length']} متر")
    if ctx["color"]:
        links.append(f"مشتركات {ctx['color']}")
    return unique(links, 6)


def build_schema(ctx: dict) -> dict:
    description = clean_text(build_meta_description(ctx))
    return {
        "name": build_h1(ctx),
        "description": description,
        "brand": ctx["brand"],
        "category": ctx["category"],
        "color": ctx["color"] or "غير محدد",
        "size_length": ctx["length"] + " متر" if ctx["length"] else (ctx["wire_size"] or "غير محدد"),
        "sku_model": ctx["model"] or ctx["current_slug"],
        "offers": {
            "price": ctx["price"],
            "priceCurrency": "EGP",
            "urlSlug": build_slug(ctx),
        },
    }


def build_keyword_quality(ctx: dict) -> str:
    return (
        "الكلمات المختارة تجارية بدرجة عالية مع جانب معلوماتي محدود، "
        "وهي مناسبة جدًا لصفحة منتج لأنها تستهدف نية شراء مباشرة مبنية على النوع والطول واللون ونوع الفيشة أو المنافذ."
    )


def build_notes(ctx: dict) -> str:
    notes = []
    if "USB" in ctx["main_type"] or "USB" in ctx["keyword_base"]:
        notes.append("يفضل إبراز كلمة USB في العنوان وأول 100 حرف من الوصف لأنها تحمل نية شرائية قوية.")
    if "Type C" in ctx["main_type"] or "2C+2A" in ctx["keyword_base"] or "1C+3A" in ctx["keyword_base"]:
        notes.append("يفضل إبراز Type C أو تايب سي لأنه عامل بحث مهم لدى مستخدمي الهواتف الحديثة.")
    if ctx["length"]:
        notes.append(f"يفضل إبراز {ctx['length']} متر في العنوان والوصف لأنه من أهم محددات الشراء.")
    if ctx["color"]:
        notes.append("اللون مهم في البحث لهذا النوع من المنتجات عند وجود أكثر من موديل أو أكثر من لون.")
    if ctx["plug_type"]:
        notes.append("نوع الفيشة مهم جدًا في العنوان لأنه يقلل الزيارات غير المناسبة ويرفع التحويل.")
    if ctx["wire_size"]:
        notes.append(f"مقاس {ctx['wire_size']} يستحق الظهور في العنوان أو bullet points لأنه عنصر مقارنة مباشر.")
    if not notes:
        notes.append("يفضل الحفاظ على اسم المنتج واضحًا مع النوع الرئيسي دون تعميم زائد أو كلمات تسويقية مبالغ فيها.")
    return " ".join(notes)


def flatten_list(items: list[str]) -> str:
    return " | ".join(items)


def flatten_faq(items: list[dict]) -> str:
    return "\n\n".join([f"س: {item['q']}\nج: {item['a']}" for item in items])


def generate_row(row: dict) -> dict:
    ctx = build_context(row)
    output = {
        "1) اسم المنتج الأصلي": ctx["original_name"],
        "2) النوع الرئيسي للمنتج": ctx["main_type"],
        "3) نية البحث الأساسية": f"شراء {ctx['keyword_base']} بمواصفات واضحة تناسب الاستخدام المنزلي أو المكتبي في السوق المصري والعربي.",
        "4) الكلمات المفتاحية الأساسية": flatten_list(primary_keywords(ctx)),
        "5) الكلمات المفتاحية الطويلة Long-tail": flatten_list(long_tail_keywords(ctx)),
        "6) الكلمات المفتاحية المرادفة باللهجة/الاستعمال العربي والمصري": flatten_list(synonym_keywords(ctx)),
        "7) SEO Title": build_title(ctx),
        "8) Meta Description": build_meta_description(ctx),
        "9) H1 مقترح": build_h1(ctx),
        "10) URL Slug مقترح": build_slug(ctx),
        "11) وصف منتج SEO احترافي": build_description(ctx),
        "12) عناوين فرعية H2/H3 داخل الوصف": build_headings(ctx),
        "13) Entity SEO": flatten_list(build_entities(ctx)),
        "14) Bullet points للمميزات": build_bullets(ctx),
        "15) Alt Text مقترح لـ 3 صور": "\n".join(build_alt_texts(ctx)),
        "16) FAQ من 3 إلى 5 أسئلة وأجوبة": flatten_faq(build_faq(ctx)),
        "17) Internal Linking Suggestions": "\n".join(build_internal_links(ctx)),
        "18) Product Schema مقترح": json.dumps(build_schema(ctx), ensure_ascii=False),
        "19) تقييم جودة الكلمة المفتاحية": build_keyword_quality(ctx),
        "20) ملاحظات تحسين إضافية": build_notes(ctx),
        "السعر": ctx["price"],
        "القسم": ctx["category"],
        "Slug الحالي": ctx["current_slug"],
    }
    return output


def main() -> None:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [generate_row(row) for row in reader]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with OUTPUT_JSON.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)

    print(f"Generated {len(rows)} SEO rows")
    print(f"CSV: {OUTPUT_CSV}")
    print(f"JSON: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
