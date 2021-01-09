import boto3
import argparse
import sys


class IdentityStore:
    def __init__(self, identitystore_id):
        self.identitystore_id = identitystore_id
        self.identitystore = boto3.client("identitystore")

    def _list_users(self, **filters):

        attrval_filters = [{"AttributePath": k, "AttributeValue": v} for k, v in filters.items()]

        return self.identitystore.list_users(
            IdentityStoreId=self.identitystore_id, MaxResults=50, Filters=attrval_filters
        )

    def get_userid(self, username):
        response = self._list_users(UserName=username)

        users = response.get("Users", [])

        if len(users) < 1:
            print(f"Could not find a UserId for Username: {username}", file=sys.stderr)
            raise (SystemExit())

        return users[0]["UserId"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("identitystore_id")
    parser.add_argument("username")
    args = parser.parse_args()

    idstore = IdentityStore(args.identitystore_id)
    userid = idstore.get_userid(args.username)
    print(userid)
