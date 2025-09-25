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
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')


class ConfigurationManager:
    """Handles user input and configuration validation"""
    
    REQUIRED_FIELDS = {
        'bot_token': {
            'prompt': 'Discord Bot Token',
            'description': '''Your Discord bot's secret token.
            
How to get it:
1. Go to https://discord.com/developers/applications
2. Select your bot application (or create a new one)
3. Go to the "Bot" section
4. Click "Reset Token" to reveal your bot token
5. Copy the token (keep it secret!)

Example: MTExNjE4ODk5ODc4MzY5MDc3Mg.GxYzQw.example_token_here''',
            'help_url': 'https://discord.com/developers/docs/topics/oauth2#bots'
        },
        'client_id': {
            'prompt': 'Discord Client ID',
            'description': '''Your Discord application's client ID (also called Application ID).

How to get it:
1. Go to https://discord.com/developers/applications
2. Select your bot application
3. In the "General Information" section, copy the "Application ID"

Example: 1116188998783690772

This is used for OAuth2 authentication and bot invites.''',
            'help_url': 'https://discord.com/developers/applications'
        }
    }
    
    OPTIONAL_FIELDS = {
        'prefix': {
            'prompt': 'Bot Prefix',
            'default': '?',
            'description': '''The command prefix for your Discord bot.

This is the character(s) users type before bot commands.
Examples: ?, !, /, ~, v!

Default: ?

Users will type commands like: ?play song_name''',
            'help_url': None
        }
    }
    
    SERVICE_CONFIGS = {
        'vocard-db': {
            'username': {
                'prompt': 'MongoDB Username',
                'default': 'admin',
                'type': str,
                'description': '''Username for MongoDB database authentication.

This will be the root username for your MongoDB instance.
Default: admin

Note: This is only used internally by the bot to connect to the database.''',
                'help_url': None
            },
            'password': {
                'prompt': 'MongoDB Password',
                'default': 'admin',
                'type': str,
                'description': '''Password for MongoDB database authentication.

Choose a secure password for your MongoDB root user.
Default: admin (change this for security!)

Note: This is only used internally by the bot to connect to the database.''',
                'help_url': None
            },
            'dbname': {
                'prompt': 'MongoDB Database Name',
                'default': 'Vocard',
                'type': str,
                'description': '''Name of the MongoDB database to store bot data.

This database will store user preferences, playlists, and bot settings.
Default: Vocard

You can use any name you prefer.''',
                'help_url': None
            }
        },
        'lavalink': {
            'port': {
                'prompt': 'Lavalink Port',
                'default': '2333',
                'type': int,
                'description': '''Port number for the Lavalink audio server.

Lavalink handles music streaming and audio processing.
Default: 2333

Make sure this port is not used by other services.''',
                'help_url': 'https://github.com/freyacodes/Lavalink'
            },
            'password': {
                'prompt': 'Lavalink Password',
                'default': 'youshallnotpass',
                'type': str,
                'description': '''Password for Lavalink server authentication.

This secures communication between the bot and Lavalink.
Default: youshallnotpass

Choose a secure password for production use.''',
                'help_url': None
            },
            'client_id': {
                'prompt': 'Spotify Client ID',
                'default': None,
                'type': str,
                'description': '''Spotify application client ID (optional but recommended).

Required for Spotify music support. Leave empty to skip Spotify integration.

How to get it:
1. Go to https://developer.spotify.com/dashboard
2. Create a new app (or use existing)
3. Copy the "Client ID"

Example: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p''',
                'help_url': 'https://developer.spotify.com/dashboard'
            },
            'client_secret': {
                'prompt': 'Spotify Client Secret',
                'default': None,
                'type': str,
                'description': '''Spotify application client secret (optional but recommended).

Required for Spotify music support. Leave empty to skip Spotify integration.

How to get it:
1. Go to https://developer.spotify.com/dashboard
2. Open your app settings
3. Click "Show client secret"
4. Copy the client secret

Example: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0''',
                'help_url': 'https://developer.spotify.com/dashboard'
            }
        },
        'vocard-dashboard': {
            'host': {
                'prompt': 'Dashboard Host',
                'default': '0.0.0.0',
                'type': str,
                'description': '''Host address for the web dashboard.

0.0.0.0 allows access from any IP address.
127.0.0.1 or localhost restricts to local access only.
Default: 0.0.0.0

For security, use 127.0.0.1 if only accessing locally.''',
                'help_url': None
            },
            'port': {
                'prompt': 'Dashboard Port',
                'default': '8080',
                'type': int,
                'description': '''Port number for the web dashboard.

The dashboard will be accessible at http://your-server:port
Default: 8080

Make sure this port is not used by other services.
Example: Access at http://localhost:8080''',
                'help_url': None
            },
            'password': {
                'prompt': 'Dashboard Password',
                'default': 'admin',
                'type': str,
                'description': '''Password for dashboard authentication.

This password protects access to your bot's web dashboard.
Default: admin (change this for security!)

Choose a strong password for production use.''',
                'help_url': None
            },
            'client_secret_id': {
                'prompt': 'Dashboard Client Secret ID',
                'default': None,
                'type': str,
                'description': '''Discord OAuth2 client secret for dashboard login.

Required for Discord OAuth2 authentication on the dashboard.

How to get it:
1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Go to "OAuth2" → "General"
4. Click "Reset Secret" to generate a new client secret
5. Copy the client secret

Example: a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0u1V2w3X4y5Z6''',
                'help_url': 'https://discord.com/developers/applications'
            },
            'secret_key': {
                'prompt': 'Dashboard Secret Key',
                'default': None,
                'type': str,
                'description': '''Random secret key for dashboard session security.

This should be a long, random string used for encrypting sessions.

How to generate:
- Use a password generator with 50+ characters
- Include letters, numbers, and symbols
- Keep it secret and unique

Example: aB3$x9Kp2#vR8mN4qL7sT1wE6yU0iO5hG9fD2cV8bN3mQ7xS1zA4''',
                'help_url': None
            },
            'redirect_url': {
                'prompt': 'Dashboard Redirect URI',
                'default': 'http://localhost:8080/callback',
                'type': str,
                'description': '''OAuth2 redirect URI for Discord authentication.

This must match the redirect URI configured in your Discord app.

How to configure:
1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Go to "OAuth2" → "General"
4. Add this URL to "Redirects"

Default: http://localhost:8080/callback
Change localhost:8080 to your actual domain/port if different.''',
                'help_url': 'https://discord.com/developers/applications'
            }
        }
    }

    @staticmethod
    def display_field_help(field_config: dict):
        """Display detailed help information for a field"""
        if 'description' in field_config:
            print(f"\n{Colors.CYAN}{'─' * 60}{Colors.END}")
            print(f"{Colors.CYAN}ℹ️  Help:{Colors.END}")
            print(field_config['description'])
            
            if field_config.get('help_url'):
                print(f"\n{Colors.BLUE}📖 More info: {field_config['help_url']}{Colors.END}")
            
            print(f"{Colors.CYAN}{'─' * 60}{Colors.END}")
        
        print()  # Add spacing

    @staticmethod
    def get_required_input(prompt: str, field_config: dict = None) -> str:
        """Get required input from user with validation"""
        if field_config:
            ConfigurationManager.display_field_help(field_config)
        
        while True:
            value = input(f"{Colors.YELLOW}{prompt}: {Colors.END}").strip()
            if value:
                Colors.clear_screen()
                return value
            print(f"{Colors.RED}This field is required. Please enter a value.{Colors.END}")
            
            # Offer to show help again for complex fields
            if field_config and input(f"{Colors.CYAN}Show help again? (y/N): {Colors.END}").strip().lower() == 'y':
                Colors.clear_screen()
                ConfigurationManager.display_field_help(field_config)

    @staticmethod
    def get_optional_input(prompt: str, default: str = '', field_config: dict = None) -> str:
        """Get optional input from user with default value"""
        if field_config:
            ConfigurationManager.display_field_help(field_config)
        
        display_prompt = f"{Colors.YELLOW}{prompt} [{default}]: {Colors.END}" if default else f"{Colors.YELLOW}{prompt} (optional): {Colors.END}"
        value = input(display_prompt).strip()
        Colors.clear_screen()
        return value if value else default

    @staticmethod
    def get_yes_no_input(prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user"""
        default_text = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} ({default_text}): ").strip().lower()
            if not response:
                Colors.clear_screen()
                return default
            if response in ['y', 'yes']:
                Colors.clear_screen()
                return True
            if response in ['n', 'no']:
                Colors.clear_screen()
                return False
            print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.END}")

    @staticmethod
    def display_section_header(title: str, color: str = Colors.PURPLE):
        """Display a section header"""
        print(f"\n{color}{'=' * 60}{Colors.END}")
        print(f"{color}{Colors.BOLD}{title}{Colors.END}")
        print(f"{color}{'=' * 60}{Colors.END}")

    def collect_basic_configuration(self) -> Dict[str, Any]:
        """Collect basic bot configuration"""
        self.display_section_header("🤖 BASIC BOT CONFIGURATION")
        
        config = {}
        
        # Required fields
        for i, (field, field_config) in enumerate(self.REQUIRED_FIELDS.items()):
            if i > 0:
                self.display_section_header("🤖 BASIC BOT CONFIGURATION")
                print(f"\n{Colors.WHITE}{'┄' * 40}{Colors.END}")
            
            print(f"\n{Colors.BOLD}{Colors.YELLOW}📋 {field_config['prompt']}{Colors.END}")
            config[field] = self.get_required_input(field_config['prompt'], field_config)
        
        # Optional fields
        for field, field_config in self.OPTIONAL_FIELDS.items():
            self.display_section_header("🤖 BASIC BOT CONFIGURATION")
            print(f"\n{Colors.WHITE}{'┄' * 40}{Colors.END}")
            print(f"\n{Colors.BOLD}{Colors.YELLOW}📋 {field_config['prompt']}{Colors.END}")
            config[field] = self.get_optional_input(field_config['prompt'], field_config['default'], field_config)
        
        print(f"\n{Colors.GREEN}✅ Basic configuration completed!{Colors.END}")
        return config

    def collect_service_configuration(self, service_name: str) -> Dict[str, Any]:
        """Collect configuration for a specific service"""
        config = {}
        service_config = self.SERVICE_CONFIGS[service_name]
        
        # Service-specific icons and titles
        service_icons = {
            'vocard-db': '🗄️',
            'lavalink': '🎵',
            'vocard-dashboard': '🌐'
        }
        icon = service_icons.get(service_name, '⚙️')
        service_title = f"{icon} {service_name.replace('-', ' ').title().upper()} CONFIGURATION"
        
        self.display_section_header(service_title, Colors.CYAN)
        
        for i, (field, field_config) in enumerate(service_config.items()):
            if i > 0:
                self.display_section_header(service_title, Colors.CYAN)
                print(f"\n{Colors.WHITE}{'┄' * 40}{Colors.END}")
            
            print(f"\n{Colors.BOLD}{Colors.YELLOW}📋 {field_config['prompt']}{Colors.END}")
            
            while True:
                if field_config['default'] is None:
                    value = self.get_required_input(field_config['prompt'], field_config)
                else:
                    value = self.get_optional_input(field_config['prompt'], str(field_config['default']), field_config)
                
                # If empty value is provided for optional field, use default
                if not value and field_config['default'] is not None:
                    value = str(field_config['default'])
                    break
                
                # Skip empty optional fields (like Spotify credentials)
                if not value and field_config['default'] is None:
                    config[field] = ""
                    break
                
                # Convert value to the appropriate type
                try:
                    if field_config['type'] == int:
                        config[field] = int(value)
                    else:
                        config[field] = value
                    break  # Exit the loop if conversion succeeds
                except ValueError:
                    print(f"{Colors.RED}Invalid number format for {field_config['prompt']}. Please enter a valid number.{Colors.END}")
                    continue  # Ask for input again
        
        print(f"\n{Colors.GREEN}✅ {service_name.replace('-', ' ').title()} configuration completed!{Colors.END}")
        return config

    def collect_installation_directory(self, default_dir: Path) -> Path:
        """Collect installation directory from user"""
        self.display_section_header("📁 INSTALLATION DIRECTORY")
        
        dir_config = {
            'prompt': 'Installation directory',
            'default': str(default_dir),
            'description': f'''Directory where Vocard will be installed.

This directory will contain:
- docker-compose.yml (main configuration)
- settings.json (bot settings)
- lavalink/ (audio server config)
- dashboard/ (web dashboard config)

The installer will create this directory if it doesn't exist.''',
            'help_url': None
        }
        
        print(f"\n{Colors.BOLD}{Colors.YELLOW}📋 {dir_config['prompt']}{Colors.END}")
        install_dir = self.get_optional_input(
            dir_config['prompt'],
            str(default_dir),
            dir_config
        )
        
        print(f"\n{Colors.GREEN}✅ Installation directory set!{Colors.END}")
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
            with open(file_path, 'r', encoding="utf-8") as f:
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
                    # Add volume for persistent data with proper permissions
                    service["volumes"] = ["./mongodb_data:/data/db"]
                
                if service_name == "vocard-dashboard":
                    dashboard_config = config['service_configs']['vocard-dashboard']
                    service["ports"] = [f"{dashboard_config['port']}:{dashboard_config['port']}"]

            with open(file_path, 'w', encoding="utf-8") as f:
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
            with open(file_path, 'r', encoding="utf-8") as f:
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
                    settings['ipc_client']['host'] = "vocard-dashboard"
                    settings['ipc_client']['port'] = int(dashboard_config['port'])
                    settings['ipc_client']['password'] = dashboard_config['password']
                    settings['ipc_client']['enable'] = True

            with open(file_path, 'w', encoding="utf-8") as f:
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
            
            with open(file_path, 'r', encoding="utf-8") as f:
                settings = yaml.safe_load(f)

            # Update server settings
            settings['server']['port'] = int(lavalink_config['port'])
            settings['server']['password'] = lavalink_config['password']

            # Update Spotify settings
            spotify_settings = settings.get('plugins', {}).get('lavasrc', {}).get('spotify', {})
            spotify_settings['clientId'] = lavalink_config['client_id']
            spotify_settings['clientSecret'] = lavalink_config['client_secret']
            spotify_settings['preferAnonymousToken'] = False

            with open(file_path, 'w', encoding="utf-8") as f:
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
            
            with open(file_path, 'r', encoding="utf-8") as f:
                settings = json.load(f)

            settings.update({
                "host": dashboard_config['host'],
                "port": int(dashboard_config['port']),
                "password": dashboard_config['password'],
                "client_id": config['client_id'],
                "client_secret_id": dashboard_config['client_secret_id'],
                "redirect_url": dashboard_config['redirect_url'],
                "secret_key": dashboard_config['secret_key']
            })

            with open(file_path, 'w', encoding="utf-8") as f:
                json.dump(settings, f, indent=4)

            print(f"{Colors.GREEN}Updated dashboard settings{Colors.END}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Failed to update dashboard settings: {e}{Colors.END}")
            return False


class PermissionManager:
    """Handles file and directory permissions for Docker containers"""
    
    @staticmethod
    def check_docker_permissions() -> Tuple[bool, str]:
        """Check if current user can run Docker commands"""
        try:
            result = subprocess.run(
                "docker ps", shell=True, capture_output=True, 
                text=True, timeout=10
            )
            if result.returncode == 0:
                return True, "Docker permissions OK"
            else:
                error_msg = result.stderr.lower()
                if "permission denied" in error_msg or "dial unix" in error_msg:
                    return False, "Docker permission denied. User needs to be in docker group or use sudo."
                return False, f"Docker error: {result.stderr}"
        except Exception as e:
            return False, f"Docker check failed: {e}"
    
    @staticmethod
    def fix_directory_permissions(directory: Path, recursive: bool = True) -> bool:
        """Fix directory permissions for Docker container access"""
        try:
            # Set directory permissions to 777 (rwxr-xr-x)
            os.chmod(directory, 0o777)
            
            if recursive and directory.is_dir():
                for item in directory.rglob("*"):
                    if item.is_dir():
                        os.chmod(item, 0o777)  # Directories: 777
                    else:
                        os.chmod(item, 0o644)  # Files: 644
            
            return True
        except PermissionError:
            return False
        except Exception:
            return False
    
    @staticmethod
    def create_docker_directories(install_dir: Path, enabled_services: set) -> bool:
        """Create and set proper permissions for Docker directories"""
        directories_to_create = []
        
        # Lavalink directories
        if 'lavalink' in enabled_services:
            directories_to_create.extend([
                install_dir / "lavalink" / "plugins",
                install_dir / "lavalink" / "logs"
            ])
        
        # Dashboard directories
        if 'vocard-dashboard' in enabled_services:
            directories_to_create.append(install_dir / "dashboard")
        
        # Database directories (for persistent data)
        if 'vocard-db' in enabled_services:
            directories_to_create.append(install_dir / "mongodb_data")
        
        success = True
        for directory in directories_to_create:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                
                # Set permissions for Docker container access
                if not PermissionManager.fix_directory_permissions(directory):
                    print(f"{Colors.YELLOW}Warning: Could not set optimal permissions for {directory}{Colors.END}")
                    print(f"{Colors.YELLOW}You may need to run: sudo chmod -R 777 {directory}{Colors.END}")
                else:
                    print(f"{Colors.GREEN}Created and set permissions for: {directory}{Colors.END}")
                    
            except Exception as e:
                print(f"{Colors.RED}Failed to create directory {directory}: {e}{Colors.END}")
                success = False
        
        return success
    
    @staticmethod
    def check_write_permissions(install_dir: Path) -> bool:
        """Check if we have write permissions in the installation directory"""
        test_file = install_dir / ".permission_test"
        try:
            # Try to create a test file
            with open(test_file, 'w', encoding="utf-8") as f:
                f.write("test")
            
            # Try to delete it
            test_file.unlink()
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def suggest_permission_fixes(install_dir: Path) -> None:
        """Suggest permission fixes based on the system"""
        system = platform.system().lower()
        
        print(f"\n{Colors.YELLOW}{'=' * 60}{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  PERMISSION ISSUES DETECTED{Colors.END}")
        print(f"{Colors.YELLOW}{'=' * 60}{Colors.END}")
        
        print(f"\n{Colors.WHITE}To fix permission issues, try one of these solutions:{Colors.END}")
        
        if system == "linux":
            print(f"\n{Colors.CYAN}Option 1 - Add user to docker group (recommended):{Colors.END}")
            print(f"  sudo usermod -aG docker $USER")
            print(f"  newgrp docker  # Or logout/login")
            
            print(f"\n{Colors.CYAN}Option 2 - Fix directory permissions:{Colors.END}")
            print(f"  sudo chown -R $USER:$USER {install_dir}")
            print(f"  sudo chmod -R 777 {install_dir}")
            
            print(f"\n{Colors.CYAN}Option 3 - Run installer with sudo:{Colors.END}")
            print(f"  sudo python3 {sys.argv[0]}")
            
        elif system == "darwin":  # macOS
            print(f"\n{Colors.CYAN}Option 1 - Fix directory permissions:{Colors.END}")
            print(f"  sudo chown -R $(whoami):staff {install_dir}")
            print(f"  chmod -R 777 {install_dir}")
            
            print(f"\n{Colors.CYAN}Option 2 - Run installer with sudo:{Colors.END}")
            print(f"  sudo python3 {sys.argv[0]}")
        
        print(f"\n{Colors.WHITE}After fixing permissions, run the installer again.{Colors.END}")


class DockerManager:
    """Handles Docker operations"""

    @staticmethod
    def run_command(command: str, timeout: int = 1800) -> Tuple[bool, str, str]:
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
        self.permission_manager = PermissionManager()

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
        self.config_manager.display_section_header("🔧 OPTIONAL SERVICES CONFIGURATION", Colors.CYAN)
        print(f"{Colors.WHITE}Vocard supports several optional services that enhance functionality:{Colors.END}")
        
        service_descriptions = {
            'lavalink': '🎵 Lavalink - High-quality audio streaming server (Recommended)',
            'vocard-db': '🗄️ MongoDB - Database for user data and playlists (Recommended)', 
            'vocard-dashboard': '🌐 Web Dashboard - Web interface for bot management',
            'spotify-tokener': '🎧 Spotify Token Service - Enhanced Spotify integration'
        }
        
        config['service_configs'] = {}
        enabled_services = set()
        
        for i, service in enumerate(self.OPTIONAL_SERVICES):
            if i > 0:
                self.config_manager.display_section_header("🔧 OPTIONAL SERVICES CONFIGURATION", Colors.CYAN)
                print(f"{Colors.WHITE}Vocard supports several optional services that enhance functionality:{Colors.END}")
                print(f"\n{Colors.WHITE}{'┄' * 40}{Colors.END}")
            
            description = service_descriptions.get(service, f"⚙️ {service}")
            print(f"\n{Colors.BLUE}{description}{Colors.END}")
            
            if self.config_manager.get_yes_no_input(f"{Colors.YELLOW}Enable {service}?{Colors.END}"):
                enabled_services.add(service)
                if service in self.config_manager.SERVICE_CONFIGS:
                    config['service_configs'][service] = (
                        self.config_manager.collect_service_configuration(service)
                    )
        
        config['enabled_services'] = enabled_services
        
        print(f"\n{Colors.GREEN}✅ Service selection completed!{Colors.END}")
        print(f"{Colors.WHITE}Enabled services: {', '.join(enabled_services) if enabled_services else 'None'}{Colors.END}")
        
        return config

    def setup_configuration_files(self, config: Dict[str, Any]) -> bool:
        """Download and configure all files"""
        install_dir = config['install_dir']
        enabled_services = config['enabled_services']
        
        # Download files
        if not self.file_manager.download_config_files(install_dir, enabled_services):
            return False
        
        # Create Docker directories with proper permissions
        print(f"\n{Colors.CYAN}Setting up Docker directories and permissions...{Colors.END}")
        if not self.permission_manager.create_docker_directories(install_dir, enabled_services):
            print(f"{Colors.YELLOW}Warning: Some directories could not be created with optimal permissions{Colors.END}")
        
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
        
        # Final permission check and fix for all created files
        print(f"{Colors.CYAN}Fixing file permissions...{Colors.END}")
        if not self.permission_manager.fix_directory_permissions(install_dir):
            print(f"{Colors.YELLOW}Warning: Could not fix all file permissions. You may need to run:{Colors.END}")
            print(f"{Colors.YELLOW}  sudo chmod -R 777 {install_dir}{Colors.END}")
        else:
            print(f"{Colors.GREEN}File permissions set successfully{Colors.END}")
        
        return True

    def print_success_message(self, config: Dict[str, Any]):
        """Print installation success message"""
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}{Colors.GREEN}VOCARD INSTALLATION COMPLETED!{Colors.END}")
        print(f"{Colors.GREEN}You can invite your bot using the following link:\nhttps://discord.com/oauth2/authorize?client_id={config['client_id']}&permissions=8&scope=bot+applications.commands{Colors.END}")
        
        if 'vocard-dashboard' in config['enabled_services']:
            dashboard_port = config['service_configs']['vocard-dashboard']['port']
            print(f"{Colors.GREEN}Access the dashboard at: http://localhost:{dashboard_port}{Colors.END}")
            
        print("=" * 60)
        print(f"{Colors.BLUE}Installation directory: {config['install_dir']}{Colors.END}")
        print(f"\n{Colors.CYAN}Management Commands:{Colors.END}")
        print(f"  cd {config['install_dir']}")
        print("  docker compose up -d    # Start services")
        print("  docker compose down     # Stop services")
        print("  docker compose logs -f  # View logs")
        print("  docker compose pull     # Update images")
        
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  If containers can't write to directories:")
        print(f"    sudo chmod -R 777 {config['install_dir']}")
        print(f"    sudo chown -R $USER:$USER {config['install_dir']}")
        print("  If Docker permission errors occur:")
        print("    sudo usermod -aG docker $USER && newgrp docker")
        
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
            
            # Check Docker permissions
            docker_perms_ok, docker_msg = self.permission_manager.check_docker_permissions()
            if not docker_perms_ok:
                print(f"{Colors.RED}Docker permission issue: {docker_msg}{Colors.END}")
                self.permission_manager.suggest_permission_fixes(Path.cwd())
                return False
            
            print(f"{Colors.GREEN}Docker permissions are OK{Colors.END}")
            
            # Collect configuration
            config = self.collect_configuration()
            
            # Check installation directory permissions
            install_dir = config['install_dir']
            if not self.permission_manager.check_write_permissions(install_dir):
                print(f"{Colors.RED}No write permissions in installation directory: {install_dir}{Colors.END}")
                self.permission_manager.suggest_permission_fixes(install_dir)
                return False
            
            print(f"{Colors.GREEN}Installation directory permissions are OK{Colors.END}")
            
            # Setup configuration files
            if not self.setup_configuration_files(config):
                return False
            
            # Start services
            if not self.docker_manager.start_services(config['install_dir']):
                return False
            
            # Print success message
            self.print_success_message(config)
            
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