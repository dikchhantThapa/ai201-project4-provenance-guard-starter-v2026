# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. Limit false positives

Of 10 clearly human-written pieces, at most 1 should receive the high-confidence AI label.

**Why this target:**  
A false accusation is more harmful than missing some AI-written text, so the system should be conservative about giving a high-confidence AI label.

---

## 2. Clearly different texts should have meaningfully different scores

The average combined score for clearly AI-written text should be at least 0.15 higher than the average combined score for clearly human-written text.

**Why this target:**  
If clearly different examples receive almost the same score, the signals are not separating the two cases enough to make the confidence score useful.

---

## 3. All three label outcomes should be reachable

Across at least 3 deliberately chosen test inputs, the system should produce all three label variants at least once: high-confidence human, unsure, and high-confidence AI.

**Why this target:**  
Each label should represent a real, reachable outcome. If one of the labels can never be produced, the scoring thresholds are not working as intended.

---

## 4. Valid appeals should always enter review

100% of valid appeals — meaning an existing `content_id` with non-empty reasoning — should change the submission status to `under_review` and be recorded in the audit log.

**Why this target:**  
Submitting an appeal does not mean the original decision is automatically overturned. It means the result should be flagged for review. A valid appeal should never be silently lost or ignored.

---

## 5. Bad input should fail safely

100% of requests with missing or empty `text` should return HTTP 400 with a JSON error message, and none should crash or return HTTP 500.

**Why this target:**  
Invalid input is expected in a web service. The service should clearly tell the caller what went wrong instead of crashing.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
