from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

@dataclass
class AdapterConfig:
    """Configuration for an adapter."""
    
    provider_name: str
    package_name: str
    license: str
    deterministic_level: str = "high"
    required_dependencies: List[str] = None
    optional_dependencies: List[str] = None
    configuration_options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.required_dependencies is None:
            self.required_dependencies = []
        if self.optional_dependencies is None:
            self.optional_dependencies = []
        if self.configuration_options is None:
            self.configuration_options = {}

@dataclass
class AdapterResult:
    """Base result type for all adapter operations."""
    
    adapter_name: str
    operation: str
    success: bool
    data: Any
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None

class BaseAdapter(ABC):
    """Abstract base class for all Workforce Management Harness adapters."""
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self._validate_dependencies()
        self._initialize_adapter()
    
    def _validate_dependencies(self):
        """Validate that required dependencies are available."""
        # This will be implemented by each adapter
        pass
    
    def _initialize_adapter(self):
        """Initialize adapter-specific resources."""
        # This will be implemented by each adapter
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check if the adapter is healthy and ready to use."""
        pass
    
    @abstractmethod
    def forecast(self, data: Any, **kwargs) -> AdapterResult:
        """Generate forecasts."""
        pass
    
    @abstractmethod
    def staff(self, data: Any, **kwargs) -> AdapterResult:
        """Calculate staffing requirements."""
        pass
    
    @abstractmethod
    def schedule(self, data: Any, **kwargs) -> AdapterResult:
        """Generate schedules."""
        pass
    
    @abstractmethod
    def optimize(self, data: Any, **kwargs) -> AdapterResult:
        """Optimize operations."""
        pass
    
    @abstractmethod
    def validate(self, data: Any, **kwargs) -> AdapterResult:
        """Validate data or configurations."""
        pass
    
    def execute_operation(self, operation: str, data: Any, **kwargs) -> AdapterResult:
        """Execute a specific operation."""
        try:
            if operation == "forecast":
                return self.forecast(data, **kwargs)
            elif operation == "staff":
                return self.staff(data, **kwargs)
            elif operation == "schedule":
                return self.schedule(data, **kwargs)
            elif operation == "optimize":
                return self.optimize(data, **kwargs)
            elif operation == "validate":
                return self.validate(data, **kwargs)
            else:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation=operation,
                    success=False,
                    data=None,
                    error_message=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation=operation,
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the provider."""
        return {
            "name": self.config.provider_name,
            "package": self.config.package_name,
            "license": self.config.license,
            "deterministic_level": self.config.deterministic_level,
            "required_dependencies": self.config.required_dependencies,
            "optional_dependencies": self.config.optional_dependencies,
            "configuration_options": self.config.configuration_options
        }
    
    def get_adaptation_metadata(self) -> Dict[str, Any]:
        """Get adaptation-specific metadata."""
        return {
            "adapter_type": self.__class__.__name__,
            "configured": True,
            "health_check": self.health_check()
        }