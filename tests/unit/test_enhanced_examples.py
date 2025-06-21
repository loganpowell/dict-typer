from dict_typer import get_type_definitions


def test_basic_optional_field_inference():
    """Test basic optional field inference from multiple examples."""
    
    examples = [
        {
            "id": 1,
            "name": "John",
            "email": "john@example.com",
            "age": 30
        },
        {
            "id": 2,
            "name": "Jane",
            "email": "jane@example.com"
            # age missing - should make age optional
        },
        {
            "id": 3,
            "name": "Bob",
            "age": 25
            # email missing - should make email optional
        }
    ]
    
    result = get_type_definitions(examples)
    
    # Check that basic structure is correct
    assert "class Root(TypedDict):" in result
    assert "id: int" in result
    assert "name: str" in result
    
    # Check that optional fields are properly marked
    assert "email: Optional[str]" in result
    assert "age: Optional[int]" in result
    
    # Check imports
    assert "Optional" in result


def test_nested_optional_fields():
    """Test optional field inference in nested dictionaries."""
    
    examples = [
        {
            "user": {
                "id": 1,
                "profile": {
                    "name": "John",
                    "bio": "Developer"
                }
            },
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        },
        {
            "user": {
                "id": 2,
                "profile": {
                    "name": "Jane"
                    # bio missing
                }
            },
            "settings": {
                "theme": "light"
                # notifications missing
            }
        },
        {
            "user": {
                "id": 3,
                "profile": {
                    "name": "Bob",
                    "bio": "Designer"
                }
            }
            # settings completely missing
        }
    ]
    
    result = get_type_definitions(examples)
    
    # Check that nested types are created
    assert "class Profile(TypedDict):" in result
    assert "class Settings(TypedDict):" in result
    assert "class User(TypedDict):" in result
    
    # Check that optional fields in nested structures are marked
    assert "bio: Optional[str]" in result
    assert "notifications: Optional[bool]" in result
    
    # Check that the settings field itself becomes optional
    assert "settings: Union[None, Settings]" in result or "settings: Optional[Settings]" in result


def test_mixed_types_with_optional():
    """Test optional fields with different types - this should be treated as examples."""
    
    # This example has core fields (most items have both value and data) with variations
    examples = [
        {
            "value": 42,
            "data": "string",
            "id": 1
        },
        {
            "value": 3.14,  # different numeric type
            "data": "another string",
            "id": 2
        },
        {
            "value": 100,
            "id": 3
            # data missing - makes it optional
        },
        {
            "data": "yet another string",
            "id": 4
            # value missing - makes it optional
        }
    ]
    
    result = get_type_definitions(examples)
    
    # Should be treated as examples because all have 'id' (core field) with optional variations
    assert "class Root(TypedDict):" in result
    assert "id: int" in result  # Core field should not be optional
    assert "value: Union[None, float, int]" in result or "value: Optional[Union[float, int]]" in result
    assert "data: Optional[str]" in result


def test_single_dict_provided():
    """Test that the function works normally when a single dict is provided."""
    
    source = {
        "id": 1,
        "name": "John",
        "email": "john@example.com"
    }
    
    result = get_type_definitions(source)
    
    # Should work exactly as before
    assert "class Root(TypedDict):" in result
    assert "id: int" in result
    assert "name: str" in result
    assert "email: str" in result
    
    # No Optional types should be present
    assert "Optional" not in result


def test_list_of_dicts_as_examples():
    """Test that a list of dicts is treated as multiple examples for optional field inference."""
    
    # When we provide a list of dicts, it should be treated as multiple examples
    source = [
        {"id": 1, "name": "Item 1", "active": True},
        {"id": 2, "name": "Item 2", "active": False},
        {"id": 3, "name": "Item 3"}  # active missing - should make it optional
    ]
    
    result = get_type_definitions(source)
    
    # Should create a TypedDict with optional fields, not a List type
    assert "class Root(TypedDict):" in result
    assert "id: int" in result
    assert "name: str" in result
    assert "active: Optional[bool]" in result  # Should be optional since missing in one example


def test_empty_list():
    """Test that empty list doesn't break anything."""
    
    source = []
    
    result = get_type_definitions(source)
    
    # Should handle empty lists gracefully
    assert "Root = List" in result


def test_examples_with_completely_different_structure():
    """Test behavior when examples have completely different structure."""
    
    # Examples with completely different fields (no shared fields)
    # Our heuristic should treat this as a regular list, not as examples
    examples = [
        {"id": 1, "name": "test"},
        {"foo": "bar"},
        {"baz": 123}
    ]
    
    result = get_type_definitions(examples)
    
    # Should be treated as a regular list since there are no shared fields
    assert "Root = List[Union[" in result
    assert "RootItem0" in result
    assert "RootItem1" in result
    assert "RootItem2" in result

