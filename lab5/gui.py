"""
Networks and Network Security
Lab 5 - Distributed Sensor Network
GUI

DO NOT MODIFY THIS FILE!
"""
import tkinter as tk
import tkinter.scrolledtext as tkst

import sys
import os
import queue
import threading



class FloatEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        validate_cmd = (self.register(self.validate), '%P')
        self.config(validate="all", validatecommand=validate_cmd)

    def validate(self, text):
        try:
            float(text)
            return True
        except ValueError:
            self.text = str(self.get())
            return False


class LinkedIntVar(tk.IntVar):
    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
        self.trace("w", self.callback)

    def callback(self, *args):
        try:
            self.value = self.get()
            try:
                self.linked()
            except AttributeError:
                pass
        except (ValueError, tk.TclError):
            self.set(self.value)


class LinkedDoubleVar(tk.DoubleVar):
    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
        self.trace("w", self.callback)

    def callback(self, *args):
        try:
            self.value = self.get()
            try:
                self.linked()
            except AttributeError:
                pass
        except (ValueError, tk.TclError):
            self.set(self.value)


class MainWindow:
    def __init__(self, master=None, client=None):
        master = master or tk.Tk()
        self._master = master

        # Create queue for communication between GUI and client thread
        self.write_queue = queue.Queue()
        self.write_event = '<<message>>'
        self._master.bind(self.write_event, self._process_write)

        self._master.protocol("WM_DELETE_WINDOW", self._on_close_window)

        self.quit_event = threading.Event()

        self.wake_thread, self.write_wake_thread = os.pipe()
        self.wake_thread = os.fdopen(self.wake_thread, 'r')
        self.write_wake_thread = os.fdopen(self.write_wake_thread, 'w')

        # Set initial state
        self._line = ""
        self._client = client
        self._master.title("Sensor Client")

        # Make frame
        main_frame = tk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Make message log frame
        console_frame = tk.Frame(main_frame)
        console_frame.pack(fill=tk.BOTH, expand=True)

        # Make message log
        self._txtlog = tkst.ScrolledText(console_frame,
                                         height=10,
                                         wrap=tk.WORD,
                                         borderwidth=2,
                                         relief=tk.FLAT,
                                         highlightthickness=0)
        self._txtlog.pack(fill=tk.BOTH, expand=True)

        # Make properties frame
        properties_frame = tk.Frame(master, height=10)
        properties_frame.pack(side=tk.TOP, expand=False, fill=tk.X, padx=10, pady=5)
        
        tk.Label(properties_frame, text="Strength:").pack(side=tk.LEFT)
        self._strength = LinkedIntVar()
        self._strength_field = tk.Spinbox(properties_frame, from_=0, to=1000, width=3, textvariable=self._strength)
        self._strength_field.pack(side=tk.LEFT)

        tk.Label(properties_frame, text="Position: (").pack(side=tk.LEFT, padx=(15, 0))
        self._x = LinkedIntVar()
        self._x_field = tk.Spinbox(properties_frame, from_=0, to=1000, width=3, textvariable=self._x)
        self._x_field.pack(side=tk.LEFT, expand=False)
        tk.Label(properties_frame, text=",").pack(side=tk.LEFT)
        self._y = LinkedIntVar()
        self._y_field = tk.Spinbox(properties_frame, from_=0, to=1000, width=3, textvariable=self._y)
        self._y_field.pack(side=tk.LEFT, expand=False)
        tk.Label(properties_frame, text=")").pack(side=tk.LEFT)

        tk.Label(properties_frame, text="Value:").pack(side=tk.LEFT)
        self._value = LinkedDoubleVar()
        self._value_field = tk.Entry(properties_frame, width=5, textvariable=self._value)
        self._value_field.pack(side=tk.LEFT)

        tk.Label(properties_frame, text="Ping period:").pack(side=tk.LEFT)
        self._period = LinkedIntVar()
        self._period_field = tk.Spinbox(properties_frame, from_=0, to=1000, width=3, textvariable=self._period)
        self._period_field.pack(side=tk.LEFT)


        # Make compose frame
        compose_frame = tk.Frame(master, height=10)
        compose_frame.pack(side=tk.BOTTOM, expand=False, fill=tk.X,
                           padx=10, pady=10)

        # Make compose field
        self._compose_field = tk.Entry(compose_frame)
        self._compose_field.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self._compose_field.bind('<Return>', self.submit)

        # Make buttons
        self._clearbutton = tk.Button(compose_frame, text="Clear", fg="red",
                                      command=self.clear)
        self._clearbutton.pack(side=tk.LEFT)
        self._sendbutton = tk.Button(compose_frame, text="Submit",
                                     command=self.submit)
        self._sendbutton.pack(side=tk.LEFT)

        # Set appropriate minimum and initial window size
        master.update()
        master.minsize(master.winfo_width(), master.winfo_height())
        master.geometry("500x350")

    def start(self):
        self._master.lift()
        self._master.mainloop()
        self._master.destroy()

    def submit(self, event=None):
        """
        Submits the prompt text and clears the prompt.
        """
        self._line = self._compose_field.get()
        self._compose_field.delete(0, tk.END)
        if self._client is not None:
            self._client.text_entered(self._line)

    def write(self, text):
        """
        Writes a string to the text box.
        """
        self.write_queue.put(text)
        self._master.event_generate(self.write_event, when='tail')

    def _process_write(self, event):
        while not self.write_queue.empty():
            self._txtlog.config(state='normal')
            self._txtlog.insert(tk.END, self.write_queue.get())
            self._txtlog.yview(tk.END)
            self._txtlog.config(state='disabled')

    def writeln(self, text):
        """
        Writes a string to the text box followed by a newline.
        """
        self.write('%s\n' % text)

    def clear(self):
        """
        Clears the text box.
        """
        self._txtlog.config(state='normal')
        self._txtlog.delete(0.0, tk.END)
        self._txtlog.config(state='disabled')

    @property
    def line(self):
        """
        Get the prompt text.
        Returns an empty string if the prompt is empty.
        """
        line, self._line = self._line, ''
        return line

    def set_client(self, client):
        self._client = client

    def _on_close_window(self):
        self.quit_event.set()
        self.write_wake_thread.write(' ')
        self.write_wake_thread.flush()
        sys.exit()

# For testing only
if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)

    root.mainloop()
    root.destroy()
