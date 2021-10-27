import json
import requests
from requests_html import HTMLSession

# file path to write final json file
OUT = "data/courses.json"
# URLs to scrape
URLS = [
    # "https://math.gatech.edu/projected-schedule-of-undergraduate-courses",
    "https://math.gatech.edu/projected-schedule-of-graduate-courses"
]

def course_data(session: HTMLSession, url: str) -> dict:
    """ Scrapes the specific course page. """
    r = session.get(url)
    find = lambda s: r.html.find(s, first=True)
    field = lambda s: "None." if find(s) is None else \
        find(s).find("div.field-items", first=True).text.strip()

    prereqs = field("div.field-name-field-prerequisites").splitlines()
    prereqs, extra = prereqs[0], "\n".join(prereqs[1:])

    return {
        "title": find("h2.title").text.strip(),
        "hours": field("div.field-name-field-hours-total-credit"),
        "schedule": field("div.field-name-field-typical-scheduling"),
        "description": field("div.field-name-body"),
        "prereqs": prereqs,
        "extra": extra,
    }

def scrape(url: str) -> None:
    """ Goes through each course on the page. """
    with open(OUT) as f:
        courses = json.load(f)

    session = HTMLSession()
    r = session.get(url, params={"field_semesters_offered_tid": "All"})

    table = r.html.find("table")[0]
    for row in table.find("tr")[1:]:
        title, cid, semesters = map(str.strip, row.text.splitlines())
        url = [url for url in row.absolute_links if "courses" in url][0]
        course = f"MATH {cid}"
        data = course_data(session, url)
        data["offered"] = semesters
        courses[course] = data

    with open(OUT, "w") as f:
        json.dump(courses, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    for url in URLS:
        scrape(url)

