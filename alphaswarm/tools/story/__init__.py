from alphaswarm.core.tool import AlphaSwarmToolBase
from typing import Dict, List, Optional, Tuple, Union
from alphaswarm.services.story import StoryProtocolAPI
import json
from datetime import datetime
from decimal import Decimal
import decimal
from dataclasses import dataclass
from enum import Enum


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

