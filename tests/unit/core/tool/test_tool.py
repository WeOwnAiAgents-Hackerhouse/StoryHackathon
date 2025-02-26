from typing import Tuple

import pytest
from pydantic import BaseModel, Field
from alphaswarm.core.tool import AlphaSwarmToolBase
from smolagents import Tool

from alphaswarm.core.tool.tool import AlphaSwarmToSmolAgentsToolAdapter
from alphaswarm.tools.story import GetIPAssetDetails

import json
import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from web3 import Web3

from alphaswarm.services.story import StoryProtocolAPI
from alphaswarm.tools.story import (
    QueryStoryIPAssets,
    RegisterIPAsset,
    GetIPAssetDetails,
    CreateLicenseTerms,
    AttachLicenseTerms,
    MintLicenseToken,
    DisputeIPAsset,
    IPType,
    IPMetadata
)

def alphaswarm_tool_and_smolagents_tool(tool: AlphaSwarmToolBase) -> Tuple[AlphaSwarmToolBase, Tool]:
    return tool, AlphaSwarmToSmolAgentsToolAdapter.adapt(tool)


def test_base() -> None:
    class MyTool(AlphaSwarmToolBase):
        """This is my tool description"""

        def forward(self) -> None:
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    assert tool.name == smolagents_tool.name == "MyTool"
    assert tool.description == smolagents_tool.description == "This is my tool description"
    assert tool.output_type is type(None)
    assert smolagents_tool.output_type == "null"


def test_multiline_description() -> None:
    class MyTool(AlphaSwarmToolBase):
        """
        This is my multiline
        tool description
        """

        def forward(self) -> str:
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    assert tool.name == smolagents_tool.name == "MyTool"
    assert tool.description == smolagents_tool.description == "This is my multiline\ntool description"
    assert tool.output_type is str
    assert smolagents_tool.output_type == "string"


def test_missing_description() -> None:
    with pytest.raises(ValueError) as e:

        class MyTool(AlphaSwarmToolBase):
            def forward(self) -> None:
                raise NotImplementedError

    assert str(e.value) == "Description of the tool must be provided either as a class attribute or docstring"


def test_override() -> None:
    class MyTool(AlphaSwarmToolBase):
        """This is my tool description"""

        name = "MyTool2"
        description = "This is my tool description v2"
        output_type = int

        def forward(self) -> None:
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    assert tool.name == smolagents_tool.name == "MyTool2"
    assert tool.description == smolagents_tool.description == "This is my tool description v2"
    assert tool.output_type is int
    assert smolagents_tool.output_type == "integer"


def test_output_type_base_model() -> None:
    class MyModel(BaseModel):
        name: str = Field(..., description="The name of the person")
        age: int = Field(..., description="The age of the person")

    class MyTool(AlphaSwarmToolBase):
        """This is my BaseModel tool description"""

        def forward(self) -> MyModel:
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    for t in [tool, smolagents_tool]:
        assert t.description.startswith("This is my BaseModel tool description")
        assert "Returns a MyModel object with the following schema:" in t.description
        assert "The name of the person" in t.description
        assert "The age of the person" in t.description

    assert tool.output_type is MyModel
    assert smolagents_tool.output_type == "object"


def test_with_examples() -> None:
    class MyTool(AlphaSwarmToolBase):
        """This is my tool description"""

        examples = ["Examples:", "- Example 1", "- Example 2"]

        def forward(self) -> float:
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    for t in [tool, smolagents_tool]:
        assert t.description.startswith("This is my tool description")
        for example in MyTool.examples:
            assert example in t.description

    assert tool.output_type is float
    assert smolagents_tool.output_type == "number"


def test_incorrect_inputs_descriptions() -> None:
    with pytest.raises(ValueError) as e:

        class MyTool(AlphaSwarmToolBase):
            """This is my tool description"""

            def forward(self, a: str, b) -> None:  # type: ignore
                raise NotImplementedError

    assert str(e.value) == "Missing type hints for forward() method parameters: b"

    with pytest.raises(ValueError) as e:

        class MyTool_v2(AlphaSwarmToolBase):
            """This is my tool description"""

            def forward(self, a: str, b: int) -> None:
                raise NotImplementedError

    assert str(e.value) == "Missing docstring for the forward() method. Must contain parameters descriptions."

    with pytest.raises(ValueError) as e:

        class MyTool_v3(AlphaSwarmToolBase):
            """This is my tool description"""

            def forward(self, a: str, b: int) -> None:
                """This is a docstring"""
                raise NotImplementedError

    assert str(e.value) == "Missing Args/Parameters section in the forward() method docstring."

    with pytest.raises(ValueError) as e:

        class MyTool_v4(AlphaSwarmToolBase):
            """This is my tool description"""

            def forward(self, a: str, b: int) -> None:
                """
                Args:
                    a: This is a description for a
                """
                raise NotImplementedError

    assert str(e.value) == "Missing description for parameters: b"


def test_inputs_descriptions() -> None:
    class MyTool(AlphaSwarmToolBase):
        """This is my tool description"""

        def forward(self, a: str, b: int) -> None:
            """
            Args:
                a: This is a description for a
                b: This is a description for b
            """
            raise NotImplementedError

    tool, smolagents_tool = alphaswarm_tool_and_smolagents_tool(MyTool())
    assert tool.inputs_descriptions == {"a": "This is a description for a", "b": "This is a description for b"}
    assert smolagents_tool.inputs == {
        "a": {"description": "This is a description for a", "type": "string"},
        "b": {"description": "This is a description for b", "type": "integer"},
    }


@pytest.mark.skip("Not implemented yet.")
def test_multiline_inputs_descriptions() -> None:
    class MyTool(AlphaSwarmToolBase):
        """This is my tool description"""

        def forward(self, a: str, b: int) -> None:
            """
            Args:
                a: This is a multiline
                    description for a
                b: This is a description for b
            """
            raise NotImplementedError

    my_tool = MyTool()
    assert my_tool.inputs_descriptions == {
        "a": "This is a multiline\ndescription for a",
        "b": "This is a description for b",
    }


def test_story_protocol_addresses():
    """Test that the addresses in the JSON file match the ones in the Story Protocol documentation."""
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to the root directory
    root_dir = os.path.abspath(os.path.join(current_dir, "../../../.."))
    addresses_file = os.path.join(root_dir, "alphaswarm/services/story/addresses.json")
    
    with open(addresses_file, 'r') as f:
        addresses = json.load(f)
    
    # Verify mainnet addresses match the documentation
    assert addresses["mainnet"]["core"]["IPAssetRegistry"] == "0x77319B4031e6eF1250907aa00018B8B1c67a244b"
    assert addresses["mainnet"]["core"]["LicenseRegistry"] == "0x529a750E02d8E2f15649c13D69a465286a780e24"
    assert addresses["mainnet"]["core"]["LicensingModule"] == "0x04fbd8a2e56dd85CFD5500A4A4DfA955B9f1dE6f"
    assert addresses["mainnet"]["core"]["PILicenseTemplate"] == "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"
    assert addresses["mainnet"]["core"]["RoyaltyPolicyLAP"] == "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E"
    assert addresses["mainnet"]["core"]["LicenseToken"] == "0xFe3838BFb30B34170F00030B52eA4893d8aAC6bC"
    assert addresses["mainnet"]["core"]["RoyaltyModule"] == "0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
    assert addresses["mainnet"]["pheriphery"]["RoyaltyWorkflows"] == "0x9515faE61E0c0447C6AC6dEe5628A2097aFE1890"


@pytest.fixture
def mock_story_api():
    """Create a mock StoryProtocolAPI instance with real addresses."""
    mock_api = MagicMock(spec=StoryProtocolAPI)
    mock_api.network = "mainnet"
    
    # Set mock addresses from the actual addresses.json file
    mock_api.dispute_module_address = "0x9b7A9c70AFF961C799110954fc06F3093aeb94C5"
    mock_api.arbitration_policy_address = "0xfFD98c3877B8789124f02C7E8239A4b0Ef11E936"
    mock_api.ip_asset_registry_address = "0x77319B4031e6eF1250907aa00018B8B1c67a244b"
    mock_api.license_registry_address = "0x529a750E02d8E2f15649c13D69a465286a780e24"
    mock_api.licensing_module_address = "0x04fbd8a2e56dd85CFD5500A4A4DfA955B9f1dE6f"
    mock_api.pil_template_address = "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"
    mock_api.royalty_policy_lap_address = "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E"
    mock_api.royalty_policy_lrp_address = "0x9156e603C949481883B1d3355c6f1132D191fC41"
    mock_api.license_token_address = "0xFe3838BFb30B34170F00030B52eA4893d8aAC6bC"
    mock_api.royalty_module_address = "0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
    mock_api.merc20_address = "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"
    
    # Mock async methods
    mock_api.get_min_liveness = AsyncMock(return_value=86400)  # 1 day
    mock_api.get_max_liveness = AsyncMock(return_value=2592000)  # 30 days
    mock_api.get_max_bonds = AsyncMock(return_value=1000000000000000000)  # 1 ETH
    mock_api.is_whitelisted_dispute_tag = AsyncMock(return_value=True)
    mock_api.convert_cid_to_hash = AsyncMock(return_value="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
    
    # Mock IP asset data based on the Story Protocol documentation
    mock_api.get_ip_assets = AsyncMock(return_value=[
        {
            "id": "0x123456789abcdef123456789abcdef123456789a",
            "metadata": {
                "title": "Test IP Asset",
                "description": "A test IP asset for unit testing",
                "ipType": "image",
                "attributes": [{"trait_type": "Creator", "value": "Test Creator"}],
                "creators": [{"address": "0xa11ce", "share": 100}],
                "tags": ["test", "image", "unit-test"]
            },
            "owner": "0xa11ce",
            "creation_date": "2023-01-01T00:00:00Z",
            "last_sale_price": "0.5"
        }
    ])
    
    # Mock IP asset details based on the Story Protocol documentation
    mock_api.get_ip_asset_details = AsyncMock(return_value={
        "id": "0x123456789abcdef123456789abcdef123456789a",
        "metadata": {
            "title": "Test IP Asset",
            "description": "A test IP asset for unit testing",
            "ipType": "image",
            "attributes": [{"trait_type": "Creator", "value": "Test Creator"}],
            "creators": [{"address": "0xa11ce", "share": 100}],
            "tags": ["test", "image", "unit-test"]
        },
        "owner": "0xa11ce",
        "creation_date": "2023-01-01T00:00:00Z",
        "last_sale_price": "0.5",
        "license_terms_id": "10"
    })
    
    # Mock register IP asset
    mock_api.register_ip_asset = AsyncMock(return_value={
        "ipId": "0x123456789abcdef123456789abcdef123456789a",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "status": "success"
    })
    
    return mock_api


@pytest.mark.asyncio
async def test_register_ip_asset(mock_story_api):
    """Test registering an IP asset on Story Protocol."""
    tool = RegisterIPAsset(client=mock_story_api)
    
    # Create metadata based on the Story Protocol documentation
    metadata = IPMetadata(
        title="Test IP Asset",
        description="A test IP asset for unit testing",
        ipType=IPType.IMAGE,
        attributes=[{"trait_type": "Creator", "value": "Test Creator"}],
        creators=[{"address": "0xa11ce", "share": 100}],
        tags=["test", "image", "unit-test"]
    )
    
    result = await tool.forward(
        metadata=json.dumps(metadata.__dict__, default=lambda o: o.value if isinstance(o, IPType) else o),
        owner_address="0xa11ce",
        network="mainnet"
    )
    
    # Verify the result
    result_json = json.loads(result)
    assert "ipId" in result_json
    assert "txHash" in result_json
    assert result_json["status"] == "success"
    
    # Verify the API was called with the correct parameters
    mock_story_api.register_ip_asset.assert_called_once()


@pytest.mark.asyncio
async def test_create_license_terms(mock_story_api):
    """Test creating license terms on Story Protocol."""
    tool = CreateLicenseTerms(client=mock_story_api)
    
    # Create license terms based on the Story Protocol documentation
    result = await tool.forward(
        minting_fee="0.05",  # 0.05 ETH
        commercial_rev_share=1000000,  # 10%
        royalty_policy=mock_story_api.royalty_policy_lap_address,
        currency_token=mock_story_api.merc20_address,
        network="mainnet"
    )
    
    # Verify the result
    result_json = json.loads(result)
    assert "licenseTermsId" in result_json
    assert result_json["mintingFee"] == "0.05"
    assert result_json["commercialRevShare"] == 1000000
    assert result_json["royaltyPolicy"] == mock_story_api.royalty_policy_lap_address
    assert result_json["currencyToken"] == mock_story_api.merc20_address
    assert result_json["network"] == "mainnet"


@pytest.mark.asyncio
async def test_attach_license_terms(mock_story_api):
    """Test attaching license terms to an IP asset on Story Protocol."""
    tool = AttachLicenseTerms(client=mock_story_api)
    
    # Mock the attach_license_terms method
    mock_story_api.attach_license_terms = AsyncMock(return_value={
        "status": "success",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "message": "Successfully attached license terms"
    })
    
    result = await tool.forward(
        ip_id="0x123456789abcdef123456789abcdef123456789a",
        license_terms_id="10",
        license_template=mock_story_api.pil_template_address,
        network="mainnet"
    )
    
    # Verify the result
    result_json = json.loads(result)
    assert result_json["status"] == "success"
    assert "txHash" in result_json
    
    # Verify the API was called with the correct parameters
    mock_story_api.attach_license_terms.assert_called_once_with(
        "0x123456789abcdef123456789abcdef123456789a",
        "10",
        mock_story_api.pil_template_address
    )


@pytest.mark.asyncio
async def test_mint_license_token(mock_story_api):
    """Test minting a license token on Story Protocol."""
    tool = MintLicenseToken(client=mock_story_api)
    
    # Mock the mint_license_token method
    mock_story_api.mint_license_token = AsyncMock(return_value={
        "status": "success",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "licenseTokenId": "1",
        "message": "Successfully minted license token"
    })
    
    result = await tool.forward(
        licensor_ip_id="0x123456789abcdef123456789abcdef123456789a",
        license_terms_id="10",
        license_template=mock_story_api.pil_template_address,
        amount="2",
        receiver="0xb0b",
        network="mainnet"
    )
    
    # Verify the result
    result_json = json.loads(result)
    assert result_json["status"] == "success"
    assert "licenseTokenId" in result_json
    
    # Verify the API was called with the correct parameters
    mock_story_api.mint_license_token.assert_called_once()


@pytest.mark.asyncio
async def test_dispute_ip_asset(mock_story_api):
    """Test disputing an IP asset on Story Protocol."""
    tool = DisputeIPAsset(client=mock_story_api)
    
    result = await tool.forward(
        target_ip_id="0x123456789abcdef123456789abcdef123456789a",
        target_tag="copyright",
        cid="QmTest1234567890",
        bond="0",  # No bond
        liveness="2592000",  # 30 days
        wait_for_transaction=True,
        network="mainnet"
    )
    
    # Verify the API methods were called
    mock_story_api.get_min_liveness.assert_called_once()
    mock_story_api.get_max_liveness.assert_called_once()
    mock_story_api.is_whitelisted_dispute_tag.assert_called_once_with("copyright")
    mock_story_api.convert_cid_to_hash.assert_called_once_with("QmTest1234567890")
    
    # Verify the result is properly formatted JSON
    result_json = json.loads(result)
    assert "txHash" in result_json
    assert "disputeId" in result_json
    assert result_json["network"] == "mainnet"
    assert result_json["disputeModuleAddress"] == mock_story_api.dispute_module_address


@pytest.mark.asyncio
async def test_network_switching():
    """Test that tools correctly switch networks when requested."""
    with patch('alphaswarm.services.story.StoryProtocolAPI') as MockAPI:
        # Setup mock instances for different networks
        mock_mainnet = MagicMock()
        mock_mainnet.network = "mainnet"
        mock_mainnet.royalty_policy_lap_address = "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E"
        
        mock_testnet = MagicMock()
        mock_testnet.network = "testnet"
        mock_testnet.royalty_policy_lap_address = "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E"  # Same address in testnet
        
        # Configure the mock to return different instances based on network
        MockAPI.side_effect = lambda network="mainnet", **kwargs: mock_mainnet if network == "mainnet" else mock_testnet
        
        # Test CreateLicenseTerms with network switching
        tool = CreateLicenseTerms()
        
        # First call with mainnet
        await tool.forward(
            minting_fee="0.05",
            commercial_rev_share=1000000,  # 10% in basis points as per documentation
            network="mainnet"
        )
        
        # Second call with testnet
        await tool.forward(
            minting_fee="0.05",
            commercial_rev_share=1000000,
            network="testnet"
        )
        
        # Verify that the API was initialized with the correct networks
        MockAPI.assert_any_call(network="mainnet")
        MockAPI.assert_any_call(network="testnet")


@pytest.mark.asyncio
async def test_full_ip_asset_workflow(mock_story_api):
    """Test a complete workflow of registering an IP asset, creating license terms, attaching them, and minting a license token."""
    # Mock the necessary methods
    mock_story_api.register_ip_asset = AsyncMock(return_value={
        "ipId": "0x123456789abcdef123456789abcdef123456789a",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "status": "success"
    })
    
    mock_story_api.create_license_terms = AsyncMock(return_value={
        "licenseTermsId": "10",
        "status": "success"
    })
    
    mock_story_api.attach_license_terms = AsyncMock(return_value={
        "status": "success",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    mock_story_api.mint_license_token = AsyncMock(return_value={
        "status": "success",
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "licenseTokenId": "1"
    })
    
    # 1. Register IP Asset
    register_tool = RegisterIPAsset(client=mock_story_api)
    metadata = IPMetadata(
        title="Test IP Asset",
        description="A test IP asset for unit testing",
        ipType=IPType.IMAGE,
        attributes=[{"trait_type": "Creator", "value": "Test Creator"}],
        creators=[{"address": "0xa11ce", "share": 100}],
        tags=["test", "image", "unit-test"]
    )
    
    register_result = await register_tool.forward(
        metadata=json.dumps(metadata.__dict__, default=lambda o: o.value if isinstance(o, IPType) else o),
        owner_address="0xa11ce",
        network="mainnet"
    )
    register_json = json.loads(register_result)
    ip_id = register_json["ipId"]
    
    # 2. Create License Terms
    license_terms_tool = CreateLicenseTerms(client=mock_story_api)
    license_terms_result = await license_terms_tool.forward(
        minting_fee="0.05",
        commercial_rev_share=1000000,  # 10%
        royalty_policy=mock_story_api.royalty_policy_lap_address,
        currency_token=mock_story_api.merc20_address,
        network="mainnet"
    )
    license_terms_json = json.loads(license_terms_result)
    license_terms_id = license_terms_json["licenseTermsId"]
    
    # 3. Attach License Terms
    attach_tool = AttachLicenseTerms(client=mock_story_api)
    attach_result = await attach_tool.forward(
        ip_id=ip_id,
        license_terms_id=license_terms_id,
        license_template=mock_story_api.pil_template_address,
        network="mainnet"
    )
    attach_json = json.loads(attach_result)
    assert attach_json["status"] == "success"
    
    # 4. Mint License Token
    mint_tool = MintLicenseToken(client=mock_story_api)
    mint_result = await mint_tool.forward(
        licensor_ip_id=ip_id,
        license_terms_id=license_terms_id,
        license_template=mock_story_api.pil_template_address,
        amount="2",
        receiver="0xb0b",
        network="mainnet"
    )
    mint_json = json.loads(mint_result)
    assert mint_json["status"] == "success"
    assert "licenseTokenId" in mint_json


