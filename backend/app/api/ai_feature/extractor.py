"""
Vendor Price PDF → SKU Auto-Updater (v4 — Production-Ready)
============================================================
Requirements:  pip install google-genai

Usage:
  python extractor.py --pdf AMUL.pdf --sku SKU_table_2.csv \
      --vendor Vendor.csv --vendorproduct VendorProduct.csv \
      --product Product.csv --apikey KEY1,KEY2

Pipeline:
  1. Validate PDF file
  2. Detect vendor from PDF filename (AMUL.pdf → Amul Engineering)
  3. Filter & enrich SKUs for that vendor (join with Product table)
  4. Extract ALL tables from PDF via Gemini (vision)
  5. Match enriched SKUs with extracted tables via Gemini (text, batched)
  6. Validate matches (price change %, confidence, cross-checks)
  7. Show differences → ask user to approve → save audit log

Features:
  - Multi-key rotation: auto-switches API key on rate limit
  - Batched matching: handles 500+ SKUs efficiently
  - Safe JSON parsing: retries on malformed LLM output
  - PDF validation: checks file before wasting API calls
"""

import argparse, base64, json, re, csv, os, sys, time
from datetime import datetime

MAX_PDF_SIZE_MB = 20

# No default API keys are stored in code. Provide keys via --apikey or
# the GEMINI_API_KEY environment variable (comma-separated for rotation).
DEFAULT_API_KEYS = []


def _sku_id(raw_id) -> str:
    """Normalize SKU ID: 'SKU 19' → '19', '19' → '19'.
    Gemini returns 'SKU 19' but CSV has just '19'."""
    s = str(raw_id).strip()
    if s.upper().startswith("SKU "):
        s = s[4:].strip()
    return s


# ══════════════════════════════════════════════════════════════════════════════
#  VENDOR DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def load_vendors(vendor_csv: str) -> dict:
    """Load Vendor.csv → {VID: {name, prefix, ...}}"""
    vendors = {}
    with open(vendor_csv, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            vid = str(row["VID"])
            vendors[vid] = {
                "name": row["VendorName"],
                "prefix": row["VendorPrefix"],
                "location": row.get("Location", ""),
            }
    return vendors


def detect_vendor_from_pdf(pdf_path: str, vendors: dict) -> str | None:
    """
    Detect vendor ID from PDF filename.
    AMUL.pdf → Amul Engineering, Khedut.pdf → Khedut Enterprises
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0].lower()

    for vid, vdata in vendors.items():
        vendor_word = vdata["name"].lower().split()[0]
        if re.search(r'\b' + re.escape(vendor_word) + r'\b', pdf_name) or pdf_name.startswith(vendor_word):
            return vid
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  SKU ENRICHMENT
# ══════════════════════════════════════════════════════════════════════════════

def enrich_skus_for_vendor(
    sku_path: str,
    vendor_id: str,
    vendorproduct_path: str,
    product_path: str,
) -> list[dict]:
    """
    Filter SKUs for a vendor and enrich with product names:
    SKU → VendorProduct (filter by VID) → Product (join for PName)
    """
    pid_to_pname = {}
    with open(product_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            pid_to_pname[str(row["PID"])] = row["PName"]

    vpid_to_pid = {}
    with open(vendorproduct_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if str(row["VID"]) == str(vendor_id):
                vpid_to_pid[str(row["VPID"])] = str(row["PID"])

    enriched = []
    with open(sku_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            vpid = str(row["VendorProduct_ID"])
            pid = vpid_to_pid.get(vpid)
            if pid:
                row["ProductName"] = pid_to_pname.get(pid, "Unknown")
                enriched.append(row)

    return enriched


# ══════════════════════════════════════════════════════════════════════════════
#  PDF VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def validate_pdf(pdf_path: str) -> tuple[bool, str]:
    """
    Validate PDF file before processing.
    Returns (is_valid, error_message).
    """
    if not os.path.exists(pdf_path):
        return False, f"File not found: {pdf_path}"

    if not pdf_path.lower().endswith('.pdf'):
        return False, f"Not a PDF file: {pdf_path}"

    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    if size_mb > MAX_PDF_SIZE_MB:
        return False, f"PDF too large: {size_mb:.1f}MB (max {MAX_PDF_SIZE_MB}MB)"

    if size_mb < 0.001:
        return False, f"PDF file is empty or corrupt: {pdf_path}"

    # Check PDF magic bytes
    with open(pdf_path, 'rb') as f:
        header = f.read(5)
    if header != b'%PDF-':
        return False, f"Invalid PDF header (file may be corrupt): {pdf_path}"

    return True, ""


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-KEY GEMINI API HELPER
# ══════════════════════════════════════════════════════════════════════════════

def create_clients(api_keys: list[str]) -> list:
    """
    Create a Gemini client for each API key.
    Supports key rotation on rate limits.
    """
    import google.genai as genai
    return [genai.Client(api_key=key.strip()) for key in api_keys if key.strip()]


def call_gemini(clients: list, model: str, contents, max_retries=3):
    """
    Call Gemini with:
    - Multi-key rotation: tries next API key on rate limit
    - Structured JSON output (no markdown fences to clean)
    - Exponential backoff retry for rate limits (429)
    """
    from google.genai.types import GenerateContentConfig

    config = GenerateContentConfig(response_mime_type="application/json")

    # If a single client was passed (backward compat), wrap it
    if not isinstance(clients, list):
        clients = [clients]

    total_attempts = max_retries * len(clients)
    attempt = 0

    for retry_round in range(max_retries):
        for key_idx, client in enumerate(clients):
            attempt += 1
            key_label = f"key{key_idx + 1}" if len(clients) > 1 else "key"
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = any(
                    s in error_str
                    for s in ["429", "rate", "quota", "resource_exhausted", "too many"]
                )
                if is_rate_limit and attempt < total_attempts:
                    if len(clients) > 1:
                        print(f"  ⏳ {key_label} rate limited → switching to next key...")
                    else:
                        wait = min(2 ** retry_round * 15, 60)
                        print(f"  ⏳ Rate limited. Waiting {wait}s... "
                              f"(attempt {attempt}/{total_attempts})")
                        time.sleep(wait)
                else:
                    raise

        # After trying all keys in this round, wait before next round
        if retry_round < max_retries - 1:
            wait = min(2 ** retry_round * 15, 60)
            print(f"  ⏳ All keys exhausted this round. Waiting {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"All {len(clients)} API keys exhausted after {max_retries} rounds")


def safe_json_parse(raw: str, context: str = "response") -> list | dict:
    """
    Safely parse JSON from Gemini response.
    Handles markdown fences and gives clear error messages.
    """
    text = raw.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Failed to parse {context}: {e}")
        # Save the raw response for debugging
        debug_file = f"debug_bad_response_{datetime.now().strftime('%H%M%S')}.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(raw)
        print(f"  📄 Raw response saved to {debug_file}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1: EXTRACT TABLES FROM PDF
# ══════════════════════════════════════════════════════════════════════════════

EXTRACT_PROMPT = """
You are a precise price table extractor for hardware vendor price lists.

Your task: extract EVERY price table from this PDF into structured JSON.

OUTPUT FORMAT — return a JSON array where each element is one table:
{
  "table_name": "<exact heading as printed>",
  "columns": ["<col1>", "<col2>", ...],
  "rows": [
    { "<col1>": <value>, "<col2>": <value>, ... }
  ]
}

STRICT RULES:
1. table_name: copy the EXACT heading text — do not abbreviate, translate, or rephrase.
2. column names: copy EXACTLY as printed, including spaces, dots, brackets, slashes.
3. Size/dimension strings: keep EXACTLY as printed (preserve inch marks, spacing, ranges, hyphens).
4. Rate/price values: numbers (int or float), NOT strings.
5. Empty cells: null — never use empty string or 0 for a missing value.
6. MATRIX TABLES: expand into flat rows (Size × Length → one row per cell).
7. SIDE-BY-SIDE TABLES: two tables on the same page → two separate JSON objects.
8. Do NOT skip any table, even small or partial ones.

Return ONLY the JSON array.
"""


def extract_tables(pdf_path: str, clients) -> list[dict]:
    """Send PDF to Gemini vision and extract all price tables."""
    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode()

    print(f"  Sending {os.path.basename(pdf_path)} to model gpt-3.1-pro...")
    response = call_gemini(
        clients,
        model="gpt-3.1-pro",
        contents=[{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}},
                {"text": EXTRACT_PROMPT}
            ]
        }],
    )

    tables = safe_json_parse(response.text.strip(), "table extraction")
    print(f"  ✓ Extracted {len(tables)} tables")
    return tables


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2: MATCH SKUs WITH EXTRACTED TABLES (batched + pre-filtered)
# ══════════════════════════════════════════════════════════════════════════════

BATCH_SIZE = 50  # Max SKUs per Gemini call
BATCH_DELAY = 5  # Seconds between batches (rate limit)


def _normalize_words(text: str) -> set[str]:
    """Extract meaningful words (len>2) from a string, lowercased."""
    return {w for w in re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower().split() if len(w) > 2}


def _filter_tables_for_skus(tables: list[dict], skus: list[dict]) -> list[dict]:
    """
    Pre-filter: only include tables whose name shares keywords with
    the product names in this SKU batch.  Falls back to ALL tables
    if no keyword overlap is found (safety net).
    """
    sku_words = set()
    for s in skus:
        sku_words |= _normalize_words(s.get('ProductName', ''))

    scored = []
    for t in tables:
        table_words = _normalize_words(t.get('table_name', ''))
        overlap = len(sku_words & table_words)
        if overlap > 0:
            scored.append(t)

    # Safety: if nothing matched, send all tables
    return scored if scored else tables


def _group_skus_by_product(skus: list[dict]) -> list[list[dict]]:
    """
    Group SKUs by ProductName, then pack groups into batches of ~BATCH_SIZE.
    Keeps same-product SKUs together so the model sees them as a coherent set.
    """
    from collections import OrderedDict
    groups = OrderedDict()
    for s in skus:
        key = s.get('ProductName', 'Unknown')
        groups.setdefault(key, []).append(s)

    batches = []
    current_batch = []
    for product_name, group in groups.items():
        if len(current_batch) + len(group) > BATCH_SIZE and current_batch:
            batches.append(current_batch)
            current_batch = []
        current_batch.extend(group)
    if current_batch:
        batches.append(current_batch)

    return batches


def build_match_prompt(tables: list[dict], skus: list[dict]) -> str:
    """Build the matching prompt with extracted tables + enriched SKUs."""
    tables_json = json.dumps(tables, indent=2)

    skus_text = "PRODUCT SKUS TO MATCH:\n"
    for sku in skus:
        skus_text += f"- SKU {sku['SKU ID']}: Product='{sku['ProductName']}', Specs={sku['Specs_JSON']}\n"

    return f"""You are a price matcher for hardware vendor catalogs.

I have extracted price tables from a PDF and have a list of SKUs (product + specs) I need to find prices for.

{skus_text}

EXTRACTED TABLES:
```json
{tables_json}
```

TASK: For each SKU, find the matching row in the extracted tables.

OUTPUT FORMAT — return a JSON array:
[
  {{
    "sku_id": "<SKU ID>",
    "product_name": "<product name>",
    "table_name": "<table where found>",
    "matched_row": {{ ... row data ... }},
    "price": <numeric price>,
    "confidence": <1-10>,
    "reason": "<why this match>"
  }}
]

MATCHING RULES:
1. Match by PRODUCT NAME + SPECS (dimensions/sizes in specs should match table row values).
2. Extract PRICE from "Rate" or similar column (numeric).
3. HIGH confidence (8-10): specs match exactly. MEDIUM (5-7): partial match. LOW (1-4): vague.
4. If product not found, still include it with price: null.
5. Return ONLY the JSON array.
"""


def match_skus(tables: list[dict], skus: list[dict], clients) -> list[dict]:
    """
    Match SKUs against extracted tables using batched Gemini calls.
    - Groups SKUs by product name
    - Pre-filters tables per batch (only relevant ones)
    - Processes in batches of ~50 to avoid token limits
    """
    batches = _group_skus_by_product(skus)
    total_batches = len(batches)

    if total_batches == 1:
        print(f"  Matching {len(skus)} SKUs against {len(tables)} tables...")
    else:
        print(f"  Matching {len(skus)} SKUs in {total_batches} batches (≤{BATCH_SIZE} SKUs each)...")

    all_matches = []

    for i, batch in enumerate(batches):
        # Pre-filter tables for this batch
        relevant_tables = _filter_tables_for_skus(tables, batch)
        products_in_batch = set(s.get('ProductName', '?') for s in batch)

        if total_batches > 1:
            print(f"\n  ── Batch {i+1}/{total_batches}: {len(batch)} SKUs, "
                  f"{len(relevant_tables)}/{len(tables)} tables")
            print(f"     Products: {', '.join(sorted(products_in_batch))}")

        prompt = build_match_prompt(relevant_tables, batch)

        response = call_gemini(
            clients,
            model="gpt-3.1-pro",
            contents=[{"parts": [{"text": prompt}]}],
        )

        raw = response.text.strip()

        # Safe JSON parse with one retry on failure
        try:
            batch_matches = safe_json_parse(raw, f"batch {i+1} match response")
        except json.JSONDecodeError:
            print(f"  🔄 Retrying batch {i+1}...")
            time.sleep(5)
            response = call_gemini(
                clients,
                model="gpt-3.1-pro",
                contents=[{"parts": [{"text": prompt}]}],
            )
            raw = response.text.strip()
            batch_matches = safe_json_parse(raw, f"batch {i+1} retry")

        found = len([m for m in batch_matches if m.get('price')])
        print(f"  ✓ {found}/{len(batch)} matched with prices")

        all_matches.extend(batch_matches)

        # Rate-limit delay between batches
        if i < total_batches - 1:
            print(f"  ⏳ Waiting {BATCH_DELAY}s (rate limit)...")
            time.sleep(BATCH_DELAY)

    # Save combined response for caching / debugging
    with open("gemini_match_response.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(all_matches, indent=2, ensure_ascii=False))

    total_found = len([m for m in all_matches if m.get('price')])
    print(f"\n  ✓ Total: {total_found}/{len(skus)} SKUs matched with prices")
    return all_matches


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3: VALIDATE MATCHES
# ══════════════════════════════════════════════════════════════════════════════

def validate(matches: list[dict], skus: list[dict]) -> list[dict]:
    """
    Validate each match:
    - Compare new price vs current price (flag if >30% change)
    - Cross-check table name against product name
    - Assign: AUTO_ACCEPT / FLAG_FOR_REVIEW / REJECT
    """
    sku_lookup = {_sku_id(s['SKU ID']): s for s in skus}
    validated = []

    for m in matches:
        issues = []
        sku = sku_lookup.get(_sku_id(m.get('sku_id', '')))

        current_price = None
        change_pct = None
        new_price = m.get('price')

        # Price change check
        if sku and sku.get('Current_Buy') and new_price:
            try:
                current_price = float(sku['Current_Buy'])
                if current_price > 0:
                    change_pct = ((float(new_price) - current_price) / current_price) * 100
                    if abs(change_pct) > 30:
                        issues.append(f"Price change: {change_pct:+.1f}%")
            except (ValueError, TypeError):
                pass

        # Table-product cross-check
        product_words = [w for w in (m.get('product_name') or '').lower().split() if len(w) > 2]
        table_lower = (m.get('table_name') or '').lower()
        if product_words and not any(w in table_lower for w in product_words):
            issues.append("Table name doesn't match product")

        # Assign action
        confidence = m.get('confidence', 0)
        m['current_price'] = current_price
        m['change_pct'] = change_pct
        m['issues'] = issues

        if new_price is None:
            m['action'] = 'REJECT'
        elif confidence >= 8 and not issues:
            m['action'] = 'AUTO_ACCEPT'
        elif confidence >= 5:
            m['action'] = 'FLAG_FOR_REVIEW'
        else:
            m['action'] = 'REJECT'

        validated.append(m)

    return validated


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4: INTERACTIVE REVIEW
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_price(val):
    return f"₹{val:.0f}" if val else "—"

def _fmt_change(val):
    return f"{val:+.1f}%" if val is not None else "—"


def review(validated: list[dict]) -> list[dict]:
    """
    Show all matches grouped by action. Ask user to approve.
    AUTO_ACCEPT: batch approve. FLAG_FOR_REVIEW: one by one. REJECT: show only.
    Returns list of user-approved matches.
    """
    auto    = [m for m in validated if m['action'] == 'AUTO_ACCEPT']
    flagged = [m for m in validated if m['action'] == 'FLAG_FOR_REVIEW']
    reject  = [m for m in validated if m['action'] == 'REJECT']
    approved = []

    print(f"\n{'='*90}")
    print(f"  RESULTS: {len(auto)} AUTO_ACCEPT | {len(flagged)} REVIEW | {len(reject)} REJECT")
    print(f"{'='*90}")

    # ── AUTO_ACCEPT
    if auto:
        print(f"\n✅ AUTO_ACCEPT — Confidence ≥8, no issues ({len(auto)}):")
        print(f"  {'SKU':<8} {'Product':<25} {'Current':>10} {'→':>3} {'New':>10} {'Change':>10} {'Conf':>6}")
        print(f"  {'─'*78}")
        for m in auto:
            print(f"  {m['sku_id']:<8} {m['product_name']:<25} "
                  f"{_fmt_price(m['current_price']):>10} → "
                  f"{_fmt_price(m.get('price')):>10} "
                  f"{_fmt_change(m['change_pct']):>10} "
                  f"{m.get('confidence','?'):>5}/10")

        ans = input(f"\n  Accept all {len(auto)} ? (y/n): ").strip().lower()
        if ans in ('y', 'yes'):
            approved.extend(auto)
            print(f"  ✓ {len(auto)} accepted")
        else:
            print(f"  ✗ Skipped all")

    # ── FLAG_FOR_REVIEW (one by one)
    if flagged:
        print(f"\n⚠️  NEEDS REVIEW ({len(flagged)}):")
        print(f"  {'─'*78}")
        for m in flagged:
            issues_str = ", ".join(m.get('issues', [])) or "medium confidence"
            print(f"\n  SKU {m['sku_id']}: {m['product_name']}")
            print(f"    Price:  {_fmt_price(m['current_price'])}  →  {_fmt_price(m.get('price'))}  ({_fmt_change(m['change_pct'])})")
            print(f"    Table:  {m.get('table_name', '?')}")
            print(f"    Why:    {m.get('reason', '?')}")
            print(f"    Issues: {issues_str}")
            print(f"    Conf:   {m.get('confidence', '?')}/10")

            ans = input(f"    Accept? (y/n): ").strip().lower()
            if ans in ('y', 'yes'):
                approved.append(m)
                print(f"    ✓ Accepted")
            else:
                print(f"    ✗ Skipped")

    # ── REJECTED (info only)
    if reject:
        print(f"\n❌ REJECTED ({len(reject)}):")
        for m in reject:
            print(f"  SKU {m.get('sku_id','?')} ({m.get('product_name','?')}): "
                  f"{m.get('reason', 'no match')[:60]}")

    return approved


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════

def save_audit_log(vendor_name: str, pdf_path: str, validated: list[dict], approved: list[dict]):
    """
    Save a timestamped audit log so you can always trace:
    - What was matched, at what confidence
    - What was approved vs rejected
    - Old price → new price for each SKU
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    vendor_short = vendor_name.replace(" ", "_").lower()
    log_filename = f"audit_{vendor_short}_{timestamp}.json"

    approved_ids = {_sku_id(m['sku_id']) for m in approved}

    log_entries = []
    for m in validated:
        log_entries.append({
            "sku_id": _sku_id(m.get('sku_id', '')),
            "product_name": m.get('product_name'),
            "current_price": m.get('current_price'),
            "new_price": m.get('price'),
            "change_pct": round(m['change_pct'], 2) if m.get('change_pct') is not None else None,
            "confidence": m.get('confidence'),
            "table_name": m.get('table_name'),
            "reason": m.get('reason'),
            "issues": m.get('issues', []),
            "action": m.get('action'),
            "user_approved": _sku_id(m.get('sku_id', '')) in approved_ids,
        })

    audit = {
        "timestamp": datetime.now().isoformat(),
        "vendor": vendor_name,
        "pdf_file": os.path.basename(pdf_path),
        "total_skus_matched": len(validated),
        "user_approved": len(approved),
        "user_rejected": len(validated) - len(approved),
        "matches": log_entries,
    }

    with open(log_filename, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)

    print(f"  📋 Audit log saved → {log_filename}")
    return log_filename


# ══════════════════════════════════════════════════════════════════════════════
#  APPLY UPDATES
# ══════════════════════════════════════════════════════════════════════════════

def apply_updates(sku_path: str, approved: list[dict], out_path: str):
    """Write approved price updates to a new CSV file."""
    updates = {_sku_id(m['sku_id']): m['price'] for m in approved if m.get('price')}

    if not updates:
        print("  No updates to apply.")
        return

    rows = []
    with open(sku_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            norm_id = _sku_id(row["SKU ID"])
            if norm_id in updates:
                row["Current_Buy"] = updates[norm_id]
            rows.append(row)

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ Saved → {out_path}  ({len(updates)} prices updated)")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="Vendor Price PDF → SKU Updater (v4)")
    ap.add_argument("--pdf",            required=True,  help="Vendor price list PDF")
    ap.add_argument("--sku",            required=True,  help="SKU CSV file")
    ap.add_argument("--vendor",         required=True,  help="Vendor CSV file")
    ap.add_argument("--vendorproduct",  required=True,  help="VendorProduct CSV file")
    ap.add_argument("--product",        required=True,  help="Product CSV file")
    ap.add_argument("--apikey",         required=False,
                    help="Gemini API key(s), comma-separated for rotation (or GEMINI_API_KEY env var)")
    ap.add_argument("--output",         default="SKU_table_2.csv", help="Output CSV path")
    ap.add_argument("--skip-extract",   action="store_true", help="Reuse cached extracted_tables.json")
    ap.add_argument("--skip-match",     action="store_true", help="Reuse cached gemini_match_response.txt")
    args = ap.parse_args()

    # ── PDF validation
    print(f"\n📋 Validating PDF...")
    is_valid, error_msg = validate_pdf(args.pdf)
    if not is_valid:
        print(f"  ❌ {error_msg}")
        sys.exit(1)
    size_mb = os.path.getsize(args.pdf) / (1024 * 1024)
    print(f"  ✓ Valid PDF ({size_mb:.1f}MB)")

    # ── API keys: priority → --apikey flag > env var > hardcoded defaults
    if args.apikey:
        api_keys = [k.strip() for k in args.apikey.split(',') if k.strip()]
    elif os.environ.get("GEMINI_API_KEY"):
        api_keys = [k.strip() for k in os.environ["GEMINI_API_KEY"].split(',') if k.strip()]
    else:
        api_keys = [k for k in DEFAULT_API_KEYS if k and not k.startswith("PASTE")]

    if not api_keys and not (args.skip_extract and args.skip_match):
        print("ERROR: No API keys found.")
        print("  Options:")
        print("    1. Edit DEFAULT_API_KEYS in extractor.py")
        print("    2. Pass --apikey KEY1,KEY2")
        print("    3. Set GEMINI_API_KEY env var")
        print("  (Use --skip-extract --skip-match to work offline with cached data)")
        sys.exit(1)

    clients = []
    if api_keys:
        clients = create_clients(api_keys)
        print(f"  🔑 Loaded {len(clients)} API key(s)")

    # ── Vendor detection
    print(f"\n📂 Loading vendors from {args.vendor}...")
    vendors = load_vendors(args.vendor)
    print(f"  Found {len(vendors)} vendors: {', '.join(v['name'] for v in vendors.values())}")

    print(f"\n🔍 Detecting vendor from: {os.path.basename(args.pdf)}")
    vendor_id = detect_vendor_from_pdf(args.pdf, vendors)
    if not vendor_id:
        print(f"  ❌ Could not detect vendor from '{os.path.basename(args.pdf)}'")
        print(f"  Known vendors: {', '.join(v['name'] for v in vendors.values())}")
        sys.exit(1)
    vendor_name = vendors[vendor_id]["name"]
    print(f"  ✓ Vendor: {vendor_name} (ID: {vendor_id})")

    # ── SKU enrichment
    print(f"\n📊 Filtering SKUs for {vendor_name}...")
    enriched = enrich_skus_for_vendor(args.sku, vendor_id, args.vendorproduct, args.product)
    print(f"  Found {len(enriched)} SKUs for this vendor")
    for s in enriched[:5]:
        print(f"    • SKU {s['SKU ID']}: {s['ProductName']} — {s['Specs_JSON'][:50]}...")
    if len(enriched) > 5:
        print(f"    ... and {len(enriched) - 5} more")

    # ── Step 1: Extract
    print(f"\n{'━'*80}")
    print(f"  STEP 1: Extract tables from PDF")
    print(f"{'━'*80}")
    if args.skip_extract:
        print(f"  [cached] Loading extracted_tables.json...")
        with open("extracted_tables.json", encoding="utf-8") as f:
            tables = json.load(f)
        print(f"  ✓ {len(tables)} tables loaded from cache")
    else:
        tables = extract_tables(args.pdf, clients)
        with open("extracted_tables.json", "w", encoding="utf-8") as f:
            json.dump(tables, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Cached → extracted_tables.json")

    # ── RPM delay
    if not args.skip_extract and not args.skip_match:
        print(f"\n  ⏳ Waiting 15s (RPM=5 rate limit)...")
        time.sleep(15)

    # ── Step 2: Match
    print(f"\n{'━'*80}")
    print(f"  STEP 2: Match SKUs with extracted tables")
    print(f"{'━'*80}")
    if args.skip_match:
        print(f"  [cached] Loading gemini_match_response.txt...")
        with open("gemini_match_response.txt", encoding="utf-8") as f:
            raw = f.read().strip()
        # Handle old cached files that might have markdown fences
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*",     "", raw)
        raw = re.sub(r"\s*```$",     "", raw)
        matches = json.loads(raw)
        print(f"  ✓ {len(matches)} matches loaded from cache")
    else:
        matches = match_skus(tables, enriched, clients)

    if not matches:
        print("\n  ❌ No matches returned. Check gemini_match_response.txt for details.")
        return

    # ── Step 3: Validate
    print(f"\n{'━'*80}")
    print(f"  STEP 3: Validate & compare prices")
    print(f"{'━'*80}")
    validated = validate(matches, enriched)

    # ── Step 4: Interactive review
    approved = review(validated)

    # ── Save audit log (always, even if nothing approved)
    save_audit_log(vendor_name, args.pdf, validated, approved)

    if not approved:
        print("\n  No updates approved. Audit log saved for reference.")
        return

    # ── Step 5: Apply
    print(f"\n{'━'*80}")
    print(f"  STEP 4: Apply {len(approved)} approved updates → {args.output}")
    print(f"{'━'*80}")
    apply_updates(args.sku, approved, args.output)
    print("\n✓ Done!")


if __name__ == "__main__":
    main()