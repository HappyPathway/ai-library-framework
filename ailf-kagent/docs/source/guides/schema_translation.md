# Schema Translation

This guide explains how to translate between AILF and Kagent schemas.

## Basic Schema Mapping

The `map_ailf_to_kagent_schema` and `map_kagent_to_ailf_schema` functions convert between schema types:

```python
from ailf_kagent import map_ailf_to_kagent_schema, map_kagent_to_ailf_schema
from ailf.schemas import AILFUserProfile
from kagent.schema import KagentUserSchema

# Convert AILF schema to Kagent schema
kagent_user_schema = map_ailf_to_kagent_schema(AILFUserProfile)

# Convert Kagent schema to AILF schema
ailf_user_schema = map_kagent_to_ailf_schema(KagentUserSchema)
```

## Instance Conversion

The `convert_instance_to_schema` function transforms data between schema instances:

```python
from ailf_kagent import convert_instance_to_schema

# Convert an AILF model instance to a Kagent model instance
ailf_user = AILFUserProfile(name="Alice", email="alice@example.com")
kagent_user = convert_instance_to_schema(ailf_user, kagent_user_schema)

# Convert a Kagent model instance to an AILF model instance
kagent_response = KagentResponseSchema(status="success", data={"result": 42})
ailf_response = convert_instance_to_schema(kagent_response, ailf_response_schema)
```

## SchemaRegistry

For more complex applications, use the `SchemaRegistry` to manage schema mappings:

```python
from ailf_kagent import SchemaRegistry

# Create a schema registry
registry = SchemaRegistry()

# Register schema mappings
registry.register_mapping(AILFUserProfile, KagentUserSchema)
registry.register_mapping(AILFResponseModel, KagentResponseSchema)
registry.register_mapping(AILFQueryModel, KagentQuerySchema)

# Convert instances using the registry
kagent_user = registry.convert_to_kagent(ailf_user)
ailf_response = registry.convert_to_ailf(kagent_response)
```

## Custom Field Mapping

For complex field mappings, you can specify custom field conversions:

```python
from pydantic import BaseModel, Field

class AILFAddress(BaseModel):
    street: str
    city: str
    zipcode: str
    country: str = "USA"

class KagentLocation(BaseModel):
    address_line: str
    city_name: str
    postal_code: str
    country_code: str

# Create a registry with custom field mapping
registry = SchemaRegistry()
registry.register_mapping(
    AILFAddress, 
    KagentLocation,
    field_mappings={
        "street": "address_line",
        "city": "city_name",
        "zipcode": "postal_code",
        "country": "country_code"
    }
)

# Convert instances
ailf_addr = AILFAddress(street="123 Main St", city="Springfield", zipcode="12345")
kagent_loc = registry.convert_to_kagent(ailf_addr)
```

## Handling Nested Schemas

The schema translation functions handle nested schemas automatically:

```python
class AILFUserWithAddress(BaseModel):
    name: str
    email: str
    address: AILFAddress

class KagentUserWithLocation(BaseModel):
    full_name: str
    email_address: str
    location: KagentLocation

# Register the parent models and their nested components
registry.register_mapping(
    AILFUserWithAddress,
    KagentUserWithLocation,
    field_mappings={
        "name": "full_name",
        "email": "email_address",
        "address": "location"
    }
)

# The nested address/location will be converted correctly
ailf_user = AILFUserWithAddress(
    name="Alice",
    email="alice@example.com",
    address=AILFAddress(street="123 Main St", city="Springfield", zipcode="12345")
)
kagent_user = registry.convert_to_kagent(ailf_user)
```

## Best Practices

1. **Consistent Field Naming**: Use consistent naming conventions when possible
2. **Schema Documentation**: Document schema mappings for clarity
3. **Validation**: Validate data after conversion when necessary
4. **Minimal Conversion**: Convert only when needed to avoid overhead
5. **Registry Management**: For large applications, organize schema registries by domain
