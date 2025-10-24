from urllib.parse import parse_qs

# Map query keys -> human labels (adjust to your fields)
LABELS = {
    "q": "Keywords",
    "skills": "Skills",
    "location": "Location",
    "education": "Education",
    "exp_min": "Min YOE",
    "salary_range": "Salary",
    "job_type": "Job Type",
    "work_type": "Work Type",
    "visa_sponsorship": "Visa",
}

def pretty_filters_from_querystring(qs: str):
    """
    Turn 'q=Research&skills=&location=' into a list of (label, value) pairs,
    skipping empties and normalizing a couple values.
    """
    if not qs:
        return []

    parsed = parse_qs(qs, keep_blank_values=False)
    items = []
    for key, vals in parsed.items():
        if not vals:
            continue
        val = vals[0]
        if not val:
            continue

        label = LABELS.get(key, key)

        # Normalize a few known values
        if key == "salary_range":
            if val.endswith("+"):
                val = f"${val[:-1]}+"
            elif "-" in val:
                lo, hi = val.split("-", 1)
                val = f"${lo}–${hi}"
        elif key == "visa_sponsorship":
            val = "Yes" if val == "Y" else "No" if val == "N" else val

        items.append((label, val))
    return items
