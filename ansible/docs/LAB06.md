# Task 1

## ansible-playbook playbooks/provision.yml --list-tags
```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

## ansible-playbook playbooks/provision.yml --tags "docker"
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

## ansible-playbook playbooks/provision.yml --tags "docker_install"
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

## Testing rescue block

I replaced `https://download.docker.com/linux/ubuntu/gpg` with `https://download.docker.com/linux/ubuntu/gpgBROKEN` in the task "Add Docker GPG key" to trigger the rescue block.

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

# Task 2

## ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --ask-vault-pass
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

TASK [web_app : Wait for application] **************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Show deployment status] ************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application successfully deployed and running on http://217.60.7.22:5000"
}

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=15   changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

## ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --ask-vault-pass (второй запуск без changed)
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

TASK [web_app : Wait for application] **************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Show deployment status] ************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application is already running on http://217.60.7.22:5000"
}

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=15   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

## checking
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

# Task 3

### Scenario 1 (нормальный deploy)
```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml --ask-vault-pass
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

TASK [web_app : Create application directory] ******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Template docker-compose.yml] *******************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Login to Docker Hub] ***************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Start containers with Docker Compose] **********************************************************************************
[WARNING]: /opt/app_python/docker-compose.yml: `version` is obsolete
changed: [server-oCOcbk]

TASK [web_app : Wait for application] **************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Show deployment status] ************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application successfully deployed and running on http://217.60.7.22:5000"
}

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=17   changed=1    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

### Scenario 2 (wipe only)
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

```bash
root@server-ococbk:~# docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
root@server-ococbk:~# 
```

### Scenario 3 (clean reinstall)
```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --ask-vault-pass
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

TASK [web_app : Wait for application] **************************************************************************************************
ok: [server-oCOcbk]

TASK [web_app : Show deployment status] ************************************************************************************************
ok: [server-oCOcbk] => {
    "msg": "Application successfully deployed and running on http://217.60.7.22:5000"
}

PLAY RECAP *****************************************************************************************************************************
server-oCOcbk              : ok=20   changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

```bash
root@server-ococbk:~# docker ps
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                                       NAMES
a1b2c3d4e5f6   app_python:latest   "python app.py"          10 seconds ago   Up 9 seconds    0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   app_python
```

### Scenario 4 (проверка safety)
```bash
(venv) gleb-pp@gleb-mac ansible % ansible-playbook playbooks/deploy.yml --tags web_app_wipe --ask-vault-pass   
Vault password: 

PLAY [Deploy application] **********************************************************************************************

TASK [Gathering Facts] *************************************************************************************************
[WARNING]: Host 'server-oCOcbk' is using the discovered Python interpreter at '/usr/bin/python3.12', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [server-oCOcbk]

TASK [web_app : Include wipe tasks] ************************************************************************************
included: /Users/gleb-pp/Documents/InnoAssignments/S26 DevOps/iu-devops-course/ansible/roles/web_app/tasks/wipe.yml for server-oCOcbk

TASK [web_app : Stop and remove containers with docker compose] ********************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove docker-compose file] ****************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Remove application directory] **************************************************************************
skipping: [server-oCOcbk]

TASK [web_app : Log wipe completion] ***********************************************************************************
skipping: [server-oCOcbk]

PLAY RECAP *************************************************************************************************************
server-oCOcbk              : ok=2    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0   
```

# Task 4
[![Ansible Deployment](https://github.com/gleb-pp/iu-devops-course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/gleb-pp/iu-devops-course/actions/workflows/ansible-deploy.yml)