

class ViewModel:
    """
    puppet class to define what the UI should show
    """
    def __init__(self):
        self.record = False
        self.current_action = "ASLEEP"  # "RNAV, DPAD
        self.history = []
        self.rnav_options = []
        self.rnav_index = 0

    def get_view(self):
        return {}

