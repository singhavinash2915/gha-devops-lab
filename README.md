# gha-devops-lab

Practice repository for the GitHub Actions + DevOps Python interview prep guide (Part D, Labs 1–10).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ruff check . && python -m pytest
```

Push to a new public GitHub repository and follow the labs in the guide. Lab 7 needs the environments
`dev`, `staging` and `production` created under Settings → Environments.
