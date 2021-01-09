# Sym Community Scripts

## Setup
1. Clone this repo
2. Install `poetry`
3. Run `poetry install`
4. Run `poetry build`

## Find instances without SSM

`poetry run python -m sym_community_scripts.instances_without_ssm`

## Find UserId in AWS SSO Identity Store given a Username

Pass you own **Identity store ID** and desired **Username** to the command below

`poetry run python identitystore_userids d-xxxxxxxxxx bob@acme.com`