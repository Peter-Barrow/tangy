from typing import Union, Tuple, Callable, Optional
import datetime
from enum import Enum
import json
import customtkinter as ctk
from tkinter.filedialog import askopenfilename, asksaveasfilename


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
        self.entry.grid(row=0, column=2,
                        padx=3, pady=3, sticky="ns")
        # default value
        self.entry.insert(0, "0.0")

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
            current_value = float(self.get())
            value = self.in_range(current_value, step)
            self.entry.delete(0, "end")
            self.entry.insert(0, f"{value:.2f}")
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

    def get(self) -> Union[float, None]:
        try:
            return float(self.entry.get())
        except ValueError:
            return None

    def set(self, value: float):
        self.entry.delete(1, "end")
        self.entry.insert(0, f"{value:.2f}")


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

        self.grid_columnconfigure((2), weight=1)
        self.label = ctk.CTkLabel(self, text=f"{label}", height=height)
        self.label.grid(row=0, column=0, padx=(3, 6), pady=3, sticky="nsew")

        self.edge_detection = edge_detection
        self.edge_var = ctk.StringVar(value=edge_detection.name)
        self.edge_button = ctk.CTkSegmentedButton(self, values=["Rising", "Falling"],
                                                  variable=self.edge_var,
                                                  height=height)
        self.edge_button.grid(row=0, column=1, padx=(6, 0), pady=(6, 6),
                              sticky="nsew")

        self.threshold = FloatSpinbox(self, height=24, step_size=0.1,
                                      step_size_big=1, units="V",
                                      value_range=voltage_range)
        self.threshold.grid(row=0, column=2, pady=3, sticky="nsew")

    def get(self) -> Tuple[float, EdgeDetection]:
        voltage = self.threshold.get()
        edge = EdgeDetection.Rising
        if self.edge_var.get() == "Falling":
            edge = EdgeDetection.Falling
        return (voltage, edge)


class Channels(ctk.CTkScrollableFrame):
    def __init__(self, parent, n_channels, **kwargs):
        super().__init__(parent, label_text="Channels", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.grid(row=n_channels, column=0, padx=(5, 5), sticky="nsew")
        self.channels = []
        for i in range(n_channels):
            channel = Channel(self, label=i + 1, voltage_range=(-2, 2),
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
        file_name = asksaveasfilename(filetypes=[("json", "*.json")])
        with open(file_name, "w") as file:
            json.dump(self.config, file, indent=4)


class UQD(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("UQD")
        self.geometry("450x670")
        self.minsize(450, 670)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.uptime = UpTime(self)
        self.uptime.grid(row=0, column=0, sticky="nsew")

        self.total_counts = TotalCounts(self)
        self.total_counts.grid(row=1, column=0, sticky="nsew")

        n_channels = 8

        self.voltages = [0 for i in range(n_channels)]
        self.edges = [0 for i in range(n_channels)]

        self.channels = Channels(self, n_channels)
        self.channels.grid(row=2, column=0, pady=(5, 0), sticky="nsew")

        self.load_save = LoadSave(self)
        self.load_save.grid(row=3, column=0, pady=(5, 0), sticky="nsew")

        self.apply_button = ctk.CTkButton(self, text="Apply",
                                          command=self.apply_thresholds)
        self.apply_button.grid(row=4, column=0, padx=5,
                               pady=(5, 0), sticky="ew")

        self.start_stop_state = ctk.StringVar(value="Stop")
        self.start_button = ctk.CTkSegmentedButton(self, values=["Start", "Stop"],
                                                   variable=self.start_stop_state,
                                                   state="disabled",
                                                   command=self.start_stop)
        self.start_button.grid(row=5, column=0, padx=5, pady=(5, 5),
                               sticky="ew")

    def load_path(self):
        file_name = askopenfilename()
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

        for i, ch in enumerate(self.channels.channels):
            ch.threshold.set(self.voltages[i])
            ch.edge_button.set(EdgeDetection(self.edges[i]).name)

    def apply_thresholds(self):
        for i, channel in enumerate(self.channels.channels):
            (voltage, edge) = channel.get()
            self.voltages[i] = voltage
            self.edges[i] = edge.value

        config = {
            "voltages": {f"ch{i+1}": v for i, v in enumerate(self.voltages)},
            "edges": {f"ch{i+1}": EdgeDetection(e).name for i, e in enumerate(self.edges)},
        }

        self.load_save.save_button.configure(state="normal")
        self.load_save.config = config
        self.start_button.configure(state="normal")

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


if __name__ == '__main__':
    app = UQD()
    app.mainloop()
