"""Claim-level fact checking for report drafts.

Every figure in a draft is read the way a client would read it: which channel
it is about, which metric, which month, and whether it is a level, a change,
a share or a target. The verifier then looks for a fact on the sheet that
matches all of that, not just the number. A correct number attached to the
wrong channel, the wrong month or the wrong direction is an error.

Citations such as [F12] are treated as hints: a correct sentence with a wrong
or missing citation is accepted (and its provenance corrected), and a cited
fact never excuses a sentence that says something else.

Sentences about the future ("next month we will…", "we recommend…") are not
claims about the data. Their figures are listed for the reviewer, unchecked.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Optional

from .facts import FLAT_BAND, Fact, FactSheet, singular
from .model import CHANNELS, METRICS, MONTHS, TOTAL, TOTAL_WORDS, channel_label

COMBINED = "__combined__"   # several channels named together: their sum is not on the sheet

# A claimed direction contradicts the data only when the change is at least this big.
DIRECTION_SLACK = 1.0      # % — "rose" when the figure fell 0.4% is noise, not a lie
FLAT_CLAIM_LIMIT = 5.0     # % — "held steady" is wrong once the change passes this


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #
@dataclass
class Issue:
    kind: str           # unsupported | wrong_direction | wrong_scope | wrong_metric | wrong_period | wrong_kind
    quote: str          # the figure or phrase as written
    sentence: str
    message: str        # for the reviewer
    hint: str           # for the drafter: names the correct fact and figure
    start: int = -1     # offsets into the draft
    end: int = -1
    expected: Optional[str] = None      # id of the fact the sentence should have used

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Claim:
    quote: str
    start: int
    end: int
    status: str                         # verified | issue | forward_looking | unchecked
    fact_id: Optional[str] = None       # the fact that backs it (verified claims)
    cited: Optional[str] = None         # the citation the drafter gave, if any

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verification:
    claims: list[Claim] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)   # non-blocking (e.g. corrected citations)

    @property
    def ok(self) -> bool:
        return not self.issues

    @property
    def checked(self) -> int:
        return sum(1 for c in self.claims if c.status in ("verified", "issue"))

    def to_dict(self) -> dict:
        return {"ok": self.ok, "checked": self.checked,
                "claims": [c.to_dict() for c in self.claims],
                "issues": [i.to_dict() for i in self.issues], "notes": list(self.notes)}

    @classmethod
    def from_dict(cls, d: dict) -> "Verification":
        return cls(claims=[Claim(**c) for c in d.get("claims", [])],
                   issues=[Issue(**i) for i in d.get("issues", [])], notes=list(d.get("notes", [])))

    def feedback_for_drafter(self) -> str:
        if self.ok:
            return ""
        lines = ["The fact-checker rejected these statements. Fix each one using only the fact sheet:"]
        for n, i in enumerate(self.issues, 1):
            lines.append(f"{n}. \"{i.sentence.strip()}\" — {i.hint}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #
def _alt(words) -> str:
    return "|".join(sorted({re.escape(w) for w in words}, key=len, reverse=True))


def _phrase_rx(words) -> re.Pattern:
    return re.compile(rf"(?<![\w-])(?:{_alt(words)})(?![\w-])", re.I)


_SCOPE_WORDS: dict[str, frozenset[str]] = {}
for _c in CHANNELS.values():
    for _w in _c.words:
        if _w in ("other",):
            continue
        _SCOPE_WORDS[_w] = _SCOPE_WORDS.get(_w, frozenset()) | {_c.slug}
for _w in TOTAL_WORDS:
    _SCOPE_WORDS[_w] = frozenset({TOTAL})
_SCOPE_RX = _phrase_rx(_SCOPE_WORDS)

_GENERIC_CPA = ("enquiry", "inquiry", "lead", "conversion", "booking", "order", "sale", "result",
                "acquisition", "sign-up", "signup", "appointment", "call", "customer", "patient",
                "client", "member", "key event")


@lru_cache(maxsize=32)
def _metric_vocab(conversion_label: str) -> tuple[re.Pattern, dict[str, frozenset[str]]]:
    words: dict[str, frozenset[str]] = {}

    def add(w: str, *metrics: str) -> None:
        words[w.lower()] = words.get(w.lower(), frozenset()) | set(metrics)

    for m in METRICS.values():
        for w in m.words:
            if w in ("return", "converted", "conversion"):
                continue
            add(w, m.key)
    add("conversion", "conversions", "conv_rate")
    add("converted", "conversions", "conv_rate")
    label = conversion_label.strip().lower() or "conversions"
    one = singular(label)
    add(label, "conversions")
    add(one, "conversions")
    for noun in set(_GENERIC_CPA) | {one, one.split(" ")[-1]}:
        add(f"cost per {noun}", "cpa")
        add(f"per {noun}", "cpa")
        add(f"cost-per-{noun}", "cpa")
    add(f"{one} rate", "conv_rate")
    add("per click", "cpc")
    add("cost per click", "cpc")
    add("return on ad spend", "roas")
    add("return on spend", "roas")
    add("places", "avg_position")
    add("spots", "avg_position")
    return _phrase_rx(words), words


_TARGET_RX = re.compile(r"(?<![\w-])(?:target|targets|goal|goals|kpi|objective)(?![\w-])", re.I)
_SHARE_RX = re.compile(r"(?<![\w-])(?:share|shares|accounted for|account for|accounting for|made up|"
                       r"makes up|making up|of all|of the total|of total|of overall|of every|"
                       r"proportion|portion|responsible for)(?![\w-])", re.I)
_CHANGE_NOUN_RX = re.compile(r"(?<![\w-])(?:increase|rise|growth|uplift|jump|decrease|decline|drop|fall|"
                             r"dip|reduction|change|improvement|swing|lift|gain)\s+of\s*$", re.I)

_UP = ("beat", "beating", "exceeded", "exceeding", "surpassed", "topped", "above", "rose", "rise", "rises", "rising", "risen", "grew", "grow", "grows", "growing", "grown",
       "growth", "increase", "increased", "increases", "increasing", "up", "climbed", "climb",
       "climbing", "jumped", "jump", "jumps", "gained", "gain", "gains", "higher", "boost",
       "boosted", "surged", "surge", "lifted", "lift", "uplift", "added", "expanded", "more",
       "ahead", "upturn", "peaked", "doubled", "tripled", "trebled", "quadrupled")
_DOWN = ("missed", "missing", "below", "fell", "fall", "falls", "falling", "fallen", "dropped", "drop", "drops", "dropping",
         "declined", "decline", "declines", "declining", "decrease", "decreased", "decreasing",
         "down", "lower", "fewer", "less", "slipped", "slip", "dipped", "dip", "dips", "shrank",
         "shrunk", "reduced", "reduction", "cut", "eased", "softened", "slowed", "contracted",
         "lost", "behind", "downturn", "halved", "slid", "slumped", "tumbled")
_FLAT = ("flat", "steady", "stable", "unchanged", "held", "maintained", "static")
_GOOD = ("improved", "improve", "improving", "improvement", "better", "stronger", "strengthened")
_BAD = ("worse", "worsened", "weaker", "weakened", "deteriorated", "deteriorating")
_DIR_WORDS = {**{w: "up" for w in _UP}, **{w: "down" for w in _DOWN}, **{w: "flat" for w in _FLAT},
              **{w: "good" for w in _GOOD}, **{w: "bad" for w in _BAD}}
_DIR_RX = _phrase_rx(_DIR_WORDS)
_NEGATION_RX = re.compile(r"(?:\bnot|n't|\bno|\bnever|\bwithout|\bhardly|\bbarely)\s+(?:\w+\s+)?$", re.I)
_NOT_DIRECTION_RX = re.compile(r"(?:\bset|\bfollow|\bsign|\bback|\bmake|\bmade|\bopt|\bwind|\bend|\bsum)\s*$", re.I)

_FUTURE_RX = re.compile(r"(?<![\w-])(?:next month|next quarter|next year|will|we'll|we will|going to|"
                        r"recommend\w*|suggest\w*|propos\w*|plan to|plans to|planning to|aim to|aims to|"
                        r"aiming to|intend\w*|forecast\w*|projected|projection\w*|should|could|would|"
                        r"if we|hope to|expect to|expected to)(?![\w-])", re.I)

_HEDGE_RX = re.compile(r"(?<![\w-])(just under|just over|more than|less than|fewer than|upwards of|"
                       r"in excess of|at least|up to|close to|in the region of|an estimated|nearly|"
                       r"almost|around|about|roughly|approximately|approx\.?|circa|c\.|some|over|under|"
                       r"above|below|exceeding|north of|shy of|well over|well under)\s*$", re.I)
_HEDGE_KIND = {"just under": "below", "almost": "below", "nearly": "below", "shy of": "below",
               "close to": "approx", "less than": "under", "fewer than": "under", "under": "under",
               "below": "under", "well under": "under", "up to": "upto",
               "just over": "over", "more than": "over", "upwards of": "over", "in excess of": "over",
               "at least": "atleast", "over": "over", "above": "over", "exceeding": "over",
               "north of": "over", "well over": "over"}

_QUAL_RX = re.compile(r"(?<![\w-])(?:(nearly|almost|more than|over|just over|roughly|about|around|"
                      r"well over|close to)\s+)?(doubled|tripled|trebled|quadrupled|halved)(?![\w-])", re.I)
_QUAL_RATIO = {"doubled": 2.0, "tripled": 3.0, "trebled": 3.0, "quadrupled": 4.0, "halved": 0.5}
_FRACTION_RX = re.compile(r"(?<![\w-])(?:(nearly|almost|more than|over|just over|just under|roughly|about|"
                          r"around|under|less than|close to)\s+)?(half|a third|one third|a quarter|"
                          r"one quarter|two thirds|two-thirds|three quarters|three-quarters|"
                          r"the majority|a fifth|one fifth)\s+of(?![\w-])", re.I)
_FRACTION = {"half": 50.0, "a third": 100 / 3, "one third": 100 / 3, "a quarter": 25.0,
             "one quarter": 25.0, "two thirds": 200 / 3, "two-thirds": 200 / 3,
             "three quarters": 75.0, "three-quarters": 75.0, "a fifth": 20.0, "one fifth": 20.0}

_NUM_RX = re.compile(r"""
    (?<![\w.,£$€/:])
    (?P<sign>[+\-−–](?=[£$€]?\d))?
    (?P<cur>[£$€])?
    (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
    (?P<suf>(?:k|K|m|bn)(?![\w])|\s(?:million|thousand|billion)(?![\w]))?
    (?P<unit>\s?%|\s(?:per\s?cent|percent)(?![\w])|\s?(?:pp|pts)(?![\w])|
       \s(?:percentage\s+points?|points?)(?![\w])|[x×](?![\w])|\s×|\stimes(?![\w]))?
""", re.X | re.I)
_SCALE = {"k": 1e3, "m": 1e6, "bn": 1e9, "thousand": 1e3, "million": 1e6, "billion": 1e9}
_SPAN_AFTER_RX = re.compile(r"^\s*(?:-|\s)?\s*(?:days?|weeks?|months?|years?|hours?|hrs?|minutes?|mins?|"
                            r"seconds?|secs?|quarters?|nights?)\b(?![- ](?:on|over)[- ](?:month|year|week))", re.I)
_SKIP_BEFORE_RX = re.compile(r"(?:\btop|\bpage|\bstep|\bphase|\bweek|\bday|\btier|\blevel|\bversion|"
                             r"\bno\.|\bnumber|#|\bsection|\bfigure|\btable|\bchart|\bslide|\bitem|"
                             r"\bpriority|\bround|\bstage|\bwave)\s*$", re.I)
_MONTH_NAMES = MONTHS + tuple(m[:3] for m in MONTHS) + ("Sept",)
_MONTH_RX = re.compile(rf"\b(?:{'|'.join(_MONTH_NAMES)})\.?\b")
_EVERY_POUND_RX = re.compile(r"([£$€])(\d+(?:\.\d+)?)\s+(?:back\s+|in\s+(?:revenue|sales|return|income)\s+)?(?:for|per)\s+every\s+"
                             r"(?:[£$€]1(?:\.00)?|dollar|pound|euro)\b(?:\s+(?:of\s+(?:ad\s+)?(?:spend|budget)|spent|invested))?")

_CAUSE_RX = re.compile(r"(?:mainly|mostly|largely|primarily|partly|chiefly|driven|thanks to|due to|led by|"
                       r"because of)\b", re.I)
_CHG_NOUNS = (r"(?:increase|rise|growth|jump|drop|fall|decline|decrease|uplift|gain|reduction|improvement|"
              r"lift|dip|uptick|boost|swing)")
_ADV = r"(?:(?:year|month)[- ](?:on|over)[- ](?:year|month)|yoy|mom|y/y|m/m)"
_ADV_RX = re.compile(_ADV, re.I)
_CHG_AFTER_RX = re.compile(rf"\s*(?:{_ADV}\s+)?{_CHG_NOUNS}\b", re.I)
_RANGE_RX = re.compile(
    r"(?<![\w.,£$€/:-])(?P<c1>[£$€])?(?P<n1>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?P<s1>k)?\s?[-–—]\s?"
    r"(?P<c2>[£$€])?(?P<n2>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?P<s2>k)?(?P<u>\s?%)?(?![\w])|"
    r"(?<![\w-])between\s+(?P<c3>[£$€])?(?P<n3>\d[\d,]*(?:\.\d+)?)(?P<s3>k)?\s+and\s+(?P<c4>[£$€])?"
    r"(?P<n4>\d[\d,]*(?:\.\d+)?)(?P<s4>k)?(?P<u2>\s?%)?(?![\w])", re.I)
_EVERY_DOLLAR_RX = re.compile(
    r"\bevery\s+(?:dollar|pound|euro|[£$€]1(?:\.00)?)\b[^.;]*?\b(?:returned|generated|brought in|produced|earned|made|"
    r"yielded|delivered)\s+(?:about\s+|around\s+|roughly\s+)?(?P<c>[£$€])(?P<n>\d+(?:\.\d+)?)", re.I)
_COMPARE_CUE_RX = re.compile(r"(?:\bvs\.?|\bversus|\bagainst|\bcompared (?:with|to)|\bthan|\bcf\.?)"
                             r"(?:\s+(?:the|a))?\s*$", re.I)
_CHANNEL_GAP_RX = re.compile(r"\s*(?:\w+\s+){0,2}?(?:from|for|on|at|in|with|by|via|through)\s+(?:the\s+|our\s+|its\s+)?$", re.I)
_FUTURE_HEADING_RX = re.compile(r"next (?:month|steps|quarter)|recommend|plan|outlook|priorit|roadmap|looking ahead|"
                                r"going forward|what.?s next|focus|proposal|opportunit|actions?$", re.I)
_UNTRACKED_RX = re.compile(r"(?<![\w-])(?:impression share|search impression share|quality score|bounce rate|engagement rate|"
                           r"engaged sessions?|average order value|aov|lifetime value|ltv|churn|retention|open rate|"
                           r"unsubscribe\w*|page speed|core web vitals|domain (?:rating|authority)|backlinks?|"
                           r"referring domains|keyword rankings?|top[- ]\d+ (?:keywords|rankings))(?![\w-])", re.I)
_STOP_NOUNS = frozenset("of to in on at and or for from with by this last the a an as vs versus than compared per "
                        "out up down so but which while over month months year years is was were are it its their "
                        "our your we they that these those has have had".split())
_CITE_RX = re.compile(r"\[\s*(F\d+(?:\s*[,;/]\s*F?\d+)*)\s*\]")
_CLAUSE_RX = re.compile(r"[;:()]|,(?!\d)|\s[–—-]\s|(?<![\w-])(?:while|whereas|but|although|though|and|"
                        r"yet|however|which|meanwhile)(?![\w-])", re.I)
_ABBREV = ("vs", "e.g", "i.e", "approx", "c", "etc", "inc", "ltd", "no", "mr", "mrs", "ms", "dr", "st")


# --------------------------------------------------------------------------- #
# Text preparation: mask markdown and citations without moving offsets
# --------------------------------------------------------------------------- #
def _mask(text: str) -> tuple[str, list[tuple[int, int, list[str]]]]:
    cites: list[tuple[int, int, list[str]]] = []
    chars = list(text)

    def blank(a: int, b: int) -> None:
        for i in range(a, b):
            if chars[i] != "\n":
                chars[i] = " "

    for m in _CITE_RX.finditer(text):
        ids = ["F" + x.lstrip("Ff") for x in re.split(r"\s*[,;/]\s*", m.group(1))]
        cites.append((m.start(), m.end(), ids))
        blank(m.start(), m.end())
    masked = "".join(chars)
    for rx in (re.compile(r"^\s{0,3}#{1,6}\s", re.M), re.compile(r"^\s*(?:[-*+•]|\d{1,2}[.)])\s", re.M),
               re.compile(r"^\s*>\s?", re.M), re.compile(r"\*\*|__|(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)"),
               re.compile(r"\|")):
        for m in rx.finditer(masked):
            blank(m.start(), m.end())
        masked = "".join(chars)
    return masked, cites


@dataclass
class _Sentence:
    start: int
    end: int
    text: str
    inherited: Optional[frozenset]      # scope carried over from the previous sentence or heading
    future: bool = False                # sits under a "Next month" / "Recommendations" heading


def _sentences(masked: str, raw: str) -> list[_Sentence]:
    out: list[_Sentence] = []
    heading_scope: Optional[frozenset] = None
    heading_future = False
    pos = 0
    blocks: list[tuple[int, int, bool]] = []      # (start, end, is_heading)
    para_start = None
    for line in raw.splitlines(keepends=True):
        a, b = pos, pos + len(line)
        pos = b
        stripped = line.strip()
        is_heading = bool(re.match(r"^#{1,6}\s", stripped))
        is_bullet = bool(re.match(r"^(?:[-*+•]|\d{1,2}[.)])\s", stripped))
        if not stripped or is_heading or is_bullet:
            if para_start is not None:
                blocks.append((para_start, a, False))
                para_start = None
            if is_heading:
                blocks.append((a, b, True))
            elif is_bullet:
                para_start = a
            continue
        if para_start is None:
            para_start = a
    if para_start is not None:
        blocks.append((para_start, len(raw), False))

    for a, b, is_heading in blocks:
        seg = masked[a:b]
        if is_heading:
            scopes = _scopes_in(seg)
            heading_scope = frozenset().union(*scopes) if scopes else None
            heading_future = bool(_FUTURE_HEADING_RX.search(seg))
            continue
        carried = heading_scope
        starts = [0] + [m.end() for m in re.finditer(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9£$€+−-])", seg)
                        if not _is_abbrev(seg, m.start())]
        bounds = list(zip(starts, starts[1:] + [len(seg)]))
        for s, e in bounds:
            text = seg[s:e]
            if not text.strip():
                continue
            out.append(_Sentence(a + s, a + e, text, carried, heading_future))
            sc = _scopes_in(text)
            if sc:
                carried = frozenset().union(*sc)
    return out


def _is_abbrev(seg: str, dot_pos: int) -> bool:
    j = seg.rfind(".", 0, dot_pos + 1)
    k = j - 1
    while k >= 0 and (seg[k].isalpha() or seg[k] == "."):
        k -= 1
    word = seg[k + 1:j].lower()
    return word in _ABBREV


def _scopes_in(text: str) -> list[frozenset]:
    return [s for _, _, s in _scope_hits(text)]


def _scope_hits(text: str) -> list[tuple[int, int, frozenset]]:
    hits = []
    for m in _SCOPE_RX.finditer(text):
        w = m.group(0).lower()
        before, after = text[:m.start()].lower(), text[m.end():].lower()
        if w == "total" and re.search(r"\ba\s+$", before) and after.startswith(" of"):
            continue                            # "a total of 143"
        if w in ("total", "overall", "combined") and re.search(r"\bof\s+(?:the\s+|all\s+)?$", before):
            continue                            # "47.7% of the total" names the denominator, not the scope
        if w == "direct" and re.match(r"\s+(?:result|response|consequence|comparison|link)", text[m.end():], re.I):
            continue
        hits.append((m.start(), m.end(), _SCOPE_WORDS[w]))
    # "On social, organic sessions rose…" — a bare "organic"/"paid" qualifies the platform named nearby
    words = [text[a:b].lower() for a, b, _ in hits]
    if any(w in ("social", "social media") for w in words):
        hits = [(a, b, frozenset({"organic_social"}) if text[a:b].lower() == "organic" else sc)
                for a, b, sc in hits]
    return hits


# --------------------------------------------------------------------------- #
# Number mentions
# --------------------------------------------------------------------------- #
@dataclass
class _Mention:
    start: int          # within the sentence
    end: int
    raw: str
    value: float        # absolute, scaled
    unit: str           # currency | percent | points | ratio | count
    sign: Optional[int]
    tol: float
    hedge: Optional[str] = None
    kinds: Optional[set] = None         # forced kinds (qualitative / converted mentions)
    hedge_band: Optional[tuple[float, float]] = None    # explicit acceptable [lo, hi] for qualitative claims
    cur: str = ""                                        # currency symbol written with the figure
    rng: Optional[tuple[float, float]] = None            # "4–5%": acceptable [lo, hi]
    force_metrics: Optional[frozenset] = None            # "$4 for every $1" is always ROAS


def _mentions(s: str) -> list[_Mention]:
    out: list[_Mention] = []
    skip_spans: list[tuple[int, int]] = []
    for m in _EVERY_POUND_RX.finditer(s):
        v = float(m.group(2))
        dec = len(m.group(2).split(".")[1]) if "." in m.group(2) else 0
        out.append(_Mention(m.start(), m.end(), m.group(0), v, "ratio", None, 0.5 * 10 ** -dec + 1e-9,
                            force_metrics=frozenset({"roas"})))
        skip_spans.append((m.start(), m.end()))
    for m in _EVERY_DOLLAR_RX.finditer(s):
        v = float(m.group("n"))
        dec = len(m.group("n").split(".")[1]) if "." in m.group("n") else 0
        out.append(_Mention(m.start("c"), m.end("n"), m.group(0), v, "ratio", None, 0.5 * 10 ** -dec + 1e-9,
                            force_metrics=frozenset({"roas"})))
        skip_spans.append((m.start(), m.end()))
    for m in _RANGE_RX.finditer(s):
        g = m.groupdict()
        n1, n2 = (g["n1"], g["n2"]) if g["n1"] else (g["n3"], g["n4"])
        c = (g["c1"] or g["c2"] or g["c3"] or g["c4"] or "")
        k1, k2 = (g["s1"], g["s2"]) if g["n1"] else (g["s3"], g["s4"])
        pct = bool(g["u"] or g["u2"])
        a, b = m.start(), m.end()
        if re.fullmatch(r"(19[9]\d|20\d\d)", n1.replace(",", "")) or re.fullmatch(r"(19[9]\d|20\d\d)", n2.replace(",", "")):
            continue
        if not c and not pct and (_SPAN_AFTER_RX.match(s[b:]) or re.match(rf"\s*(?:{'|'.join(_MONTH_NAMES)})\b", s[b:])):
            continue
        if g["n1"] and not (c or pct or k1 or k2) and float(n1.replace(",", "")) >= float(n2.replace(",", "")):
            continue                                   # "1-30", "10-5": not a range of results
        lo = float(n1.replace(",", "")) * (1000 if (k1 or k2) else 1)
        hi = float(n2.replace(",", "")) * (1000 if (k2 or k1) else 1)
        dec = max(len(x.split(".")[1]) if "." in x else 0 for x in (n1, n2))
        out.append(_Mention(a, b, m.group(0).strip(), hi, "currency" if c else ("percent" if pct else "count"),
                            None, 0.5 * 10 ** -dec + 1e-9, None, None, None, c, (min(lo, hi), max(lo, hi))))
        skip_spans.append((a, b))
    for m in _NUM_RX.finditer(s):
        a, b = m.start(), m.end()
        if any(x <= a < y for x, y in skip_spans):
            continue
        num = m.group("num")
        cur, suf, unit_raw, sign_raw = m.group("cur"), m.group("suf"), m.group("unit"), m.group("sign")
        nxt = s[b:b + 1]
        if nxt.isalpha() or (nxt in "-–" and s[b + 1:b + 2].isalpha()) or nxt == ":":
            continue                                    # 4G, 30th, 30-day, 9:30
        after, before = s[b:], s[:a]
        if not cur and not unit_raw and not suf:
            if _SPAN_AFTER_RX.match(after):
                continue                                # 30 days, 12 months
            if _SKIP_BEFORE_RX.search(before):
                continue                                # top 10, page 2
            if re.search(rf"\b(?:{'|'.join(_MONTH_NAMES)})\.?\s*$", before) or \
               re.match(rf"\s*(?:st|nd|rd|th)?\s*(?:of\s+)?(?:{'|'.join(_MONTH_NAMES)})\b", after):
                continue                                # 30 September / September 30
            if re.fullmatch(r"(19[9]\d|20\d\d|2100)", num):
                continue                                # a year
            if re.search(r"\b[QH]\s*$|\bFY\s*$", before):
                continue
        scale = 1.0
        if suf:
            scale = _SCALE[suf.strip().lower()]
        v = float(num.replace(",", "")) * scale
        dec = len(num.split(".")[1]) if "." in num else 0
        tol = 0.5 * 10 ** -dec * scale
        if scale > 1:
            tol = min(tol, 0.03 * v)          # "$5k" is not a fair rounding of $5,480
        if dec == 0 and scale == 1 and v >= 1000:
            digits = num.replace(",", "")
            tz = len(digits) - len(digits.rstrip("0"))
            if tz:
                tol = max(tol, min(0.5 * 10 ** tz, 0.02 * v))
        u = (unit_raw or "").strip().lower()
        if cur:
            unit = "currency"
        elif u in ("%", "per cent", "percent", "percent") or u.replace(" ", "") == "percent":
            unit = "percent"
        elif u in ("pp", "pts") or u.startswith("percentage") or u.startswith("point"):
            unit = "points"
        elif u in ("x", "×", "times"):
            unit = "ratio"
        else:
            unit = "count"
        sign = None
        if sign_raw:
            sign = 1 if sign_raw == "+" else -1
        hedge = None
        hm = _HEDGE_RX.search(before)
        if hm:
            hw = hm.group(1).lower()
            hedge = _HEDGE_KIND.get(hw, "approx")
        out.append(_Mention(a, b, m.group(0).strip(), v, unit, sign, tol + 1e-9, hedge, cur=cur or ""))
    out.sort(key=lambda x: x.start)
    return out


def _value_ok(stated: float, truth: float, tol: float, hedge: Optional[str]) -> bool:
    if hedge is None:
        return abs(truth - stated) <= tol
    if hedge == "approx":
        return abs(truth - stated) <= max(tol, 0.05 * abs(stated))
    if hedge == "below":           # nearly / almost / just under
        return stated * 0.9 - tol <= truth <= stated + tol
    if hedge == "under":
        return stated * 0.67 - tol <= truth <= stated + tol
    if hedge == "upto":
        return truth <= stated + tol
    if hedge in ("over", "atleast"):
        return stated - tol <= truth <= stated * 1.5 + tol
    return abs(truth - stated) <= tol


# --------------------------------------------------------------------------- #
# Reading a sentence
# --------------------------------------------------------------------------- #
class _Reader:
    """Everything the verifier needs to know about one sentence."""

    def __init__(self, sent: _Sentence, sheet: FactSheet, metric_rx: re.Pattern, metric_words: dict):
        self.sent = sent
        self.s = sent.text
        self.sheet = sheet
        self.scope_hits = _scope_hits(self.s)
        self.metric_hits = [(m.start(), m.end(), metric_words[m.group(0).lower()])
                            for m in metric_rx.finditer(self.s)]
        self.dir_hits = self._directions()
        cuts = [m for m in _CLAUSE_RX.finditer(self.s) if not self._joins_channels(m)]
        self.bounds = sorted({0, len(self.s)} | {m.start() for m in cuts} | {m.end() for m in cuts})
        self.periods = self._period_words()

    def _joins_channels(self, m: re.Match) -> bool:
        """'Google Ads and Meta', 'paid, organic and email': a list of channels is one phrase."""
        if m.group(0).strip().lower() != "and":
            return False
        before = any(abs(b - m.start()) <= 1 for _, b, _ in self.scope_hits) or \
            re.search(r"(?:paid|organic)\s*$", self.s[:m.start()], re.I)
        after = any(0 <= a - m.end() <= 1 for a, _, _ in self.scope_hits) or \
            re.match(r"\s*(?:paid|organic)\b", self.s[m.end():], re.I)
        return bool(before and after)

    def _channel_list(self, hit_index: int) -> list[int]:
        """Indexes of scope hits forming a list with the given one ('A, B and C')."""
        idx = [hit_index]
        i = hit_index
        while i > 0 and re.fullmatch(r"\s*(?:,|and|&|or|,\s*and)\s*(?:the\s+)?",
                                     self.s[self.scope_hits[i - 1][1]:self.scope_hits[i][0]], re.I):
            i -= 1
            idx.insert(0, i)
        j = hit_index
        while j + 1 < len(self.scope_hits) and re.fullmatch(
                r"\s*(?:,|and|&|or|,\s*and)\s*(?:the\s+)?",
                self.s[self.scope_hits[j][1]:self.scope_hits[j + 1][0]], re.I):
            j += 1
            idx.append(j)
        return idx

    def _resolve_scope_hit(self, k: int) -> frozenset:
        lst = self._channel_list(k)
        if len(lst) >= 2 and not any(
                re.search(r"\b(?:and|or)\b|&", self.s[self.scope_hits[i][1]:self.scope_hits[i + 1][0]], re.I)
                for i in lst[:-1]):
            lst = [k]
        if len(lst) < 2:
            return self.scope_hits[k][2]
        union = frozenset().union(*(self.scope_hits[i][2] for i in lst))
        if TOTAL in union:
            return frozenset({TOTAL})
        ca, cb = self.clause(self.scope_hits[k][0])
        present = {f.scope for f in self.sheet.facts if f.scope != TOTAL}
        if re.search(r"(?<![\w-])(?:total|combined|together|altogether|in all|overall)(?![\w-])",
                     self.s[ca:cb], re.I) or present <= union:
            return frozenset({TOTAL})
        return union | {COMBINED}

    # -------------------------------------------------------------- clauses
    def clause(self, pos: int) -> tuple[int, int]:
        a = max((b for b in self.bounds if b <= pos), default=0)
        b = min((b for b in self.bounds if b > pos), default=len(self.s))
        # extend over the boundary word itself so "and" etc. don't make empty clauses
        return a, b

    # -------------------------------------------------------------- direction words
    def _directions(self) -> list[tuple[int, int, str]]:
        hits = []
        for m in _DIR_RX.finditer(self.s):
            w = m.group(0).lower()
            before, after = self.s[:m.start()], self.s[m.end():]
            if _NEGATION_RX.search(before):
                continue
            if w == "up" and (_NOT_DIRECTION_RX.search(before) or re.match(r"\s+to\s+[£$€]?\d", after)):
                continue
            if w in ("more", "less", "fewer"):
                if re.match(r"\s+than\s+[£$€]?\d", after) or re.match(r"\s+than\s+(?:a|an|one|two|half)\b", after):
                    continue
                if not (re.search(r"[\d%]\s*$", before) or self._metric_right_after(m.end())):
                    continue
            if w == "held" and re.match(r"\s+(?:back|up|off)\b", after):
                continue
            if w in ("ahead", "behind") and not re.match(r"\s+of\s+(?:the\s+|your\s+|our\s+|its\s+)?(?:monthly\s+|agreed\s+)?(?:target|goal|plan|forecast)", after, re.I):
                continue
            if w == "cut" and re.search(r"\b(?:a|the)\s+$", before):
                continue
            if w in ("beat", "beating", "exceeded", "exceeding", "surpassed", "topped", "missed", "missing",
                     "above", "below") and not re.search(r"\b(?:target|goal)\b", self.s, re.I):
                continue                  # only direction words when talking about the target
            if w in ("above", "below") and not re.match(
                    r"\s+(?:the\s+|our\s+|your\s+|its\s+)?(?:monthly\s+)?(?:target|goal)", after, re.I):
                continue
            hits.append((m.start(), m.end(), _DIR_WORDS[w]))
        return hits

    def _metric_right_after(self, pos: int) -> bool:
        window = self.s[pos:pos + 30]
        for a, _, _ in self.metric_hits:
            if pos <= a <= pos + 30 and len(re.findall(r"\w+", self.s[pos:a])) <= 2:
                return True
        return bool(re.match(r"\s+(?:\w+\s+)?(?:" + _alt(self.sheet.conversion_label.split()) + ")", window, re.I))

    # -------------------------------------------------------------- period words
    def _period_words(self) -> list[tuple[int, int, str]]:
        """(start, end, mode) with mode current | previous | year_ago."""
        sh = self.sheet
        cur_y, cur_m = (int(x) for x in sh.period.split("-"))
        prev_y, prev_m = (cur_y, cur_m - 1) if cur_m > 1 else (cur_y - 1, 12)
        cur_n, prev_n = MONTHS[cur_m - 1], MONTHS[prev_m - 1]
        cur_a = "Sept?" if cur_n == "September" else cur_n[:3]
        prev_a = "Sept?" if prev_n == "September" else prev_n[:3]
        # phrases (any case) first, then month names (capitalised only: "May" vs "may")
        specs = [
            (r"year[- ]on[- ]year|year[- ]over[- ]year|yoy|y/y|last year|a year ago|a year earlier|"
             r"the year before|same month last year|this time last year|the same month a year ago|"
             rf"last {cur_n}|prior year|the prior year|previous year|the previous year|py|prior[- ]year|"
             rf"same period last year|(?:in|than in|vs\.?|versus|from) {cur_y - 1}", "year_ago", re.I),
            (r"month[- ]on[- ]month|month[- ]over[- ]month|mom|m/m|last month|the previous month|"
             r"previous month|prior month|the month before", "previous", re.I),
            (r"this month|this period", "current", re.I),
            (rf"(?:{cur_n}|{cur_a})\.? {cur_y - 1}", "year_ago", 0),
            (rf"(?:{prev_n}|{prev_a})\.?(?: {prev_y})?", "previous", 0),
            (rf"(?:{cur_n}|{cur_a})\.?(?: {cur_y})?", "current", 0),
        ]
        hits: list[tuple[int, int, str]] = []
        for rx, mode, flags in specs:
            for m in re.finditer(rf"(?<![\w-])(?:{rx})(?:'s)?(?![\w-])", self.s, flags):
                if any(a <= m.start() < b or m.start() <= a < m.end() for a, b, _ in hits):
                    continue
                hits.append((m.start(), m.end(), mode))
        return sorted(hits)

    def _is_comparison_phrase(self, a: int) -> bool:
        before = self.s[:a].lower()
        return bool(re.search(r"(?:than|vs\.?|versus|against|compared (?:with|to)|on|from|over|relative to|"
                              r"ahead of|behind|since)\s+(?:the\s+)?$", before))

    def figure_period(self, m: _Mention) -> tuple[str, bool]:
        """Which month a level (value) refers to; second item: was it explicit."""
        before = self.s[:m.start]
        stripped = _HEDGE_RX.sub("", before).rstrip()
        ca, _ = self.clause(m.start)
        if _COMPARE_CUE_RX.search(stripped) and self._channel_follows(m):
            return "current", False        # "$44.20, compared to $40.00 on paid social": same month, other channel
        from_move = re.search(r"\bfrom(?:\s+(?:last month's|last year's|\w+'s|the|a))?\s*$", stripped, re.I) and (
            any(ca <= x and y <= m.start for x, y, _ in self.dir_hits) or
            re.match(r"\s*(?:\w+\s+){0,2}to\s+[£$€]?\d", self.s[m.end:]))
        if from_move or re.search(r"(?:\bvs\.?|\bversus|\bagainst|\bthan|\bcompared (?:with|to)|\bpreviously|"
                     r"\bbase of)(?:\s+(?:last month's|last year's|the previous month's|"
                     r"a year ago's|\w+'s|the|a))?\s*$", stripped, re.I):
            return ("year_ago" if self.comparison(m) == "yoy" else "previous"), True
        ca, cb = self.clause(m.start)
        nums_after = [x for x in _NUM_RX.finditer(self.s, m.end)]
        next_num = nums_after[0].start() if nums_after else len(self.s)
        trailing = [mode for a, b, mode in self.periods
                    if m.end <= a < min(cb, next_num) and not self._is_comparison_phrase(a)
                    and not _ADV_RX.fullmatch(self.s[a:b])]
        if trailing:
            return trailing[0], True                  # "came in at 10,170 in August"
        if re.search(r"(?:\bto|\bat|\breached|\breaching|\bhit|\bhitting|\btotalled|\btotaled|\btotalling|"
                     r"\btotaling)\s*$", stripped, re.I):
            return "current", True
        # nearest month word, ignoring comparison phrases ("than last month") and words beyond another number
        nums_after = [x for x in _NUM_RX.finditer(self.s, m.end)]
        next_num = nums_after[0].start() if nums_after else len(self.s)
        ca, cb = self.clause(m.start)
        best = None
        for a, b, mode in self.periods:
            if self._is_comparison_phrase(a) or _ADV_RX.fullmatch(self.s[a:b]):
                continue                    # "month over month" describes a change, not which month a level is from
            if a >= m.end and a > next_num:
                continue
            d = (m.start - b) if b <= m.start else (a - m.end)
            tier = 0 if ca <= a < cb else (1 if b <= m.start else 2)
            if best is None or (tier, d) < best[0]:
                best = ((tier, d), mode)
        return (best[1] if best else "current"), best is not None

    def _channel_follows(self, m: _Mention) -> bool:
        """Is the figure followed by 'from/for/on <channel>'?"""
        for sa, sb, _ in self.scope_hits:
            if m.end <= sa <= m.end + 40 and _CHANNEL_GAP_RX.fullmatch(self.s[m.end:sa]):
                return True
        return False

    def _clause_has_number(self, pos: int) -> bool:
        ca, cb = self.clause(pos)
        return any(ca <= x.start() < cb and not re.fullmatch(r"(19[9]\d|20\d\d)", x.group("num"))
                   for x in _NUM_RX.finditer(self.s))

    def comparison(self, m_or_pos) -> Optional[str]:
        pos = m_or_pos.start if isinstance(m_or_pos, _Mention) else m_or_pos
        ca, cb = self.clause(pos)
        modes_clause = [mode for a, b, mode in self.periods if ca <= a < cb and mode != "current"]
        # A comparison phrase in a *different* clause that has its own figure belongs to that figure.
        def usable(a: int) -> bool:
            if ca <= a < cb:
                return True
            # "up 16.7% YoY, while leads were up 28.5%": a phrase earlier in the sentence carries forward;
            # one that comes later and sits in a clause with its own figure belongs to that figure.
            return a < ca or not self._clause_has_number(a)
        modes_sent = [mode for a, b, mode in self.periods if mode != "current" and usable(a)]
        for modes in (modes_clause, modes_sent):
            if modes:
                # the nearest one wins
                near = min(((abs(a - pos), mode) for a, b, mode in self.periods
                            if mode != "current" and (ca <= a < cb or (modes is modes_sent and usable(a)))),
                           default=None)
                if near:
                    return "yoy" if near[1] == "year_ago" else "mom"
        return None

    # -------------------------------------------------------------- scope
    def scope(self, a: int, b: int) -> Optional[frozenset]:
        ca, cb = self.clause(a)
        # 1. "… from paid search", "… via Google Ads" right after the figure
        tail = self.s[b:min(len(self.s), b + 45)]
        nxt = _NUM_RX.search(self.s, b)
        lim = (nxt.start() - b) if nxt else len(tail)
        hits = list(enumerate(self.scope_hits))
        for k, (sa, sb, sc) in hits:
            if b <= sa < b + min(45, lim):
                gap = self.s[b:sa]
                if re.search(r"(?:\bfrom|\bvia|\bthrough|\bby|\bon|\bin|\bacross|\bwith|\bfor|\bat)\s+(?:the\s+|our\s+|your\s+|its\s+)?$",
                             gap, re.I) and not re.search(r"[.;]", gap) and \
                        not re.search(r"(?:mainly|mostly|largely|primarily|partly|chiefly|driven|thanks to|"
                                      r"due to|led by|because of)\b[^.;]*$", gap, re.I):
                    return self._resolve_scope_hit(k)
        # 2. nearest before, same clause
        pre = [k for k, h in hits if ca <= h[0] and h[1] <= a]
        if pre:
            return self._resolve_scope_hit(pre[-1])
        # 3. after, same clause
        post = [k for k, h in hits if b <= h[0] < cb and h[0] - b <= 40 and not _CAUSE_RX.search(self.s[b:h[0]])]
        if post:
            return self._resolve_scope_hit(post[0])
        # 4. nearest before in the sentence
        pre = [k for k, h in hits if h[1] <= a]
        if pre:
            return self._resolve_scope_hit(pre[-1])
        # 5. a single channel named later in the sentence owns the sentence
        post = [k for k, h in hits if h[0] >= b]
        if post and len({h[2] for h in self.scope_hits}) == 1 and not re.search(
                r"(?:mainly|mostly|largely|primarily|partly|chiefly|driven|thanks to|due to|led by|because of)\b",
                self.s[b:self.scope_hits[post[0]][0]], re.I):
            return self._resolve_scope_hit(post[0])
        return self.sent.inherited

    # -------------------------------------------------------------- metric
    def metric(self, a: int, b: int, unit: str = "") -> Optional[frozenset]:
        def fit(ms: frozenset) -> frozenset:
            if unit == "currency":
                return frozenset(x for x in ms if METRICS[x].unit == "currency")
            if unit in ("count",):
                return frozenset(x for x in ms if METRICS[x].unit in ("count", "number"))
            return ms
        ca, cb = self.clause(a)
        nxt = _NUM_RX.search(self.s, b)
        limit = min(cb, nxt.start() if nxt else len(self.s), b + 28)
        for ma, mb, ms in self.metric_hits:
            if b <= ma < limit and fit(ms):
                return fit(ms)
        pre = [fit(h[2]) for h in self.metric_hits if ca <= h[0] and h[1] <= a and fit(h[2])]
        if pre:
            return pre[-1]
        pre = [fit(h[2]) for h in self.metric_hits if h[1] <= a and fit(h[2])]
        if pre:
            return pre[-1]
        return None

    # -------------------------------------------------------------- what kind of figure
    def kinds(self, m: _Mention) -> Optional[set]:
        if m.kinds:
            return m.kinds
        before = self.s[:m.start]
        stripped = _HEDGE_RX.sub("", before).rstrip()
        after = self.s[m.end:m.end + 30]
        win = self.s[max(0, m.start - 30):m.end + 25]
        if re.search(r"(?:target|goal|kpi|objective)s?\s*(?:of|was|is|were|:|at|by)?\s*$", stripped, re.I) or \
                re.match(r"\s*(?:%\s*)?(?:of|above|below|ahead of|behind|short of|over|under|beyond|past)?\s*"
                         r"(?:the\s+|our\s+|its\s+|their\s+|a\s+)?(?:[£$€]?[\d,.]+\s+)?(?:monthly\s+|agreed\s+)?(?:target|goal)\b",
                         after, re.I):
            return {"target"}
        ca, _ = self.clause(m.start)
        if m.unit == "percent" and re.search(r"(?:convert(?:ed|s|ing)?|conversion rate(?: of| was| is| at)?|converting at)"
                                              r"\s*(?:at\s+)?$", stripped, re.I):
            return {"value"}                # "converted 6.7% of its sessions" is a rate, not a share
        if m.unit == "percent" and (_SHARE_RX.search(self.s[max(ca, m.start - 30):m.start]) or
                                    re.match(r"\s*(?:of\b|share\b)", after, re.I)):
            if re.match(r"\s*(?:of\b)[^.;,]*\bconvert", self.s[m.end:], re.I):
                return {"value"}            # "6.7% of sessions converted"
            return {"share"}
        if _CHANGE_NOUN_RX.search(stripped):
            return {"change", "delta"}
        last = re.search(r"([A-Za-z']+)\s*$", stripped)
        lw = last.group(1).lower() if last else ""
        if lw not in ("to", "at") and re.match(
                r"\s*(?:more|fewer|less|extra|additional|higher|lower)\b(?!\s+than\s+[£$€]?\d)", after, re.I):
            return {"change", "delta"}
        if lw in ("to", "at", "of", "reached", "reaching", "hit", "totalled", "totaled", "totalling",
                  "totaling", "was", "were", "is", "are", "with", "delivered", "drove", "generated",
                  "recorded", "produced", "brought", "spent", "spend", "attracted", "logged",
                  "saw", "achieved", "returned", "from", "against", "than", "versus", "vs", "a", "an"):
            if lw == "a" and _CHG_AFTER_RX.match(self.s[m.end:m.end + 60]):
                return {"change", "delta"}
            return {"value"}
        if lw == "by" and re.search(r"(?:beat|beating|exceed\w*|surpass\w*|miss\w*|short of|ahead of|behind|above|"
                                    r"below|over|under)[^.;]*\b(?:target|goal)\b", before_clause := self.s[ca:m.start], re.I):
            return {"target"}
        if lw == "by" or (m.sign is not None):
            return {"change", "delta"}
        if lw in _DIR_WORDS and _DIR_WORDS[lw] in ("up", "down", "good", "bad"):
            return {"change", "delta"}
        if _CHG_AFTER_RX.match(self.s[m.end:m.end + 60]) or re.match(
                r"\s*(?:higher|lower|more|fewer|less|up|down|better|worse)\b", after, re.I):
            return {"change", "delta"}
        return None

    def stated_direction(self, m: _Mention, metrics: Optional[frozenset]) -> Optional[str]:
        if m.sign is not None:
            return "up" if m.sign > 0 else "down"
        ca, cb = self.clause(m.start)
        cands = [(m.start - b, d) for a, b, d in self.dir_hits if ca <= a and b <= m.start and m.start - b <= 45]
        cands += [(a - m.end, d) for a, b, d in self.dir_hits if a >= m.end and b <= cb and a - m.end <= 15]
        if not cands:
            return None
        d = min(cands)[1]
        return self._resolve_valence(d, metrics)

    def _resolve_valence(self, d: str, metrics: Optional[frozenset]) -> Optional[str]:
        if d in ("good", "bad"):
            if not metrics or len({METRICS[x].higher_is_better for x in metrics}) != 1:
                return None
            hib = METRICS[next(iter(metrics))].higher_is_better
            return ("up" if hib else "down") if d == "good" else ("down" if hib else "up")
        return d

    def future(self, pos: int, _depth: int = 0) -> bool:
        if self.sent.future:
            return True
        ca, cb = self.clause(pos)
        if _FUTURE_RX.search(self.s[ca:cb]):
            return True
        # "We will publish 4 pages and target a 10% lift": the plan carries across "and"/"or"
        if _depth < 4 and re.search(r"(?:\band|\bor)\s*$", self.s[:ca], re.I) and ca > 0:
            j = len(self.s[:ca].rstrip())
            prev_pos = max(0, j - 4)
            if prev_pos < ca and self.future(prev_pos, _depth + 1):
                return True
        # "Next month, we will…" — the future marker opens the sentence
        head = self.s[:ca]
        return bool(re.match(r"\s*(?:next month|next quarter|in (?:the )?(?:coming|next)|going forward|looking ahead|"
                             r"for next month|we recommend|we suggest|we propose|we plan|our plan)", head, re.I))


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
_KIND_ORDER = ["value", "change", "delta", "share", "target"]


def verify(text: str, sheet: FactSheet) -> Verification:
    res = Verification()
    if not text or not text.strip():
        return res
    masked, cites = _mask(text)
    metric_rx, metric_words = _metric_vocab(sheet.conversion_label or "conversions")
    known_ids = {f.id for f in sheet.facts}
    for cs, ce, ids in cites:
        for fid in ids:
            if fid not in known_ids:
                res.notes.append(f"Citation [{fid}] does not exist on the fact sheet and was ignored.")

    for sent in _sentences(masked, text):
        r = _Reader(sent, sheet, metric_rx, metric_words)
        r.prev = None
        mentions = _mentions(sent.text)
        mentions += _qualitative(sent.text)
        mentions.sort(key=lambda x: x.start)
        clauses_with_figures = set()
        for i, m in enumerate(mentions):
            clauses_with_figures.add(r.clause(m.start))
            nxt_start = mentions[i + 1].start if i + 1 < len(mentions) else len(sent.text) + 14
            cited = _cited(cites, sent.start + m.end, sent.start + nxt_start)
            _check_mention(res, r, m, sheet, cited, raw_text=text)
        _check_directions(res, r, sheet, clauses_with_figures, text)
        _check_rankings(res, r, sheet, text)
    return res


def _cited(cites, a: int, b: int) -> Optional[str]:
    for cs, ce, ids in cites:
        if a <= cs < b:
            return ids[0]
    return None


def _qualitative(s: str) -> list[_Mention]:
    out = []
    for q in _QUAL_RX.finditer(s):
        ratio = _QUAL_RATIO[q.group(2).lower()]
        hedge = (q.group(1) or "").lower()
        pct = (ratio - 1) * 100
        if hedge in ("nearly", "almost", "close to"):
            lo, hi = (ratio - 0.3 if ratio > 1 else ratio), (ratio if ratio > 1 else ratio + 0.15)
        elif hedge in ("more than", "over", "just over", "well over"):
            lo, hi = (ratio, ratio + 0.6) if ratio > 1 else (ratio - 0.15, ratio)
        elif hedge in ("roughly", "about", "around"):
            lo, hi = ratio * 0.9, ratio * 1.1
        else:
            lo, hi = ratio * 0.93, ratio * 1.07
        band = ((lo - 1) * 100, (hi - 1) * 100)
        out.append(_Mention(q.start(), q.end(), q.group(0), abs(pct), "percent",
                            1 if ratio > 1 else -1, 0, None, {"change"}, band))
    for q in _FRACTION_RX.finditer(s):
        word = q.group(2).lower()
        hedge = (q.group(1) or "").lower()
        if word == "the majority":
            band = (50.0, 100.0)
            v = 50.0
        else:
            v = _FRACTION[word]
            if hedge in ("nearly", "almost", "just under", "close to"):
                band = (v - 8, v + 0.5)
            elif hedge in ("more than", "over", "just over"):
                band = (v, v + 12)
            elif hedge in ("under", "less than"):
                band = (v - 12, v)
            elif hedge in ("roughly", "about", "around"):
                band = (v - 5, v + 5)
            else:
                band = (v - 3, v + 3)
        out.append(_Mention(q.start(), q.end(), q.group(0), v, "percent", None, 0, None, {"share"}, band))
    return out


def _unit_ok(f: Fact, m: _Mention) -> bool:
    if m.unit == "currency":
        return f.unit == "currency"
    if m.unit == "percent":
        return f.unit in ("percent", "points") or (f.metric == "roas" and f.kind == "value")
    if m.unit == "points":
        return f.unit == "points"
    if m.unit == "ratio":
        return f.metric == "roas" and f.kind in ("value", "delta")
    return f.unit in ("count", "number")


def _truth(f: Fact, m: _Mention) -> float:
    v = f.value
    if m.unit == "percent" and f.metric == "roas" and f.kind == "value":
        v *= 100
    if f.kind in ("change", "delta") or (f.kind == "target" and f.target_kind in ("gap", "gap_pct")):
        v = abs(v)
    return v


def _num_ok(f: Fact, m: _Mention) -> bool:
    if not _unit_ok(f, m):
        return False
    t = _truth(f, m)
    if m.rng:
        return m.rng[0] - m.tol <= t <= m.rng[1] + m.tol
    if m.hedge_band:
        signed = f.value
        if f.kind == "change":
            return m.hedge_band[0] - 1e-9 <= signed <= m.hedge_band[1] + 1e-9
        return m.hedge_band[0] - 1e-9 <= t <= m.hedge_band[1] + 1e-9
    return _value_ok(m.value, t, m.tol, m.hedge)


class _Ctx:
    def __init__(self, scopes, metrics, kinds, period, period_explicit, comparison, sheet: FactSheet):
        self.scopes, self.metrics, self.kinds = scopes, metrics, kinds
        self.period, self.period_explicit, self.comparison = period, period_explicit, comparison
        self.sheet = sheet

    def fails(self, f: Fact) -> list[str]:
        out = []
        if self.scopes is not None and (f.scope not in self.scopes or COMBINED in self.scopes):
            out.append("scope")
        if self.metrics is not None and f.metric not in self.metrics and not (
                f.kind == "target" and "conversions" in self.metrics):
            out.append("metric")
        if self.kinds is not None and f.kind not in self.kinds:
            out.append("kind")
        if f.kind == "value" and f.period != self.period:
            out.append("period")
        if f.kind in ("change", "delta"):
            want = self.comparison or ("mom" if self.sheet.previous_period else "yoy")
            if f.comparison != want:
                out.append("period")
        return out


def _check_mention(res: Verification, r: _Reader, m: _Mention, sheet: FactSheet, cited: Optional[str],
                   raw_text: str) -> None:
    s = r.s
    abs_a, abs_b = r.sent.start + m.start, r.sent.start + m.end
    quote = raw_text[abs_a:abs_b]
    if r.future(m.start):
        res.claims.append(Claim(quote, abs_a, abs_b, "forward_looking", None, cited))
        return

    if m.cur and m.cur not in sheet.currency:
        msg = (f"\"{quote}\" is written in {m.cur}, but this client's figures are in {sheet.currency}. "
               f"The amount may be right; the currency symbol is not.")
        res.issues.append(Issue("wrong_currency", quote, r.s.strip(), msg,
                                f"Use {sheet.currency}, not {m.cur}.", abs_a, abs_b))
        res.claims.append(Claim(quote, abs_a, abs_b, "issue", None, cited))
        r.prev = None
        return

    scopes = r.scope(m.start, m.end)
    metrics = r.metric(m.start, m.end, m.unit)
    ca_, cb_ = r.clause(m.start)
    own_metric = any(ca_ <= h[0] < cb_ for h in r.metric_hits)
    before_txt = _HEDGE_RX.sub("", s[:m.start]).rstrip()
    prev = getattr(r, "prev", None)
    inherited_kinds = None
    if prev and not own_metric and prev["unit"] == m.unit and prev["metrics"] and m.unit in ("percent", "count"):
        metrics = prev["metrics"]                       # "up from 5.6%": the same measure as the figure before it
    if prev and prev["unit"] == m.unit and _COMPARE_CUE_RX.search(before_txt):
        inherited_kinds = prev["kinds"]                 # "31.8% of leads, compared to 41.1% from paid search"
    forced_rate = m.unit == "percent" and bool(
        re.search(r"(?:convert(?:ed|s|ing)?|conversion rate(?: of| was| is| at)?|converting at)\s*(?:at\s+)?$",
                  before_txt, re.I) or re.match(r"\s*of\b[^.;,]*\bconvert", s[m.end:], re.I))
    if forced_rate:
        metrics = frozenset({"conv_rate"})
    if m.force_metrics:
        metrics = m.force_metrics
    if m.unit == "currency" and re.match(r"\s*(?:each|apiece|a head|per head|a time)\b", s[m.end:], re.I):
        metrics = frozenset({"cpc"}) if metrics and "clicks" in metrics else \
            frozenset({"cpa"}) if metrics and "conversions" in metrics else frozenset({"cpa", "cpc"})
    if metrics and "avg_position" in metrics and m.unit == "count" and \
            re.match(r"\s*(?:places|spots|positions)\b", s[m.end:], re.I):
        m.kinds = {"delta"}
    # "2x the traffic" with a non-ROAS metric is a change claim
    if m.unit == "ratio" and metrics is not None and "roas" not in metrics and not m.force_metrics:
        m.unit, m.value, m.tol, m.kinds = "percent", (m.value - 1) * 100, m.tol * 100, {"change"}
    kinds = r.kinds(m)
    if inherited_kinds and (kinds is None or kinds == {"value"}):
        kinds = inherited_kinds
    if forced_rate:
        kinds = {"value"}
    if m.force_metrics:
        kinds = None
    period, explicit = r.figure_period(m)
    comparison = r.comparison(m)
    # A figure in a sentence that names no channel reads as the account total.
    if scopes is None and metrics is not None and kinds != {"target"}:
        if any(f.scope == TOTAL and f.metric in metrics for f in sheet.facts):
            scopes = frozenset({TOTAL})
    ctx = _Ctx(scopes, metrics, kinds, period, explicit, comparison, sheet)
    r.prev = {"unit": m.unit, "kinds": kinds, "metrics": metrics}

    num_ok = [f for f in sheet.facts if _num_ok(f, m)]
    good = [f for f in num_ok if not ctx.fails(f)]
    if not good and _UNTRACKED_RX.search(s[ca_:cb_]):
        res.claims.append(Claim(quote, abs_a, abs_b, "unchecked", None, cited))     # a platform metric we don't import
        return
    if not good and m.unit == "count" and not own_metric and not m.sign and _activity_noun(s, m):
        # "We published 4 new articles": something the agency did, not a figure from the data
        res.claims.append(Claim(quote, abs_a, abs_b, "unchecked", None, cited))
        return
    if good:
        best = next((f for f in good if f.id == cited), None) or \
            sorted(good, key=lambda f: _KIND_ORDER.index(f.kind))[0]
        issue = _direction_issue(r, m, best, metrics, sheet, quote, abs_a, abs_b)
        if issue and any(i.kind == "wrong_direction" and i.expected == issue.expected and i.sentence == issue.sentence
                         for i in res.issues):
            res.claims.append(Claim(quote, abs_a, abs_b, "issue", None, cited))
            return
        if issue:
            res.issues.append(issue)
            res.claims.append(Claim(quote, abs_a, abs_b, "issue", None, cited))
            return
        if cited and cited != best.id:
            res.notes.append(f"\"{quote}\" was cited as [{cited}] but matches [{best.id}] ({best.label}); "
                             f"provenance corrected.")
        res.claims.append(Claim(quote, abs_a, abs_b, "verified", best.id, cited))
        return

    expected = _expected(sheet, ctx, m)
    exp_txt = f" The fact sheet has {expected.label}: {sheet.fmt(expected)} [{expected.id}]." if expected else ""
    sentence = r.s.strip()
    near = None
    if num_ok:
        def rank(f):
            return (len(ctx.fails(f)), 0 if f.id == cited else 1, _KIND_ORDER.index(f.kind))
        near = sorted(num_ok, key=rank)[0]
        if len(ctx.fails(near)) != 1:
            near = None          # a coincidence: same number, unrelated fact
    if near is None and m.unit == "count" and metrics is None and scopes is None:
        # "we published 4 blog posts": not a data claim we can check; the reviewer sees it flagged as unchecked
        res.claims.append(Claim(quote, abs_a, abs_b, "unchecked", None, cited))
        return
    if near is None and m.hedge_band and m.kinds == {"change"}:
        ch = next((f for f in sheet.facts if f.kind == "change" and not ctx.fails(f)), None)
        if ch and (ch.value > 0) != (m.sign > 0):
            res.issues.append(_dir_issue(ch, sheet, "up" if m.sign > 0 else "down", quote, r.s.strip(),
                                         abs_a, abs_b, ch))
            res.claims.append(Claim(quote, abs_a, abs_b, "issue", None, cited))
            return
    if near is not None:
        fail = ctx.fails(near)[0]
        kind = {"scope": "wrong_scope", "metric": "wrong_metric", "kind": "wrong_kind",
                "period": "wrong_period"}[fail]
        what = {"wrong_scope": f"belongs to a different channel",
                "wrong_metric": "is a different metric",
                "wrong_kind": "is a different kind of figure",
                "wrong_period": "is from a different period"}[kind]
        said = _describe(ctx)
        msg = f"\"{quote}\" {what}: it is {near.label} ({sheet.fmt(near)}), but the sentence presents it as {said}."
        msg += exp_txt
        hint = f"\"{quote}\" is [{near.id}] {near.label}, not {said}.{exp_txt} Use the matching fact or rephrase."
        res.issues.append(Issue(kind, quote, sentence, msg, hint, abs_a, abs_b, expected.id if expected else None))
    else:
        said = _describe(ctx)
        msg = f"\"{quote}\" doesn't match any figure in the data for {said}.{exp_txt}"
        hint = (f"\"{quote}\" is not on the fact sheet for {said}.{exp_txt} "
                f"Only state figures that appear on the fact sheet, rounded no further than shown.")
        res.issues.append(Issue("unsupported", quote, sentence, msg, hint, abs_a, abs_b,
                                expected.id if expected else None))
    res.claims.append(Claim(quote, abs_a, abs_b, "issue", None, cited))


def _activity_noun(s: str, m: _Mention) -> bool:
    """A bare count followed by a noun that isn't one of our metrics: '4 new articles', '4,800 subscribers'."""
    w = re.match(r"\s+([A-Za-z][\w'-]*)", s[m.end:])
    if not w:
        return False
    word = w.group(1).lower()
    return word not in _STOP_NOUNS and word not in _DIR_WORDS and word not in (
        "ahead", "behind", "short", "above", "below", "off", "away", "more", "extra", "additional")


def _describe(ctx: _Ctx) -> str:
    parts = []
    if ctx.scopes:
        names = sorted(channel_label(s) for s in ctx.scopes if s != COMBINED)
        parts.append((" and ".join(names) + " combined") if COMBINED in ctx.scopes else " or ".join(names))
    if ctx.metrics:
        names = sorted({_metric_name(x, ctx.sheet) for x in ctx.metrics})
        parts.append(" / ".join(names))
    if ctx.kinds and ctx.kinds != {"value"}:
        k = "change" if "change" in ctx.kinds else next(iter(ctx.kinds))
        parts.append({"change": "change", "share": "share", "target": "vs target", "delta": "change"}.get(k, k))
    if ctx.kinds and ctx.kinds & {"change", "delta"}:
        comp = ctx.comparison or ("mom" if ctx.sheet.previous_period else "yoy")
        parts.append("year on year" if comp == "yoy" else "month on month")
    elif ctx.period != "current":
        parts.append({"previous": "last month", "year_ago": "a year ago"}[ctx.period])
    return " ".join(parts) if parts else "this report"


def _metric_name(key: str, sheet: FactSheet) -> str:
    if key == "conversions":
        return sheet.conversion_label
    if key == "cpa":
        return f"cost per {singular(sheet.conversion_label)}"
    return METRICS[key].label.lower() if key not in ("ctr", "roas", "cpc") else METRICS[key].label


def _expected(sheet: FactSheet, ctx: _Ctx, m: _Mention) -> Optional[Fact]:
    scopes = ctx.scopes or frozenset({TOTAL})
    if not ctx.metrics or COMBINED in scopes:
        return None
    for f in sheet.facts:
        if f.scope in scopes and f.metric in ctx.metrics and _unit_ok(f, m) and not ctx.fails(f):
            return f
    for f in sheet.facts:          # unit-insensitive fallback: "143" said where a % was meant
        if f.scope in scopes and f.metric in ctx.metrics and not ctx.fails(f):
            return f
    return None


def _direction_issue(r: _Reader, m: _Mention, f: Fact, metrics, sheet: FactSheet, quote: str,
                     a: int, b: int) -> Optional[Issue]:
    stated = r.stated_direction(m, frozenset({f.metric}))
    if stated is None or (m.rng and stated == "flat"):
        return None
    sentence = r.s.strip()
    if f.kind in ("change", "delta") or (f.kind == "target" and f.target_kind in ("gap", "gap_pct")):
        actual = f.value
        if f.kind == "change":
            pct = actual
        else:
            base = f.base if f.base else None
            pct = (actual / abs(base) * 100) if base else (100.0 if actual else 0.0)
        wrong = (stated == "up" and actual < 0) or (stated == "down" and actual > 0) or \
                (stated == "flat" and abs(pct) >= FLAT_CLAIM_LIMIT)
        if not wrong:
            return None
        return _dir_issue(f, sheet, stated, quote, sentence, a, b, f)
    if f.kind == "value" and f.period == "current":
        # "rose to 143": check the month's change for that metric
        ca, cb = r.clause(m.start)
        linked = [d for x, y, d in r.dir_hits if ca <= x and y <= m.start]
        if not linked:
            return None
        comp = r.comparison(m) or ("mom" if sheet.previous_period else "yoy")
        ch = sheet.find(f.scope, f.metric, "change", "current", comp)
        if not ch:
            return None
        wrong = (stated == "up" and ch.value <= -DIRECTION_SLACK) or \
                (stated == "down" and ch.value >= DIRECTION_SLACK) or \
                (stated == "flat" and abs(ch.value) >= FLAT_CLAIM_LIMIT)
        if wrong:
            return _dir_issue(ch, sheet, stated, quote, sentence, a, b, ch)
    return None


def _dir_issue(f: Fact, sheet: FactSheet, stated: str, quote: str, sentence: str, a: int, b: int,
               expected: Fact) -> Issue:
    actual = "rose" if f.value > 0 else ("fell" if f.value < 0 else "did not change")
    if f.kind == "change" and abs(f.value) < FLAT_BAND and stated != "flat":
        actual = "was broadly flat (" + sheet.fmt(f) + ")"
    else:
        actual += f" ({sheet.fmt(f)})"
    said = {"up": "went up", "down": "went down", "flat": "held steady"}[stated]
    msg = f"The sentence says {f.label.split(',')[0]} {said}, but it {actual}."
    hint = f"Wrong direction: {f.label} is {sheet.fmt(f)} [{f.id}]. Describe it as it moved."
    return Issue("wrong_direction", quote, sentence, msg, hint, a, b, expected.id)


def _check_directions(res: Verification, r: _Reader, sheet: FactSheet, clauses_with_figures: set,
                      raw_text: str) -> None:
    """Direction claims with no number: "Paid search sessions dropped this month."""
    seen = set()
    for a, b, d in r.dir_hits:
        clause = r.clause(a)
        if clause in clauses_with_figures or clause in seen:
            continue
        if r.future(a):
            continue
        ca, cb = clause
        mets = [(abs(ma - a), ms) for ma, mb, ms in r.metric_hits if ca <= ma < cb]
        if not mets:
            continue
        metrics = min(mets, key=lambda x: x[0])[1]
        if "conv_rate" in metrics and "conversions" in metrics:
            metrics = frozenset({"conversions"})
        stated = r._resolve_valence(d, metrics)
        if stated is None:
            continue
        if re.search(r"(?<![\w-])(?:if|when|whether|unless)(?![\w-])", r.s[ca:cb], re.I):
            continue
        scopes = r.scope(a, b)
        if scopes is None:
            scopes = frozenset({TOTAL})
        scopes = scopes - {COMBINED}
        comp = r.comparison(a) or ("mom" if sheet.previous_period else "yoy")
        changes = [sheet.find(sc, mt, "change", "current", comp) for sc in scopes for mt in metrics]
        changes = [c for c in changes if c]
        if not changes:
            continue
        def contradicts(c: Fact) -> bool:
            return (stated == "up" and c.value <= -FLAT_BAND) or (stated == "down" and c.value >= FLAT_BAND) or \
                   (stated == "flat" and abs(c.value) >= FLAT_CLAIM_LIMIT)
        if all(contradicts(c) for c in changes):
            seen.add(clause)
            c = changes[0]
            qa, qb = r.sent.start + ca, r.sent.start + cb
            quote = raw_text[qa:qb].strip(" ,;")
            res.issues.append(_dir_issue(c, sheet, stated, quote, r.s.strip(), qa, qb, c))
            res.claims.append(Claim(quote, qa, qb, "issue"))


# --------------------------------------------------------------------------- #
# Ranking claims: "largest source of traffic", "most cost-efficient", "the only channel where leads fell"
# --------------------------------------------------------------------------- #
_SUPER_RX = re.compile(r"(?<![\w-])(?:largest|biggest|top|leading|main|primary|strongest|best|highest|greatest|"
                       r"number[- ]one)\s+(?:single\s+)?(?:\w+\s+){0,2}?(?:source|channel|driver|contributor|performer|"
                       r"generator)s?\b", re.I)
_EFFICIENT_RX = re.compile(r"(?<![\w-])(?:(?:most|more)\s+(?:cost[- ]?efficient|cost[- ]?effective|efficient)|cheapest|"
                           r"lowest[- ]cost|lowest\s+(?:cost per \w+|cpa|cpl|cpc|cost[- ]per[- ]\w+))", re.I)
_BEST_METRIC_RX = re.compile(r"(?<![\w-])(highest|best|strongest|top|lowest|worst|weakest)\s+(roas|return on ad spend|"
                             r"conversion rate|ctr|click[- ]through rate|cpc|cost per click|cpa|cpl)\b", re.I)
_ONLY_RX = re.compile(r"(?<![\w-])(?:the |our |your )?only\s+(?:single\s+)?(?:channel|source)\b[^.;]{0,50}?"
                      r"\b(fell|dropped|declined|decreased|slipped|dipped|rose|grew|increased|climbed|improved|gained)\b", re.I)
_EVERY_RX = re.compile(r"(?<![\w-])(?:every|each|all)\s+(?:single\s+)?(?:other\s+)?channels?\b[^.;,]{0,30}?"
                       r"\b(fell|dropped|declined|decreased|slipped|rose|grew|increased|climbed|improved)\b", re.I)
_UPWORDS = ("rose", "grew", "increased", "climbed", "improved", "gained")
_RANK_METRIC = {"roas": ("roas", True), "return on ad spend": ("roas", True), "conversion rate": ("conv_rate", True),
                "ctr": ("ctr", True), "click-through rate": ("ctr", True), "click through rate": ("ctr", True),
                "cpc": ("cpc", False), "cost per click": ("cpc", False), "cpa": ("cpa", False), "cpl": ("cpa", False)}


def _rank_subject(r: _Reader, before: int) -> Optional[str]:
    hits = [h for h in r.scope_hits if h[0] < before and TOTAL not in h[2]]
    if hits:
        sc = hits[-1][2]
    elif r.sent.inherited and TOTAL not in r.sent.inherited:
        sc = r.sent.inherited
    else:
        return None
    return next(iter(sc)) if len(sc) == 1 else None


def _channel_facts(sheet: FactSheet, metric: str) -> dict[str, Fact]:
    return {f.scope: f for f in sheet.facts
            if f.metric == metric and f.kind == "value" and f.period == "current" and f.scope != TOTAL}


def _rank_issue(res: Verification, r: _Reader, a: int, b: int, quote: str, msg: str, hint: str, raw: str) -> None:
    abs_a, abs_b = r.sent.start + a, r.sent.start + b
    res.issues.append(Issue("wrong_ranking", raw[abs_a:abs_b], r.s.strip(), msg, hint, abs_a, abs_b))
    res.claims.append(Claim(raw[abs_a:abs_b], abs_a, abs_b, "issue"))


def _check_rankings(res: Verification, r: _Reader, sheet: FactSheet, raw: str) -> None:
    s = r.s
    if r.sent.future or _FUTURE_RX.search(s):
        return

    def ranked(metric: str, highest: bool, subject: Optional[str], m: re.Match, what: str) -> None:
        facts = _channel_facts(sheet, metric)
        if subject is None or subject not in facts or len(facts) < 2:
            return
        best = max(facts.values(), key=lambda f: f.value) if highest else min(facts.values(), key=lambda f: f.value)
        mine = facts[subject]
        if (mine.value >= best.value - 1e-9) if highest else (mine.value <= best.value + 1e-9):
            return
        word = "highest" if highest else "lowest"
        msg = (f"{channel_label(subject)} isn't the {what}: {channel_label(best.scope)} has the {word} "
               f"{_metric_name(metric, sheet)} ({sheet.fmt(best)} [{best.id}]) against {channel_label(subject)}'s "
               f"{sheet.fmt(mine)} [{mine.id}].")
        _rank_issue(res, r, m.start(), m.end(), m.group(0), msg, msg + " Correct the claim or drop it.", raw)

    for m in _SUPER_RX.finditer(s):
        after = [h for h in r.metric_hits if h[0] >= m.end()]
        before = [h for h in r.metric_hits if h[1] <= m.start()]
        hit = (after or before or [None])[0 if after else -1] if (after or before) else None
        if not hit:
            continue
        metric = next((x for x in ("conversions", "sessions", "revenue", "spend") if x in hit[2]), None)
        if metric:
            ranked(metric, metric != "spend" or True, _rank_subject(r, m.start()), m,
                   f"{m.group(0).split()[0].lower()} source of {_metric_name(metric, sheet)}")
    def about_channels(end: int) -> bool:
        return bool(re.search(r"\b(?:channels?|sources?|campaign types?)\b|\bof (?:the|our|all|any)\b", s[end:end + 60], re.I))

    for m in _EFFICIENT_RX.finditer(s):
        if not about_channels(m.end()):
            continue                       # "its most efficient month" compares months, not channels
        metric = "cpc" if re.search(r"click|cpc", s[m.start():m.end() + 25], re.I) else "cpa"
        ranked(metric, False, _rank_subject(r, m.start()), m, "most cost-efficient channel")
    for m in _BEST_METRIC_RX.finditer(s):
        if not about_channels(m.end()):
            continue
        metric, hib = _RANK_METRIC[m.group(2).lower()]
        want_high = m.group(1).lower() in ("highest", "best", "strongest", "top")
        highest = want_high if hib else not want_high
        ranked(metric, highest, _rank_subject(r, m.start()), m, f"channel with the {m.group(1).lower()} {m.group(2)}")

    def metric_in_sentence() -> str:
        for h in r.metric_hits:
            for x in ("conversions", "sessions", "revenue", "spend"):
                if x in h[2]:
                    return x
        return "conversions"

    for m in _ONLY_RX.finditer(s):
        metric = metric_in_sentence()
        up = m.group(1).lower() in _UPWORDS
        movers = []
        for scope, f in _channel_facts(sheet, metric).items():
            ch = sheet.find(scope, metric, "change", "current", "mom")
            if ch and ((ch.value > 0) if up else (ch.value < 0)) and ch.direction != "flat":
                movers.append((scope, ch))
        subject = _rank_subject(r, m.start())
        names = ", ".join(f"{channel_label(sc)} ({sheet.fmt(c)} [{c.id}])" for sc, c in movers) or "none"
        if len(movers) != 1 or (subject and movers and movers[0][0] != subject):
            msg = (f"It isn't the only channel where {_metric_name(metric, sheet)} "
                   f"{'rose' if up else 'fell'}. Channels where it did: {names}.")
            _rank_issue(res, r, m.start(), m.end(), m.group(0), msg, msg + " Correct the claim or drop it.", raw)
    for m in _EVERY_RX.finditer(s):
        if re.search(r"(?:across|for|in|on|from|over|of|by|with|to|and)\s+$", s[:m.start()], re.I):
            continue                      # "across all channels, sessions rose" is about the total
        metric = metric_in_sentence()
        up = m.group(1).lower() in _UPWORDS
        off = []
        for scope in _channel_facts(sheet, metric):
            ch = sheet.find(scope, metric, "change", "current", "mom")
            if ch and ((ch.value < 0) if up else (ch.value > 0)):
                off.append(f"{channel_label(scope)} ({sheet.fmt(ch)} [{ch.id}])")
        if off:
            msg = (f"Not every channel's {_metric_name(metric, sheet)} {'rose' if up else 'fell'}: "
                   + ", ".join(off) + " moved the other way.")
            _rank_issue(res, r, m.start(), m.end(), m.group(0), msg, msg + " Correct the claim or drop it.", raw)
