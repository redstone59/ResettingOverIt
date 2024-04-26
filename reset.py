from order import ORDERED_CLIPS
from config import *

from pygame import mixer # For playing sounds
import keyboard, time    # For functionality
import os, sys, pathlib  # For working with filepaths
import statistics

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

mixer.init()

# TODO: customisable keybinds for reset and reverse (non-resetting run-killers)
# TODO: customisable z_scores
# TODO: customisable audio & quotes

def get_keybind_string(keybinds: list[list[str]]):
    result_list = []
    for keybind in keybinds:
        result_list += [" and ".join(keybind)]
    return " or ".join(result_list)

def keybind_is_pressed(keybind: list[str]):
    for key in keybind:
        if not keyboard.is_pressed(key):
            return False
    
    return True

def test_keybinds(keybinds: list[list[str]]):
    for keybind in keybinds:
        if keybind_is_pressed(keybind):
            return True
    
    return False

class ResettingOverIt:
    def __init__(self, config: dict):
        self.index = 0
        self.has_reversed = False
        self.to_close = False
        self.times = []
        mixer.music.set_volume(0.8)
        self.volume = 80
        
        self.apply_config(config)
        
        self.pressed_reset = lambda: test_keybinds(self.reset_keybinds)
        self.pressed_reverse = lambda: test_keybinds(self.reverse_keybinds)
    
    def apply_config(self, config):
        self.min_z_score = config["statistics"]["min_z_score"]
        self.max_z_score = config["statistics"]["max_z_score"]
        self.minimum_runs = config["statistics"]["minimum_runs"]
        
        self.reset_keybinds = config["keybinds"]["reset"]
        self.reverse_keybinds = config["keybinds"]["non_resetting_run_end"]
        
        # Ew.
        keyboard.on_press_key(config["keybinds"]["exit"][0][0], lambda x: self.set_close())
        keyboard.on_press_key(config["keybinds"]["volume_up"][0][0], lambda x: self.change_volume(10))
        keyboard.on_press_key(config["keybinds"]["volume_down"][0][0], lambda x: self.change_volume(-10))
        keyboard.on_press_key(config["keybinds"]["recalibrate"][0][0], lambda x: self.recalibrate())
        
        self.opening_message(config["keybinds"])
    
    def calibrated_message(self):
        mean = sum(self.times) / len(self.times)
        standard_deviation = statistics.stdev(self.times)
        
        calibrated_string  =  "Calibrated!\n"
        calibrated_string +=  "--------------------\n"
        calibrated_string += f"Average reset time: {mean:.6f}s\n"
        calibrated_string += f"Standard Deviation: {standard_deviation:.6f}"
        
        print(calibrated_string)
    
    def change_volume(self, delta: float):
        new_volume = self.volume + delta
        new_volume = min(max(new_volume, 0), 100) # Clamping volume between 0 and 1.
        
        if new_volume == self.volume: return
        
        self.volume = new_volume
        mixer.music.set_volume(self.volume / 100)
        print(f"Set volume to {self.volume}%")
        if mixer.music.get_busy(): return
        
        # Sound test on volume change.
        
        voiceline = pathlib.Path(PATH, "clips", "oofsorry.wav")
        with open(voiceline) as file:
            mixer.music.load(file)
            mixer.music.play()
            time.sleep(0.6) # Length of "uff..."
            mixer.music.stop()
    
    def is_outlier(self, time_taken: float):
        if len(self.times) >= self.minimum_runs:
            mean = sum(self.times) / len(self.times)
            standard_deviation = statistics.stdev(self.times)
            
            z_score = (time_taken - mean) / standard_deviation
            
            if z_score >= self.max_z_score:
                return True
            elif z_score <= self.min_z_score:
                return False
            
        self.times += [time_taken]
        return False
        
    def play_voiceline(self):
        key = list(ORDERED_CLIPS.keys())[self.index]
        quote = ORDERED_CLIPS[key]
        voiceline = pathlib.Path(PATH, "clips", key + ".wav")
        with open(voiceline) as file:
            mixer.music.load(file)
            mixer.music.play()
            print("-" * 20)
            print(quote)
            while mixer.music.get_busy(): pass
            self.index += 1
            self.index %= len(ORDERED_CLIPS)
    
    def main_loop(self):  
        while not self.to_close:
            is_outlier_time = self.wait_loop()
            
            if len(self.times) == self.minimum_runs - 1:
                self.calibrated_message()
            
            if is_outlier_time and not self.to_close:
                self.play_voiceline()
            else:
                # Hang to prevent the loop from running a shit ton of times.
                time.sleep(1)
            
            # Hang until reset if reversed.
            while self.has_reversed and not self.pressed_reset() and not self.to_close:
                pass
            time.sleep(0.5)
            self.has_reversed = False
    
    def opening_message(self, keybinds: dict):
        print("-" * 20)
        print("Resetting Over It with Bennett Foddy")
        print("-" * 20)
        print(f"Press {keybinds["volume_up"][0][0]} or {keybinds["volume_down"][0][0]} to increase and decrease the volume.")
        keybind_string = get_keybind_string(self.reset_keybinds)
        print(f"Resetting set to {keybind_string}")
        keybind_string = get_keybind_string(self.reverse_keybinds)
        print(f"Non-resetting run end set to {keybind_string}")
        print(f"To recalibrate, press {keybinds["recalibrate"][0][0]}")
        print(f"To exit, please press {keybinds["exit"][0][0]}")
        print("-" * 20)
        print("Calibrating...")
        print("-" * 20)

    def recalibrate(self):
        self.times = []
        print("Recalibrating...")
        print("-" * 20)
    
    def set_close(self):
        self.to_close = True
    
    def wait_loop(self):
        """
        Waits until the reverse keybind or reset keybind are pressed, appends the time taken to `self.times`.
        
        Returns `True` if the time taken to reset is an outlier.
        """
        start_time = time.time()
        has_reset = False
        
        while not has_reset and not self.to_close:
            if self.pressed_reset():
                has_reset = True
            elif self.pressed_reverse():
                self.has_reversed = True
                has_reset = True
        
        time_taken = time.time() - start_time
        
        return self.is_outlier(time_taken)

config = parse_config(pathlib.Path(PATH, "settings.ini"))
print(config)
ResettingOverIt(config).main_loop()