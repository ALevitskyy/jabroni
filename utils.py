import json
import time
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright
from playwright.async_api._generated import Page
from tqdm import tqdm


@asynccontextmanager
async def init_browser_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page: Page = await browser.new_page()
        try:
            yield page
        finally:
            await page.close()
            await browser.close()


def get_datetime() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


async def async_write_json_stream(async_func, iterable, path):
    with open(path, "a", encoding="utf-8") as f:
        for item in tqdm(iterable):
            try:
                res = await async_func(item)
                for x in res:
                    json.dump(x.dict(), f)
                    f.write("\n")
            except Exception as e:
                print("error processing", item, e)
                continue


def read_tjson(filename):
    with open(filename, "r") as file:
        data = file.readlines()
        tjson = []
        for row in data:
            try:
                tjson.append(json.loads(row))
            except:
                continue
    return tjson
