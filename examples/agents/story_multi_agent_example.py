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
from alphaswarm.tools.story import QueryStoryIPAssets, RegisterIPAsset, GetIPAssetDetails, CreateLicenseTerms, AttachLicenseTerms, MintLicenseToken, EstimateIPAssetValue, MakeOffer, RespondToOffer, ClaimRoyalty, DisputeIPAsset
from alphaswarm.services.story import StoryProtocolAPI
from alphaswarm.tools.story import IPAsset, IPMetadata, IPType, NegotiationState



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
                 seller_agent: SellerAgent, negotiation_agent: NegotiationAgent,
                 network: str = "mainnet"):
        self.valuation_agent = valuation_agent
        self.buyer_agent = buyer_agent
        self.seller_agent = seller_agent
        self.negotiation_agent = negotiation_agent
        self.negotiations = {}  # Track ongoing negotiations
        self.network = network  # "mainnet" or "testnet"
        
        # Initialize the Story Protocol API with the specified network
        self.story_api = StoryProtocolAPI(network=network)
        
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
        asset_details_response = await self.run_tool("GetIPAssetDetails", {
            "asset_id": asset_id,
            "network": self.network
        })
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
            # Get the royalty policy address from the API
            royalty_policy = self.story_api.royalty_policy_lap_address
            
            license_terms_response = await self.run_tool("CreateLicenseTerms", {
                "minting_fee": "0.05",  # 0.05 ETH
                "commercial_rev_share": 1000000,  # 10%
                "royalty_policy": royalty_policy,
                "network": self.network
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
async def run_example(network: str = "mainnet"):
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
        negotiation_agent=negotiation_agent,
        network=network
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
    # You can change this to "testnet" to use testnet addresses
    network = os.getenv("STORY_NETWORK", "mainnet")
    asyncio.run(run_example(network))