"""
Example Python module for testing vector database ingestion.
"""

def hello_world():
    """Print a greeting message."""
    print("Hello, World!")

class TestClass:
    """Example class for testing."""
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self):
        """Return a greeting message."""
        return f"Hello, {self.name}!"

# Main execution
if __name__ == "__main__":
    test = TestClass("Vector DB")
    print(test.greet())