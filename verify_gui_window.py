import subprocess
import time
import ctypes
import ctypes.wintypes

script = r'd:\CARDIAC_ARRHYTHMIA_UPDATED\.venv\Scripts\python.exe'
args = [script, r'CARDIAC_ARRHYTHMIA_UPDATED\UI_Working.py']
proc = subprocess.Popen(args, cwd=r'd:\CARDIAC_ARRHYTHMIA_UPDATED')
try:
    time.sleep(20)
    titles = []
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.c_void_p)

    def cb(hwnd, lParam):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length and ctypes.windll.user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            titles.append(buf.value)
        return True

    ctypes.windll.user32.EnumWindows(CB(cb), 0)
    visible_titles = [t for t in titles if t]
    print('VISIBLE_TITLES_COUNT=', len(visible_titles))
    for title in visible_titles:
        print(title)
finally:
    proc.terminate()
    proc.wait(timeout=5)
