from .aws import SSO, IAM  # noqa
from .pagerduty import PagerDuty  # noqa
from .populate_users import populate_users


def main():
    populate_users()


if __name__ == "__main__":
    populate_users()
