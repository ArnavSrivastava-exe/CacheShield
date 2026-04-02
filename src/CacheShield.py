import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from test_api import test_api
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

def create_gui():
    window = tk.Tk()
    window.title("🛡️ CacheShield - API Cache Validator")
    window.state('zoomed')
    window.configure(bg="#1e1e1e")
    window.bind("<Escape>", lambda e: window.state('normal'))

    entry_style = {"bg": "#2b2b2b", "fg": "white", "font": ("Segoe UI", 11), "insertbackground": "white"}
    label_style = {"bg": "#1e1e1e", "fg": "white", "font": ("Segoe UI", 12, "bold")}
    button_style = {"bg": "#4caf50", "fg": "white", "font": ("Segoe UI", 11, "bold"), "padx": 10, "pady": 5}

    global alert_mode
    alert_mode = tk.BooleanVar(value=True)

    tk.Checkbutton(window, text="🔔 Alert Mode", variable=alert_mode,
                   bg="#1e1e1e", fg="white", selectcolor="#333333", font=("Segoe UI", 10)).pack(pady=5)

    tk.Label(window, text="Enter API URLs (one per line):", **label_style).pack(pady=5)
    global url_input_box
    url_input_box = scrolledtext.ScrolledText(window, width=100, height=5, **entry_style)
    url_input_box.pack(pady=5)

    tk.Label(window, text="Scan Results:", **label_style).pack()
    output_box = scrolledtext.ScrolledText(window, width=120, height=25,
                                           bg="#2e2e2e", fg="white", font=("Consolas", 10))
    output_box.pack(pady=10)

    tk.Label(window, text="Monitoring Interval (seconds):", bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack()
    interval_var = tk.IntVar(value=60)
    interval_entry = tk.Entry(window, textvariable=interval_var, width=5, **entry_style)
    interval_entry.pack(pady=5)

    response_times_log = []
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlabel('Test Number')
    ax.set_ylabel('Response Time (ms)')
    ax.set_title('Live API Response Times')
    line_plot, = ax.plot([], [], marker='o', linestyle='-', color='cyan')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    graph_window = None
    canvas = None
    monitoring = {"running": False}

    def update_graph():
        if not response_times_log:
            return
        times = [item[1] for item in response_times_log]
        x_vals = list(range(1, len(times)+1))
        line_plot.set_data(x_vals, times)
        ax.set_xlim(1, max(10, len(times)))
        ax.set_ylim(0, max(times) * 1.2)
        if canvas:
            canvas.draw_idle()

    def run_tests_continuous():
        while monitoring["running"]:
            urls = url_input_box.get("1.0", tk.END).strip().splitlines()
            if not urls or urls == ['']:
                output_box.insert("end", "⚠️ No URLs to monitor. Please enter API URLs.\n")
                break
            success, fail, total_time = 0, 0, 0
            output_box.insert("end", f"\n🔍 Starting test cycle for {len(urls)} API(s)...\n\n")
            for url in urls:
                if not monitoring["running"]:
                    break
                try:
                    status, response_time = test_api(url.strip(), output_box=output_box, alert=alert_mode.get())
                    if status:
                        success += 1
                        total_time += response_time
                        response_times_log.append((url.strip(), response_time))
                    else:
                        fail += 1
                    output_box.see("end")
                except Exception as e:
                    output_box.insert("end", f"❌ Error testing {url}: {str(e)}\n")
                    fail += 1
                    output_box.see("end")

            avg_time = total_time / success if success > 0 else 0
            output_box.insert("end", f"\n📊 Cycle Summary:\n✅ Success: {success}\n❌ Failed: {fail}\n⏱️ Avg Response Time: {avg_time:.2f} ms\n\n")
            output_box.see("end")
            window.after(0, update_graph)
            for _ in range(interval_var.get()):
                if not monitoring["running"]:
                    break
                time.sleep(1)

        output_box.insert("end", "🔴 Monitoring stopped.\n")
        output_box.see("end")

    monitor_thread = None

    def start_monitoring():
        nonlocal monitor_thread, graph_window, canvas
        if monitoring["running"]:
            messagebox.showinfo("Info", "Monitoring already running!")
            return
        urls = url_input_box.get("1.0", tk.END).strip().splitlines()
        if not urls or urls == ['']:
            messagebox.showwarning("Warning", "Please enter at least one API URL to monitor.")
            return
        monitoring["running"] = True
        response_times_log.clear()
        output_box.insert("end", "🟢 Monitoring started...\n")
        output_box.see("end")
        if graph_window is None or not tk.Toplevel.winfo_exists(graph_window):
            graph_window = tk.Toplevel(window)
            graph_window.title("📊 CacheShield - Live Response Time Graph")
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.get_tk_widget().pack()
            tk.Button(graph_window, text="Close", command=graph_window.destroy).pack(pady=5)
        monitor_thread = threading.Thread(target=run_tests_continuous, daemon=True)
        monitor_thread.start()

    def stop_monitoring():
        if not monitoring["running"]:
            messagebox.showinfo("Info", "Monitoring is not running.")
            return
        monitoring["running"] = False

    def on_test_click():
        if monitoring["running"]:
            messagebox.showwarning("Warning", "Stop monitoring before running manual test.")
            return
        urls = url_input_box.get("1.0", tk.END).strip().splitlines()
        success, fail, total_time = 0, 0, 0
        response_times_log.clear()
        output_box.insert("end", f"\n🔍 Testing {len(urls)} API(s)...\n\n")
        for url in urls:
            try:
                status, response_time = test_api(url.strip(), output_box=output_box, alert=alert_mode.get())
                if status:
                    success += 1
                    total_time += response_time
                    response_times_log.append((url.strip(), response_time))
                else:
                    fail += 1
                output_box.see("end")
            except Exception as e:
                output_box.insert("end", f"❌ Error testing {url}: {str(e)}\n")
                fail += 1
                output_box.see("end")
        avg_time = total_time / success if success > 0 else 0
        output_box.insert("end", f"\n📊 Summary:\n✅ Success: {success}\n❌ Failed: {fail}\n⏱️ Avg Response Time: {avg_time:.2f} ms\n\n")
        output_box.see("end")
        update_graph()

    def on_clear_click():
        if monitoring["running"]:
            messagebox.showwarning("Warning", "Stop monitoring before clearing output.")
            return
        output_box.delete("1.0", tk.END)
        response_times_log.clear()
        update_graph()

    def on_exit_click():
        if monitoring["running"]:
            messagebox.showwarning("Warning", "Stop monitoring before exiting.")
            return
        window.destroy()

    def export_api_list():
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Save API List As")
        if file_path:
            urls = url_input_box.get("1.0", tk.END).strip()
            try:
                with open(file_path, "w") as f:
                    f.write(urls)
                messagebox.showinfo("Success", "API list exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export API list:\n{str(e)}")

    def import_api_list():
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")],
                                               title="Select API List File")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                url_input_box.delete("1.0", tk.END)
                url_input_box.insert(tk.END, content)
                messagebox.showinfo("Success", "API list imported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import API list:\n{str(e)}")

    button_frame = tk.Frame(window, bg="#1e1e1e")
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Run Test", command=on_test_click, **button_style).grid(row=0, column=0, padx=10)
    tk.Button(button_frame, text="Start Monitoring", command=start_monitoring, **button_style).grid(row=0, column=1, padx=10)
    tk.Button(button_frame, text="Stop Monitoring", command=stop_monitoring, **button_style).grid(row=0, column=2, padx=10)
    tk.Button(button_frame, text="Clear Output", command=on_clear_click, **button_style).grid(row=0, column=3, padx=10)
    tk.Button(button_frame, text="Exit", command=on_exit_click, **button_style).grid(row=0, column=4, padx=10)
    tk.Button(button_frame, text="Export API List", command=export_api_list, **button_style).grid(row=0, column=5, padx=10)
    tk.Button(button_frame, text="Import API List", command=import_api_list, **button_style).grid(row=0, column=6, padx=10)


    # sonar trigger

    window.mainloop()

if __name__ == "__main__":
    create_gui()
