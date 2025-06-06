from unittest.mock import MagicMock
from unittest.mock import patch

from datacommons_client.endpoints.base import API
from datacommons_client.endpoints.node import NodeEndpoint
from datacommons_client.endpoints.response import NodeResponse
from datacommons_client.models.node import Arcs
from datacommons_client.models.node import Name
from datacommons_client.models.node import Node
from datacommons_client.models.node import NodeGroup
from datacommons_client.utils.names import DEFAULT_NAME_PROPERTY
from datacommons_client.utils.names import NAME_WITH_LANGUAGE_PROPERTY


def test_node_endpoint_initialization():
  """Test if the NodeEndpoint initializes correctly."""
  api_mock = MagicMock(spec=API)
  endpoint = NodeEndpoint(api=api_mock)

  assert endpoint.endpoint == "node"
  assert endpoint.api == api_mock


def test_node_endpoint_fetch():
  """Test the fetch method of NodeEndpoint."""
  api_mock = MagicMock(spec=API)
  api_mock.post.return_value = {"data": {"test_node": {"properties": ["name"]}}}

  endpoint = NodeEndpoint(api=api_mock)
  response = endpoint.fetch(node_dcids="test_node", expression="name")

  api_mock.post.assert_called_once_with(
      payload={
          "nodes": ["test_node"],
          "property": "name"
      },
      endpoint="node",
      all_pages=True,
      next_token=None,
  )
  assert isinstance(response, NodeResponse)
  assert "test_node" in response.data


def test_node_endpoint_fetch_property_labels():
  """Test fetch_property_labels method."""
  api_mock = MagicMock(spec=API)
  endpoint = NodeEndpoint(api=api_mock)
  endpoint.fetch = MagicMock(return_value=NodeResponse(
      data={"node1": {
          "properties": []
      }}))

  response = endpoint.fetch_property_labels(node_dcids="node1", out=False)
  endpoint.fetch.assert_called_once_with(node_dcids="node1",
                                         expression="<-",
                                         all_pages=True,
                                         next_token=None)
  assert isinstance(response, NodeResponse)
  assert "node1" in response.data


def test_node_endpoint_fetch_property_values_out():
  """Test fetch_property_values method with constraints and direction (out)"""

  api_mock = MagicMock(spec=API)
  api_mock.post.return_value = {"data": {"node1": {"properties": ["name"]}}}

  endpoint = NodeEndpoint(api=api_mock)
  response = endpoint.fetch_property_values(node_dcids="node1",
                                            properties="name",
                                            constraints="typeOf:City",
                                            out=True)

  expected_expression = "->name{typeOf:City}"
  api_mock.post.assert_called_once_with(
      payload={
          "nodes": ["node1"],
          "property": expected_expression
      },
      endpoint="node",
      all_pages=True,
      next_token=None,
  )
  assert isinstance(response, NodeResponse)
  assert "node1" in response.data


def test_node_endpoint_fetch_property_values_in():
  """Test fetch_property_values method with constraints and direction (in)"""

  api_mock = MagicMock(spec=API)
  api_mock.post.return_value = {"data": {"node1": {"properties": ["name"]}}}

  endpoint = NodeEndpoint(api=api_mock)
  response = endpoint.fetch_property_values(node_dcids="node1",
                                            properties="name",
                                            constraints="typeOf:City",
                                            out=False)

  expected_expression = "<-name{typeOf:City}"
  api_mock.post.assert_called_once_with(
      payload={
          "nodes": ["node1"],
          "property": expected_expression
      },
      endpoint="node",
      all_pages=True,
      next_token=None,
  )
  assert isinstance(response, NodeResponse)
  assert "node1" in response.data


def test_node_endpoint_fetch_all_classes():
  """Test fetch_all_classes method."""
  api_mock = MagicMock(spec=API)
  endpoint = NodeEndpoint(api=api_mock)
  endpoint.fetch_property_values = MagicMock(return_value=NodeResponse(
      data={"Class": {
          "arcs": {}
      }}))

  response = endpoint.fetch_all_classes()
  endpoint.fetch_property_values.assert_called_once_with(
      node_dcids="Class",
      properties="typeOf",
      out=False,
      all_pages=True,
      next_token=None,
  )
  assert isinstance(response, NodeResponse)
  assert "Class" in response.data


def test_node_endpoint_fetch_property_values_string_vs_list():
  """Test fetch_property_values with string and list expressions."""
  api_mock = MagicMock(spec=API)
  api_mock.post.return_value = {"data": {"node1": {"properties": ["name"]}}}

  endpoint = NodeEndpoint(api=api_mock)

  # String input
  response = endpoint.fetch_property_values(node_dcids="node1",
                                            properties="name",
                                            constraints=None,
                                            out=True)
  api_mock.post.assert_called_with(
      payload={
          "nodes": ["node1"],
          "property": "->name"
      },
      endpoint="node",
      all_pages=True,
      next_token=None,
  )

  # List input
  response = endpoint.fetch_property_values(node_dcids="node1",
                                            properties=["name", "typeOf"],
                                            constraints=None,
                                            out=True)
  api_mock.post.assert_called_with(
      payload={
          "nodes": ["node1"],
          "property": "->[name, typeOf]"
      },
      endpoint="node",
      all_pages=True,
      next_token=None,
  )


@patch(
    "datacommons_client.endpoints.node.extract_name_from_english_name_property")
def test_fetch_entity_names_english(mock_extract_name):
  """Test fetching names in English (default behavior)."""
  mock_extract_name.return_value = "Guatemala"
  api_mock = MagicMock()
  endpoint = NodeEndpoint(api=api_mock)

  # Mock the response from fetch_property_values
  endpoint.fetch_property_values = MagicMock(return_value=NodeResponse(
      data={
          'dc/123':
              Arcs(arcs={
                  DEFAULT_NAME_PROPERTY:
                      NodeGroup(nodes=[Node(value='Guatemala')])
              })
      }))

  result = endpoint.fetch_entity_names("dc/123")
  endpoint.fetch_property_values.assert_called_once_with(
      node_dcids=["dc/123"], properties=DEFAULT_NAME_PROPERTY)
  assert result == {
      "dc/123":
          Name(
              value="Guatemala",
              language="en",
              property=DEFAULT_NAME_PROPERTY,
          )
  }

  mock_extract_name.assert_called_once_with(
      properties=[Node(value="Guatemala")])


@patch(
    "datacommons_client.endpoints.node.extract_name_from_property_with_language"
)
def test_fetch_entity_names_non_english(mock_extract_name):
  """Test fetching names in a non-English language."""
  mock_extract_name.return_value = ("Californie", "fr")
  api_mock = MagicMock()
  endpoint = NodeEndpoint(api=api_mock)

  endpoint.fetch_property_values = MagicMock(return_value=NodeResponse(
      data={
          'dc/123':
              Arcs(
                  arcs={
                      NAME_WITH_LANGUAGE_PROPERTY:
                          NodeGroup(nodes=[Node(value='Californie')])
                  })
      }))

  result = endpoint.fetch_entity_names("dc/123", language="fr")
  endpoint.fetch_property_values.assert_called_once_with(
      node_dcids=["dc/123"], properties=NAME_WITH_LANGUAGE_PROPERTY)
  assert result == {
      "dc/123":
          Name(
              value="Californie",
              language="fr",
              property=NAME_WITH_LANGUAGE_PROPERTY,
          )
  }

  mock_extract_name.assert_called_once_with(
      properties=[Node(value='Californie')],
      language='fr',
      fallback_language=None)


@patch(
    "datacommons_client.endpoints.node.extract_name_from_property_with_language"
)
def test_fetch_entity_names_with_fallback(mock_extract_name_lang):
  """Test fallback to another language when target language is unavailable."""
  mock_extract_name_lang.return_value = ("Chiquimula", "en")
  api_mock = MagicMock()
  endpoint = NodeEndpoint(api=api_mock)

  endpoint.fetch_property_values = MagicMock(return_value=NodeResponse(
      data={
          'dc/123':
              Arcs(
                  arcs={
                      NAME_WITH_LANGUAGE_PROPERTY:
                          NodeGroup(nodes=[Node(value='Chiquimula')])
                  })
      }))

  result = endpoint.fetch_entity_names("dc/123",
                                       language="fr",
                                       fallback_language="en")

  assert result == {
      "dc/123":
          Name(
              value="Chiquimula",
              language="en",
              property=NAME_WITH_LANGUAGE_PROPERTY,
          )
  }
  mock_extract_name_lang.assert_called_once_with(
      properties=[Node(value='Chiquimula')],
      language='fr',
      fallback_language='en')


@patch(
    "datacommons_client.endpoints.node.extract_name_from_property_with_language"
)
def test_fetch_entity_names_no_result(mock_extract_name_lang):
  """Test case when no name is found."""
  mock_extract_name_lang.return_value = (None, None)
  api_mock = MagicMock()
  endpoint = NodeEndpoint(api=api_mock)

  endpoint.fetch_property_values = MagicMock(return_value=NodeResponse(
      data={"dc/999": {
          "properties": []
      }}))

  result = endpoint.fetch_entity_names("dc/999",
                                       language="es",
                                       fallback_language="en")
  assert result == {}


@patch("datacommons_client.endpoints.node.flatten_relationship")
@patch("datacommons_client.endpoints.node.build_graph_map")
@patch("datacommons_client.endpoints.node.fetch_relationship_lru")
def test_fetch_entity_relationships_delegates_to_lru(mock_lru, mock_build_map,
                                                     mock_flatten):
  """Ensure that the private helper builds a fetch‑function that ultimately
    calls through to ``fetch_relationship_lru`` for each root DCID."""

  mock_lru.return_value = [Node(dcid="B", name="B name", types=["Region"])]

  def _fake_build_graph_map(root, fetch_fn):
    # simulate the internal traversal by invoking the provided fetch_fn once
    fetch_fn(dcid=root)
    return root, {}

  mock_build_map.side_effect = _fake_build_graph_map
  mock_flatten.return_value = []

  endpoint = NodeEndpoint(api=MagicMock())
  result = endpoint._fetch_place_relationships(place_dcids="X",
                                               as_tree=False,
                                               contained_type="Region",
                                               relationship="parents")

  assert result == {"X": []}
  mock_lru.assert_called_once_with(
      endpoint,
      dcid="X",
      contained_type="Region",
      relationship="parents",
  )


@patch("datacommons_client.endpoints.node.flatten_relationship")
@patch("datacommons_client.endpoints.node.build_graph_map")
def test_fetch_entity_ancestry_flat(mock_build_map, mock_flatten):
  """Flat ancestry structure should be derived via ``flatten_relationship``."""
  mock_build_map.return_value = (
      "X",
      {
          "X": [Node(dcid="A", name="A name", types=["Country"])],
          "A": [],
      },
  )
  mock_flatten.return_value = [{
      "dcid": "A",
      "name": "A name",
      "type": "Country"
  }]

  endpoint = NodeEndpoint(api=MagicMock())
  result = endpoint.fetch_place_ancestors("X", as_tree=False)

  assert result == {"X": [{"dcid": "A", "name": "A name", "type": "Country"}]}
  mock_build_map.assert_called_once()
  mock_flatten.assert_called_once()


@patch("datacommons_client.endpoints.node.build_relationship_tree")
@patch("datacommons_client.endpoints.node.build_graph_map")
def test_fetch_entity_ancestry_tree(mock_build_map, mock_build_tree):
  """Nested ancestry structure should be derived via
    ``build_relationship_tree``."""
  mock_build_map.return_value = (
      "Y",
      {
          "Y": [Node(dcid="Z", name="Z name", types=["Region"])],
          "Z": [],
      },
  )

  mock_build_tree.return_value = {
      "dcid":
          "Y",
      "name":
          None,
      "type":
          None,
      "parents": [{
          "dcid": "Z",
          "name": "Z name",
          "type": "Region",
          "parents": []
      }],
  }

  endpoint = NodeEndpoint(api=MagicMock())
  result = endpoint.fetch_place_ancestors("Y", as_tree=True)

  assert "Y" in result
  assert result["Y"]["dcid"] == "Y"
  assert result["Y"]["parents"][0]["dcid"] == "Z"
  mock_build_map.assert_called_once()
  mock_build_tree.assert_called_once_with(root="Y",
                                          graph=mock_build_map.return_value[1],
                                          relationship_key="parents")
