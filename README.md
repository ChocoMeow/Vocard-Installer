# Vocard-Installer

A Python-based installer for setting up Vocard with Docker and Lavalink integration.

## Project Structure

- `installer.py` - Main installation script
- `docker-compose.yml` - Docker configuration file
- `lavalink/` - Lavalink server configuration
  - `application.yml` - Lavalink configuration file
- `requirements.txt` - Python dependencies

## Prerequisites

- Python 3.x
- Docker and Docker Compose
- Internet connection for downloading dependencies

## Installation

### For Windows Users
1. Create a new directory for Vocard
2. Open Command Prompt (CMD) as Administrator
3. Navigate to your created directory using the `cd` command
4. Download the installer by running this command:
   ```
   curl -o installer.bat https://raw.githubusercontent.com/ChocoMeow/Vocard-Installer/main/installer.bat
   ```
5. Run the downloaded installer:
   ```
   installer.bat
   ```

### For Other Operating Systems
1. Clone this repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the installer:
   ```
   python installer.py
   ```

## License

This project is licensed under the terms included in the `LICENSE` file.

## Contributing

Feel free to open issues or submit pull requests if you find any problems or have suggestions for improvements.