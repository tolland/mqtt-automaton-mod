"""
Farming behavior for automated crop farming
"""
from typing import Dict, Any, List, Tuple
from behaviors.base_behavior import BaseBehavior, BehaviorState


class FarmingBehavior(BaseBehavior):
    """
    Behavior for automated farming using waypoints and patterns.
    
    This behavior can:
    - Navigate to farming waypoints
    - Execute farming patterns (planting, harvesting, etc.)
    - Handle different crop types
    - Manage farming tools and inventory
    """
    
    def __init__(self, name: str = "farming", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.waypoints = config.get("waypoints", []) if config else []
        self.patterns = config.get("patterns", {}) if config else {}
        self.current_waypoint_index = 0
        self.pattern_engine = None
        
    def set_pattern_engine(self, pattern_engine):
        """Set the pattern engine for this behavior"""
        self.pattern_engine = pattern_engine
        
    def can_start(self, context: Dict[str, Any]) -> bool:
        """Check if farming can start"""
        # Check if we have waypoints and patterns configured
        if not self.waypoints or not self.patterns:
            print(f"[farming] Cannot start: no waypoints or patterns configured")
            return False
            
        # Check if pattern engine is available
        if not self.pattern_engine:
            print(f"[farming] Cannot start: no pattern engine available")
            return False
            
        # Check if bot is in a safe state
        if context.get("emergency_state", False):
            print(f"[farming] Cannot start: bot is in emergency state")
            return False
            
        return True
    
    def execute(self, context: Dict[str, Any]) -> bool:
        """Execute farming behavior"""
        print(f"[farming] Starting farming behavior with {len(self.waypoints)} waypoints")
        
        try:
            for wp_idx, waypoint in enumerate(self.waypoints):
                if self.state != BehaviorState.RUNNING:
                    print(f"[farming] Behavior interrupted at waypoint {wp_idx}")
                    return False
                
                print(f"[farming] Processing waypoint {wp_idx + 1}/{len(self.waypoints)}")
                
                # Navigate to waypoint
                if not self._navigate_to_waypoint(waypoint, context):
                    print(f"[farming] Failed to reach waypoint {wp_idx + 1}")
                    return False
                
                # Execute patterns at this waypoint
                patterns_to_run = waypoint.get("run", [])
                if patterns_to_run:
                    if not self._execute_patterns_at_waypoint(patterns_to_run, waypoint, context):
                        print(f"[farming] Failed to execute patterns at waypoint {wp_idx + 1}")
                        return False
                
                self.current_waypoint_index = wp_idx + 1
            
            print(f"[farming] Farming behavior completed successfully")
            return True
            
        except Exception as e:
            print(f"[farming] Error during farming execution: {e}")
            return False
    
    def _navigate_to_waypoint(self, waypoint: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Navigate to a specific waypoint"""
        waypoint_name = waypoint.get("name", "unnamed")
        print(f"[farming] Navigating to waypoint: {waypoint_name}")
        
        # Create navigation command
        if "name" in waypoint and waypoint["name"]:
            # Named waypoint - use chat command
            nav_cmd = f"#wp goto {waypoint['name']}"
            message_data = {
                "service": "baritone",
                "method": "chat",
                "correlationId": self.pattern_engine.correlation_id if self.pattern_engine else None,
                "params": {"message": nav_cmd}
            }
        else:
            # Coordinate waypoint
            x, y, z = waypoint["x"], waypoint["y"], waypoint["z"]
            message_data = {
                "service": "baritone",
                "method": "goto",
                "correlationId": self.pattern_engine.correlation_id if self.pattern_engine else None,
                "params": {"x": int(x), "y": int(y), "z": int(z)}
            }
        
        # Send navigation command
        cmd = str(message_data).replace("'", '"')
        print(f"[farming] Navigation command: {cmd}")
        # Note: In real implementation, this would use the actual message sender
        # self.message_sender(cmd)
        
        # For now, simulate successful navigation
        print(f"[farming] Successfully reached waypoint: {waypoint_name}")
        return True
    
    def _execute_patterns_at_waypoint(self, pattern_names: List[str], waypoint: Dict[str, Any], 
                                    context: Dict[str, Any]) -> bool:
        """Execute patterns at the current waypoint"""
        print(f"[farming] Executing {len(pattern_names)} patterns at waypoint")
        
        # Determine starting position for patterns
        if "x" in waypoint and "y" in waypoint and "z" in waypoint:
            start_pos = (float(waypoint["x"]), float(waypoint["y"]), float(waypoint["z"]))
        else:
            # Use current position
            start_pos = context.get("current_position", (0.0, 0.0, 0.0))
        
        for pattern_name in pattern_names:
            if self.state != BehaviorState.RUNNING:
                print(f"[farming] Behavior interrupted during pattern execution")
                return False
            
            pattern_steps = self.patterns.get(pattern_name)
            if not pattern_steps:
                print(f"[farming] Pattern '{pattern_name}' not found, skipping")
                continue
            
            print(f"[farming] Executing pattern: {pattern_name}")
            if not self.pattern_engine.execute_pattern(pattern_name, pattern_steps, start_pos):
                print(f"[farming] Pattern '{pattern_name}' failed")
                return False
        
        return True
    
    def cleanup(self, context: Dict[str, Any]) -> None:
        """Clean up after farming behavior"""
        print(f"[farming] Cleaning up farming behavior")
        
        # Stop any ongoing farming activities
        stop_cmd = {
            "service": "wurst",
            "method": "command",
            "correlationId": self.pattern_engine.correlation_id if self.pattern_engine else None,
            "params": {
                "command": "t",
                "args": ["autofarm", "off"]
            }
        }
        
        cmd = str(stop_cmd).replace("'", '"')
        print(f"[farming] Sending stop command: {cmd}")
        # Note: In real implementation, this would use the actual message sender
        # self.message_sender(cmd)
        
        # Reset state
        self.current_waypoint_index = 0
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current farming progress"""
        total_waypoints = len(self.waypoints)
        completed_waypoints = self.current_waypoint_index
        
        return {
            "total_waypoints": total_waypoints,
            "completed_waypoints": completed_waypoints,
            "progress_percent": (completed_waypoints / total_waypoints * 100) if total_waypoints > 0 else 0,
            "current_waypoint": self.waypoints[self.current_waypoint_index] if self.current_waypoint_index < total_waypoints else None
        }
