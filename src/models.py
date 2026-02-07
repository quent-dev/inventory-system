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
    units_sold_30_days: int = 0
    daily_sales_velocity: float = 0.0
    unit_cost: float = 0.0
    
    @property
    def available_stock(self) -> int:
        return max(0, self.current_stock - self.reserved_stock)
    
    @property
    def days_of_stock(self) -> Optional[float]:
        """Calculate days of stock remaining based on sales velocity."""
        if self.daily_sales_velocity <= 0:
            return None  # No sales data or no sales
        return self.available_stock / self.daily_sales_velocity
    
    @property
    def recommended_buffer(self) -> int:
        """Calculate recommended minimum buffer based on sales velocity."""
        if self.daily_sales_velocity <= 0:
            return 0
        # Recommend 7 days worth of inventory as buffer
        return int(self.daily_sales_velocity * 7)
    
    @property
    def inventory_value(self) -> float:
        """Calculate total inventory value (available stock × unit cost)."""
        return self.available_stock * self.unit_cost
    
    @property
    def total_inventory_value(self) -> float:
        """Calculate total inventory value including reserved stock."""
        return self.current_stock * self.unit_cost


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
    
    def calculate_cost_from_components(self, component_costs: Dict[str, float]) -> float:
        """Calculate total kit cost from component costs."""
        total_cost = 0.0
        
        for component in self.components:
            component_cost = component_costs.get(component.component_sku, 0.0)
            total_cost += component_cost * component.quantity_per_kit
        
        return total_cost


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