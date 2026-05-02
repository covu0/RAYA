# RAYA — MVP Starter

سلامة الأدوية للأسرة السعودية. Medication safety for Saudi families.

This is a working MVP: caregiver creates a patient profile, adds medications by Arabic or English brand name, and gets real-time interaction warnings.

---

## 1. What's inside

```
raya/
├── backend/
│   ├── main.py            FastAPI app — all endpoints
│   ├── interactions.py    Drug aliases (AR/EN) + interaction matrix
│   ├── requirements.txt
│   └── raya.db            (created on first run)
└── frontend/
    ├── index.html         RTL Arabic UI, Tailwind via CDN
    └── app.js             Vanilla JS — no build step
```

No build tools, no node_modules, no Docker. Two terminals, one browser.

---

## 2. Run it (first time, ~5 minutes)

You need **Python 3.10+** installed. That's it.

### Backend

```bash
cd raya/backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`.
Open `http://localhost:8000/docs` to see the auto-generated Swagger UI.

### Frontend

Open a **second terminal**:

```bash
cd raya/frontend
python3 -m http.server 5500
```

Now open **`http://localhost:5500`** in your browser.

> Don't open `index.html` directly with `file://` — browser CORS will block the API calls.

---

## 3. Test scenarios

### Scenario 1 — Severe interaction (the headline demo)
1. Create patient: `جدي أحمد`, age `72`.
2. Add medication: `وارفارين`, dose `5mg`, freq `يوميًا`.
3. Add medication: `بانادول`, dose `500mg`, freq `عند الحاجة`.
   → No warning. Paracetamol is safe with warfarin.
4. Add medication: `أسبرين`, dose `81mg`, freq `يوميًا`.
   → 🔴 Severe warning appears in red: bleeding risk.

### Scenario 2 — Cross-language matching
1. Add `Concor` (English brand). Then add `كونكور` (Arabic).
   → Both resolve to `bisoprolol`. The system sees them as the same drug.
2. Add `Plavix` then add `Nexium`.
   → 🟡 Moderate warning: esomeprazole reduces clopidogrel effectiveness.

### Scenario 3 — Multi-drug elderly profile
Add this real-world combination one by one:
- `Lasix` (furosemide — diuretic)
- `Concor` (bisoprolol — heart)
- `Lipitor` (atorvastatin — cholesterol)
- `Brufen` (ibuprofen — pain)
   → 🟡 Moderate warning: ibuprofen reduces Lasix effect. This is the kind of silent interaction the app is designed to catch.

Open `http://localhost:8000/drugs` to see the full list of recognized names.

---

## 4. What the API looks like

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/caregivers` | Create caregiver |
| POST | `/patients` | Create patient under caregiver |
| GET | `/patients/{id}/medications` | List meds |
| POST | `/patients/{id}/medications` | Add med, returns warnings vs existing |
| DELETE | `/medications/{id}` | Remove |
| GET | `/patients/{id}/check` | Full scan across all meds |
| GET | `/drugs` | Known aliases (autocomplete) |

---

## 5. Roadmap after MVP

**Build next (in this order):**
1. **Auth + multi-patient.** One caregiver, multiple patients (parents, in-laws). Phone-based OTP login (Saudi numbers).
2. **Expand the drug DB to ~200 drugs.** Pull the SFDA-registered drug list. Map each brand to active ingredient. This is your moat — no Western app has this.
3. **Pharmacist-shareable PDF report.** One button → Arabic PDF with the patient's full med list and any flagged interactions, ready to hand to the pharmacy. This is what makes caregivers actually trust the app.
4. **Push notifications.** When a new med is added that interacts with existing meds, notify a second caregiver (the sibling sharing care).

**Improve:**
- Replace mock interaction matrix with calls to RxNav / OpenFDA on the *active ingredient* (after you've resolved the brand name locally).
- Add severity tiers: severe, moderate, minor + "monitor" notes.
- Add allergy field on patient profile (penicillin allergy → flag Augmentin).

**Ignore for now (do NOT build yet):**
- Arabic OCR for prescriptions. Validate the core loop manually first. OCR is a rabbit hole.
- ML / "AI features." You don't need them. The product wins on *coverage of Arabic brand names*, not on AI.
- Native iOS/Android. Ship as PWA from this same codebase.
- Doctor-side dashboard. Caregivers sharing PDFs is enough for v1.
- Pricing / subscriptions. Get 50 real caregivers using it free first.
