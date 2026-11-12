from pathlib import Path
import requests

ENDPOINT="http://localhost:3030/kg-23p-3007/query"

Path("results").mkdir(exist_ok=True)

for i in range(1, 7):
    query=Path(f"queries/q{i}.rq").read_text(encoding="utf-8")
    r=requests.post(
        ENDPOINT,
        data={"query": query},
        headers={"Accept": "text/csv"},
        timeout=30,
    )
    r.raise_for_status()
    Path(f"results/q{i}.csv").write_text(r.text, encoding="utf-8")
    rows=len(r.text.strip().splitlines()) - 1
    print(f"q{i}: {rows} rows -> results/q{i}.csv")