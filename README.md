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

**My limits:** 5 per minute, 50 per day

**Why those numbers and not others:**
A normal writer is unlikely to submit more than five pieces of writing in one minute, so five per minute still allows normal use while slowing down scripts that rapidly probe the detector. The daily limit of 50 allows repeated legitimate use without letting one caller send hundreds or thousands of submissions.
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** 
A caller is counted by creator_id when one is provided. If there is no usable creator_id, the service falls back to the caller's address.
<!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**
<!-- python run_attacks.py --flood 15 -->

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

---

## Attack Run — Before
I ran all 56 attacks before making any fixes.

- **HELD:** 32
- **BROKE:** 24
- **Auto-crashes:** 2

The biggest problem was false positives. Six of the eight false-positive attacks were genuine human writing that my service labeled as high-confidence AI.

The evasion attacks also exposed a weakness: 9 of 10 AI-evasion examples avoided the high-confidence AI label.

The prompt-injection attacks held because the submitted instructions did not control the response schema, fixed label text, or audit fields.

The rate-limit attack held. The first five requests from the shared creator were accepted, and requests 6–12 returned HTTP 429.
<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `c_e26590803d00` | human | 0.317 | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `c_c6840b009879` | unsure | 0.547 | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `c_85a1fa37bfc2` | unsure | 0.647 | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `c_cf3ba880ca73` | unsure | 0.645 | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `c_78d7f5cad5ed` | human | 0.327 | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `c_9926e697bef3` | unsure | 0.504 | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 | `c_c3ec84b292b8` | unsure | 0.589 | BROKE |
| EV08 | evasion | signal one: text below the token window | 200 | `c_71ba3426474a` | unsure | 0.399 | BROKE |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `c_b07f4aef1b73` | unsure | 0.675 | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `c_6c3ff394f7fc` | ai | 0.885 | HELD |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `c_336add0b81ed` | unsure | 0.606 | HELD |
| FP02 | false_positive | human writing in a formal register | 200 | `c_8675be6e032e` | ai | 0.728 | BROKE |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `c_850ce62804d2` | ai | 0.777 | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 | `c_896799928222` | ai | 0.801 | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 | `c_f30b61843294` | ai | 0.748 | BROKE |
| FP06 | false_positive | a person imitating a formal template | 200 | `c_fc4d4c771ada` | ai | 0.803 | BROKE |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `c_ed347dd32724` | ai | 0.749 | BROKE |
| FP08 | false_positive | very short genuine human submission | 200 | `c_e810c45a6951` | unsure | 0.438 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `c_69d888f64e0e` | unsure | 0.514 | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `c_bf98ca9c22ca` | human | 0.294 | HELD |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `c_cca59e2a75a7` | unsure | 0.641 | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `c_83506462c080` | unsure | 0.543 | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `c_325a81d18e7e` | unsure | 0.596 | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 | `c_b165e6ed44cb` | unsure | 0.564 | HELD |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — | HELD |
| MF02 | malformed | text is a single character | 500 | `—` | — | — | BROKE |
| MF03 | malformed | text is control characters | 200 | `c_68fda5683d57` | human | 0.250 | BROKE |
| MF04 | malformed | text is only punctuation | 200 | `c_8aa21753a554` | human | 0.208 | BROKE |
| MF05 | malformed | text is a very long single word | 200 | `c_0d6effb0f493` | ai | 0.998 | BROKE |
| MF06 | malformed | text is emoji only | 200 | `c_16522127f3ae` | ai | 0.948 | BROKE |
| MF07 | malformed | text is right-to-left script | 200 | `c_f5d7ce3d9a97` | ai | 0.880 | BROKE |
| MF08 | malformed | text is 60,000 characters | 200 | `c_4e7332f559c0` | ai | 0.875 | BROKE |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — | HELD |
| RQ02 | malformed | no creator_id | 200 | `c_8157608cbd5b` | unsure | 0.430 | HELD |
| RQ03 | malformed | text is a number | 400 | `—` | — | — | HELD |
| RQ04 | malformed | text is a list | 400 | `—` | — | — | HELD |
| RQ05 | malformed | text is null | 400 | `—` | — | — | HELD |
| RQ06 | malformed | creator_id is an object | 200 | `c_d5ba76918c3a` | human | 0.287 | BROKE |
| RQ07 | malformed | body is a JSON array, not an object | 500 | `—` | — | — | BROKE |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — | HELD |
| RQ09 | malformed | body is empty | 400 | `—` | — | — | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_ef5ab4b246dc` | human | 0.272 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_d73f81ada074` | human | 0.272 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_0dde52810133` | human | 0.272 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_53fdd778a6d5` | human | 0.272 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `c_f59350b79952` | human | 0.272 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — | HELD |

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json
[
  {
    "combined_score": 0.3173,
    "content_id": "c_e26590803d00",
    "creator_id": "attacker_EV01",
    "guess": "human",
    "label": "This text appears likely to have been written by a person.",
    "model_score": 0.1635,
    "status": "decided",
    "style_score": 0.7785,
    "timestamp": "2026-11-05T02:20:46+00:00"
  },
  {
    "combined_score": 0.3268,
    "content_id": "c_78d7f5cad5ed",
    "creator_id": "attacker_EV05",
    "guess": "human",
    "label": "This text appears likely to have been written by a person.",
    "model_score": 0.3212,
    "status": "decided",
    "style_score": 0.3436,
    "timestamp": "2026-11-05T02:20:47+00:00"
  },
  {
    "combined_score": 0.8851,
    "content_id": "c_6c3ff394f7fc",
    "creator_id": "attacker_EV10",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.9792,
    "status": "decided",
    "style_score": 0.603,
    "timestamp": "2026-11-05T02:20:48+00:00"
  },
  {
    "combined_score": 0.7279,
    "content_id": "c_8675be6e032e",
    "creator_id": "attacker_FP02",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.7387,
    "status": "decided",
    "style_score": 0.6954,
    "timestamp": "2026-11-05T02:20:48+00:00"
  },
  {
    "combined_score": 0.7774,
    "content_id": "c_850ce62804d2",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.8051,
    "status": "decided",
    "style_score": 0.6942,
    "timestamp": "2026-11-05T02:20:48+00:00"
  },
  {
    "combined_score": 0.8014,
    "content_id": "c_896799928222",
    "creator_id": "attacker_FP04",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.8329,
    "status": "decided",
    "style_score": 0.707,
    "timestamp": "2026-11-05T02:20:49+00:00"
  },
  {
    "combined_score": 0.8033,
    "content_id": "c_fc4d4c771ada",
    "creator_id": "attacker_FP06",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.8814,
    "status": "decided",
    "style_score": 0.5689,
    "timestamp": "2026-11-05T02:20:49+00:00"
  },
  {
    "combined_score": 0.5433,
    "content_id": "c_83506462c080",
    "creator_id": "attacker_PI04",
    "guess": "unsure",
    "label": "We can't confidently tell whether this text was written by a person or generated by AI.",
    "model_score": 0.4998,
    "status": "decided",
    "style_score": 0.6738,
    "timestamp": "2026-11-05T02:20:50+00:00"
  },
  {
    "combined_score": 0.8798,
    "content_id": "c_f5d7ce3d9a97",
    "creator_id": "attacker_MF07",
    "guess": "ai",
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship.",
    "model_score": 0.9064,
    "status": "decided",
    "style_score": 0.8,
    "timestamp": "2026-11-05T02:20:53+00:00"
  },
  {
    "creator_id": "attacker_flood",
    "event": "rejected",
    "limit": "5 per 1 minute",
    "reason": "rate_limited",
    "status": "rejected",
    "timestamp": "2026-11-05T02:20:54+00:00"
  }
]

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

Six of the eight false-positive attacks were genuine human writing that my service labeled as high-confidence AI. This was the worst outcome because a real writer could be wrongly accused of using AI even though the system cannot actually determine authorship.


---
## Run Log — Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Human false positives | At most 1 of 10 labeled high-confidence AI | 0/10 | 0/10 | 0/10 | MET |
| 2. AI vs. human score spread | AI average at least 0.15 higher than human average | 0.1179 | 0.1179 | 0.1179 | MISSED |
| 3. Label coverage | All 3 label variants reached | 3/3 | 3/3 | 3/3 | MET |
| 4. Valid appeals | 100% move to `under_review` and are logged | 1/1 | 1/1 | 1/1 | MET |
| 5. Missing or empty text | 100% return HTTP 400, none 500 | 4/4 | 4/4 | 4/4 | MET |

For criterion 2, the three AI-written samples averaged **0.6921** and the three human-written samples averaged **0.5742**, giving a difference of **0.1179**. Because my target required a difference of at least **0.15**, this criterion was missed.

**Real output from one trial**

Criteria 1, 2, 3, and 5 below come from `results/run_2026-11-04_1919_before.md`, produced by `run_eval.py::main`. Criterion 4 was tested separately through the real `/submit` → `/appeal` flow and saved in `results/appeal_before.md`.

### Criterion 1 — Human false positives

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6751,
    "model_score": 0.6425,
    "style_score": 0.7729,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5699,
    "model_score": 0.5686,
    "style_score": 0.5739,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4777,
    "model_score": 0.4226,
    "style_score": 0.643,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5915,
    "model_score": 0.6105,
    "style_score": 0.5344,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5889,
    "model_score": 0.534,
    "style_score": 0.7535,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5981,
    "model_score": 0.6615,
    "style_score": 0.4079,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.363,
    "model_score": 0.31,
    "style_score": 0.522,
    "label": "This text appears likely to have been written by a person."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5351,
    "model_score": 0.4751,
    "style_score": 0.715,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.3346,
    "model_score": 0.1745,
    "style_score": 0.8148,
    "label": "This text appears likely to have been written by a person."
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.2885,
    "model_score": 0.1413,
    "style_score": 0.7302,
    "label": "This text appears likely to have been written by a person."
  }
]
```

### Criterion 2 — AI vs. human score spread

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.8172,
    "model_score": 0.8084,
    "style_score": 0.8434
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5942,
    "model_score": 0.5348,
    "style_score": 0.7725
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.665,
    "model_score": 0.6013,
    "style_score": 0.8561
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6751,
    "model_score": 0.6425,
    "style_score": 0.7729
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5699,
    "model_score": 0.5686,
    "style_score": 0.5739
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4777,
    "model_score": 0.4226,
    "style_score": 0.643
  }
]
```

The first three entries are the AI-written samples and average `0.6921`. The last three are human-written samples and average `0.5742`, for a difference of `0.1179`.

### Criterion 3 — Label coverage

```json
[
  {
    "status": 200,
    "guess": "ai",
    "confidence": 0.7198,
    "model_score": 0.7544,
    "style_score": 0.6158,
    "label": "This text shows strong signs of being AI-generated, but this result is not proof of authorship."
  },
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.3653,
    "model_score": 0.4445,
    "style_score": 0.1279,
    "label": "This text appears likely to have been written by a person."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3758,
    "model_score": 0.3489,
    "style_score": 0.4564,
    "label": "We can't confidently tell whether this text was written by a person or generated by AI."
  }
]
```

### Criterion 4 — Valid appeals

```json
{
  "trial": 1,
  "submit_status": 200,
  "content_id": "c_80a4a13f4614",
  "appeal_status": 200,
  "appeal_response": {
    "content_id": "c_80a4a13f4614",
    "message": "Appeal received. This submission is now under review.",
    "status": "under_review"
  },
  "appeal_logged": true
}
```

### Criterion 5 — Missing or empty text

```json
[
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "   "
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_bad_missing_1\"}"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_bad_missing_2\"}"
  }
]
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
