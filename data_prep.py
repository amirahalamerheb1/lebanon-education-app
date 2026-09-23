import re
import pandas as pd

LEVELS = {
    "PercentageofEducationlevelofresidents-illeterate": "Illiterate",
    "PercentageofEducationlevelofresidents-elementary": "Elementary",
    "PercentageofEducationlevelofresidents-intermediate": "Intermediate",
    "PercentageofEducationlevelofresidents-vocational": "Vocational",
    "PercentageofEducationlevelofresidents-secondary": "Secondary",
    "PercentageofEducationlevelofresidents-university": "University",
    "PercentageofEducationlevelofresidents-highereducation": "Higher education",
}
LEVEL_ORDER = list(LEVELS.values())
DISTRICT_FIX = {
    "Miniyeh Danniyeh": "Miniyeh-Danniyeh",
    "Zahle": "Zahle",
    "Tripoli District, Lebanon": "Tripoli",
}


def _clean_district(url: str) -> str:
    name = str(url).split("/")[-1].replace("_", " ")
    name = name.replace(" District, Lebanon", "").replace(" District", "")
    # the raw file has mojibake in two names (Miniyeh-Danniyeh, Zahle)
    if name.startswith("Miniyeh"):
        return "Miniyeh-Danniyeh"
    if name.startswith("Zahl"):
        return "Zahle"
    return name


def load(path: str = "lebanon_education.csv"):
    raw = pd.read_csv(path)
    df = raw.rename(columns={**LEVELS, "PercentageofSchooldropout": "School dropout"})
    df["Governorate"] = (df["refArea Governorate"].str.split("/").str[-1]
                         .str.replace("_Governorate", "").str.replace("_", " "))
    df["District"] = df["refArea District"].map(_clean_district)
    df["Town"] = df["Town"].str.strip()

    total = df[LEVEL_ORDER].sum(axis=1, min_count=len(LEVEL_ORDER))
    complete = df[LEVEL_ORDER].notna().all(axis=1)
    valid = complete & total.between(80, 120)
    clean = df[valid].copy()
    # rescale each town so its seven levels sum to exactly 100
    clean[LEVEL_ORDER] = clean[LEVEL_ORDER].div(total[valid], axis=0) * 100
    clean.loc[clean["School dropout"] > 100, "School dropout"] = pd.NA
    report = {
        "raw_rows": len(raw),
        "missing": int((~complete).sum()),
        "bad_total": int((complete & ~total.between(80, 120)).sum()),
        "kept": len(clean),
    }
    cols = ["Town", "District", "Governorate", *LEVEL_ORDER, "School dropout"]
    return clean[cols].reset_index(drop=True), report
