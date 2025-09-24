import requests
import time
import pandas as pd
from tqdm import tqdm
import os

SPECIES_SEARCH_URL = "https://species-ws.nbnatlas.org/search"
OCC_SEARCH_URL = "https://records-ws.nbnatlas.org/occurrences/search"

def get_species_tvk(common_or_sp_name, by="commonName"):
    """
    Get a species TVK/guid from the species service.
    by: "commonName" or "scientificName"
    """
    q = f'{by}:"{common_or_sp_name}"'
    params = {"q": q, "pageSize": 5}
    r = requests.get(SPECIES_SEARCH_URL, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    results = js.get("searchResults", {}).get("results", [])
    if not results:
        return None
    # return the first matching GUID (taxon version key)
    return results[0].get("guid")

def fetch_occurrences_by_tvk(tvk, year_from=None, year_to="*", page_size=500, sleep=0.2):
    """
    Paginate through occurrence search results for one species TVK (lsid).
    Returns a pandas.DataFrame (flattened JSON).
    """
    all_rows = []
    start = 0
    while True:
        q = f'lsid:{tvk}'
        params = {"q": q, "pageSize": page_size, "start": start}
        if year_from is not None:
            params["fq"] = f'year:[{year_from} TO {year_to}]'
        r = requests.get(OCC_SEARCH_URL, params=params, timeout=60)
        r.raise_for_status()
        js = r.json()
        occ = js.get("occurrences", [])
        if not occ:
            break
        # flatten occurrences
        df = pd.json_normalize(occ)
        all_rows.append(df)
        # stop if fewer than page_size (last page)
        if len(occ) < page_size:
            break
        start += page_size
        time.sleep(sleep)  # avoid hammering API
    if not all_rows:
        return pd.DataFrame()
    return pd.concat(all_rows, ignore_index=True)

