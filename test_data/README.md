# Test Data

This directory is reserved for local test-data files used by the automated test suite.

The public repository intentionally does **not** include real company templates, resident information, phone numbers, or other production/test-environment data.

For the isolated authorized task flow, the default public configuration expects:

```text
test_data/invite_sample.xlsx
```

Create your own local sample file only with synthetic or explicitly authorized test data, then point `TEST_INVITE_EXCEL` in `.env` to that file if needed.

Do not commit:

- real names or phone numbers
- company Excel templates
- exported production data
- access tokens, cookies, or credentials
