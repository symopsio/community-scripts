# Author: Adam Buggia <adam@symops.io>
# Author: Joshua Timberman <joshua@symops.io>
#
# Copyright: (c) SymOps, Inc.
# License: BSD-3-Clause
#

import boto3
import sys
import botocore
import csv
import click
from tabulate import tabulate
from collections import namedtuple


class IdentityStore:
    def __init__(self, identitystore_id=None):
        self.Elements = namedtuple("Elements", "arn store_id")
        self.identitystore = boto3.client("identitystore")
        self.ssoadmin = boto3.client("sso-admin")
        self.instance_elements = self._pull_identitystore_elements()

        if identitystore_id:
            self.identitystore_id = identitystore_id
        else:
            self.identitystore_id = self.instance_elements.store_id

        self.arn = self.instance_elements.arn

    def _pull_identitystore_elements(self):

        try:
            response = self.ssoadmin.list_instances()

        except botocore.errorfactory.AccessDeniedException:
            sys.exit("Access Denied: you need permissions to list SSO Instances")

        instances = response.get("Instances", [])

        if len(instances) == 1:
            return self.Elements(*instances[0].values())

        error = (
            "No AWS SSO instances found for the current account"
            if len(instances) == 0
            else "Found more than one AWS SSO instance. Please specify the Identity store ID via the --identitystore-id option"
        )
        sys.exit(error)

    def get_userids(self, usernames):

        userdata = [["Email", "InstanceArn", "PrincipalId"]]

        for username in usernames:
            response = self.identitystore.list_users(
                IdentityStoreId=self.identitystore_id,
                MaxResults=50,
                Filters=[{"AttributePath": "UserName", "AttributeValue": username}],
            )

            users = response.get("Users", [])

            if not users:
                sys.exit(f"Could not find a UserId for Username: {username}")

            userdata.append([username, self.arn, users[0]["UserId"]])

        return userdata


@click.command()
@click.option("--identitystore-id", help="Specify a particular IdentityStoreId")
@click.option("--outfile", help="Write output to a CSV file")
@click.option("--infile", help="Read in a CSV for users to look up")
@click.argument("usernames", nargs=-1)
def main(identitystore_id, outfile, infile, usernames):

    if infile:
        usernames = []
        with open(infile) as csvfile:
            csv_reader = list(csv.reader(csvfile, delimiter=","))
            for rows in csv_reader[1:]:
                usernames.append(rows[0])

    idstore = IdentityStore(identitystore_id)
    userdata = idstore.get_userids(usernames)

    print(tabulate(userdata[1:], headers=userdata[0]))

    if outfile:
        with open(outfile, "w") as csvfile:
            csv.writer(csvfile, quoting=csv.QUOTE_ALL).writerows(userdata)
        print(f"\nWrote {len(userdata) - 1} rows to {outfile}")

if __name__ == "__main__":
    main()
