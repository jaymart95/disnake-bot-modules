from aiohttp import ClientSession
from json import dump, load
from html import unescape


async def fetch_categories():
    '''Scrape the categories API and return the ID: Category list items'''
    url = "https://opentdb.com/api_category.php"
    async with ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            return data["trivia_categories"]


async def update_categories():
    '''
    Reformat the ID: Category name to Category Name: ID and store in JSON
    Only runs once when the bot is first started to ensure most up to date categories
    '''
    categories = await fetch_categories()
    new_data = {}
    new_data["categories"] = []

    for row in categories:
        new_data["categories"].append({row["name"]: row["id"]})

        with open("./cogs/_trivia/data/categories.json", "w") as x:
            dump(new_data, x, indent=4)


async def get_category_id(category):
    '''
    Returns the category ID for the api url where category has been specified

    Parameters
    ----------
    category: (str) The category name passed from the /trivia question command

    Returns
    -------
    The category ID
    '''
    with open("./cogs/_trivia/data/categories.json") as f:
        data = load(f)["categories"]

        for item in data:
            for k, v in item.items():
                if k == category:
                    return v


async def trivia_question(category=None, difficulty=None):
    '''
    Fetch the trivia question from the API based on if a category and/or difficulty is present
    Assign bonus points based on which arguments are passed.

    Parameters
    ---------
    category: (str) The category passed from the /trivia question command (Defaults None)
    difficulty: (str) The difficulty passed from the /trivia question command (Defaults None)

    Returns
    -------
    Trivia question and info: category, difficulty, correct answer, wrong answers
    Calculated points (includes bonus)
    '''
    if category and difficulty:
        cat_id = await get_category_id(category)
        url = f"https://opentdb.com/api.php?amount=1&category={cat_id}&difficulty={difficulty}"
        print(url)
        bonus = 0
    elif category is None and difficulty:
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}"
        bonus = 5

    elif category and difficulty is None:
        cat_id = await get_category_id(category)
        url = f"https://opentdb.com/api.php?amount=1&category={cat_id}"
        bonus = 5
    else:
        url = f"https://opentdb.com/api.php?amount=1"
        bonus = 10

    async with ClientSession() as session:
        async with session.get(url) as r:
            response = await r.json()

    print(response)
    results = response["results"][0]
    points = get_points(results['difficulty'])
    points += bonus

    return (
        results["category"].title(),
        results["difficulty"].title(),
        unescape(results["question"]),
        unescape(results["correct_answer"]),
        results["incorrect_answers"],
        points
        )


def get_points(difficulty):
    if difficulty == 'hard':
        return 30
    elif difficulty == 'medium':
        return 20
    else:
        return 10