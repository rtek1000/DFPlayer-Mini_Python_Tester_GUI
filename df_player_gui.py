import serial
import serial.tools.list_ports
import threading
import tkinter as tk
import time
from tkinter import scrolledtext, messagebox

# --- CONFIGURATION ---
BAUD = 9600
# Expanded dictionary of DFPlayer responses
RESPONSES = {
    "3F": "SD Card Online", "3D": "Playback Finished", "40": "Module Error",
    "41": "Command OK (ACK)", "3A": "SD Card Removed", "3B": "SD Card Inserted",
    "4C": "Current Playing ID", "43": "Current Volume", "48": "Total Files on SD"
}

class DFPlayerApp:
    def __init__(self, root):
        self.root = root
        self.ser = None
        self.is_connected = False
        self.previous_volume = 20
        self.is_muted = False
        self.eq_modes = ["Normal", "Pop", "Rock", "Jazz", "Classic", "Bass"]
        
        self.setup_ui()
        
        # Start reception monitor and auto-query threads
        threading.Thread(target=self.read_serial, daemon=True).start()
        self.schedule_query()

    # --- CONNECTION LOGIC ---
    def list_ports(self):
        """Lists available USB/ACM serial ports"""
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports if "USB" in p.device.upper() or "ACM" in p.device.upper()]

    def refresh_ports(self):
        """Updates the port selection menu"""
        ports = self.list_ports()
        menu = self.om_ports['menu']
        menu.delete(0, 'end')
        for p in ports:
            menu.add_command(label=p, command=lambda port=p: self.var_port.set(port))
        if ports and not self.var_port.get():
            self.var_port.set(ports[0])

    def connect(self):
        """Attempts to connect to the selected serial port"""
        port = self.var_port.get()
        if not port: return
        try:
            if self.ser: self.ser.close()
            self.ser = serial.Serial(port, BAUD, timeout=0.1)
            self.is_connected = True
            self.log(f"Connected to: {port}", "green")
            self.lbl_status.config(text=f"Status: ON ({port})", fg="green")
        except Exception as e:
            self.log(f"Connection Error: {e}", "red")
            self.is_connected = False

    def send_command(self, command, p_high=0x00, p_low=0x00, feedback=0x00):
        """Sends a standard data packet to the DFPlayer"""
        if self.is_connected:
            try:
                # Structure: Start, Ver, Len, Cmd, Feedback, High, Low, End
                packet = bytearray([0x7E, 0xFF, 0x06, command, feedback, p_high, p_low, 0xEF])
                self.ser.write(packet)
                self.log(f"TX: {packet.hex().upper()}", "blue")
            except:
                self.is_connected = False
                self.lbl_status.config(text="Status: OFF (Send Error)", fg="red")
        else:
            self.log("Error: Not connected!", "red")

    def read_serial(self):
        """Monitors incoming data from DFPlayer TX"""
        while True:
            if self.is_connected:
                try:
                    if self.ser.in_waiting >= 10:
                        data = self.ser.read(10)
                        hex_list = [f"{b:02X}" for b in data]
                        cmd_resp = hex_list[3]
                        value = int(hex_list[6], 16)
                        translation = RESPONSES.get(cmd_resp, "Unknown")
                        self.log(f"RX: {translation} (Val: {value})", "red")
                        if cmd_resp == "4C":
                            self.root.title(f"DFPlayer - Playing ID: {value}")
                except:
                    self.is_connected = False
            time.sleep(0.05)

    def schedule_query(self):
        """Periodically requests current playing track"""
        if self.is_connected:
            self.send_command(0x4C, 0x00, 0x00, feedback=0x01)
        self.root.after(5000, self.schedule_query)

    # --- INTERFACE LOGIC ---
    def toggle_mute(self):
        """Mutes sound while remembering current volume"""
        if not self.is_muted:
            self.previous_volume = self.scale_vol.get()
            self.send_command(0x06, 0x00, 0)
            self.btn_mute.configure(text="UNMUTE", bg="yellow")
            self.is_muted = True
        else:
            self.send_command(0x06, 0x00, self.previous_volume)
            self.btn_mute.configure(text="MUTE", bg="lightgray")
            self.is_muted = False

    def log(self, message, color="black"):
        """Displays messages in the log area"""
        self.txt_log.configure(state='normal')
        self.txt_log.insert(tk.END, message + "\n", color)
        self.txt_log.configure(state='disabled')
        self.txt_log.see(tk.END)

    def setup_ui(self):
        """Builds the English Graphical User Interface"""
        self.root.title("DFPlayer English Controller v11")
        self.root.geometry("600x750")

        # --- CONNECTION PANEL ---
        f_con = tk.LabelFrame(self.root, text="Serial Connection")
        f_con.pack(fill="x", padx=10, pady=5)
        self.var_port = tk.StringVar()
        self.om_ports = tk.OptionMenu(f_con, self.var_port, "")
        self.om_ports.pack(side="left", padx=10, pady=5, expand=True, fill="x")
        tk.Button(f_con, text="↻", command=self.refresh_ports).pack(side="left", padx=5)
        tk.Button(f_con, text="Connect", bg="lightblue", command=self.connect).pack(side="left", padx=5)
        self.lbl_status = tk.Label(self.root, text="Status: OFF", fg="red", font=("Arial", 10, "bold"))
        self.lbl_status.pack()

        # LOGGING AREA
        self.txt_log = scrolledtext.ScrolledText(self.root, height=7, state='disabled')
        self.txt_log.pack(fill="both", padx=10, pady=5)
        self.txt_log.tag_config("blue", foreground="blue")
        self.txt_log.tag_config("red", foreground="red")
        self.txt_log.tag_config("green", foreground="darkgreen")

        # --- MEDIA SOURCES ---
        f_source = tk.LabelFrame(self.root, text="Media Source (0x09)")
        f_source.pack(fill="x", padx=10, pady=5)
        tk.Button(f_source, text="U-Disk (USB)", width=15, command=lambda: self.send_command(0x09, 0, 1)).grid(row=0, column=0, padx=20, pady=5)
        tk.Button(f_source, text="SD Card", width=15, command=lambda: self.send_command(0x09, 0, 2)).grid(row=0, column=1, padx=20, pady=5)

        # --- PLAYBACK MODES ---
        f_modes = tk.LabelFrame(self.root, text="Playback Modes (0x11, 0x18, 0x19)")
        f_modes.pack(fill="x", padx=10, pady=5)
        tk.Button(f_modes, text="LOOP ALL ON", bg="cyan", width=12, command=lambda: self.send_command(0x11, 0, 1)).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(f_modes, text="LOOP OFF", width=12, command=lambda: self.send_command(0x11, 0, 0)).grid(row=0, column=1, padx=5)
        tk.Button(f_modes, text="SHUFFLE", bg="plum", width=12, command=lambda: self.send_command(0x18)).grid(row=0, column=2, padx=5)
        tk.Button(f_modes, text="SINGLE LOOP", bg="yellow", width=12, command=lambda: self.send_command(0x19, 0, 0)).grid(row=0, column=3, padx=5)

        # --- FOLDER CONTROL ---
        f_folders = tk.LabelFrame(self.root, text="Specific Folder Controls")
        f_folders.pack(fill="x", padx=10, pady=5)
        tk.Label(f_folders, text="Folder (01-99):").grid(row=0, column=0)
        self.e_p = tk.Entry(f_folders, width=4); self.e_p.insert(0,"1"); self.e_p.grid(row=0, column=1)
        tk.Label(f_folders, text="Track:").grid(row=0, column=2)
        self.e_m = tk.Entry(f_folders, width=4); self.e_m.insert(0,"1"); self.e_m.grid(row=0, column=3)
        tk.Button(f_folders, text="Play Folder", command=lambda: self.send_command(0x0F, int(self.e_p.get()), int(self.e_m.get()))).grid(row=0, column=4, padx=5)
        
        tk.Label(f_folders, text="MP3 Track:").grid(row=1, column=0)
        self.e_mp3 = tk.Entry(f_folders, width=4); self.e_mp3.insert(0,"1"); self.e_mp3.grid(row=1, column=1)
        tk.Button(f_folders, text="Play MP3", fg="purple", command=lambda: self.send_command(0x12, 0, int(self.e_mp3.get()))).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(f_folders, text="Advert Track:").grid(row=1, column=3)
        self.e_adv = tk.Entry(f_folders, width=4); self.e_adv.insert(0,"1"); self.e_adv.grid(row=1, column=4)
        tk.Button(f_folders, text="ADVERT", fg="orange", command=lambda: self.send_command(0x13, 0, int(self.e_adv.get()))).grid(row=1, column=5, padx=5)

        # --- EQUALIZER ---
        f_eq = tk.LabelFrame(self.root, text="Equalizer")
        f_eq.pack(fill="x", padx=10, pady=5)
        for i, m in enumerate(self.eq_modes):
            tk.Button(f_eq, text=m, width=8, command=lambda idx=i: self.send_command(0x07, 0, idx)).grid(row=0, column=i, padx=2, pady=5)

        # --- VOLUME & MUTE ---
        f_v = tk.Frame(self.root)
        f_v.pack(fill="x", padx=10, pady=10)
        self.scale_vol = tk.Scale(f_v, from_=0, to=30, orient="horizontal", label="Volume", command=lambda v: self.send_command(0x06, 0, int(v)))
        self.scale_vol.set(20); self.scale_vol.pack(side="left", expand=True, fill="x")
        self.btn_mute = tk.Button(f_v, text="MUTE", width=8, command=self.toggle_mute)
        self.btn_mute.pack(side="right", padx=5)

        # --- PLAYBACK CONTROLS ---
        f_b = tk.Frame(self.root)
        f_b.pack(pady=10)
        tk.Button(f_b, text="STOP", bg="salmon", width=10, command=lambda: self.send_command(0x16)).grid(row=0, column=0, padx=5)
        tk.Button(f_b, text="PAUSE", bg="orange", width=10, command=lambda: self.send_command(0x0E)).grid(row=0, column=1, padx=5)
        tk.Button(f_b, text="PLAY", bg="lightgreen", width=10, command=lambda: self.send_command(0x0D)).grid(row=0, column=2, padx=5)
        tk.Button(f_b, text="RESET", bg="red", fg="white", width=10, command=lambda: self.send_command(0x0C)).grid(row=0, column=3, padx=5)
        
        self.refresh_ports()

if __name__ == "__main__":
    root = tk.Tk()
    app = DFPlayerApp(root)
    root.mainloop()