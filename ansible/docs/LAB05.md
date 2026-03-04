# Lab 5 — Configuration Management (Ansible)

## Architecture Overview

### Ansible Version Used

Ansible was installed on macOS using Homebrew:

```bash
(venv) gleb-pp@gleb-mac ansible % ansible --version
ansible [core 2.20.x]
  config file = /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/ansible.cfg
  python version = 3.12.x
```

### Target VM

Since Yandex Cloud turned out to be a paid service (despite the instructions in the previous lab) and the balance went into the red, the account was blocked. In this lab, I decided to use my own server:

* OS: Ubuntu 24.04 LTS
* Architecture: x86_64
* Public IP: 31.56.27.152
* SSH user: root

Ansible connects to this VM via SSH using key-based authentication.

## Ansible Project Structure

The project follows a role-based architecture:

```
ansible/
├── inventory/
│   └── hosts.ini
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
├── playbooks/
│   ├── provision.yml
│   └── deploy.yml
├── group_vars/
│   └── all.yml (Vault encrypted)
├── ansible.cfg
└── docs/LAB05.md
```

### Why Roles Instead of Monolithic Playbooks?

Roles separate logic into reusable components:

* `common` → base system configuration
* `docker` → container runtime setup
* `app_deploy` → application deployment

This improves:

* Reusability
* Maintainability
* Scalability
* Readability

# Connectivity Verification

### Ansible Ping

```bash
(venv) gleb-pp@gleb-mac ansible % ansible all -m ping
[WARNING]: Host 'gleb-server' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
gleb-server | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
```

### Remote Command Execution

```bash
(venv) gleb-pp@gleb-mac ansible % ansible webservers -a "uname -a"
[WARNING]: Host 'gleb-server' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
gleb-server | CHANGED | rc=0 >>
Linux gleb-server 6.8.0-35-generic #35-Ubuntu SMP PREEMPT_DYNAMIC Mon May 20 15:51:52 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

This confirms:

* SSH connectivity works
* Python interpreter detected
* Remote command execution works

# Roles Documentation

## Role: common

### Purpose

Performs base system provisioning:

* Updates apt cache
* Installs essential packages
* Sets timezone

### Key Variables

Defined in `roles/common/defaults/main.yml`:

```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
timezone: "UTC"
```

### Idempotent Behavior

* `apt state=present` ensures packages are only installed if missing
* `timezone` module updates only if needed

## Role: docker

### Purpose

Installs and configures Docker engine.

### Tasks Performed

* Adds Docker GPG key
* Adds Docker repository
* Installs Docker packages
* Ensures Docker service is running
* Adds user to docker group
* Installs `python3-docker`

### Handler

```yaml
- name: Restart Docker
  service:
    name: docker
    state: restarted
```

### Idempotency Strategy

* `creates:` parameter prevents re-downloading GPG key
* `apt state=present` prevents reinstalling packages
* `service state=started` avoids unnecessary restarts

## Role: app_deploy

### Purpose

Deploys containerized Python application.

### Tasks Performed

* Login to Docker Hub
* Pull image
* Stop existing container
* Remove old container
* Run new container
* Wait for port
* Health check

### Default Variables

```yaml
restart_policy: unless-stopped
env_vars: {}
```

### Handler

```yaml
- name: Restart application container
  community.docker.docker_container:
    name: "{{ app_container_name }}"
    state: started
    restart: true
```

# Idempotency Demonstration

## First Run — provision.yml

```bash
ansible-playbook playbooks/provision.yml
```

Screenshot saved:

* `docs/ansible_provision_yellow.png`

Result:

* Packages installed
* Docker installed
* Services started
* User added to docker group

Several tasks showed `changed`.

## Second Run — provision.yml

```bash
ansible-playbook playbooks/provision.yml
```

Screenshot saved:

* `docs/ansible_provision_green.png`

Result:

```
ok=XX
changed=0
```

### Analysis

First run changed because:

* Packages were missing
* Docker not installed
* Repo not configured
* User not in docker group

Second run showed no changes because:

* Desired state matched current state
* All resources already configured
* GPG key already created
* Services already running

### What Makes It Idempotent?

A task is idempotent when:

> Running it multiple times produces the same result without changing system state unnecessarily.

This was achieved using:

* `state: present`
* `creates:`
* `state: started`
* Declarative configuration

# Ansible Vault Usage

Sensitive data stored in:

```
group_vars/all.yml
```

Created using:

```bash
ansible-vault create group_vars/all.yml
```

Encrypted content example:

```yaml
$ANSIBLE_VAULT;1.1;AES256
663864663838393532353234...
```

### Stored Secrets

* Docker Hub username
* Docker Hub access token
* Application configuration

### Why Vault Is Important

* Prevents credential exposure in Git
* Encrypts sensitive variables
* Supports secure automation

Vault password is requested during deployment:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

# Deployment Verification

## Deploy Command

```bash
gleb-pp@gleb-mac ansible % ansible-playbook \
  -i inventory/hosts.ini \
  -e "@group_vars/all.yml" \
  playbooks/deploy.yml \
  --ask-vault-pass
Vault password:
```

### Full Terminal Output

```bash
PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'gleb-server' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [gleb-server]

TASK [app_deploy : Log in to Docker Hub] ***********************************************************************************************
ok: [gleb-server]

TASK [app_deploy : Set docker_image full name] *****************************************************************************************
ok: [gleb-server]

TASK [app_deploy : Pull Docker image] **************************************************************************************************
ok: [gleb-server]

TASK [app_deploy : Stop existing container] ********************************************************************************************
changed: [gleb-server]

TASK [app_deploy : Remove old container] ***********************************************************************************************
changed: [gleb-server]

TASK [app_deploy : Run new container] **************************************************************************************************
[WARNING]: Docker warning: The requested image's platform (linux/arm64) does not match the detected host platform (linux/amd64/v4) and no specific platform was requested
changed: [gleb-server]

TASK [app_deploy : Wait for application to start] **************************************************************************************
ok: [gleb-server]

TASK [app_deploy : Check health endpoint] **********************************************************************************************
ok: [gleb-server]

RUNNING HANDLER [app_deploy : Restart application container] **************************************************************************
ok: [gleb-server]

PLAY RECAP *****************************************************************************************************************************
gleb-server                : ok=9    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

gleb-pp@gleb-mac ansible %
```

## Health Check

```bash
gleb-pp@gleb-mac iu-devops-course % curl http://31.56.27.152:5000/health
{"status":"healthy","timestamp":"2026-02-26T18:41:32.482917","uptime_seconds":28}
gleb-pp@gleb-mac iu-devops-course %
```

## Root Endpoint

```bash
gleb-pp@gleb-mac iu-devops-course % curl http://31.56.27.152:5000/
{"service":{"name":"Python Web Application","version":"1.0","description":"Simple production-ready Pythonweb service with comprehensive system information","framework":"FastAPI"},"system":{"hostname":"gleb-server","platform":"Linux","platform_version":"#35-Ubuntu SMP PREEMPT_DYNAMIC Thu Jan 16 12:34:56 UTC 2026","architecture":"x86_64","cpu_count":2,"python_version":"3.12.3"},"runtime":{"uptime_seconds":34,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-26T18:41:38.193204","timezone":"UTC"},"request":{"client_ip":"31.56.27.152","user_agent":"curl/8.7.1","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
gleb-pp@gleb-mac iu-devops-course %
```


# Key Decisions

### Why Use Roles Instead of Plain Playbooks?

Roles modularize configuration, separate concerns, and allow reuse across multiple projects.

### How Do Roles Improve Reusability?

Roles encapsulate logic and variables, making them portable and composable.

### What Makes a Task Idempotent?

A task is idempotent when it defines a desired state and only changes the system if it does not match that state.

### How Do Handlers Improve Efficiency?

Handlers run only when notified, preventing unnecessary service restarts.

### Why Is Ansible Vault Necessary?

It protects credentials and secrets from being exposed in version control systems.

# Challenges Encountered

* SSH timeout during initial deploy attempt
* Docker image platform mismatch warning
* Ensuring proper port binding inside container
* Interpreter discovery warning

All issues were resolved by:

* Verifying inventory configuration
* Ensuring VM was reachable
* Confirming Docker installation
* Validating container port exposure

# Final Result

The infrastructure provisioned in Lab 4 was successfully configured using Ansible:

* Base system configured
* Docker installed
* Application deployed
* Secrets encrypted
* Idempotency verified

Lab 5 demonstrates practical configuration management, secure secret handling, and reproducible infrastructure automation using Ansible.
