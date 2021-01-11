import boto3
import argparse
import sys
import botocore


class IdentityStore:
    def __init__(self, identitystore_id=None):
        self.identitystore = boto3.client("identitystore")
        self.ssoadmin = boto3.client("sso-admin")

        if identitystore_id:
            self.identitystore_id = identitystore_id
        else:
            self.identitystore_id = self._pull_identitystore_id()

    def _list_users(self, **filters):

        attrval_filters = [{"AttributePath": k, "AttributeValue": v} for k, v in filters.items()]

        return self.identitystore.list_users(
            IdentityStoreId=self.identitystore_id, MaxResults=50, Filters=attrval_filters
        )

    def _pull_identitystore_id(self):

        try:
            response = self.ssoadmin.list_instances()

        except botocore.errorfactory.AccessDeniedException:
            sys.exit("Access Denied: you need permissions to list SSO Instances")


        instances = response.get("Instances", [])

        if len(instances) == 1:
            return instances[0]["IdentityStoreId"]

        error = (
            "No AWS SSO instances found for the current account"
            if len(instances) == 0
            else "Found more than one AWS SSO instance. Please specify the Identity store ID via the --identitystore_id option"
        )
        sys.exit(error)

    def get_userid(self, username):

        response = self._list_users(UserName=username)

        users = response.get("Users", [])

        if len(users) < 1:
            sys.exit(f"Could not find a UserId for Username: {username}")

        return users[0]["UserId"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--identitystore_id")
    parser.add_argument("username")
    args = parser.parse_args()

    idstore = IdentityStore(args.identitystore_id)
    userid = idstore.get_userid(args.username)

    print(userid)
