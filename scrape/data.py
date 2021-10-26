import sys, os, json

# file path to write final json file
OUT = "data/courses.json"
# end of line marker
END = "© 2021 Ellucian Company L.P. and its affiliates."
# categories: https://www.cc.gatech.edu/threads-better-way-learn-computing
CATEGORIES = [
    "Devices",
    "Info Internetworks",
    "Intelligence",
    "Media",
    "Modeling & Simulation",
    "People",
    "Systems & Architecture",
    "Theory",
    "Miscellaneous"
]

def get_category(title: str) -> int:
    """ Returns the index of a category. """
    while True:
        try:
            prompt = f"{title}\n" + \
                ", ".join(f"{i} - {name[:4]}"
                          for i, name in enumerate(CATEGORIES)) + "\n"
            response = int(input(prompt))
            if 0 <= response < len(CATEGORIES):
                return response
        except ValueError:
            pass
        print("Invalid category!")

def parse_course(lines: list) -> dict:
    """ Parses raw text data into a course. """
    i, title = [(i, line) for i, line in enumerate(lines) if "-" in line][0]
    tokens = list(map(str.strip, title.split("-")))
    course, title = tokens[0], "-".join(tokens[1:])

    description = lines[i + 1]
    credit = float(lines[i + 2].split()[0])

    indexes = [i for i in range(len(lines)) if lines[i] == "Prerequisites:"]
    prereqs = lines[indexes[0] + 1] if len(indexes) > 0 else ""

    return course, {"title": title,
                    "description": description,
                    "credit": credit,
                    "prereqs": prereqs,
                   }

if __name__ == "__main__":
    # tag existing parsed data
    if os.path.exists(OUT):
        with open(OUT) as f:
            courses = json.load(f)
        try:
            for course in sorted(courses):
                data = courses[course]
                if "category" not in data:
                    data["category"] = \
                        CATEGORIES[get_category(f"{course} {data['title']}")]
                if isinstance(data["category"], int):
                    data["category"] = CATEGORIES[int(data["category"])]
        # if KeyboardInterrupt or other exception, write to file
        except:
            pass
    # read data from stdin
    else:
        courses, course = {}, []
        for line in sys.stdin:
            line = line.strip()
            course.append(line)
            if line == END:
                course, data = parse_course(course)
                courses[course] = data
                course = []

    with open(OUT, "w") as f:
        json.dump(courses, f, indent=4, sort_keys=True)

