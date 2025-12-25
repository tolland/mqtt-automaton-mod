"""
Behavior engine for orchestrating multiple bot behaviors
"""
from typing import Dict, Any, List, Optional
import time
import threading
from behaviors.base_behavior import BaseBehavior, BehaviorState


class BehaviorEngine:
    """
    Orchestrates multiple behaviors, handling priorities, interruptions, and state management.
    
    The behavior engine:
    - Manages a queue of behaviors
    - Handles behavior priorities and interruptions
    - Provides context sharing between behaviors
    - Manages emergency situations
    """
    
    def __init__(self):
        self.behaviors: List[BaseBehavior] = []
        self.active_behavior: Optional[BaseBehavior] = None
        self.behavior_queue: List[BaseBehavior] = []
        self.context: Dict[str, Any] = {}
        self.running = False
        self.emergency_mode = False
        self.lock = threading.Lock()
        
    def add_behavior(self, behavior: BaseBehavior) -> None:
        """Add a behavior to the engine"""
        with self.lock:
            self.behaviors.append(behavior)
            print(f"[behavior_engine] Added behavior: {behavior.name}")
    
    def remove_behavior(self, behavior_name: str) -> bool:
        """Remove a behavior by name"""
        with self.lock:
            for i, behavior in enumerate(self.behaviors):
                if behavior.name == behavior_name:
                    del self.behaviors[i]
                    print(f"[behavior_engine] Removed behavior: {behavior_name}")
                    return True
            return False
    
    def queue_behavior(self, behavior: BaseBehavior) -> None:
        """Queue a behavior for execution"""
        with self.lock:
            # Insert behavior in priority order (lower number = higher priority)
            inserted = False
            for i, queued_behavior in enumerate(self.behavior_queue):
                if behavior.priority < queued_behavior.priority:
                    self.behavior_queue.insert(i, behavior)
                    inserted = True
                    break
            
            if not inserted:
                self.behavior_queue.append(behavior)
            
            print(f"[behavior_engine] Queued behavior: {behavior.name} (priority: {behavior.priority})")
    
    def start(self) -> None:
        """Start the behavior engine"""
        self.running = True
        print(f"[behavior_engine] Behavior engine started")
        
        # Start the main behavior loop in a separate thread
        self.engine_thread = threading.Thread(target=self._behavior_loop, daemon=True)
        self.engine_thread.start()
    
    def stop(self) -> None:
        """Stop the behavior engine"""
        self.running = False
        print(f"[behavior_engine] Behavior engine stopped")
        
        # Stop active behavior
        if self.active_behavior:
            self.active_behavior.suspend()
            self.active_behavior.cleanup(self.context)
            self.active_behavior = None
    
    def _behavior_loop(self) -> None:
        """Main behavior execution loop"""
        while self.running:
            try:
                with self.lock:
                    # Check for emergency situations first
                    if self._check_emergency_conditions():
                        self._handle_emergency()
                        continue
                    
                    # Get next behavior to execute
                    next_behavior = self._get_next_behavior()
                    if not next_behavior:
                        time.sleep(0.1)  # No behaviors to execute
                        continue
                    
                    # Check if we need to interrupt current behavior
                    if self.active_behavior and self._should_interrupt_current(next_behavior):
                        self._interrupt_current_behavior()
                    
                    # Start new behavior if none is active
                    if not self.active_behavior:
                        self._start_behavior(next_behavior)
                    
                    # Check if active behavior is complete
                    if self.active_behavior and self.active_behavior.state in [BehaviorState.COMPLETED, BehaviorState.FAILED]:
                        self._complete_behavior()
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                print(f"[behavior_engine] Error in behavior loop: {e}")
                time.sleep(1)
    
    def _check_emergency_conditions(self) -> bool:
        """Check if any emergency conditions are present"""
        # Check for pillager attacks
        if self.context.get("pillager_attack", False):
            return True
        
        # Check for player detection
        if self.context.get("player_detected", False):
            return True
        
        # Check for low health
        if self.context.get("low_health", False):
            return True
        
        return False
    
    def _handle_emergency(self) -> None:
        """Handle emergency situations"""
        if self.emergency_mode:
            return  # Already handling emergency
        
        print(f"[behavior_engine] Emergency detected, entering emergency mode")
        self.emergency_mode = True
        
        # Find emergency behavior
        emergency_behavior = None
        for behavior in self.behaviors:
            if behavior.name == "emergency":
                emergency_behavior = behavior
                break
        
        if emergency_behavior:
            # Interrupt current behavior
            if self.active_behavior:
                self._interrupt_current_behavior()
            
            # Start emergency behavior
            self._start_behavior(emergency_behavior)
        else:
            print(f"[behavior_engine] No emergency behavior found!")
    
    def _get_next_behavior(self) -> Optional[BaseBehavior]:
        """Get the next behavior to execute"""
        # In emergency mode, only emergency behaviors can run
        if self.emergency_mode:
            for behavior in self.behaviors:
                if behavior.name == "emergency" and behavior.state == BehaviorState.IDLE:
                    return behavior
            return None
        
        # Find highest priority behavior that can start
        for behavior in self.behavior_queue:
            if behavior.state == BehaviorState.IDLE and behavior.can_start(self.context):
                return behavior
        
        return None
    
    def _should_interrupt_current(self, next_behavior: BaseBehavior) -> bool:
        """Check if current behavior should be interrupted"""
        if not self.active_behavior:
            return False
        
        # Emergency behaviors always interrupt
        if next_behavior.name == "emergency":
            return True
        
        # Higher priority behaviors interrupt lower priority ones
        if next_behavior.priority < self.active_behavior.priority:
            return self.active_behavior.can_be_interrupted()
        
        return False
    
    def _interrupt_current_behavior(self) -> None:
        """Interrupt the currently active behavior"""
        if not self.active_behavior:
            return
        
        print(f"[behavior_engine] Interrupting behavior: {self.active_behavior.name}")
        
        if self.active_behavior.can_be_interrupted():
            self.active_behavior.suspend()
            self.active_behavior.cleanup(self.context)
        else:
            print(f"[behavior_engine] Cannot interrupt behavior: {self.active_behavior.name}")
        
        self.active_behavior = None
    
    def _start_behavior(self, behavior: BaseBehavior) -> None:
        """Start a behavior"""
        print(f"[behavior_engine] Starting behavior: {behavior.name}")
        
        if behavior.start(self.context):
            self.active_behavior = behavior
            
            # Execute behavior in a separate thread
            behavior_thread = threading.Thread(
                target=self._execute_behavior,
                args=(behavior,),
                daemon=True
            )
            behavior_thread.start()
        else:
            print(f"[behavior_engine] Failed to start behavior: {behavior.name}")
            behavior.complete(success=False)
    
    def _execute_behavior(self, behavior: BaseBehavior) -> None:
        """Execute a behavior"""
        try:
            success = behavior.execute(self.context)
            behavior.complete(success=success)
            
            if success:
                print(f"[behavior_engine] Behavior completed successfully: {behavior.name}")
            else:
                print(f"[behavior_engine] Behavior failed: {behavior.name}")
                
        except Exception as e:
            print(f"[behavior_engine] Error executing behavior {behavior.name}: {e}")
            behavior.complete(success=False)
        finally:
            behavior.cleanup(self.context)
    
    def _complete_behavior(self) -> None:
        """Handle completion of active behavior"""
        if not self.active_behavior:
            return
        
        behavior = self.active_behavior
        print(f"[behavior_engine] Behavior completed: {behavior.name}")
        
        # Remove from queue if it was queued
        if behavior in self.behavior_queue:
            self.behavior_queue.remove(behavior)
        
        # Reset emergency mode if emergency behavior completed
        if behavior.name == "emergency":
            self.emergency_mode = False
            print(f"[behavior_engine] Emergency mode cleared")
        
        self.active_behavior = None
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the shared context"""
        with self.lock:
            self.context.update(updates)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        with self.lock:
            return {
                "running": self.running,
                "emergency_mode": self.emergency_mode,
                "active_behavior": self.active_behavior.get_status() if self.active_behavior else None,
                "queued_behaviors": [b.get_status() for b in self.behavior_queue],
                "available_behaviors": [b.get_status() for b in self.behaviors if b.state == BehaviorState.IDLE],
                "context": self.context
            }
