# Query notes
## Q3–shared birthplaces (0 rows)
No two people in the graph share a birthplace. The query itself works: it would return a pair if
two people had the same `bornIn` node.

## Q4–two or more birthplaces (0 rows)
No person has more than one birthplace. This does not mean the data is clean: Wolfgang Pauli is
split into two nodes ("Wolfgang Pauli" and "Wolfgang Ernst Pauli"), and only one of them has a
birthplace. An alias split hides this kind of error, because each node on its own looks valid.
The SHACL `maxCount 1` shape passes for the same reason.

## Q5–people with no educatedAt (6 rows)
This shows only that the graph contains no educatedAt triple for these people. It cannot prove
that they had no education: under the open-world assumption, a missing fact is unknown, not false.
Here the gaps come from the extractor (e.g. a fact phrased in a way no rule covers), from wrong
nodes such as UNESCO being typed as a Person, and from facts the text never states.

## Q6–doctoral ancestors (1 row)
The only result is Saba Hashmi → Waleed Tarar, a chain of length one. The `+` path can only go
further if the advisor has an advisor of their own, and Waleed Tarar has none in the graph. No
doctoral advisors were extracted from the Wikipedia articles at all: Rule 5 needs the words
"doctoral" and "advisor" in one sentence, while the articles say things like "dissertation…
approved by Alfred Kleiner". With the real advisors (Kleiner, Sommerfeld, Langevin) and *their*
advisors in the graph, this query would return multi-step chains.

Louis de Broglie appears only after Fix 2: his single educatedAt triple pointed to the generic
node "university", which the fix removed. The graph became more correct but less complete, and
this query cannot tell those two situations apart.