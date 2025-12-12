#!/usr/bin/env python3
"""
Test script to find working import paths for LangChain 1.x components
"""

import sys

print("Python version:", sys.version)
print("\n" + "="*50)
print("Testing LangChain Import Paths")
print("="*50)

# Test basic LangChain installation
print("\n1. Testing basic LangChain installation:")
try:
    import langchain
    print(f"✓ langchain version: {langchain.__version__}")
except ImportError as e:
    print(f"✗ langchain import failed: {e}")

print("\n2. Testing Memory Components:")
print("-" * 30)

# Test ConversationBufferMemory
memory_imports_to_test = [
    "from langchain.memory import ConversationBufferMemory",
    "from langchain.memory import ConversationSummaryMemory",
    "from langchain.memory import ConversationBufferWindowMemory",
    "from langchain.memory import ConversationTokenBufferMemory",
    "from langchain.memory import ConversationKGMemory",
    "from langchain.memory import ConversationEntityMemory",
    "from langchain.memory import VectorStoreRetrieverMemory",
    # Test with different paths
    "from langchain_community.memory import ConversationBufferMemory",
    "from langchain_community.memory import ConversationSummaryMemory",
    "from langchain_community.memory import ConversationBufferWindowMemory",
    "from langchain_core.memory import ConversationBufferMemory",
    "from langchain_core.memory import ConversationSummaryMemory",
]

for import_statement in memory_imports_to_test:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

print("\n3. Testing Chain Components:")
print("-" * 30)

chain_imports_to_test = [
    "from langchain.chains import LLMChain",
    "from langchain.chains import ConversationChain",
    "from langchain.chains import SequentialChain",
    "from langchain.chains import SimpleSequentialChain",
    "from langchain.chains import TransformChain",
    "from langchain.chains import RouterChain",
    "from langchain.chains import ConversationBufferMemoryChain",
    "from langchain.chains import ConversationSummaryMemoryChain",
    # Test with different paths
    "from langchain_community.chains import LLMChain",
    "from langchain_community.chains import ConversationChain",
    "from langchain_community.chains import SequentialChain",
    "from langchain_core.chains import LLMChain",
    "from langchain_core.chains import ConversationChain",
]

for import_statement in chain_imports_to_test:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

print("\n4. Testing Core Components:")
print("-" * 30)

core_imports_to_test = [
    "from langchain_core.prompts import PromptTemplate",
    "from langchain_core.prompts import ChatPromptTemplate",
    "from langchain_core.messages import HumanMessage",
    "from langchain_core.messages import AIMessage",
    "from langchain_core.messages import SystemMessage",
    "from langchain_core.runnables import RunnablePassthrough",
    "from langchain_core.runnables import RunnableLambda",
    "from langchain_core.language_models import BaseLanguageModel",
    # Test legacy imports
    "from langchain.prompts import PromptTemplate",
    "from langchain.prompts import ChatPromptTemplate",
    "from langchain.schema import HumanMessage",
    "from langchain.schema import AIMessage",
    "from langchain.schema import SystemMessage",
]

for import_statement in core_imports_to_test:
    try:
        exec(import_statement)
        print(f"✓ {import_statement}")
    except ImportError as e:
        print(f"✗ {import_statement} - {e}")

print("\n5. Testing Memory Classes Directly:")
print("-" * 30)

# Test specific memory classes
memory_classes_to_test = [
    ("ConversationBufferMemory", [
        "from langchain.memory import ConversationBufferMemory",
        "from langchain_community.memory import ConversationBufferMemory",
        "from langchain_core.memory import ConversationBufferMemory",
    ]),
    ("ConversationSummaryMemory", [
        "from langchain.memory import ConversationSummaryMemory",
        "from langchain_community.memory import ConversationSummaryMemory",
        "from langchain_core.memory import ConversationSummaryMemory",
    ]),
]

for class_name, import_list in memory_classes_to_test:
    print(f"\n{class_name}:")
    for import_statement in import_list:
        try:
            # Execute import
            namespace = {}
            exec(import_statement, namespace)
            class_obj = namespace[class_name]

            # Try to instantiate it (might require parameters)
            try:
                instance = class_obj()
                print(f"  ✓ {import_statement} - Can instantiate")
            except Exception as inst_error:
                print(f"  ✓ {import_statement} - Import works, instantiation failed: {inst_error}")

        except ImportError as e:
            print(f"  ✗ {import_statement} - {e}")

print("\n6. Testing Package Structure:")
print("-" * 30)

# Test what packages are available
packages_to_test = [
    "langchain.memory",
    "langchain.chains",
    "langchain.prompts",
    "langchain.schema",
    "langchain_core.memory",
    "langchain_core.chains",
    "langchain_core.prompts",
    "langchain_core.messages",
    "langchain_community.memory",
    "langchain_community.chains",
    "langchain_community.prompts",
]

for package in packages_to_test:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError as e:
        print(f"✗ {package} - {e}")

print("\n" + "="*50)
print("Test Complete!")
print("="*50)