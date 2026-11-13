# Reflection
## Predictions

I did not write `predictions.md` before the first full run, so I cannot compare genuine
predictions with the results. Anything I wrote now would be shaped by hindsight: after seeing
that educatedAt had the lowest precision, it feels obvious that it would. That is exactly the bias
the predictions step is designed to prevent.

What I can describe honestly is what surprised me:
**spaCy's entity labels were less reliable than I assumed.** The Riverbend Gold Medal was tagged
  LAW and Westmere College of Science got no label at all, so the rules had to rely on grammar
  position instead of labels.
**[Your answer: e.g. how low recall was. Did you expect to find most facts? What did you
  assume about how much of Wikidata appears in the articles?]**
**[Your answer: e.g. that no doctoral advisors came out of Wikipedia, or that UNESCO became a
  Person. Pick whichever genuinely surprised you.]**

The private-document traps (pronoun, alias, negation) were all handled, but mainly because the
rules were tested on that document. The Wikipedia articles showed how fragile the same heuristics
are: "Paul" merged into the wrong person, and "Wolfgang Ernst Pauli" stayed a separate node.

## Open-world assumption

The clearest case was Query 5 (people with no educatedAt). After Fix 2, Louis de Broglie appeared in
the results. Before the fix, he had one educatedAt triple pointing to a generic node called
"university", which was wrong. The fix removed it, so the graph now says nothing about his education.

My first reading was that the fix had made his record worse. Under the open-world assumption, it had
not: before, the graph claimed something false; afterwards, it claimed nothing. "Not in the graph"
means unknown, not "he had no education". Query 5 cannot distinguish a person who was never educated
from one whose education the extractor missed, so its result describes the extractor, not the world.

The same applies to recall. Most of the 108 false negatives are facts the articles never state, such
as Weber as Einstein's advisor. A missing triple can mean the extractor failed, or simply that the
source was silent.