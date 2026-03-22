# DFPlayer Mini Python Tester GUI

This script is a DFPlayer Mini Serial Controller.
A Python-based Graphical User Interface (GUI) to control the DFPlayer Mini MP3 module via Serial (UART). This tool allows you to manage folders, volume, equalizers, and real-time status monitoring.

🛠 Features & Controls
1. Serial Connection
Port Selector (↻): Automatically scans your system for available USB/ACM serial ports.

Connect: Initializes the serial communication at 9600 baud.

2. Playback Controls
PLAY: Resumes playback or starts the current track from the beginning after a STOP.

PAUSE: Freezes the current track at its exact position.

STOP: Ends playback and resets the track pointer to the start.

RESET: Performs a hardware reset on the DFPlayer module.

3. Folder Management
Play Folder (0x0F): Plays a specific track from a numbered folder (01-99).

Play MP3 (0x12): Accesses the special MP3 folder. Supports up to 3000 files.

ADVERT (0x13): Plays an announcement from the ADVERT folder. Crucial feature: It pauses the current music, plays the advert, and then automatically resumes the music from where it left off.

4. Audio Customization
Equalizer: Quick buttons for 6 preset modes: Normal, Pop, Rock, Jazz, Classic, and Bass.

Volume Slider: Real-time volume control (0 to 30).

MUTE: Instantly silences the output. It has a "memory" feature that restores your previous volume level when unmuted.

5. Advanced Monitoring
Real-time Log: Displays Hexadecimal packets sent (TX) and received (RX).

Auto-Title Update: The window title automatically updates every 5 seconds to show the ID of the file currently playing (via Query 0x4C).

📂 SD Card Requirements
To use all features, organize your SD card as follows:

Folders named 01, 02, etc., containing files named 001.mp3, 002.mp3.

A folder named MP3 for general files.

A folder named ADVERT for interruptive announcements (files must be named 0001.mp3, 0002.mp3, etc.).

🚀 How to Run
Install dependencies: pip install pyserial

Connect your DFPlayer to your computer using a USB-to-Serial adapter.

Run the script: python df_player_gui_en.py
