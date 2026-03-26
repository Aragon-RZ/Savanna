# utils/colors.py

class Colors:
    # --- The Color Palette (ANSI Codes) ---
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # This is crucial! It resets the color back to normal
    RESET = '\033[0m'

    # --- Custom Methods for your Simulation ---
    
    @staticmethod
    def state(text):
        """Used in your Watering Hole to color the animal's name"""
        return f"{Colors.CYAN}{text}{Colors.RESET}"

    @staticmethod
    def animal(name, species="Herbivore"):
        """You could use this to color predators and prey differently!"""
        if species == "Carnivore":
            return f"{Colors.RED}{name}{Colors.RESET}"
        return f"{Colors.GREEN}{name}{Colors.RESET}"

    @staticmethod
    def warning(text):
        """Great for death or extreme thirst messages"""
        return f"{Colors.YELLOW}{text}{Colors.RESET}"
        
    @staticmethod
    def dead(text):
        return f"{Colors.RED}{text}{Colors.RESET}"
    

    @staticmethod
    def bar(value, max_value=100, length=10):
        """Generates a visual progress bar. Changes color if getting dangerously high."""
        filled = int((value / max_value) * length)
        empty = length - filled
        bar_str = "█" * filled + "░" * empty
        
        if value >= 85: # Desperate
            return f"{Colors.RED}[{bar_str}]{Colors.RESET}"
        elif value >= 70: # Hungry/Thirsty
            return f"{Colors.YELLOW}[{bar_str}]{Colors.RESET}"
        return f"{Colors.GREEN}[{bar_str}]{Colors.RESET}"
        
    @staticmethod
    def desperate(text):
        return f"{Colors.RED}{Colors.YELLOW}{text}{Colors.RESET}"