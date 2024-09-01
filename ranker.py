import re
from pathlib import Path

import pandas as pd
from utils import read_tjson

job_title_weights = [
    ("python", 0.8),
    ("machine", 0.8),
    ("ml", 0.8),
    ("quantitative", 0.8),
    ("scientist", 0.8),
    ("deep", 0.8),
    ("data", 0.3),
    ("ai", 0.3),
    ("analyst", 0.3),
    ("analytics", 0.3),
    ("fraud", 0.3),
    ("intelligence", 0.3),
    ("artificial", 0.3),
    ("mlops", 0.3),
    ("recommendations", 0.3),
    ("recommendation", 0.3),
    ("full", 0.15),
    ("stack", 0.15),
    ("engineer", 0.15),
    ("developer", 0.15),
    ("software", 0.15),
    ("engineering", 0.15),
    ("development", 0.15),
    ("researcher", 0.15),
    ("senior", 0.05),
    ("azure", 0.05),
    ("remote", 0.05),
    ("sr", 0.05),
    ("staff", 0.05),
    ("lead", 0.05),
]


def calculate_column_score(column, term_weights, preprocessor):
    def score_function(x):
        score = 0
        for term in x:
            if term in term_weights:
                score += term_weights[term]
        return score

    col = column.apply(preprocessor)
    col = col.apply(score_function)
    return col.rank(pct=True)


dummy_preprcessor = lambda x: x


def remove_punctuation(text):
    return re.sub(r"[^\w\s]", " ", text)


def preprocess(text):
    text = text.replace("\n", " ")
    text = remove_punctuation(text)
    text = text.lower()
    return text


def text_preprocessor(x):
    return set(preprocess(x).split(" "))


def interesting_geography(x: str):
    good_keywords = ["remote", "york", "toronto", "canada"]
    bad_keywords = ["india", "poland", "jamaica"]
    if x is None:
        return False
    for keyword in bad_keywords:
        if keyword in x.lower():
            return False
    for keyword in good_keywords:
        if keyword in x.lower():
            return True
    return False


def filter_by_score(df, score_columnn, groupby_column, n=2):
    top_2_rows = df.groupby(groupby_column)[score_columnn].nlargest(n)
    new_df = df.loc[top_2_rows.index.get_level_values(1)]
    return new_df.sort_values(by=[groupby_column, score_columnn], ascending=False)


def generate_intersting_job_csv(rundir, out_name):
    all_jobs = []
    all_tjson = Path(rundir).glob("./**/jobs.tjson")
    all_jobs = pd.concat([pd.DataFrame(read_tjson(x)) for x in all_tjson])
    all_jobs["job_score"] = calculate_column_score(
        all_jobs["job_title"], dict(job_title_weights), text_preprocessor
    )
    mask = all_jobs["job_location"].apply(interesting_geography)
    jobs_df = all_jobs[mask]
    jobs_df = filter_by_score(jobs_df, "job_score", "company_job_website")
    jobs_df = jobs_df.sort_values("job_score", ascending=False)
    jobs_df.to_csv(Path(rundir) / out_name, index=False)


if __name__ == "__main__":
    generate_intersting_job_csv(
        rundir="./cache_dir/2024-08-31 23:23:22", out_name="interesting_jobs.csv"
    )
