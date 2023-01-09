#! /usr/bin/env python3


from datetime import timedelta as td
from datetime import datetime as dt
from pathlib import PosixPath
from typing import List, Tuple

from sgqlc.endpoint.http import HTTPEndpoint

# local imports
from config import Cfg

# generated from gql schema:
from schema import PullRequestEdge
from operations import Operations


GITHUB_URL = "https://api.github.com/graphql"

BASE_HEADERS = {"Authorization": f"Bearer {Cfg().cfg['github']['secret']}"}

ENDPOINT = HTTPEndpoint(GITHUB_URL, base_headers=BASE_HEADERS)


# ----
# ---- GraphQL queries


def repo_query() -> Tuple[str, List[PullRequestEdge]]:
    # get the first open PR - this is the parent PR for each week's post
    initial_query = Operations.query.get_first_pr

    data = ENDPOINT(initial_query)
    repo = (initial_query + data).repository
    cursor = repo.pull_requests.edges[0].cursor
    title = repo.pull_requests.edges[0].node.title

    full_query = Operations.query.get_all_prs
    data = ENDPOINT(full_query, {"cursor": cursor})
    prs = (full_query + data).repository.pull_requests.edges

    # maybe return the parent PR baseRef here too so i know what to target later
    return title, prs


if __name__ == "__main__":
    q = repo_query()
    print(q)
