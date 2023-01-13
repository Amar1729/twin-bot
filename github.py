#! /usr/bin/env python3


import re
from base64 import b64encode
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


def get_base_path(pr: PullRequestEdge) -> PosixPath:
    pth = PosixPath(pr.node.files.edges[0].node.path)

    # naive checking for now, until i add more proper tests
    if pth.parts[0] != "contents":
        raise Exception(f"Path changed - update: {pth}")
    if len(pth.parts) < 5:
        raise Exception(f"Path changed - update: {pth}")

    return PosixPath(*pth.parts[:4])


def canonical(plugin_name: str) -> str:
    canonical = plugin_name.replace(".nvim", "")
    return re.sub(r"[ .]", "-", canonical)


# ----
# ---- GraphQL queries


def repo_query() -> Tuple[str, List[PullRequestEdge]]:
    # get the first open PR - this is the parent PR for each week's post
    initial_query = Operations.query.get_first_pr

    data = ENDPOINT(initial_query)
    repo = (initial_query + data).repository
    cursor = repo.pull_requests.edges[0].cursor
    branch_name = repo.pull_requests.edges[0].node.head_ref.name

    full_query = Operations.query.get_all_prs
    data = ENDPOINT(full_query, {"cursor": cursor})
    prs = (full_query + data).repository.pull_requests.edges

    # maybe return the parent PR baseRef here too so i know what to target later
    return branch_name, prs


def sync_twin_branch() -> Tuple[str, str, str]:
    """Sync branches from upstream.

    Returns:
        A 3-tuple of:
            - the upstream repo ID
            - forked repo ID
            - ID of the non-master (i.e. this week's TWiN) branch
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

    # return:
    # repository ID
    # ID of the only non-master branch in our fork (after we sync from upstream)
    for ref_name in refs_upstream:
        if ref_name != "master":
            return (repo_upstream.id, repo_fork.id, refs_fork[ref_name])

    raise Exception("non-master branch not found in upstream.")


def create_commit_mutation(
    repo_id: str,
    base_ref: str,
    commit_msg: str,
    file_path: PosixPath,
    contents: str,
):
    b64_contents = b64encode(contents.encode()).decode()
    repo_name_with_owner = "amar1729/this-week-in-neovim-contents"

    # create a branch for the new commit to live on
    d = dt.utcnow()
    branch_name = d.strftime("patch-%d%H%M")
    ENDPOINT(
        Operations.mutation.create_branch,
        {"name": f"refs/heads/{branch_name}", "base_ref": base_ref, "repo_id": repo_id},
    )

    # create the commit
    create_commit = Operations.mutation.create_commit

    variables = {
        "repoName": repo_name_with_owner,
        "branchName": branch_name,
        "head": base_ref,
        "commitMsg": commit_msg,
        "filePath": str(file_path),
        "contents": b64_contents,
    }

    ENDPOINT(create_commit, variables)


def create_pr_mutation(
    title: str,
    repo_id: str,
    head_ref: str,
    base_ref: str,
) -> str:
    """Create a PR on phaazon/this-week-in-neovim-contents.

    Args:
        title (str): The title of the PR.
        repo_id (str): The repo ID of the target repo (? should this be required ?).
        head_ref (str): The name of the source branch (user:branch).
        base_ref (str): The name of the target branch (user:branch).

    Returns:
        URL of the opened pull request.
    """

    body = "Automated PR, created by twin-bot - @Amar1729"

    variables = {
        "title": title,
        "repoId": repo_id,
        "headRef": head_ref,
        "baseRef": base_ref,
        "body": body,
    }

    data = ENDPOINT(Operations.mutation.create_pr, variables)
    return data["data"]["createPullRequest"]["pullRequest"]["url"]


# ----


def count_sections(prs: List[PullRequestEdge]) -> List[int]:
    """Find the next available number for each section.

    Args:
        prs: all pull requests for this week (open and closed).

    Returns:
        list of max current number for each section.
    """
    sections = [0] * 7

    # for node in results["data"]["repository"]["pullRequests"]["edges"]:
    for pr in prs:
        # files = pr.node.files.edges[0].node.path
        files = pr.node.files.edges

        if len(files) > 1:
            print("Found a PR with more files than expected, continuing.")
            continue

        file = files[0].node.path
        pth = PosixPath(file)

        # should be robust for paths with 6 (new plugins, updated plugins)
        # or 5 (did you know) components
        section, *fp = map(
            lambda s: int(s.split("-")[0]),
            pth.parts[4:],
        )

        if fp:
            fp_int = fp[0]
        else:
            fp_int = 1

        sections[section] = max(sections[section], fp_int)

    return sections


def open_pull_req(
    section: int,
    plugin_name: str,
    contents: str,
) -> str:
    """Opens a new Pull Request on github for the given changes.

    This function does several things:
        - query the origin repository to see what Nth change we're about to make
        - sync the current TWiN branch if necessary
        - create a new branch based off of the current TWiN branch
        - create a new commit in that branch
        - open the actual PR, with the new branch targeting the base branch

    Note: this currently only supports new/updated plugins.

    Args:
        section: for which section of TWiN to open a PR.
        plugin_name: name of the plugin.
        contents: string content of the markdown file to add.

    Returns:
        URL of opened pull request.

    Raises:
        Exception: if an invalid 'section' is passed.
    """
    branch_name, prs = repo_query()
    sections = count_sections(prs)

    base_path = get_base_path(prs[0])

    id_upstream, id_fork, weekly_base_ref = sync_twin_branch()

    # commit message
    if section == 3:
        commit_msg = f"[new plugin]: {plugin_name}"
        dir_path = "3-new-plugins"
    elif section == 4:
        commit_msg = f"[plugin update]: {plugin_name}"
        dir_path = "4-updates"
    else:
        raise Exception(f"Invalid section: {section}")

    file_path = base_path / dir_path / f"{sections[section] + 1}-{canonical(plugin_name)}.md"

    create_commit_mutation(
        repo_id=id_fork,
        base_ref=weekly_base_ref,
        commit_msg=commit_msg,
        file_path=file_path,
        contents=contents,
    )

    args = [
        id_upstream,
        f"Amar1729:{branch_name}",
        f"phaazon:{branch_name}",
    ]

    dbg = True
    if dbg:
        args = [
            id_fork,
            branch_name,
            "master",
        ]

    result = create_pr_mutation(
        # use commit msg as title
        commit_msg,
        *args,
    )

    return result


if __name__ == "__main__":
    # TODO - test this functionality by simply passing a reddit URL?
    pass
