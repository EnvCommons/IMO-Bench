from openreward.environments import Server

from answerbench import IMOBenchAnswerBench
from gradingbench import IMOBenchGradingBench
from proofbench import IMOBenchProofBench

if __name__ == "__main__":
    server = Server([IMOBenchAnswerBench, IMOBenchGradingBench, IMOBenchProofBench])
    server.run()
