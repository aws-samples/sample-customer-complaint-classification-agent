"""Property-based tests for JSON extraction completeness.

Feature: codebase-cleanup, Property 2: JSON Extraction Completeness
"""

import json

from hypothesis import given, settings, strategies as st

from src.complaints_agent.utils.json_parser import find_json_objects


simple_json_value_strategy = st.one_of(
    st.text(min_size=0, max_size=50).map(lambda s: s.replace('"', '\\"').replace('\\', '\\\\')),
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)

simple_key_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_'),
    min_size=1,
    max_size=20
).filter(lambda x: x.strip() and x[0].isalpha())


@st.composite
def simple_json_object_strategy(draw):
    num_keys = draw(st.integers(min_value=1, max_value=5))
    keys = draw(st.lists(simple_key_strategy, min_size=num_keys, max_size=num_keys, unique=True))
    values = draw(st.lists(simple_json_value_strategy, min_size=num_keys, max_size=num_keys))
    return dict(zip(keys, values))


@st.composite
def nested_json_object_strategy(draw):
    base = draw(simple_json_object_strategy())
    if draw(st.booleans()):
        nested_key = draw(simple_key_strategy)
        nested_obj = draw(simple_json_object_strategy())
        base[nested_key] = nested_obj
    return base


prose_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), blacklist_characters='{}[]"\\'),
    min_size=0,
    max_size=100
)


class TestJsonExtractionCompleteness:
    """
    Feature: codebase-cleanup, Property 2: JSON Extraction Completeness

    *For any* text containing one or more valid JSON objects (whether as plain JSON,
    within markdown code blocks, or embedded in prose), find_json_objects() SHALL
    return all valid JSON objects found, correctly handling nested braces and
    escaped characters.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    @settings(max_examples=10)
    @given(json_obj=simple_json_object_strategy())
    def test_extracts_plain_json(self, json_obj: dict):
        """Plain JSON objects are extracted correctly."""
        json_str = json.dumps(json_obj)
        result = find_json_objects(json_str)
        assert len(result) >= 1
        assert json_obj in result

    @settings(max_examples=10)
    @given(json_obj=simple_json_object_strategy())
    def test_extracts_json_from_markdown_code_block(self, json_obj: dict):
        """JSON within markdown code blocks is extracted correctly."""
        json_str = json.dumps(json_obj)
        text = f"Here is some JSON:\n```json\n{json_str}\n```\nEnd of JSON."
        result = find_json_objects(text)
        assert len(result) >= 1
        assert json_obj in result

    @settings(max_examples=10)
    @given(
        json_obj=simple_json_object_strategy(),
        prefix=prose_strategy,
        suffix=prose_strategy
    )
    def test_extracts_json_embedded_in_prose(self, json_obj: dict, prefix: str, suffix: str):
        """JSON embedded in prose text is extracted correctly."""
        json_str = json.dumps(json_obj)
        text = f"{prefix} {json_str} {suffix}"
        result = find_json_objects(text)
        assert len(result) >= 1
        assert json_obj in result

    @settings(max_examples=10)
    @given(json_obj=nested_json_object_strategy())
    def test_handles_nested_braces(self, json_obj: dict):
        """Nested JSON objects with nested braces are extracted correctly."""
        json_str = json.dumps(json_obj)
        result = find_json_objects(json_str)
        assert len(result) >= 1
        assert json_obj in result

    @settings(max_examples=10)
    @given(
        key=simple_key_strategy,
        value=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
    )
    def test_handles_escaped_characters_in_strings(self, key: str, value: str):
        """JSON with escaped characters in string values is handled correctly."""
        escaped_value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        json_obj = {key: escaped_value}
        json_str = json.dumps(json_obj)
        result = find_json_objects(json_str)
        assert len(result) >= 1
        found = False
        for r in result:
            if key in r:
                found = True
                break
        assert found

    @settings(max_examples=10)
    @given(
        obj1=simple_json_object_strategy(),
        obj2=simple_json_object_strategy()
    )
    def test_extracts_multiple_json_objects(self, obj1: dict, obj2: dict):
        """Multiple JSON objects in text are all extracted."""
        json_str1 = json.dumps(obj1)
        json_str2 = json.dumps(obj2)
        text = f"First object: {json_str1}\nSecond object: {json_str2}"
        result = find_json_objects(text)
        assert obj1 in result
        assert obj2 in result
        if obj1 != obj2:
            assert len(result) >= 2
        else:
            assert len(result) >= 1

    @settings(max_examples=10)
    @given(
        obj1=simple_json_object_strategy(),
        obj2=simple_json_object_strategy()
    )
    def test_extracts_multiple_json_from_markdown_blocks(self, obj1: dict, obj2: dict):
        """Multiple JSON objects in separate markdown blocks are all extracted."""
        json_str1 = json.dumps(obj1)
        json_str2 = json.dumps(obj2)
        text = f"```json\n{json_str1}\n```\nSome text\n```json\n{json_str2}\n```"
        result = find_json_objects(text)
        assert obj1 in result
        assert obj2 in result
        if obj1 != obj2:
            assert len(result) >= 2
        else:
            assert len(result) >= 1

    @settings(max_examples=10)
    @given(json_obj=simple_json_object_strategy())
    def test_deduplicates_identical_json_objects(self, json_obj: dict):
        """Identical JSON objects appearing multiple times are deduplicated."""
        json_str = json.dumps(json_obj)
        text = f"{json_str}\n{json_str}\n{json_str}"
        result = find_json_objects(text)
        count = sum(1 for r in result if r == json_obj)
        assert count == 1

    @settings(max_examples=10)
    @given(st.text(min_size=0, max_size=200).filter(lambda x: '{' not in x))
    def test_returns_empty_list_for_no_json(self, text: str):
        """Text without JSON objects returns empty list."""
        result = find_json_objects(text)
        assert result == []

    @settings(max_examples=10)
    @given(
        json_obj=simple_json_object_strategy(),
        prefix=prose_strategy,
        middle=prose_strategy,
        suffix=prose_strategy
    )
    def test_extracts_json_mixed_with_prose_and_markdown(
        self, json_obj: dict, prefix: str, middle: str, suffix: str
    ):
        """JSON in mixed prose and markdown format is extracted correctly."""
        json_str = json.dumps(json_obj)
        text = f"{prefix}\n```json\n{json_str}\n```\n{middle}\n{json_str}\n{suffix}"
        result = find_json_objects(text)
        assert len(result) >= 1
        assert json_obj in result

