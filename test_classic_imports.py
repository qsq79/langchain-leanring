#!/usr/bin/env python3
"""
Test imports from langchain_classic where legacy components now live
"""

print("Testing langchain_classic imports:")
print("=" * 50)

# Test Memory Components from langchain_classic
print("\n1. Memory Components:")
memory_imports = [
    "from langchain_classic.memory import ConversationBufferMemory",
    "from langchain_classic.memory import ConversationSummaryMemory",
    "from langchain_classic.memory import ConversationBufferWindowMemory",
    "from langchain_classic.memory import ConversationTokenBufferMemory",
    "from langchain_classic.memory import ConversationKGMemory",
    "from langchain_classic.memory import ConversationEntityMemory",
    "from langchain_classic.memory import VectorStoreRetrieverMemory",
    "from langchain_classic.memory import CombinedMemory",
    "from langchain_classic.memory import ReadOnlySharedMemory",
]

for import_statement in memory_imports:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

# Test Chain Components from langchain_classic
print("\n2. Chain Components:")
chain_imports = [
    "from langchain_classic.chains import LLMChain",
    "from langchain_classic.chains import ConversationChain",
    "from langchain_classic.chains import SequentialChain",
    "from langchain_classic.chains import SimpleSequentialChain",
    "from langchain_classic.chains import TransformChain",
    "from langchain_classic.chains import RouterChain",
    "from langchain_classic.chains import ConversationBufferMemoryChain",
    "from langchain_classic.chains import ConversationSummaryMemoryChain",
    "from langchain_classic.chains import RetrievalQA",
    "from langchain_classic.chains import StuffDocumentsChain",
    "from langchain_classic.chains import MapReduceDocumentsChain",
    "from langchain_classic.chains import ReduceDocumentsChain",
    "from langchain_classic.chains import AnalyzeDocumentChain",
    "from langchain_classic.chains import SummarizeCheckerChain",
    "from langchain_classic.chains import ConstitutionalChain",
    "from langchain_classic.chains import GraphQAChain",
    "from langchain_classic.chains import VectorDBQA",
    "from langchain_classic.chains import VectorDBQATool",
    "from langchain_classic.chains import QAWithSourcesChain",
]

for import_statement in chain_imports:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

# Test Prompts from langchain_classic
print("\n3. Prompt Components:")
prompt_imports = [
    "from langchain_classic.prompts import PromptTemplate",
    "from langchain_classic.prompts import ChatPromptTemplate",
    "from langchain_classic.prompts import FewShotPromptTemplate",
    "from langchain_classic.prompts import FewShotChatMessagePromptTemplate",
    "from langchain_classic.prompts import PipelinePromptTemplate",
    "from langchain_classic.prompts import SemanticSimilarityExampleSelector",
]

for import_statement in prompt_imports:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

# Test Memory instantiation
print("\n4. Testing Memory Instantiation:")
try:
    from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory

    # Test ConversationBufferMemory
    buffer_memory = ConversationBufferMemory()
    print("✓ ConversationBufferMemory instantiated successfully")

    # Test ConversationSummaryMemory (might need LLM)
    try:
        summary_memory = ConversationSummaryMemory()
        print("✓ ConversationSummaryMemory instantiated successfully")
    except Exception as e:
        print(f"✗ ConversationSummaryMemory instantiation failed: {e}")

except ImportError as e:
    print(f"✗ Memory import failed: {e}")

# Test Chain instantiation
print("\n5. Testing Chain Instantiation:")
try:
    from langchain_classic.chains import LLMChain, ConversationChain
    from langchain_classic.prompts import PromptTemplate
    from langchain_classic.memory import ConversationBufferMemory

    # Test LLMChain
    try:
        prompt = PromptTemplate(template="Hello {input}", input_variables=["input"])
        # We can't instantiate without an LLM, but we can check if the class loads
        print("✓ LLMChain class imported successfully")
    except Exception as e:
        print(f"✗ LLMChain setup failed: {e}")

    # Test ConversationChain
    try:
        memory = ConversationBufferMemory()
        # We can't instantiate without an LLM, but we can check if the class loads
        print("✓ ConversationChain class imported successfully")
    except Exception as e:
        print(f"✗ ConversationChain setup failed: {e}")

except ImportError as e:
    print(f"✗ Chain import failed: {e}")

print("\n" + "="*50)
print("Test Complete!")
print("="*50)