# utils/colors.py
class Colors:
    """ANSI color codes for terminal output"""
    CYAN = '\033[36m'      # Position
    YELLOW = '\033[33m'    # Thirst
    MAGENTA = '\033[35m'   # State
    RESET = '\033[0m'      # Reset to default
    RED = '\033[31m'      # Danger / Alerts
    GREEN = '\033[32m'    # Success / Positive states
    
    @staticmethod
    def position(text):
        return f"{Colors.CYAN}{text}{Colors.RESET}"
    
    @staticmethod
    def thirst(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"
    
    @staticmethod
    def hunger(text):
        return f"{Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def state(text):
        if text == "DRINKING":
            return f"{Colors.GREEN}{text}{Colors.RESET}"
        elif text in ["HUNTING", "FLEEING"]:
            return f"{Colors.RED}{text}{Colors.RESET}"
        else:
            return f"{Colors.MAGENTA}{text}{Colors.RESET}"
