import os
import requests
import json
from web3 import Web3
from typing import Dict, Any, List, Optional


class StoryProtocolAPI:
    """Helper class to interact with Story Protocol's RPC endpoint."""
    
    def __init__(self, rpc_url=None, network="mainnet"):
        self.rpc_url = rpc_url or os.getenv("STORY_RPC_URL", "https://aeneid.storyrpc.io")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.network = network  # "mainnet" or "testnet"
        
        # Load contract addresses from JSON file
        self.addresses = self._load_addresses()
        
        # Set contract addresses based on the network
        self.dispute_module_address = self.addresses.get(self.network, {}).get("core", {}).get("DisputeModule")
        self.arbitration_policy_address = self.addresses.get(self.network, {}).get("core", {}).get("ArbitrationPolicyUMA")
        self.ip_asset_registry_address = self.addresses.get(self.network, {}).get("core", {}).get("IPAssetRegistry")
        self.royalty_policy_lap_address = self.addresses.get(self.network, {}).get("core", {}).get("RoyaltyPolicyLAP")
        self.royalty_policy_lrp_address = self.addresses.get(self.network, {}).get("core", {}).get("RoyaltyPolicyLRP")
        self.license_registry_address = self.addresses.get(self.network, {}).get("core", {}).get("LicenseRegistry")
    
    def _load_addresses(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Load contract addresses from the JSON file."""
        try:
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            addresses_file = os.path.join(current_dir, "addresses.json")
            
            with open(addresses_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading addresses: {e}")
            return {"mainnet": {"core": {}, "pheriphery": {}}, "testnet": {"core": {}, "pheriphery": {}}}
    
    def get_address(self, contract_name: str, category: str = "core") -> str:
        """Get a contract address by name and category."""
        return self.addresses.get(self.network, {}).get(category, {}).get(contract_name, "0x0")
    
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
    
    async def get_min_liveness(self) -> int:
        """
        Get minimum liveness period from the arbitration policy.
        
        Returns:
            Minimum liveness period in seconds
        """
        try:
            params = {
                "method": "story_getMinLiveness",
                "params": [],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", 86400)  # Default to 1 day
                return int(result)
            else:
                return 86400  # Default to 1 day if request fails
        except Exception:
            return 86400  # Default to 1 day if any error occurs
    
    async def get_max_liveness(self) -> int:
        """
        Get maximum liveness period from the arbitration policy.
        
        Returns:
            Maximum liveness period in seconds
        """
        try:
            params = {
                "method": "story_getMaxLiveness",
                "params": [],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", 2592000)  # Default to 30 days
                return int(result)
            else:
                return 2592000  # Default to 30 days if request fails
        except Exception:
            return 2592000  # Default to 30 days if any error occurs
    
    async def get_max_bonds(self, token_address: str) -> int:
        """
        Get maximum bond amount for the given token.
        
        Args:
            token_address: Address of the token
            
        Returns:
            Maximum bond amount in wei
        """
        try:
            params = {
                "method": "story_getMaxBonds",
                "params": [token_address],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", 1000000000000000000)  # Default to 1 ETH
                return int(result)
            else:
                return 1000000000000000000  # Default to 1 ETH if request fails
        except Exception:
            return 1000000000000000000  # Default to 1 ETH if any error occurs
    
    async def is_whitelisted_dispute_tag(self, tag: str) -> bool:
        """
        Check if a dispute tag is whitelisted.
        
        Args:
            tag: The dispute tag to check
            
        Returns:
            True if the tag is whitelisted, False otherwise
        """
        try:
            params = {
                "method": "story_isWhitelistedDisputeTag",
                "params": [tag],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", False)
                return bool(result)
            else:
                # If request fails, check against known whitelisted tags
                whitelisted_tags = ["IMPROPER_REGISTRATION", "IMPROPER_USAGE", 
                                   "IMPROPER_PAYMENT", "CONTENT_STANDARDS_VIOLATION"]
                return tag in whitelisted_tags
        except Exception:
            # If any error occurs, check against known whitelisted tags
            whitelisted_tags = ["IMPROPER_REGISTRATION", "IMPROPER_USAGE", 
                               "IMPROPER_PAYMENT", "CONTENT_STANDARDS_VIOLATION"]
            return tag in whitelisted_tags
    
    async def convert_cid_to_hash(self, cid: str) -> str:
        """
        Convert IPFS Content Identifier to hash format.
        
        Args:
            cid: IPFS Content Identifier
            
        Returns:
            Hash representation of the CID
        """
        try:
            params = {
                "method": "story_convertCIDtoHash",
                "params": [cid],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", "")
                return result
            else:
                # If request fails, generate a mock hash
                return f"0x{hash(cid):064x}"
        except Exception:
            # If any error occurs, generate a mock hash
            return f"0x{hash(cid):064x}"
    
    async def raise_dispute(self, target_ip_id: str, target_tag: str, cid: str, 
                           bond: int = 0, liveness: int = 2592000, 
                           wait_for_transaction: bool = True) -> Dict[str, Any]:
        """
        Raise a dispute against an IP asset.
        
        Args:
            target_ip_id: The IP ID that is the target of the dispute
            target_tag: The target tag of the dispute
            cid: IPFS Content Identifier that contains the dispute evidence
            bond: The bond amount in native currency
            liveness: The liveness period in seconds
            wait_for_transaction: Whether to wait for the transaction to be mined
            
        Returns:
            Dictionary containing the dispute information and transaction result
        """
        try:
            # Validate parameters
            min_liveness = await self.get_min_liveness()
            max_liveness = await self.get_max_liveness()
            
            if liveness < min_liveness or liveness > max_liveness:
                return {
                    "status": "error",
                    "message": f"Liveness must be between {min_liveness} and {max_liveness}."
                }
            
            # Get token address for the chain
            token_address = "0x0000000000000000000000000000000000000000"  # Native token
            
            max_bonds = await self.get_max_bonds(token_address)
            if bond > max_bonds:
                return {
                    "status": "error",
                    "message": f"Bond must be less than {max_bonds}."
                }
            
            # Check if tag is whitelisted
            is_whitelisted = await self.is_whitelisted_dispute_tag(target_tag)
            if not is_whitelisted:
                return {
                    "status": "error",
                    "message": f"The target tag {target_tag} is not whitelisted."
                }
            
            # Convert CID to hash format
            dispute_evidence_hash = await self.convert_cid_to_hash(cid)
            
            # Use the dispute module address from the loaded addresses
            dispute_module_address = self.dispute_module_address
            if not dispute_module_address or dispute_module_address == "0x0":
                return {
                    "status": "error",
                    "message": "Dispute module address not configured."
                }
            
            # Encode parameters for the contract call
            encoded_data = Web3.solidity_keccak(
                ['uint64', 'address', 'uint256'],
                [liveness, token_address, bond]
            ).hex()
            
            # Prepare transaction parameters
            params = {
                "method": "story_raiseDispute",
                "params": [{
                    "targetIpId": target_ip_id,
                    "targetTag": Web3.solidity_keccak(['string'], [target_tag]).hex(),
                    "disputeEvidenceHash": dispute_evidence_hash,
                    "data": encoded_data,
                    "waitForTransaction": wait_for_transaction
                }],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            # Send the transaction
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", {})
                return result
            else:
                return {
                    "status": "error",
                    "message": f"Failed to raise dispute: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error raising dispute: {str(e)}"
            }
    
    async def get_dispute_details(self, dispute_id: str) -> Dict[str, Any]:
        """
        Get details about a dispute.
        
        Args:
            dispute_id: The ID of the dispute
            
        Returns:
            Dictionary containing the dispute details
        """
        try:
            params = {
                "method": "story_getDispute",
                "params": [dispute_id],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", {})
                return result
            else:
                return {"error": f"Failed to fetch dispute details: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error querying dispute: {str(e)}"}
    
    async def get_disputes_by_ip(self, ip_id: str) -> List[Dict[str, Any]]:
        """
        Get all disputes for a specific IP asset.
        
        Args:
            ip_id: The ID of the IP asset
            
        Returns:
            List of disputes for the IP asset
        """
        try:
            params = {
                "method": "story_getDisputesByIp",
                "params": [ip_id],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", [])
                return result
            else:
                return {"error": f"Failed to fetch disputes: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error querying disputes: {str(e)}"}
    
    async def get_whitelisted_dispute_tags(self) -> List[str]:
        """
        Get all whitelisted dispute tags.
        
        Returns:
            List of whitelisted dispute tags
        """
        try:
            params = {
                "method": "story_getWhitelistedDisputeTags",
                "params": [],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", [])
                return result
            else:
                # Return default tags if request fails
                return ["IMPROPER_REGISTRATION", "IMPROPER_USAGE", 
                       "IMPROPER_PAYMENT", "CONTENT_STANDARDS_VIOLATION"]
        except Exception:
            # Return default tags if any error occurs
            return ["IMPROPER_REGISTRATION", "IMPROPER_USAGE", 
                   "IMPROPER_PAYMENT", "CONTENT_STANDARDS_VIOLATION"]
    
    async def vote_on_dispute(self, dispute_id: str, vote: bool) -> Dict[str, Any]:
        """
        Vote on a dispute.
        
        Args:
            dispute_id: The ID of the dispute
            vote: True to vote in favor, False to vote against
            
        Returns:
            Dictionary containing the vote result
        """
        try:
            params = {
                "method": "story_voteOnDispute",
                "params": [dispute_id, vote],
                "id": 1,
                "jsonrpc": "2.0"
            }
            
            response = requests.post(self.rpc_url, json=params)
            if response.status_code == 200:
                result = response.json().get("result", {})
                return result
            else:
                return {"error": f"Failed to vote on dispute: {response.status_code}"}
        except Exception as e:
            return {"error": f"Error voting on dispute: {str(e)}"}
