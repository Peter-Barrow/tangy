from typing import Union, Tuple, Callable, Optional
from math import log10, sqrt
import time
# from enum import Enum
# import json
# import threading
# from queue import Queue
import customtkinter as ctk

from tangy import buffer_list_update
from tangy import TangyBuffer


class FloatSpinbox(ctk.CTkFrame):
    def __init__(self, *args,
                 height: int = 18,
                 width: Optional[int] = 50,
                 step_size: Union[int, float] = 1,
                 step_size_big: Optional[Union[int, float]] = None,
                 value_range: Optional[Tuple[Union[int, float]]] = None,
                 units: Optional[str] = "",
                 uniform: Optional[str] = None,
                 command: Callable = None,
                 **kwargs):

        super().__init__(*args, height=height, bg_color="transparent", **kwargs)

        self.units = units
        self.units_len = len(units)
        self.command = command

        self.configure(fg_color=("gray78", "gray28"))  # set frame color

        self.value_range = value_range

        width = width
        width_small = int(50 * 0.6)

        num_columns = 2
        weights = [0, 1, 0]
        entry_column = 1
        self.step_size = step_size
        self.step_size_small = 0
        if step_size_big is not None:
            num_columns += 2
            entry_column += 1
            self.step_size = step_size_big
            self.step_size_small = step_size
            weights = [0, 0, 1, 0, 0]

        if units != "":
            num_columns += 1
            weights = [0, 0, 1, 0, 0, 0]

        # self.grid(column=num_columns, row=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        for i, w in enumerate(weights):
            self.columnconfigure(i, weight=w)

        self.subtract_button = ctk.CTkButton(self,
                                             text="-",
                                             width=width,
                                             command=self.button_step_backward)
        self.subtract_button.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)

        self.entry = ctk.CTkEntry(self, border_width=0, width=width)
        self.entry.grid(row=0, column=entry_column,
                        padx=3, pady=3, sticky="nsew")
        # default value
        if isinstance(value_range[0], (float)):
            self.entry.insert(0, "0.0")
        else:
            self.entry.insert(0, "0")

        if units != "":
            self.label = ctk.CTkLabel(self, text=self.units)
            self.label.grid(row=0, column=entry_column + 1, padx=1, pady=3,
                            sticky="nsew")

        self.add_button = ctk.CTkButton(self,
                                        text="+",
                                        width=width,
                                        command=self.button_step_forward)
        self.add_button.grid(row=0, column=num_columns,
                             sticky="nsew", padx=3, pady=3)

        if step_size_big is not None:
            self.subtract_button_small = ctk.CTkButton(self,
                                                       text="-",
                                                       width=width_small,
                                                       command=self.button_step_backward_small)
            self.subtract_button_small.grid(
                row=0, column=1, padx=8, pady=8, sticky="nsew")

            self.add_button_small = ctk.CTkButton(self,
                                                  text="+",
                                                  width=width_small,
                                                  command=self.button_step_forward_small)
            self.add_button_small.grid(
                row=0, column=num_columns - 1, padx=8, pady=8, sticky="nsew")

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


class Pair(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.grid_columnconfigure((2), weight=1)

        self.signal_label = ctk.CTkLabel(self, text="Signal: ")
        self.signal_label.grid(row=0, column=0, padx=(5, 5), pady=(5, 0))

        self.signal_channel = FloatSpinbox(self,
                                           step_size=int(1),
                                           value_range=(int(0), int(255)),
                                           width=45,
                                           )
        self.signal_channel.grid(row=0, column=1, padx=(5, 10), pady=(5, 5), sticky="nsew")

        self.signal_label = ctk.CTkLabel(self, text="Idler:  ")
        self.signal_label.grid(row=1, column=0, padx=(5, 5), pady=(5, 5))

        self.idler_channel = FloatSpinbox(self,
                                          step_size=int(1),
                                          value_range=(int(0), int(255)),
                                          width=45,
                                          )
        self.idler_channel.grid(row=1, column=1, padx=(5, 10), pady=(5, 5), sticky="nsew")

        self.delay = 0

        self.delay_value = ctk.DoubleVar(self, value=0)
        self.delay_slider = ctk.CTkSlider(
            self, from_=-1000, to=1000, variable=self.delay_value, command=self.delay_slider_apply)
        self.delay_slider.grid(row=0, column=2, columnspan=3, sticky="ew")

        self.searching = False
        self.delay_search_button = ctk.CTkButton(self, text="Find Delay", command=self.delay_search)
        self.delay_search_button.grid(row=0, column=5, padx=(5, 5), pady=(5, 5), stick="ew")

        self.window_label = ctk.CTkLabel(self, text="Window (ns)")
        self.window_label.grid(row=1, column=2, sticky="e")
        self.window_entry = ctk.CTkEntry(self, border_width=0, width=40)
        self.window_entry.grid(row=1, column=3, sticky="w", padx=(5, 5))
        self.window_entry.insert(0, "1.0")

        self.delay_label = ctk.CTkEntry(self, border_width=0)
        self.delay_label.grid(row=1, column=4, sticky="ew")
        self.delay_label.insert(0, "0.0")

        self.delay_units_options = ["ps", "ns", "µs", "ms", "s"]
        self.delay_units_magnitude = [-12, -9, -6, -3, 0]
        self.delay_units = ctk.CTkComboBox(
            self, width=60, values=self.delay_units_options, command=self.delay_calculate)
        self.delay_units.grid(row=1, column=5, sticky="ew", padx=(5, 5))

        self.changed = False

        self.delay_calculate(None)

    def configuration(self):
        channels = self.channel_choice()
        delays = [0, self.delay]

        return channels, delays

    def channel_choice(self):
        channel_signal = self.signal_channel.get()
        channel_idler = self.idler_channel.get()
        return [channel_idler, channel_signal]

    def delay_search(self):
        self.searching = True

    def delay_slider_apply(self, value):
        self.delay_label.delete(0, "end")
        self.delay_label.insert(0, f"{value:.5g}")
        self.delay = self.delay_calculate(None)

    def delay_from_found(self, delay_seconds):
        self.delay = delay_seconds
        self.delay_units.get()

        order = log10(abs(delay_seconds))
        for i, mag in enumerate(self.delay_units_magnitude):
            if order < mag:
                break
        # i -= 1
        print(self.delay_units_magnitude[i])
        self.delay_units.set(self.delay_units_options[i])
        d = delay_seconds / (10 ** self.delay_units_magnitude[i])
        self.delay_slider_apply(d)
        self.delay_slider.set(d)
        self.delay_calculate(None)

    def delay_calculate(self, choice):
        if choice is None:
            choice = self.delay_units.get()
        for i, unit in enumerate(self.delay_units_options):
            if unit == choice:
                break
        value = self.delay_slider.get()
        delay = value * (10 ** self.delay_units_magnitude[i])
        self.delay = delay


class BufferList(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.columnconfigure((1), weight=0)
        self.columnconfigure((0, 2, 3), weight=1)
        self.rowconfigure((0), weight=0)

        self.buffer_list = buffer_list_update()
        self.format = 0
        self.buffer = None

        self.refresh = ctk.CTkButton(self, text="Refresh", width=45, command=self.refresh_list)
        self.refresh.grid(row=0, column=0, padx=(5, 10), pady=(5, 5), sticky="nsw")

        self.label = ctk.CTkLabel(self, text="Buffer: ")
        self.label.grid(row=0, column=1, padx=(5, 0), pady=(5, 5), sticky="nsw")

        values = list(self.buffer_list.keys())
        if len(values) == 0:
            values = ["No buffers available"]
        self.buffer_choice = ctk.CTkComboBox(self, values=values)
        self.buffer_choice.grid(row=0, column=2, padx=(5, 10), pady=(5, 5), sticky="nsew")

        self.connect = ctk.CTkButton(self, text="Connect", width=45, command=self.connect_to_buffer)
        self.connect.grid(row=0, column=3, padx=(5, 5), pady=(5, 5), sticky="nse")

        self.running = False
        self.start_stop_state = ctk.StringVar(value="Stop")
        self.start_button = ctk.CTkSegmentedButton(self, values=["Start", "Stop"],
                                                   variable=self.start_stop_state,
                                                   state="disabled",
                                                   command=self.start_stop)
        self.start_button.grid(row=0, column=4, padx=5, pady=(5, 5),
                               sticky="ew")

    def start_stop(self, value):
        if value == "Stop":
            self.running = False
            return
        self.running = True

    def refresh_list(self):
        self.buffer_list = buffer_list_update()
        values = list(self.buffer_list.keys())
        if len(values) == 0:
            values = ["No buffers available"]
        self.buffer_choice.configure(values=values)

    def connect_to_buffer(self):
        buffer_name = self.buffer_choice.get()

        if buffer_name == "No buffers available":
            return

        buffer_format = self.buffer_list[buffer_name]["format"]

        # self.format = buffer_format
        # if buffer_format == 0:
        #     self.buffer = TangyBufferStandard(name=buffer_name)
        # elif buffer_format == 1:
        #     self.buffer = TangyBufferClocked(name=buffer_name)
        # else:
        #     pass
        self.buffer = TangyBuffer(buffer_name, 1.0)

        self.start_button.configure(state="normal")


class HUDElement(ctk.CTkFrame):
    def __init__(self, parent, label, **kwargs):
        super().__init__(parent, **kwargs)

        self.label_font = ctk.CTkFont(size=14)
        self.label = ctk.CTkLabel(self, text=label, font=self.label_font)
        self.label.pack(anchor="nw")

        self.text_font = ctk.CTkFont(size=48, weight="bold")
        self.text = ctk.CTkLabel(self, text="0", font=self.text_font)
        self.text.pack(anchor="se", side="bottom", padx=(0, 5), pady=(0, 5))


class HUD(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.grid_columnconfigure((0, 1), weight=1, uniform="a")
        self.grid_rowconfigure((0, 1), weight=1)

        self.rate_signal = HUDElement(self, "Signal")
        self.rate_signal.grid(row=0, column=0, padx=(5, 2.5), pady=(5, 0), sticky="nsew")

        self.rate_idler = HUDElement(self, "Idler")
        self.rate_idler.grid(row=1, column=0, padx=(5, 2.5), pady=(5, 5), sticky="nsew")

        self.rate_coincidence = HUDElement(self, "Coincidences")
        self.rate_coincidence.grid(row=0, column=1, padx=(2.5, 5), pady=(5, 0), sticky="nsew")

        self.efficiency = HUDElement(self, "Efficiency")
        self.efficiency.grid(row=1, column=1, padx=(2.5, 5), pady=(5, 5), sticky="nsew")


class CoincidenceCounter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tangy Pair Counter")
        self.geometry("650x400")
        self.minsize(650, 400)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0), weight=1)
        self.grid_rowconfigure((1, 2, 3), weight=0)

        self.hud = HUD(self)
        self.hud.grid(row=0, column=0, padx=(5, 5), pady=(5, 0), sticky="nsew")

        # self.signal = Channel(self)
        # self.signal.grid(row=1, column=1, padx=(5, 5), pady=(5, 0), sticky="nsew")

        # self.idler = Channel(self)
        # self.idler.grid(row=2, column=1, padx=(5, 5), pady=(5, 0), sticky="nsew")

        self.pair = Pair(self)
        self.pair.grid(row=1, column=0, padx=(5, 5), pady=(5, 0), sticky="nsew")

        self.buffer_list = BufferList(self)
        self.buffer_list.grid(row=3, column=0, padx=(5, 5), pady=(5, 5), sticky="nsew")

        self.count()

    def count(self):
        if self.buffer_list.running is True:
            # start_time = time.perf_counter()
            channels = [self.pair.idler_channel.get(), self.pair.signal_channel.get()]
            delays = [0, self.pair.delay]
            try:
                window = float(self.pair.window_entry.get())
            except ValueError:
                window = 1

            window *= (1e-9)

            (total, singles_count) = self.buffer_list.buffer.singles(1.0)
            rate_i = singles_count[channels[0]]
            rate_s = singles_count[channels[1]]
            eta = 0
            cc = 0
            if not (rate_i == 0 or rate_s == 0):
                cc = self.buffer_list.buffer.coincidence_count(1, window, channels, delays=delays)
                eta = (cc / sqrt(rate_i * rate_s)) * 100
            self.hud.rate_idler.text.configure(text=f"{rate_i}")
            self.hud.rate_signal.text.configure(text=f"{rate_s}")
            self.hud.rate_coincidence.text.configure(text=f"{cc}")
            self.hud.efficiency.text.configure(text=f"{eta:.4g}")
            # stop_time = time.perf_counter()
            # print(stop_time - start_time)

        if self.pair.searching is True:
            self.pair.searching = False
            channels, delays = self.pair.configuration()
            delay_result = self.buffer_list.buffer.relative_delay(
                channels[0], channels[1], 10, resolution=6.25e-9, window=100e-7)
            new_delay = delay_result.t0
            self.pair.delay_from_found(new_delay)

        self.after(25, self.count)


def run():
    app = CoincidenceCounter()
    app.mainloop()


if __name__ == '__main__':
    run()
