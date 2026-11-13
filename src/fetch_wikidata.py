import csv
import time
from pathlib import Path

import requests

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
ENTITY_PREFIX = "http://www.wikidata.org/entity/"
OUT_DIR = Path("eval")

PEOPLE =[
    "Henri Becquerel",
    "Louis de Broglie",
    "Albert Einstein",
    "Wolfgang Pauli",
    "Lev Landau",
]

PREDICATE_MAP ={
    "bornIn": "P19",
    "educatedAt": "P69",
    "receivedAward": "P166",
    "worksAt": "P108",
    "doctoralAdvisor": "P184",
}

session = requests.Session()
session.headers.update({"User-Agent": "KRR-coursework/1.0 (p233007@pwr.nu.edu.pk)"})


def build_facts_query(qid):
    pairs = "\n".join(f'    ("{name}" wdt:{prop})' for name, prop in PREDICATE_MAP.items())
    return f"""
SELECT ?pred ?value ?label (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?aliases)
WHERE {{
  VALUES (?pred ?wdt) {{
{pairs}
  }}
  wd:{qid} ?wdt ?value .
  ?value rdfs:label ?label . FILTER(LANG(?label) = "en")
  OPTIONAL {{ ?value skos:altLabel ?alt . FILTER(LANG(?alt) = "en") }}
}}
GROUP BY ?pred ?value ?label
"""


def build_person_query(qid):
    return f"""
SELECT ?label (GROUP_CONCAT(DISTINCT ?alt; separator="|") AS ?aliases)
WHERE {{
  wd:{qid} rdfs:label ?label . FILTER(LANG(?label) = "en")
  OPTIONAL {{ wd:{qid} skos:altLabel ?alt . FILTER(LANG(?alt) = "en") }}
}}
GROUP BY ?label
"""


def lookup_qid(article):
    """Return the Wikidata item ID linked to a Wikipedia article."""
    params = {
        "action": "query",
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "redirects": 1,
        "titles": article,
        "format": "json",
    }
    data = session.get(WIKIPEDIA_API, params=params, timeout=30).json()
    pages = list(data["query"]["pages"].values())
    return pages[0]["pageprops"]["wikibase_item"]


def query_wikidata(sparql):
    resp = session.get(WIKIDATA_SPARQL, params={"query": sparql, "format": "json"}, timeout=60)
    resp.raise_for_status()
    return resp.json()["results"]["bindings"]


def field(row, name):
    """Safely pull a value out of a SPARQL result row ('' if missing)."""
    return row[name]["value"] if name in row else ""


def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    all_people=[]

    for name in PEOPLE:
        qid =lookup_qid(name)
        print(f"{name}: {qid}")

        for row in query_wikidata(build_person_query(qid)):
            all_people.append([name, qid, field(row, "label"), field(row, "aliases")])

        results = query_wikidata(build_facts_query(qid))
        fact_rows = [
            [
                field(row, "pred"),
                field(row, "value").replace(ENTITY_PREFIX, ""),
                field(row, "label"),
                field(row, "aliases"),
            ]
            for row in results
        ]
        target = OUT_DIR / f"wikidata_{name.replace(' ', '_')}.csv"
        save_csv(target, ["predicate", "value_id", "value_label", "value_aliases"], fact_rows)
        print(f"  {len(fact_rows)} facts -> {target}")

        time.sleep(1)

    save_csv(OUT_DIR / "wikidata_people.csv", ["title", "qid", "label", "aliases"], all_people)


if __name__ =="__main__":
    main()