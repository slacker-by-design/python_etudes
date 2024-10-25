"""
Main module of the Simple Calculator app
written as a demo of TKInter program using
Model-View-Controller concept.
"""
import tkinter as tk
import ttkcalculator.model as model
import ttkcalculator.view as view
import ttkcalculator.controller as controller


def main():
    """
    Simple Calculator App entry point

    Use this function to wire up all calculator components
    together and start it up.
    """
    app = tk.Tk()
    app.title('Simple TTK Calculator')
    app.resizable(width=False, height=False)

    display_view = view.TkDisplayView()
    keypad_view = view.TkKeypadView()
    engine = model.Calculator()
    keypad_ctrl = controller.KeypadController(display_view, keypad_view, engine)
    view.TkDisplay(app, display_view.tk_variable)
    view.TkKeypad(app, keypad_view.register, keypad_ctrl.key_pressed)

    app.mainloop()


if __name__ == '__main__':
    main()
