import configparser
import regex as re

def parse_keybinds(keybind_string: str):
    keybind_string = re.sub(r"\s*,\s*", ",", keybind_string)
    all_keybinds = re.split(r"\s*\|\s*", keybind_string)
    
    for i in range(len(all_keybinds)):
        all_keybinds[i] = all_keybinds[i].split(",")
    
    return all_keybinds

def parse_config(filepath: str):
    config = configparser.ConfigParser()
    config.read(filepath)

    parsed_dict = {"keybinds": {}, "statistics": {}}

    for key in config["keybinds"].keys():
        required_keys = parse_keybinds(config["keybinds"][key])
        parsed_dict["keybinds"][key] = required_keys
    
    for key in config["statistics"].keys():
        parsed_dict["statistics"][key] = float(config["statistics"][key])

    return parsed_dict