"""Evidence-linked medicine reference lookup.

This module retrieves drug identity and official labeling; it does not recommend
medicines for symptoms or generate prescriptions.
"""
import re
import httpx

RXNORM_SEARCH_URL = "https://rxnav.nlm.nih.gov/REST/drugs.json"
DAILYMED_SEARCH_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"


def extract_medicine_query(query: str) -> str:
    """Remove common request wording; the remaining text is a search term, not a diagnosis."""
    text = query.strip()
    patterns = [
        r"\b(please|tell me|show me|give me|find|search|information|details|about|"
        r"medicine|medicines|medication|medications|drug|drugs|tablet|tablets|"
        r"side effects|uses|of|for)\b",
    ]
    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return " ".join(text.split()).strip(" .,?!-")


async def search_medicine_references(query: str) -> dict:
    """Search RxNorm and DailyMed by a medicine name or ingredient."""
    term = extract_medicine_query(query)
    if len(term) < 2:
        return {"query": term, "medicines": [], "sources": []}

    headers = {"User-Agent": "HealthGenieAI/1.0 (educational project)"}
    timeout = httpx.Timeout(12.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        rx_task = client.get(RXNORM_SEARCH_URL, params={"name": term})
        label_task = client.get(DAILYMED_SEARCH_URL, params={"drug_name": term, "pagesize": 5})
        rx_response, label_response = await _gather_responses(rx_task, label_task)

    medicines = []
    sources = []
    if rx_response is not None and rx_response.is_success:
        data = rx_response.json()
        groups = data.get("drugGroup", {}).get("conceptGroup", []) or []
        seen = set()
        for group in groups:
            for item in group.get("conceptProperties", []) or []:
                rxcui = item.get("rxcui")
                name = item.get("name")
                if name and rxcui and rxcui not in seen:
                    seen.add(rxcui)
                    medicines.append({
                        "name": name,
                        "rxcui": rxcui,
                        "tty": item.get("tty"),
                        "reference": "RxNorm",
                        "source_url": f"https://rxnav.nlm.nih.gov/id/{rxcui}",
                    })
        if medicines:
            sources.append({"title": "RxNorm drug terminology", "url": "https://www.nlm.nih.gov/research/umls/rxnorm/"})

    if label_response is not None and label_response.is_success:
        data = label_response.json()
        for item in data.get("data", []) or []:
            setid = item.get("setid")
            if setid:
                sources.append({
                    "title": item.get("title") or item.get("drug_name") or "DailyMed official label",
                    "url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}",
                })
                if len(sources) >= 6:
                    break

    return {"query": term, "medicines": medicines[:10], "sources": sources}


async def _gather_responses(rx_task, label_task):
    """Run independent reference lookups concurrently while isolating source failures."""
    import asyncio
    results = await asyncio.gather(rx_task, label_task, return_exceptions=True)
    return tuple(None if isinstance(result, Exception) else result for result in results)
