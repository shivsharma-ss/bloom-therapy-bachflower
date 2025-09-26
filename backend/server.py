from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
import json
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
from textblob import TextBlob
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Bach Flower Remedy Recommendation System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize AI components
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
knowledge_graph = nx.Graph()

# Bach Flower Remedy Knowledge Base
BACH_REMEDIES = {
    "agrimony": {
        "name": "Agrimony",
        "symptoms": ["anxiety hidden behind cheerful mask", "inner torment", "worry concealed", "restlessness", "torture behind brave face", "mental anguish", "seeks company to avoid being alone with thoughts"],
        "emotional_state": "mental torture hidden behind cheerful facade",
        "remedy_for": "Those who hide worries behind a happy mask",
        "category": "oversensitive",
        "combinations": ["walnut", "mimulus", "white_chestnut"]
    },
    "aspen": {
        "name": "Aspen", 
        "symptoms": ["vague fears", "apprehension", "foreboding", "unknown fears", "nightmares", "anxiety without cause", "trembling", "nervousness"],
        "emotional_state": "fear of unknown things",
        "remedy_for": "Vague unknown fears and anxieties",
        "category": "fear",
        "combinations": ["mimulus", "cherry_plum", "rock_rose"]
    },
    "beech": {
        "name": "Beech",
        "symptoms": ["intolerance", "critical", "arrogance", "lack of compassion", "judgmental", "fault-finding", "irritability"],
        "emotional_state": "intolerance and criticism of others",
        "remedy_for": "Intolerance and being overly critical",
        "category": "overcare",
        "combinations": ["willow", "impatiens", "vine"]
    },
    "centaury": {
        "name": "Centaury",
        "symptoms": ["weakness of will", "subservience", "difficulty saying no", "eager to please", "easily influenced", "weak-willed", "doormat"],
        "emotional_state": "inability to say no",
        "remedy_for": "Those who cannot say no and are easily exploited",
        "category": "oversensitive",
        "combinations": ["walnut", "pine", "larch"]
    },
    "cerato": {
        "name": "Cerato",
        "symptoms": ["lack of confidence in own judgment", "seeks advice constantly", "doubt own decisions", "easily influenced", "intuition distrust"],
        "emotional_state": "doubt in own wisdom",
        "remedy_for": "Those who doubt their own judgment",
        "category": "uncertainty",
        "combinations": ["scleranthus", "wild_oat", "gentian"]
    },
    "cherry_plum": {
        "name": "Cherry Plum",
        "symptoms": ["fear of losing control", "desperation", "fear of doing something terrible", "breakdown", "hysteria", "loss of reason"],
        "emotional_state": "fear of losing mental control",
        "remedy_for": "Fear of losing control and desperate thoughts",
        "category": "fear",
        "combinations": ["rock_rose", "aspen", "sweet_chestnut"]
    },
    "chestnut_bud": {
        "name": "Chestnut Bud",
        "symptoms": ["failure to learn from experience", "repeating mistakes", "lack of observation", "carelessness", "inattention"],
        "emotional_state": "failure to learn from mistakes",
        "remedy_for": "Those who repeat the same mistakes",
        "category": "insufficient_interest",
        "combinations": ["honeysuckle", "clematis", "wild_rose"]
    },
    "chicory": {
        "name": "Chicory",
        "symptoms": ["possessiveness", "selfishness", "manipulation", "self-pity", "attention seeking", "controlling", "conditional love"],
        "emotional_state": "selfish possessive love",
        "remedy_for": "Possessive love and self-centered care",
        "category": "overcare",
        "combinations": ["heather", "willow", "beech"]
    },
    "clematis": {
        "name": "Clematis",
        "symptoms": ["dreamy", "absent-minded", "lack of interest in present", "escapism", "drowsiness", "inattention", "living in future"],
        "emotional_state": "dreamy inattention to present",
        "remedy_for": "Dreaminess and lack of interest in present",
        "category": "insufficient_interest",
        "combinations": ["wild_rose", "chestnut_bud", "honeysuckle"]
    },
    "crab_apple": {
        "name": "Crab Apple",
        "symptoms": ["self-disgust", "feeling unclean", "shame", "poor self-image", "obsession with details", "perfectionism"],
        "emotional_state": "self-hatred and disgust",
        "remedy_for": "Self-disgust and feeling unclean",
        "category": "despondency",
        "combinations": ["pine", "larch", "elm"]
    },
    "elm": {
        "name": "Elm",
        "symptoms": ["overwhelm", "temporary inadequacy", "responsibility burden", "momentary loss of confidence", "feeling inadequate"],
        "emotional_state": "overwhelmed by responsibility",
        "remedy_for": "Temporary feelings of being overwhelmed",
        "category": "despondency",
        "combinations": ["oak", "olive", "hornbeam"]
    },
    "gentian": {
        "name": "Gentian",
        "symptoms": ["discouragement", "doubt", "setbacks affect easily", "pessimism", "depression from known cause"],
        "emotional_state": "discouragement from setbacks",
        "remedy_for": "Discouragement and doubt from known causes",
        "category": "uncertainty",
        "combinations": ["gorse", "mustard", "cerato"]
    },
    "gorse": {
        "name": "Gorse",
        "symptoms": ["hopelessness", "despair", "giving up", "no faith in recovery", "pessimism", "lost hope"],
        "emotional_state": "hopelessness and despair",
        "remedy_for": "Great hopelessness and despair",
        "category": "uncertainty",
        "combinations": ["sweet_chestnut", "gentian", "wild_rose"]
    },
    "heather": {
        "name": "Heather",
        "symptoms": ["self-centered", "talkative", "attention seeking", "loneliness", "poor listener", "self-obsessed"],
        "emotional_state": "self-centered talkativeness",
        "remedy_for": "Self-centeredness and constant need for attention",
        "category": "loneliness",
        "combinations": ["chicory", "impatiens", "water_violet"]
    },
    "holly": {
        "name": "Holly",
        "symptoms": ["hatred", "jealousy", "envy", "revenge", "suspicion", "anger", "vexation"],
        "emotional_state": "hatred and jealousy",
        "remedy_for": "Hatred, envy, jealousy and revenge",
        "category": "oversensitive",
        "combinations": ["willow", "beech", "vine"]
    },
    "honeysuckle": {
        "name": "Honeysuckle",
        "symptoms": ["living in past", "nostalgia", "regret", "homesickness", "dwelling on past", "loss of interest in present"],
        "emotional_state": "living in the past",
        "remedy_for": "Living in the past and nostalgia",
        "category": "insufficient_interest",
        "combinations": ["clematis", "wild_rose", "chestnut_bud"]
    },
    "hornbeam": {
        "name": "Hornbeam",
        "symptoms": ["mental fatigue", "procrastination", "tiredness before starting", "doubt in ability to cope", "weariness"],
        "emotional_state": "mental weariness",
        "remedy_for": "Mental fatigue and procrastination",
        "category": "uncertainty",
        "combinations": ["olive", "elm", "oak"]
    },
    "impatiens": {
        "name": "Impatiens",
        "symptoms": ["impatience", "irritability", "hasty", "tension", "intolerance of slow pace", "quick thinking"],
        "emotional_state": "impatience and irritability",
        "remedy_for": "Impatience and irritability with others",
        "category": "loneliness",
        "combinations": ["beech", "heather", "vine"]
    },
    "larch": {
        "name": "Larch",
        "symptoms": ["lack of confidence", "expects failure", "inferiority complex", "hesitation", "despondency"],
        "emotional_state": "lack of confidence",
        "remedy_for": "Lack of confidence and expectation of failure",
        "category": "despondency",
        "combinations": ["cerato", "centaury", "pine"]
    },
    "mimulus": {
        "name": "Mimulus",
        "symptoms": ["fear of known things", "shyness", "timidity", "nervousness", "anxiety about specific things", "phobias"],
        "emotional_state": "fear of known things",
        "remedy_for": "Fear of known things and shyness",
        "category": "fear",
        "combinations": ["aspen", "larch", "agrimony"]
    },
    "mustard": {
        "name": "Mustard",
        "symptoms": ["depression without cause", "gloom", "melancholy", "sadness", "dark cloud feeling"],
        "emotional_state": "deep depression without reason",
        "remedy_for": "Deep depression that comes and goes without reason",
        "category": "insufficient_interest",
        "combinations": ["gentian", "gorse", "sweet_chestnut"]
    },
    "oak": {
        "name": "Oak",
        "symptoms": ["exhaustion but keeps going", "never gives up", "duty bound", "stubborn persistence", "overwork"],
        "emotional_state": "exhausted but struggling on",
        "remedy_for": "Those who struggle on despite exhaustion",
        "category": "despondency",
        "combinations": ["elm", "olive", "hornbeam"]
    },
    "olive": {
        "name": "Olive",
        "symptoms": ["complete exhaustion", "drained", "no reserves left", "worn out", "fatigue"],
        "emotional_state": "complete mental and physical exhaustion",
        "remedy_for": "Complete exhaustion of mind and body",
        "category": "insufficient_interest",
        "combinations": ["oak", "elm", "hornbeam"]
    },
    "pine": {
        "name": "Pine",
        "symptoms": ["guilt", "self-reproach", "blame self for others' mistakes", "never satisfied with efforts", "apologetic"],
        "emotional_state": "guilt and self-reproach",
        "remedy_for": "Guilt and self-reproach",
        "category": "despondency",
        "combinations": ["crab_apple", "larch", "centaury"]
    },
    "red_chestnut": {
        "name": "Red Chestnut",
        "symptoms": ["excessive worry for others", "fearful for loved ones", "anxiety for others' wellbeing", "over-concern"],
        "emotional_state": "excessive concern for others",
        "remedy_for": "Excessive worry and fear for others",
        "category": "overcare",
        "combinations": ["chicory", "vine", "beech"]
    },
    "rescue_remedy": {
        "name": "Rescue Remedy",
        "symptoms": ["emergency", "trauma", "shock", "panic", "crisis", "stress", "accident"],
        "emotional_state": "emergency and crisis situations",
        "remedy_for": "Emergency situations, trauma, shock and crisis",
        "category": "emergency",
        "combinations": ["rock_rose", "impatiens", "cherry_plum", "star_of_bethlehem", "clematis"]
    },
    "rock_rose": {
        "name": "Rock Rose",
        "symptoms": ["terror", "panic", "nightmare", "extreme fear", "helplessness", "emergency"],
        "emotional_state": "extreme terror and panic",
        "remedy_for": "Terror, panic and extreme fear",
        "category": "fear",
        "combinations": ["cherry_plum", "aspen", "mimulus"]
    },
    "rock_water": {
        "name": "Rock Water",
        "symptoms": ["self-denial", "rigidity", "self-discipline", "hard on self", "strict principles", "inflexibility"],
        "emotional_state": "rigid self-discipline",
        "remedy_for": "Self-denial and rigid adherence to principles",
        "category": "overcare",
        "combinations": ["vine", "beech", "oak"]
    },
    "scleranthus": {
        "name": "Scleranthus",
        "symptoms": ["indecision", "uncertainty between choices", "mood swings", "hesitation", "vacillation"],
        "emotional_state": "indecision between alternatives",
        "remedy_for": "Indecision and uncertainty between two choices",
        "category": "uncertainty",
        "combinations": ["cerato", "wild_oat", "gentian"]
    },
    "star_of_bethlehem": {
        "name": "Star of Bethlehem",
        "symptoms": ["shock", "trauma", "grief", "distress", "after-effects of shock", "comfort"],
        "emotional_state": "shock and trauma",
        "remedy_for": "Shock, trauma and grief",
        "category": "despondency",
        "combinations": ["sweet_chestnut", "willow", "pine"]
    },
    "sweet_chestnut": {
        "name": "Sweet Chestnut",
        "symptoms": ["extreme mental anguish", "despair", "limit of endurance", "dark night of soul", "hopelessness"],
        "emotional_state": "extreme mental anguish",
        "remedy_for": "Extreme mental anguish and despair",
        "category": "despondency",
        "combinations": ["gorse", "cherry_plum", "star_of_bethlehem"]
    },
    "vervain": {
        "name": "Vervain",
        "symptoms": ["over-enthusiasm", "fanaticism", "strain", "tension", "fixed ideas", "missionary zeal"],
        "emotional_state": "over-enthusiasm and strain",
        "remedy_for": "Over-enthusiasm and fixed ideas",
        "category": "overcare",
        "combinations": ["vine", "impatiens", "beech"]
    },
    "vine": {
        "name": "Vine",
        "symptoms": ["dominating", "inflexible", "tyrannical", "arrogant", "ruthless", "ambitious", "leadership"],
        "emotional_state": "domination and inflexibility",
        "remedy_for": "Dominating behavior and inflexibility",
        "category": "overcare",
        "combinations": ["beech", "vervain", "impatiens"]
    },
    "walnut": {
        "name": "Walnut",
        "symptoms": ["influenced by others", "life changes", "transition", "protection from change", "easily led"],
        "emotional_state": "influenced by change and others",
        "remedy_for": "Protection during change and transition",
        "category": "oversensitive",
        "combinations": ["centaury", "cerato", "agrimony"]
    },
    "water_violet": {
        "name": "Water Violet",
        "symptoms": ["pride", "aloofness", "superiority", "independence", "withdrawn", "self-reliant"],
        "emotional_state": "proud aloofness",
        "remedy_for": "Pride and aloof superiority",
        "category": "loneliness",
        "combinations": ["impatiens", "heather", "vine"]
    },
    "white_chestnut": {
        "name": "White Chestnut",
        "symptoms": ["persistent thoughts", "mental arguments", "worrying thoughts", "insomnia", "racing mind"],
        "emotional_state": "persistent unwanted thoughts",
        "remedy_for": "Persistent unwanted thoughts and mental arguments",
        "category": "insufficient_interest",
        "combinations": ["agrimony", "clematis", "mustard"]
    },
    "wild_oat": {
        "name": "Wild Oat",
        "symptoms": ["uncertainty about life path", "ambition without direction", "dissatisfaction", "unclear goals"],
        "emotional_state": "uncertainty about life direction",
        "remedy_for": "Uncertainty about life direction and goals",
        "category": "uncertainty",
        "combinations": ["scleranthus", "cerato", "gentian"]
    },
    "wild_rose": {
        "name": "Wild Rose",
        "symptoms": ["apathy", "resignation", "lack of interest", "drift through life", "no effort", "acceptance of fate"],
        "emotional_state": "resignation and apathy",
        "remedy_for": "Apathy and resignation to circumstances",
        "category": "insufficient_interest",
        "combinations": ["clematis", "honeysuckle", "gorse"]
    },
    "willow": {
        "name": "Willow",
        "symptoms": ["resentment", "bitterness", "self-pity", "victim mentality", "blame others", "grudges"],
        "emotional_state": "resentment and bitterness",
        "remedy_for": "Resentment and bitter thoughts",
        "category": "despondency",
        "combinations": ["holly", "beech", "chicory"]
    }
}

# Initialize knowledge graph
def initialize_knowledge_graph():
    global knowledge_graph
    knowledge_graph.clear()
    
    for remedy_id, remedy_data in BACH_REMEDIES.items():
        knowledge_graph.add_node(remedy_id, **remedy_data)
        
        # Add edges based on combinations
        for combination in remedy_data.get('combinations', []):
            if combination in BACH_REMEDIES:
                knowledge_graph.add_edge(remedy_id, combination, weight=0.8)
        
        # Add category connections
        category = remedy_data.get('category')
        for other_id, other_data in BACH_REMEDIES.items():
            if other_id != remedy_id and other_data.get('category') == category:
                knowledge_graph.add_edge(remedy_id, other_id, weight=0.6)

# Initialize on startup
initialize_knowledge_graph()

# Models
class RemedySelection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symptoms: str
    nlp_mode: bool = False
    recommendations: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RemedySelectionCreate(BaseModel):
    user_id: str
    symptoms: str
    nlp_mode: bool = False

class RecommendationRequest(BaseModel):
    symptoms: str
    nlp_mode: bool = False

class AdminKnowledgeSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str  # 'web', 'pdf', 'image', 'text'
    content: str
    source_url: Optional[str] = None
    processed: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdminKnowledgeSourceCreate(BaseModel):
    source_type: str
    content: str
    source_url: Optional[str] = None

# AI Chat initialization
async def get_llm_chat():
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM API key not configured")
    
    chat = LlmChat(
        api_key=api_key,
        session_id=str(uuid.uuid4()),
        system_message="You are an expert in Bach flower remedies. Analyze symptoms and emotional states to recommend appropriate remedies based on Dr. Bach's original 38 flower essences."
    ).with_model("openai", "gpt-5")
    
    return chat

# NLP Processing Functions
async def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment and extract emotional keywords from text"""
    blob = TextBlob(text)
    
    # Basic sentiment analysis
    sentiment = {
        'polarity': blob.sentiment.polarity,  # -1 to 1
        'subjectivity': blob.sentiment.subjectivity  # 0 to 1
    }
    
    # Extract emotional keywords using LLM
    try:
        llm_chat = await get_llm_chat()
        
        analysis_prompt = f"""
        Analyze this text and extract emotional symptoms that relate to Bach flower remedies:
        
        Text: "{text}"
        
        Please identify:
        1. Primary emotional state
        2. Key symptoms present
        3. Underlying emotional patterns
        4. Suggested Bach flower remedy categories
        
        Return only the emotional symptoms as a comma-separated list that could match Bach flower remedy indications.
        """
        
        user_message = UserMessage(text=analysis_prompt)
        response = await llm_chat.send_message(user_message)
        
        extracted_symptoms = response.strip()
        
    except Exception as e:
        print(f"LLM analysis error: {e}")
        extracted_symptoms = text  # Fallback to original text
    
    return {
        'sentiment': sentiment,
        'extracted_symptoms': extracted_symptoms,
        'original_text': text
    }

def create_embeddings(text_list: List[str]) -> np.ndarray:
    """Create embeddings for symptom matching"""
    return embedding_model.encode(text_list)

def find_vector_matches(query_symptoms: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Find matches using vector similarity"""
    
    # Create remedy texts for embedding
    remedy_texts = []
    remedy_ids = []
    
    for remedy_id, remedy_data in BACH_REMEDIES.items():
        # Combine symptoms and emotional state for better matching
        text = f"{' '.join(remedy_data['symptoms'])} {remedy_data['emotional_state']} {remedy_data['remedy_for']}"
        remedy_texts.append(text)
        remedy_ids.append(remedy_id)
    
    # Create embeddings
    query_embedding = embedding_model.encode([query_symptoms])
    remedy_embeddings = embedding_model.encode(remedy_texts)
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, remedy_embeddings)[0]
    
    # Get top matches
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    matches = []
    for idx in top_indices:
        remedy_id = remedy_ids[idx]
        remedy_data = BACH_REMEDIES[remedy_id]
        
        matches.append({
            'remedy_id': remedy_id,
            'remedy_name': remedy_data['name'],
            'similarity_score': float(similarities[idx]),
            'symptoms': remedy_data['symptoms'],
            'remedy_for': remedy_data['remedy_for'],
            'category': remedy_data['category'],
            'method': 'vector_similarity'
        })
    
    return matches

def find_knowledge_graph_matches(symptoms: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Find matches using knowledge graph analysis"""
    
    symptom_words = set(symptoms.lower().split())
    
    # Calculate relevance scores for each remedy
    scores = {}
    for remedy_id, remedy_data in BACH_REMEDIES.items():
        score = 0
        
        # Check symptom overlap
        remedy_words = set(' '.join(remedy_data['symptoms']).lower().split())
        overlap = len(symptom_words.intersection(remedy_words))
        score += overlap * 2
        
        # Check emotional state match
        emotional_words = set(remedy_data['emotional_state'].lower().split())
        emotional_overlap = len(symptom_words.intersection(emotional_words))
        score += emotional_overlap * 3
        
        # Check remedy description match
        remedy_for_words = set(remedy_data['remedy_for'].lower().split())
        remedy_overlap = len(symptom_words.intersection(remedy_for_words))
        score += remedy_overlap * 2.5
        
        scores[remedy_id] = score
    
    # Get top matches
    sorted_remedies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_matches = sorted_remedies[:top_k]
    
    matches = []
    for remedy_id, score in top_matches:
        if score > 0:  # Only include remedies with some relevance
            remedy_data = BACH_REMEDIES[remedy_id]
            
            # Get connected remedies for combination suggestions
            connected_remedies = []
            if knowledge_graph.has_node(remedy_id):
                neighbors = list(knowledge_graph.neighbors(remedy_id))
                connected_remedies = [BACH_REMEDIES[n]['name'] for n in neighbors[:3]]
            
            matches.append({
                'remedy_id': remedy_id,
                'remedy_name': remedy_data['name'],
                'relevance_score': score,
                'symptoms': remedy_data['symptoms'],
                'remedy_for': remedy_data['remedy_for'],
                'category': remedy_data['category'],
                'connected_remedies': connected_remedies,
                'method': 'knowledge_graph'
            })
    
    return matches

# API Routes
@api_router.post("/recommendations", response_model=Dict[str, Any])
async def get_recommendations(request: RecommendationRequest):
    """Get Bach flower remedy recommendations"""
    
    try:
        symptoms_text = request.symptoms
        
        # If NLP mode, analyze the text first
        if request.nlp_mode:
            nlp_analysis = await analyze_text_sentiment(symptoms_text)
            symptoms_text = nlp_analysis['extracted_symptoms']
        
        # Get recommendations from both methods
        vector_matches = find_vector_matches(symptoms_text, top_k=1)
        graph_matches = find_knowledge_graph_matches(symptoms_text, top_k=1)
        
        # Combine and format results
        recommendations = {
            'vector_recommendation': vector_matches[0] if vector_matches else None,
            'knowledge_graph_recommendation': graph_matches[0] if graph_matches else None,
            'symptoms_analyzed': symptoms_text,
            'nlp_mode': request.nlp_mode
        }
        
        if request.nlp_mode:
            recommendations['nlp_analysis'] = {
                'sentiment_polarity': nlp_analysis['sentiment']['polarity'],
                'sentiment_subjectivity': nlp_analysis['sentiment']['subjectivity'],
                'original_text': nlp_analysis['original_text']
            }
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@api_router.post("/remedy-selections", response_model=RemedySelection)
async def save_remedy_selection(selection: RemedySelectionCreate):
    """Save a remedy selection"""
    
    # Get recommendations first
    recommendations_response = await get_recommendations(
        RecommendationRequest(symptoms=selection.symptoms, nlp_mode=selection.nlp_mode)
    )
    
    # Create selection object
    remedy_selection = RemedySelection(
        user_id=selection.user_id,
        symptoms=selection.symptoms,
        nlp_mode=selection.nlp_mode,
        recommendations=recommendations_response
    )
    
    # Save to database
    selection_dict = remedy_selection.dict()
    selection_dict['timestamp'] = selection_dict['timestamp'].isoformat()
    
    await db.remedy_selections.insert_one(selection_dict)
    
    return remedy_selection

@api_router.get("/remedy-selections/{user_id}", response_model=List[RemedySelection])
async def get_user_selections(user_id: str):
    """Get all remedy selections for a user"""
    
    selections = await db.remedy_selections.find({"user_id": user_id}).to_list(100)
    
    for selection in selections:
        if isinstance(selection.get('timestamp'), str):
            selection['timestamp'] = datetime.fromisoformat(selection['timestamp'])
    
    return [RemedySelection(**selection) for selection in selections]

@api_router.put("/remedy-selections/{selection_id}")
async def update_remedy_selection(selection_id: str, updated_symptoms: str):
    """Update a remedy selection"""
    
    # Get new recommendations
    recommendations_response = await get_recommendations(
        RecommendationRequest(symptoms=updated_symptoms, nlp_mode=False)
    )
    
    # Update in database
    update_data = {
        "symptoms": updated_symptoms,
        "recommendations": recommendations_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.remedy_selections.update_one(
        {"id": selection_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    return {"message": "Selection updated successfully"}

@api_router.get("/remedies", response_model=Dict[str, Any])
async def get_all_remedies():
    """Get all Bach flower remedies information"""
    return {"remedies": BACH_REMEDIES}

@api_router.get("/remedies/{remedy_id}", response_model=Dict[str, Any])
async def get_remedy_details(remedy_id: str):
    """Get details for a specific remedy"""
    
    if remedy_id not in BACH_REMEDIES:
        raise HTTPException(status_code=404, detail="Remedy not found")
    
    remedy_data = BACH_REMEDIES[remedy_id]
    
    # Get connected remedies from knowledge graph
    connected_remedies = []
    if knowledge_graph.has_node(remedy_id):
        neighbors = list(knowledge_graph.neighbors(remedy_id))
        connected_remedies = [
            {
                'id': neighbor,
                'name': BACH_REMEDIES[neighbor]['name'],
                'category': BACH_REMEDIES[neighbor]['category']
            }
            for neighbor in neighbors
        ]
    
    return {
        'remedy': remedy_data,
        'connected_remedies': connected_remedies
    }

# Admin Routes
@api_router.post("/admin/knowledge-sources", response_model=AdminKnowledgeSource)
async def add_knowledge_source(source: AdminKnowledgeSourceCreate):
    """Add a new knowledge source for admin"""
    
    knowledge_source = AdminKnowledgeSource(**source.dict())
    source_dict = knowledge_source.dict()
    source_dict['timestamp'] = source_dict['timestamp'].isoformat()
    
    await db.knowledge_sources.insert_one(source_dict)
    
    return knowledge_source

@api_router.get("/admin/knowledge-sources", response_model=List[AdminKnowledgeSource])
async def get_knowledge_sources():
    """Get all knowledge sources"""
    
    sources = await db.knowledge_sources.find().to_list(100)
    
    for source in sources:
        if isinstance(source.get('timestamp'), str):
            source['timestamp'] = datetime.fromisoformat(source['timestamp'])
    
    return [AdminKnowledgeSource(**source) for source in sources]

@api_router.post("/admin/rebuild-knowledge-base")
async def rebuild_knowledge_base():
    """Rebuild the knowledge base from stored sources"""
    
    try:
        # Get all knowledge sources
        sources = await db.knowledge_sources.find({"processed": False}).to_list(100)
        
        # Process each source (placeholder for actual processing)
        processed_count = 0
        for source in sources:
            # Here you would implement actual processing logic
            # For now, just mark as processed
            await db.knowledge_sources.update_one(
                {"id": source['id']},
                {"$set": {"processed": True}}
            )
            processed_count += 1
        
        # Reinitialize knowledge graph
        initialize_knowledge_graph()
        
        return {
            "message": f"Knowledge base rebuilt successfully. Processed {processed_count} sources."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding knowledge base: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)