import docker
from docker.errors import NotFound, APIError

# Initialize Docker client
try:
    client = docker.from_env()
except APIError:
    client = None

def get_docker_client():
    if client is None:
        raise RuntimeError("Docker is not available or not configured correctly.")
    return client

def create_container(image: str, name: str, command: str = None, ports: dict = None, volumes: dict = None, environment: dict = None, mem_limit: str = "256m", cpu_shares: int = 512):
    """
    Creates a new Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.create(
            image=image,
            name=name,
            command=command,
            ports=ports,
            volumes=volumes,
            environment=environment,
            mem_limit=mem_limit,
            cpu_shares=cpu_shares, # Relative weight, 1024 is the default
            detach=True,
        )
        return container
    except APIError as e:
        # Handle creation errors, e.g., name conflict
        raise RuntimeError(f"Failed to create container: {e}")

def start_container(container_id: str):
    """
    Starts a Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.get(container_id)
        container.start()
        return True
    except NotFound:
        return False
    except APIError as e:
        raise RuntimeError(f"Failed to start container: {e}")

def stop_container(container_id: str):
    """
    Stops a Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.get(container_id)
        container.stop()
        return True
    except NotFound:
        return False
    except APIError as e:
        raise RuntimeError(f"Failed to stop container: {e}")

def restart_container(container_id: str):
    """
    Restarts a Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.get(container_id)
        container.restart()
        return True
    except NotFound:
        return False
    except APIError as e:
        raise RuntimeError(f"Failed to restart container: {e}")

def remove_container(container_id: str):
    """
    Removes a Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.get(container_id)
        container.remove(force=True) # Force removal even if running
        return True
    except NotFound:
        return False
    except APIError as e:
        raise RuntimeError(f"Failed to remove container: {e}")

def get_container_status(container_id: str):
    """
    Gets the status of a Docker container.
    """
    d_client = get_docker_client()
    try:
        container = d_client.containers.get(container_id)
        return container.status
    except NotFound:
        return "not_found"
    except APIError as e:
        raise RuntimeError(f"Failed to get container status: {e}")