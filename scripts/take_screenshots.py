"""
Script to take screenshots of the running GUI applications
"""
import time
import subprocess
import os
from PIL import ImageGrab
import tkinter as tk

def take_screenshot(filename, delay=2):
    """Take a screenshot after a delay"""
    time.sleep(delay)
    screenshot = ImageGrab.grab()
    screenshot.save(filename)
    print(f"Screenshot saved: {filename}")

def main():
    # Create screenshots directory
    os.makedirs("screenshots", exist_ok=True)
    
    print("Taking screenshots of the running applications...")
    print("Make sure client_app.py and admin_dashboard.py are running!")
    
    # Take screenshots with delays
    take_screenshot("screenshots/client_app.png", delay=3)
    take_screenshot("screenshots/admin_dashboard.png", delay=3)
    
    print("\nScreenshots completed!")
    print("Check the 'screenshots' folder for the images.")

if __name__ == "__main__":
    main()

