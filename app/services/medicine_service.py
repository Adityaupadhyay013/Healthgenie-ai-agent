"""Evidence-linked medicine reference lookup through RxNorm and DailyMed."""
import asyncio
import re
import httpx

RXNORM_SEARCH_URL = "https://rxnav.nlm.nih.gov/REST/drugs.json"
DAILYMED_SEARCH_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"


def extract_medicine_query(query: str) -> str:
    text = query.strip()
    pattern = (
        r"\b(please|tell me|show me|give me|find|search|information|details|about|"
        r"what|is|are|used|use|does|do|can|i|take|the|medicine|medicines|medication|"
        r"medications|drug|drugs|tablet|tablets|side effects|uses|of|for)\b"
    )
    return " ".join(re.sub(pattern, " ", text, flags=re.IGNORECASE).split()).strip(" .,?!-")


async def search_medicine_references_direct(query: str) -> dict:
    """Direct REST implementation used by the MCP server and local fallback."""
    term = extract_medicine_query(query)
    if len(term) < 2:
        return {"query": term, "medicines": [], "sources": []}

    headers = {"User-Agent": "HealthGenieAI/1.0 (educational project)"}
    timeout = httpx.Timeout(12.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        rx_task = client.get(RXNORM_SEARCH_URL, params={"name": term})
        label_task = client.get(DAILYMED_SEARCH_URL, params={"drug_name": term, "pagesize": 5})
        rx_response, label_response = await asyncio.gather(
            rx_task, label_task, return_exceptions=True
        )

    medicines, sources = [], []
    if not isinstance(rx_response, Exception) and rx_response.is_success:
        groups = rx_response.json().get("drugGroup", {}).get("conceptGroup", []) or []
        seen = set()
        for group in groups:
            for item in group.get("conceptProperties", []) or []:
                rxcui, name = item.get("rxcui"), item.get("name")
                if name and rxcui and rxcui not in seen:
                    seen.add(rxcui)
                    medicines.append({
                        "name": name, "rxcui": rxcui, "tty": item.get("tty"),
                        "reference": "RxNorm",
                        "source_url": f"https://rxnav.nlm.nih.gov/id/{rxcui}",
                    })
        if medicines:
            sources.append({
                "title": "RxNorm drug terminology",
                "url": "https://www.nlm.nih.gov/research/umls/rxnorm/",
            })

    if not isinstance(label_response, Exception) and label_response.is_success:
        for item in label_response.json().get("data", []) or []:
            setid = item.get("setid")
            if setid:
                sources.append({
                    "title": item.get("title") or "DailyMed official label",
                    "url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={setid}",
                })
                if len(sources) >= 6:
                    break
    return {"query": term, "medicines": medicines[:10], "sources": sources}


async def search_medicine_references(query: str) -> dict:
    """Prefer MCP; fall back to the direct REST adapters when MCP is disabled."""
    from app.services.mcp_client import call_mcp_tool
    remote = await call_mcp_tool(
        "search_medicine_reference",
        {"medicine_name_or_ingredient": query},
    )
    if remote is not None:
        return remote
    return await search_medicine_references_direct(query)
