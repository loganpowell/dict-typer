from dict_typer import get_type_definitions


def test_empty_dict_makes_all_fields_optional():
    """Test that providing an empty dict with a complex dict makes all fields (including nested) optional."""
    
    complex_dict = {
        'name': 'John',
        'age': 30,
        'address': {
            'street': '123 Main St',
            'city': 'NYC',
            'country': 'USA'
        },
        'contacts': [
            {
                'type': 'email',
                'value': 'john@example.com'
            }
        ]
    }
    empty_dict = {}
    
    result = get_type_definitions([complex_dict, empty_dict])
    
    # Check that all top-level fields are optional
    assert "name: Optional[str]" in result
    assert "age: Optional[int]" in result
    assert "address: Optional[Address]" in result
    assert "contacts: Optional[List[ContactsItem0]]" in result
    
    # Check that nested Address fields are optional
    assert "street: Optional[str]" in result
    assert "city: Optional[str]" in result
    assert "country: Optional[str]" in result
    
    # Check that nested ContactsItem0 fields are optional
    assert "type: Optional[str]" in result
    assert "value: Optional[str]" in result
    
    # Check imports include Optional
    assert "Optional" in result
    
    # Should be treated as examples, not as a list union
    assert "should_treat_as_examples" not in result  # Internal function shouldn't appear


def test_empty_dict_with_deeply_nested_structure():
    """Test empty dict functionality with deeply nested structures."""
    
    complex_dict = {
        'user': {
            'profile': {
                'personal': {
                    'name': 'John',
                    'age': 30
                },
                'settings': {
                    'theme': 'dark',
                    'notifications': True
                }
            }
        }
    }
    empty_dict = {}
    
    result = get_type_definitions([complex_dict, empty_dict])
    
    # Check that all levels are optional
    assert "user: Optional[User]" in result
    assert "profile: Optional[Profile]" in result
    assert "personal: Optional[Personal]" in result
    assert "settings: Optional[Settings]" in result
    
    # Check that leaf fields are optional
    assert "name: Optional[str]" in result
    assert "age: Optional[int]" in result
    assert "theme: Optional[str]" in result
    assert "notifications: Optional[bool]" in result


def test_multiple_non_empty_dicts_with_one_empty():
    """Test that one empty dict among multiple non-empty dicts makes all fields optional."""
    
    dict1 = {'a': 1, 'b': 'hello'}
    dict2 = {'a': 2, 'c': 'world'}
    empty_dict = {}
    
    result = get_type_definitions([dict1, dict2, empty_dict])
    
    # All fields should be optional due to empty dict
    assert "a: Optional[Union[int]]" in result or "a: Optional[int]" in result
    assert "b: Optional[str]" in result
    assert "c: Optional[str]" in result


def test_no_empty_dict_normal_behavior():
    """Test that without empty dict, the normal optional field inference works."""
    
    # Use examples that have shared core fields and partial fields
    dict1 = {'a': 1, 'b': 'hello', 'shared': 'core'}
    dict2 = {'a': 2, 'b': 'world', 'shared': 'core'}  # 'a' and 'shared' in both, 'b' in both
    dict3 = {'a': 3, 'shared': 'core', 'c': 'optional'}  # 'c' only in this one
    
    result = get_type_definitions([dict1, dict2, dict3])
    
    # 'a' and 'shared' should not be optional (appears in all)
    assert "a: int" in result
    assert "shared: str" in result
    # 'b' and 'c' should be optional (appear in some but not all)
    assert "b: Optional[str]" in result
    assert "c: Optional[str]" in result


def test_single_empty_dict():
    """Test that a single empty dict works correctly."""
    
    result = get_type_definitions({})
    
    # Should create an empty TypedDict
    assert "class Root(TypedDict):" in result
    assert "pass" in result


def test_only_empty_dicts():
    """Test that multiple empty dicts work correctly."""
    
    result = get_type_definitions([{}, {}])
    
    # Should be treated as a list of empty dicts
    assert "Root = List[" in result or "class Root(TypedDict):" in result

