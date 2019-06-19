#!/usr/bin/env python3
import re

import click
from jira import JIRA
import typing as t

from jira.resources import Version

JIRA_SERVER_URL = "https://jira.XXX.com

description_template = """{{original_version_id}} {JIRA_SERVER_URL}/browse/WWSD/fixforversion/{{original_version_id}}/""".format(JIRA_SERVER_URL=JIRA_SERVER_ULR)

version_pattern = re.compile("wows( |_)(\d+\.?){3}_(\w*)")
version_identifier_pattern = re.compile("(?P<version_id>\d{5,6}) .*")


def get_versions_for_creation(
    original_versions: t.List[Version], target_versions: t.List[Version]
) -> t.List[Version]:
    """
    Match version by identifier in description. Allow change version name and add some extra useful information.
    :param original_versions:
    :param target_versions:
    :return:
    """
    diff = set([v.id for v in original_versions]).difference(
        set(
            [
                version_identifier_pattern.match(v.description).groupdict()[
                    "version_id"
                ]
                for v in target_versions
                if version_identifier_pattern.match(v.description)
            ]
        )
    )
    return [v for v in original_versions if v.id in diff]


def create_versions(jira: JIRA, project: str, versions: t.List[Version]):
    if len(versions) == 0:
        click.echo("\nThere is no versions for creation")
    else:
        click.echo("\nVersions for creation:")

        for version in versions:
            click.echo("- {}".format(version.name))

        if click.confirm(
            "Do you want to create this versions in {project} project?".format(
                project=project
            )
        ):

            with click.progressbar(versions) as versions_bar:
                for version in versions_bar:
                    jira.create_version(
                        name=version.name,
                        project=project,
                        description=description_template.format(
                            original_version_id=version.id
                        ),
                    )


@click.command()
@click.option("-u", "--username", type=str, help="Jira username")
@click.option(
    "-p", "--password", prompt=True, hide_input=True, confirmation_prompt=True
)
@click.option(
    "-o", "--origin-project", type=str, help="Origin Jira project name",
)
@click.option(
    "-t",
    "--target-project",
    type=str,
    help="Target Jira project name",
)
@click.option("-v", "--verbose", is_flag=True, default=False)
def main(username, password, origin_project, target_project, verbose):
    jira = JIRA(JIRA_SERVER_URL, basic_auth=(username, password))

    _origin_project_versions = jira.project_versions(origin_project)
    origin_project_versions = [
        version
        for version in _origin_project_versions
        if version_pattern.match(version.name) is not None
    ]

    _target_project_versions = jira.project_versions(target_project)
    target_project_versions = [
        version
        for version in _target_project_versions
        if version_pattern.match(version.name) is not None
    ]

    if verbose:
        click.echo("\nOriginal project versions")
        for version in origin_project_versions:
            click.echo("- {}".format(version.name))

        click.echo("\nTarget project versions")
        for version in origin_project_versions:
            click.echo("- {}".format(version.name))

    # Put diff of original and target
    versions_to_creation = get_versions_for_creation(
        origin_project_versions, target_project_versions
    )
    create_versions(jira, target_project, versions_to_creation)

    # Put diff by status
    # version_to_status_update = []


if __name__ == "__main__":
    main()
