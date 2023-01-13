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


def sync_twin_branch() -> str:
    """Sync branches from upstream.

    Returns:
        The ID of the non-master (i.e. this week's TWiN) branch.
    """
    get_refs = Operations.query.get_refs

    # get refs from upstream
    data_upstream = ENDPOINT(get_refs, {"owner": "phaazon"})
    repo_upstream = (get_refs + data_upstream).repository

    # "sort" this so the "master" ref gets inserted into this dict first
    refs_upstream = {
        ref.node.name: ref.node.target.oid
        for ref in repo_upstream.refs.edges
        if ref.node.name == "master"
    }

    for ref in repo_upstream.refs.edges:
        if ref.node.name != "master":
            refs_upstream[ref.node.name] = ref.node.target.oid

    # get node IDs from my fork
    data_fork = ENDPOINT(get_refs, {"owner": "amar1729"})
    repo_fork = (get_refs + data_fork).repository

    refs_fork = {
        # note: .id not .target.oid
        ref.node.name: ref.node.id
        for ref in repo_fork.refs.edges
    }

    # assume that upstream only has 'master' and this week's branch
    # so only update those refs
    # NOTE: this should update the master ref first, and then other refs
    # (since refs_upstream should have 'master' ref first due to insertion order)
    push_branch = Operations.mutation.sync_upstream
    create_branch = Operations.mutation.create_branch
    for ref_name, ref_target in refs_upstream.items():
        if ref_name not in refs_fork:
            # create ref (branch) if it doesn't exist in my fork
            data = ENDPOINT(
                create_branch,
                {
                    "name": f"refs/heads/{ref_name}",
                    "baseRef": refs_upstream["master"],
                    "repoId": repo_fork.id,
                }
            )

            ref = data["data"]["createRef"]["ref"]["id"]
            refs_fork[ref_name] = ref

        ENDPOINT(
            push_branch,
            {"refId": refs_fork[ref_name], "oid": ref_target},
        )

    # return the ID of the only non-master branch in our fork (after we sync from upstream)
    for ref_name in refs_upstream:
        if ref_name != "master":
            return refs_fork[ref_name]

    raise Exception("non-master branch not found in upstream.")


if __name__ == "__main__":
    q = repo_query()
    print(q)
