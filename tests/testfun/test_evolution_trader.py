import numpy as np
import matplotlib.pyplot as plt

class GeneFrequencySimulator:
    def __init__(self, initial_frequency, fitness_A, fitness_a):
        """
        Initialize the simulator with starting conditions
        
        Args:
            initial_frequency (float): Initial frequency of allele A (between 0 and 1)
            fitness_A (float): Relative fitness of genotype A
            fitness_a (float): Relative fitness of genotype a
        """
        self.p = initial_frequency  # frequency of allele A
        self.w_A = fitness_A       # fitness of A allele
        self.w_a = fitness_a       # fitness of a allele
        self.frequency_history = [initial_frequency]
        
    def simulate(self, num_generations):
        """
        Run the simulation for specified number of generations
        
        Args:
            num_generations (int): Number of generations to simulate
        """
        for _ in range(num_generations):
            # Calculate genotype frequencies
            freq_AA = self.p ** 2
            freq_Aa = 2 * self.p * (1 - self.p)
            freq_aa = (1 - self.p) ** 2
            
            # Calculate mean fitness
            mean_fitness = (self.w_A * (freq_AA + 0.5 * freq_Aa) + 
                          self.w_a * (freq_aa + 0.5 * freq_Aa))
            
            # Calculate new allele frequency
            self.p = (self.w_A * (freq_AA + 0.5 * freq_Aa)) / mean_fitness
            
            # Store the frequency
            self.frequency_history.append(self.p)
    
    def plot_result(self):
        """Plot the frequency changes over generations"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.frequency_history)
        plt.xlabel('Generation')
        plt.ylabel('Frequency of Allele A')
        plt.title('Change in Allele Frequency Over Time')
        plt.grid(True)
        plt.show()
    
    def get_final_frequency(self):
        """Return the final frequency of allele A"""
        return self.frequency_history[-1] 

def test_simulator():
    simulator = GeneFrequencySimulator(
        initial_frequency = 0.5,
        fitness_A = 1.2,
        fitness_a = 1.0
    )
    simulator.simulate(num_generations=500)
    simulator.plot_result()
    print(simulator.get_final_frequency())

# Write an explaintory example to explain and calculate 适应度 in evolutionary biology
def fitness_example():
    pass

if __name__ == "__main__":
    test_simulator()