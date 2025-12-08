"""
Simple script to capture screenshots of the running GUI applications
"""
import time
import os
from PIL import ImageGrab

def main():
    os.makedirs("screenshots", exist_ok=True)
    
    print("Waiting for applications to fully load...")
    print("Please make sure the client app and admin dashboard windows are visible!")
    time.sleep(15)  # Wait for apps to fully load
    
    print("\nTaking screenshots...")
    
    # Take multiple screenshots to capture different states
    for i in range(3):
        print(f"Taking screenshot {i+1}/3...")
        screenshot = ImageGrab.grab()
        screenshot.save(f"screenshots/screenshot_{i+1}.png")
        print(f"[OK] Screenshot {i+1} saved")
        if i < 2:
            time.sleep(3)
    
    print("\n" + "="*50)
    print("Screenshots completed!")
    print("="*50)
    print("Check the 'screenshots' folder for the images:")
    print("  - screenshot_1.png")
    print("  - screenshot_2.png")
    print("  - screenshot_3.png")

if __name__ == "__main__":
    main()

