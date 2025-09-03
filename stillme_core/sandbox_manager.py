import os
import subprocess
import logging
from typing import Optional, List
from stillme_core.ai_manager import AIManager # Cần import AIManager để sử dụng nếu sandbox cần gọi AI

logger = logging.getLogger('StillmeCore-SandboxManager')
class DockerSandboxManager:
        def __init__(self, project_path: str = ".", docker_image: str = "python:3.9-slim-buster"):
            self.project_path = os.path.abspath(project_path)
            self.docker_image = docker_image
            self.container_name = f"agent_dev_sandbox_{os.path.basename(self.project_path).replace('.', '_')}_{os.getpid()}"
            self.container_id = None
            logger.info(f"DockerSandboxManager initialized with image: {self.docker_image}")

        def _run_command_in_host(self, command: List[str], timeout: int = 60):
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
                return result
            except Exception as e:
                logger.error(f"Error running command: {command} | {e}")
                return None



        def start_container(self) -> bool:
            # Check if Docker is running
            try:
                self._run_command_in_host(["docker", "info"], timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                logger.error("Docker is not running or not found. Please start Docker.")
                return False

            # Stop and remove any old container with the same name
            self._run_command_in_host(["docker", "rm", "-f", self.container_name])

            # Build or pull the Docker image if it doesn't exist
            # For simplicity, we just pull the default python image.
            # In a real scenario, you might have a custom Dockerfile for your project environment.
            logger.info(f"Pulling Docker image {self.docker_image}...")
            result = self._run_command_in_host(["docker", "pull", self.docker_image], timeout=60)
            if result is None or result.returncode != 0:
                logger.error(f"Failed to pull Docker image: {result.stderr}")
                return False

            # Run the container, mounting the project directory
            logger.info(f"Starting Docker container {self.container_name}...")
            # Use a dummy command to keep the container running
            cmd = ["docker", "run", "-d",
                   "--name", self.container_name,
                   "-v", f"{self.project_path}:/app", # Mount project directory
                   "-w", "/app", # Set working directory inside container
                   self.docker_image,
                   "tail", "-f", "/dev/null"] # Keep container running
            
            result = self._run_command_in_host(cmd)
            if result.returncode != 0:
                logger.error(f"Failed to start container: {result.stderr}")
                return False
            
            self.container_id = result.stdout.strip()
            logger.info(f"Container {self.container_name} started with ID: {self.container_id}")
            return True

        def stop_container(self):
            if self.container_id:
                logger.info(f"Stopping and removing container {self.container_name}...")
                self._run_command_in_host(["docker", "stop", self.container_name])
                self._run_command_in_host(["docker", "rm", self.container_name])
                self.container_id = None
            logger.info("Docker container stopped and removed.")

        def run_command(self, command: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
            if not self.container_id:
                logger.error("No active container to run command in.")
                return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr="No active container.")
            
            full_command = ["docker", "exec", self.container_id] + command
            logger.info(f"Running command in container: {' '.join(command)}")
            try:
                # Add a timeout to prevent commands from hanging indefinitely
                result = self._run_command_in_host(full_command, timeout=timeout)
                return result
            except subprocess.TimeoutExpired:
                logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
                return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr="Command timed out.")
            except Exception as e:
                logger.error(f"Error executing command in container: {e}")
                return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr=f"Error: {e}")

        def get_file_content(self, file_path_in_container: str) -> Optional[str]:
            if not self.container_id:
                logger.error("No active container to get file content from.")
                return None
            try:
                # Use docker exec cat to get file content
                result = self.run_command(["cat", file_path_in_container])
                if result.returncode == 0:
                    return result.stdout
                else:
                    logger.error(f"Failed to get file content from {file_path_in_container}: {result.stderr}")
                    return None
            except Exception as e:
                logger.error(f"Error getting file content from container: {e}")
                return None

        def write_file_content(self, file_path_in_container: str, content: str) -> bool:
            if not self.container_id:
                logger.error("No active container to write file content to.")
                return False
            try:
                # Using docker exec sh -c "echo 'content' > file"
                # Need to be careful with quotes and special characters
                # For more complex content, writing to a temp file and copying might be better
                # Or using 'docker cp' from host to container after writing a temp file on host
                escaped_content = content.replace("'", "'\\''") # Escape single quotes
                cmd = ["sh", "-c", f"echo '{escaped_content}' > {file_path_in_container}"]
                result = self.run_command(cmd)
                if result.returncode == 0:
                    return True
                else:
                    logger.error(f"Failed to write file content to {file_path_in_container}: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Error writing file content in container: {e}")
                return False
    # --- End Fallback/Local Definitions ---