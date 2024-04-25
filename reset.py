from order import ORDERED_CLIPS

from pygame import mixer # For playing sounds
import keyboard, time    # For functionality
import os, sys, pathlib  # For working with filepaths
import statistics

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))

mixer.init()

class ResettingOverIt:
    def __init__(self):
        self.index = 0
        self.has_reversed = False
        self.to_close = False
        self.times = []
        keyboard.hook_key("escape", lambda x: self.set_close())
        
        self.pressed_reset = lambda: keyboard.is_pressed("i") and keyboard.is_pressed("e")
        self.pressed_reverse = lambda: keyboard.is_pressed("backspace")
    
    def calibrated_message(self):
        mean = sum(self.times) / len(self.times)
        standard_deviation = statistics.stdev(self.times)
        
        calibrated_string  =  "Calibrated!\n"
        calibrated_string +=  "--------------------\n"
        calibrated_string += f"Average reset time: {mean:.6f}s\n"
        calibrated_string += f"Standard Deviation: {standard_deviation:.6f}"
        
        print(calibrated_string)
    
    def is_outlier(self, time_taken: float):
        if len(self.times) >= 10:
            mean = sum(self.times) / len(self.times)
            standard_deviation = statistics.stdev(self.times)
            
            z_score = (time_taken - mean) / standard_deviation
            
            if z_score >= 3:    # Commonly accepted z-score for outliers. Also seems to work for 3-1 FFPG, so.
                return True
            elif z_score <= -1: # Discard outlier resets. (z_score from just pressing reset along with gaster's stream)
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
        self.opening_message()
        
        while not self.to_close:
            is_outlier_time = self.wait_loop()
            
            if len(self.times) == 9: self.calibrated_message()
            
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
    
    def opening_message(self):
        print("-" * 20)
        print("Resetting Over It with Bennett Foddy")
        print("Press ESC to leave.")
        print("-" * 20)
        print("Calibrating...")
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

ResettingOverIt().main_loop()