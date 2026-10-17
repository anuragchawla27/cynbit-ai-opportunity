"""Synthetic inbound-inquiry generator for the lead-qualification model.

Cynbit has no public inquiry log, so this builds one from a latent-variable model.
Each message is composed from phrase pools; its label is drawn from the latent
attributes plus noise, so the label is correlated with, but not identical to, any
rule a person would write. Junk (spam, students, vendors, job seekers) is always Cold.
"""
from __future__ import annotations

import random

BIZ = ["clinic", "retail store", "coaching institute", "restaurant chain", "logistics firm",
       "real estate agency", "D2C brand", "school", "hotel", "pharmacy", "salon chain", "manufacturing unit"]
NEEDS = [
    "need a website for my {b}", "looking to build a mobile app for our {b}",
    "want an AI chatbot to handle customer queries for the {b}", "want to automate invoice data entry using LLMs",
    "looking for SEO and Google ads for our {b}", "want to migrate our servers to AWS",
    "need a custom ERP and dashboard for operations", "want a voice agent to take appointment calls",
    "want to build a SaaS product for the {b} sector", "need a booking system for our {b}",
    "interested in CRM automation for our sales team", "want to modernise our legacy software",
]
DETAIL = [
    "Right now everything runs on Excel and WhatsApp.", "We get about 200 customer messages a day.",
    "It should integrate with our existing billing software.", "Users would be our staff and customers across 3 cities.",
    "We tried a vendor before but the result was poor.", "Main goal is to cut manual work and response time.",
    "Needs to work in Hindi and English.", "We already have designs and a feature list ready.",
]
ORG = ["We are a {n}-branch {b}.", "I run a {b} in Jaipur.", "Our company is a {b} with {m} staff.",
       "This is from the management team of a {b}.", "We are a growing {b}."]
BUDGET = ["Budget is around Rs {x} lakh.", "We can spend up to {x}0k INR.", "Budget: ${x}k.",
          "We have approved about ₹{x} lakh for this.", "Our budget range is {x}-{y} lakh."]
TIMELINE = ["Need it live in {w} weeks.", "Target launch is next quarter.", "Deadline is end of next month.",
            "We want to start asap.", "Planning to go live before {mo}."]
CONTACT = ["Call me on 9{d}.", "Email: owner@{dom}.in", "WhatsApp {p}.", "Reach me at team@{dom}.com or +91 9{d}."]
OPENERS = ["Hello,", "Hi team,", "Dear Sir/Madam,", "Good morning,", "", "", ""]
DOMS = ["shreeretail", "medilife", "gyanacademy", "spicetrail", "urbanloom", "fastlogix", "homenest"]
MONTHS = ["December", "January", "March", "April", "the festive season"]

JUNK = [
    "hi", "hello", "send price list", "how much for website", "just checking if your site works",
    "We guarantee first page Google ranking for just Rs 999. Reply for details.",
    "I am a final year student looking for a free internship, please share details.",
    "Looking for a job in marketing, my resume is attached, kindly consider.",
    "We are a bulk SMS provider with lowest rates in India. Can we schedule a demo?",
    "Congratulations, you are selected for a pre-approved business loan. Click the link now.",
    "Do you need freelancers? I can design logos very cheap.",
    "Please like and follow our page for free followers.",
    "need website", "pls call me", "quote?", "can i get discount on internship fees",
]


def _typo(s: str, rng: random.Random) -> str:
    if rng.random() < 0.25:
        s = s.lower()
    if rng.random() < 0.2 and len(s) > 20:
        i = rng.randrange(5, len(s) - 3)
        s = s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return s


def make_message(rng: random.Random) -> tuple[str, str]:
    if rng.random() < 0.15:
        return _typo(rng.choice(JUNK), rng), "Cold"

    org = rng.random() < 0.6
    budget = rng.random() < 0.45
    timeline = rng.random() < 0.45
    contact = rng.random() < 0.5
    detail = rng.choices([0, 1, 2], weights=[0.35, 0.4, 0.25])[0]
    b = rng.choice(BIZ)
    x = rng.randint(1, 9)

    parts = [rng.choice(OPENERS)]
    if org:
        parts.append(rng.choice(ORG).format(n=rng.randint(2, 12), b=b, m=rng.randint(10, 200)))
    parts.append(("I " if not org else "We ") + rng.choice(NEEDS).format(b=b) + ".")
    parts += rng.sample(DETAIL, detail)
    if budget:
        parts.append(rng.choice(BUDGET).format(x=x, y=x + rng.randint(1, 4)))
    if timeline:
        parts.append(rng.choice(TIMELINE).format(w=rng.randint(2, 12), mo=rng.choice(MONTHS)))
    if contact:
        parts.append(rng.choice(CONTACT).format(d=rng.randint(10**8, 10**9 - 1), dom=rng.choice(DOMS),
                                               p=rng.randint(7 * 10**9, 8 * 10**9 - 1)))
    text = _typo(" ".join(p for p in parts if p), rng)

    s = (0.22 * detail / 2 + 0.25 * budget + 0.22 * timeline + 0.18 * org + 0.08 * contact
         + rng.gauss(0, 0.1))
    label = "Hot" if s >= 0.55 else "Warm" if s >= 0.25 else "Cold"
    return text, label


def generate(n: int = 1500, seed: int = 7) -> tuple[list[str], list[str]]:
    rng = random.Random(seed)
    rows = [make_message(rng) for _ in range(n)]
    return [r[0] for r in rows], [r[1] for r in rows]
