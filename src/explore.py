import csv
import sys
from pathlib import Path

import spacy
nlp=spacy.load("en_core_web_sm")

HE_WORDS={"he", "him", "his"}
SHE_WORDS ={"she", "her", "hers"}
TITLES ={"dr", "dr.", "prof", "prof.", "professor", "sir", "the"}

ORG_WORDS= {"university","institute","college",  "school", "gymnasium",
             "polytechnic", "academy", "laboratory", "eth", "sorbonne"}
AWARD_WORDS= {"prize", "medal", "award"}
DEGREE_WORDS= {"doctorate", "degree", "phd", "diploma"}

merges=set()



#Cleaning names
def clean(text):
    text =text.strip().strip('"')
    if text.endswith("'s"):
        text=text[:-2]
    words = text.split()
    while words and words[0].lower() in TITLES:
        words.pop(0)
    return " ".join(words)


def full_phrase(token):
    for ent in token.doc.ents:
        if ent.start <=token.i < ent.end and ent.label_ not in ("DATE", "CARDINAL"):
            return clean(ent.text)


    words=[]
    for child in token.lefts:
        if child.dep_ in ("compound", "amod"):
            words.append(child.text)
    words.append(token.text)
    for child in token.rights:
        if child.dep_ =="prep" and child.text=="of":
            words.append("of")
            for obj in child.children:
                for t in obj.subtree:
                    words.append(t.text)
    return clean(" ".join(words))


def is_org(token, name):
    if token.ent_type_ in ("ORG","FAC"):
        return True
    for word in name.split():
        if word.lower() in ORG_WORDS:
            return True
    return False


def is_award(name):
    for word in name.split():
        if word.lower() in AWARD_WORDS:
            return True
    return False


#Reading the parse tree
def get_subject(verb):
    for child in verb.children:
        if child.dep_ in ("nsubj","nsubjpass"):

            if child.text.lower() =="who" and verb.dep_ =="relcl":
                return verb.head
            return child
    if verb.dep_ == "acl":
        return verb.head
    if verb.dep_ in ("conj", "xcomp", "advcl"):
        return get_subject(verb.head)
    return None


def is_negated(verb):
    for child in verb.children:
        if child.dep_ == "neg":
            return True
    return False


def prep_objects(verb, preps):

    found= []
    for child in verb.children:
        if child.dep_ == "prep" and child.text.lower() in preps:
            for obj in child.children:
                if obj.dep_ == "pobj":
                    found.append(obj)
                    for c in obj.children:
                        if c.dep_ == "conj":
                            found.append(c)
    return found


def direct_objects(verb):
    found= []
    for child in verb.children:
        if child.dep_ == "dobj":
            found.append(child)
            for c in child.children:
                if c.dep_ =="conj":
                    found.append(c)
    return found


#Who is who: pronouns and aliases
def same_person(name, state):
    for known in state["known"]:
        if set(name.split()) <=set(known.split()):
            if name != known:
                merges.add((state["doc"], name, known))
            return known
    if len(name.split()) > 1:
        state["known"].append(name)
    return name


def who_is(token, state):
    if token is None:
        return None
    word=token.text.lower()

    if word in HE_WORDS or word in SHE_WORDS:
        gender = "m" if word in HE_WORDS else "f"
        if gender == state["main_gender"]:
            return state["main"]
        return state["other"]

    if token.pos_=="PRON": 
        return None
    if token.pos_!= "PROPN" and token.ent_type_ != "PERSON":
        return None
    return same_person(full_phrase(token), state)


def remember_people(sent, state):
    for ent in sent.ents:
        if ent.label_ =="PERSON":
            name= same_person(clean(ent.text), state)
            if name != state["main"]:
                state["other"] =name


#The extraction rules
def extract(sent, state):
    triples =[]

    for tok in sent:
        lemma= tok.lemma_.lower()

        if is_negated(tok):
            continue
        if lemma in ("bear", "born"):
            person = who_is(get_subject(tok), state)
            for place in prep_objects(tok, {"in"}):
                if place.ent_type_ in ("GPE", "LOC"): 
                    triples.append((person, "bornIn", full_phrase(place)))
                    break 
        if lemma in ("study", "graduate", "attend", "educate"):
            person =who_is(get_subject(tok), state)
            orgs =prep_objects(tok, {"at", "from"})
            if lemma== "attend":
                orgs+= direct_objects(tok)
            for org in orgs:
                name = full_phrase(org)
                if is_org(org, name):
                    triples.append((person, "educatedAt", name))
        if lemma in ("receive", "obtain", "earn"):
            for obj in direct_objects(tok):
                if obj.text.lower() in DEGREE_WORDS:
                    person = who_is(get_subject(tok), state)
                    for org in prep_objects(tok, {"from", "at"}) + prep_objects(obj, {"from", "at"}):
                        name = full_phrase(org)
                        if is_org(org, name):
                            triples.append((person, "educatedAt", name))



        if lemma in ("receive", "win", "award", "earn"):
            person = who_is(get_subject(tok), state)
            for obj in direct_objects(tok):
                name = full_phrase(obj)
                if is_award(name):
                    triples.append((person, "receivedAward", name))

        if lemma in ("join", "work", "teach", "move"):
            person =who_is(get_subject(tok), state)
            if lemma== "join":
                orgs= direct_objects(tok)
            elif lemma== "move":
                orgs =prep_objects(tok, {"to"})
            else:
                orgs = prep_objects(tok, {"at", "for"})
            for org in orgs:
                name =full_phrase(org)
                if is_org(org, name):
                    triples.append((person, "worksAt", name))

        if lemma in ("advisor", "adviser", "supervisor") and "doctoral" in sent.text.lower():
            student =None
            advisor =None
            for child in tok.children:
                if child.dep_== "poss":   
                    student= child
            if tok.dep_ =="nsubj":  
                for child in tok.head.children:
                    if child.dep_ =="attr":
                        advisor = child
            elif tok.dep_== "attr":
                for child in tok.head.children:
                    if child.dep_== "nsubj":
                        advisor = child
            triples.append((who_is(student, state), "doctoralAdvisor", who_is(advisor, state)))

    good = []
    for s, p, o in triples:
        if s and o and s != o:
            good.append((s, p, o))
    return good


# Running over files
def process_file(path):
    lines =[]
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("="):
            lines.append(line)
    docs = list(nlp.pipe(lines))

    if path.stem== "private_document":
        main = None
        for doc in docs:
            for ent in doc.ents:
                if ent.label_ == "PERSON" and main is None:
                    main = clean(ent.text)
    else:
        main = path.stem.replace("_"," ") 

    he_count =0
    she_count= 0
    for doc in docs:
        for tok in doc:
            if tok.text.lower() in HE_WORDS:
                he_count += 1
            if tok.text.lower() in SHE_WORDS:
                she_count += 1

    state = {
        "doc": path.name,
        "main": main,
        "main_gender": "f" if she_count > he_count else "m",
        "other": None,
        "known": [main],
    }

    rows = []
    for doc in docs:
        for sent in doc.sents:
            sentence = " ".join(sent.text.split())
            for s, p, o in extract(sent, state):
                rows.append([s, p, o, path.name, sentence])
            remember_people(sent, state)
    return rows


def main():
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        files = sorted(Path("data/raw").glob("*.txt"))

    all_rows = []
    seen = set()
    for path in files:
        for row in process_file(path):
            key =(row[0], row[1], row[2])
            if key not in seen:  
                seen.add(key)
                all_rows.append(row)

    Path("out").mkdir(exist_ok=True)
    with open("out/triples.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["subject", "predicate", "object", "source_doc", "sentence"])
        writer.writerows(all_rows)

    with open("out/merges.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_doc", "short_name", "merged_into"])
        writer.writerows(sorted(merges))

    print(len(all_rows), "triples written to out/triples.csv")
    for pred in ["bornIn", "educatedAt", "receivedAward", "worksAt", "doctoralAdvisor"]:
        count = sum(1 for r in all_rows if r[1] == pred)
        print("  ", pred, count)
    print(len(merges), "alias merges written to out/merges.csv")


if __name__=="__main__":
    main()