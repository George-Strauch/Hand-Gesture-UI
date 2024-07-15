import logging
import subprocess
import pyvolume
import mouse
import traceback


class ActionHandler:
    """
    class to handle basic controls of the computer, such as set volume, toggle play pause etc
    """

    def __init__(self):
        self.logger = logging.getLogger('ActionHandler')
        self.mouse_sensitivity = 5
        pass

    def set_volume(self, volume):
        """
        method to set the volume of the computer
        :param volume: the volume level to set
        """
        try:
            self.logger.info(f"Setting volume to {volume}")
            pyvolume.custom(volume)
            return True
        except Exception as e:
            self.logger.error('Failed to set volume.', exc_info=True)
            # self.logger.info(traceback.format_exc())
            return False

    def toggle_play(self):
        try:
            self.logger.info("Toggling play")
            subprocess.call(("playerctl", "play-pause"))
            return True
        except Exception as e:
            self.logger.error('Failed to toggle play.', exc_info=True)
            return False

    def move_mouse(self, x, y):
        try:
            self.logger.info(f"Moving mouse direction {x} {y}")
            direction = [x * self.mouse_sensitivity, y * self.mouse_sensitivity]
            mouse.move(*direction, duration=0.01, absolute=False)
            return True
        except Exception as e:
            self.logger.error('Failed to move mouse.', exc_info=True)
            return False


if __name__ == '__main__':
    ah = ActionHandler()

    if not ah.set_volume(50):
        print('Failed to set volume.')

    if not ah.toggle_play():
        print('Failed to toggle play.')
