from app.services.reference import reference_service

class ValidationService:
    def validate_category(self, category: str) -> bool:
        return category in reference_service.categories

    def verify_route_vehicle(self, route_id: str, vehicle_id: str) -> dict:
        """
        Validates if route and vehicle match known Delhi reference records.
        Returns verification metadata.
        """
        route_ok = route_id in reference_service.valid_routes if reference_service.valid_routes else True
        vehicle_ok = vehicle_id in reference_service.valid_vehicles if reference_service.valid_vehicles else True
        
        return {
            "route_verified": route_ok,
            "vehicle_verified": vehicle_ok,
            "all_verified": route_ok and vehicle_ok
        }

validation_service = ValidationService()
