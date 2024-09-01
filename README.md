# jabroni

Scraping vacancies from internet

Helped me to find a job, may help you

The code uses search engines to search for jobs indexed on certain job board providers

Then it goes to those specific job board providers and scrapes all jobs from there

Finally, using some very simple NLP the code ranks all the jobs and creates a spreadsheet with all the most interesting ones

## How to run
```
pip install playwright bs4 pydantic tqdm

python -m playwright install chromium

python link_extractor.py
```

The code will run for around half an hour

Then check cache_dir/<run_timestamp>/intersting_jobs.csv for the vacancies

## Things to tweak

link_extractor.py - line 158, can change search terms to your liking

ranker.py - line 8, change weights and terms based on your needs

ranker.py - line 86, can change n=2 to different values if you want more than two jobs per company

## Why async?

So that the code runs easily both in a Jupyter Notebook and as a script

When using Jupyter Notebook no need to wrap function calls into ```asyncio.run()```

Developing in Jupyter Notebook helps me to see all intermediate states of the browser

and ability to pause at any given time
