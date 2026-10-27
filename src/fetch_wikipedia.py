import requests, pathlib
HEADERS = {"User-Agent": "KRR-coursework/1.0 (p233007@pwr.nu.edu.pk)"}
def fetch(title):
    r = requests.get(
    "https://en.wikipedia.org/w/api.php",
    params={"action": "query", "prop": "extracts", "explaintext": 1,
    "redirects": 1, "titles": title, "format": "json"},
    headers=HEADERS, timeout=30)
    page = next(iter(r.json()["query"]["pages"].values()))
    return page["extract"]
pathlib.Path("data/raw").mkdir(parents=True, exist_ok=True)
wikipedia_titles= ["Henri Becquerel", "Louis de Broglie","Albert Einstein", "Wolfgang Pauli","Lev Landau"]

for title in wikipedia_titles:
    text = fetch(title)
    pathlib.Path(f"data/raw/{title.replace(' ', '_')}.txt").write_text(text, encoding="utf-8")