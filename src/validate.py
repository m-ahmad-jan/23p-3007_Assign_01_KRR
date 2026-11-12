from pathlib import Path
from rdflib import Graph
from pyshacl import validate

data =Graph().parse("out/kg.ttl", format="turtle")
shapes =Graph().parse("shapes.ttl", format="turtle")

conforms, report_graph, report_text =validate(
    data,
    shacl_graph=shapes,
    inference="none", 
    abort_on_first=False,
)

Path("shacl_report.txt").write_text(report_text, encoding="utf-8")
print("Conforms:",conforms)