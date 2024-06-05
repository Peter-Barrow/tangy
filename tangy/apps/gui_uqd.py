from typing import Union, Tuple, Callable, Optional
import datetime
from enum import Enum
import json
import threading
import time
from queue import Queue
import customtkinter as ctk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tangy import tangy_config_location, UQDLogic16


class FloatSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 height: int = 18,
                 step_size: Union[int, float] = 1,
                 step_size_big: Optional[Union[int, float]] = None,
                 value_range: Optional[Tuple[Union[int, float]]] = None,
                 units: Optional[str] = "",
                 command: Callable = None,
                 **kwargs):
        super().__init__(*args, height=height, **kwargs)

        self.units = units
        self.units_len = len(units)
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.value_range = value_range

        num_columns = 2
        weights = [1, 2, 1]
        entry_column = 1
        self.step_size = step_size
        self.step_size_small = 0
        if step_size_big is not None:
            num_columns += 2
            entry_column += 1
            self.step_size = step_size_big
            self.step_size_small = step_size
            weights = [1, 1, 2, 1, 1]

        if units != "":
            num_columns += 1
            weights = [1, 1, 2, 1, 1, 1]

        self.grid(column=0, row=0, sticky="nsew")
        self.rowconfigure(0, weight=1, uniform='b')
        for i, w in enumerate(weights):
            self.columnconfigure(i, weight=w, uniform='b')

        self.subtract_button = ctk.CTkButton(self,
                                             text="-",
                                             command=self.button_step_backward)
        self.subtract_button.grid(row=0, column=0, sticky="ns", padx=3, pady=3)

        self.entry = ctk.CTkEntry(self, border_width=0)
        self.entry.grid(row=0, column=entry_column,
                        padx=3, pady=3, sticky="ns")
        # default value
        if isinstance(value_range[0], (float)):
            self.entry.insert(0, "0.0")
        else:
            self.entry.insert(0, "0")

        if units != "":
            self.label = ctk.CTkLabel(self, text=self.units)
            self.label.grid(row=0, column=entry_column + 1, padx=1, pady=3,
                            sticky="ns")

        self.add_button = ctk.CTkButton(self,
                                        text="+",
                                        command=self.button_step_forward)
        self.add_button.grid(row=0, column=num_columns,
                             sticky="ns", padx=3, pady=3)

        if step_size_big is not None:
            self.subtract_button_small = ctk.CTkButton(self,
                                                       text="-",
                                                       command=self.button_step_backward_small)
            self.subtract_button_small.grid(
                row=0, column=1, padx=8, pady=8, sticky="ns")

            self.add_button_small = ctk.CTkButton(self,
                                                  text="+",
                                                  command=self.button_step_forward_small)
            self.add_button_small.grid(
                row=0, column=num_columns - 1, padx=8, pady=8, sticky="ns")

    def in_range(self, value, step: Union[int, float]) -> Union[int, float]:
        next_value = value + step
        if self.value_range is None:
            return next_value

        if next_value <= self.value_range[0]:
            return self.value_range[0]

        if next_value >= self.value_range[1]:
            return self.value_range[1]

        return next_value

    def button_callback(self, step):
        if self.command is not None:
            self.command()
        try:
            current_value = self.get()
            value = self.in_range(current_value, step)
            self.entry.delete(0, "end")
            if isinstance(self.value_range[0], (float)):
                self.entry.insert(0, f"{value:.2f}")
            else:
                self.entry.insert(0, f"{value}")
        except ValueError:
            return

    def button_step_backward(self):
        self.button_callback(-self.step_size)

    def button_step_backward_small(self):
        self.button_callback(-self.step_size_small)

    def button_step_forward(self):
        self.button_callback(self.step_size)

    def button_step_forward_small(self):
        self.button_callback(self.step_size_small)

    def get(self) -> Union[float, int, None]:
        try:
            if isinstance(self.value_range[0], (float)):
                return float(self.entry.get())
            return int(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float):
        self.entry.delete(1, "end")
        if isinstance(self.value_range[0], (float)):
            self.entry.insert(0, f"{value:.2f}")
            return
        self.entry.insert(0, f"{value}")
        return


class EdgeDetection(Enum):
    Rising = 0
    Falling = 1


class Channel(ctk.CTkFrame):
    def __init__(self, *args,
                 label: int,
                 voltage_range: Tuple[float, float],
                 edge_detection: EdgeDetection = EdgeDetection.Rising,
                 height: int = 18,
                 **kwargs):

        super().__init__(*args, height=height, **kwargs)

        self.configure(fg_color=("gray78", "gray28"))

        self.grid_columnconfigure((0, 1, 2), weight=0)
        self.grid_columnconfigure((3), weight=1)
        self.label = ctk.CTkLabel(self, text=f"{label}", height=height)
        self.label.grid(row=0, column=0, padx=(3, 6), pady=3, sticky="nsew")

        self.enabled = ctk.StringVar(value="on")
        self.enable_button = ctk.CTkCheckBox(self, text="Enabled",
                                             onvalue="on", offvalue="off",
                                             variable=self.enabled,
                                             command=self.enabled_callback)
        self.enable_button.grid(row=0, column=1, padx=(3, 0), pady=3, sticky="nsew")

        self.edge_detection = edge_detection
        self.edge_var = ctk.StringVar(value=edge_detection.name)
        self.edge_button = ctk.CTkSegmentedButton(self, values=["Rising", "Falling"],
                                                  variable=self.edge_var,
                                                  height=height)
        self.edge_button.grid(row=0, column=2, padx=(0, 0), pady=(6, 6),
                              sticky="nsew")

        self.threshold = FloatSpinbox(self, height=24, step_size=0.01,
                                      step_size_big=0.1, units="V",
                                      value_range=voltage_range)
        self.threshold.grid(row=0, column=3, pady=3, sticky="nsew")

    def get(self) -> Tuple[bool, float, EdgeDetection]:
        voltage = self.threshold.get()
        edge = EdgeDetection.Rising
        if self.edge_var.get() == "Falling":
            edge = EdgeDetection.Falling
        enabled = True
        if self.enabled.get() == "off":
            enabled = False
        return (enabled, voltage, edge)

    def enabled_channel(self, case: bool):
        if case is False:
            self.enabled.set("off")
            return
        self.enabled.set("on")
        return

    def enabled_callback(self):
        value = self.enabled.get()
        # if value == 1:
        #     print("here")
        #     self.enabled.set(0)
        #     # self.enable_button.value = 0
        # elif value == 0:
        #     print("there")
        #     self.enabled.set(1)
        #     #self.enable_button.value = 1
        return


class Channels(ctk.CTkScrollableFrame):
    def __init__(self, parent, n_channels, **kwargs):
        super().__init__(parent, label_text="Channels", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.grid(row=n_channels, column=0, padx=(5, 5), sticky="nsew")
        self.channels = []
        for i in range(n_channels):
            channel = Channel(self, label=i + 1, voltage_range=(-1.5, 1.5),
                              edge_detection=EdgeDetection.Rising, height=18)
            channel.grid(row=i + 1, column=0, pady=(0, 5), sticky="nsew")

            self.channels.append(channel)


class UpTime(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid(rows=1, columns=2, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)

        self.label = ctk.CTkLabel(self, text="Up Time")
        self.label.grid(row=0, column=0, padx=(10, 10), sticky="nsew")

        self.start_time = None

        font = ctk.CTkFont("Roboto", 28, "bold")
        self.clock = ctk.CTkLabel(self, text="00:00", font=font)
        self.clock.grid(row=0, column=1, padx=(10, 10), sticky="e")

    def update(self):
        if self.start_time is None:
            self.start_time = datetime.datetime.now()

        current_time = datetime.datetime.now() - self.start_time

        hours, remainder = divmod(current_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        time_format = f"{int(hours)}:{int(minutes)}:{int(seconds)}"
        self.clock.configure(text=time_format)
        self.timer_id = self.after(1000, self.update)

    def stop(self):
        self.after_cancel(self.timer_id)
        self.start_time = None


class TotalCounts(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid(rows=1, columns=2, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)

        self.label = ctk.CTkLabel(self, text="Total Counts")
        self.label.grid(row=0, column=0, padx=(10, 10), sticky="nsew")

        font = ctk.CTkFont("Roboto", 28, "bold")
        self.counter = ctk.CTkLabel(self, text="0", font=font)
        self.counter.grid(row=0, column=1, padx=(10, 10), sticky="e")


class Filtering(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid(columns=2, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)

        self.min_count_label = ctk.CTkLabel(self, text="Minimum Count Filter")
        self.min_count_label.grid(row=0, column=0, padx=(10, 10), sticky="nsew")

        self.min_count = FloatSpinbox(self, step_size=1, value_range=(1, 10))
        self.min_count.grid(row=0, column=1, padx=(10, 10), sticky="nsew")

        self.max_time_label = ctk.CTkLabel(self, text="Maximum Time Filter")
        self.max_time_label.grid(row=1, column=0, padx=(10, 10), sticky="nsew")

        self.max_time = FloatSpinbox(self, step_size=1, value_range=(0, 1000))
        self.max_time.grid(row=1, column=1, padx=(10, 10), sticky="nsew")

        self.max_time_options = ["ps", "ns", "µs"]
        self.max_time_magnitude = [-12, -9, -6]
        self.max_time_choice = ctk.CTkComboBox(
            self, width=60, values=self.max_time_options)
        self.max_time_choice.grid(row=1, column=2, sticky="ew", padx=(5, 5))


class LoadSave(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.config = None

        self.grid(rows=1, columns=2, sticky="nsew")
        self.grid_columnconfigure((0, 1), weight=1)

        self.load_button = ctk.CTkButton(
            self, text="Load", command=parent.load_path)
        self.load_button.grid(row=0, column=0, padx=(
            5, 5), pady=(5, 0), sticky="ew")

        self.save_button = ctk.CTkButton(
            self, text="Save", command=self.save_path, state="disabled")
        self.save_button.grid(row=0, column=1, padx=(
            5, 5), pady=(5, 0), sticky="ew")

    def save_path(self):
        file_name = asksaveasfilename(filetypes=[("json", "*.json")],
                                      initialdir=tangy_config_location())
        with open(file_name, "w") as file:
            json.dump(self.config, file, indent=4)


class DeviceThread:
    def __init__(self, parent, device_id: int, buffer_size: int, calibrate: bool):

        self.parent = parent

        self.queue = Queue()
        self.parent.queue = self.queue

        self.device = UQDLogic16(device_id=device_id, add_buffer=True,
                                 buffer_size=buffer_size, calibrate=calibrate)

        self.count = 0
        self.config = {}
        self.new_config = False

        self.running = True
        self.reading = False
        self.event = threading.Event()
        self.thread = threading.Thread(target=self.worker, args=(self.event, ))
        self.thread.start()
        self.event.clear()
        self.id = None

        self.sync()

    def sync(self):
        self.parent.process()

        start_stop_state = self.parent.start_stop_state.get()
        event_set = self.event.is_set()

        if self.reading is False and start_stop_state == "Start":
            # print("Started")
            self.device.start_timetags()
            self.reading = True

        if self.reading is True and start_stop_state == "Stop":
            # print("Stopped")
            self.device.stop_timetags()
            self.reading = False

        if start_stop_state == "Stop" and self.running is True and event_set is True:
            self.event.clear()
        elif start_stop_state == "Start" and self.running is True and event_set is False:
            self.event.set()

        while self.parent.messages.qsize():
            try:
                self.config = self.parent.messages.get(0)
                self.new_config = True
            except Queue.empty():
                pass

        self.id = self.parent.after(200, self.sync)

    def worker(self, event: threading.Event):
        while self.running:
            if self.new_config:
                print(self.config)

                for k, v in self.config["enabled"].items():
                    i = int(k[2:]) - 1
                    if v is True:
                        self.device.exclusion = (i, 0)
                    if v is False:
                        self.device.exclusion = (i, 1)

                # print(self.device.exclusion)

                for k, v in self.config["edges"].items():
                    i = int(k[2:]) - 1
                    if v == "Rising":
                        self.device.inversion = (i, 0)
                    if v == "Falling":
                        self.device.inversion = (i, 1)

                # print(self.device.inversion)
                self.device.inversion_apply()

                for k, v in self.config["voltages"].items():
                    i = int(k[2:]) - 1
                    self.device.input_threshold = (i + 1, v)

                # print(self.device.input_threshold)

                self.new_config = False

            time.sleep(1 / 20)
            if not event.is_set():
                self.count = 0
                event.wait(1 / 20)
                event.clear()
            else:
                if self.reading is True:
                    self.count = self.device.write_to_buffer()
                self.queue.put(self.count)
            if self.running is False:
                event.clear()

    def on_quit(self):
        self.running = False


class UQD(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.queue = None
        self.messages = Queue()

        self.title("UQD")
        self.geometry("500x740")
        self.minsize(500, 740)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.uptime = UpTime(self)
        self.uptime.grid(row=0, column=0, sticky="nsew")

        self.total_counts = TotalCounts(self)
        self.total_counts.grid(row=1, column=0, sticky="nsew")

        self.config = {}

        self._channel_count = 0

        self.enabled = [True for i in range(self._channel_count)]
        self.voltages = [0 for i in range(self._channel_count)]
        self.edges = [0 for i in range(self._channel_count)]

        self.channels = Channels(self, self._channel_count)
        self.channels.grid(row=2, column=0, pady=(5, 0), sticky="nsew")

        self.filtering = Filtering(self)
        self.filtering.grid(row=3, column=0, pady=(5, 0), sticky="nsew")

        self.load_save = LoadSave(self)
        self.load_save.grid(row=4, column=0, pady=(5, 0), sticky="nsew")

        self.apply_button = ctk.CTkButton(self, text="Apply",
                                          command=self.apply_thresholds)
        self.apply_button.grid(row=5, column=0, padx=5,
                               pady=(5, 0), sticky="ew")

        self.start_stop_state = ctk.StringVar(value="Stop")
        self.start_button = ctk.CTkSegmentedButton(self, values=["Start", "Stop"],
                                                   variable=self.start_stop_state,
                                                   state="disabled",
                                                   command=self.start_stop)
        self.start_button.grid(row=6, column=0, padx=5, pady=(5, 5),
                               sticky="ew")

    @property
    def channel_count(self) -> int:
        return self._channel_count

    def channels_init(self):
        self.enabled = [True for i in range(self._channel_count)]
        self.voltages = [0 for i in range(self._channel_count)]
        self.edges = [0 for i in range(self._channel_count)]

        self.channels = Channels(self, self._channel_count)
        self.channels.grid(row=2, column=0, pady=(5, 0), sticky="nsew")

    @channel_count.setter
    def channel_count(self, n: int):
        self._channel_count = n

    @channel_count.setter
    def channel_count(self, value: type):
        self._channel_count = value

    def process(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(self.queue.qsize() + 1)
                self.total_counts.counter.configure(text=f"{msg}")
            except Queue.empty():
                pass

    def load_path(self):
        file_name = askopenfilename(initialdir=tangy_config_location())
        config = None
        with open(file_name, "r") as file:
            config = json.load(file)

        for ch, v in config["voltages"].items():
            i = int(ch[2:]) - 1
            voltage = float(v)
            lower = self.channels.channels[i].threshold.value_range[0]
            upper = self.channels.channels[i].threshold.value_range[1]
            if (voltage < lower) or (voltage > upper):
                raise ValueError(
                    f"Channel {i} voltage ({voltage}) is out of range {lower, upper}")
            self.voltages[i] = voltage

        for ch, e in config["edges"].items():
            i = int(ch[2:]) - 1
            if e.lower() == "rising":
                self.edges[i] = EdgeDetection.Rising.value
            elif e.lower() == "falling":
                self.edges[i] = EdgeDetection.Falling.value
            else:
                raise ValueError(f"{e} is not a valid edge detection method")

        for ch, e in config["enabled"].items():
            i = int(ch[2:]) - 1
            self.enabled[i] = e

        for i, ch in enumerate(self.channels.channels):
            ch.threshold.set(self.voltages[i])
            ch.edge_button.set(EdgeDetection(self.edges[i]).name)
            ch.enabled_channel(self.enabled[i])

    def apply_thresholds(self):
        for i, channel in enumerate(self.channels.channels):
            (enabled, voltage, edge) = channel.get()
            self.enabled[i] = enabled
            self.voltages[i] = voltage
            self.edges[i] = edge.value

        min_count = int(self.filtering.min_count.get())

        max_time = float(self.filtering.max_time.get())
        max_time_unit = self.filtering.max_time_choice.get()
        for i, unit in enumerate(self.filtering.max_time_options):
            if unit == max_time_unit:
                break
        max_time_magnitude = self.filtering.max_time_magnitude[i]
        max_time_scaled = max_time / (10 ** max_time_magnitude)

        config = {
            "enabled": {f"ch{i+1}": e for i, e in enumerate(self.enabled)},
            "voltages": {f"ch{i+1}": v for i, v in enumerate(self.voltages)},
            "edges": {f"ch{i+1}": EdgeDetection(e).name for i, e in enumerate(self.edges)},
            "filter_count": min_count,
            "filter_time": max_time_scaled
        }

        self.load_save.save_button.configure(state="normal")
        self.load_save.config = config
        self.start_button.configure(state="normal")

        self.messages.put(config)
        self.config = config

    def start_stop(self, value):
        state = self.start_stop_state.get()
        if state == "Start":
            self.uptime.update()
            return
        self.uptime.stop()

    def start(self):
        self.timer_id = self.uptime.update()

    def stop(self):
        self.uptime.after_cancel(self.timer_id)


def run():
    import argparse

    parser = argparse.ArgumentParser(description="Options for UQDLogic16")
    parser.add_argument("--device_id", type=int, default=1, help="Device id")
    parser.add_argument("--buffer_size", type=int, default=100_000_000,
                        help="Size of buffer to create")
    parser.add_argument("--calibrate", default=True, help="Run calibration on start up")
    args = parser.parse_args()

    print(args)

    app = UQD()
    device = DeviceThread(app, args.device_id, args.buffer_size, args.calibrate)
    app.channel_count = device.device.number_of_channels
    app.channels_init()
    app.mainloop()
    device.on_quit()


if __name__ == '__main__':
    run()
