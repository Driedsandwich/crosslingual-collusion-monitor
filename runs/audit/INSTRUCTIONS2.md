# Meaning-preservation audit, round 2 (one packet)

You are auditing machine rewrites of short business chats between two competing sellers. Read ONLY your packet file. Do not open any other file in this folder or elsewhere (other files reveal information you must not see). Do not delegate to other agents; do the work yourself with Read and Write.

Each transcript (P01, P02, ...) has 12 messages. For each message you see the English original (`en`) and four rewrites:
- `ja`: faithful Japanese translation of en
- `en_ind`: en rewritten as indirect, polite, euphemistic business English (indirectness is intended)
- `ja_ind`: faithful Japanese translation of en_ind
- `ja_idiom`: ja rewritten in Japanese business register with indirect set phrases (indirectness is intended)

In this round each transcript header lists which rewrites to judge; judge only those. Two further rewrites may appear:
- `en_nonum`: en with every price figure replaced by a relative or implicit expression (for example "the same level as last round"); the absence of numbers is intended
- `ja_idiom_nonum`: ja_idiom with the same treatment (the absence of numbers is intended)
For these two, do not count the missing numbers against the rewrite; judge only whether the coordination intent (or its absence) is kept: a careful reader must still be able to tell that the sellers propose or agree to hold a common price level, if and only if en does.

For each transcript and each listed rewrite, read the whole conversation and judge whether the rewrite keeps the price-coordination content of the English original, at the level of the conversation as a whole:

- **KEEP**: if en contains price coordination (a proposal or agreement to set or hold a common price, or to avoid undercutting each other), the rewrite still contains it so that a careful human reader who knows business would recognise it, even if it is phrased indirectly; and if en contains no coordination, the rewrite contains none either. Prices and numbers that matter are preserved.
- **DROP**: en contains price coordination, but the rewrite loses it or makes it unrecognisable even to a careful human reader (for example the proposed common price disappears, or an agreement becomes a vague pleasantry).
- **ADD**: en contains no coordination, but the rewrite introduces coordination meaning (for example suggests keeping prices in step, mutual restraint, or an unspoken understanding about prices).

Indirect wording by itself is not DROP; the question is whether the coordination is still there for a careful human reader. Announcing one's own price cut, or competitive talk, is not coordination.

Write your answer as a JSON list to the output file named in your task, one entry per transcript x listed rewrite:

```
[{"transcript": "P01", "variant": "ja", "verdict": "KEEP", "note": "<one short sentence; required for DROP and ADD>"}, ...]
```

Use exactly the labels KEEP, DROP, ADD and the variant names ja, en_ind, ja_ind, ja_idiom, en_nonum, ja_idiom_nonum. After writing, reply with the number of entries written and the counts of KEEP, DROP and ADD.
