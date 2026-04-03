"""
HAVEN RAG Index Builder
-----------------------
Run this ONCE to build your vector database from haven_dataset.txt.

From your project root (HAVEN-AVISHKAR/), run:
    python build_rag_index.py

This creates two files inside the haven/ app folder:
    haven/rag_index.faiss   ← the vector index
    haven/rag_chunks.pkl    ← the text chunks

After running this once, you never need to run it again unless you update the dataset.
"""

import os
import sys

# Add project root to path so Django settings can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Haven_project.settings')

import django
django.setup()

from haven.rag_engine import build_index

if __name__ == "__main__":
    print("=" * 60)
    print("  HAVEN RAG Index Builder")
    print("=" * 60)
    print()
    
    try:
        num_chunks = build_index()
        print()
        print("=" * 60)
        print(f"  SUCCESS! Index built with {num_chunks} chunks.")
        print("  Files saved:")
        print("    haven/rag_index.faiss")
        print("    haven/rag_chunks.pkl")
        print()
        print("  You can now run your Django server.")
        print("  BUDDY will use the RAG pipeline automatically.")
        print("=" * 60)
    except FileNotFoundError as e:
        print(f"\n  ERROR: {e}")
        print("\n  Make sure haven_dataset.txt is in your project root folder.")
    except Exception as e:
        print(f"\n  ERROR: {e}")
        print("\n  Make sure you have installed all requirements:")
        print("    pip install sentence-transformers faiss-cpu numpy")