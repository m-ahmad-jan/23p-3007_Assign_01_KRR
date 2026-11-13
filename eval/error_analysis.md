# Error Analysis (Step 5)
Positions from my sheet: false positives **4, 5, 8, 13**; false negatives **1, 3, 4, 11**.
Lists were sorted alphabetically (case-insensitive) by subject, predicate, object.
The items below were selected from the before-fix run, since the fixes changed the lists afterwards.

## False positives
### FP 4 – Albert Einstein, receivedAward, 1921 Nobel Prize in Physics
- **Sentence:** "In 1922, he was awarded the 1921 Nobel Prize in Physics 'for his services to Theoretical Physics…'"
- **Code:** E1 – wrong span
- **Why:** The fact is correct, but spaCy's entity span included the year, and `full_phrase()` returns entity spans unchanged. "1921 Nobel Prize in Physics" does not match Wikidata's "Nobel Prize in Physics".
- **Fix:** Strip leading years, ordinals and articles in `clean()`.

### FP 5 – Albert Einstein, receivedAward, a Nobel Prize
- **Sentence:** "…Einstein agreed that if he were to win a Nobel Prize, he would give the money that he received to Marić…"
- **Code:** E5 – hypothetical statement treated as fact
- **Why:** The verb "win" sits inside an *if*-clause. The negation check only looks for a `neg` child, so conditional statements pass through as facts. The leading "a" also stopped the name from matching.
- **Fix:** Skip verbs that have, or sit under, a `mark` child "if".

### FP 8 – Albert Einstein, worksAt, National Association for the Advancement of Colored People (NAACP
- **Sentence:** "Einstein joined the National Association for the Advancement of Colored People (NAACP) in Princeton…"
- **Code:** E4 – wrong relation
- **Why:** Rule 4 treats every *join* + organisation as employment, but here "joined" means membership. The span was also cut off mid-parenthesis.
- **Fix:** Reject non-employer organisations such as associations, societies, conferences and parties in `is_org()`.

### FP 13 – Lev Landau, receivedAward, Nobel Prize in Physics for his development of a mathematical
- **Sentence:** "He received the 1962 Nobel Prize in Physics for his development of a mathematical theory of superfluidity…"
- **Code:** E1 – span too long
- **Why:** spaCy's entity span ran past the prize name into the reason for the award, and the code trusted it.
- **Fix:** Cut award names at " for ".

## False negatives

### FN 1 – Albert Einstein, doctoralAdvisor, Alfred Kleiner
- **Sentence:** "His 24-page doctoral dissertation… was completed on 30 April 1905 and approved by Alfred Kleiner of the University of Zurich…"
- **Code:** E7 – relation expressed indirectly
- **Why:** Rule 5 only matches the noun *advisor* or *supervisor* together with "doctoral". Here the relation is expressed as a dissertation "approved by" a person, which no rule covers. Approving a dissertation is arguably not the same as supervising it, but Wikidata records Kleiner as the advisor.
- **Fix:** Add a pattern for *dissertation/thesis* + *approve/supervise* + "by" PERSON.

### FN 3 – Albert Einstein, doctoralAdvisor, Heinrich Friedrich Weber
- **Sentence:** None. "Weber" does not appear anywhere in the article.
- **Code:** E7 – fact absent from the source text
- **Why:** Wikidata contains more than the article. No extractor working on this text could find it.
- **Fix:** None within this task; it only lowers the maximum possible recall.

### FN 4 – Albert Einstein, educatedAt, ETH Zurich
- **Sentences:** "…graduated from the federal polytechnic school in 1900…" and "…the federal polytechnic school (later the Eidgenössische Technische Hochschule, ETH) in Zurich…"
- **Code:** E3 – one entity, different names
- **Why:** The article uses the historical name and Wikidata uses the modern one. Before the fixes, "federal polytechnic school" was extracted and counted as a false positive instead of this true positive. Fix 2 then removed it because the name is all lowercase.
- **Fix:** Entity linking: match extracted names against an alias table such as Wikidata's aliases, or use the "later … ETH" phrase as an alias.

### FN 11 – Albert Einstein, receivedAward, Foreign Member of the Royal Society
- **Sentence:** "Einstein was elected… a Foreign Member of the Royal Society in 1921."
- **Code:** E7 – modelling difference
- **Why:** "elect" is not an award verb and "Member" is not an award keyword. More fundamentally, my ontology treats awards as prizes and medals, while Wikidata models this membership as an award.
- **Fix:** Add *elect* + "Member of" or "Fellow of" as an award pattern, or accept it as a difference in modelling choices rather than an extraction error.

## Fixes and their effect

**Fix 1 – span cleaning:** `clean()` now strips leading years, ordinals and articles and cuts names at " (". Rule 3 cuts award names at " for ".

**Fix 2 – stricter organisations:** `is_org()` now requires at least one capitalised word and rejects non-employers such as associations, societies, conferences, parties, committees and leagues.

| Predicate | P before | P after | R before | R after |
|---|---|---|---|---|
| bornIn | 0.750 | 0.750 | 0.600 | 0.600 |
| educatedAt | 0.125 | 0.333 | 0.071 | 0.071 |
| worksAt | 0.167 | 0.200 | 0.029 | 0.029 |
| receivedAward | 0.583 | 0.727 | 0.113 | 0.129 |
| doctoralAdvisor | n/a | n/a | 0.000 | 0.000 |
| **ALL** | **0.400** | **0.565** | **0.099** | **0.107** |

Fix 2 cut educatedAt false positives from 7 to 2 by removing generic nouns such as "university" and the Solvay Conference, and removed the NAACP from worksAt. Fix 1 turned Landau's over-long prize name into "Nobel Prize in Physics", a new true positive, and cleaned two other award spans.

Both were precision fixes: precision rose from 0.40 to 0.565 while recall barely moved. Recall is limited mainly by the source texts, since many Wikidata facts, such as Weber as advisor and most of the 34 employers, never appear in the articles. One side effect is that Fix 2 also removed "federal polytechnic school", which was really ETH Zurich under its historical name.