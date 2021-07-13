from functools import cached_property
from typing import Dict, Generator, Optional, Set

import boto3
import inquirer
from botocore.exceptions import BotoCoreError, ClientError

from .integration import Integration, IntegrationException


class _AWSPaginator:
    def __init__(self, client, method, key) -> None:
        self.fn = getattr(client, method)
        self.key = key
        self.next_token = None

    def paginate(self, **kwargs) -> Generator[Dict, None, None]:
        while True:
            if self.next_token:
                kwargs["NextToken"] = self.next_token
            res = self.fn(**kwargs)
            for item in res.get(self.key, []):
                yield item
            if not res.get("NextToken"):
                break
            self.next_token = res["NextToken"]


class IAM(Integration, slug="iam"):
    @cached_property
    def _iam(self):
        return boto3.client("iam")

    def prompt_for_creds(self) -> None:
        try:
            self._iam.get_user()
        except self._iam.exceptions.AccessDeniedException:
            raise IntegrationException("Access Denied: Please ensure you can GetUser for AWS IAM.")
        except (ClientError, BotoCoreError) as e:
            raise IntegrationException(str(e))

    def _fetch_user(self, user_name: str):
        try:
            user = self._iam.get_user(UserName=user_name)
        except self._iam.exceptions.NoSuchEntityException:
            return None
        return user["User"]["Arn"]

    def fetch(self, user_names: Set[str]) -> Dict[str, str]:
        results = {}
        for user_name in user_names:
            if (id := self._fetch_user(user_name)) :
                results[user_name] = id
        return results


class SSO(Integration, slug="aws_sso"):
    def __init__(self) -> None:
        self.instances = []

    def _get_sso_instances(self) -> Dict[str, str]:
        sso_admin = boto3.client("sso-admin")
        try:
            instances = sso_admin.list_instances()
        except sso_admin.exceptions.AccessDeniedException:
            raise IntegrationException(
                "Access Denied: Please ensure you can ListInstances for AWS SSO Admin."
            )
        except (ClientError, BotoCoreError) as e:
            raise IntegrationException(str(e))

        return {i["InstanceArn"]: i["IdentityStoreId"] for i in instances["Instances"]}

    def prompt_for_creds(self) -> None:
        options = self._get_sso_instances()
        if len(options) == 1:
            self.instances = [list(options.values())[0]]
        else:
            question = inquirer.Checkbox(
                "instances",
                message="Which SSO Instances?",
                choices=options.items(),
            )
            self.instances = inquirer.prompt([question])["instances"]

    def _fetch_identitystore_user(self, instance, email) -> Optional[str]:
        identitystore = boto3.client("identitystore")
        paginator = _AWSPaginator(identitystore, "list_users", "Users")
        for user in paginator.paginate(
            IdentityStoreId=instance,
            Filters=[{"AttributePath": "UserName", "AttributeValue": email}],
        ):
            return user["UserId"]

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        results = {}
        for instance in self.instances:
            for email in emails:
                if (id := self._fetch_identitystore_user(instance, email)) :
                    results[email] = id
        return results
