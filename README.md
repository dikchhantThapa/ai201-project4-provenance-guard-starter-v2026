# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does
A submission enters through `POST /submit` with the writer's text and `creator_id`. The service validates the input and runs two independent signals: a model-based detector that evaluates how predictable the text is to a language model, and a stylometric signal that examines surface writing patterns. The two signal scores are combined into one confidence score. That score is mapped to one of three reader-facing labels: likely human-written, unsure, or likely AI-generated. The decision and its component scores are written to the audit log with a unique `content_id`, and the structured result is returned as JSON. If a writer believes the decision is wrong, they can later use `POST /appeal`, which records their reasoning and moves the submission to `under_review`.

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

### False-positive path

If a real writer's work receives an AI-like score, the system may show an AI-related label even though the writing is genuine. The writer can submit an appeal using the content ID and explain why they believe the decision is wrong. The appeal changes the item's status to `under_review` and is recorded in the audit log for later review.

### Endpoint contract

`POST /submit`

Input:

```json
{
  "text": "...",
  "creator_id": "..."
}
```

Output:

```json
{
  "content_id": "...",
  "guess": "...",
  "confidence": 0.0,
  "label": "...",
  "model_score": 0.0,
  "style_score": 0.0
}
```

`POST /appeal`

Input:

```json
{
  "content_id": "...",
  "reasoning": "..."
}
```

Output:

```json
{
  "content_id": "...",
  "status": "under_review",
  "message": "..."
}
```
---

## Signals and Scoring
### Signal one — the model signal

**What it measures:**  
The model signal in `detector.py` measures how predictable the submitted text is to a local language model and converts that into a score where a higher value means the text appears more AI-like.

**Why that might differ between human and AI writing:**  
AI-generated text can sometimes follow statistically predictable language patterns more consistently than human writing, so a language-model-based signal may detect that regularity.

**What it can't see:**  
It cannot know who actually wrote the text. Human writing can also be polished, formal, or highly predictable, while AI-generated writing can be edited to become less predictable. A high model score therefore does not prove that AI wrote the submission.

### Signal two — the style signal

**What it measures:**  
The style signal in `stylometry.py` measures surface-level writing characteristics such as sentence-length variation, vocabulary diversity, and punctuation patterns.

**Why that might differ between human and AI writing:**  
Human and AI writing may differ in how much these surface features vary. For example, some generated text may use more uniform sentence structures or vocabulary patterns than naturally written text.

**What it can't see:**  
Stylometry cannot determine authorship or understand why a person writes in a particular style. A human can intentionally write in a very regular style, and AI can imitate irregular or conversational human writing.
<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->


### The combining rule

**The rule:**

I use a weighted average of the two signals. The model signal gets more weight because the stylometric signal produced a strong false positive on a plain human-written calibration sample. When the signals disagree, the weighted average moves the final score toward the middle instead of letting either signal decide by itself.

**The numbers:**

- Model signal: 75%
- Style signal: 25%

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:**

The borderline calibration sample produced a model score of 0.3489 and a style score of 0.4564. The signals disagree somewhat, with the style signal seeing the text as more AI-like. With the model signal weighted at 75% and the style signal at 25%, the final combined score is 0.3758. This keeps the result closer to the model signal while still allowing the style signal to affect the final score.

---

## Label Variants

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.37 or lower | This text appears likely to have been written by a person. |
| unsure | above 0.37 and below 0.70 | We can't confidently tell whether this text was written by a person or generated by AI. |
| high-confidence AI | 0.70 or higher | This text shows strong signs of being AI-generated, but this result is not proof of authorship. |

**Why I worded the "unsure" one this way:**

I wanted the unsure label to clearly admit that the system does not know the answer. It gives both possibilities without accusing the writer of using AI when the evidence is not strong enough.

---

## Sample Run

**A submission**

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d @samples/clearly_ai.json
```

```json
{
  "confidence": 0.7198,
  "content_id": "c_4f1b60bde639",
  "creator_id": "demo_instructor",
  "guess": "ai",
  "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
  "model_score": 0.7544,
  "style_score": 0.6158
}
```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id":"c_4f1b60bde639","reasoning":"I wrote this text myself and believe the AI classification is incorrect."}'
```

```json
{
  "content_id": "c_4f1b60bde639",
  "message": "Appeal received. This submission is now under review.",
  "status": "under_review"
}
```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=5"
```

Relevant entries from the response:

```json
{
  "combined_score": 0.7198,
  "content_id": "c_4f1b60bde639",
  "creator_id": "demo_instructor",
  "guess": "ai",
  "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
  "model_score": 0.7544,
  "status": "decided",
  "style_score": 0.6158,
  "timestamp": "2026-10-29T21:10:00+00:00"
}
```

```json
{
  "content_id": "c_4f1b60bde639",
  "creator_id": "demo_instructor",
  "event": "appeal",
  "reasoning": "I wrote this text myself and believe the AI classification is incorrect.",
  "status": "under_review",
  "timestamp": "2026-10-29T21:26:32+00:00"
}
```

---

## How I Used AI

**Moment 1**

- **What I asked for:** I asked AI to check whether my acceptance criteria were measurable and could be tested without needing extra explanation from me.
- **What came back:** It pointed out places where the wording needed a specific number or observable result, especially around false positives and appeals.
- **What I changed:** I kept the criteria I chose, but made the outcomes measurable, such as limiting high-confidence AI false positives and requiring valid appeals to move to `under_review`.

**Moment 2**

- **What I asked for:** I used AI to help me reason about my score thresholds after testing the detector on calibration samples, including writing I had written myself.
- **What came back:** The original AI threshold of 0.65 would have labeled my human-written sample, which scored 0.6751, as high-confidence AI.
- **What I changed:** I moved the AI threshold to 0.70 and kept scores between the human and AI thresholds in the unsure range. I preferred an uncertain result over making a strong AI claim on a borderline score.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
