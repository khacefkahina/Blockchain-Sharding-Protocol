from blockchain import Block, Node, Blockchain, Secusca1, Secusca2
from graphs_secusca import plot_graphs
    

NUMBER_OF_BLOCKS = 5000

blockchain = Blockchain()
blockchain.generate_blockchain(number_of_blocks=100)
secusca_1 = Secusca1()
secusca_1.generate_blockchain(number_of_blocks=NUMBER_OF_BLOCKS)
secusca_2 = Secusca2()
secusca_2.generate_blockchain(number_of_blocks=NUMBER_OF_BLOCKS)


y_info_challenger = {"label":"SecuSca_2"}
y_info_baseline = {"label":"SecuSca_1"}


file_name = "number_of_blocks_stored_by-SecuSca_1"
graph_name = "Unfairness metric"

graph_info = {"file_name": file_name, "graph_name": graph_name}

plot_graphs(x_axis=list(range(NUMBER_OF_BLOCKS)),
           y_baseline=secusca_1.unfairness_values,
           y_challenger=secusca_2.unfairness_values,
           y_info_baseline=y_info_baseline,
           y_info_challenger=y_info_challenger,
           graph_info=graph_info
           )


    
