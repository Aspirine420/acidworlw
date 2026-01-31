🧬 EVOLUTION TERMINAL v3.5
Autonomous Natural Selection Simulation via Neural Networks.
This project is a digital "Petri dish" where geometric "Nodes" survive, hunt, and evolve in real-time. Each entity is controlled by its own SimpleBrain (Neural Network), passing its weights to descendants with random mutations.
🕹 Operator Controls
The system allows for direct manual intervention in the simulation:
LMB (Left Click): Select a Node. Opens the deep analysis panel: health status, current "thoughts," and a real-time visualization of its neural architecture.
Mouse Wheel: Instantly synthesize a random Resource at the cursor position.
RMB (Right Click): Deploy a Weapon Crate (Plasma or Railgun) for Nodes to scavenge.
🧠 Simulation Mechanics
Neural Brain: Nodes process 7 input parameters (Coordinates, HP, Angle/Distance to the nearest target, Enemy presence, Constant) to decide their rotation and movement speed.
Genetics & Mutation: Upon reaching the age of 5 minutes (300s), a Node reproduces. The offspring inherits:
Color: Smooth color drift (dynasties change hue over several generations).
Form: 30% chance to mutate into a different class (Tank, Scout, or Striker).
Weights: Slight random brain mutations to discover new survival strategies.
Swarm Bonus: Nodes of similar colors receive a damage buff when staying close to each other.
Lifespan: Entities are long-lived (12–15 minutes) unless destroyed by enemies or starvation. The UI tracks the current age of the selected Node.
🛠 Tech Stack
Language: Python 3.x
Library: Pygame
Algorithms: Feed-forward Neural Network, Euclidean metrics for targeting, Trigonometric navigation.
📉 Monitoring
The right-hand terminal panel provides:
Global Stats: Current population, total born entities, collected resources, and neutralized threats.
Population Graph: A real-time history of population dynamics.
Thought Log: Displays the current behavioral dominant of the selected Node (Analysis, Hunting, Drift, etc.).
