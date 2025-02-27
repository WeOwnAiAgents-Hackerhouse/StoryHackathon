from alphaswarm.core.tool import AlphaSwarmToolBase
from typing import Dict, List, Optional, Tuple, Union, Any
from alphaswarm.services.story import StoryProtocolAPI
import json
from datetime import datetime
from decimal import Decimal
import decimal
from dataclasses import dataclass
from enum import Enum
import requests
from web3 import Web3


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

    async def forward(self, 
                    title: str, 
                    description: str, 
                    ip_type: str, 
                    content_url: str, 
                    creator_name: str = "Anonymous", 
                    creator_address: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    wait_for_transaction: bool = True,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            title: Title of the IP asset
            description: Description of the IP asset
            ip_type: Type of the IP asset
            content_url: URL to the content of the IP asset
            creator_name: Name of the creator
            creator_address: Blockchain address of the creator
            tags: List of tags for the IP asset
            wait_for_transaction: Whether to wait for the transaction to be mined
            network: The network to use ("mainnet" or "testnet")
        """
        try:
            # Validate IP type
            if ip_type not in [t.value for t in IPType]:
                return "Error: Invalid IP type"
            
            # Validate creator address
            if creator_address and not Web3.is_address(creator_address):
                return "Error: Invalid creator address format"
            
            # In a real implementation, this would call the Story Protocol SDK
            # client.ipAsset.mintAndRegisterIpAsset({...})
            asset_id = f"ip-{hash(f'{title}-{description}-{ip_type}-{content_url}-{creator_name}-{creator_address}-{tags}')}"
            return json.dumps({
                "status": "success",
                "ipId": asset_id,
                "txHash": f"0x{hash(asset_id + creator_address):x}",
                "message": "Successfully registered IP asset on Story Protocol"
            })
        except Exception as e:
            return f"Error: {str(e)}"


class GetIPAssetDetails(AlphaSwarmToolBase):
    """Get details about an IP asset registered on Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, ip_id: str, network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            network: The network to use ("mainnet" or "testnet")
        """
        # First try to get real data from Story Protocol
        api = StoryProtocolAPI()
        result = await api.get_ip_asset_details(ip_id)
        
        # If we got an error, fall back to mock data
        if "error" in result:
            # Mock implementation - in reality would query the Story Protocol
            if not ip_id.startswith("ip-"):
                return "Error: Invalid asset ID format"
            
            # Create a mock asset for demonstration
            mock_asset = IPAsset(
                id=ip_id,
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
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    minting_fee: str, 
                    commercial_rev_share: int,
                    royalty_policy: Optional[str] = None,
                    currency_token: Optional[str] = None,
                    wait_for_transaction: bool = True,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            minting_fee: The fee to mint a license token (in ETH)
            commercial_rev_share: Revenue share for commercial use (in basis points)
            royalty_policy: Address of the royalty policy contract (optional)
            currency_token: The token used for payments (optional)
            wait_for_transaction: Whether to wait for the transaction to be mined
            network: The network to use ("mainnet" or "testnet")
        """
        try:
            # Initialize client with the specified network if needed
            if self.client.network != network:
                self.client = StoryProtocolAPI(network=network)
            
            minting_fee_decimal = Decimal(minting_fee)
            if minting_fee_decimal < 0:
                return "Error: Minting fee cannot be negative"
            
            if commercial_rev_share < 0 or commercial_rev_share > 10000:
                return "Error: Commercial revenue share must be between 0 and 10000 basis points"
            
            # Use the provided royalty policy address or get it from the client
            if not royalty_policy:
                royalty_policy = self.client.royalty_policy_lap_address
            
            # Use the provided currency token or a default value
            if not currency_token:
                # This would be a default token address for the network
                currency_token = "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"
            
            # Mock license terms creation
            license_terms_id = f"terms-{hash(f'{minting_fee}-{commercial_rev_share}-{royalty_policy}')}"
            
            return json.dumps({
                "status": "success",
                "licenseTermsId": license_terms_id,
                "mintingFee": minting_fee,
                "commercialRevShare": commercial_rev_share,
                "royaltyPolicy": royalty_policy,
                "currencyToken": currency_token,
                "network": network,
                "message": "Successfully created license terms"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid minting fee format"


class AttachLicenseTerms(AlphaSwarmToolBase):
    """Attach license terms to an IP asset on Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    ip_id: str, 
                    license_terms_id: str,
                    license_template: Optional[str] = None,
                    wait_for_transaction: bool = True,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            license_terms_id: The ID of the license terms
            license_template: The template for the license terms
            wait_for_transaction: Whether to wait for the transaction to be mined
            network: The network to use ("mainnet" or "testnet")
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
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    licensor_ip_id: str, 
                    license_terms_id: str,
                    license_template: str,
                    amount: str = "1",
                    receiver: Optional[str] = None,
                    wait_for_transaction: bool = True,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            licensor_ip_id: The ID of the IP asset
            license_terms_id: The ID of the license terms
            license_template: The template for the license terms
            amount: The amount of license tokens to mint
            receiver: Address of the receiver of the license tokens
            wait_for_transaction: Whether to wait for the transaction to be mined
            network: The network to use ("mainnet" or "testnet")
        """
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                return "Error: Amount must be positive"
            
            if not licensor_ip_id.startswith("ip-"):
                return "Error: Invalid IP asset ID format"
            
            if not license_terms_id.startswith("terms-"):
                return "Error: Invalid license terms ID format"
            
            # Mock license token minting
            license_token_id = f"license-{hash(f'{licensor_ip_id}-{license_terms_id}-{amount}-{receiver}')}"
            
            return json.dumps({
                "status": "success",
                "licenseTokenId": license_token_id,
                "ipId": licensor_ip_id,
                "licenseTermsId": license_terms_id,
                "amount": amount,
                "receiver": receiver,
                "issuanceDate": datetime.now().isoformat(),
                "message": "Successfully minted license token"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid amount format"


class EstimateIPAssetValue(AlphaSwarmToolBase):
    """Estimate the value of an IP asset based on its metadata and market data."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    ip_id: str, 
                    market_data: Optional[Dict[str, Any]] = None,
                    network: str = "testnet") -> str:
        """
        Estimate the value of an IP asset.
        
        Args:
            ip_id: The ID of the IP asset
            market_data: Optional dictionary containing market data
            network: The network to use ("mainnet" or "testnet")
            
        Returns:
            Estimated value range for the IP asset
        """
        # In a real implementation, this would analyze market data and asset properties
        if not ip_id.startswith("ip-"):
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
            "asset_id": ip_id,
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
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    ip_id: str, 
                    offer_amount: str,
                    buyer_address: str,
                    expiration_days: int = 7,
                    license_terms_id: Optional[str] = None,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            offer_amount: Offer amount in ETH
            buyer_address: Address of the buyer
            expiration_days: Expiration period in days
            license_terms_id: The ID of the license terms
            network: The network to use ("mainnet" or "testnet")
        """
        try:
            offer_amount_decimal = Decimal(offer_amount)
            if offer_amount_decimal <= 0:
                return "Error: Offer amount must be positive"
            
            expiration = datetime.now().replace(microsecond=0) + timedelta(days=expiration_days)
            
            # Mock offer creation
            offer_id = f"offer-{hash(f'{ip_id}-{buyer_address}-{offer_amount}-{expiration}')}"
            
            return json.dumps({
                "status": "success",
                "offer_id": offer_id,
                "asset_id": ip_id,
                "buyer": buyer_address,
                "amount_eth": offer_amount,
                "expiration": expiration.isoformat(),
                "license_terms_id": license_terms_id,
                "message": "Offer successfully submitted"
            }, indent=2)
        except (ValueError, decimal.InvalidOperation):
            return "Error: Invalid offer amount format"


class RespondToOffer(AlphaSwarmToolBase):
    """Respond to an offer for an IP asset (accept, reject, or counter)."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    negotiation_id: str, 
                    response: str,
                    counter_offer: Optional[str] = None,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            negotiation_id: The ID of the negotiation
            response: One of "accept", "reject", or "counter"
            counter_offer: If response is "counter", the counter offer amount in ETH
            network: The network to use ("mainnet" or "testnet")
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
            "negotiation_id": negotiation_id,
            "response": response,
            "counter_offer": counter_offer if response == "counter" else None,
            "message": f"Successfully {response}ed the offer"
        }, indent=2)


class ClaimRoyalty(AlphaSwarmToolBase):
    """Claim royalties for an IP asset on Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    ip_id: str, 
                    recipient: Optional[str] = None,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality.

        Args:
            ip_id: The ID of the IP asset
            recipient: Address of the recipient
            network: The network to use ("mainnet" or "testnet")
        """
        # In a real implementation, this would call the Story Protocol SDK
        # client.royalty.claimRoyalty({...})
        
        # Mock royalty amount
        import random
        royalty_amount = Decimal(str(random.uniform(0.01, 0.5)))
        
        return json.dumps({
            "status": "success",
            "ip_id": ip_id,
            "recipient": recipient,
            "amount_claimed": str(royalty_amount),
            "currency": "ETH",
            "message": f"Successfully claimed {royalty_amount} ETH in royalties"
        })


class DisputeIPAsset(AlphaSwarmToolBase):
    """Dispute an IP asset on Story Protocol."""
    
    def __init__(self, client: Optional[StoryProtocolAPI] = None):
        super().__init__()
        self.client = client or StoryProtocolAPI()
    
    async def forward(self, 
                    target_ip_id: str, 
                    target_tag: str, 
                    cid: str, 
                    bond: str = "0", 
                    liveness: str = "2592000",
                    wait_for_transaction: bool = True,
                    network: str = "testnet") -> str:
        """Execute the tool's core functionality to raise a dispute against an IP asset.

        Args:
            target_ip_id: The IP ID that is the target of the dispute.
            target_tag: The target tag of the dispute, must be one of the whitelisted tags.
            cid: IPFS Content Identifier that contains the dispute evidence.
            bond: The bond amount in native currency.
            liveness: The liveness period in seconds.
            wait_for_transaction: Whether to wait for the transaction to be mined.
            network: The network to use ("mainnet" or "testnet").
        
        Returns:
            JSON string containing the dispute information and transaction result.
        """
        try:
            # Initialize client with the specified network
            if self.client.network != network:
                self.client = StoryProtocolAPI(network=network)
            
            # Convert parameters
            liveness_value = int(liveness)
            bond_value = int(bond)
            
            # Validate parameters
            min_liveness = await self.client.get_min_liveness()
            max_liveness = await self.client.get_max_liveness()
            
            if liveness_value < min_liveness or liveness_value > max_liveness:
                raise ValueError(f"Liveness must be between {min_liveness} and {max_liveness}.")
            
            # Get token address for the chain
            token_address = "0x0000000000000000000000000000000000000000"  # Native token
            
            max_bonds = await self.client.get_max_bonds(token_address)
            if bond_value > max_bonds:
                raise ValueError(f"Bond must be less than {max_bonds}.")
            
            # Check if tag is whitelisted
            is_whitelisted = await self.client.is_whitelisted_dispute_tag(target_tag)
            if not is_whitelisted:
                raise ValueError(f"The target tag {target_tag} is not whitelisted.")
            
            # Convert CID to hash format
            dispute_evidence_hash = await self.client.convert_cid_to_hash(cid)
            
            # Get the dispute module address from the client
            dispute_module_address = self.client.dispute_module_address
            if not dispute_module_address or dispute_module_address == "0x0":
                raise ValueError("Dispute module address not configured.")
            
            # Encode parameters for the contract call
            encoded_data = Web3.solidity_keccak(
                ['uint64', 'address', 'uint256'],
                [liveness_value, token_address, bond_value]
            ).hex()
            
            # Prepare transaction
            tx_data = {
                'targetIpId': target_ip_id,
                'targetTag': Web3.solidity_keccak(['string'], [target_tag]).hex(),
                'disputeEvidenceHash': dispute_evidence_hash,
                'data': encoded_data,
                'disputeModuleAddress': dispute_module_address
            }
            
            # In a real implementation, this would send the transaction
            # tx_hash = await self.send_transaction(tx_data)
            tx_hash = f"0x{hash(str(tx_data)):064x}"  # Mock transaction hash
            
            response = {
                "txHash": tx_hash,
                "network": network,
                "disputeModuleAddress": dispute_module_address
            }
            
            # If waiting for transaction
            if wait_for_transaction:
                # In a real implementation, this would wait for the transaction receipt
                # receipt = await self.client.web3.eth.wait_for_transaction_receipt(tx_hash)
                # dispute_id = self.extract_dispute_id_from_logs(receipt)
                dispute_id = f"0x{hash(tx_hash):064x}"  # Mock dispute ID
                response["disputeId"] = dispute_id
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Failed to raise dispute: {str(e)}"
            }
            return json.dumps(error_response, indent=2)
    
    async def send_transaction(self, tx_data: Dict[str, Any]) -> str:
        """Send a transaction to the dispute module contract."""
        # This would use web3.py to send the transaction
        # Example implementation:
        # contract = self.client.web3.eth.contract(
        #     address=self.client.dispute_module_address,
        #     abi=dispute_module_abi
        # )
        # tx = contract.functions.raiseDispute(
        #     tx_data['targetIpId'],
        #     tx_data['targetTag'],
        #     tx_data['disputeEvidenceHash'],
        #     tx_data['data']
        # ).build_transaction({
        #     'from': self.client.web3.eth.accounts[0],
        #     'gas': 2000000,
        #     'gasPrice': self.client.web3.eth.gas_price,
        #     'nonce': self.client.web3.eth.get_transaction_count(self.client.web3.eth.accounts[0])
        # })
        # signed_tx = self.client.web3.eth.account.sign_transaction(tx, private_key)
        # tx_hash = self.client.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # return tx_hash.hex()
        pass
    
    def extract_dispute_id_from_logs(self, receipt: Dict[str, Any]) -> str:
        """Extract the dispute ID from transaction logs."""
        # This would parse the logs to find the DisputeRaised event
        # and extract the disputeId from it
        pass

