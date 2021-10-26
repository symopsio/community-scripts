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


class AWSIntegration:
    @classmethod
    def supports_importing_new(cls) -> bool:
        return False


class IAM(Integration, AWSIntegration, slug="iam"):
    @cached_property
    def _iam(self):
        return boto3.client("iam")

    def prompt_for_creds(self) -> None:
        self._iam.get_user()

    def prompt_for_external_id(self) -> str:
        try:
            user = self._get_current_iam_user()
            return self._account_id_from_arn(user["User"]["Arn"])
        except (KeyError, IndexError):
            question = inquirer.Text("account_id", message="What AWS account ID?")
            return inquirer.prompt([question])["account_id"]

    def _get_current_iam_user(self) -> dict:
        try:
            return self._iam.get_user()
        except (ClientError, BotoCoreError) as e:
            # Some error codes are embedded in the basic ClientError and must be parsed from the message itself.
            error_message = str(e)
            if "ValidationError" in error_message:
                raise IntegrationException("You must authenticate using an IAM User's credentials.")
            elif "AccessDenied" in error_message:
                raise IntegrationException(
                    "Access Denied: Please ensure you can GetUser for AWS IAM."
                )

            raise IntegrationException(str(e))

    def _account_id_from_arn(self, arn: str) -> str:
        return arn.split(":")[4]

    def _fetch_user(self, email: str):
        try:
            user = self._iam.get_user(UserName=email)
        except self._iam.exceptions.NoSuchEntityException:
            return None
        return user["User"]["Arn"]

    def fetch(self, emails: Set[str]) -> Dict[str, str]:
        results = {}
        for email in emails:
            if id := self._fetch_user(email):
                results[email] = id
        return results


class SSO(Integration, AWSIntegration, slug="aws_sso"):
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

    def prompt_for_external_id(self) -> str:
        options = self._get_sso_instances()
        if len(options) == 1:
            return list(options.keys())[0]

        question = inquirer.List(
            "instance_arn", message="Which Instance ARN?", choices=options.items()
        )
        return inquirer.prompt([question])["instance_arn"]

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
                if id := self._fetch_identitystore_user(instance, email):
                    results[email] = id
        return results
