"""
build_kg.py - turn out/triples.csv into an RDF graph (out/kg.ttl).

Each name becomes a URI in my namespace, e.g. "Saba Hashmi" -> kg:Saba_Hashmi.
Each node also gets:
  - an rdfs:label with its original name
  - an rdf:type taken from the property's domain/range in ontology.ttl
"""
import csv
import re

from rdflib import Graph, Literal, Namespace, RDF, RDFS

KG = Namespace("http://example.org/kg/23p-3007/")

# predicate -> (class of the subject, class of the object), same as ontology.ttl
TYPES = {
    "bornIn":          ("Person", "Place"),
    "educatedAt":      ("Person", "Organization"),
    "receivedAward":   ("Person", "Award"),
    "worksAt":         ("Person", "Organization"),
    "doctoralAdvisor": ("Person", "Person"),
}


def make_uri(name):
    """'Calder College of Science' -> kg:Calder_College_of_Science"""
    slug = re.sub(r"\W+", "_", name).strip("_")
    return KG[slug]


g = Graph()
g.bind("kg", KG)

with open("out/triples.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        s, p, o = row["subject"], row["predicate"], row["object"]
        s_uri, o_uri = make_uri(s), make_uri(o)

        g.add((s_uri, KG[p], o_uri))                 # the fact itself

        subject_class, object_class = TYPES[p]       # types from domain/range
        g.add((s_uri, RDF.type, KG[subject_class]))
        g.add((o_uri, RDF.type, KG[object_class]))

        g.add((s_uri, RDFS.label, Literal(s)))       # human-readable names
        g.add((o_uri, RDFS.label, Literal(o)))

g.serialize("out/kg.ttl", format="turtle")
print(len(g), "RDF triples written to out/kg.ttl")