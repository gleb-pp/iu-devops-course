import pulumi
import pulumi_yandex as yc

network = yc.VpcNetwork("lab-network")

subnet = yc.VpcSubnet("lab-subnet",
    zone="ru-central1-a",
    network_id=network.id,
    v4_cidr_blocks=["10.5.0.0/24"])

sg = yc.VpcSecurityGroup("lab-sg",
    network_id=network.id,
    ingresses=[
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
            predefined_target="self_security_group"
        ),
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            predefined_target="self_security_group"
        ),
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            predefined_target="self_security_group"
        ),
    ],
    egresses=[
        yc.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            predefined_target="self_security_group"
        )
    ])

vm = yc.ComputeInstance("lab-vm",
    resources=yc.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20),
    boot_disk=yc.ComputeInstanceBootDiskArgs(
        initialize_params=yc.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd83ica41cade1mj35sr",
            size=10)),
    network_interfaces=[yc.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat=True,
        security_group_ids=[sg.id])],
    metadata={
        "ssh-keys": "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG8joAWrULmQflRXNMaMWxT1JxZ41Wt78UKL8bUTmWNN gleb-pp@gleb-mac.local"
    })

pulumi.export("external_ip",
    vm.network_interfaces[0].nat_ip_address)
