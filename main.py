from blockchain import Blockchain
from blockchain.block import Block
from network.node import Node
from wallet.wallet import Wallet

def main():
    # Initialize Blockchain
    blockchain = Blockchain()
    
    # Create and Add a New Block
    new_block = Block(1, "Transaction Data", blockchain.chain[-1].hash)
    blockchain.add_block(new_block)

    # Verify Blockchain
    print("Blockchain Valid:", blockchain.is_chain_valid())

    # Start a P2P Node
    node = Node()
    # Uncomment the next line to start the server (it will run indefinitely)
    node.start_server()

    # Create Wallet
    wallet = Wallet()
    wallet.save_keys()
    print("Wallet created successfully.")

if __name__ == "__main__":
    main()
# from ui.gui import CryptocurrencyApp
# import tkinter as tk

# if __name__ == '__main__':
#     root = tk.Tk()
#     app = CryptocurrencyApp(root)
#     app.protocol("WM_DELETE_WINDOW", app.on_closing)
#     root.mainloop()
