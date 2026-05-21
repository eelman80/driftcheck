# driftcheck

> Compares live infrastructure state against Terraform plans to surface silent config drift.

---

## Overview

`driftcheck` is a lightweight CLI tool that detects configuration drift by comparing your live infrastructure state with your Terraform plan output. Catch untracked changes before they become incidents.

---

## Installation

```bash
pip install driftcheck
```

Or install from source:

```bash
git clone https://github.com/yourorg/driftcheck.git && cd driftcheck && pip install -e .
```

---

## Usage

Generate a Terraform plan and pipe it into `driftcheck`:

```bash
terraform show -json tfplan.binary > plan.json
driftcheck compare --plan plan.json --provider aws --region us-east-1
```

Example output:

```
[DRIFT DETECTED] aws_security_group.web
  Expected: ingress port 443
  Actual:   ingress port 443, 8080  ← untracked rule added

[OK] aws_s3_bucket.assets
Summary: 1 drift(s) found across 2 resource(s).
```

### Options

| Flag | Description |
|------|-------------|
| `--plan` | Path to Terraform JSON plan file |
| `--provider` | Cloud provider (`aws`, `gcp`, `azure`) |
| `--region` | Target region |
| `--output` | Output format: `text`, `json`, `sarif` |

---

## License

This project is licensed under the [MIT License](LICENSE).