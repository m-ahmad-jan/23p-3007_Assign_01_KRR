import csv
import re
import unicodedata
from pathlib import Path

EVAL_DIR = Path("eval")
TRIPLES_FILE = Path("out/triples.csv")
SKIP_DOC = "private_document.txt"

PREDICATES =["bornIn", "educatedAt", "worksAt", "receivedAward","doctoralAdvisor"]
FP_POSITIONS= [4, 5, 8, 13]
FN_POSITIONS =[1, 3, 4, 11]

ARTICLES =("the", "a", "an")
NON_ALNUM= re.compile(r"[^a-z0-9 ]")



def normalise(text):
    decomposed =unicodedata.normalize("NFKD", text)
    no_accents ="".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned =NON_ALNUM.sub(" ", no_accents.lower())
    return " ".join(tok for tok in cleaned.split() if tok not in ARTICLES)


def aliases_of(field):
    return [part for part in field.split("|") if part]


def name_variants(main, alias_field, *extra):
    variants = {normalise(main)} | {normalise(x) for x in extra}
    variants |= {normalise(a) for a in aliases_of(alias_field)}
    return variants


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_dicts(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_ratio(num, den):
    return round(num / den, 3) if den else "n/a"


def alpha_key(rec):
    return (rec["subject"].lower(), rec["predicate"].lower(), rec["object"].lower())


def take_positions(rows, positions):
    if not rows:
        return []
    return [(p, rows[(p - 1) % len(rows)]) for p in positions]


def load_reference():
    people = {}
    for rec in read_rows(EVAL_DIR / "wikidata_people.csv"):
        people[rec["title"]] = name_variants(rec["label"], rec["aliases"], rec["title"])

    facts={}
    for title in people:
        fname = EVAL_DIR / f"wikidata_{title.replace(' ', '_')}.csv"
        for rec in read_rows(fname):
            bucket = facts.setdefault((title, rec["predicate"]), {})
            bucket[rec["value_id"]] = (rec["value_label"],
                                       name_variants(rec["value_label"], rec["value_aliases"]))
    return people, facts


def find_match(obj, candidates):
    obj_norm = normalise(obj)
    for wid, (_label, variants) in candidates.items():
        if obj_norm in variants:
            return wid
    return None


def score_triples(people, facts):
    hits=set() 
    wrong= []
    already_listed =set()

    for rec in read_rows(TRIPLES_FILE):
        doc =rec["source_doc"]
        if doc== SKIP_DOC:
            continue
        title= Path(doc).stem.replace("_", " ")
        pred =rec["predicate"]

        right_subject =normalise(rec["subject"]) in people[title]
        wid =find_match(rec["object"], facts.get((title, pred), {})) if right_subject else None

        if wid:
            hits.add((title, pred, wid))
            continue

        triple =(rec["subject"], pred, rec["object"])
        if triple in already_listed:
            continue
        already_listed.add(triple)
        wrong.append({
            "subject": rec["subject"],
            "predicate": pred,
            "object": rec["object"],
            "reason": "object not in Wikidata" if right_subject else "subject is not the article's person",
            "source_doc": doc,
            "sentence": rec["sentence"],
        })
    return hits, wrong


def collect_missed(facts, hits):
    missed=[]
    for (title, pred), values in facts.items():
        for wid, (label, _variants) in values.items():
            if (title, pred, wid) not in hits:
                missed.append({"subject": title, "predicate": pred,
                               "object": label, "wikidata_id": wid})
    return missed


def build_metrics(hits, wrong, missed):
    table =[]
    for pred in PREDICATES + ["ALL"]:
        def matches(p):
            return pred == "ALL" or p == pred
        tp = sum(1 for h in hits if matches(h[1]))
        fp = sum(1 for w in wrong if matches(w["predicate"]))
        fn = sum(1 for m in missed if matches(m["predicate"]))
        table.append({"predicate": pred, "TP": tp, "FP": fp, "FN": fn,
                      "precision": safe_ratio(tp, tp + fp),
                      "recall": safe_ratio(tp, tp + fn)})
    return table


def main():
    people, facts =load_reference()
    hits, wrong =score_triples(people, facts)
    missed=collect_missed(facts, hits)

    metrics= build_metrics(hits, wrong, missed)
    write_dicts(EVAL_DIR / "metrics.csv",
                ["predicate", "TP", "FP", "FN", "precision", "recall"], metrics)

    wrong.sort(key=alpha_key)
    missed.sort(key=alpha_key)
    for stem, records in (("false_positives", wrong), ("false_negatives", missed)):
        if records:
            write_dicts(EVAL_DIR / f"{stem}.csv", list(records[0].keys()), records)

    with open(EVAL_DIR / "selected_errors.csv", "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["type", "position", "subject", "predicate", "object", "source_doc", "sentence"])
        for pos, r in take_positions(wrong, FP_POSITIONS):
            out.writerow(["FP", pos, r["subject"], r["predicate"], r["object"],
                          r["source_doc"], r["sentence"]])
        for pos, r in take_positions(missed, FN_POSITIONS):
            out.writerow(["FN", pos, r["subject"], r["predicate"], r["object"], "", ""])

    print(f"{'predicate':<16} {'TP':>4} {'FP':>4} {'FN':>4} {'P':>7} {'R':>7}")
    for m in metrics:
        print(f"{m['predicate']:<16} {m['TP']:>4} {m['FP']:>4} {m['FN']:>4} "
              f"{str(m['precision']):>7} {str(m['recall']):>7}")
    print(f"\n{len(wrong)} FPs, {len(missed)} FNs. Selected errors -- eval/selected_errors.csv")


if __name__=="__main__":
    main()