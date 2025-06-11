import requests
import time
from tkinter import messagebox

def test_api(url, output_box=None, alert=False):
    """
    Tests a single API endpoint.
    
    Parameters:
    - url (str): The API URL to test.
    - output_box (tkinter.ScrolledText, optional): Output display widget.
    - alert (bool): If True, show alert popups for non-200 responses.

    Returns:
    - (bool, float): (status_ok, response_time_in_ms)
    """
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed_time = (time.time() - start_time) * 1000  # in ms

        # Format output
        status_line = f"🔗 {url}\n"
        code_line = f"  📦 Status Code: {response.status_code}\n"
        time_line = f"  ⏱️ Response Time: {elapsed_time:.2f} ms\n\n"

        # Print to GUI
        if output_box:
            output_box.insert("end", status_line)
            output_box.insert("end", code_line)
            output_box.insert("end", time_line)
            output_box.see("end")  # Scroll to latest

        # Optional alert
        if alert and response.status_code != 200:
            messagebox.showwarning("⚠️ API Alert", f"{url} returned {response.status_code}")

        return response.status_code == 200, elapsed_time

    except requests.exceptions.RequestException as e:
        if output_box:
            output_box.insert("end", f"❌ {url}\n  Error: {str(e)}\n\n")
            output_box.see("end")

        if alert:
            messagebox.showerror("❌ Request Failed", f"{url}\n{str(e)}")

        return False, 0
