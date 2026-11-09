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
|
| `data/raw/` | Five Wikipedia texts + `private_document.txt` |
| `src/` | Python scripts (fetching, extraction) |
| `out/` | `triples.csv`, `kg.ttl` |
| `queries/` | SPARQL queries `q1.rq`–`q6.rq` |
| `results/` | Query results as CSV |
| `eval/` | Wikidata exports, metrics,error analysis |
| `screenshots/` | Fuseki evidence |

## Extraction rules

## Extraction rules

All rules work on spaCy's dependency parse (`en_core_web_sm`). A rule starts from a
verb or noun identified by its **lemma**, then follows grammatical links (`nsubj`,
`dobj`, `prep` → `pobj`, etc.) to find the subject and object. Entity labels are used
only as a supporting signal, because spaCy mislabels unseen names (e.g. it tagged
"Riverbend Gold Medal" as LAW and gave "Westmere College of Science" no label).

### Rule 1 –bornIn (dependency parse)
Finds the verb *born* (lemma `bear`), takes its passive subject (`nsubjpass`) as the
person, and the `pobj` of an attached `in` preposition as the place. The place must be
tagged GPE/LOC, which stops "in 1935" from becoming a birthplace. Only the first place
is kept.

### Rule 2 –educatedAt (dependency parse)
Finds *study / graduate / attend / educate* and takes the `pobj` of `at`/`from`
(or the `dobj` of *attend*). A second pattern handles "received his doctorate from X".
The object is kept only if it looks like an organisation (ORG label or a word such as
University/College/Institute). Because each `at` phrase attaches to the verb
separately, "studied at X and later at Y" yields two triples.

### Rule 3 – receivedAward (dependency parse)
Finds *receive / win / award / earn* and takes the direct object (`dobj`). The object is
accepted if its name contains Prize/Medal/Award; spaCy's entity label is ignored here.

### Rule 4 – worksAt (dependency parse)
*join* → direct object; *work / teach* → `pobj` of `at`/`for`; *move* → `pobj` of `to`.
Objects must look like organisations, so "moved to Berlin" is rejected.
**Assumption:** moving *to an organisation* is treated as employment there
(private document: "He later moved to Thornfield College of Science").

### Rule 5 – doctoralAdvisor (dependency parse + keyword)
Fires only in sentences containing "doctoral". Finds the noun *advisor/supervisor*; its
possessor (`poss`) is the student. In "X's advisor was Y" the advisor is the `attr` of
the copula; in "Y was his advisor" it is the `nsubj`.

### Negation
Before any rule fires, the verb is checked for a `neg` child (*never, not, n't*). If
present, nothing is extracted, so "she never studied at Northgate College of Science"
produces no triple.

### Pronoun resolution
Each document has a main person (the Wikipedia title, or the first PERSON in the private
document). The more frequent pronoun set (he/she) in the document is assigned to that
person. A pronoun of the **other** gender resolves to the most recently mentioned
non-main person. In the private document this sends S7's "He" to Waleed Tarar while
S8's "she" stays with Saba Hashmi.

### Alias merging
Names are cleaned (titles like *Dr.*, leading *the*, possessive *'s* removed). If every
word of a name appears in a full name already seen in the document, the two are merged
("Dr. Hashmi" → "Hashmi" → "Saba Hashmi"). Every merge is logged in `out/merges.csv`.

**Merges made:** _N_ (fill in after the full run).

### Provenance and duplicates
Every triple records its source file and sentence. If the same (subject, predicate,
object) appears more than once, only the first occurrence is kept.

### Known limitations
1."became professor at X": the `at` attaches to *professor*, not the verb, so it is missed.
2."studied under Sommerfeld" is not covered by Rule 5.
3.The pronoun heuristic fails when "he" refers to a third person (e.g. a father).
4.Surname-only merging can join different people who share a surname.