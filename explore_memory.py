#!/usr/bin/env python3
"""
Explore what's actually available in LangChain memory and chain modules
"""

import sys
import pkgutil

def explore_module(module_name):
    """Explore what's available in a module"""
    try:
        module = __import__(module_name)
        for submodule_name in pkgutil.iter_modules(module.__path__):
            full_name = f"{module_name}.{submodule_name.name}"
            try:
                submodule = __import__(full_name, fromlist=[submodule_name.name])
                print(f"  ✓ {full_name}")

                # List available classes/functions
                for name in dir(submodule):
                    if not name.startswith('_'):
                        obj = getattr(submodule, name)
                        if hasattr(obj, '__module__') and obj.__module__ == full_name:
                            print(f"    - {name}: {type(obj).__name__}")
            except ImportError as e:
                print(f"  ✗ {full_name} - {e}")
    except ImportError as e:
        print(f"✗ {module_name} - {e}")

print("Exploring langchain_community.memory:")
explore_module("langchain_community.memory")

print("\nExploring langchain_community.chains:")
explore_module("langchain_community.chains")

print("\nExploring langchain.memory (if it exists):")
explore_module("langchain.memory")

print("\nExploring langchain.chains (if it exists):")
explore_module("langchain.chains")

# Also check if there's a langchain_classic module that might have the legacy components
print("\nExploring langchain_classic:")
try:
    import langchain_classic
    print("✓ langchain_classic available")
    if hasattr(langchain_classic, '__path__'):
        for submodule_name in pkgutil.iter_modules(langchain_classic.__path__):
            full_name = f"langchain_classic.{submodule_name.name}"
            print(f"  ✓ {full_name}")
except ImportError as e:
    print(f"✗ langchain_classic - {e}")