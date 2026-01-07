# Lab 6: Advanced Ansible & CI/CD

![Difficulty: Intermediate](https://img.shields.io/badge/Difficulty-Intermediate-yellow)
![Points: 10+2.5](https://img.shields.io/badge/Points-10+2.5-blue)
![Prerequisites: Lab 5](https://img.shields.io/badge/Prerequisites-Lab%205-orange)

**Objective:** Enhance your Ansible automation with advanced features including blocks, tags, Docker Compose, role dependencies, wipe logic, and CI/CD integration.

**Estimated Time:** 4-6 hours

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Learning Outcomes](#learning-outcomes)
4. [Task 1: Refactor with Blocks & Tags (2 pts)](#task-1-refactor-with-blocks--tags-2-pts)
5. [Task 2: Upgrade to Docker Compose (3 pts)](#task-2-upgrade-to-docker-compose-3-pts)
6. [Task 3: Wipe Logic Implementation (1 pt)](#task-3-wipe-logic-implementation-1-pt)
7. [Task 4: CI/CD with GitHub Actions (3 pts)](#task-4-cicd-with-github-actions-3-pts)
8. [Task 5: Documentation (1 pt)](#task-5-documentation-1-pt)
9. [Bonus Part 1: Multi-App Deployment (1.5 pts)](#bonus-part-1-multi-app-deployment-15-pts)
10. [Bonus Part 2: Multi-App CI/CD (1 pt)](#bonus-part-2-multi-app-cicd-1-pt)
11. [Submission Guidelines](#submission-guidelines)
12. [Grading Criteria](#grading-criteria)

---

## Overview

This lab builds directly on Lab 5 by adding advanced Ansible features that improve maintainability, flexibility, and automation. You'll enhance your existing roles with blocks and tags, upgrade from `docker run` to Docker Compose, implement cleanup logic, and automate everything with CI/CD.

**What You'll Build:**
- Enhanced roles with blocks for error handling and logical grouping
- Tagged tasks for selective execution
- Docker Compose-based deployment with role dependencies
- Wipe logic for clean application removal
- GitHub Actions workflow for automated Ansible deployments

**Prerequisites from Lab 5:**
- Working Ansible setup with ansible.cfg
- Three roles: `common`, `docker`, `app_deploy`
- Playbooks: `provision.yml`, `deploy.yml`
- Vault-encrypted credentials

---

## Prerequisites

### Technical Requirements
- ✅ Lab 5 completed with all roles working
- ✅ Target VM accessible via SSH
- ✅ GitHub repository with Lab 5 code
- ✅ Python web app from Lab 1 containerized (Lab 2)

### Knowledge Requirements
- Ansible roles and playbooks (Lab 5)
- Docker basics (Lab 2)
- GitHub Actions (Lab 3)
- Understanding of idempotency

### Optional (for Bonus)
- Second application from Lab 1 Bonus (Go/Rust/Java/C#)
- Experience with multi-container deployments

---

## Learning Outcomes

After completing this lab, you will be able to:

1. **Use blocks** to group tasks logically and handle errors with `rescue` and `always`
2. **Implement tags** for selective task execution and deployment flexibility
3. **Create Docker Compose templates** with Jinja2 for dynamic configuration
4. **Define role dependencies** to ensure correct execution order
5. **Implement wipe logic** with variables and tags for clean application removal
6. **Automate Ansible deployments** with GitHub Actions CI/CD
7. **Deploy multiple applications** using role reusability patterns (Bonus)

---

## Task 1: Refactor with Blocks & Tags (2 pts)

### 1.1 Understanding Blocks

Blocks allow you to:
- **Group tasks** logically (e.g., all Docker installation tasks)
- **Apply directives** once to multiple tasks (when, become, tags)
- **Handle errors** with rescue and always sections
- **Improve readability** by showing task relationships

**Example Block Pattern:**
```yaml
- name: Install package with error handling
  block:
    - name: Update apt cache
      # task 1

    - name: Install package
      # task 2

  rescue:
    - name: Handle installation failure
      # runs only if block fails

  always:
    - name: Cleanup temp files
      # runs regardless of success/failure

  when: ansible_os_family == "Debian"
  become: true
  tags:
    - packages
```

### 1.2 Understanding Tags

Tags enable selective execution:
```bash
# Run only tagged tasks
ansible-playbook provision.yml --tags "docker"

# Skip specific tags
ansible-playbook provision.yml --skip-tags "common"

# Multiple tags
ansible-playbook provision.yml --tags "packages,docker"

# List all available tags
ansible-playbook provision.yml --list-tags
```

### 1.3 Refactor `common` Role

**File:** `roles/common/tasks/main.yml`

**Requirements:**
1. Group package installation tasks in a block with tag `packages`
2. Group user creation tasks in a block with tag `users`
3. Add error handling with rescue for apt cache update failures
4. Use always block to log completion

**Tag Strategy:**
- `packages` - all package installation tasks
- `users` - all user management tasks
- `common` - entire role (applied at role level)

**Hints:**
- Add rescue block that runs `apt-get update --fix-missing` on failure
- Use always block to create a log file in /tmp indicating completion
- Apply `become: true` at block level instead of per task

**Research Questions:**
- Q: What happens if rescue block also fails?
- Q: Can you have nested blocks?
- Q: How do tags inherit to tasks within blocks?

### 1.4 Refactor `docker` Role

**File:** `roles/docker/tasks/main.yml`

**Requirements:**
1. Group Docker installation tasks in block with tag `docker_install`
2. Group Docker configuration tasks in block with tag `docker_config`
3. Add rescue block to retry apt update on GPG key failure
4. Use always block to ensure Docker service is enabled

**Additional Tags:**
- `docker` - entire role
- `docker_install` - installation only
- `docker_config` - configuration only

**Hints:**
- Docker GPG key addition may fail on first try (network timeout)
- Rescue block should wait 10 seconds and retry
- Always block should ensure Docker service is enabled and started

### 1.5 Testing Blocks & Tags

**Test Commands:**
```bash
# Test provision with only docker
ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only across all roles
ansible-playbook playbooks/provision.yml --tags "packages"

# Check mode to see what would run
ansible-playbook playbooks/provision.yml --tags "docker" --check

# Run only docker installation tasks
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

**Evidence Required:**
- Output showing selective execution with --tags
- Output showing error handling with rescue block triggered
- List of all available tags (--list-tags output)

---

## Task 2: Upgrade to Docker Compose (3 pts)

### 2.1 Why Docker Compose?

**Advantages over `docker run`:**
- **Declarative configuration** - define desired state, not commands
- **Multi-container management** - networks, volumes, dependencies
- **Environment variable management** - .env files, variable substitution
- **Easy updates** - change config file and recreate
- **Better for production** - consistent, reproducible deployments

### 2.2 Rename Role

**Action Required:**
```bash
cd ansible/roles
mv app_deploy web_app
```

**Update all references:**
- Playbook imports: `roles/app_deploy` → `roles/web_app`
- Documentation: app_deploy → web_app
- Variable prefixes: Consider `web_app_*` for consistency

**Why rename?**
- `web_app` is more specific and descriptive
- Prepares for potential other app types (database_app, cache_app)
- Better aligns with wipe logic variable naming

### 2.3 Create Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

**Requirements:**
1. Use Jinja2 templating for dynamic values
2. Define service name, image, ports, environment variables
3. Include restart policy
4. Use networks if needed
5. Support variable substitution for app-specific config

**Template Pattern:**
```yaml
version: '3.8'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      # Add environment variables here
      # Use Vault-encrypted secrets
    restart: unless-stopped
    # Add other configuration
```

**Variables to support:**
- `app_name` - service/container name (default: devops-app)
- `docker_image` - Docker Hub image
- `docker_tag` - image version (default: latest)
- `app_port` - host port (default: 8000)
- `app_internal_port` - container port (default: 8000)
- Environment variables for app configuration

**Research Questions:**
- Q: What's the difference between `restart: always` and `restart: unless-stopped`?
- Q: How do Docker Compose networks differ from Docker bridge networks?
- Q: Can you reference Ansible Vault variables in the template?

### 2.4 Define Role Dependencies

**File:** `roles/web_app/meta/main.yml`

**Purpose:** Ensure Docker is installed before deploying web app.

**Pattern:**
```yaml
---
dependencies:
  - role: role_name
    # Optional variables to pass
    vars:
      var_name: value
```

**Requirements:**
1. Add `docker` role as dependency
2. Ensure correct execution order automatically
3. Document why dependency is needed

**Test:** Run only `web_app` role - Docker should install automatically:
```bash
ansible-playbook playbooks/deploy.yml
# Should automatically run docker role first
```

### 2.5 Implement Docker Compose Deployment

**File:** `roles/web_app/tasks/main.yml`

**Requirements:**
1. Create application directory (e.g., /opt/{{ app_name }})
2. Template docker-compose.yml to the directory
3. Use `docker_compose` module (or `community.docker.docker_compose`)
4. Ensure idempotency (check if already running)
5. Add appropriate tags: `app_deploy`, `compose`

**Deployment Block Pattern:**
```yaml
- name: Deploy application with Docker Compose
  block:
    - name: Create app directory
      # Use file module

    - name: Template docker-compose file
      # Use template module

    - name: Deploy with docker-compose
      # Use docker_compose module
      # state: present (or up)

  rescue:
    - name: Handle deployment failure
      # Log error, optionally rollback

  tags:
    - app_deploy
    - compose
```

**Hints:**
- Install docker-compose Python library: `pip3 install docker-compose`
- Or use `community.docker` collection (requires installation)
- Set `pull: yes` to always get latest image
- Use `project_src` to specify directory with docker-compose.yml

**Research:**
- Look up `community.docker.docker_compose_v2` module
- Compare `state: present` vs other state options
- Understand `recreate` parameter options

### 2.6 Variables Configuration

**File:** `group_vars/all.yml` (or role defaults)

**Required Variables:**
```yaml
# Application Configuration
app_name: devops-app
docker_image: your_dockerhub_username/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000

# Docker Compose Config
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"

# Secrets (use Vault)
app_secret_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

**Encrypt sensitive values:**
```bash
ansible-vault encrypt_string 'secret_value' --name 'app_secret_key'
```

### 2.7 Testing Docker Compose Deployment

**Test Commands:**
```bash
# Full deployment
ansible-playbook playbooks/deploy.yml

# Check idempotency (run twice, second should show no changes)
ansible-playbook playbooks/deploy.yml
ansible-playbook playbooks/deploy.yml

# Verify on target VM
ssh user@vm_ip
docker ps
docker-compose -f /opt/devops-app/docker-compose.yml ps
curl http://localhost:8000
```

**Evidence Required:**
- Output showing Docker Compose deployment success
- Idempotency proof (second run shows "ok" not "changed")
- Application running and accessible
- Contents of templated docker-compose.yml

---

## Task 3: Wipe Logic Implementation (1 pt)

### 3.1 Understanding Wipe Logic

**Purpose:** Clean removal of deployed applications for:
- Fresh redeployments
- Testing from clean state
- Decommissioning applications
- Resource cleanup

**Implementation Requirements:**
- ✅ Controlled by variable: `web_app_wipe: true`
- ✅ Gated by specific tag: `web_app_wipe`
- ❌ NOT using the special "never" tag
- Default behavior: wipe tasks do NOT run
- Explicit invocation required

### 3.2 Create Wipe Tasks

**File:** `roles/web_app/tasks/wipe.yml`

**Requirements:**
1. Stop and remove containers (Docker Compose down)
2. Remove docker-compose.yml file
3. Remove application directory
4. Optionally remove Docker images (consider disk space)
5. Log wipe completion

**Implementation Pattern:**
```yaml
---
- name: Wipe web application
  block:
    - name: Stop and remove containers
      community.docker.docker_compose:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: true  # In case already stopped

    - name: Remove docker-compose file
      file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      file:
        path: "{{ compose_project_dir }}"
        state: absent

    - name: Log wipe completion
      debug:
        msg: "Application {{ app_name }} wiped successfully"

  when: web_app_wipe | default(false) | bool
  tags:
    - web_app_wipe
```

**Key Points:**
- `when` condition checks variable (default: false)
- `tags` enables selective execution
- `ignore_errors` prevents failure if already clean
- `| bool` ensures proper boolean evaluation

### 3.3 Include Wipe in Main Tasks

**File:** `roles/web_app/tasks/main.yml`

**Add at the end:**
```yaml
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags:
    - web_app_wipe
```

**Why at the end?**
- Wipe should not run during normal deployment
- Explicit tag ensures it only runs when requested
- Keeps main deployment logic clean

### 3.4 Configure Wipe Variable

**File:** `roles/web_app/defaults/main.yml`

**Add:**
```yaml
# Wipe Logic Control
web_app_wipe: false  # Default: do not wipe
```

**Documentation comment:**
```yaml
# Set to true to remove application completely
# Usage: ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```

### 3.5 Testing Wipe Logic

**Test Scenarios:**

**Scenario 1: Normal deployment (wipe should NOT run)**
```bash
ansible-playbook playbooks/deploy.yml

# Verify: app should be deployed and running
ssh user@vm_ip "docker ps"
```

**Scenario 2: Explicit wipe**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Verify: app should be removed
ssh user@vm_ip "docker ps"  # Should not show app
ssh user@vm_ip "ls /opt"    # Should not have app directory
```

**Scenario 3: Deploy with wipe tag but variable false (should NOT wipe)**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe

# Verify: nothing should happen (when condition prevents execution)
```

**Scenario 4: Deploy with variable true but without tag (should NOT wipe)**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# Verify: app deploys normally, wipe tasks skipped (tag not specified)
```

**Evidence Required:**
- Output of Scenario 2 showing successful wipe
- Output of Scenario 3 showing wipe skipped (when condition)
- Proof that normal deployment doesn't trigger wipe
- Screenshot or output of clean VM after wipe

### 3.6 Research Questions

Answer these in your documentation:
1. **Why use both variable AND tag?** (Double safety mechanism)
2. **What's the difference between `never` tag and this approach?**
3. **When would you want to wipe before redeployment?**
4. **How would you extend this to wipe Docker images too?**

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### 4.1 Why Automate Ansible?

**Benefits:**
- **Consistency** - same process every time
- **Speed** - automatic deployments on push
- **Safety** - linting catches errors before execution
- **Auditability** - GitHub logs every deployment
- **Integration** - combines with testing, building, scanning

**CI/CD Flow:**
```
Code Push → Lint Ansible → Run Ansible Playbook → Verify Deployment
```

### 4.2 Install GitHub Actions Runner (Optional)

**Two Approaches:**

**Approach A: Self-hosted runner on target VM (Recommended)**
- More realistic for production
- Direct access to target server
- Faster (no SSH overhead)
- Setup: GitHub Repo → Settings → Actions → Runners → Add runner

**Approach B: GitHub-hosted runner with SSH**
- Easier setup
- Requires SSH key configuration
- Uses GitHub Secrets for credentials
- Slower but simpler

Choose based on your infrastructure preference.

### 4.3 Create Ansible Workflow

**File:** `.github/workflows/ansible-deploy.yml`

**Requirements:**
1. Trigger on push to ansible directory
2. Run ansible-lint for syntax checking
3. Execute Ansible playbook
4. Verify deployment success
5. Use path filters to avoid unnecessary runs

**Workflow Structure:**
```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'ansible/**'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install ansible ansible-lint

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest  # or self-hosted
    steps:
      # Add deployment steps
      # - Setup Ansible
      # - Configure SSH (if needed)
      # - Decrypt Vault (use GitHub Secrets)
      # - Run playbook
      # - Verify deployment
```

### 4.4 Configure GitHub Secrets

**Required Secrets:** (Settings → Secrets and variables → Actions)

1. `ANSIBLE_VAULT_PASSWORD` - Vault password for decryption
2. `SSH_PRIVATE_KEY` - SSH key for target VM (if using remote runner)
3. `VM_HOST` - Target VM IP/hostname
4. `VM_USER` - SSH username

**Using Secrets in Workflow:**
```yaml
- name: Deploy with Ansible
  env:
    ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
  run: |
    echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
    ansible-playbook playbooks/deploy.yml \
      --vault-password-file /tmp/vault_pass
    rm /tmp/vault_pass
```

### 4.5 Implement Deployment Step

**For self-hosted runner:**
```yaml
deploy:
  runs-on: self-hosted
  steps:
    - uses: actions/checkout@v4

    - name: Deploy with Ansible
      run: |
        cd ansible
        echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
        ansible-playbook playbooks/deploy.yml \
          --vault-password-file /tmp/vault_pass \
          --tags "app_deploy"
        rm /tmp/vault_pass
```

**For GitHub-hosted runner:**
```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install Ansible
      run: pip install ansible

    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts

    - name: Deploy with Ansible
      run: |
        cd ansible
        echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
        ansible-playbook playbooks/deploy.yml \
          -i inventory/hosts.ini \
          --vault-password-file /tmp/vault_pass
        rm /tmp/vault_pass
```

### 4.6 Add Verification Step

**After deployment, verify it worked:**
```yaml
- name: Verify Deployment
  run: |
    sleep 10  # Wait for app to start
    curl -f http://${{ secrets.VM_HOST }}:8000 || exit 1
    curl -f http://${{ secrets.VM_HOST }}:8000/health || exit 1
```

### 4.7 Path Filters Best Practice

**Why path filters?**
- Don't run Ansible workflow when changing docs
- Separate workflows for different concerns
- Faster CI, lower costs

**Example:**
```yaml
on:
  push:
    paths:
      - 'ansible/**'           # Ansible code
      - '!ansible/docs/**'     # Exclude docs
      - '.github/workflows/ansible-deploy.yml'  # Workflow changes
```

### 4.8 Add Status Badge

**File:** `README.md` (or ansible/README.md)

**Add badge:**
```markdown
[![Ansible Deployment](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml)
```

### 4.9 Testing CI/CD

**Test Sequence:**
1. Make a change to ansible code (e.g., update variable in group_vars)
2. Commit and push to GitHub
3. Watch Actions tab for workflow execution
4. Verify lint job passes
5. Verify deploy job succeeds
6. Check application is updated on target VM

**Evidence Required:**
- Screenshot of successful workflow run
- Output logs showing ansible-lint passing
- Output logs showing ansible-playbook execution
- Verification step output showing app responding
- Status badge in README showing passing

### 4.10 Research Questions

Answer in documentation:
1. **What are the security implications of storing SSH keys in GitHub Secrets?**
2. **How would you implement a staging → production deployment pipeline?**
3. **What would you add to make rollbacks possible?**
4. **How does self-hosted runner improve security compared to GitHub-hosted?**

---

## Task 5: Documentation (1 pt)

### 5.1 Documentation Requirements

Create comprehensive documentation in **`ansible/docs/LAB06.md`**

**Required Sections:**

#### 1. Overview
- What was accomplished in Lab 6
- How it builds on Lab 5
- Key technologies used

#### 2. Blocks & Tags Implementation
- Explanation of block usage in each role
- Tag strategy and naming conventions
- Examples of selective execution commands
- Screenshots of tagged execution
- Error handling examples with rescue blocks

#### 3. Docker Compose Migration
- Why Docker Compose over docker run
- Template structure explanation
- Role dependencies reasoning
- Before/after comparison
- Benefits gained

#### 4. Wipe Logic
- Implementation details
- Variable + tag approach explanation
- Why not use "never" tag
- Usage examples
- Test results proving correct behavior

#### 5. CI/CD Integration
- Workflow architecture diagram
- GitHub Actions setup steps
- Secrets configuration
- Path filters rationale
- Evidence of successful automated deployments

#### 6. Testing Results
- All test scenarios executed
- Idempotency verification
- CI/CD pipeline evidence
- Application accessibility proof

#### 7. Challenges & Solutions
- Difficulties encountered
- How you solved them
- Lessons learned

#### 8. Research Answers
- All research questions answered
- Sources cited
- Your analysis and understanding

### 5.2 Code Comments

**Ensure clear comments in:**
- `roles/*/tasks/main.yml` - explain block purposes
- `templates/docker-compose.yml.j2` - document variables
- `roles/web_app/tasks/wipe.yml` - explain safety mechanisms
- `.github/workflows/ansible-deploy.yml` - document each step

### 5.3 Evidence Requirements

Include terminal outputs (text, not screenshots) for:
- Ansible playbook runs with different tags
- Wipe logic execution
- CI/CD workflow logs (can be screenshots)
- Verification commands

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Bonus 1.1 Prerequisites

**Required:**
- Completed Lab 1 Bonus (compiled language app: Go/Rust/Java/C#)
- Completed Lab 2 Bonus (multi-stage Docker build)
- Completed Lab 3 Bonus Part 1 (multi-app CI/CD)

**You should have:**
- Python web app (everyone has this)
- Compiled language web app (Go/Rust/Java/C#)
- Both apps containerized and on Docker Hub
- Both apps with similar endpoints (/, /health)

### Bonus 1.2 Role Reusability Pattern

**Key Concept:** Use the same `web_app` role for both apps with different variables.

**Directory Structure:**
```
ansible/
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml
├── host_vars/          # Optional: per-host vars
├── vars/
│   ├── app_python.yml  # NEW: Python app variables
│   └── app_bonus.yml   # NEW: Bonus app variables
├── roles/
│   └── web_app/        # Reused for both apps
└── playbooks/
    ├── provision.yml
    ├── deploy_python.yml    # NEW
    ├── deploy_bonus.yml     # NEW
    └── deploy_all.yml       # NEW: Deploy both
```

### Bonus 1.3 Create Variable Files

**File:** `ansible/vars/app_python.yml`
```yaml
---
app_name: devops-python
docker_image: your_username/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000
compose_project_dir: "/opt/{{ app_name }}"
```

**File:** `ansible/vars/app_bonus.yml`
```yaml
---
app_name: devops-go  # or rust, java, csharp
docker_image: your_username/devops-info-service-go
docker_tag: latest
app_port: 8001  # Different port!
app_internal_port: 8080  # Go apps often use 8080
compose_project_dir: "/opt/{{ app_name }}"
```

**Important:** Use different ports to run both apps simultaneously.

### Bonus 1.4 Create Deployment Playbooks

**File:** `ansible/playbooks/deploy_python.yml`
```yaml
---
- name: Deploy Python Application
  hosts: all
  become: true
  vars_files:
    - ../vars/app_python.yml

  roles:
    - web_app
```

**File:** `ansible/playbooks/deploy_bonus.yml`
```yaml
---
- name: Deploy Bonus Application
  hosts: all
  become: true
  vars_files:
    - ../vars/app_bonus.yml

  roles:
    - web_app
```

**File:** `ansible/playbooks/deploy_all.yml`
```yaml
---
- name: Deploy All Applications
  hosts: all
  become: true

  tasks:
    - name: Deploy Python App
      include_role:
        name: web_app
      vars:
        app_name: devops-python
        docker_image: your_username/devops-info-service
        app_port: 8000

    - name: Deploy Bonus App
      include_role:
        name: web_app
      vars:
        app_name: devops-go
        docker_image: your_username/devops-info-service-go
        app_port: 8001
        app_internal_port: 8080
```

### Bonus 1.5 Extend Wipe Logic

**Wipe logic should support app-specific wipe:**

**Usage:**
```bash
# Wipe only Python app
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Wipe only Bonus app
ansible-playbook playbooks/deploy_bonus.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Wipe both apps
ansible-playbook playbooks/deploy_all.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```

**The role automatically handles different apps because `app_name` and `compose_project_dir` are different!**

### Bonus 1.6 Testing Multi-App Deployment

**Test Commands:**
```bash
# Deploy both apps
ansible-playbook playbooks/deploy_all.yml

# Verify both running
ssh user@vm_ip "docker ps"
curl http://vm_ip:8000        # Python app
curl http://vm_ip:8001        # Bonus app

# Test independent deployment
ansible-playbook playbooks/deploy_python.yml  # Should not affect bonus app
ansible-playbook playbooks/deploy_bonus.yml   # Should not affect python app

# Test independent wipe
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Verify: Python app removed, bonus app still running

# Test idempotency
ansible-playbook playbooks/deploy_all.yml
ansible-playbook playbooks/deploy_all.yml  # Should show minimal changes
```

**Evidence Required:**
- Output showing both apps deployed
- `docker ps` output showing both containers
- Curl outputs from both apps
- Proof of independent wipe functionality
- Idempotency verification for multi-app deployment

### Bonus 1.7 Documentation

**Add to LAB06.md:**
- Multi-app architecture explanation
- Variable file strategy
- Role reusability benefits
- Port conflict resolution
- Independent vs. combined deployment trade-offs

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Bonus 2.1 Prerequisites

**Required:**
- Bonus Part 1 completed (multi-app deployment working)
- Task 4 completed (single app CI/CD working)

### Bonus 2.2 Workflow Strategy

**Two Approaches:**

**Approach A: Separate Workflows**
- One workflow per app
- Path filters for each app's code
- Independent deployment
- More control, more files

**Approach B: Matrix Strategy**
- Single workflow with matrix
- Deploys both apps
- Simpler, less flexible

Choose based on your preference (Approach A recommended).

### Bonus 2.3 Create Workflow for Bonus App

**File:** `.github/workflows/ansible-deploy-bonus.yml`

**Requirements:**
1. Trigger on bonus app code changes
2. Run ansible-lint
3. Deploy bonus app only
4. Verify bonus app responds
5. Independent from Python app workflow

**Path Filters:**
```yaml
on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/vars/app_bonus.yml'
      - 'ansible/playbooks/deploy_bonus.yml'
      - 'ansible/roles/web_app/**'
      - '.github/workflows/ansible-deploy-bonus.yml'
```

**Deployment Step:**
```yaml
- name: Deploy Bonus Application
  run: |
    cd ansible
    echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
    ansible-playbook playbooks/deploy_bonus.yml \
      --vault-password-file /tmp/vault_pass
    rm /tmp/vault_pass
```

**Verification:**
```yaml
- name: Verify Bonus App Deployment
  run: |
    sleep 10
    curl -f http://${{ secrets.VM_HOST }}:8001 || exit 1
    curl -f http://${{ secrets.VM_HOST }}:8001/health || exit 1
```

### Bonus 2.4 Update Python App Workflow

**File:** `.github/workflows/ansible-deploy.yml`

**Update path filters to be more specific:**
```yaml
on:
  push:
    paths:
      - 'ansible/vars/app_python.yml'
      - 'ansible/playbooks/deploy_python.yml'
      - 'ansible/playbooks/deploy.yml'  # If this deploys Python
      - 'ansible/roles/web_app/**'
      - '.github/workflows/ansible-deploy.yml'
```

**Update deployment to use specific playbook:**
```yaml
- name: Deploy Python Application
  run: |
    cd ansible
    ansible-playbook playbooks/deploy_python.yml \
      --vault-password-file /tmp/vault_pass
```

### Bonus 2.5 Matrix Strategy Alternative

**File:** `.github/workflows/ansible-deploy-matrix.yml`

**Using matrix to deploy both:**
```yaml
name: Ansible Multi-App Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app:
          - name: python
            playbook: deploy_python.yml
            port: 8000
          - name: bonus
            playbook: deploy_bonus.yml
            port: 8001

    steps:
      - uses: actions/checkout@v4

      - name: Deploy ${{ matrix.app.name }}
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/${{ matrix.app.playbook }} \
            --vault-password-file /tmp/vault_pass
          rm /tmp/vault_pass

      - name: Verify ${{ matrix.app.name }}
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:${{ matrix.app.port }}
```

### Bonus 2.6 Testing Multi-App CI/CD

**Test Scenarios:**

**Test 1: Python app change should deploy only Python**
```bash
# Change ansible/vars/app_python.yml
git add ansible/vars/app_python.yml
git commit -m "Update Python app config"
git push

# Watch Actions - only ansible-deploy.yml should run
# Verify only Python app redeployed
```

**Test 2: Bonus app change should deploy only Bonus**
```bash
# Change ansible/vars/app_bonus.yml
git add ansible/vars/app_bonus.yml
git commit -m "Update Bonus app config"
git push

# Watch Actions - only ansible-deploy-bonus.yml should run
```

**Test 3: Role change should deploy both**
```bash
# Change ansible/roles/web_app/tasks/main.yml
git add ansible/roles/web_app/
git commit -m "Update web_app role"
git push

# Watch Actions - both workflows should run
```

**Evidence Required:**
- Screenshots showing independent workflow triggers
- Logs proving only affected app deployed
- Verification of both apps working after role change
- Status badges for both workflows

### Bonus 2.7 Documentation

**Add to LAB06.md:**
- Multi-app CI/CD architecture
- Workflow triggering logic
- Path filter strategy
- Matrix vs separate workflows comparison
- Evidence of independent deployments

---

## Submission Guidelines

### What to Submit

Submit a single markdown file: **`ansible/docs/LAB06.md`**

### Required Structure

```markdown
# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Your Name
**Date:** YYYY-MM-DD
**Lab Points:** 10 + X bonus

---

## Task 1: Blocks & Tags (2 pts)
[Your implementation details]
[Evidence: terminal outputs, tag listings]
[Research answers]

## Task 2: Docker Compose (3 pts)
[Your implementation]
[Template code]
[Before/after comparison]
[Evidence: deployments, idempotency]

## Task 3: Wipe Logic (1 pt)
[Implementation explanation]
[Test results for all scenarios]
[Evidence proving correct behavior]

## Task 4: CI/CD (3 pts)
[Workflow setup]
[Secrets configuration]
[Evidence: successful runs, badges]

## Task 5: Documentation
[This file serves as documentation]

## Bonus Part 1: Multi-App (1.5 pts)
[If completed]

## Bonus Part 2: Multi-App CI/CD (1 pt)
[If completed]

---

## Summary
[Overall reflection]
[Total time spent]
[Key learnings]
```

### GitHub Repository Requirements

**Commit all code:**
```bash
git add ansible/
git add .github/workflows/
git add ansible/docs/LAB06.md
git commit -m "Complete Lab 6: Advanced Ansible & CI/CD"
git push
```

**Repository should contain:**
- ✅ Updated roles with blocks and tags
- ✅ Docker Compose templates
- ✅ Wipe logic implementation
- ✅ CI/CD workflows
- ✅ Documentation with evidence
- ✅ Working deployments (apps accessible)

### Evidence Checklist

**Required Proof:**
- [ ] Ansible playbook output with selective tags
- [ ] Rescue block triggered output
- [ ] Docker Compose deployment success
- [ ] Idempotency verification (2nd run)
- [ ] Wipe logic test results (all 4 scenarios)
- [ ] GitHub Actions successful workflow
- [ ] ansible-lint passing
- [ ] Status badge(s) in README
- [ ] Application(s) accessible via curl

**Bonus Proof (if applicable):**
- [ ] Both apps deployed and accessible
- [ ] Independent wipe functionality
- [ ] Separate workflow runs for each app
- [ ] Path filter effectiveness demonstrated

---

## Grading Criteria

### Task 1: Blocks & Tags (2 pts)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Block Implementation | 0.75 | All three roles refactored with blocks |
| Error Handling | 0.5 | Rescue and always blocks implemented |
| Tag Strategy | 0.5 | Comprehensive tags for selective execution |
| Testing Evidence | 0.25 | Demonstrated various tag combinations |

### Task 2: Docker Compose (3 pts)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Template Quality | 0.75 | Well-structured, templated compose file |
| Role Dependencies | 0.5 | meta/main.yml correctly configured |
| Deployment Logic | 1.0 | Working docker_compose module usage |
| Idempotency | 0.5 | Second run shows no unnecessary changes |
| Evidence | 0.25 | Clear before/after comparison |

### Task 3: Wipe Logic (1 pt)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Implementation | 0.5 | Variable + tag approach correct |
| Testing | 0.3 | All 4 scenarios tested and proven |
| Documentation | 0.2 | Clear explanation of design choices |

### Task 4: CI/CD (3 pts)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Workflow Structure | 0.75 | Proper jobs, steps, and triggers |
| Linting | 0.5 | ansible-lint integrated and passing |
| Deployment | 1.0 | Automated deployment working |
| Path Filters | 0.25 | Efficient triggering |
| Verification | 0.25 | Post-deployment checks |
| Evidence | 0.25 | Successful runs documented |

### Task 5: Documentation (1 pt)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Completeness | 0.4 | All sections present |
| Evidence | 0.3 | Terminal outputs and proofs |
| Analysis | 0.3 | Research questions answered thoughtfully |

### Bonus Part 1: Multi-App (1.5 pts)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Role Reusability | 0.5 | Same role for both apps |
| Variable Strategy | 0.25 | Clean separation via variable files |
| Independent Deployment | 0.5 | Each app can be deployed separately |
| Wipe Extension | 0.25 | App-specific wipe working |

### Bonus Part 2: Multi-App CI/CD (1 pt)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Workflow Design | 0.4 | Separate or matrix strategy implemented |
| Path Filters | 0.3 | Independent triggering working |
| Evidence | 0.3 | Independent deployments proven |

### Total Points

- **Main Tasks:** 10 points
- **Bonus Tasks:** 2.5 points
- **Maximum Total:** 12.5 points

---

## Common Issues & Solutions

### Issue 1: ansible-lint Errors

**Problem:** Many linting warnings/errors in existing code

**Solution:**
```bash
# Create .ansible-lint config
cat > ansible/.ansible-lint << EOF
skip_list:
  - yaml[line-length]
  - name[casing]
  - fqcn[action-core]
EOF

# Or fix issues one by one
ansible-lint --fix playbooks/deploy.yml
```

### Issue 2: Docker Compose Module Not Found

**Problem:** `community.docker.docker_compose` module missing

**Solution:**
```bash
# Install collection
ansible-galaxy collection install community.docker

# Or use legacy docker_compose module (built-in)
# Change: community.docker.docker_compose
# To: docker_compose
```

### Issue 3: Wipe Not Running

**Problem:** Wipe tasks skipped even with correct flags

**Solution:**
- Check variable spelling: `web_app_wipe` (not `web_wipe`)
- Verify tag: `--tags web_app_wipe`
- Check when condition: `when: web_app_wipe | default(false) | bool`
- Debug: Add `debug` task before wipe to print variable value

### Issue 4: CI/CD Can't Connect to VM

**Problem:** GitHub Actions can't SSH to target VM

**Solutions:**
- Verify VM has public IP or is accessible from internet
- Check VM network settings allow SSH access (port 22)
- Consider self-hosted runner on VM itself
- Use Tailscale or similar for secure access
- Test SSH key authentication manually first

### Issue 5: Vault Password in CI

**Problem:** How to safely use Vault password in GitHub Actions

**Solution:**
```yaml
# Store in GitHub Secrets: ANSIBLE_VAULT_PASSWORD
# Use in workflow:
- name: Create vault password file
  run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass

- name: Run playbook
  run: ansible-playbook playbooks/deploy.yml --vault-password-file /tmp/vault_pass

- name: Cleanup
  if: always()
  run: rm -f /tmp/vault_pass
```

### Issue 6: Multiple Apps on Same Port

**Problem:** Port conflict when deploying multiple apps

**Solution:**
- Use different ports for each app (8000, 8001, 8002)
- Update variable files with unique ports
- Ensure VM allows traffic on new ports
- Use reverse proxy (bonus challenge!)

---

## Advanced Challenges (Optional)

Want to go further? Try these:

### Challenge 1: Nginx Reverse Proxy
Set up Nginx as reverse proxy:
- Python app: http://vm_ip/python/
- Bonus app: http://vm_ip/bonus/
- Single entry point, multiple apps

### Challenge 2: Health Check Integration
- Add health check tasks after deployment
- Retry deployment if health check fails
- Notify on Discord/Slack if deployment fails

### Challenge 3: Blue-Green Deployment
- Deploy to alternate directory
- Switch symlink after verification
- Instant rollback capability

### Challenge 4: Dynamic Inventory from Terraform
- Use Terraform output as Ansible inventory
- Automate VM creation → configuration → deployment
- Full IaC pipeline

### Challenge 5: Secrets from External Source
- Use HashiCorp Vault instead of Ansible Vault
- Fetch secrets at runtime
- Better secret rotation

---

## Resources

### Official Documentation
- [Ansible Blocks](https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html)
- [Ansible Tags](https://docs.ansible.com/ansible/latest/user_guide/playbooks_tags.html)
- [Docker Compose Module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_module.html)
- [Ansible Lint](https://ansible-lint.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

### Useful Tools
- [ansible-lint](https://github.com/ansible/ansible-lint) - Ansible best practices checker
- [ansible-playbook --syntax-check](https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html) - Syntax validation
- [Molecule](https://molecule.readthedocs.io/) - Ansible role testing framework

### Community Resources
- [Ansible Galaxy](https://galaxy.ansible.com/) - Community roles
- [Ansible Examples](https://github.com/ansible/ansible-examples) - Official examples
- [DevOps StackExchange](https://devops.stackexchange.com/questions/tagged/ansible) - Q&A

---

## FAQ

**Q: Do I need to complete both bonus tasks?**
A: No, they're independent. Complete what interests you.

**Q: Can I use Docker Swarm or Kubernetes instead of Docker Compose?**
A: This lab focuses on Docker Compose. K8s comes in Labs 9-11.

**Q: My Ansible is version 2.9, is that okay?**
A: Recommended: 2.10+. Some community.docker modules need newer versions.

**Q: Can I use Ansible Tower/AWX for CI/CD instead of GitHub Actions?**
A: Yes, but document your setup. GitHub Actions is easier to grade.

**Q: Should wipe remove Docker images too?**
A: Your choice. Discuss trade-offs: disk space vs. re-pull time.

**Q: Can I use ansible-pull instead of ansible-playbook?**
A: Interesting approach! Document why and how it differs.

**Q: Is it okay to commit .vault_pass to private repo?**
A: NO. Always .gitignore. Use environment variables or CI secrets.

---

## Conclusion

Congratulations on completing Lab 6! You've mastered:

✅ Advanced Ansible features (blocks, tags, dependencies)
✅ Production-ready Docker Compose deployments
✅ Safe wipe logic with double-gating
✅ Automated CI/CD for infrastructure
✅ Role reusability patterns

These skills form the foundation for:
- **Lab 7-8:** Monitoring with Prometheus & Grafana
- **Lab 9-10:** Kubernetes fundamentals
- **Lab 11:** Advanced Kubernetes patterns

**Next Steps:**
1. Ensure all evidence is documented
2. Verify CI/CD workflows are passing
3. Test all functionality one final time
4. Submit your documentation
5. Star the course repo and share your progress!

**Time to move to monitoring and observability! 🚀**

---

**Lab 6 Complete!** | Version 1.0 | Updated: 2026-01-07
