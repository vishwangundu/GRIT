"""Demo data from PRD section 11."""

from dataclasses import dataclass

TRACK = "AI Product Mastery"
BADGE_LEVELS = ("novice", "specialist", "expert", "master", "grand_master")
SKILLS = (
    "Computational Thinking",
    "CS Fundamentals",
    "Applied Gen AI Development",
    "UI Engineering",
    "Product Thinking",
)
# (skill index, min level) per badge level. Specialist needs 5; demo students clear 1 of them.
REQUIREMENTS = {
    "novice": ((0, 1), (1, 1), (2, 1), (3, 2)),
    "specialist": ((0, 2), (1, 2), (2, 2), (3, 3), (4, 1)),
}
NOVICE_CLEARED = ((0, 1), (1, 1), (2, 1), (3, 2))
SPECIALIST_HEAD_START = ((4, 1),)
EMAIL_DOMAIN = "demo.grit"


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    miles: int = 0


INTERVIEWERS = (
    Person("priya", "Priya Sharma"),
    Person("rahul", "Rahul Verma"),
    Person("neha", "Neha Iyer"),
)
ADMIN = Person("admin", "Interview Team")
STUDENTS = (
    Person("aarav", "Aarav Reddy", 2340),
    Person("sneha", "Sneha Kulkarni", 2210),
    Person("divya", "Divya Menon", 2475),
    Person("rohan", "Rohan Das", 1990),
    Person("ishita", "Ishita Jain", 2620),
    Person("kavya", "Kavya Shetty", 2080),
    Person("pooja", "Pooja Reddy", 2290),
    Person("arjun", "Arjun Mehta", 2150),
    Person("meera", "Meera Nair", 2550),
    Person("nikhil", "Nikhil Joshi", 2700),
    Person("tanvi", "Tanvi Patil", 1940),
    Person("ananya", "Ananya Gupta", 2380),
    Person("harsha", "Harsha Vardhan", 2260),
    Person("lakshmi", "Lakshmi Prasad", 2030),
    Person("ravi", "Ravi Teja", 1880),
    Person("sana", "Sana Sheikh", 2490),
)
_FIRST = ("Aditya", "Bhavya", "Chetan", "Deepika", "Eshwar", "Farah", "Gautam", "Hema")
_LAST = ("Rao", "Iyer", "Kapoor", "Naidu", "Pillai")
EXTRA_MILES_MIN = 1800
EXTRA_MILES_SPAN = 1400
EXTRA_STUDENTS = tuple(
    Person(
        f"learner{i + 1:02d}",
        f"{_FIRST[i % len(_FIRST)]} {_LAST[i // len(_FIRST)]}",
        EXTRA_MILES_MIN + (i * 367) % EXTRA_MILES_SPAN,
    )
    for i in range(len(_FIRST) * len(_LAST))
)


def email_for(person: Person) -> str:
    return f"{person.key}@{EMAIL_DOMAIN}"


def meet_link_for(person: Person) -> str:
    return f"https://meet.google.com/grit-{person.key}-demo"
