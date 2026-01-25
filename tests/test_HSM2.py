class TaskHSM:
    def __init__(self):
        self.state = self.state_ready
        self.progress = 0

    def dispatch(self, event):
        print(f"Executing: {event}")
        # Logic: Try current state. If it returns None, try parent.
        handled = self.state(event)
        if handled is None:
            self.state_active_parent(event)

    def transition_to(self, new_state):
        print(f"  [Transition] -> {new_state.__name__}")
        self.state = new_state

    # --- STATES ---

    def state_ready(self, event):
        if event == "start":
            self.transition_to(self.state_sent)
        elif event == "suspend":
            print("  (Ready State): Easy suspend. Parking task.")
            self.transition_to(self.state_suspended)
        return True

    def state_active_parent(self, event):
        """Default behavior for any 'Active' sub-state."""
        if event == "suspend":
            print("  (Parent): Generic suspension logic applied.")
            self.transition_to(self.state_suspended)
        elif event == "error":
            self.transition_to(self.state_ready)
        return True

    def state_sent(self, event):
        """Specialized Child: Logic differs from the parent."""
        if event == "suspend":
            # OVERRIDE: We can't suspend while 'Sent' (non-interruptible)
            print("  (Sent State): CANNOT SUSPEND. Forcing Cancel/Ignore instead.")
            self.transition_to(self.state_ready)
            return True  # Event handled, don't bubble to parent

        if event == "receive_ack":
            print("  (Sent State): Data received!")
            self.transition_to(self.state_ready)
            return True

        return None  # Bubble up other events (like 'error') to parent

    def state_suspended(self, event):
        if event == "resume":
            self.transition_to(self.state_ready)
        return True


# --- CALLER ---
task = TaskHSM()

print("--- Scenario: Suspend while READY ---")
task.dispatch("suspend")  # Uses local state_ready logic

print("\n--- Scenario: Suspend while SENT (The Override) ---")
task.dispatch("start")
task.dispatch("suspend")  # state_sent overrides parent logic

print("\n--- Scenario: Error while SENT (The Bubble) ---")
task.dispatch("start")
task.dispatch("error")  # state_sent ignores it, bubbles to state_active_parent
