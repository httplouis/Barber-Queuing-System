"""
Script to capture screenshots of the GUI applications
"""
import time
import os
from PIL import ImageGrab
import win32gui
import win32ui
import win32con

def capture_window_by_title(title_contains):
    """Capture a window by partial title match"""
    def enum_handler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_contains.lower() in window_title.lower():
                ctx.append((hwnd, window_title))
    
    windows = []
    win32gui.EnumWindows(enum_handler, windows)
    
    if not windows:
        return None
    
    # Get the first matching window
    hwnd, title = windows[0]
    
    # Get window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    # Bring window to front
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    
    # Capture window
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (width, height), dcObj, (0, 0), win32con.SRCCOPY)
    
    # Convert to PIL Image
    bmpinfo = dataBitMap.GetInfo()
    bmpstr = dataBitMap.GetBitmapBits(True)
    img = ImageGrab.Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )
    
    # Cleanup
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())
    
    return img

def capture_full_screen():
    """Capture full screen as fallback"""
    screenshot = ImageGrab.grab()
    return screenshot

def main():
    os.makedirs("screenshots", exist_ok=True)
    
    print("Waiting for applications to load...")
    time.sleep(10)  # Wait for apps to fully load
    
    print("Capturing screenshots...")
    
    # Try to capture client app window
    try:
        print("Looking for client app...")
        client_img = capture_window_by_title("client")
        if client_img:
            client_img.save("screenshots/client_app.png")
            print("✓ Client app screenshot saved")
        else:
            print("✗ Client app window not found, capturing full screen...")
            full_screen = capture_full_screen()
            full_screen.save("screenshots/client_app_fullscreen.png")
    except Exception as e:
        print(f"Error capturing client app: {e}")
        full_screen = capture_full_screen()
        full_screen.save("screenshots/client_app_fullscreen.png")
    
    time.sleep(2)
    
    # Try to capture admin dashboard window
    try:
        print("Looking for admin dashboard...")
        admin_img = capture_window_by_title("admin")
        if admin_img:
            admin_img.save("screenshots/admin_dashboard.png")
            print("✓ Admin dashboard screenshot saved")
        else:
            print("✗ Admin dashboard window not found, capturing full screen...")
            full_screen = capture_full_screen()
            full_screen.save("screenshots/admin_dashboard_fullscreen.png")
    except Exception as e:
        print(f"Error capturing admin dashboard: {e}")
        full_screen = capture_full_screen()
        full_screen.save("screenshots/admin_dashboard_fullscreen.png")
    
    # Also take a full screen capture
    print("Taking full screen capture...")
    full_screen = capture_full_screen()
    full_screen.save("screenshots/full_screen.png")
    print("✓ Full screen screenshot saved")
    
    print("\nScreenshots completed!")
    print("Check the 'screenshots' folder for the images.")

if __name__ == "__main__":
    try:
        import win32gui
        import win32ui
        import win32con
        main()
    except ImportError:
        print("pywin32 not installed. Using simple screenshot method...")
        time.sleep(10)
        os.makedirs("screenshots", exist_ok=True)
        screenshot = ImageGrab.grab()
        screenshot.save("screenshots/full_screen.png")
        print("Full screen screenshot saved to screenshots/full_screen.png")

