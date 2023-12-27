# Generative AI Conference Automation

This repo is a collection of my automation scripts for [2024 Generative AI Conference](https://2024.gaiconf.com/).

## Airtable form submission to Gmail draft (airtable-to-draft.py)

When someone fills "Call for Sponsors" form, I need to sned an email with our standard sponsor proposal.

This script automates the process of:
1. fetching data from Airtable,
2. creating email drafts in Gmail,
3. and updating records in Airtable.

----

## INSTALL

1. Install Dependencies:

    ```
    pip install -r requirements.txt
    ```

2. Configuration File: Copy `config.ini.example` to `config.ini`.
3. Google Credentials: Follow the Google API Console documentation to obtain your `credentials.json` file for Gmail API access.
