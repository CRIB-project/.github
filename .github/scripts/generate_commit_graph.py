import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Get Access Token from the secrets environment and the organization name
GITHUB_TOKEN = os.getenv("TOKEN_MADE_BY_OKAWA")
ORG_NAME = "crib-project"

# Base URL of the GitHub
BASE_URL = "https://api.github.com"

# Half-year range
end_date = datetime.now() + timedelta(days=1)  # include the current day
start_date = end_date - timedelta(days=180)


# make a list of the date (string)
def get_weekly_dates():
    weeks = []
    current = start_date
    while current <= end_date:
        week_str = current.strftime("%Y-%m-%d")
        weeks.append(week_str)
        # move to next week
        current += timedelta(days=7)
    return weeks


# get commit numbers of each repository per week
def get_commit_counts_by_week(repo_name):
    url = f"{BASE_URL}/repos/{ORG_NAME}/{repo_name}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    commit_counts = defaultdict(int)

    page = 1
    while True:
        params = {
            "since": start_date.isoformat(),
            "until": end_date.isoformat(),
            "page": page,
            "per_page": 100,
        }
        response = requests.get(url, headers=headers, params=params)
        commits = response.json()
        if not commits:
            break

        for commit in commits:
            commit_date = commit["commit"]["committer"]["date"]
            commit_week = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
            # コミット日を週の開始日に丸める
            week_start = (commit_week - timedelta(days=commit_week.weekday())).strftime(
                "%Y-%m-%d"
            )
            commit_counts[week_start] += 1

        page += 1
        time.sleep(1)  # for API request limits

    return commit_counts


# get total number of commits from all repository per week
def generate_commit_graph():
    weeks = get_weekly_dates()

    # get all repository name
    url = f"{BASE_URL}/orgs/{ORG_NAME}/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    repos = [repo["name"] for repo in response.json() if not repo["private"]]

    total_commit_counts = defaultdict(int, {week: 0 for week in weeks})  # initialize 0
    for repo in repos:
        repo_commit_counts = get_commit_counts_by_week(repo)
        for week, count in repo_commit_counts.items():
            total_commit_counts[week] += count

    commit_counts = [total_commit_counts[week] for week in weeks]

    # make a month label for x-axis
    month_labels = []
    for week in weeks:
        date = datetime.strptime(week, "%Y-%m-%d")
        if date.day <= 7:
            month_labels.append(date.strftime("%Y-%m"))
        else:
            month_labels.append("")

    # graph settings
    size = 4.0
    plt.figure(figsize=(1.618 * size, 1.0 * size))
    plt.bar(weeks, commit_counts, color="blue", alpha=0.3)
    plt.title("Total Commits per Week", fontsize=20)
    plt.xticks(weeks, month_labels, rotation=45, ha="right")
    plt.yticks(fontsize=16)
    plt.ylim(0, None)
    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    plt.tight_layout()

    plt.savefig(".github/scripts/commit_graph.png")


if __name__ == "__main__":
    generate_commit_graph()
