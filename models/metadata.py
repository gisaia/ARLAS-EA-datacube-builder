from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Dimension:
    axis: str = field()
    description: str = field()

    def as_dict(self):
        dimension = {}
        dimension["axis"] = self.axis
        dimension["description"] = self.description
        return dimension


@dataclass
class HorizontalSpatialDimension(Dimension):
    extent: List[float | int] = field()
    step: float | int | None = field()
    type: str = field(default="spatial")
    reference_system: str | int | object = field(default=4326)

    def as_dict(self):
        dimension = super().as_dict()
        dimension["extent"] = self.extent
        dimension["step"] = self.step
        dimension["type"] = self.type
        dimension["reference_system"] = self.reference_system
        return dimension


@dataclass
class TemporalDimension(Dimension):
    extent: List[str | None] = field()
    step: str | None = field()

    def as_dict(self):
        dimension = super().as_dict()
        dimension["extent"] = self.extent
        dimension["step"] = self.step
        return dimension


@dataclass
class Variable:
    dimensions: List[str] = field()
    type: str = field()
    description: str = field()
    extent: List[float | int | str | None] = field()
    unit: str = field()
    expression: str = field()

    def as_dict(self):
        variable = {}
        variable["dimensions"] = self.dimensions
        variable["type"] = self.type
        variable["description"] = self.description
        variable["extent"] = self.extent
        variable["unit"] = self.unit
        variable["expression"] = self.expression
        return variable


@dataclass
class DatacubeMetadata:
    dimensions: Dict[str, Dimension] = field()
    variables: Dict[str, Variable] = field()
    composition: Dict[int, List[str]] = field()

    def as_dict(self):
        metadata = {}
        metadata["dimensions"] = {
            k: v.as_dict() for k, v in self.dimensions.items()}
        metadata["variables"] = {
            k: v.as_dict() for k, v in self.variables.items()}
        metadata["composition"] = self.composition

        return metadata
