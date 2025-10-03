#!/usr/bin/env python
"""
HAVEN RAG Knowledge Base Setup Script

This script sets up the RAG (Retrieval-Augmented Generation) system for the HAVEN chatbot.
It indexes documents from the knowledge_base/ directory into a ChromaDB vector store
using Google's Gemini embedding model.

Usage:
    python setup_rag.py

Requirements:
    - Google API Key set in environment variables
    - Documents in knowledge_base/ directory
    - All required packages installed
"""

import os
import sys
import django
from pathlib import Path
from typing import List, Dict
import logging

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Haven_project.settings')
django.setup()

from django.conf import settings
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HAVENRAGSetup:
    """Setup and manage the RAG knowledge base for HAVEN chatbot"""
    
    def __init__(self):
        self.knowledge_base_dir = settings.RAG_KNOWLEDGE_BASE_DIR
        self.vector_store_dir = settings.RAG_VECTOR_STORE_DIR
        self.api_key = settings.GOOGLE_API_KEY
        
        if not self.api_key or self.api_key == 'your_google_api_key_here':
            raise ValueError("Please set your GOOGLE_API_KEY in environment variables or .env file")
        
        # Configure Google AI
        genai.configure(api_key=self.api_key)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        
        # Create directories if they don't exist
        self.knowledge_base_dir.mkdir(exist_ok=True)
        self.vector_store_dir.mkdir(exist_ok=True)
    
    def create_sample_knowledge_base(self):
        """Create sample knowledge base documents if none exist"""
        sample_docs = {
            "mental_health_basics.txt": """
Mental Health Basics

Mental health is an essential part of overall health and well-being. It affects how we think, feel, and act. Good mental health helps us:
- Handle stress and challenges
- Make meaningful connections with others
- Work productively
- Realize our full potential

Common Mental Health Conditions:
1. Anxiety Disorders: Excessive worry, fear, or nervousness
2. Depression: Persistent sadness, loss of interest, low energy
3. Stress: Physical and emotional response to challenges
4. Trauma: Emotional response to distressing events

Self-Care Strategies:
- Regular exercise and physical activity
- Healthy sleep patterns
- Balanced nutrition
- Mindfulness and meditation
- Social connections
- Professional help when needed

Remember: Seeking help is a sign of strength, not weakness.
            """,
            
            "coping_strategies.txt": """
Coping Strategies for Mental Health

When facing difficult emotions or situations, these strategies can help:

Breathing Techniques:
- 4-7-8 Breathing: Inhale for 4, hold for 7, exhale for 8
- Box Breathing: 4 counts in, hold, out, hold
- Deep Belly Breathing: Focus on expanding your diaphragm

Grounding Techniques:
- 5-4-3-2-1 Method: Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste
- Progressive Muscle Relaxation: Tense and release each muscle group
- Mindful Observation: Focus on one object and describe it in detail

Cognitive Strategies:
- Challenge negative thoughts with evidence
- Practice gratitude by listing 3 good things daily
- Use positive affirmations
- Break large problems into smaller steps

Physical Strategies:
- Take a walk in nature
- Listen to calming music
- Practice yoga or stretching
- Take a warm bath or shower

Remember: Different strategies work for different people. Find what works best for you.
            """,
            
            "crisis_resources.txt": """
Crisis Resources and Emergency Contacts

If you or someone you know is in immediate danger or having thoughts of self-harm:

Emergency Contacts:
- National Suicide Prevention Lifeline: 988 (US)
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911 (US) or your local emergency number

International Resources:
- International Association for Suicide Prevention: iasp.info
- Befrienders Worldwide: befrienders.org
- Crisis Support Services in your country

Warning Signs to Watch For:
- Talking about wanting to die or hurt oneself
- Looking for ways to kill oneself
- Talking about feeling hopeless or having no reason to live
- Talking about being a burden to others
- Increasing use of alcohol or drugs
- Acting anxious, agitated, or reckless
- Sleeping too little or too much
- Withdrawing or feeling isolated
- Showing rage or talking about seeking revenge
- Extreme mood swings

How to Help Someone in Crisis:
1. Take all threats seriously
2. Listen without judgment
3. Stay with the person
4. Remove any means of self-harm
5. Get professional help immediately
6. Follow up and continue to support

Remember: You are not alone. Help is available 24/7.
            """,
            
            "study_wellness.txt": """
Study Wellness and Academic Mental Health

Balancing academic demands with mental health is crucial for student success:

Study Strategies:
- Pomodoro Technique: 25 minutes focused study, 5-minute break
- Active recall and spaced repetition
- Create a dedicated study space
- Set realistic goals and deadlines
- Take regular breaks every 45-60 minutes

Managing Academic Stress:
- Prioritize tasks using the Eisenhower Matrix
- Break large projects into smaller tasks
- Practice time management techniques
- Set boundaries between study and personal time
- Seek help from professors or tutors when needed

Exam Anxiety Management:
- Prepare thoroughly but don't over-study
- Practice relaxation techniques before exams
- Get adequate sleep before important tests
- Eat nutritious meals
- Arrive early to avoid rushing

Building Resilience:
- Develop a growth mindset
- Learn from failures and setbacks
- Celebrate small victories
- Maintain perspective on grades and performance
- Focus on learning rather than just grades

Remember: Your worth is not determined by your academic performance.
            """,
            
            "relationships_communication.txt": """
Healthy Relationships and Communication

Building and maintaining healthy relationships is essential for mental well-being:

Communication Skills:
- Active listening: Focus fully on what the other person is saying
- Use "I" statements instead of "you" statements
- Express feelings clearly and directly
- Ask for clarification when needed
- Practice empathy and understanding

Setting Boundaries:
- Know your limits and communicate them clearly
- Say "no" when you need to without guilt
- Respect others' boundaries
- Be consistent with your boundaries
- Re-evaluate boundaries as relationships evolve

Conflict Resolution:
- Address issues early before they escalate
- Focus on the problem, not the person
- Look for win-win solutions
- Take breaks when emotions run high
- Apologize when you're wrong

Building Trust:
- Be honest and transparent
- Keep your promises
- Show respect for others' feelings and opinions
- Be reliable and consistent
- Give others the benefit of the doubt

Toxic Relationship Warning Signs:
- Constant criticism or belittling
- Controlling behavior
- Lack of respect for boundaries
- Manipulation or gaslighting
- Physical, emotional, or verbal abuse

Remember: Healthy relationships should make you feel supported, respected, and valued.
            """
        }
        
        logger.info("Creating sample knowledge base documents...")
        for filename, content in sample_docs.items():
            file_path = self.knowledge_base_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                logger.info(f"Created: {filename}")
            else:
                logger.info(f"Already exists: {filename}")
    
    def load_documents(self) -> List[Document]:
        """Load all documents from the knowledge base directory"""
        logger.info(f"Loading documents from {self.knowledge_base_dir}")
        
        # Load all text files from the knowledge base directory
        loader = DirectoryLoader(
            str(self.knowledge_base_dir),
            glob="**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} documents")
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks for better retrieval"""
        logger.info("Splitting documents into chunks...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} document chunks")
        
        return chunks
    
    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """Create and persist the ChromaDB vector store"""
        logger.info("Creating vector store with ChromaDB...")
        
        # Create the vector store
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(self.vector_store_dir),
            collection_name="haven_knowledge_base"
        )
        
        # Persist the vector store
        vector_store.persist()
        logger.info(f"Vector store created and persisted to {self.vector_store_dir}")
        
        return vector_store
    
    def test_retrieval(self, vector_store: Chroma):
        """Test the retrieval system with sample queries"""
        logger.info("Testing retrieval system...")
        
        test_queries = [
            "How can I manage anxiety?",
            "What are the signs of depression?",
            "How do I help someone in crisis?",
            "What are good study techniques?",
            "How do I build healthy relationships?"
        ]
        
        for query in test_queries:
            logger.info(f"\nQuery: {query}")
            docs = vector_store.similarity_search(query, k=2)
            for i, doc in enumerate(docs, 1):
                logger.info(f"Result {i}: {doc.page_content[:100]}...")
    
    def setup(self):
        """Main setup function"""
        try:
            logger.info("Starting HAVEN RAG setup...")
            
            # Create sample knowledge base if needed
            self.create_sample_knowledge_base()
            
            # Load and process documents
            documents = self.load_documents()
            if not documents:
                logger.warning("No documents found in knowledge base directory")
                return
            
            # Split documents into chunks
            chunks = self.split_documents(documents)
            
            # Create vector store
            vector_store = self.create_vector_store(chunks)
            
            # Test the system
            self.test_retrieval(vector_store)
            
            logger.info("HAVEN RAG setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during RAG setup: {str(e)}")
            raise


def main():
    """Main function to run the RAG setup"""
    try:
        rag_setup = HAVENRAGSetup()
        rag_setup.setup()
    except Exception as e:
        logger.error(f"Failed to setup RAG system: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
