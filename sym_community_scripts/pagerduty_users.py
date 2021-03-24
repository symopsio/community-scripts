# Author: Joshua Timberman <joshua@symops.io>
# Copyright: (c) SymOps, Inc.
# License: BSD-3-Clause
#

import pdpyras
import click
import sys
import csv
import io
from tabulate import tabulate


def display(table):
    print(tabulate(table, headers=["Email", "Name"]))

def session(api_token):
    return pdpyras.APISession(api_token)

@click.command()
@click.option(
    "--token", help="PagerDuty API token", envvar="PD_API_TOKEN", show_envvar="PD_API_TOKEN"
)
@click.option("--match", help="Show users that match the specified string")
@click.option("--email-only", is_flag=True, default=False, help="Show only the email addresses")
@click.option("--outfile", help="Write output to a CSV file")
def main(token, match, email_only, outfile):
    userdata = []

    if not token:
        print("You must supply a token, use `--token` or export `PD_API_TOKEN` in your shell")
        exit(1)

    if match:
        query = {"query": match}
    else:
        query = {}

    for user in session(token).iter_all("users", params=query):
        row = [user["email"]]
        if not email_only:
            row.append(user["name"])
        userdata.append(row)

    display(userdata)

    if outfile:
        with open(outfile, 'w') as csvfile:
            csv.writer(csvfile, quoting=csv.QUOTE_ALL).writerows(userdata)


if __name__ == "__main__":
    main()
