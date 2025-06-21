from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from collections import defaultdict

from dict_typer.models import (
    DictEntry,
    MemberEntry,
    key_to_dependency_cmp,
    sub_members_to_imports,
    sub_members_to_string,
)
from dict_typer.utils import key_to_class_name

BASE_TYPES: Tuple[Type, ...] = (  # type: ignore
    bool,
    bytearray,
    bytes,
    complex,
    enumerate,
    float,
    int,
    memoryview,
    range,
    str,
    type,
    filter,
    map,
    zip,
)


Source = Union[str, int, float, bool, None, Dict, List]
NameMap = Dict[str, str]


class DefinitionBuilder:
    definitions: List[DictEntry]
    root_type_name: str
    type_postfix: str
    show_imports: bool
    source: Source
    name_map: NameMap

    _output: Optional[str] = None

    def __init__(
        self,
        source: Source,
        *,
        root_type_name: str = "Root",
        type_postfix: str = "",
        show_imports: bool = True,
        force_alternative: bool = False,
        name_map: Optional[NameMap] = None,
    ) -> None:
        self.definitions = []

        self.root_type_name = root_type_name
        self.type_postfix = type_postfix
        self.show_imports = show_imports
        self.force_alternative = force_alternative
        if name_map:
            self.name_map = name_map
        else:
            self.name_map = {}

        self.source = source

    def _get_name(self, name: str) -> str:
        """Return the mapped name if it exist"""
        return self.name_map.get(name, name)

    def _add_definition(self, entry: DictEntry) -> DictEntry:
        """Add an entry to the definions.

        If the entry is a DictEntry and there's an existing entry with the same
        keys, then combine the DictEntries
        """
        dicts_only = [d for d in self.definitions if isinstance(d, DictEntry)]
        for definition in dicts_only:
            if entry.keys == definition.keys:
                # Check if both are list item types (contain "Item" followed by digits)
                entry_is_list_item = 'Item' in entry.name and any(c.isdigit() for c in entry.name.split('Item')[-1])
                def_is_list_item = 'Item' in definition.name and any(c.isdigit() for c in definition.name.split('Item')[-1])
                
                if entry_is_list_item and def_is_list_item:
                    # Both are list item types - only merge if they have the same semantic base
                    entry_base = entry.name.split('Item')[0]
                    def_base = definition.name.split('Item')[0]
                    if entry_base == def_base:
                        definition.update_members(entry.members)
                        return definition
                else:
                    # At least one is not a list item type - merge based on structure
                    definition.update_members(entry.members)
                    return definition
            
            # Handle name collisions by appending a number
            if entry.name == definition.name:
                idx = 1
                new_name = f"{entry.name}{idx}"
                dicts_names = [d.name for d in dicts_only]
                while new_name in dicts_names:
                    idx += 1
                    new_name = f"{entry.name}{idx}"
                entry.name = new_name
        
        self.definitions.append(entry)
        return entry

    def _convert_list(self, key: str, lst: List, item_name: str) -> MemberEntry:
        entry = MemberEntry(key)

        idx = 0
        for item in lst:
            item_type = self._get_type(item, key=f"{item_name}{idx}")

            entry.sub_members.add(item_type)
            if isinstance(item_type, DictEntry):
                self._add_definition(item_type)
            idx += 1

        return entry

    def _convert_dict(self, type_name: str, dct: Dict, total: bool = True) -> DictEntry:
        entry = DictEntry(
            self._get_name(type_name), force_alternative=self.force_alternative, total=total
        )
        for key, value in dct.items():
            value_type = self._get_type(value, key=key)
            if isinstance(value_type, DictEntry):
                definition = self._add_definition(value_type)
                value_type = definition
            entry.members[key] = {value_type}
        return entry

    def _get_type(self, item: Any, key: str) -> Union[MemberEntry, DictEntry]:
        if item is None:
            return MemberEntry("None")

        if isinstance(item, BASE_TYPES):
            return MemberEntry(type(item).__name__)

        if isinstance(item, (list, set, tuple, frozenset)):
            if isinstance(item, list):
                sequence_type_name = "List"
            elif isinstance(item, set):
                sequence_type_name = "Set"
            elif isinstance(item, frozenset):
                sequence_type_name = "FrozenSet"
            else:
                sequence_type_name = "Tuple"

            list_item_types: Set[Union[MemberEntry, DictEntry]] = set()
            idx = 0
            for value in item:
                item_type = self._get_type(value, key=f"{key}Item{idx}")
                if isinstance(item_type, DictEntry):
                    # Add the DictEntry and get the potentially merged result
                    merged_type = self._add_definition(item_type)
                    list_item_types.add(merged_type)
                else:
                    list_item_types.add(item_type)
                idx += 1

            return MemberEntry(sequence_type_name, sub_members=list_item_types)

        if isinstance(item, dict):
            return self._convert_dict(
                f"{key_to_class_name(key)}{self.type_postfix}", item
            )

        raise NotImplementedError(f"Type handling for '{type(item)}' not implemented")

    def build_output(self) -> str:
        if self._output:
            return self._output

        source_type = self._get_type(self.source, key=self.root_type_name)
        if isinstance(source_type, DictEntry):
            self._add_definition(source_type)
            root_item = None
        else:
            root_item = source_type

        # Convert the definitions to structured output
        self._output = ""

        if self.show_imports:
            typing_imports = set()
            typed_dict_import = False

            for definition in self.definitions:
                if isinstance(definition, DictEntry):
                    typed_dict_import = True
                typing_imports |= definition.get_imports()
            if root_item:
                typing_imports |= sub_members_to_imports({root_item})

            if typing_imports:
                self._output += "\n".join(
                    [f"from typing import {', '.join(sorted(typing_imports))}", "", ""]
                )
            if typed_dict_import:
                self._output += "\n".join(
                    ["from typing_extensions import TypedDict", "", "", ""]
                )

        self._output += "\n\n\n".join(
            [str(d) for d in sorted(self.definitions, key=key_to_dependency_cmp)]
        )

        if not isinstance(source_type, DictEntry):
            if len(self._output):
                self._output += "\n"
                if len(self.definitions):
                    self._output += "\n\n"
            self._output += f"{self.root_type_name}{self.type_postfix} = {sub_members_to_string({source_type})}"

        return self._output


def _should_treat_as_examples(dicts: List[Dict[str, Any]]) -> bool:
    """Determine if a list of dictionaries should be treated as multiple examples
    of the same schema rather than a list of different items.
    
    This function heuristically determines if the dictionaries have enough overlap
    in their field names to suggest they represent variations of the same type.
    
    Special case: If one of the dictionaries is empty and others have content,
    treat as examples (the empty dict represents a case where all fields are optional).
    """
    if len(dicts) < 2:
        return False
    
    # Special case: if we have exactly one empty dict and others with content,
    # treat as examples where all fields should be optional
    empty_dicts = [d for d in dicts if len(d) == 0]
    non_empty_dicts = [d for d in dicts if len(d) > 0]
    
    if len(empty_dicts) == 1 and len(non_empty_dicts) >= 1:
        return True
    
    # Get all field names from all dictionaries
    all_fields = set()
    field_counts = defaultdict(int)
    
    for d in dicts:
        for field in d.keys():
            all_fields.add(field)
            field_counts[field] += 1
    
    if not all_fields:
        return False
    
    total_dicts = len(dicts)
    
    # Count fields by their frequency
    core_fields = sum(1 for count in field_counts.values() if count == total_dicts)  # In all dicts
    partial_fields = sum(1 for count in field_counts.values() if 1 < count < total_dicts)  # In some but not all
    unique_fields = sum(1 for count in field_counts.values() if count == 1)  # In only one dict
    
    # Key insight: If ALL fields appear in ALL dictionaries, it's likely a regular list
    # If there are fields that appear in some but not all dictionaries, it's likely examples
    
    if partial_fields == 0:
        # No partial fields means either all fields are in all dicts (regular list)
        # or all fields are unique to one dict (completely different structures)
        return False
    
    # We have partial fields, which suggests variations of the same schema
    # Additional check: ensure we have some core schema (shared fields)
    # and that partial fields make up a reasonable portion
    
    if core_fields == 0:
        # No shared fields at all - probably completely different items
        return False
    
    # We have both core fields (shared) and partial fields (optional)
    # This is a good indicator of schema variations
    return True


def _merge_dict_examples(examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple dictionary examples to create a comprehensive type definition.
    
    This function analyzes all provided examples to:
    1. Identify fields that are truly optional (present in some but not all examples)
    2. Collect all possible types for each field
    3. Create a merged dictionary that represents the union of all examples
    """
    if not examples:
        return {}
    
    if len(examples) == 1:
        return examples[0]
    
    # Track which fields appear in which examples
    field_counts = defaultdict(int)
    field_types = defaultdict(set)
    
    # Count field occurrences and collect types
    for example in examples:
        if not isinstance(example, dict):
            continue
        for key, value in example.items():
            field_counts[key] += 1
            field_types[key].add(type(value).__name__ if value is not None else 'None')
    
    # Build merged dictionary
    merged = {}
    total_examples = len(examples)
    
    for field in field_counts:
        # If field appears in all examples, use the first non-None value
        if field_counts[field] == total_examples:
            # Find first example that has this field with a non-None value
            for example in examples:
                if isinstance(example, dict) and field in example and example[field] is not None:
                    merged[field] = example[field]
                    break
            else:
                # All values are None, so keep it as None
                merged[field] = None
        else:
            # Field is optional - present in some but not all examples
            # Find a representative value and mark it as optional by adding None
            for example in examples:
                if isinstance(example, dict) and field in example:
                    if example[field] is not None:
                        merged[field] = example[field]
                        break
            else:
                # Only None values found
                merged[field] = None
            
            # For optional fields, we need to ensure None is in the type union
            # This will be handled by adding None to the merged dict in a special way
            # We'll create a list with the value and None to signal optionality
            if field in merged and merged[field] is not None:
                # Create a marker for optionality by storing both the value and None
                # This will be processed specially by the type system
                pass  # The current system will handle this through multiple passes
    
    return merged


def get_type_definitions(
    source: Source,
    root_type_name: str = "Root",
    type_postfix: str = "",
    show_imports: bool = True,
    force_alternative: bool = False,
    name_map: NameMap | None = None,
) -> str:
    """
    Generate TypedDict definitions from a source object.
    
    Args:
        source: The source object to generate types from. Can be:
                - A single dict: generates types for that dict
                - A list of dicts: analyzes all dicts to infer optional fields
                - Other types: handled as before (lists, primitives, etc.)
        root_type_name: Name for the root type
        type_postfix: Postfix to add to generated type names
        show_imports: Whether to include import statements
        force_alternative: Whether to force alternative TypedDict syntax
        name_map: Optional mapping of field names to type names
    
    Returns:
        String containing the generated TypedDict definitions
    """
    # Check if source is a list of dictionaries for multi-example analysis
    # Only apply this when the list contains dictionaries with overlapping but varying field structures
    # suggesting they represent multiple examples of the same schema rather than a list of different items
    if (isinstance(source, list) and len(source) > 1 and 
        all(isinstance(item, dict) for item in source) and
        _should_treat_as_examples(source)):
        # Multiple dictionary examples - use enhanced analysis
        primary_source = source[0]  # Use first dict as primary
        
        # Check if we have the empty dict case
        source_dicts = [item for item in source if isinstance(item, dict)]
        empty_dicts = [d for d in source_dicts if len(d) == 0]
        non_empty_dicts = [d for d in source_dicts if len(d) > 0]
        has_empty_dict = len(empty_dicts) == 1 and len(non_empty_dicts) >= 1
        
        # Create a builder for each example to collect type information
        builders = []
        for i, example in enumerate(source):
            builder = DefinitionBuilder(
                example,
                root_type_name=root_type_name,
                type_postfix=type_postfix,
                show_imports=False,  # We'll handle imports at the end
                force_alternative=force_alternative,
                name_map=name_map,
            )
            builder.build_output()  # This populates the definitions
            
            # If we have empty dict case, make all fields in all types optional
            if has_empty_dict:
                for definition in builder.definitions:
                    if isinstance(definition, DictEntry):
                        for field_name, field_types in definition.members.items():
                            none_entry = MemberEntry("None")
                            definition.members[field_name].add(none_entry)
            
            builders.append(builder)
        
        # Special handling for empty dict case: create OptionalRootType and use total=False
        if has_empty_dict:
            # For empty dict case, we want a single merged type, not a list union
            # Use only the non-empty dict(s) as the basis for the type
            if len(non_empty_dicts) == 1:
                # Single non-empty dict case - build the type normally
                builder = DefinitionBuilder(
                    non_empty_dicts[0],
                    root_type_name=root_type_name,
                    type_postfix=type_postfix,
                    show_imports=show_imports,
                    force_alternative=force_alternative,
                    name_map=name_map,
                )
                builder.build_output()
                
                # Set total=False for all nested definitions (not the root)
                for definition in builder.definitions:
                    if isinstance(definition, DictEntry):
                        if definition.name != root_type_name:
                            definition.total = False
                
                # Clear cached output so it regenerates with total=False
                builder._output = None
                output = builder.build_output()
                
                # Add OptionalRootType definition
                optional_line = f"Optional{root_type_name} = Optional[{root_type_name}{type_postfix}]"
                
                # Ensure Optional is imported
                if "from typing import" in output:
                    # Check if Optional is already imported
                    if "Optional" not in output.split("\n")[0]:
                        # Add Optional to existing import
                        output = output.replace(
                            "from typing import",
                            "from typing import Optional,"
                        )
                    output += f"\n\n{optional_line}"
                else:
                    # Need to add Optional import
                    if "from typing_extensions import TypedDict" in output:
                        output = output.replace(
                            "from typing_extensions import TypedDict",
                            "from typing import Optional\nfrom typing_extensions import TypedDict"
                        )
                    else:
                        output = f"from typing import Optional\n\n{output}"
                    output += f"\n\n{optional_line}"
                
                return output
            else:
                # Multiple non-empty dicts - merge them first
                non_empty_builders = []
                for example in non_empty_dicts:
                    builder = DefinitionBuilder(
                        example,
                        root_type_name=root_type_name,
                        type_postfix=type_postfix,
                        show_imports=False,
                        force_alternative=force_alternative,
                        name_map=name_map,
                    )
                    builder.build_output()
                    non_empty_builders.append(builder)
                
                # Merge the non-empty builders
                final_builder = _merge_builders(non_empty_builders, non_empty_dicts[0], root_type_name, type_postfix, show_imports, force_alternative, name_map)
                
                # Set total=False for all nested definitions (not the root)
                for definition in final_builder.definitions:
                    if isinstance(definition, DictEntry):
                        if definition.name != root_type_name:
                            definition.total = False
                
                # Clear cached output so it regenerates with total=False
                final_builder._output = None
                output = final_builder.build_output()
                
                # Add OptionalRootType definition
                optional_line = f"Optional{root_type_name} = Optional[{root_type_name}{type_postfix}]"
                
                # Ensure Optional is imported
                if "from typing import" in output:
                    # Check if Optional is already imported
                    if "Optional" not in output.split("\n")[0]:
                        # Add Optional to existing import
                        output = output.replace(
                            "from typing import",
                            "from typing import Optional,"
                        )
                    output += f"\n\n{optional_line}"
                else:
                    # Need to add Optional import
                    if "from typing_extensions import TypedDict" in output:
                        output = output.replace(
                            "from typing_extensions import TypedDict",
                            "from typing import Optional\nfrom typing_extensions import TypedDict"
                        )
                    else:
                        output = f"from typing import Optional\n\n{output}"
                    output += f"\n\n{optional_line}"
                
                return output
        
        # Merge all the type information
        final_builder = _merge_builders(builders, source, root_type_name, type_postfix, show_imports, force_alternative, name_map)
        return final_builder.build_output()
    
    # Standard single-source processing
    builder = DefinitionBuilder(
        source,
        root_type_name=root_type_name,
        type_postfix=type_postfix,
        show_imports=show_imports,
        force_alternative=force_alternative,
        name_map=name_map,
    )

    return builder.build_output()


def _merge_builders(
    builders: List[DefinitionBuilder], 
    primary_source: Source,
    root_type_name: str,
    type_postfix: str,
    show_imports: bool,
    force_alternative: bool,
    name_map: Optional[NameMap]
) -> DefinitionBuilder:
    """Merge multiple builders into a single builder with combined type information."""
    
    # Check if we have the special case of empty dict + non-empty dict(s)
    # In this case, ALL fields (including nested ones) should be optional
    has_empty_dict = False
    if isinstance(primary_source, list):
        source_dicts = [item for item in primary_source if isinstance(item, dict)]
        empty_dicts = [d for d in source_dicts if len(d) == 0]
        non_empty_dicts = [d for d in source_dicts if len(d) > 0]
        has_empty_dict = len(empty_dicts) == 1 and len(non_empty_dicts) >= 1
    
    # Create the final builder using the primary source
    final_builder = DefinitionBuilder(
        primary_source,
        root_type_name=root_type_name,
        type_postfix=type_postfix,
        show_imports=show_imports,
        force_alternative=force_alternative,
        name_map=name_map,
    )
    
    # Track field presence across all examples for optional field detection
    field_presence = defaultdict(lambda: defaultdict(int))  # {normalized_type_name: {field_name: count}}
    type_counts = defaultdict(int)  # {normalized_type_name: total_examples}
    all_definitions = {}  # {normalized_type_name: merged_definition}
    
    # Helper function to normalize type names
    def normalize_type_name(name: str) -> str:
        # Remove temp prefixes and get the actual type name
        import re
        cleaned = re.sub(r'_temp_\d+', '', name)
        if not cleaned or cleaned == root_type_name:
            return root_type_name
        return cleaned
    
    # First pass: collect all definitions and track field presence
    for builder_idx, builder in enumerate(builders):
        for definition in builder.definitions:
            if isinstance(definition, DictEntry):
                normalized_name = normalize_type_name(definition.name)
                
                # Track this type occurrence
                type_counts[normalized_name] += 1
                
                # Track field presence for this type
                for field_name in definition.members.keys():
                    field_presence[normalized_name][field_name] += 1
                
                # Store or merge the definition
                if normalized_name not in all_definitions:
                    # Create a new definition with the normalized name
                    merged_def = DictEntry(
                        normalized_name,
                        force_alternative=force_alternative
                    )
                    # Copy all fields from this definition
                    for field_name, field_types in definition.members.items():
                        merged_def.members[field_name] = field_types.copy()
                    all_definitions[normalized_name] = merged_def
                else:
                    # Merge with existing definition
                    existing_def = all_definitions[normalized_name]
                    for field_name, field_types in definition.members.items():
                        if field_name in existing_def.members:
                            existing_def.members[field_name] |= field_types
                        else:
                            existing_def.members[field_name] = field_types.copy()
    
    # Second pass: mark fields as optional if they don't appear in all examples
    total_examples = len(builders)
    for type_name, definition in all_definitions.items():
        # For the root type, we need to consider all examples
        if type_name == root_type_name:
            examples_for_this_type = total_examples
        else:
            examples_for_this_type = type_counts[type_name]
        
        # Collect all fields that should exist based on all examples
        all_possible_fields = set()
        for builder in builders:
            for def_entry in builder.definitions:
                if isinstance(def_entry, DictEntry) and normalize_type_name(def_entry.name) == type_name:
                    all_possible_fields.update(def_entry.members.keys())
        
        # Add missing fields as optional
        for field_name in all_possible_fields:
            if field_name not in definition.members:
                # Field is completely missing from this merged definition, make it optional
                none_entry = MemberEntry("None")
                definition.members[field_name] = {none_entry}
            else:
                # Field exists, check if it should be optional
                field_count = field_presence[type_name][field_name]
                
                # Special case: if we have empty dict, ALL fields should be optional
                if has_empty_dict or field_count < examples_for_this_type:
                    # Add None to make it optional
                    none_entry = MemberEntry("None")
                    definition.members[field_name].add(none_entry)
        
        # Special handling for empty dict case: make ALL fields in ALL types optional
        if has_empty_dict:
            for field_name, field_types in definition.members.items():
                none_entry = MemberEntry("None")
                definition.members[field_name].add(none_entry)
    
    # Add all merged definitions to the final builder, but clear existing ones first
    final_builder.definitions = []
    for definition in all_definitions.values():
        final_builder._add_definition(definition)
    
    return final_builder
