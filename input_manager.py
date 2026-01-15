import pygame

class InputManager:
    def __init__(self, joystick=None):
        self.joystick = joystick

    def eixo(self, axis, deadzone=0.2):
        if not self.joystick:
            return 0
        v = self.joystick.get_axis(axis)
        return 0 if abs(v) < deadzone else v

    def botao(self, btn):
        if not self.joystick:
            return False
        return self.joystick.get_button(btn)
