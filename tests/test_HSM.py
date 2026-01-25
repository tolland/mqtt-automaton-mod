

class ToasterHSM:
    def __init__(self):
        # Start in the 'Off' state
        self.state = self.state_off

    def dispatch(self, event):
        """The engine: sends events to the current state."""
        self.state(event)

    def transition_to(self, new_state):
        print(f"-> Transitioning to {new_state.__name__}")
        self.state = new_state

    # --- STATES ---

    def state_off(self, event):
        if event == "power_button":
            self.transition_to(self.state_on_heating)
        else:
            print("Toaster is OFF. Doing nothing.")

    def state_on_parent(self, event):
        """The Parent State: Handles global 'ON' logic."""
        if event == "cancel":
            print("Parent caught 'cancel': Safety shutdown.")
            self.transition_to(self.state_off)
        else:
            print(f"Event '{event}' not handled by parent. Ignoring.")

    def state_on_heating(self, event):
        """The Child State: Inherits from state_on_parent."""
        if event == "timer_up":
            print("Toast is done!")
            self.transition_to(self.state_off)
        else:
            # If the child doesn't know what to do, it asks the parent
            self.state_on_parent(event)

# --- CALLER CODE ---
if __name__ == "__main__":
    toaster = ToasterHSM()

    print("--- Scenario 1: Normal Toasting ---")
    toaster.dispatch("power_button") # Moves to Heating
    toaster.dispatch("timer_up")     # Moves to Off

    print("\n--- Scenario 2: Emergency Cancel ---")
    toaster.dispatch("power_button") # Moves to Heating
    # 'cancel' isn't in 'heating' logic, but it IS in the parent 'on' logic
    toaster.dispatch("cancel")
