# Author: Joshua Timberman <joshua@symops.io>
# Copyright: (c) SymOps, Inc.
# License: BSD-3-Clause
#

import json
import pdpyras
import click


@click.command()
@click.option(
    "--token", help="PagerDuty API token", envvar="PD_API_TOKEN", show_envvar="PD_API_TOKEN"
)
@click.option("--match", help="Show users that match the specified string")
@click.option("--email-only", is_flag=True, default=False, help="Show only the email addresses")
def main(token, match, email_only):
    if not token:
        print("You must supply a token, use `--token` or export `PD_API_TOKEN` in your shell")
        exit(1)

    session = pdpyras.APISession(token)
    if match:
        query = {"query": match}
    else:
        query = {}

    for user in session.iter_all("users", params=query):
        display = [user["email"]]
        if not email_only:
            display.append(user["name"])
        print(",".join(display))


if __name__ == "__main__":
    main()
