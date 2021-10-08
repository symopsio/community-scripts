# Sym Community Scripts

## Setup
1. Clone this repo
2. Install [`poetry`](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions)
3. Run `poetry install`

## Find instances without SSM

```
poetry run instances_without_ssm
```

## Populate a User CSV File

```
poetry run populate_users users.csv
```

### Aptible

You can set your Aptible Username and Password with the APTIBLE_USERNAME and APTIBLE_PASSWORD environment variables, or be prompted for them.

### AWS

The standard AWS environment variables are supported for authentication.

### PagerDuty

You can set your PagerDuty API key with the PAGERDUTY_API_KEY environment variable or be prompted for it.
