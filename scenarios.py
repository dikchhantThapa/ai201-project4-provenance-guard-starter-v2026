"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sample_text(filename):
    with open(ROOT / "samples" / filename, encoding="utf-8") as f:
        return json.load(f)["text"]
    
OWN_WRITING = [
    "I usually like tea for breakfast, along with french toast and eggs with hollandaise sauce. This is my typical breakfast, and sometimes I eat veggies to keep me healthy.",
    "Germans made up the largest number of migrants from the European. Immigrants included artisans and merchants, but majority of them were farmers and laborers. By 1720s, Germans who had established themselves in the colonies wrote back to their friends and relatives in Germany regarding civil and religious liberties and privileges in the colonies. These letters convinced more Germans to come to the colonies specifically in Pennsylvania where they knew people from their home country.",
    "Before the French and Indian War, American mainland colonies(English) were mostly along the east coast. England also had some colonies further North which is now in Canada. French Empire were along the interior part of North America coming down the St. Lawrence river, the Great lakes, and then Mississippi river. The French mostly engaged in fur trade with Native Americans.",
    "Due to the rise in population in the Colonies, there was internal migration by many of the Colonists pursuing more land. There was an area of land pursued by both the French and the British due to which a war was set off between them now known as the French and Indian war. The naming was given by the Colonists, because from their point of view, that was naming the enemies (French and Indian). Since they were fighting against the French and the many French Indian allies.",
    "When the Colonists first decided to meet in the 1st Continental Congress in 1774, all delegates from the 13 colonies met except Georgia. Their main item of business was to decide what to do about England’s Coercive Acts that it was trying to carry out against Masachusetts and Boston. After this meeting, they denounced England’s Coercive Acts and urged colonies to send militia to protect Massachusetts against these acts.",
    "American Revolution brought some major changes in the American government, however, lives of most Americans stayed the same. The first major change Revolution brought was that the British central government was replaced by the The U.S. national government, meaning US gained independence from Britain. The U.S. also instituted a Republican government at every level of government, this meant that hereditary ruling system was abolished and people were actually elected by citizens.",
    "However, most people experienced continuity than change. Local leaders were still same home raised aristocrats, and the voters were still the same because the poor stayed poor. Revolution also did not bring liberation for African Americans. Slavery was not mentioned in the Declaration of Independence, hence slavery was not abolished after American Revolution.",
    "Women also experienced some gains even though there weren’t major changes. For example, there were gains in education because many women started having access to education. More schools for women were opened following Independence, so many more women got basic education. Political participation and awareness of women also saw an increase even though they did not have much rights.",
    "For example Daughters of Liberty was one female American rights organization who along with other organizations organized boycotts against British goods. There was also a concept of The “Republican Mother” after the revolution. Women taught children the basics of Republicanism at home and taught civic virtue.",
    "Native Americans did not see any improvements after the Revolution, because they greatly lost their lands. It actually left a very negative impact on them. Hence overall, Revolution planted seeds that blossomed over time even though results weren’t visible immediately.",
]


AI_WRITING = [
    (
        "Artificial intelligence systems are increasingly used to automate "
        "repetitive tasks across many industries. These systems can process "
        "large amounts of information quickly, identify patterns, and produce "
        "consistent outputs. Organizations often adopt them to improve "
        "efficiency and reduce the amount of manual work required."
    ),
    (
        "Cloud computing provides organizations with flexible access to "
        "computing resources without requiring them to maintain all hardware "
        "locally. Applications can scale according to demand, while storage "
        "and processing capacity can be adjusted as requirements change. "
        "This model can improve operational flexibility and simplify "
        "infrastructure management."
    ),
    (
        "Software testing is an important part of the development process "
        "because it helps identify defects before a system reaches users. "
        "Automated tests can verify expected behavior repeatedly and provide "
        "developers with faster feedback when code changes. A strong testing "
        "strategy can therefore improve reliability and reduce regressions."
    ),
]


SCENARIOS = [
    {
        "name": "human false positives",
        "criterion": 1,
        "texts": OWN_WRITING,
    },
    {
        "name": "AI human score spread",
        "criterion": 2,
        "texts": AI_WRITING + OWN_WRITING[:3],
    },
    {
        "name": "label coverage",
        "criterion": 3,
        "texts": [
            sample_text("clearly_ai.json"),
            sample_text("clearly_human.json"),
            sample_text("borderline.json"),
        ],
    },
    {
        "name": "missing or empty text",
        "criterion": 5,
        "bodies": [
            {"text": "", "creator_id": "eval_bad_empty_1"},
            {"text": "   ", "creator_id": "eval_bad_empty_2"},
            {"creator_id": "eval_bad_missing_1"},
            {"creator_id": "eval_bad_missing_2"},
        ],
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict — bodies are whole "
                        f"request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
