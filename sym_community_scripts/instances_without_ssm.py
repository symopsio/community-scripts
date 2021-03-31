import json
from collections import defaultdict

import boto3
import parliament

from .script import Script

REQUIRED_PERMISSIONS = [
    "ssm:UpdateInstanceInformation",
    "ssmmessages:CreateControlChannel",
    "ssmmessages:CreateDataChannel",
    "ssmmessages:OpenControlChannel",
    "ssmmessages:OpenDataChannel",
]


class InstancesWithoutSSM(Script):
    # Setup

    def __init__(self):
        self.init_clients()
        self.init_caches()

    def init_clients(self):
        self.ec2 = boto3.resource("ec2")
        self.iam = boto3.client("iam")
        self.ssm = boto3.client("ssm")

    def init_caches(self):
        self.instances = {}
        self.instance_profiles = defaultdict(set)
        self.profile_roles = defaultdict(set)
        self.roles = defaultdict(set)
        self.policies = {}
        self.ssm_policies = set()

    # Helpers

    def populate_instance(self):
        self._section_start("Finding Instances")

        instances = self.ec2.instances.filter(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        for instance in instances:
            profile_name = instance.iam_instance_profile["Arn"].split("/")[-1]

            self.instances[instance.id] = instance
            self.instance_profiles[profile_name].add(instance.id)

        self._section_end(f"Found {len(self.instances)} Instances")

    def populate_roles(self):
        self._section_start("Fetching Roles")

        for name in self.instance_profiles:
            profile = self.iam.get_instance_profile(InstanceProfileName=name)
            for role in profile["InstanceProfile"]["Roles"]:
                self.profile_roles[name].add(role["RoleName"])
                self.roles[role["RoleName"]] = set()

        self._section_end(f"Found {len(self.roles)} Roles")

    def populate_policies(self):
        self._section_start("Fetching Policies")

        for role in self.roles:
            for policy in self.iam.list_role_policies(RoleName=role)["PolicyNames"]:
                document = self.iam.get_role_policy(RoleName=role, PolicyName=policy)

                self.roles[role].add(policy)
                self.policies[policy] = document["PolicyDocument"]
            for policy in self.iam.list_attached_role_policies(RoleName=role)["AttachedPolicies"]:
                version = self.iam.get_policy(PolicyArn=policy["PolicyArn"])["Policy"]
                document = self.iam.get_policy_version(
                    PolicyArn=policy["PolicyArn"], VersionId=version["DefaultVersionId"]
                )

                self.roles[role].add(policy["PolicyName"])
                self.policies[policy["PolicyName"]] = document["PolicyVersion"]["Document"]

        self._section_end(f"Found {len(self.policies)} Policies")

    def check_policies(self):
        self._section_start("Checking Policies")

        for name, document in self.policies.items():
            if self.check_policy(name, document):
                self.ssm_policies.add(name)

        self._section_end(f"Verified {len(self.ssm_policies)} SSM Policies")

    def check_policy(self, name, document):
        policy = parliament.analyze_policy_string(json.dumps(document))
        for permission in REQUIRED_PERMISSIONS:
            if policy.get_allowed_resources(*permission.split(":")) != ["*"]:
                self._failure(
                    f"Discarding Instance Policy {name}\n\tMissing permission {permission}"
                )
                return False

        self._success(f"Found Valid SSM Instance Policy {name}")
        return True

    def check_instances(self):
        self._section_start("Checking Instance Profiles")

        ssm_roles = {role for role, policies in self.roles.items() if policies & self.ssm_policies}
        ssm_profiles = {
            profile for profile, roles in self.profile_roles.items() if roles & ssm_roles
        }

        if (bad_profiles := self.instance_profiles.keys() - ssm_profiles) :
            self._error(f"Found {len(bad_profiles)} Bad Instance Profiles")

            for profile in bad_profiles:
                self._error(f"Instances with profile {profile} will not be able to connect to SSM")
                instance = self.instances[next(iter(self.instance_profiles[profile]))]
                self._failure(f"One such instance ({instance.id}) has the following tags:")
                self._failure(f"{json.dumps(instance.tags, indent=2)}")
        else:
            self._section_end("No Bad Instance Profiles!")

    def check_ssm_instances(self):
        self._section_start("Checking SSM Instances")

        instances = [
            i
            for page in self.ssm.get_paginator("describe_instance_information").paginate()
            for i in page["InstanceInformationList"]
        ]
        instance_ids = {i["InstanceId"] for i in instances}

        if (missing_ids := self.instances.keys() - instance_ids) :
            self.report_missing_ssm_instances(missing_ids)
        else:
            self._section_end("No Instances Missing in SSM!")

    def report_missing_ssm_instances(self, missing_ids):
        self._error(f"Found {len(missing_ids)} Instances Missing in SSM")

        reported_profiles = set()

        for instance_id in missing_ids:
            instance = self.instances[instance_id]
            profile = instance.iam_instance_profile["Arn"].split("/")[-1]

            if profile in reported_profiles:
                continue
            else:
                reported_profiles.add(profile)
                if len(reported_profiles) > 3:
                    return

            self._error(f"At least one instance with the {profile} profile is missing in SSM")
            self._failure(f"One such instance ({instance.id}) has the following tags:")
            self._failure(f"{json.dumps(instance.tags, indent=2)}")

    # Run

    def run(self):
        self.populate_instance()
        self.populate_roles()
        self.populate_policies()
        self.check_policies()
        self.check_instances()
        self.check_ssm_instances()


def main():
    InstancesWithoutSSM().run()


if __name__ == "__main__":
    main()
