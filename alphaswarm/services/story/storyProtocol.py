
import os
import requests


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
