from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Product:
    sku: str
    name: str
    current_stock: int
    reserved_stock: int = 0
    last_updated: Optional[datetime] = None
    
    @property
    def available_stock(self) -> int:
        return max(0, self.current_stock - self.reserved_stock)


@dataclass
class KitComponent:
    kit_sku: str
    component_sku: str
    component_name: str
    quantity_per_kit: float
    component_cost: float = 0.0
    is_critical: bool = True


@dataclass
class Kit:
    sku: str
    name: str
    description: str
    price: float
    components: List[KitComponent]
    is_active: bool = True
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class BusinessRule:
    component_sku: str
    minimum_buffer_stock: int = 0
    maximum_kit_assembly: int = 1000
    lead_time_days: int = 7
    assembly_time_minutes: int = 15
    priority_level: str = "Medium"  # High/Medium/Low


@dataclass
class EffectiveInventory:
    kit_sku: str
    kit_name: str
    max_kits_possible: int
    bottleneck_component: Optional[str] = None
    days_of_stock: Optional[float] = None
    status: str = "OK"  # OK/LOW/CRITICAL