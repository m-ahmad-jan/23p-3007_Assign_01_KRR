# Note on the SHACL report

The final report has no violations and five warnings, all from the shape that expects every
Person to have a birthplace (`minCount 1`, severity Warning). The two extractor fixes in Step 5
did not change the report, because they affected awards and organisations, not birthplaces.

## The five warnings

| Focus node | Real error or shape too strict? | Explanation |
|---|---|---|
| Lev Landau | Real error | His article gives his birthplace (Baku), but "in Baku" does not attach directly to "born", so Rule 1 misses it. |
| Louis de Broglie | Real error (E1/E3) | His birthplace was extracted onto the wrong node: spaCy split his long name, producing "Pierre Raymond bornIn Dieppe". |
| Wolfgang Pauli | Real error (E3) | His birthplace (Vienna) sits on a separate node, "Wolfgang Ernst Pauli": one person, two nodes. |
| UNESCO | Real error (E4) | The real problem is that UNESCO is typed as a Person at all; the warning only catches a symptom of that. |
| Waleed Tarar | Shape too strict | The private document never states his birthplace. Under the open-world assumption a missing fact is unknown, not wrong, so this is correctly only a warning. |

Several errors pass validation completely: "Pierre Raymond" and "Wolfgang Ernst Pauli" each have
exactly one birthplace, so they satisfy every shape. The `maxCount 1` birthplace shape cannot catch
the Pauli split, because the split leaves each node with one birthplace. SHACL checks that the data
fits the shapes, not that it is true.

## OWL reasoner vs SHACL

**An OWL reasoner can, SHACL cannot:** infer new facts. From the range of `bornIn`, a reasoner
concludes that Ulm is a Place without being told. Because `bornIn` is functional, if the two Pauli
nodes were declared the same person (`owl:sameAs`), a reasoner would conclude that their birthplaces
are the same place, rather than reporting an error.

**SHACL can, an OWL reasoner cannot:** report missing data. The Waleed Tarar warning is exactly
this: SHACL checks the graph as a closed world and notices that no birthplace is recorded. An OWL
reasoner works under the open-world assumption, where a missing fact is simply unknown, so it can
never complain that something is absent.