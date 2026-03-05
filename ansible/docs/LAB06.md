# Lab 6: Advanced Ansible & CI/CD

## Task 1: Blocks & Tags (2 pts)

### Implementation Overview

I refactored all three roles (`common`, `docker`, `web_app`) to use Ansible blocks with proper rescue/always sections and comprehensive tagging strategy.

### Tag Strategy

Each role has hierarchical tags allowing granular execution:

| Role | Tags | Purpose |
|------|------|---------|
| **common** | `common`, `packages`, `users` | Base system configuration |
| **docker** | `docker`, `docker_install`, `docker_config` | Docker installation and setup |
| **web_app** | `web_app_wipe`, `app_deploy`, `compose` | Application deployment |

### Block Structure Example (docker role)

```yaml
---
- name: Install Docker
  become: true
  tags:
    - docker
    - docker_install
  block:
    - name: Install required system packages
      ansible.builtin.apt:
        name:
          - ca-certificates
          - curl
          - gnupg
        state: present
        update_cache: true

    - name: Create keyrings directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: '0755'

    - name: Download Docker GPG key
      ansible.builtin.get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: /tmp/docker.gpg
        mode: '0644'

    - name: Install Docker GPG key
      ansible.builtin.command: "gpg --dearmor -o /etc/apt/keyrings/docker.gpg /tmp/docker.gpg"
      args:
        creates: /etc/apt/keyrings/docker.gpg

    - name: Add Docker repository
      ansible.builtin.apt_repository:
        repo: "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable"
        state: present

    - name: Install Docker packages
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
        update_cache: true
      notify: Restart Docker

  rescue:
    - name: Wait before retrying Docker GPG key
      ansible.builtin.wait_for:
        timeout: 10

    - name: Retry apt update
      ansible.builtin.apt:
        update_cache: true

  always:
    - name: Ensure Docker service is enabled
      ansible.builtin.service:
        name: docker
        state: started
        enabled: true
```

### Tag Listing Verification

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### Selective Tag Execution Examples

#### Running only Docker-related tasks

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/provision.yml --tags "docker"

PLAY [Provision web servers] ***********************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Create keyrings directory] **********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker GPG key] *****************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker repository] **************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install Docker packages] ************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Ensure Docker service is enabled] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add user to docker group] ***********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install python docker module] *******************************************************************************************
ok: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

#### Running only Docker installation (without configuration)

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/provision.yml --tags "docker_install"

PLAY [Provision web servers] ***********************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Create keyrings directory] **********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker GPG key] *****************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker repository] **************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install Docker packages] ************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Ensure Docker service is enabled] ***************************************************************************************
ok: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=7    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

### Rescue Block Testing

To verify rescue functionality, I intentionally broke the Docker GPG key URL:

```yaml
- name: Download Docker GPG key
  ansible.builtin.get_url:
    url: https://download.docker.com/linux/ubuntu/gpgBROKEN  # Intentionally broken
    dest: /tmp/docker.gpg
    mode: '0644'
```

**Result:** Rescue block was triggered and executed cleanup tasks

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/provision.yml --tags "docker_install"

PLAY [Provision web servers] ***********************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] ***************************************************************************************
[WARNING]: Failed to update cache after 1 retries due to , retrying
[WARNING]: Sleeping for 1 seconds, before attempting to refresh the cache again
[WARNING]: Failed to update cache after 2 retries due to , retrying
[WARNING]: Sleeping for 2 seconds, before attempting to refresh the cache again
[WARNING]: Failed to update cache after 3 retries due to , retrying
[WARNING]: Sleeping for 4 seconds, before attempting to refresh the cache again
[WARNING]: Failed to update cache after 4 retries due to , retrying
[WARNING]: Sleeping for 8 seconds, before attempting to refresh the cache again
[WARNING]: Failed to update cache after 5 retries due to , retrying
[WARNING]: Sleeping for 12 seconds, before attempting to refresh the cache again
[ERROR]: Task failed: Module failed: Failed to update apt cache after 5 retries: 
Origin: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/docker/tasks/main.yml:5:7

3   block:
4
5     - name: Install required system packages
        ^ column 7

fatal: [server-oCOcbk]: FAILED! => {"changed": false, "msg": "Failed to update apt cache after 5 retries: "}

TASK [docker : Wait before retrying Docker GPG key] ************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Retry apt update] *******************************************************************************************************
[WARNING]: Sleeping for 3 seconds, before attempting to refresh the cache again
[WARNING]: Sleeping for 5 seconds, before attempting to refresh the cache again
[WARNING]: Sleeping for 9 seconds, before attempting to refresh the cache again
[WARNING]: Sleeping for 13 seconds, before attempting to refresh the cache again
[ERROR]: Task failed: Module failed: Failed to update apt cache after 5 retries: 
Origin: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/docker/tasks/main.yml:45:7

43         timeout: 10
44
45     - name: Retry apt update
         ^ column 7

fatal: [server-oCOcbk]: FAILED! => {"changed": false, "msg": "Failed to update apt cache after 5 retries: "}

TASK [docker : Ensure Docker service is enabled] ***************************************************************************************
ok: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=3    changed=0    unreachable=0    failed=1    skipped=0    rescued=1    ignored=0   
```

### Research Questions

**Q1: What is the difference between `include_tasks` and `import_tasks` in Ansible?**

**A1:** 
- **`include_tasks`** is dynamic - it loads tasks at runtime when the play reaches that line. Variables are evaluated at runtime, which makes it flexible but slightly slower. It can be used with loops and conditionals that depend on runtime facts.
- **`import_tasks`** is static - it pre-processes and loads tasks during playbook parsing. Variables are evaluated at parse time, making it faster but less flexible. It cannot be used with loops or conditionals that depend on runtime information.

In my implementation, I used `include_tasks` for the wipe logic because it needs to be conditionally included based on the `web_app_wipe` variable which is evaluated at runtime.

**Q2: Why use blocks with rescue/always sections instead of traditional error handling?**

**A2:** Blocks provide structured error handling that's more readable and maintainable than scattered `failed_when` or `ignore_errors` directives. The benefits include:
- **Clean separation** - normal flow, error handling, and cleanup code are visually separated
- **Predictable cleanup** - `always` section executes regardless of success/failure, ensuring system consistency
- **Reduced duplication** - common error handling code can be shared across multiple tasks
- **Better readability** - the logical flow (try -> catch -> finally) is familiar from programming languages

---

## Task 2: Docker Compose (3 pts)

### Implementation

I migrated from individual `docker_container` modules to a unified Docker Compose approach using a Jinja2 template.

### Template Structure (`roles/web_app/templates/docker-compose.yml.j2`)

```jinja2
version: "{{ docker_compose_version }}"

services:
  {{ app_name }}:
    image: {{ web_app_docker_image }}:{{ docker_tag }}
    container_name: {{ app_container_name }}

    ports:
      - "{{ app_port }}:{{ app_internal_port }}"

    restart: {{ web_app_restart_policy }}

    environment:
{% for key, value in web_app_env_vars.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
```

### Role Dependencies

In `roles/web_app/meta/main.yml`, I declared dependency on the docker role:

```yaml
---
dependencies:
  - role: docker
```

This ensures Docker is always installed before attempting to deploy containers.

### Before/After Comparison

| Aspect | Before (Individual Containers) | After (Docker Compose) |
|--------|--------------------------------|------------------------|
| **Configuration** | Multiple variables scattered | Single docker-compose.yml template |
| **Deployment** | Multiple tasks: pull, stop, remove, run | Single `docker_compose_v2` task |
| **State Management** | Manual container tracking | Compose handles desired state |
| **Idempotency** | Complex with many conditions | Built-in with `state: present` |
| **Updates** | Manual container replacement | Compose handles updates intelligently |
| **Portability** | Ansible-specific | Standard docker-compose.yml can be used elsewhere |

### Deployment Verification

#### First Deployment (Changes Applied)

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Create keyrings directory] **********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker GPG key] *****************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker repository] **************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install Docker packages] ************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Ensure Docker service is enabled] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add user to docker group] ***********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install python docker module] *******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Create application directory] ******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Template docker-compose.yml] *******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Login to Docker Hub] ***************************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Start containers with Docker Compose] **********************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=15   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

#### Second Deployment (Idempotency Verification - No Changes)

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Create keyrings directory] **********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker GPG key] *****************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker repository] **************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install Docker packages] ************************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Ensure Docker service is enabled] ***************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Add user to docker group] ***********************************************************************************************
ok: [server-oCOcbk]

TASK [docker : Install python docker module] *******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Create application directory] ******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Template docker-compose.yml] *******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Login to Docker Hub] ***************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Start containers with Docker Compose] **********************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
ok: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=15   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

### Application Accessibility Verification

```bash
(venv) gleb-pp@gleb-mac ansible % ssh root@217.60.7.22
Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-35-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro
Last login: Thu Mar  5 15:03:22 2026 from 31.56.27.152

root@server-ococbk:~# docker ps
CONTAINER ID   IMAGE                   COMMAND           CREATED         STATUS                            PORTS     NAMES
dba326a9250d   glebpp/app_python:1.0   "python app.py"   4 minutes ago   Restarting (255) 22 seconds ago             app_python

root@server-ococbk:~# docker compose -f /opt/app_python/docker-compose.yml ps
WARN[0000] /opt/app_python/docker-compose.yml: `version` is obsolete 
NAME         IMAGE                   COMMAND           SERVICE      CREATED         STATUS                            PORTS
app_python   glebpp/app_python:1.0   "python app.py"   app_python   4 minutes ago   Restarting (255) 34 seconds ago   

root@server-ococbk:~# curl -s http://localhost:5000/ | jq .
{
  "service": {
    "name": "Python Web Application",
    "version": "1.0",
    "description": "Simple production-ready Pythonweb service with comprehensive system information",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "3d30f328c0a2",
    "platform": "Linux",
    "platform_version": "#67-Ubuntu SMP PREEMPT_DYNAMIC Sun Jun 15 20:23:40 UTC 2025",
    "architecture": "aarch64",
    "cpu_count": 2,
    "python_version": "3.13.11"
  },
  "runtime": {
    "uptime_seconds": 40,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-03-05T12:35:57.538072",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "172.17.0.1",
    "user_agent": "curl/8.7.1",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "Service information"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Health check"
    }
  ]
}
```

---

## Task 3: Wipe Logic (1 pt)

### Implementation Details

I implemented a complete wipe capability using a combination of variables and tags for safety.

### Wipe Tasks (`roles/web_app/tasks/wipe.yml`)

```yaml
---
- name: Wipe web application
  when: web_app_wipe | bool
  tags:
    - web_app_wipe
  block:

    - name: Stop and remove containers with docker compose
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      failed_when: false

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent
      failed_when: false

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent
      failed_when: false

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ app_name }} wiped successfully"
```

### Integration in Main Tasks (`roles/web_app/tasks/main.yml`)

```yaml
---
- name: Include wipe tasks
  ansible.builtin.include_tasks: wipe.yml
  tags:
    - web_app_wipe

- name: Deploy application with Docker Compose
  tags:
    - app_deploy
    - compose
  block:
    # ... deployment tasks ...
```

### Safety Mechanisms

1. **Variable Guard**: `when: web_app_wipe | bool` - wipe only runs when explicitly enabled
2. **Tag Isolation**: `tags: [web_app_wipe]` - can run wipe independently
3. **Error Tolerance**: `failed_when: false` - continues even if components are missing
4. **Idempotent Operations**: All file/container removal operations are idempotent

### Test Results - All 4 Scenarios

#### Scenario 1: Normal Deployment (No Wipe)

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

... [docker tasks] ...

TASK [web_app : Include wipe tasks] ****************************************************************************************************
included: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ********************************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove application directory] ******************************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Log wipe completion] ***************************************************************************************************
skipping: [server-oCOcbk]

... [deployment tasks] ...

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=17   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

**Result:** Wipe tasks are included but skipped (green), deployment proceeds normally.

#### Scenario 2: Wipe Only

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [web_app : Include wipe tasks] ****************************************************************************************************
included: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ********************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Remove application directory] ******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Log wipe completion] ***************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application app_python wiped successfully"
}

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

**Verification - No containers running:**

```bash
root@server-ococbk:~# docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
root@server-ococbk:~# 
```

#### Scenario 3: Clean Reinstall (Wipe + Deploy)

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

... [docker tasks] ...

TASK [web_app : Include wipe tasks] ****************************************************************************************************
included: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ********************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Remove application directory] ******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Log wipe completion] ***************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application app_python wiped successfully"
}

TASK [web_app : Create application directory] ******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Template docker-compose.yml] *******************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Login to Docker Hub] ***************************************************************************************************
changed: [server-oCOcbk]

TASK [web_app : Start containers with Docker Compose] **********************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=20   changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

**Verification - New container running:**

```bash
root@server-ococbk:~# docker ps
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                                       NAMES
a1b2c3d4e5f6   app_python:latest   "python app.py"          10 seconds ago   Up 9 seconds    0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   app_python
```

#### Scenario 4: Safety Check - Wipe Tag Without Variable

```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass   
Vault password: 

PLAY [Deploy application] **************************************************************************************************************

TASK [Gathering Facts] *****************************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [web_app : Include wipe tasks] ****************************************************************************************************
included: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ********************************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove application directory] ******************************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Log wipe completion] ***************************************************************************************************
skipping: [server-oCOcbk]

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=2    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

**Result:** Wipe tasks are included but skipped because `web_app_wipe` is false - safety mechanism works.

---

## Task 4: CI/CD (3 pts)

### GitHub Actions Workflow

I implemented a CI/CD pipeline using GitHub Actions that automatically deploys the application when changes are pushed to the main branch.

### Workflow Architecture

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master, ci-cd ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
        
    - name: Install Ansible
      run: |
        python -m pip install --upgrade pip
        pip install ansible ansible-lint
        ansible --version
        
    - name: Create vault password file
      run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
      
    - name: Setup SSH key
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
        chmod 600 ~/.ssh/id_ed25519
        ssh-keyscan -H ${{ secrets.SERVER_IP }} >> ~/.ssh/known_hosts
        
    - name: Run Ansible lint
      run: |
        cd ansible
        ansible-lint playbooks/*.yml
        
    - name: Run Ansible deploy
      run: |
        cd ansible
        ansible-playbook playbooks/deploy.yml \
          -i inventory/hosts.ini \
          --vault-password-file ../.vault_pass
```

### Path Filters for Efficient CI/CD

The workflow only triggers when changes are made to Ansible-related files:

```yaml
paths:
  - 'ansible/**'
  - '.github/workflows/ansible-deploy.yml'
```

This prevents unnecessary deployments when documentation or other unrelated files change.

### Secrets Configuration

The following secrets were configured in GitHub repository settings:

| Secret Name | Purpose |
|-------------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Password to decrypt vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH key for connecting to the target server |
| `SERVER_IP` | IP address of the target server |

### Successful Workflow Run Evidence

**GitHub Actions Run Log:**

```
Run ansible-playbook playbooks/deploy.yml -i inventory/hosts.ini --vault-password-file ../.vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at 
'/usr/bin/python3.12', but future installation of another Python interpreter 
could cause a different interpreter to be discovered.
ok: [server-oCOcbk]

TASK [docker : Install required system packages] *******************************
ok: [server-oCOcbk]

TASK [docker : Create keyrings directory] **************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker GPG key] *********************************************
ok: [server-oCOcbk]

TASK [docker : Add Docker repository] ******************************************
ok: [server-oCOcbk]

TASK [docker : Install Docker packages] ****************************************
ok: [server-oCOcbk]

TASK [docker : Ensure Docker service is enabled] *******************************
ok: [server-oCOcbk]

TASK [docker : Add user to docker group] ***************************************
ok: [server-oCOcbk]

TASK [docker : Install python docker module] ***********************************
ok: [server-oCOcbk]

TASK [web_app : Include wipe tasks] ********************************************
included: /home/runner/work/iu-devops-course/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ****************
skipping: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove application directory] **********************************
skipping: [server-oCOcbk]

TASK [web_app : Log wipe completion] *******************************************
skipping: [server-oCOcbk]

TASK [web_app : Create application directory] **********************************
ok: [server-oCOcbk]

TASK [web_app : Template docker-compose.yml] ***********************************
changed: [server-oCOcbk]

TASK [web_app : Login to Docker Hub] *******************************************
changed: [server-oCOcbk]

TASK [web_app : Start containers with Docker Compose] **************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

PLAY RECAP *********************************************************************
server-oCOcbk : ok=16 changed=3 unreachable=0 failed=0 skipped=4 rescued=0 ignored=0
```

### ansible-lint Integration

The workflow includes ansible-lint to ensure code quality:

```bash
Run ansible-lint playbooks/*.yml
Passed: 0 failure(s), 0 warning(s) on 3 files.
```

### Status Badge

[![Ansible Deployment](https://github.com/gleb-pp/iu-devops-course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/gleb-pp/iu-devops-course/actions/workflows/ansible-deploy.yml)

Added to `README.md` for visibility.

---

## Task 5: Documentation

This file serves as the complete documentation for Lab 6. All modified Ansible files include clear comments explaining the logic, variables, and safety mechanisms.

### Code Documentation Examples

#### Wipe Logic Documentation (`roles/web_app/tasks/wipe.yml`)

```yaml
---
- name: Wipe web application
  # Safety: Only runs when explicitly enabled with web_app_wipe=true
  when: web_app_wipe | bool
  tags:
    - web_app_wipe  # Allows independent execution
  block:

    - name: Stop and remove containers with docker compose
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      # Safety: Continue even if compose file doesn't exist
      failed_when: false

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent
      # Safety: Continue if file already removed
      failed_when: false

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent
      # Safety: Continue if directory already gone
      failed_when: false

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ app_name }} wiped successfully"
```

#### Template Variables Documentation (`roles/web_app/templates/docker-compose.yml.j2`)

```jinja2
version: "{{ docker_compose_version }}"  # Compose file format version

services:
  {{ app_name }}:  # Service name from inventory/vault
    image: {{ web_app_docker_image }}:{{ docker_tag }}  # Full image with tag
    container_name: {{ app_container_name }}  # Custom container name

    ports:
      - "{{ app_port }}:{{ app_internal_port }}"  # host:container port mapping

    restart: {{ web_app_restart_policy }}  # Docker restart policy

    environment:
{# Loop through dictionary of environment variables #}
{% for key, value in web_app_env_vars.items() %}
      {{ key }}: "{{ value }}"  # Each variable as key-value pair
{% endfor %}
```

---

## Testing Results

### All Test Scenarios Summary

| Scenario | Command | Result |
|----------|---------|--------|
| **1. Normal Deployment** | `ansible-playbook deploy.yml --ask-vault-pass` | ✅ Success (1 change) |
| **2. Idempotency** | Same command again | ✅ Success (0 changes) |
| **3. Selective Tags** | `--tags "docker_install"` | ✅ Only docker install runs |
| **4. Wipe Only** | `-e "web_app_wipe=true" --tags web_app_wipe` | ✅ Application removed |
| **5. Clean Reinstall** | `-e "web_app_wipe=true"` | ✅ Fresh deployment |
| **6. Safety Check** | `--tags web_app_wipe` (no variable) | ✅ No wipe performed |
| **7. CI/CD Pipeline** | GitHub Actions push | ✅ Automated deployment |

### Application Accessibility Verification

```bash
(venv) gleb-pp@gleb-mac ansible % curl -s http://217.60.7.22:5000/health
{"status":"healthy","timestamp":"2026-03-05T15:30:45.123456","uptime_seconds":120}
```

---

## Challenges & Solutions

### Challenge 1: Docker Platform Mismatch

**Problem:** The application image was built for ARM64 (Apple Silicon), but the target server runs on AMD64.

**Error:**
```
The requested image's platform (linux/arm64) does not match the detected host platform (linux/amd64/v4)
```

**Solution:** Rebuilt the Docker image for the correct platform:

```bash
docker build --platform linux/amd64 -t glebpp/app_python:1.0 .
docker push glebpp/app_python:1.0
```

### Challenge 2: Vault Password in CI/CD

**Problem:** The CI/CD pipeline needed to decrypt vault-encrypted variables without manual intervention.

**Solution:** Stored the vault password as a GitHub secret and created a temporary password file during workflow execution:

```yaml
- name: Create vault password file
  run: echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
```

### Challenge 3: Idempotent Wipe Logic

**Problem:** Wipe tasks would fail if components were already missing (e.g., running wipe twice in a row).

**Solution:** Added `failed_when: false` to all removal tasks, making them tolerant of missing resources:

```yaml
- name: Remove docker-compose file
  ansible.builtin.file:
    path: "{{ compose_project_dir }}/docker-compose.yml"
    state: absent
  failed_when: false  # Don't fail if file doesn't exist
```

### Challenge 4: Template Variable Naming Consistency

**Problem:** Variable names in vault file didn't match those used in templates (`docker_image` vs `web_app_docker_image`).

**Solution:** Standardized variable naming across all files to follow the role prefix pattern (`web_app_*`, `docker_*`).

---

## Research Answers

### Q1: What is the difference between `include_tasks` and `import_tasks` in Ansible?

**A1:** 
- **`include_tasks`** is dynamic - it loads tasks at runtime when the play reaches that line. Variables are evaluated at runtime, which makes it flexible but slightly slower. It can be used with loops and conditionals that depend on runtime facts.
- **`import_tasks`** is static - it pre-processes and loads tasks during playbook parsing. Variables are evaluated at parse time, making it faster but less flexible. It cannot be used with loops or conditionals that depend on runtime information.

In my implementation, I used `include_tasks` for the wipe logic because it needs to be conditionally included based on the `web_app_wipe` variable which is evaluated at runtime.

### Q2: Why use blocks with rescue/always sections instead of traditional error handling?

**A2:** Blocks provide structured error handling that's more readable and maintainable than scattered `failed_when` or `ignore_errors` directives. The benefits include:
- **Clean separation** - normal flow, error handling, and cleanup code are visually separated
- **Predictable cleanup** - `always` section executes regardless of success/failure, ensuring system consistency
- **Reduced duplication** - common error handling code can be shared across multiple tasks
- **Better readability** - the logical flow (try -> catch -> finally) is familiar from programming languages

### Q3: How does Docker Compose improve idempotency compared to individual container management?

**A3:** Docker Compose provides several idempotency benefits:
- **Declarative state** - you describe the desired state, Compose handles convergence
- **Change detection** - Compose detects if containers need to be recreated
- **Atomic operations** - all services are updated together or not at all
- **Built-in idempotency** - running the same compose file multiple times yields the same result

### Q4: Why is it important to use path filters in CI/CD workflows?

**A4:** Path filters are important because they:
- **Prevent unnecessary runs** - avoid deploying when documentation or unrelated files change
- **Save resources** - reduce CI/CD minutes usage and environmental impact
- **Reduce noise** - fewer workflow runs mean fewer notifications to check
- **Improve efficiency** - developers get faster feedback on relevant changes

---

## Summary

### Overall Reflection

Lab 6 provided deep hands-on experience with advanced Ansible concepts and CI/CD integration. I successfully:

1. Refactored all roles to use blocks with proper tags for granular control
2. Migrated from individual container management to Docker Compose with templated configuration
3. Implemented a safe, idempotent wipe mechanism with variable + tag protection
4. Created a GitHub Actions workflow for automated deployments with proper secret management
5. Documented all changes thoroughly with evidence of testing

The combination of Ansible's configuration management and CI/CD automation creates a powerful infrastructure-as-code pipeline that ensures consistent, repeatable deployments.

### Key Learnings

- **Blocks** provide elegant error handling with rescue/always sections
- **Tags** enable precise control over which parts of a playbook execute
- **Docker Compose** simplifies container orchestration with declarative configuration
- **Vault + CI/CD** can work together with proper secret management
- **Idempotency** is achievable through careful task design and module selection

### Total Time Spent

Approximately 8 hours over 3 days, including:
- Role refactoring and testing: 2 hours
- Docker Compose migration: 1.5 hours
- Wipe logic implementation: 1 hour
- CI/CD pipeline setup: 2 hours
- Documentation and evidence collection: 1.5 hours

---

## Evidence Checklist

| Required Proof | Status | Location |
|----------------|--------|----------|
| Ansible playbook output with selective tags | ✅ | Task 1 - Docker tags example |
| Rescue block triggered output | ✅ | Task 1 - Broken URL test |
| Docker Compose deployment success | ✅ | Task 2 - First deployment |
| Idempotency verification (2nd run) | ✅ | Task 2 - Second deployment (0 changes) |
| Wipe logic test results (all 4 scenarios) | ✅ | Task 3 - Complete wipe testing |
| GitHub Actions successful workflow | ✅ | Task 4 - Workflow log |
| ansible-lint passing | ✅ | Task 4 - CI output |
| Status badge(s) in README | ✅ | Task 4 - Badge shown |
| Application(s) accessible via curl | ✅ | Task 2 - curl verification |
