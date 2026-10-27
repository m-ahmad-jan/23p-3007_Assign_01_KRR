# AI3001 KRR – Assignment 01: From Text to Knowledge Graph

**Roll number:** 23P-3007

## Description
Turns biographical text (5 Wikipedia articles + 1 private document) into a small knowledge graph, validates it with OWL/SHACL, queries it with SPARQL, and evaluates it against Wikidata.

## Requirements

Python 3.10+ (developed on 3.13)
Java 17+ (developed on Temurin 25)
Apache Jena Fuseki 6.2.0

## Setup

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

```bash
# Fuseki should be installed outside the repo
cd ~/tools/apache-jena-fuseki-6.2.0
./fuseki-server
```

Then open http://localhost:3030 and create a **Persistent (TDB2)** dataset named `kg-23p-3007`.

## How to run

```bash
# Step 1: download the five Wikipedia articles into data/raw/
python src/fetch_wikipedia.py
```

## Repository structure

| Path | Contents |
|---|---|
| `data/raw/` | Five Wikipedia texts + `private_document.txt` |
| `src/` | Python scripts (fetching, extraction) |
| `out/` | `triples.csv`, `kg.ttl` |
| `queries/` | SPARQL queries `q1.rq`–`q6.rq` |
| `results/` | Query results as CSV |
| `eval/` | Wikidata exports, metrics, error analysis |
| `screenshots/` | Fuseki evidence |

## Extraction rules

TODO