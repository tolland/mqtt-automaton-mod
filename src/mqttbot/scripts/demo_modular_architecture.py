#!/usr/bin/env python3
"""
Demonstration of the modular bot architecture
"""
import os
import sys
import time

# Add the scripts directory to the path
sys.path.append(os.path.dirname(__file__))

from behaviors.farming_behavior import FarmingBehavior
from behaviors.emergency_behavior import EmergencyBehavior
from patterns.pattern_engine import PatternEngine
from core.behavior_engine import BehaviorEngine


class MockMessageSender:
    """Mock message sender for demonstration"""

    def __init__(self):
        self.messages = []

    def __call__(self, message: str):
        self.messages.append(message)
        print(f"[mock] Sent: {message}")


class MockPositionTracker:
    """Mock position tracker for demonstration"""

    def __init__(self):
        self.position = (100.0, 64.0, -200.0)

    def __call__(self):
        return self.position


def demo_pattern_engine():
    """Demonstrate the pattern engine"""
    print("=== Pattern Engine Demo ===")

    # Create mock components
    message_sender = MockMessageSender()
    position_tracker = MockPositionTracker()

    # Create pattern engine
    pattern_engine = PatternEngine(message_sender, position_tracker)
    pattern_engine.set_correlation_id("demo-123")

    # Define a test pattern with dwell
    test_pattern = [
        "~ ~ ~2",
        "~ ~ ~-1",
        "~ ~ ~2",
        {"type": "dwell", "period": "2s"},  # 2 second dwell for demo
        "~ ~ ~-1",
        "~ ~ ~2",
    ]

    print("Executing test pattern with dwell...")
    success = pattern_engine.execute_pattern("test_pattern", test_pattern)
    print(f"Pattern execution result: {success}")
    print(f"Messages sent: {len(message_sender.messages)}")
    print()


def demo_behavior_engine():
    """Demonstrate the behavior engine"""
    print("=== Behavior Engine Demo ===")

    # Create behavior engine
    engine = BehaviorEngine()

    # Create mock components
    message_sender = MockMessageSender()
    position_tracker = MockPositionTracker()
    pattern_engine = PatternEngine(message_sender, position_tracker)

    # Create farming behavior
    farming_config = {
        "waypoints": [
            {"x": 100, "y": 64, "z": -200, "run": ["test_pattern"]},
            {"x": 102, "y": 64, "z": -202, "run": ["test_pattern"]},
        ],
        "patterns": {
            "test_pattern": ["~ ~ ~1", {"type": "dwell", "period": "1s"}, "~ ~ ~-1"]
        },
    }
    farming_behavior = FarmingBehavior("farming", farming_config)
    farming_behavior.set_pattern_engine(pattern_engine)

    # Create emergency behavior
    emergency_behavior = EmergencyBehavior("emergency")

    # Add behaviors to engine
    engine.add_behavior(farming_behavior)
    engine.add_behavior(emergency_behavior)

    # Set up context
    context = {
        "current_position": (100.0, 64.0, -200.0),
        "safe_locations": [{"name": "home", "x": 0, "y": 64, "z": 0}],
    }
    engine.update_context(context)

    # Queue farming behavior
    engine.queue_behavior(farming_behavior)

    print("Starting behavior engine...")
    engine.start()

    # Let it run for a bit
    time.sleep(3)

    # Simulate emergency
    print("Simulating pillager attack...")
    engine.update_context(
        {"pillager_attack": True, "pillager_data": {"threat_level": "high"}}
    )

    time.sleep(2)

    # Get status
    status = engine.get_status()
    print(f"Engine status: {status}")

    # Stop engine
    engine.stop()
    print("Behavior engine stopped")
    print()


def demo_emergency_handling():
    """Demonstrate emergency behavior handling"""
    print("=== Emergency Handling Demo ===")

    # Create emergency behavior
    emergency_config = {
        "safe_locations": [{"name": "home", "x": 0, "y": 64, "z": 0}],
        "discrete_locations": [{"x": 50, "y": 64, "z": 50}],
    }
    emergency_behavior = EmergencyBehavior("emergency", emergency_config)

    # Test different emergency scenarios
    scenarios = [
        {
            "name": "Pillager Attack",
            "context": {
                "pillager_attack": True,
                "pillager_data": {"threat_level": "high"},
            },
        },
        {
            "name": "Player Detection",
            "context": {"player_detected": True, "player_data": {"name": "Player123"}},
        },
        {
            "name": "Low Health",
            "context": {"low_health": True, "health_data": {"health": 5}},
        },
    ]

    for scenario in scenarios:
        print(f"Testing scenario: {scenario['name']}")

        if emergency_behavior.can_start(scenario["context"]):
            print(f"  Emergency behavior can start")
            emergency_behavior.start(scenario["context"])
            print(f"  Emergency behavior started")
            # Note: In real implementation, execute() would be called by the behavior engine
            print(f"  Emergency behavior would execute appropriate response")
            emergency_behavior.cleanup(scenario["context"])
            print(f"  Emergency behavior cleaned up")
        else:
            print(f"  Emergency behavior cannot start")
        print()


def main():
    """Run all demonstrations"""
    print("Modular Bot Architecture Demonstration")
    print("=" * 50)
    print()

    try:
        demo_pattern_engine()
        demo_emergency_handling()
        demo_behavior_engine()

        print("All demonstrations completed successfully!")
        print()
        print("Key Benefits of Modular Architecture:")
        print("1. Behaviors can be easily added/removed")
        print("2. Emergency situations are handled automatically")
        print("3. Patterns are reusable across different behaviors")
        print("4. Each component has a single responsibility")
        print("5. Easy to test and debug individual components")
        print("6. Current working code is preserved in legacy/")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
