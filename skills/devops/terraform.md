---
id: terraform
name: Terraform Expert
category: deploying
level1: "For Terraform infrastructure as code — providers, modules, state, plan/apply, AWS/GCP"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Terraform Expert** — Activate for: Terraform IaC, .tf files, providers, modules, remote state, terraform plan/apply/destroy/import, AWS/GCP/Azure infrastructure, HCL syntax, state locking, workspaces.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Terraform Expert — Core Instructions

1. **Run `terraform plan` before every `apply`** — read the diff carefully: count of resources to add/change/destroy must match your intent before proceeding.
2. **Use remote state for all non-local environments** — S3 + DynamoDB (AWS) or GCS (GCP) with state locking enabled; never commit `.tfstate` files to git.
3. **Structure modules with a single responsibility** — one module per logical resource group (VPC, database, compute); keep `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf` in every module.
4. **Pin provider and module versions explicitly** — use `~>` for minor-version flexibility (e.g., `~> 5.0`) but never leave versions unconstrained in production.
5. **Never hardcode secrets in `.tf` files** — use `var` with sensitive = true, SSM Parameter Store, or Vault; secrets must not appear in plan output or state in plaintext.
6. **Use `terraform import` to bring existing resources under management** — always inspect state after import to reconcile drift before planning changes.
7. **Tag every resource consistently** — define a `locals` block with common tags (environment, team, repo) and merge into every resource's `tags` argument.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Terraform Expert — Full Reference

### File Structure

```
infrastructure/
├── main.tf          # root module: provider config, module calls
├── variables.tf     # input variable declarations
├── outputs.tf       # output value declarations
├── versions.tf      # required_providers + terraform block
├── locals.tf        # computed locals (tags, name prefixes)
└── modules/
    └── vpc/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### versions.tf — Provider Pinning

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}
```

### Remote State — S3 + DynamoDB Backend

```hcl
# versions.tf — backend block
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/vpc/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"   # PAY_PER_REQUEST table with LockID (String) PK
  }
}
```

```hcl
# One-time DynamoDB lock table (bootstrap with local state first)
resource "aws_dynamodb_table" "tf_lock" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### Variables and Locals

```hcl
# variables.tf
variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "db_password" {
  type      = string
  sensitive = true  # masked in plan/apply output
}

# locals.tf
locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Repo        = "github.com/my-org/infra"
  }
}
```

### AWS VPC Pattern

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = merge(local.common_tags, { Name = "${local.name_prefix}-vpc" })
}

resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = merge(local.common_tags, { Name = "${local.name_prefix}-public-${count.index}" })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${local.name_prefix}-igw" })
}
```

### AWS RDS Pattern

```hcl
resource "aws_db_instance" "postgres" {
  identifier        = "${local.name_prefix}-postgres"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password   # sensitive variable

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  skip_final_snapshot     = var.environment != "prod"
  deletion_protection     = var.environment == "prod"

  tags = local.common_tags
}
```

### Module Call Pattern

```hcl
# main.tf — root module
module "vpc" {
  source  = "./modules/vpc"

  environment         = var.environment
  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
  common_tags         = local.common_tags
}

# outputs.tf — root module consuming module output
output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "ID of the created VPC"
}
```

### Data Sources

```hcl
# Look up the latest Amazon Linux 2023 AMI
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# Reference in resource
resource "aws_instance" "app" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.small"
}
```

### Workspaces for Environment Isolation

```bash
terraform workspace new staging
terraform workspace select staging
terraform plan -var-file="staging.tfvars"
```

```hcl
# Reference workspace in config
locals {
  env = terraform.workspace   # "staging", "prod", etc.
}
```

### Common CLI Workflow

```bash
terraform init                        # download providers + modules
terraform fmt -recursive              # format all .tf files
terraform validate                    # check syntax/logic
terraform plan -out=tfplan            # save plan to file
terraform apply tfplan                # apply only what was planned
terraform state list                  # list tracked resources
terraform state show aws_vpc.main     # inspect a specific resource
terraform import aws_s3_bucket.logs my-existing-bucket  # bring existing resource under management
terraform destroy -target=aws_instance.app              # destroy single resource
```

### Anti-patterns to Avoid
- Committing `.tfstate` or `.tfstate.backup` to version control — contains secrets and drifts immediately
- Using `terraform apply` without a saved plan file in CI — the apply target may differ from what was reviewed
- Hardcoding AWS account IDs, region strings, or AMI IDs — use data sources and variables
- One giant `main.tf` with hundreds of resources — split into modules early; refactoring state is painful
- Ignoring `terraform fmt` — inconsistent formatting causes noisy diffs and obscures real changes
- Using `count` for conditionals when `for_each` on a map is cleaner and avoids index-shift bugs on deletion
<!-- LEVEL 3 END -->
