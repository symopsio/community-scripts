# Sym Community Scripts

## Setup
1. Clone this repo
2. Install `poetry`
3. Run `poetry install`

## Find instances without SSM

```
poetry run python -m sym_community_scripts.instances_without_ssm
```

## Find UserId in AWS SSO Identity Store given a Username

```
poetry run identitystore_userids bob@acme.com
```

## Return a list of emails and names from PagerDuty

```
poetry run python sym_community_scripts/pagerduty_users.py --outfile output.csv
```
