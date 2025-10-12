import libvirt
import sys

# Connect to the local QEMU/KVM daemon
try:
    conn = libvirt.open('qemu:///system')
except libvirt.libvirtError as e:
    # We can't do anything if we can't connect, so we'll print an error and exit
    # In a real app, this should be handled more gracefully (e.g., logging)
    print(f'Failed to open connection to qemu:///system: {e}', file=sys.stderr)
    conn = None

def get_libvirt_connection():
    if conn is None:
        raise RuntimeError("Failed to connect to libvirt. Is the daemon running?")
    return conn

def list_vms():
    """
    Lists all virtual machines (domains) managed by libvirt.
    """
    lv_conn = get_libvirt_connection()
    domains = lv_conn.listAllDomains(0)
    return [domain.name() for domain in domains]

def get_vm_status(domain_name: str):
    """
    Gets the status of a specific virtual machine.
    """
    lv_conn = get_libvirt_connection()
    try:
        domain = lv_conn.lookupByName(domain_name)
        state, reason = domain.state()
        # Map state integer to a human-readable string
        state_map = {
            libvirt.VIR_DOMAIN_NOSTATE: 'nostate',
            libvirt.VIR_DOMAIN_RUNNING: 'running',
            libvirt.VIR_DOMAIN_BLOCKED: 'blocked',
            libvirt.VIR_DOMAIN_PAUSED: 'paused',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'shutdown',
            libvirt.VIR_DOMAIN_SHUTOFF: 'shutoff',
            libvirt.VIR_DOMAIN_CRASHED: 'crashed',
            libvirt.VIR_DOMAIN_PMSUSPENDED: 'pmsuspended',
        }
        return state_map.get(state, 'unknown')
    except libvirt.libvirtError:
        return "not_found"

import os
import shutil
import uuid

# ... (previous code) ...

BASE_IMAGE_PATH = "/var/lib/libvirt/images/base.qcow2"
VM_DISK_DIR = "/var/lib/libvirt/images"

VM_XML_TEMPLATE = """
<domain type='kvm'>
  <name>{name}</name>
  <uuid>{uuid}</uuid>
  <memory unit='KiB'>1048576</memory>
  <currentMemory unit='KiB'>1048576</currentMemory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc-q35-8.2'>hvm</type>
    <boot dev='hd'/>
  </os>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'>
      <listen type='address' address='127.0.0.1'/>
    </graphics>
  </devices>
</domain>
"""

def create_vm(domain_name: str):
    """
    Creates a new VM by cloning a base image and defining a new domain.
    """
    lv_conn = get_libvirt_connection()

    # 1. Clone the base disk image
    disk_path = os.path.join(VM_DISK_DIR, f"{domain_name}.qcow2")
    if not os.path.exists(BASE_IMAGE_PATH):
        raise RuntimeError(f"Base image not found at {BASE_IMAGE_PATH}")
    try:
        shutil.copyfile(BASE_IMAGE_PATH, disk_path)
    except IOError as e:
        raise RuntimeError(f"Failed to clone base image: {e}")

    # 2. Define the VM from XML
    vm_uuid = str(uuid.uuid4())
    xml_config = VM_XML_TEMPLATE.format(
        name=domain_name,
        uuid=vm_uuid,
        disk_path=disk_path
    )

    try:
        domain = lv_conn.defineXML(xml_config)
        return domain
    except libvirt.libvirtError as e:
        # Clean up the cloned disk if VM definition fails
        os.remove(disk_path)
        raise RuntimeError(f"Failed to define VM: {e}")

def start_vm(domain_name: str):
    """Starts a VM."""
    lv_conn = get_libvirt_connection()
    try:
        domain = lv_conn.lookupByName(domain_name)
        domain.create()
        return True
    except libvirt.libvirtError:
        return False

def stop_vm(domain_name: str):
    """Stops a VM."""
    lv_conn = get_libvirt_connection()
    try:
        domain = lv_conn.lookupByName(domain_name)
        domain.destroy() # Force stop
        return True
    except libvirt.libvirtError:
        return False

def restart_vm(domain_name: str):
    """Restarts a VM."""
    lv_conn = get_libvirt_connection()
    try:
        domain = lv_conn.lookupByName(domain_name)
        domain.reboot()
        return True
    except libvirt.libvirtError:
        return False

def remove_vm(domain_name: str):
    """
    Removes a VM and its associated disk.
    """
    lv_conn = get_libvirt_connection()
    try:
        domain = lv_conn.lookupByName(domain_name)

        # Undefine the domain
        domain.undefine()

        # Remove the disk
        disk_path = os.path.join(VM_DISK_DIR, f"{domain_name}.qcow2")
        if os.path.exists(disk_path):
            os.remove(disk_path)

        return True
    except libvirt.libvirtError:
        return False # Domain not found

# Remember to close the connection when the application exits
# This can be handled in the main application's shutdown event
def close_connection():
    if conn:
        conn.close()