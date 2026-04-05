import json
import re
import time
import base64
from datetime import datetime
import os
import google.genai as genai
from google.genai.types import GenerateContentConfig

DEFAULT_API_KEYS = [
    "AIzaSyDdlZiWIa3VoIb_wkJDHLexMsMHYBn7k-c",
    "AIzaSyCQcs-RgMqGGJ7TyRVl-Yrupp5jrSmKWY4",
]

def get_api_keys():
    env_keys = os.environ.get("GEMINI_API_KEY")
    if env_keys:
        return [k.strip() for k in env_keys.split(",") if k.strip()]
    return DEFAULT_API_KEYS

def create_clients(api_keys: list[str]) -> list:
    return [genai.Client(api_key=key.strip()) for key in api_keys if key.strip()]

def call_gemini(clients: list, model: str, contents, max_retries=3):
    config = GenerateContentConfig(response_mime_type="application/json")
    if not isinstance(clients, list):
        clients = [clients]
    total_attempts = max_retries * len(clients)
    attempt = 0
    for retry_round in range(max_retries):
        for key_idx, client in enumerate(clients):
            attempt += 1
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
                    if len(clients) == 1:
                        time.sleep(min(2 ** retry_round * 15, 60))
                else:
                    raise
        if retry_round < max_retries - 1:
            time.sleep(min(2 ** retry_round * 15, 60))
    raise RuntimeError(f"All {len(clients)} API keys exhausted after {max_retries} rounds")

def safe_json_parse(raw: str, context: str = "response") -> list | dict:
    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []

VALIDATE_VENDOR_PROMPT = """
You are a document validator. 
Look only at the first page of this PDF to see if it belongs to the vendor: {vendor_name}.
If it is clearly a price list or catalog for this vendor (or matches their recognizable branding), respond strictly with EXACTLY the word YES.
If you are confident it belongs to a completely different vendor, or is an unrelated document, respond strictly with EXACTLY the word NO.
If unsure, answer YES to let it pass through.
"""

def validate_vendor_pdf(pdf_bytes: bytes, vendor_name: str, clients) -> bool:
    pdf_data = base64.b64encode(pdf_bytes).decode()
    prompt = VALIDATE_VENDOR_PROMPT.format(vendor_name=vendor_name)
    
    response = call_gemini(
        clients,
        model="gemini-2.5-flash",
        contents=[{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}},
                {"text": prompt}
            ]
        }],
    )
    res_text = response.text.strip().upper()
    return "NO" not in res_text  # Defaults to passing unless explicitly NO

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

def extract_tables(pdf_bytes: bytes, clients) -> list[dict]:
    pdf_data = base64.b64encode(pdf_bytes).decode()
    response = call_gemini(
        clients,
        model="gemini-2.5-flash",
        contents=[{
            "parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}},
                {"text": EXTRACT_PROMPT}
            ]
        }],
    )
    return safe_json_parse(response.text.strip(), "table extraction")

BATCH_SIZE = 50
BATCH_DELAY = 5

def _normalize_words(text: str) -> set[str]:
    return {w for w in re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower().split() if len(w) > 2}

def _filter_tables_for_skus(tables: list[dict], skus: list[dict]) -> list[dict]:
    sku_words = set()
    for s in skus:
        sku_words |= _normalize_words(s.get('product_name', ''))
    scored = []
    for t in tables:
        table_words = _normalize_words(t.get('table_name', ''))
        if len(sku_words & table_words) > 0:
            scored.append(t)
    return scored if scored else tables

def _group_skus_by_product(skus: list[dict]) -> list[list[dict]]:
    from collections import OrderedDict
    groups = OrderedDict()
    for s in skus:
        key = s.get('product_name', 'Unknown')
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
    tables_json = json.dumps(tables, indent=2)
    skus_text = "PRODUCT SKUS TO MATCH:\n"
    for sku in skus:
        skus_text += f"- SKU {sku['sku_id']}: Product='{sku['product_name']}', Specs={sku['specs']}\n"
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
    batches = _group_skus_by_product(skus)
    all_matches = []
    for i, batch in enumerate(batches):
        relevant_tables = _filter_tables_for_skus(tables, batch)
        prompt = build_match_prompt(relevant_tables, batch)
        
        try:
            response = call_gemini(
                clients,
                model="gemini-2.5-flash",
                contents=[{"parts": [{"text": prompt}]}],
            )
            batch_matches = safe_json_parse(response.text.strip(), f"batch {i+1} match response")
        except Exception:
            time.sleep(3)
            response = call_gemini(
                clients,
                model="gemini-2.5-flash",
                contents=[{"parts": [{"text": prompt}]}],
            )
            batch_matches = safe_json_parse(response.text.strip(), f"batch {i+1} retry")
            
        all_matches.extend(batch_matches)
        if i < len(batches) - 1:
            time.sleep(BATCH_DELAY)
    return all_matches

def retry_anomalies(tables: list[dict], anomalies: list[dict], skus: list[dict], clients) -> list[dict]:
    if not anomalies:
        return []
    
    anomaly_skus = [s for s in skus if str(s['sku_id']) in [str(m['sku_id']) for m in anomalies]]
    if not anomaly_skus:
        return []
    
    relevant_tables = _filter_tables_for_skus(tables, anomaly_skus)
    prompt = build_match_prompt(relevant_tables, anomaly_skus)
    
    prompt += "\nSPECIAL INSTRUCTION: In the previous attempt, the prices you matched for these SKUs were highly anomalous (deviated by >50%). Re-examine the tables intensely. Do not hallucinate columns. Ensure you are extracting from the true Rate/Price column."
    
    try:
        response = call_gemini(clients, model="gemini-2.5-flash", contents=[{"parts": [{"text": prompt}]}])
        return safe_json_parse(response.text.strip(), "retry response")
    except Exception:
        return []

def validate(matches: list[dict], skus: list[dict]) -> list[dict]:
    sku_lookup = {str(s['sku_id']): s for s in skus}
    validated = []
    for m in matches:
        issues = []
        sku_id = str(m.get('sku_id', '')).strip()
        if sku_id.upper().startswith("SKU "):
            sku_id = sku_id[4:].strip()
            
        sku = sku_lookup.get(sku_id)
        current_price = None
        change_pct = None
        new_price = m.get('price')

        if sku and sku.get('current_buy_rate') is not None and new_price:
            try:
                current_price = float(sku['current_buy_rate'])
                if current_price > 0:
                    change_pct = ((float(new_price) - current_price) / current_price) * 100
                    if abs(change_pct) > 50:
                        issues.append(f"Price change: {change_pct:+.1f}%")
            except (ValueError, TypeError):
                pass

        product_words = [w for w in (m.get('product_name') or '').lower().split() if len(w) > 2]
        table_lower = (m.get('table_name') or '').lower()
        if product_words and not any(w in table_lower for w in product_words):
            issues.append("Table name doesn't match product")

        confidence = m.get('confidence', 0)
        m['current_price'] = current_price
        m['change_pct'] = change_pct
        m['issues'] = issues
        m['sku_id'] = sku_id
        
        specs_data = sku.get('specs') if sku else None
        if specs_data:
            try:
                import ast
                parsed = ast.literal_eval(specs_data) if isinstance(specs_data, str) else specs_data
                m['specs'] = json.dumps(parsed)
            except Exception:
                m['specs'] = specs_data
        else:
            m['specs'] = None

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
