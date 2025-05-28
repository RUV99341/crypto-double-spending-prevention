import time
import logging
import json
import os
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AlertSystem:
    """
    Alert system for the cryptocurrency network to notify users about 
    potential security issues, double-spending attempts, and other suspicious activities.
    This class handles creation, distribution, and logging of alerts.
    """
    
    def __init__(self, node_id: str, log_file: str = "alerts.log"):
        """
        Initialize the alert system.
        
        Args:
            node_id: Identifier of the node that owns this alert system
            log_file: Path to file where alerts will be logged
        """
        self.node_id = node_id
        self.log_file = log_file
        self.logger = logging.getLogger(f"AlertSystem-{node_id}")
        self.logger.info(f"Alert system initialized for node {node_id}")
        
        # Create an alert log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("[]")  # Initialize with empty JSON array
        
        # In-memory cache of recent alerts to avoid duplicates
        self.recent_alerts = []
        self.max_recent_alerts = 1000  # Keep track of last 1000 alerts

    def send_alert(self, user_id: str, message: str) -> bool:
        """
        Send an alert message to a specific user.
        
        Args:
            user_id: Identifier of the user to send the alert to (wallet address)
            message: Alert message content
            
        Returns:
            True if alert was successfully sent, False otherwise
        """
        try:
            # Generate a unique alert ID
            alert_id = f"{int(time.time())}-{hash(message) % 10000}"
            
            # Create alert data structure
            alert_data = {
                "alert_id": alert_id,
                "user_id": user_id,
                "message": message,
                "timestamp": time.time(),
                "node_id": self.node_id,
                "acknowledged": False
            }
            
            # In a real system, this would send the alert through a messaging system
            # For simulation purposes, we log it
            self.logger.info(f"ALERT to {user_id}: {message}")
            
            # Log the alert
            self.log_alert(alert_data)
            
            # Store in recent alerts
            self._add_to_recent_alerts(alert_data)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to send alert to {user_id}: {e}")
            return False

    def broadcast_alert(self, peers: List[str], alert: Dict[str, Any]) -> bool:
        """
        Broadcast an alert to all peers in the network.
        
        Args:
            peers: List of peer addresses
            alert: Alert data dictionary
            
        Returns:
            True if broadcast was successful, False otherwise
        """
        try:
            # Add broadcast metadata
            broadcast_alert = alert.copy()
            broadcast_alert.update({
                "broadcast_timestamp": time.time(),
                "origin_node": self.node_id,
                "broadcast_id": f"bcast-{int(time.time())}-{hash(str(alert)) % 10000}"
            })
            
            # In a real system, this would actually send to peers
            # For simulation, we log it
            self.logger.info(f"Broadcasting alert to {len(peers)} peers: {broadcast_alert}")
            
            # Example of what would happen in a real system:
            # for peer in peers:
            #     try:
            #         self._send_to_peer(peer, broadcast_alert)
            #     except Exception as e:
            #         self.logger.warning(f"Failed to send alert to peer {peer}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to broadcast alert: {e}")
            return False

    def log_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Log an alert to the alert history file.
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            True if logging was successful, False otherwise
        """
        try:
            # Read existing alerts
            alerts = []
            with open(self.log_file, 'r') as f:
                try:
                    alerts = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Alert log file {self.log_file} was corrupted, creating new")
                    alerts = []
            
            # Add new alert
            alerts.append(alert_data)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log alert: {e}")
            return False

    def get_alert_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the history of alerts, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter alerts by
            
        Returns:
            List of alert dictionaries
        """
        try:
            # Read alert history
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            # Filter by user_id if specified
            if user_id:
                alerts = [alert for alert in alerts if alert.get('user_id') == user_id]
                
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get alert history: {e}")
            return []

    def generate_alert_message(self, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable alert message from alert data.
        
        Args:
            data: Alert data dictionary
            
        Returns:
            Formatted alert message string
        """
        alert_type = data.get('type', 'unknown')
        
        if alert_type == 'double_spending':
            return (f"⚠️ DOUBLE-SPENDING ATTEMPT DETECTED: Transaction {data.get('transaction_id')} "
                    f"appears to be a double-spending attempt by {data.get('sender')}.")
                    
        elif alert_type == 'potential_fraud':
            return (f"⚠️ SUSPICIOUS TRANSACTION DETECTED: Transaction {data.get('transaction_id')} "
                    f"from {data.get('sender')} to {data.get('receiver')} "
                    f"of amount {data.get('amount')} has been flagged as potentially fraudulent "
                    f"(fraud score: {data.get('fraud_score', 'unknown')}).")
                    
        elif alert_type == 'network_attack':
            return (f"⚠️ POTENTIAL NETWORK ATTACK: Unusual network activity detected. "
                    f"Multiple connection attempts from {data.get('source', 'unknown source')}.")
                    
        elif alert_type == 'chain_reorg':
            return (f"⚠️ BLOCKCHAIN REORGANIZATION: A chain reorganization has been detected. "
                    f"This could indicate a potential 51% attack.")
                    
        else:
            return f"⚠️ SECURITY ALERT: {data.get('message', 'Unknown security issue detected.')}"

    def mark_alert_acknowledged(self, alert_id: str) -> bool:
        """
        Mark an alert as acknowledged by the user.
        
        Args:
            alert_id: ID of the alert to mark as acknowledged
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing alerts
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            # Find and update the alert
            for alert in alerts:
                if alert.get('alert_id') == alert_id:
                    alert['acknowledged'] = True
                    alert['acknowledged_time'] = time.time()
                    
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mark alert {alert_id} as acknowledged: {e}")
            return False

    def _add_to_recent_alerts(self, alert: Dict[str, Any]) -> None:
        """
        Add an alert to the recent alerts cache and maintain its maximum size.
        
        Args:
            alert: Alert data dictionary
        """
        self.recent_alerts.append(alert)
        
        # Keep the cache within size limits
        if len(self.recent_alerts) > self.max_recent_alerts:
            self.recent_alerts = self.recent_alerts[-self.max_recent_alerts:]

    def is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Check if an alert is a duplicate of a recent alert.
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            True if alert is a duplicate, False otherwise
        """
        # Simplified duplicate check based on message and user_id
        for recent_alert in self.recent_alerts:
            if (recent_alert.get('message') == alert.get('message') and
                recent_alert.get('user_id') == alert.get('user_id') and
                time.time() - recent_alert.get('timestamp', 0) < 3600):  # Within last hour
                return True
                
        return False

    def get_unacknowledged_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all unacknowledged alerts for a specific user.
        
        Args:
            user_id: User ID to get alerts for
            
        Returns:
            List of unacknowledged alert dictionaries
        """
        try:
            # Read alert history
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            # Filter by user_id and acknowledged status
            unacknowledged = [
                alert for alert in alerts 
                if alert.get('user_id') == user_id and not alert.get('acknowledged', False)
            ]
                
            return unacknowledged
            
        except Exception as e:
            self.logger.error(f"Failed to get unacknowledged alerts for {user_id}: {e}")
            return []

    def detect_alert_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze alert history to detect patterns or repeated issues.
        
        Returns:
            List of pattern dictionaries with potential security insights
        """
        try:
            # Read alert history
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
                
            patterns = []
            
            # Check for repeated fraudulent activity from the same address
            sender_fraud_count = {}
            for alert in alerts:
                if alert.get('type') == 'potential_fraud' or alert.get('type') == 'double_spending':
                    sender = alert.get('sender')
                    if sender:
                        sender_fraud_count[sender] = sender_fraud_count.get(sender, 0) + 1
            
            # Identify frequent offenders
            for sender, count in sender_fraud_count.items():
                if count >= 3:  # Example threshold
                    patterns.append({
                        'pattern_type': 'repeated_fraud',
                        'address': sender,
                        'count': count,
                        'description': f"Address {sender} has been involved in {count} fraudulent activities"
                    })
            
            # Check for targeted attacks (multiple alerts for the same user)
            user_alert_count = {}
            for alert in alerts:
                user_id = alert.get('user_id')
                if user_id:
                    user_alert_count[user_id] = user_alert_count.get(user_id, 0) + 1
            
            # Identify frequently targeted users
            for user_id, count in user_alert_count.items():
                if count >= 5:  # Example threshold
                    patterns.append({
                        'pattern_type': 'targeted_user',
                        'user_id': user_id,
                        'count': count,
                        'description': f"User {user_id} has received {count} security alerts"
                    })
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to detect alert patterns: {e}")
            return []

    def analyze_network_health(self) -> Dict[str, Any]:
        """
        Analyze alerts to determine overall network health and security status.
        
        Returns:
            Dictionary with network health metrics
        """
        try:
            # Read alert history
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            # Calculate metrics
            total_alerts = len(alerts)
            
            # Count alerts by type
            alert_types = {}
            for alert in alerts:
                alert_type = alert.get('type', 'unknown')
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
            
            # Count recent alerts (last 24 hours)
            recent_time = time.time() - (24 * 3600)
            recent_alerts = [a for a in alerts if a.get('timestamp', 0) > recent_time]
            
            # Calculate threat level based on recent alerts
            threat_level = "low"
            if len(recent_alerts) > 50:
                threat_level = "critical"
            elif len(recent_alerts) > 20:
                threat_level = "high"
            elif len(recent_alerts) > 5:
                threat_level = "medium"
            
            return {
                "total_alerts": total_alerts,
                "alert_types": alert_types,
                "recent_alerts": len(recent_alerts),
                "threat_level": threat_level,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze network health: {e}")
            return {
                "error": str(e),
                "threat_level": "unknown",
                "timestamp": time.time()
            }

    def clear_old_alerts(self, days: int = 30) -> int:
        """
        Remove alerts older than the specified number of days.
        
        Args:
            days: Number of days to keep alerts for
            
        Returns:
            Number of alerts removed
        """
        try:
            # Read alert history
            with open(self.log_file, 'r') as f:
                alerts = json.load(f)
            
            # Calculate cutoff timestamp
            cutoff_time = time.time() - (days * 24 * 3600)
            
            # Filter out old alerts
            old_count = len(alerts)
            alerts = [alert for alert in alerts if alert.get('timestamp', 0) > cutoff_time]
            removed_count = old_count - len(alerts)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(alerts, f, indent=2)
                
            self.logger.info(f"Removed {removed_count} old alerts")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to clear old alerts: {e}")
            return 0


# Example usage if this file is run directly
if __name__ == "__main__":
    # Create an alert system instance
    alert_system = AlertSystem("test_node")
    
    # Send a test alert
    alert_system.send_alert("test_user", "This is a test alert message")
    
    # Broadcast an alert to simulated peers
    test_peers = ["peer1", "peer2", "peer3"]
    alert_system.broadcast_alert(test_peers, {
        "type": "double_spending",
        "transaction_id": "tx123456",
        "sender": "address1234",
        "timestamp": time.time()
    })
    
    # Generate a formatted alert message
    alert_data = {
        "type": "potential_fraud",
        "transaction_id": "tx789012",
        "sender": "address5678",
        "receiver": "address9012",
        "amount": 100.0,
        "fraud_score": 0.85
    }
    message = alert_system.generate_alert_message(alert_data)
    print(message)
    
    # Check for alert patterns
    patterns = alert_system.detect_alert_patterns()
    for pattern in patterns:
        print(f"Pattern detected: {pattern['description']}")