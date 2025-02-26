import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import decimal
from enum import Enum
import os
import requests
from typing import Dict, List, Optional, Tuple, Union

import dotenv
from alphaswarm.agent.agent import AlphaSwarmAgent
from alphaswarm.agent.clients import TerminalClient
from alphaswarm.core.tool import AlphaSwarmToolBase

class IPType(str, Enum):
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    MODEL = "model"
    AI_AGENT = "AI Agent"  # Added AI Agent type for Story Protocol


@dataclass
class IPMetadata:
    title: str
    description: str
    ipType: IPType
    attributes: List[Dict[str, str]]
    creators: List[Dict[str, Union[str, int]]]
    tags: List[str] = None  # Added tags field for Story Protocol
    
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=lambda o: o.value if isinstance(o, Enum) else o.__dict__)


@dataclass
class IPAsset:
    id: str
    metadata: IPMetadata
    owner: str
    creation_date: datetime
    last_sale_price: Optional[Decimal] = None
    license_terms_id: Optional[str] = None  # Added for Story Protocol
    
    @property
    def age_days(self) -> int:
        return (datetime.now() - self.creation_date).days


@dataclass
class LicenseTerms:
    id: str
    mintingFee: Decimal
    commercialRevShare: int  # In basis points (e.g., 1000000 = 10%)
    royaltyPolicy: str
    currencyToken: str
    
    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "mintingFee": str(self.mintingFee),
            "commercialRevShare": self.commercialRevShare,
            "royaltyPolicy": self.royaltyPolicy,
            "currencyToken": self.currencyToken
        })


@dataclass
class LicenseToken:
    id: str
    licenseTermsId: str
    ipAssetId: str
    licensee: str
    issuanceDate: datetime
    
    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "licenseTermsId": self.licenseTermsId,
            "ipAssetId": self.ipAssetId,
            "licensee": self.licensee,
            "issuanceDate": self.issuanceDate.isoformat()
        })


@dataclass
class Offer:
    asset_id: str
    buyer: str
    price: Decimal
    expiration: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expiration


@dataclass
class NegotiationState:
    asset_id: str
    seller: str
    buyer: str
    asking_price: Decimal
    current_offer: Optional[Decimal] = None
    counter_offer: Optional[Decimal] = None
    status: str = "pending"  # pending, accepted, rejected, expired
    license_terms_id: Optional[str] = None  # Added for Story Protocol
    license_token_id: Optional[str] = None  # Added for Story Protocol
    
    def is_accepted(self) -> bool:
        return self.status == "accepted"
    
    def is_rejected(self) -> bool:
        return self.status == "rejected"


# ===== Story Protocol API Integration =====

class StoryProtocolAPI:
    """Helper class to interact with Story Protocol's RPC endpoint."""
    
    def __init__(self, rpc_url=None):
        self.rpc_url = rpc_url or os.getenv("STORY_RPC_URL", "https://aeneid.storyrpc.io")
    
    async def get_ip_assets(self, owner_address=None, limit=10, offset=0):
        """
        Query IP assets from Story Protocol.
        
        Args:
            owner_address: Optional filter by owner address
            limit: Maximum number of results to return
            offset: Pagination offset
            
        Returns:
            List of IP assets
        """
        try:
            # This is a mock implementation - in a real scenario, you would make
            # an actual RPC call to the Story Protocol blockchain
            params = {
                "method": "story_getIpAssets",
                "params": [{"owner": owner_address, "limit": limit, "offset": offset}],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", [])
                return result
            else:
                return {"error": f"Failed to fetch IP assets: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error querying Story Protocol: {str(e)}"}
    
    async def get_ip_asset_details(self, asset_id):
        """
        Get detailed information about a specific IP asset.
        
        Args:
            asset_id: The ID of the IP asset
            
        Returns:
            Detailed information about the IP asset
        """
        try:
            params = {
                "method": "story_getIpAsset",
                "params": [asset_id],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", {})
                return result
            else:
                return {"error": f"Failed to fetch IP asset details: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error querying Story Protocol: {str(e)}"}


# ===== Story Protocol Tools =====

class QueryStoryIPAssets(AlphaSwarmToolBase):
    """Query IP assets from Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, owner_address: Optional[str] = None, limit: int = 10, offset: int = 0) -> str:
        """Execute the tool's core functionality.

        Args:
            owner_address: Optional filter by owner address
            limit: Maximum number of results to return
            offset: Pagination offset
        """
        result = await self.client.get_ip_assets(owner_address, limit, offset)
        
        return json.dumps(result, indent=2)


class RegisterIPAsset(AlphaSwarmToolBase):
    """Register a new IP asset on the Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()

    async def forward(self, metadata: str, owner_address: str) -> str:
        """Execute the tool's core functionality.

        Args:
            metadata: JSON string containing IP metadata following the IPA Metadata Standard
            owner_address: Blockchain address of the IP owner
        """
        try:
            metadata_dict = json.loads(metadata)
            # Validate metadata structure according to Story Protocol's IPA Metadata Standard
            required_fields = ["title", "description", "ipType", "attributes", "creators"]
            for field in required_fields:
                if field not in metadata_dict:
                    return f"Error: Missing required field '{field}' in metadata"
            
            # In a real implementation, this would call the Story Protocol SDK
            # client.ipAsset.mintAndRegisterIpAsset({...})
            asset_id = f"ip-{hash(metadata)}"
            return json.dumps({
                "status": "success",
                "ipId": asset_id,
                "txHash": f"0x{hash(asset_id + owner_address):x}",
                "message": "Successfully registered IP asset on Story Protocol"
            })
        except json.JSONDecodeError:
            return "Error: Invalid JSON metadata"


class GetIPAssetDetails(AlphaSwarmToolBase):
    """Get details about an IP asset registered on Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, asset_id: str) -> str:
        """Execute the tool's core functionality.

        Args:
            asset_id: The ID of the IP asset
        """
        # First try to get real data from Story Protocol
        api = StoryProtocolAPI()
        result = await api.get_ip_asset_details(asset_id)
        
        # If we got an error, fall back to mock data
        if "error" in result:
            # Mock implementation - in reality would query the Story Protocol
            if not asset_id.startswith("ip-"):
                return "Error: Invalid asset ID format"
            
            # Create a mock asset for demonstration
            mock_asset = IPAsset(
                id=asset_id,
                metadata=IPMetadata(
                    title="AI-Generated Landscape",
                    description="A beautiful landscape generated by Stable Diffusion",
                    ipType=IPType.IMAGE,
                    attributes=[
                        {"key": "Model", "value": "stable-diffusion-xl"},
                        {"key": "Prompt", "value": "Serene mountain landscape at sunset"},
                    ],
                    creators=[
                        {"name": "AI Artist", "contributionPercent": 100, "address": "0x123...abc"}
                    ],
                    tags=["AI", "Landscape", "Stable Diffusion"]
                ),
                owner="0x123...abc",
                creation_date=datetime.now(),
                last_sale_price=Decimal("0.5"),
                license_terms_id="terms-123456"
            )
            
            # Convert to dictionary for JSON serialization
            result = {
                "id": mock_asset.id,
                "metadata": {
                    "title": mock_asset.metadata.title,
                    "description": mock_asset.metadata.description,
                    "ipType": mock_asset.metadata.ipType,
                    "attributes": mock_asset.metadata.attributes,
                    "creators": mock_asset.metadata.creators,
                    "tags": mock_asset.metadata.tags
                },
                "owner": mock_asset.owner,
                "creation_date": mock_asset.creation_date.isoformat(),
                "last_sale_price": str(mock_asset.last_sale_price) if mock_asset.last_sale_price else None,
                "license_terms_id": mock_asset.license_terms_id
            }
        
        return json.dumps(result, indent=2)


class CreateLicenseTerms(AlphaSwarmToolBase):
    """Create license terms for an IP asset on Story Protocol."""
    
    async def forward(self, minting_fee: str, commercial_rev_share: int, royalty_policy: str, currency_token: str) -> str:
        """Execute the tool's core functionality.

        Args:
            minting_fee: The fee to mint a license token (in ETH)
            commercial_rev_share: Revenue share for commercial use (in basis points)
            royalty_policy: Description of the royalty policy
            currency_token: The token used for payments
        """
        try:
            minting_fee_decimal = Decimal(minting_fee)
            if minting_fee_decimal < 0:
                return "Error: Minting fee cannot be negative"
            
            if commercial_rev_share < 0 or commercial_rev_share > 10000:
                return "Error: Commercial revenue share must be between 0 and 10000 basis points"
            
            # Mock license terms creation
            license_terms_id = f"terms-{hash(f'{minting_fee}-{commercial_rev_share}-{royalty_policy}')}"
            
            return json.dumps({
                "status": "success",
                "licenseTermsId": license_terms_id,
                "mintingFee": minting_fee,
                "commercialRevShare": commercial_rev_share,
                "royaltyPolicy": royalty_policy,
                "currencyToken": currency_token,
                "message": "Successfully created license terms"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid minting fee format"


class AttachLicenseTerms(AlphaSwarmToolBase):
    """Attach license terms to an IP asset on Story Protocol."""
    
    async def forward(self, ip_id: str, license_terms_id: str) -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            license_terms_id: The ID of the license terms
        """
        # Mock attaching license terms
        if not ip_id.startswith("ip-"):
            return "Error: Invalid IP asset ID format"
        
        if not license_terms_id.startswith("terms-"):
            return "Error: Invalid license terms ID format"
        
        return json.dumps({
            "status": "success",
            "ip_id": ip_id,
            "license_terms_id": license_terms_id,
            "message": "Successfully attached license terms to IP asset"
        }, indent=2)


class MintLicenseToken(AlphaSwarmToolBase):
    """Mint a license token for an IP asset on Story Protocol."""
    
    async def forward(self, ip_id: str, license_terms_id: str, licensee_address: str, payment_amount: str) -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            license_terms_id: The ID of the license terms
            licensee_address: Address of the licensee
            payment_amount: Payment amount in ETH
        """
        try:
            payment_amount_decimal = Decimal(payment_amount)
            if payment_amount_decimal <= 0:
                return "Error: Payment amount must be positive"
            
            if not ip_id.startswith("ip-"):
                return "Error: Invalid IP asset ID format"
            
            if not license_terms_id.startswith("terms-"):
                return "Error: Invalid license terms ID format"
            
            # Mock license token minting
            license_token_id = f"license-{hash(f'{ip_id}-{licensee_address}-{payment_amount}')}"
            
            return json.dumps({
                "status": "success",
                "licenseTokenId": license_token_id,
                "ipId": ip_id,
                "licenseTermsId": license_terms_id,
                "licensee": licensee_address,
                "paymentAmount": payment_amount,
                "issuanceDate": datetime.now().isoformat(),
                "message": "Successfully minted license token"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid payment amount format"


class EstimateIPAssetValue(AlphaSwarmToolBase):
    """Estimate the value of an IP asset based on its metadata and market data."""
    
    async def __call__(
        self, 
        asset_id: str
    ) -> str:
        """
        Estimate the value of an IP asset.
        
        Args:
            asset_id: The ID of the IP asset
            
        Returns:
            Estimated value range for the IP asset
        """
        # In a real implementation, this would analyze market data and asset properties
        if not asset_id.startswith("ip-"):
            return "Error: Invalid asset ID format"
        
        # Mock valuation logic
        base_value = Decimal("0.5")  # ETH
        
        # Add some randomness to make it interesting
        import random
        variation = Decimal(str(random.uniform(-0.1, 0.2)))
        
        estimated_value = base_value + variation
        lower_bound = estimated_value * Decimal("0.8")
        upper_bound = estimated_value * Decimal("1.2")
        
        return json.dumps({
            "asset_id": asset_id,
            "estimated_value_eth": str(estimated_value),
            "value_range_eth": {
                "lower": str(lower_bound),
                "upper": str(upper_bound)
            },
            "confidence": "medium",
            "factors": [
                "Asset age",
                "Creator reputation",
                "Similar asset sales",
                "Current market trends"
            ]
        }, indent=2)


class MakeOffer(AlphaSwarmToolBase):
    """Make an offer for an IP asset on Story Protocol."""
    
    async def forward(self, asset_id: str, buyer_address: str, offer_amount: str) -> str:
        """Execute the tool's core functionality.

        Args:
            asset_id: The ID of the IP asset
            buyer_address: Address of the buyer
            offer_amount: Offer amount in ETH
        """
        try:
            offer_amount_decimal = Decimal(offer_amount)
            if offer_amount_decimal <= 0:
                return "Error: Offer amount must be positive"
            
            expiration = datetime.now().replace(microsecond=0)
            
            # Mock offer creation
            offer_id = f"offer-{hash(f'{asset_id}-{buyer_address}-{offer_amount}')}"
            
            return json.dumps({
                "status": "success",
                "offer_id": offer_id,
                "asset_id": asset_id,
                "buyer": buyer_address,
                "amount_eth": offer_amount,
                "expiration": expiration.isoformat(),
                "message": "Offer successfully submitted"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid offer amount format"


class RespondToOffer(AlphaSwarmToolBase):
    """Respond to an offer for an IP asset (accept, reject, or counter)."""
    
    async def forward(self, offer_id: str, response: str, counter_offer: Optional[str] = None) -> str:
        """Execute the tool's core functionality.

        Args:
            offer_id: The ID of the offer
            response: One of "accept", "reject", or "counter"
            counter_offer: If response is "counter", the counter offer amount in ETH
        """
        if response not in ["accept", "reject", "counter"]:
            return "Error: Response must be one of 'accept', 'reject', or 'counter'"
        
        if response == "counter" and not counter_offer:
            return "Error: Counter offer amount is required when response is 'counter'"
        
        if response == "counter":
            try:
                counter_amount = Decimal(counter_offer)
                if counter_amount <= 0:
                    return "Error: Counter offer amount must be positive"
            except (ValueError, decimal.InvalidOperation):
                return "Error: Invalid counter offer amount format"
        
        # Mock response processing
        return json.dumps({
            "status": "success",
            "offer_id": offer_id,
            "response": response,
            "counter_offer": counter_offer if response == "counter" else None,
            "message": f"Successfully {response}ed the offer"
        }, indent=2)


class ClaimRoyalty(AlphaSwarmToolBase):
    """Claim royalties for an IP asset on Story Protocol."""
    
    async def forward(self, ip_id: str, claimer_address: str) -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            claimer_address: Address of the claimer
        """
        # In a real implementation, this would call the Story Protocol SDK
        # client.royalty.claimRoyalty({...})
        
        # Mock royalty amount
        import random
        royalty_amount = Decimal(str(random.uniform(0.01, 0.5)))
        
        return json.dumps({
            "status": "success",
            "ip_id": ip_id,
            "claimer": claimer_address,
            "amount_claimed": str(royalty_amount),
            "currency": "ETH",
            "message": f"Successfully claimed {royalty_amount} ETH in royalties"
        })


class DisputeIPAsset(AlphaSwarmToolBase):
    """Dispute an IP asset on Story Protocol."""
    
    async def forward(self, ip_id: str, disputer_address: str, reason: str, evidence: str) -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            disputer_address: Address of the disputer
            reason: Reason for the dispute
            evidence: Evidence supporting the dispute
        """
        # In a real implementation, this would call the Story Protocol SDK
        # client.dispute.disputeIpAsset({...})
        
        dispute_id = f"dispute-{hash(f'{ip_id}-{disputer_address}-{reason}')}"
        
        return json.dumps({
            "status": "success",
            "dispute_id": dispute_id,
            "ip_id": ip_id,
            "disputer": disputer_address,
            "reason": reason,
            "evidence": evidence,
            "status": "pending",
            "message": "Successfully submitted dispute"
        })


# ===== Agents =====

class ValuationAgent(AlphaSwarmAgent):
    """Agent that analyzes and values IP assets."""
    
    def __init__(self):
        tools = [
            GetIPAssetDetails(),
            EstimateIPAssetValue(),
        ]
        
        hints = """
        You are a Valuation Agent specializing in determining the fair market value of intellectual property assets on Story Protocol.
        
        Your responsibilities:
        - Analyze IP asset metadata to understand its characteristics
        - Consider factors like creator reputation, asset quality, and market trends
        - Provide value estimates with confidence levels
        - Explain the reasoning behind your valuations
        
        When valuing an asset:
        1. First get the asset details using GetIPAssetDetails
        2. Analyze the metadata, especially the attributes and creator information
        3. Use EstimateIPAssetValue to get a baseline valuation
        4. Provide your own analysis of why the asset might be worth more or less than the estimate
        
        Remember that Story Protocol uses the IPA Metadata Standard for all IP assets.
        """
        
        super().__init__(tools=tools, model_id="openai/gpt-4o-mini", hints=hints)


class BuyerAgent(AlphaSwarmAgent):
    """Agent that represents potential buyers of IP assets."""
    
    def __init__(self):
        tools = [
            GetIPAssetDetails(),
            MakeOffer(),
            RespondToOffer(),
            MintLicenseToken(),
        ]
        
        hints = """
        You are a Buyer Agent representing clients interested in purchasing intellectual property assets on Story Protocol.
        
        Your responsibilities:
        - Evaluate IP assets based on their metadata and market value
        - Make strategic offers that balance fair value with client interests
        - Negotiate with sellers to reach mutually beneficial agreements
        - Know when to walk away from overpriced assets
        - Mint license tokens when agreements are reached
        
        When making offers:
        1. First get the asset details using GetIPAssetDetails
        2. Consider the asset's characteristics and potential value to your client
        3. Make an initial offer that is reasonable but leaves room for negotiation
        4. Respond appropriately to counteroffers, either accepting, rejecting, or making a counter
        5. If an agreement is reached, mint a license token using MintLicenseToken
        
        Remember that Story Protocol uses the Programmable IP License (PIL) to enforce license terms.
        """
        
        super().__init__(tools=tools, model_id="openai/gpt-4o-mini", hints=hints)


class SellerAgent(AlphaSwarmAgent):
    """Agent that represents IP asset owners/sellers."""
    
    def __init__(self):
        tools = [
            RegisterIPAsset(),
            GetIPAssetDetails(),
            CreateLicenseTerms(),
            AttachLicenseTerms(),
            RespondToOffer(),
            ClaimRoyalty(),
        ]
        
        hints = """
        You are a Seller Agent representing creators and owners of intellectual property assets on Story Protocol.
        
        Your responsibilities:
        - Help creators register their IP assets on the Story Protocol
        - Create and attach appropriate license terms to IP assets
        - Ensure IP metadata accurately represents the asset's value
        - Evaluate offers from potential buyers
        - Negotiate to maximize returns while ensuring fair deals
        - Claim royalties when due
        
        When handling offers:
        1. First get the asset details using GetIPAssetDetails to remind yourself of the asset's characteristics
        2. Evaluate whether the offer represents fair value for the asset
        3. Decide whether to accept, reject, or counter the offer
        4. If countering, set a price that reflects the asset's true value while still being realistic
        5. Periodically check and claim royalties using ClaimRoyalty
        
        Remember that Story Protocol uses the Programmable IP License (PIL) to enforce license terms.
        """
        
        super().__init__(tools=tools, model_id="openai/gpt-4o-mini", hints=hints)


class NegotiationAgent(AlphaSwarmAgent):
    """Agent that mediates negotiations between buyers and sellers."""
    
    def __init__(self):
        tools = [
            GetIPAssetDetails(),
            EstimateIPAssetValue(),
            CreateLicenseTerms(),
        ]
        
        hints = """
        You are a Negotiation Agent that mediates between buyers and sellers of intellectual property assets on Story Protocol.
        
        Your responsibilities:
        - Understand both parties' positions and interests
        - Suggest fair compromises based on market data
        - Help overcome negotiation deadlocks
        - Propose appropriate license terms that satisfy both parties
        - Ensure both parties feel they've reached a fair deal
        
        When mediating:
        1. First get the asset details using GetIPAssetDetails
        2. Use EstimateIPAssetValue to establish an objective baseline
        3. Consider both the buyer's and seller's positions
        4. Suggest a compromise that addresses both parties' core interests
        5. If needed, propose license terms using CreateLicenseTerms that balance creator compensation with fair use
        6. Explain why your suggested compromise is fair to both sides
        
        Remember that Story Protocol uses the Programmable IP License (PIL) to enforce license terms.
        """
        
        super().__init__(tools=tools, model_id="openai/gpt-4o-mini", hints=hints)


class CoordinatorAgent(AlphaSwarmAgent):
    """Agent that orchestrates the entire negotiation process."""
    
    def __init__(self, valuation_agent: ValuationAgent, buyer_agent: BuyerAgent, 
                 seller_agent: SellerAgent, negotiation_agent: NegotiationAgent):
        self.valuation_agent = valuation_agent
        self.buyer_agent = buyer_agent
        self.seller_agent = seller_agent
        self.negotiation_agent = negotiation_agent
        self.negotiations = {}  # Track ongoing negotiations
        
        tools = [
            RegisterIPAsset(),
            GetIPAssetDetails(),
            QueryStoryIPAssets(),  # Added tool to query IP assets
            CreateLicenseTerms(),
            AttachLicenseTerms(),
            MintLicenseToken(),
            ClaimRoyalty(),
            DisputeIPAsset(),
        ]
        
        hints = """
        You are a Coordinator Agent that orchestrates negotiations for intellectual property assets on Story Protocol.
        
        Your responsibilities:
        - Manage the overall negotiation process
        - Delegate tasks to specialized agents (valuation, buyer, seller, negotiation)
        - Track the state of ongoing negotiations
        - Ensure all parties have the information they need
        - Facilitate the creation and attachment of license terms
        - Help with minting license tokens and claiming royalties when appropriate
        
        Process flow:
        1. Start by registering an IP asset or selecting an existing one from Story Protocol
        2. Request a valuation from the Valuation Agent
        3. Create and attach license terms to the IP asset
        4. Facilitate initial offer from the Buyer Agent
        5. Manage response from the Seller Agent
        6. If needed, bring in the Negotiation Agent to mediate
        7. When agreement is reached, help mint a license token
        8. Assist with claiming royalties when appropriate
        9. Continue until agreement is reached or negotiation is terminated
        
        Remember that Story Protocol uses the Programmable IP License (PIL) to enforce license terms.
        """
        
        super().__init__(tools=tools, model_id="openai/gpt-4o-mini", hints=hints)
    
    async def browse_ip_assets(self, owner_address: Optional[str] = None) -> str:
        """Browse IP assets on Story Protocol."""
        assets_response = await self.run_tool("QueryStoryIPAssets", {
            "owner_address": owner_address,
            "limit": 10,
            "offset": 0
        })
        
        try:
            assets = json.loads(assets_response)
            if "error" in assets:
                return f"Error browsing IP assets: {assets['error']}"
            
            # Format the assets for display
            formatted_assets = []
            for asset in assets:
                asset_id = asset.get("id")
                title = asset.get("metadata", {}).get("title", "Untitled")
                ip_type = asset.get("metadata", {}).get("ipType", "Unknown")
                owner = asset.get("owner", "Unknown")
                
                formatted_assets.append({
                    "id": asset_id,
                    "title": title,
                    "type": ip_type,
                    "owner": owner
                })
            
            return json.dumps({"assets": formatted_assets}, indent=2)
        except json.JSONDecodeError:
            return f"Error parsing IP assets: {assets_response}"
    
    async def start_negotiation(self, asset_id: str, buyer_address: str, seller_address: str) -> str:
        """Start a new negotiation process for an IP asset."""
        # Get asset details
        asset_details_response = await self.run_tool("GetIPAssetDetails", {"asset_id": asset_id})
        try:
            asset_details = json.loads(asset_details_response)
            if "error" in asset_details:
                return f"Error: Failed to get asset details: {asset_details['error']}"
        except json.JSONDecodeError:
            return f"Error: Failed to get asset details: {asset_details_response}"
        
        # Get valuation
        valuation_prompt = f"Please analyze and value the IP asset with ID {asset_id}."
        valuation_response = await self.valuation_agent.generate_response(valuation_prompt)
        
        # Create license terms if not already present
        license_terms_id = asset_details.get("license_terms_id")
        if not license_terms_id:
            license_terms_response = await self.run_tool("CreateLicenseTerms", {
                "minting_fee": "0.05",  # 0.05 ETH
                "commercial_rev_share": 1000000,  # 10%
                "royalty_policy": "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E",  # From Story docs
                "currency_token": "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"  # From Story docs
            })
            try:
                license_terms_result = json.loads(license_terms_response)
                license_terms_id = license_terms_result.get("licenseTermsId")
                
                # Attach license terms to the IP asset
                await self.run_tool("AttachLicenseTerms", {
                    "ip_id": asset_id,
                    "license_terms_id": license_terms_id
                })
            except json.JSONDecodeError:
                return f"Error: Failed to create license terms: {license_terms_response}"
        
        # Initialize negotiation state
        asking_price = Decimal(asset_details.get("last_sale_price", "1.0")) * Decimal("1.2")  # 20% markup as starting point
        negotiation_id = f"neg-{hash(f'{asset_id}-{buyer_address}-{seller_address}')}"
        self.negotiations[negotiation_id] = NegotiationState(
            asset_id=asset_id,
            seller=seller_address,
            buyer=buyer_address,
            asking_price=asking_price,
            license_terms_id=license_terms_id
        )
        
        # Prepare summary
        summary = {
            "negotiation_id": negotiation_id,
            "asset_id": asset_id,
            "asset_title": asset_details.get("metadata", {}).get("title", "Unknown"),
            "seller": seller_address,
            "buyer": buyer_address,
            "asking_price_eth": str(asking_price),
            "license_terms_id": license_terms_id,
            "valuation_summary": valuation_response[:200] + "..." if len(valuation_response) > 200 else valuation_response,
            "status": "negotiation_started"
        }
        
        return json.dumps(summary, indent=2)
    
    async def process_offer(self, negotiation_id: str, offer_amount: str) -> str:
        """Process a buyer's offer in an ongoing negotiation."""
        if negotiation_id not in self.negotiations:
            return f"Error: Negotiation with ID {negotiation_id} not found"
        
        negotiation = self.negotiations[negotiation_id]
        
        # Update negotiation state
        try:
            offer_decimal = Decimal(offer_amount)
            negotiation.current_offer = offer_decimal
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid offer amount format"
        
        # Send to buyer agent to make formal offer
        buyer_prompt = f"""
        You are representing a buyer interested in IP asset {negotiation.asset_id}.
        Please make an offer of {offer_amount} ETH for this asset.
        Use the buyer address {negotiation.buyer}.
        """
        buyer_response = await self.buyer_agent.generate_response(buyer_prompt)
        
        # Send to seller agent for response
        seller_prompt = f"""
        You have received an offer of {offer_amount} ETH for your IP asset {negotiation.asset_id}.
        The asking price was {negotiation.asking_price} ETH.
        Please decide whether to accept, reject, or counter this offer.
        """
        seller_response = await self.seller_agent.generate_response(seller_prompt)
        
        # If there's a significant gap, involve the negotiation agent
        if offer_decimal < negotiation.asking_price * Decimal("0.8"):
            negotiation_prompt = f"""
            There's a significant gap between the buyer's offer ({offer_amount} ETH) and 
            the seller's asking price ({negotiation.asking_price} ETH) for IP asset {negotiation.asset_id}.
            
            The IP asset has license terms with ID {negotiation.license_terms_id}.
            
            Please suggest a fair compromise and explain your reasoning to both parties.
            """
            mediation_response = await self.negotiation_agent.generate_response(negotiation_prompt)
        else:
            mediation_response = "No mediation required at this time."
        
        # Prepare summary
        summary = {
            "negotiation_id": negotiation_id,
            "asset_id": negotiation.asset_id,
            "buyer": negotiation.buyer,
            "seller": negotiation.seller,
            "asking_price": str(negotiation.asking_price),
            "offer_amount": str(negotiation.current_offer),
            "buyer_response": buyer_response[:200] + "..." if len(buyer_response) > 200 else buyer_response,
            "seller_response": seller_response[:200] + "..." if len(seller_response) > 200 else seller_response,
            "mediation": mediation_response[:200] + "..." if len(mediation_response) > 200 and mediation_response != "No mediation required at this time." else mediation_response,
            "status": "offer_processed"
        }
        
        return json.dumps(summary, indent=2)
    
    async def finalize_transaction(self, negotiation_id: str, accepted_price: str) -> str:
        """Finalize a transaction after buyer and seller have agreed on a price."""
        if negotiation_id not in self.negotiations:
            return f"Error: Negotiation with ID {negotiation_id} not found"
        
        negotiation = self.negotiations[negotiation_id]
        
        try:
            final_price = Decimal(accepted_price)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid price format"
        
        # Update negotiation state
        negotiation.status = "accepted"
        
        # Mint a license token for the buyer
        mint_response = await self.run_tool("MintLicenseToken", {
            "ip_id": negotiation.asset_id,
            "license_terms_id": negotiation.license_terms_id,
            "licensee_address": negotiation.buyer,
            "payment_amount": accepted_price
        })
        
        try:
            mint_result = json.loads(mint_response)
            license_token_id = mint_result.get("licenseTokenId")
            negotiation.license_token_id = license_token_id
            
            # Notify the seller to claim royalties if needed
            royalty_claim_prompt = f"""
            Congratulations! Your IP asset {negotiation.asset_id} has been licensed to {negotiation.buyer} for {accepted_price} ETH.
            
            You can now claim any royalties associated with this transaction using the ClaimRoyalty tool.
            """
            await self.seller_agent.generate_response(royalty_claim_prompt)
            
            # Prepare transaction summary
            summary = {
                "negotiation_id": negotiation_id,
                "asset_id": negotiation.asset_id,
                "buyer": negotiation.buyer,
                "seller": negotiation.seller,
                "final_price": accepted_price,
                "license_token_id": license_token_id,
                "license_terms_id": negotiation.license_terms_id,
                "transaction_status": "completed",
                "message": "The licensing transaction has been successfully completed on Story Protocol"
            }
            
            return json.dumps(summary, indent=2)
        except json.JSONDecodeError:
            return f"Error: Failed to mint license token: {mint_response}"


# Example usage
async def run_example():
    """Run an example negotiation using the agents."""
    dotenv.load_dotenv()  # Load environment variables (e.g., API keys)
    
    # Create the agents
    valuation_agent = ValuationAgent()
    buyer_agent = BuyerAgent()
    seller_agent = SellerAgent()
    negotiation_agent = NegotiationAgent()
    
    coordinator = CoordinatorAgent(
        valuation_agent=valuation_agent,
        buyer_agent=buyer_agent,
        seller_agent=seller_agent,
        negotiation_agent=negotiation_agent
    )
    
    # Create a terminal client for direct interaction
    client = TerminalClient(coordinator)
    
    # Example 1: Browse existing IP assets
    print("Browsing IP assets on Story Protocol...")
    assets_response = await coordinator.browse_ip_assets()
    print(assets_response)
    print()
    
    # Example 2: Register a new IP asset
    print("Registering a new IP asset...")
    metadata = {
        "title": "AI-Generated Masterpiece",
        "description": "A stunning artwork created using cutting-edge AI algorithms",
        "ipType": IPType.IMAGE.value,
        "attributes": [
            {"key": "AI Model", "value": "MidJourney v5"},
            {"key": "Resolution", "value": "4K"},
            {"key": "Style", "value": "Surrealist"}
        ],
        "creators": [
            {"name": "AI Creator", "contributionPercent": 100, "address": "0xdEADbEEf123456789abcdef0123456789abcdef"}
        ],
        "tags": ["AI Art", "Digital", "Surrealism"]
    }
    
    register_response = await coordinator.run_tool("RegisterIPAsset", {
        "metadata": json.dumps(metadata),
        "owner_address": "0xdEADbEEf123456789abcdef0123456789abcdef"
    })
    
    print("Registration Response:")
    print(register_response)
    print()
    
    try:
        register_result = json.loads(register_response)
        asset_id = register_result["ipId"]
        
        # Start a negotiation
        negotiation_response = await coordinator.start_negotiation(
            asset_id=asset_id,
            buyer_address="0xBuYeR123456789abcdef0123456789abcdef",
            seller_address="0xdEADbEEf123456789abcdef0123456789abcdef"
        )
        
        print("Negotiation Started:")
        print(negotiation_response)
        print()
        
        negotiation_result = json.loads(negotiation_response)
        negotiation_id = negotiation_result["negotiation_id"]
        
        # Process an offer
        offer_response = await coordinator.process_offer(
            negotiation_id=negotiation_id,
            offer_amount="0.4"  # ETH
        )
        
        print("Offer Processed:")
        print(offer_response)
        print()
        
        # Finalize the transaction
        transaction_response = await coordinator.finalize_transaction(
            negotiation_id=negotiation_id,
            accepted_price="0.45"  # ETH (after negotiation)
        )
        
        print("Transaction Finalized:")
        print(transaction_response)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except KeyError as e:
        print(f"Missing expected key: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(run_example())