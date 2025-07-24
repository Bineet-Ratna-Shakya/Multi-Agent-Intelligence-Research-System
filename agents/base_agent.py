# Base agent

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from utils.logger import setup_logger
from utils.memory import SimpleMemory

class BaseAgent(ABC):    
    def __init__(self, name: str, memory: SimpleMemory = None):
        self.name = name
        self.logger = setup_logger(f"Agent.{name}")
        self.memory = memory or SimpleMemory()
        self.logger.info(f"Initialized {name} agent")
    
    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def log_interaction(self, interaction_type: str, data: Dict[str, Any]) -> None:
        log_data = {
            "agent": self.name,
            "type": interaction_type,
            "data": data
        }
        self.logger.info(f"Interaction: {log_data}")
        
        memory_key = f"{self.name}_{interaction_type}_{hash(str(data))}"
        self.memory.store(memory_key, log_data)
    
    def get_previous_interactions(self, interaction_type: str = None) -> List[Dict[str, Any]]:
        """Get previous interactions from memory."""
        all_keys = self.memory.get_all_keys()
        interactions = []
        
        for key in all_keys:
            if key.startswith(f"{self.name}_"):
                if interaction_type is None or interaction_type in key:
                    interaction = self.memory.retrieve(key)
                    if interaction:
                        interactions.append(interaction)
        
        return interactions

