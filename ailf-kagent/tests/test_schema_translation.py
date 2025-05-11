"""
Unit tests for AILF-Kagent schema translation utilities.

These tests verify that schemas can be translated between AILF and Kagent formats.
"""

import pytest
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Import the schema translation utilities
from ailf_kagent.adapters.schemas import (
    map_ailf_to_kagent_schema,
    map_kagent_to_ailf_schema,
    convert_instance_to_schema,
    SchemaRegistry
)


class TestSchemaTranslation:
    """Test suite for schema translation functions."""
    
    #
    # Test schema definitions
    #
    class AILFUser(BaseModel):
        """AILF user model."""
        id: str = Field(..., description="User ID")
        name: str = Field(..., description="User's full name")
        email: str = Field(..., description="User's email address")
        age: Optional[int] = Field(None, description="User's age")
        tags: List[str] = Field(default_factory=list, description="User tags")
        
    class KagentUser(BaseModel):
        """Kagent user model."""
        user_id: str = Field(..., description="User identifier")
        full_name: str = Field(..., description="Name of the user")
        contact_email: str = Field(..., description="Contact email")
        age_years: Optional[int] = Field(None, description="Age in years")
        labels: List[str] = Field(default_factory=list, description="User labels")
    
    def test_simple_schema_mapping(self):
        """Test mapping of a simple schema from AILF to Kagent."""
        # Map AILF schema to Kagent schema
        kagent_schema = map_ailf_to_kagent_schema(self.AILFUser)
        
        # Check that the schema has the expected fields
        assert hasattr(kagent_schema, "model_fields")
        assert "id" in kagent_schema.model_fields
        assert "name" in kagent_schema.model_fields
        assert "email" in kagent_schema.model_fields
        assert "age" in kagent_schema.model_fields
        assert "tags" in kagent_schema.model_fields
        
        # Check field types
        assert kagent_schema.model_fields["id"].annotation == str
        assert kagent_schema.model_fields["name"].annotation == str
        assert kagent_schema.model_fields["age"].annotation == Optional[int]
        assert kagent_schema.model_fields["tags"].annotation == List[str]
        
        # Check that default factory is preserved
        assert kagent_schema.model_fields["tags"].default_factory is not None
        
    def test_instance_conversion(self):
        """Test conversion of a model instance to another schema."""
        # Create an AILF user instance
        ailf_user = self.AILFUser(
            id="123",
            name="John Doe",
            email="john@example.com",
            age=30,
            tags=["customer", "premium"]
        )
        
        # Create a mapped Kagent schema
        kagent_schema = map_ailf_to_kagent_schema(self.AILFUser)
        
        # Convert the instance
        kagent_user = convert_instance_to_schema(ailf_user, kagent_schema)
        
        # Check the converted instance
        assert kagent_user.id == "123"
        assert kagent_user.name == "John Doe"
        assert kagent_user.email == "john@example.com"
        assert kagent_user.age == 30
        assert kagent_user.tags == ["customer", "premium"]
    
    def test_back_and_forth_conversion(self):
        """Test converting a schema to another format and back."""
        # Map AILF to Kagent
        kagent_schema = map_ailf_to_kagent_schema(self.AILFUser)
        
        # Map back to AILF
        ailf_schema_round_trip = map_kagent_to_ailf_schema(kagent_schema)
        
        # Create an instance with the original schema
        original_user = self.AILFUser(
            id="456",
            name="Jane Smith",
            email="jane@example.com"
        )
        
        # Convert to the round-trip schema
        round_trip_user = convert_instance_to_schema(original_user, ailf_schema_round_trip)
        
        # Check that data is preserved
        assert round_trip_user.id == "456"
        assert round_trip_user.name == "Jane Smith"
        assert round_trip_user.email == "jane@example.com"


class TestSchemaRegistry:
    """Test suite for SchemaRegistry."""
    
    # Test schema definitions
    class AILFProfile(BaseModel):
        """AILF profile model."""
        user_id: str
        display_name: str
        bio: Optional[str] = None
        
    class KagentProfile(BaseModel):
        """Kagent profile model."""
        id: str
        name: str
        biography: Optional[str] = None
    
    class AILFAddress(BaseModel):
        """AILF address model."""
        street: str
        city: str
        zip_code: str
        
    class KagentAddress(BaseModel):
        """Kagent address model."""
        street_address: str
        city_name: str
        postal_code: str
    
    @pytest.fixture
    def registry(self):
        """Create a schema registry for testing."""
        registry = SchemaRegistry()
        
        # Register schema mappings
        registry.register_mapping(
            self.AILFProfile, 
            self.KagentProfile,
            {
                "user_id": "id",
                "display_name": "name",
                "bio": "biography"
            }
        )
        
        registry.register_mapping(
            self.AILFAddress,
            self.KagentAddress,
            {
                "street": "street_address",
                "city": "city_name",
                "zip_code": "postal_code"
            }
        )
        
        return registry
        
    def test_registry_mappings(self, registry):
        """Test that registry correctly stores and retrieves mappings."""
        # Check AILF to Kagent mappings
        kagent_profile = registry.get_kagent_schema(self.AILFProfile)
        assert kagent_profile == self.KagentProfile
        
        kagent_address = registry.get_kagent_schema(self.AILFAddress)
        assert kagent_address == self.KagentAddress
        
        # Check Kagent to AILF mappings
        ailf_profile = registry.get_ailf_schema(self.KagentProfile)
        assert ailf_profile == self.AILFProfile
        
        ailf_address = registry.get_ailf_schema(self.KagentAddress)
        assert ailf_address == self.AILFAddress
    
    def test_convert_to_kagent(self, registry):
        """Test converting instances from AILF to Kagent."""
        # Create AILF instances
        ailf_profile = self.AILFProfile(
            user_id="user123",
            display_name="Test User",
            bio="This is a test profile"
        )
        
        # Convert to Kagent
        kagent_profile = registry.convert_to_kagent(ailf_profile)
        
        # Check conversion
        assert isinstance(kagent_profile, self.KagentProfile)
        assert kagent_profile.id == "user123"
        assert kagent_profile.name == "Test User"
        assert kagent_profile.biography == "This is a test profile"
    
    def test_convert_to_ailf(self, registry):
        """Test converting instances from Kagent to AILF."""
        # Create Kagent instances
        kagent_address = self.KagentAddress(
            street_address="123 Main St",
            city_name="Springfield",
            postal_code="12345"
        )
        
        # Convert to AILF
        ailf_address = registry.convert_to_ailf(kagent_address)
        
        # Check conversion
        assert isinstance(ailf_address, self.AILFAddress)
        assert ailf_address.street == "123 Main St"
        assert ailf_address.city == "Springfield"
        assert ailf_address.zip_code == "12345"
    
    def test_missing_mapping(self, registry):
        """Test error handling for missing mappings."""
        # Define a schema with no mapping
        class UnmappedSchema(BaseModel):
            field: str
            
        # Check that appropriate errors are raised
        with pytest.raises(ValueError, match="No registered mapping"):
            registry.get_kagent_schema(UnmappedSchema)
            
        with pytest.raises(ValueError, match="No registered mapping"):
            registry.convert_to_kagent(UnmappedSchema(field="test"))


class TestNestedSchemas:
    """Test suite for handling nested schemas."""
    
    # Test schema definitions with nesting
    class AILFAddress(BaseModel):
        street: str
        city: str
        country: str = "USA"
        
    class AILFUser(BaseModel):
        name: str
        email: str
        address: "TestNestedSchemas.AILFAddress"
        
    class KagentLocation(BaseModel):
        street_address: str
        city_name: str
        country_code: str = "USA"
        
    class KagentUser(BaseModel):
        full_name: str
        contact: str
        location: "TestNestedSchemas.KagentLocation"
    
    @pytest.fixture
    def nested_registry(self):
        """Create a registry with nested schema mappings."""
        registry = SchemaRegistry()
        
        # Register nested schemas
        registry.register_mapping(
            self.AILFAddress,
            self.KagentLocation,
            {
                "street": "street_address",
                "city": "city_name",
                "country": "country_code"
            }
        )
        
        registry.register_mapping(
            self.AILFUser,
            self.KagentUser,
            {
                "name": "full_name",
                "email": "contact",
                "address": "location"
            }
        )
        
        return registry
    
    def test_nested_schema_conversion(self, nested_registry):
        """Test conversion of instances with nested schemas."""
        # Create a nested AILF instance
        address = self.AILFAddress(street="456 Oak St", city="Portland")
        user = self.AILFUser(name="Alice", email="alice@example.com", address=address)
        
        # Convert to Kagent
        kagent_user = nested_registry.convert_to_kagent(user)
        
        # Check top-level fields
        assert kagent_user.full_name == "Alice"
        assert kagent_user.contact == "alice@example.com"
        
        # Check nested fields
        assert kagent_user.location.street_address == "456 Oak St"
        assert kagent_user.location.city_name == "Portland"
        assert kagent_user.location.country_code == "USA"  # Default value
