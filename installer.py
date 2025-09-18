#!/usr/bin/env python3
"""
Vocard One-Click Installer
Cross-platform installer for Vocard with Docker support
Supports Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import json
import yaml
import urllib.request
from pathlib import Path
from typing import Dict, Any, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class ConfigurationManager:
    """Handles user input and configuration validation"""
    
    REQUIRED_FIELDS = {
        'bot_token': 'Discord Bot Token',
        'client_id': 'Discord Client ID'
    }
    
    OPTIONAL_FIELDS = {
        'prefix': ('Bot Prefix', '?'),
        'admin_id': ('Discord Admin User ID', ''),
        'log_level': ('Log Level', 'INFO')
    }
    
    SERVICE_CONFIGS = {
        'vocard-db': {
            'username': ('MongoDB Username', 'admin', str),
            'password': ('MongoDB Password', 'admin', str),
            'dbname': ('MongoDB Database Name', 'Vocard', str)
        },
        'lavalink': {
            'port': ('Lavalink Port', '2333', int),
            'password': ('Lavalink Password', 'youshallnotpass', str),
            'client_id': ('Spotify Client ID', None, str),
            'client_secret': ('Spotify Client Secret', None, str)
        },
        'vocard-dashboard': {
            'port': ('Dashboard Port', '8080', int),
            'password': ('Dashboard Password', 'admin', str),
            'client_secret_id': ('Dashboard Client Secret ID', None, str),
            'secret_key': ('Dashboard Secret Key (random string)', None, str),
            'redirect_url': ('Dashboard Redirect URI', 'http://localhost:8080/callback', str)
        }
    }

    @staticmethod
    def get_required_input(prompt: str) -> str:
        """Get required input from user with validation"""
        while True:
            value = input(f"{prompt}: ").strip()
            if value:
                return value
            print(f"{Colors.RED}This field is required. Please enter a value.{Colors.END}")

    @staticmethod
    def get_optional_input(prompt: str, default: str = '') -> str:
        """Get optional input from user with default value"""
        display_prompt = f"{prompt} [{default}]: " if default else f"{prompt} (optional): "
        value = input(display_prompt).strip()
        return value if value else default

    @staticmethod
    def get_yes_no_input(prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user"""
        default_text = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} ({default_text}): ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
            print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.END}")

    def collect_basic_configuration(self) -> Dict[str, Any]:
        """Collect basic bot configuration"""
        print(f"\n{Colors.PURPLE}Basic Configuration{Colors.END}")
        print("-" * 30)
        
        config = {}
        
        # Required fields
        for field, prompt in self.REQUIRED_FIELDS.items():
            config[field] = self.get_required_input(prompt)
        
        # Optional fields
        for field, (prompt, default) in self.OPTIONAL_FIELDS.items():
            config[field] = self.get_optional_input(prompt, default)
        
        return config

    def collect_service_configuration(self, service_name: str) -> Dict[str, Any]:
        """Collect configuration for a specific service"""
        config = {}
        service_config = self.SERVICE_CONFIGS[service_name]
        
        print(f"\n{Colors.CYAN}{service_name.title()} Configuration{Colors.END}")
        
        for field, (prompt, default, field_type) in service_config.items():
            while True:
                if default is None:
                    value = self.get_required_input(prompt)
                else:
                    value = self.get_optional_input(prompt, default)
                
                # If empty value is provided for optional field, use default
                if not value and default:
                    value = default
                    break
                
                # Convert value to the appropriate type
                try:
                    if field_type == int:
                        config[field] = int(value)
                    else:
                        config[field] = value
                    break  # Exit the loop if conversion succeeds
                except ValueError:
                    print(f"{Colors.RED}Invalid number format for {prompt}. Please enter a valid number.{Colors.END}")
                    continue  # Ask for input again
        
        return config

    def collect_installation_directory(self, default_dir: Path) -> Path:
        """Collect installation directory from user"""
        install_dir = self.get_optional_input(
            f"Installation directory", 
            str(default_dir)
        )
        return Path(install_dir)


class FileManager:
    """Handles file operations and downloads"""
    
    def __init__(self, github_repo: str):
        self.github_repo = github_repo
        self.urls = {
            'docker_compose': f"https://raw.githubusercontent.com/{github_repo}-Installer/main/docker-compose.yml",
            'bot_settings': f"https://raw.githubusercontent.com/{github_repo}/main/settings%20Example.json",
            'dashboard_settings': f"https://raw.githubusercontent.com/{github_repo}-Dashboard/main/settings%20Example.json",
            'lavalink_settings': f"https://raw.githubusercontent.com/{github_repo}-Installer/main/lavalink/application.yml"
        }

    def download_file(self, url: str, destination: Path) -> bool:
        """Download file from URL to destination"""
        try:
            print(f"{Colors.CYAN}Downloading {url.split('/')[-1]}{Colors.END}")
            urllib.request.urlretrieve(url, destination)
            print(f"{Colors.GREEN}Downloaded to {destination}{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to download {url}: {e}{Colors.END}")
            return False

    def create_directory(self, path: Path) -> bool:
        """Create directory if it doesn't exist"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"{Colors.GREEN}Created directory: {path}{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to create directory {path}: {e}{Colors.END}")
            return False

    def download_config_files(self, install_dir: Path, enabled_services: set) -> bool:
        """Download all required configuration files"""
        # Create base directory
        if not self.create_directory(install_dir):
            return False

        # Download docker-compose.yml
        if not self.download_file(self.urls['docker_compose'], install_dir / "docker-compose.yml"):
            return False

        # Download bot settings
        if not self.download_file(self.urls['bot_settings'], install_dir / "settings.json"):
            return False

        # Download service-specific files
        if 'lavalink' in enabled_services:
            lavalink_dir = install_dir / "lavalink"
            if not self.create_directory(lavalink_dir):
                return False
            if not self.create_directory(lavalink_dir / "plugins"):
                return False
            if not self.create_directory(lavalink_dir / "logs"):
                return False
            if not self.download_file(self.urls['lavalink_settings'], lavalink_dir / "application.yml"):
                return False

        if 'vocard-dashboard' in enabled_services:
            dashboard_dir = install_dir / "dashboard"
            if not self.create_directory(dashboard_dir):
                return False
            if not self.download_file(self.urls['dashboard_settings'], dashboard_dir / "settings.json"):
                return False

        return True


class ConfigFileUpdater:
    """Updates configuration files with user settings"""

    @staticmethod
    def update_docker_compose(file_path: Path, config: Dict[str, Any], disabled_services: set) -> bool:
        """Remove disabled services from docker-compose.yml"""
        try:
            with open(file_path, 'r') as f:
                docker_compose = yaml.safe_load(f)

            services: dict[str, Any] = docker_compose.get('services', {})
            for service_name, service in services.copy().items():
                if service_name in disabled_services:
                    services.pop(service_name, None)
                    continue
                
                if service.get("depends_on"):
                    for dep in disabled_services:
                        service["depends_on"].pop(dep, None)
                        
                if service_name == "lavalink":
                    lavalink_config = config['service_configs']['lavalink']
                    service["environment"] = [
                        f"SERVER_PORT={lavalink_config['port']}",
                        f"LAVALINK_SERVER_PASSWORD={lavalink_config['password']}"
                    ]
                    service["expose"] = [lavalink_config["port"]]
                    
                if service_name == "vocard-db":
                    db_config = config['service_configs']['vocard-db']
                    service["environment"] = [
                        f"MONGO_INITDB_ROOT_USERNAME={db_config['username']}",
                        f"MONGO_INITDB_ROOT_PASSWORD={db_config['password']}"
                    ]
                
                if service_name == "vocard-dashboard":
                    dashboard_config = config['service_configs']['vocard-dashboard']
                    service["ports"] = [f"{dashboard_config['port']}:{dashboard_config['port']}"]

            with open(file_path, 'w') as f:
                yaml.dump(docker_compose, f, default_flow_style=False, indent=4)

            print(f"{Colors.GREEN}Updated docker-compose.yml{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to update docker-compose.yml: {e}{Colors.END}")
            return False

    @staticmethod
    def update_bot_settings(file_path: Path, config: Dict[str, Any]) -> bool:
        """Update bot settings.json with user configuration"""
        try:
            with open(file_path, 'r') as f:
                settings = json.load(f)

            # Basic settings
            settings['token'] = config['bot_token']
            settings['client_id'] = config['client_id']
            settings['prefix'] = config['prefix']

            # Database settings
            if db_config := config['service_configs'].get('vocard-db'):
                settings['mongodb_url'] = (
                    f"mongodb://{db_config['username']}:{db_config['password']}"
                    f"@vocard-db:27017"
                )
                settings['mongodb_name'] = db_config['dbname']

            # Lavalink settings
            if lavalink_config := config['service_configs'].get('lavalink'):
                if 'nodes' in settings and 'DEFAULT' in settings['nodes']:
                    settings['nodes']['DEFAULT']['port'] = int(lavalink_config['port'])
                    settings['nodes']['DEFAULT']['password'] = lavalink_config['password']

            # Dashboard settings
            if dashboard_config := config['service_configs'].get('vocard-dashboard'):
                if 'ipc_client' in settings:
                    settings['ipc_client']['enabled'] = True
                    settings['ipc_client']['port'] = int(dashboard_config['port'])
                    settings['ipc_client']['password'] = dashboard_config['password']

            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)

            print(f"{Colors.GREEN}Updated bot settings.json{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to update bot settings.json: {e}{Colors.END}")
            return False

    @staticmethod
    def update_lavalink_settings(file_path: Path, config: Dict[str, Any]) -> bool:
        """Update lavalink application.yml"""
        try:
            lavalink_config = config['service_configs']['lavalink']
            
            with open(file_path, 'r') as f:
                settings = yaml.safe_load(f)

            # Update server settings
            settings['server']['port'] = int(lavalink_config['port'])
            settings['server']['password'] = lavalink_config['password']

            # Update Spotify settings
            spotify_settings = settings.get('plugins', {}).get('lavasrc', {}).get('spotify', {})
            spotify_settings['clientId'] = lavalink_config['client_id']
            spotify_settings['clientSecret'] = lavalink_config['client_secret']
            spotify_settings['preferAnonymousToken'] = False

            with open(file_path, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False, indent=4)

            print(f"{Colors.GREEN}Updated lavalink settings{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to update lavalink settings: {e}{Colors.END}")
            return False

    @staticmethod
    def update_dashboard_settings(file_path: Path, config: Dict[str, Any]) -> bool:
        """Update dashboard settings.json"""
        try:
            dashboard_config = config['service_configs']['vocard-dashboard']
            
            with open(file_path, 'r') as f:
                settings = json.load(f)

            settings.update({
                "port": int(dashboard_config['port']),
                "password": dashboard_config['password'],
                "client_id": config['client_id'],
                "client_secret_id": dashboard_config['client_secret_id'],
                "redirect_url": dashboard_config['redirect_url'],
                "secret_key": dashboard_config['secret_key']
            })

            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)

            print(f"{Colors.GREEN}Updated dashboard settings{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to update dashboard settings: {e}{Colors.END}")
            return False


class DockerManager:
    """Handles Docker operations"""

    @staticmethod
    def run_command(command: str, timeout: int = 120) -> Tuple[bool, str, str]:
        """Run system command safely"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, 
                text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check_docker_installation(self) -> Tuple[bool, bool]:
        """Check if Docker and Docker Compose are installed"""
        print(f"{Colors.CYAN}Checking Docker installation...{Colors.END}")
        
        docker_installed, _, _ = self.run_command("docker --version")
        
        # Check both docker compose (v2) and docker-compose (v1)
        compose_v2, _, _ = self.run_command("docker compose version")
        compose_v1, _, _ = self.run_command("docker-compose --version")
        compose_installed = compose_v2 or compose_v1
        
        return docker_installed, compose_installed

    def start_services(self, install_dir: Path) -> bool:
        """Start Docker services"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Starting Vocard services...{Colors.END}")
        
        original_dir = os.getcwd()
        try:
            os.chdir(install_dir)
            
            # Pull images
            print(f"{Colors.CYAN}Pulling Docker images...{Colors.END}")
            success, _, stderr = self.run_command("docker compose pull")
            if not success:
                print(f"{Colors.YELLOW}Pull failed: {stderr}{Colors.END}")
            
            # Start services
            print(f"{Colors.CYAN}Starting services...{Colors.END}")
            success, stdout, stderr = self.run_command("docker compose up -d")
            
            if success:
                print(f"{Colors.GREEN}Vocard services started successfully!{Colors.END}")
                
                # Show service status
                success_status, stdout_status, _ = self.run_command("docker compose ps")
                if success_status:
                    print(f"\n{Colors.BLUE}Service Status:{Colors.END}")
                    print(stdout_status)
                return True
            else:
                print(f"{Colors.RED}Failed to start services: {stderr}{Colors.END}")
                return False
                
        finally:
            os.chdir(original_dir)


class VocardInstaller:
    """Main installer class that orchestrates the installation process"""
    
    OPTIONAL_SERVICES = ["lavalink", "spotify-tokener", "vocard-db", "vocard-dashboard"]
    GITHUB_REPO = "ChocoMeow/Vocard"

    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.config_manager = ConfigurationManager()
        self.file_manager = FileManager(self.GITHUB_REPO)
        self.config_updater = ConfigFileUpdater()
        self.docker_manager = DockerManager()

    def print_banner(self):
        """Print installation banner"""
        print("=" * 60)
        print(f"{Colors.BOLD}{Colors.CYAN}VOCARD INSTALLER{Colors.END}")
        print("=" * 60)
        print(f"{Colors.BLUE}System: {platform.system()} {platform.release()}{Colors.END}")
        print(f"{Colors.BLUE}Architecture: {platform.machine()}{Colors.END}")
        print("=" * 60)

    def collect_configuration(self) -> Dict[str, Any]:
        """Collect all configuration from user"""
        # Installation directory
        default_dir = Path(__file__).parent.resolve()
        install_dir = self.config_manager.collect_installation_directory(default_dir)
        
        # Basic configuration
        config = self.config_manager.collect_basic_configuration()
        config['install_dir'] = install_dir
        
        # Service configuration
        print(f"\n{Colors.CYAN}Optional Services Configuration{Colors.END}")
        print("Configure the following optional services:")
        
        config['service_configs'] = {}
        enabled_services = set()
        
        for service in self.OPTIONAL_SERVICES:
            if self.config_manager.get_yes_no_input(f"\n{Colors.YELLOW}Enable {service}? {Colors.END}"):
                enabled_services.add(service)
                if service in self.config_manager.SERVICE_CONFIGS:
                    config['service_configs'][service] = (
                        self.config_manager.collect_service_configuration(service)
                    )
        
        config['enabled_services'] = enabled_services
        return config

    def setup_configuration_files(self, config: Dict[str, Any]) -> bool:
        """Download and configure all files"""
        install_dir = config['install_dir']
        enabled_services = config['enabled_services']
        
        # Download files
        if not self.file_manager.download_config_files(install_dir, enabled_services):
            return False
        
        # Update docker-compose.yml
        disabled_services = set(self.OPTIONAL_SERVICES) - enabled_services
        if not self.config_updater.update_docker_compose(
            install_dir / "docker-compose.yml", config, disabled_services
        ):
            return False
        
        # Update bot settings
        if not self.config_updater.update_bot_settings(
            install_dir / "settings.json", config
        ):
            return False
        
        # Update service-specific settings
        if 'lavalink' in enabled_services:
            if not self.config_updater.update_lavalink_settings(
                install_dir / "lavalink" / "application.yml", config
            ):
                return False
        
        if 'vocard-dashboard' in enabled_services:
            if not self.config_updater.update_dashboard_settings(
                install_dir / "dashboard" / "settings.json", config
            ):
                return False
        
        return True

    def print_success_message(self, install_dir: Path):
        """Print installation success message"""
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}{Colors.GREEN}VOCARD INSTALLATION COMPLETED!{Colors.END}")
        print("=" * 60)
        print(f"{Colors.BLUE}Installation directory: {install_dir}{Colors.END}")
        print(f"\n{Colors.CYAN}Management Commands:{Colors.END}")
        print(f"  cd {install_dir}")
        print("  docker compose up -d    # Start services")
        print("  docker compose down     # Stop services")
        print("  docker compose logs -f  # View logs")
        print("  docker compose pull     # Update images")
        print(f"\n{Colors.YELLOW}For support, visit: https://github.com/{self.GITHUB_REPO}{Colors.END}")
        print("=" * 60)

    def run(self) -> bool:
        """Main installation process"""
        try:
            self.print_banner()
            
            # Check Docker installation
            docker_installed, compose_installed = self.docker_manager.check_docker_installation()
            
            if not docker_installed:
                print(f"{Colors.RED}Docker is not installed. Please install Docker manually.{Colors.END}")
                return False
            
            if not compose_installed:
                print(f"{Colors.RED}Docker Compose is not available. Please install it manually.{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}Docker and Docker Compose are available{Colors.END}")
            
            # Collect configuration
            config = self.collect_configuration()
            
            # Setup configuration files
            if not self.setup_configuration_files(config):
                return False
            
            # Start services
            if not self.docker_manager.start_services(config['install_dir']):
                return False
            
            # Print success message
            self.print_success_message(config['install_dir'])
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Installation cancelled by user{Colors.END}")
            return False
        except Exception as e:
            print(f"\n{Colors.RED}Installation failed: {e}{Colors.END}")
            return False


def main():
    """Main entry point"""
    installer = VocardInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()