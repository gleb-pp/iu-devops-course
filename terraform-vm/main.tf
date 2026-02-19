terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = "key.json"
  cloud_id  = "b1gond0tlsng6fel92pb"
  folder_id = "b1gpo0jop248pel4prbo"
  zone      = "ru-central1-a"
}

resource "yandex_vpc_network" "network" {
  name = "lab-network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.5.0.0/24"]
}

resource "yandex_vpc_security_group" "sg" {
  name       = "lab-sg"
  network_id = yandex_vpc_network.network.id

  ingress {
    protocol          = "TCP"
    description       = "SSH"
    v4_cidr_blocks    = ["0.0.0.0/0"]
    port              = 22
    predefined_target = "self_security_group"
  }

  ingress {
    protocol          = "TCP"
    description       = "HTTP"
    v4_cidr_blocks    = ["0.0.0.0/0"]
    port              = 80
    predefined_target = "self_security_group"
  }

  ingress {
    protocol          = "TCP"
    description       = "APP"
    v4_cidr_blocks    = ["0.0.0.0/0"]
    port              = 5000
    predefined_target = "self_security_group"
  }

  egress {
    protocol          = "ANY"
    v4_cidr_blocks    = ["0.0.0.0/0"]
    predefined_target = "self_security_group"
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_compute_instance" "vm" {
  name = "lab-vm"

  resources {
    cores  = 2
    memory = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG8joAWrULmQflRXNMaMWxT1JxZ41Wt78UKL8bUTmWNN gleb-pp@gleb-mac.local"
  }
}

output "external_ip" {
  value = yandex_compute_instance.vm.network_interface.0.nat_ip_address
}