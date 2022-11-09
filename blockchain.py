from curses import def_prog_mode
import hashlib
import json
from mimetypes import init
from signal import default_int_handler
from time import time
import random
import numpy as np

from graphs_secusca import plot_graphs


NUMBER_OF_NODES = 50

ALPHA = 0.3
ALPHA_0= 0.1
GAMMA = 0.5
GAMMA_0=0.2


MIN_CAPACITY = 50
CAPACITY_INCREMENT = 50

class Block:
    def __init__(self, size, identity):
        self.size= size
        self.identity= identity
      
    def __repr__(self):
        return f"Block(id={self.identity}, size={self.size})"




class Blockchain:
    def __init__(self) -> None:
        self.chain=[]
        self.peers=Network()
        self.nodes_storing_blocks = []
        self.unfairness_values=[]
        

    def add_new_block(self, block):
        self.chain.append(block)

    def mine_block(self):
        new_block= Block(size=0.5, identity=len(self.chain))
        self.delete_blocks()
        self.add_new_block(new_block)
        self.store_new_block(new_block)


    def delete_blocks(self):
        for block in self.chain:
            self.delete_block(block)


    def delete_block(self, block):
        target_replication = self.peers.get_target_replication(block=block,
                                                               blockchain_size=len(self.chain)+1)
        actual_replication = len(self.nodes_storing_blocks[block.identity])
        if actual_replication > target_replication:
            self.delete_block_once(block)
        elif actual_replication < target_replication:
            self.store_block_once(block)


    def store_block_once(self, block):
        nodes_with_enough_space = [node for node in self.peers.nodes
                                       if node.remaining_storage_capacity()>=block.size
                                       and node not in self.nodes_storing_blocks[block.identity]]
        assert len(nodes_with_enough_space) >= 1, "Not enough storage to continue the protocol"
        nodes_for_addition = self.select_nodes_for_storage(nodes = nodes_with_enough_space,
                                                          number_of_nodes=1)
        if nodes_for_addition:
            node_for_addition = nodes_for_addition[0]
            node_for_addition.store_block(block)
            self.nodes_storing_blocks[block.identity].append(node_for_addition)


    def delete_block_once(self, block):
        node_for_deletion = random.choice(self.nodes_storing_blocks[block.identity])
        node_for_deletion.delete_block(block)
        self.nodes_storing_blocks[block.identity].remove(node_for_deletion)

    def store_new_block(self, new_block):
        replication_block= self.peers.get_target_replication(block=new_block, blockchain_size=len(self.chain))
        nodes_with_enough_space = [node for node in self.peers.nodes if node.remaining_storage_capacity()>=new_block.size]
        assert len(nodes_with_enough_space) >= replication_block, "Not enough storage to continue the protocol"
        random_peers = self.select_nodes_for_storage(nodes = nodes_with_enough_space, number_of_nodes=replication_block) 
       
        for node in random_peers:
            node.store_block(new_block)
        
        self.nodes_storing_blocks.append(random_peers)

    def select_nodes_for_storage(self, nodes, number_of_nodes):
        #Dummy function for the mother class
        return []


    def generate_blockchain(self, number_of_blocks):
        for i in range(number_of_blocks):
            self.mine_block()
            self.unfairness_values.append(self.peers.compute_unfairness())
            if (i+1)*10 % number_of_blocks == 0:
                print("Block number ", i+1, "mined")


class Secusca1(Blockchain):
    def select_nodes_for_storage(self, nodes, number_of_nodes):
        return random.sample(nodes, number_of_nodes) 


class Secusca2(Blockchain):
    def select_nodes_for_storage(self, nodes, number_of_nodes):
        remaining_capacities = [node.remaining_storage_capacity() for node in nodes]
        total_capacity = sum(remaining_capacities)
        normalized_remaining_capacities = [capacity/total_capacity for capacity in remaining_capacities]
        return [*np.random.choice(nodes,
                                     size=number_of_nodes,
                                     replace=False,
                                     p=normalized_remaining_capacities)]



class Node:
    def __init__(self, storage_capacity) -> None:
        self.storage_capacity = storage_capacity
        self.blocks_stored = []

    def __repr__(self):
        return f"Node(capacity={self.storage_capacity}, blocks_stored={self.blocks_stored}), remaining capacity={self.remaining_storage_capacity()}"

    def store_block(self, block):
        self.blocks_stored.append(block)

    def stored_blocks_size(self):
        return sum([block.size for block in self.blocks_stored])


    def remaining_storage_capacity(self):
        return self.storage_capacity-self.stored_blocks_size()

    def delete_block(self, block):
        self.blocks_stored.remove(block)



class Network:
    def __init__(self):
        self.nodes = Network._create_nodes(number_nodes=NUMBER_OF_NODES,
                                           min_capacity=MIN_CAPACITY,
                                           capacity_increment=CAPACITY_INCREMENT)

    @staticmethod
    def _create_nodes(number_nodes, min_capacity, capacity_increment ):
        return [Node(storage_capacity = min_capacity+i*capacity_increment)
                    for i in range(number_nodes)]

    def get_target_replication(self, block, blockchain_size):
        block_depth=blockchain_size -1 - block.identity
        gamma_b= int(GAMMA*blockchain_size)
        gamma_0= int(GAMMA_0*blockchain_size)

        if block_depth <= gamma_0:
            block_storage_replication= ALPHA*NUMBER_OF_NODES

        elif block_depth <= gamma_b and block_depth >= gamma_0:
           block_storage_replication= (((ALPHA*NUMBER_OF_NODES - ALPHA_0*NUMBER_OF_NODES) /(gamma_b - gamma_0))* (gamma_b - block_depth)) + ALPHA_0*NUMBER_OF_NODES

        else:
            assert block_depth >= gamma_b
            block_storage_replication= ALPHA_0*NUMBER_OF_NODES

        return int(block_storage_replication)

    def compute_unfairness(self):
        saturation_expectation = sum([node.stored_blocks_size()/node.storage_capacity for node in self.nodes])/len(self.nodes)
        squared_saturation_expectation = sum([(node.stored_blocks_size()/node.storage_capacity)**2 for node in self.nodes])/len(self.nodes)
        return squared_saturation_expectation - saturation_expectation**2
