displayName = 'lifetime26'
compartmentId = 'ocid1.tenancy.oc1..aaaaaaaa5n3cee26f3lwufnx6iomxp26indk6h2dm7v44pofdo25vtzndy6a'
availabilityDomain = "VVjJ:AP-SINGAPORE-1-AD-1"
imageId = "ocid1.image.oc1.ap-singapore-1.aaaaaaaawmzeznxon5vnxxsudssz4k5nmemctydvd2dwmm54bspws7oj772q"
subnetId = 'ocid1.subnet.oc1.ap-singapore-1.aaaaaaaaawsbepg4j5mth222i3bn4tqcmnkejzyqtoxn2lvhoq6u7v6mrp4q'
ssh_authorized_keys = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHMypJ8K9qSZOdfSIkYz7fPA2gCe2+HKXa1CQE4EXakBj6PvdxAiRfusq24OQQTtB017eEVLiVnurqpsIhGWsA/SmUF48ssUl6J7jAq28S6sE65SuhrVC1YVR+9CS8YitRltWgWrUBIDyZPGzLT8SBYGfA/sh7nQlqi3RxVVJmnDFfOT9TfVhX3kT2qh8WpmbTZLhF6Haw6p7cyfDtVEr1k9L8aljNl08wcAS4/LBwzGEhIUQEaK23KcvnGznYKEcaQ90Tw9yAADwVlKR3kU2qlnyZB6MAxvb3S7T3VGfT69bGxKXlza9nxVyBNxAJQevf6vc54eV9KE4p4Rl+Rtrz ssh-key-2023-01-31"


import oci
import logging
import time
import sys
import requests

LOG_FORMAT = '[%(levelname)s] %(asctime)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("oci.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

ocpus = 1
memory_in_gbs = 1
wait_s_for_retry = 10

logging.info("#####################################################")
logging.info("Script to spawn VM.Standard.E2.1.Micro instance")


message = f'Start spawning instance VM.Standard.E2.1.Micro - {ocpus} ocpus - {memory_in_gbs} GB'
logging.info(message)

logging.info("Loading OCI config")
config = oci.config.from_file(file_location="./config")

logging.info("Initialize service client with default config file")
to_launch_instance = oci.core.ComputeClient(config)

message = f"Instance to create: VM.Standard.E2.1.Micro - {ocpus} ocpus - {memory_in_gbs} GB"
logging.info(message)

logging.info("Check current instances in account")
current_instance = to_launch_instance.list_instances(compartment_id=compartmentId)
response = current_instance.data

total_ocpus = total_memory = _A1_Flex = 0
instance_names = []
if response:
    logging.info(f"{len(response)} instance(s) found!")
    for instance in response:
        logging.info(f"{instance.display_name} - {instance.shape} - {int(instance.shape_config.ocpus)} ocpu(s) - {instance.shape_config.memory_in_gbs} GB(s) | State: {instance.lifecycle_state}")
        instance_names.append(instance.display_name)
        if instance.shape == "VM.Standard.E2.1.Micro" and instance.lifecycle_state not in ("TERMINATING", "TERMINATED"):
            _A1_Flex += 1
            total_ocpus += int(instance.shape_config.ocpus)
            total_memory += int(instance.shape_config.memory_in_gbs)

    message = f"Current: {_A1_Flex} active VM.Standard.E2.1.Micro instance(s) (including RUNNING OR STOPPED)"
    logging.info(message)
else:
    logging.info(f"No instance(s) found!")


message = f"Total ocpus: {total_ocpus} - Total memory: {total_memory} (GB) || Free {2-total_ocpus} ocpus - Free memory: {2-total_memory} (GB)"
logging.info(message)


if total_ocpus + ocpus > 2 or total_memory + memory_in_gbs > 2:
    message = "Total maximum resource exceed free tier limit (Over 2 AMD micro instances total). **SCRIPT STOPPED**"
    logging.critical(message)
    sys.exit()

if displayName in instance_names:
    message = f"Duplicate display name: >>>{displayName}<<< Change this! **SCRIPT STOPPED**"
    logging.critical(message)
    sys.exit()

message = f"Precheck pass! Create new instance VM.Standard.E2.1.Micro: {ocpus} opus - {memory_in_gbs} GB"
logging.info(message)

instance_detail = oci.core.models.LaunchInstanceDetails(
    metadata={
        "ssh_authorized_keys": ssh_authorized_keys
    },
    availability_domain=availabilityDomain,
    shape='VM.Standard.E2.1.Micro',
    compartment_id=compartmentId,
    display_name=displayName,
    source_details=oci.core.models.InstanceSourceViaImageDetails(
        source_type="image", image_id=imageId),
    create_vnic_details=oci.core.models.CreateVnicDetails(
        assign_public_ip=False, subnet_id=subnetId, assign_private_dns_record=True),
    agent_config=oci.core.models.LaunchInstanceAgentConfigDetails(
        is_monitoring_disabled=False,
        is_management_disabled=False,
        plugins_config=[oci.core.models.InstanceAgentPluginConfigDetails(
            name='Vulnerability Scanning', desired_state='DISABLED'), oci.core.models.InstanceAgentPluginConfigDetails(name='Compute Instance Monitoring', desired_state='ENABLED'), oci.core.models.InstanceAgentPluginConfigDetails(name='Bastion', desired_state='DISABLED')]
    ),
    defined_tags={},
    freeform_tags={},
    instance_options=oci.core.models.InstanceOptions(
        are_legacy_imds_endpoints_disabled=False),
    availability_config=oci.core.models.LaunchInstanceAvailabilityConfigDetails(
        recovery_action="RESTORE_INSTANCE"),
    shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
        ocpus=ocpus, memory_in_gbs=memory_in_gbs)
)

to_try = true
while to_try:
    try:
        to_launch_instance.launch_instance(instance_detail)
        to_try = False
        message = 'Success! Edit vnic to get public ip address'
        logging.info(message)
        sys.exit()
    except oci.exceptions.ServiceError as e:
        if e.status == 500:
            message = f"{e.message} Retry in {wait_s_for_retry}s"
        else:
            message = f"{e} Retry in {wait_s_for_retry}s"
        logging.info(message)
        time.sleep(wait_s_for_retry)
    except Exception as e:
        message = f"{e} Retry in {wait_s_for_retry}s"
        logging.info(message)
        time.sleep(wait_s_for_retry)
    except KeyboardInterrupt:
        sys.exit()
