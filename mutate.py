import re

import requests


URL = "https://raw.githubusercontent.com/phaazon/this-week-in-neovim-contents/master/template"


def get(section: int) -> str:
    """Get raw content of template files from master branch of repo.

    Args:
        section (int): Which section's template to get, as an int.

    Returns:
        String content of template file.
    """
    if section == 3:
        # section 3: new plugins
        section_name = "3-new-plugins"
    elif section == 4:
        # section 4: updates to plugins
        section_name = "4-updates"
    else:
        raise Exception("unimplemented")

    url = f"{URL}/{section_name}/1-example.md"

    resp = requests.get(url)
    return resp.content.decode()


def mutate(reddit: str, git_repo: str, section: int) -> str:
    """Update string content from a section's template with given info.

    Args:
        reddit (str): reddit link.
        git_repo (str): github repository link.
        section (int): section number (3 for new plugins, 4 for updates, etc).

    Returns:
        Updated string content.
    """
    content = get(section)

    # get repository name of a github link - the last part of its path
    path = list(filter(lambda x: bool(x), git_repo.split("/")))

    author = path[-2]
    plugin_name = path[-1].replace(".git", "")

    # TODO: parse this from first section of non-header lines from project README
    # (we'll assume existence of README.md or README.rst (or README?))
    plugin_desc = ""
    if not plugin_desc.endswith("."):
        plugin_desc += "."

    plugin_desc += f"By [@{author}](https://github.com/{author})."

    # TODO: parse this from README
    media_link = ""

    if section == 3:
        target = "new-your-plugin"
    elif section == 4:
        target = "update-your-plugin"
    else:
        raise Exception

    new_content = content.replace(f'"{target}.nvim"', f'"{plugin_name}"')
    new_content = content.replace(f'"#{target}.nvim"', f'"#{plugin_name}"')
    new_content = content.replace(f'<span>{target}.nvim</span>', f'<span>{plugin_name}</span>')

    if media_link:
        md_link = f"[{plugin_name}]({media_link})"
        new_content = re.sub(r"\!\[your-plugin\.nvim.*", md_link, new_content)  # ]

    if section == 3:
        # Introduce your plugin! ...
        new_content = re.sub(r"Introduce.*", plugin_desc, new_content)
    elif section == 4:
        # > One-liner description of ...
        new_content = re.sub(r"> One-liner description.*", plugin_desc, new_content)
        # \n media_link \n
        # Explain what has changed.
        # TODO - could i allow this to be passed as str when invoking twin-bot from reddit?
        new_content = re.sub(r"Explain what has changed.", "TODO by plugin author", new_content)

    new_content.replace("https://link-to-the-reddit-post", reddit)
    new_content.replace("https://link-to-the-github-project", git_repo)

    return new_content
