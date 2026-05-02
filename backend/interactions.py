"""
RAYA — Drug interaction logic for MVP.

Architecture:
1) DRUG_ALIASES maps free-text input (Arabic brand, English brand, generic name)
   to a canonical active ingredient.
2) INTERACTIONS is a symmetric matrix of known dangerous combinations,
   keyed by frozenset({ingredient_a, ingredient_b}).

This is the MVP starting dataset. For production, replace with a curated
SFDA-aligned database and link to an external API (RxNav / OpenFDA) on the
active ingredient — never on the brand name.
"""


def _norm(s: str) -> str:
    if not s:
        return ""
    return s.strip().lower()


# ---- Brand / generic / Arabic name → canonical active ingredient ----
DRUG_ALIASES = {
    # Paracetamol
    "paracetamol": "paracetamol",
    "acetaminophen": "paracetamol",
    "panadol": "paracetamol",
    "بانادول": "paracetamol",
    "باراسيتامول": "paracetamol",

    # Ibuprofen
    "ibuprofen": "ibuprofen",
    "brufen": "ibuprofen",
    "بروفين": "ibuprofen",
    "ايبوبروفين": "ibuprofen",
    "إيبوبروفين": "ibuprofen",

    # Aspirin
    "aspirin": "aspirin",
    "asa": "aspirin",
    "أسبرين": "aspirin",
    "اسبرين": "aspirin",

    # Warfarin
    "warfarin": "warfarin",
    "marevan": "warfarin",
    "وارفارين": "warfarin",

    # Clopidogrel
    "clopidogrel": "clopidogrel",
    "plavix": "clopidogrel",
    "بلافيكس": "clopidogrel",

    # Atorvastatin
    "atorvastatin": "atorvastatin",
    "lipitor": "atorvastatin",
    "ليبيتور": "atorvastatin",

    # Esomeprazole
    "esomeprazole": "esomeprazole",
    "nexium": "esomeprazole",
    "نكسيوم": "esomeprazole",

    # Furosemide
    "furosemide": "furosemide",
    "lasix": "furosemide",
    "لازكس": "furosemide",

    # Metformin
    "metformin": "metformin",
    "glucophage": "metformin",
    "جلوكوفاج": "metformin",

    # Bisoprolol
    "bisoprolol": "bisoprolol",
    "concor": "bisoprolol",
    "كونكور": "bisoprolol",

    # Tramadol
    "tramadol": "tramadol",
    "ترامادول": "tramadol",

    # Amoxicillin / Augmentin
    "amoxicillin": "amoxicillin",
    "augmentin": "amoxicillin",
    "أوجمنتين": "amoxicillin",
    "اوجمنتين": "amoxicillin",
}


# ---- Known interactions (severity: severe | moderate) ----
INTERACTIONS = {
    frozenset({"warfarin", "aspirin"}): {
        "severity": "severe",
        "summary_en": "High bleeding risk. Combining warfarin with aspirin significantly increases the risk of major bleeding.",
        "summary_ar": "خطر نزيف مرتفع. الجمع بين الوارفارين والأسبرين يزيد بشكل كبير من خطر النزيف.",
    },
    frozenset({"warfarin", "ibuprofen"}): {
        "severity": "severe",
        "summary_en": "Increases bleeding risk and may raise warfarin levels. Avoid NSAIDs with warfarin.",
        "summary_ar": "يزيد من خطر النزيف وقد يرفع مستوى الوارفارين. يُفضّل تجنب مضادات الالتهاب مع الوارفارين.",
    },
    frozenset({"warfarin", "tramadol"}): {
        "severity": "moderate",
        "summary_en": "Tramadol may increase the anticoagulant effect of warfarin. Monitor INR closely.",
        "summary_ar": "قد يزيد الترامادول من تأثير الوارفارين المضاد للتجلط. يُنصح بمراقبة INR.",
    },
    frozenset({"warfarin", "atorvastatin"}): {
        "severity": "moderate",
        "summary_en": "Atorvastatin may modestly increase warfarin's anticoagulant effect. Monitor INR.",
        "summary_ar": "قد يزيد الليبيتور من تأثير الوارفارين بشكل بسيط. يُنصح بمراقبة INR.",
    },
    frozenset({"aspirin", "ibuprofen"}): {
        "severity": "moderate",
        "summary_en": "Ibuprofen can reduce the cardioprotective effect of aspirin and increase GI bleeding risk.",
        "summary_ar": "قد يقلل الإيبوبروفين من فعالية الأسبرين القلبية ويزيد من خطر نزيف الجهاز الهضمي.",
    },
    frozenset({"clopidogrel", "aspirin"}): {
        "severity": "moderate",
        "summary_en": "Combination increases bleeding risk. Sometimes prescribed together but requires medical supervision.",
        "summary_ar": "هذا المزيج يزيد من خطر النزيف. قد يُوصف معًا أحيانًا لكن يتطلب إشرافًا طبيًا.",
    },
    frozenset({"clopidogrel", "esomeprazole"}): {
        "severity": "moderate",
        "summary_en": "Esomeprazole may reduce the antiplatelet effect of clopidogrel. Consider an alternative PPI.",
        "summary_ar": "قد يقلل النكسيوم من فعالية البلافيكس المضادة للتجلط. يُفضل النظر في بديل.",
    },
    frozenset({"clopidogrel", "ibuprofen"}): {
        "severity": "moderate",
        "summary_en": "Combination increases bleeding risk, particularly GI bleeding.",
        "summary_ar": "هذا المزيج يزيد من خطر النزيف، خصوصًا في الجهاز الهضمي.",
    },
    frozenset({"furosemide", "ibuprofen"}): {
        "severity": "moderate",
        "summary_en": "Ibuprofen can reduce the diuretic and antihypertensive effect of furosemide.",
        "summary_ar": "قد يقلل الإيبوبروفين من تأثير اللازكس المدر للبول وخافض ضغط الدم.",
    },
}


def resolve_drug(name: str):
    """Map user input (Arabic/English brand or generic) → canonical active ingredient."""
    return DRUG_ALIASES.get(_norm(name))


def check_interactions(new_ingredient: str, existing_ingredients: list) -> list:
    """Return warnings for new_ingredient against each existing ingredient."""
    warnings = []
    seen = set()
    for other in existing_ingredients:
        if other == new_ingredient or other in seen:
            continue
        seen.add(other)
        key = frozenset({new_ingredient, other})
        if key in INTERACTIONS:
            info = INTERACTIONS[key]
            warnings.append({
                "drug_a": new_ingredient,
                "drug_b": other,
                "severity": info["severity"],
                "message_en": info["summary_en"],
                "message_ar": info["summary_ar"],
            })
    return warnings


def list_known_drugs() -> dict:
    """Return mapping ingredient → list of accepted aliases (for autocomplete)."""
    by_ingredient = {}
    for alias, ingredient in DRUG_ALIASES.items():
        by_ingredient.setdefault(ingredient, []).append(alias)
    return by_ingredient
