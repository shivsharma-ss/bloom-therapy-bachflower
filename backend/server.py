from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
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
import secrets

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
security = HTTPBasic()

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return credentials.username

# Enhanced Bach Flower Remedy Knowledge Base with Detailed Information
BACH_REMEDIES = {
    "agrimony": {
        "name": "Agrimony",
        "symptoms": ["anxiety hidden behind cheerful mask", "inner torment", "worry concealed", "restlessness", "torture behind brave face", "mental anguish", "seeks company to avoid being alone with thoughts"],
        "emotional_state": "mental torture hidden behind cheerful facade",
        "remedy_for": "Those who hide worries behind a happy mask",
        "category": "oversensitive",
        "combinations": ["walnut", "mimulus", "white_chestnut"],
        "summary": "For mental torture hidden behind a brave face, helping those who suffer inwardly while appearing cheerful outwardly",
        "composition": "Agrimonia eupatoria - Common Agrimony flower essence",
        "effects": "Brings authentic joy and inner peace, helps express true feelings, reduces need to hide behind false cheerfulness",
        "dosage_notes": "Particularly effective when combined with Walnut for protection from external influences"
    },
    "aspen": {
        "name": "Aspen", 
        "symptoms": ["vague fears", "apprehension", "foreboding", "unknown fears", "nightmares", "anxiety without cause", "trembling", "nervousness"],
        "emotional_state": "fear of unknown things",
        "remedy_for": "Vague unknown fears and anxieties",
        "category": "fear",
        "combinations": ["mimulus", "cherry_plum", "rock_rose"],
        "summary": "For mysterious fears and apprehensions with no obvious cause, bringing courage to face the unknown",
        "composition": "Populus tremula - Aspen tree essence",
        "effects": "Promotes courage and security, reduces irrational fears, brings peace to the sensitive mind",
        "dosage_notes": "Often combined with Mimulus for comprehensive fear treatment"
    },
    "beech": {
        "name": "Beech",
        "symptoms": ["intolerance", "critical", "arrogance", "lack of compassion", "judgmental", "fault-finding", "irritability"],
        "emotional_state": "intolerance and criticism of others",
        "remedy_for": "Intolerance and being overly critical",
        "category": "overcare",
        "combinations": ["willow", "impatiens", "vine"],
        "summary": "For critical and intolerant attitudes, helping develop understanding and acceptance of others",
        "composition": "Fagus sylvatica - Beech tree essence",
        "effects": "Increases tolerance and empathy, reduces critical judgment, promotes understanding",
        "dosage_notes": "Works well with Willow for releasing resentment"
    },
    "centaury": {
        "name": "Centaury",
        "symptoms": ["weakness of will", "subservience", "difficulty saying no", "eager to please", "easily influenced", "weak-willed", "doormat"],
        "emotional_state": "inability to say no",
        "remedy_for": "Those who cannot say no and are easily exploited",
        "category": "oversensitive",
        "combinations": ["walnut", "pine", "larch"],
        "summary": "For those who are too eager to please others and cannot assert themselves, building inner strength",
        "composition": "Centaurium umbellatum - Centaury flower essence",
        "effects": "Strengthens will power, helps establish boundaries, promotes self-respect",
        "dosage_notes": "Excellent when paired with Walnut for protection from manipulation"
    },
    "cerato": {
        "name": "Cerato",
        "symptoms": ["lack of confidence in own judgment", "seeks advice constantly", "doubt own decisions", "easily influenced", "intuition distrust"],
        "emotional_state": "doubt in own wisdom",
        "remedy_for": "Those who doubt their own judgment",
        "category": "uncertainty",
        "combinations": ["scleranthus", "wild_oat", "gentian"],
        "summary": "For those who constantly seek others' opinions instead of trusting their own inner wisdom",
        "composition": "Ceratostigma willmottiana - Cerato flower essence",
        "effects": "Builds confidence in inner guidance, strengthens decision-making abilities, reduces need for constant validation",
        "dosage_notes": "Often used with Scleranthus for indecisive personalities"
    },
    "cherry_plum": {
        "name": "Cherry Plum",
        "symptoms": ["fear of losing control", "desperation", "fear of doing something terrible", "breakdown", "hysteria", "loss of reason"],
        "emotional_state": "fear of losing mental control",
        "remedy_for": "Fear of losing control and desperate thoughts",
        "category": "fear",
        "combinations": ["rock_rose", "aspen", "sweet_chestnut"],
        "summary": "For extreme mental pressure and fear of losing control, one of the key Rescue Remedy ingredients",
        "composition": "Prunus cerasifera - Cherry Plum flower essence",
        "effects": "Restores mental balance and calm, prevents breakdown, maintains rational thinking",
        "dosage_notes": "Core ingredient in Rescue Remedy, excellent for crisis situations"
    },
    "chestnut_bud": {
        "name": "Chestnut Bud",
        "symptoms": ["failure to learn from experience", "repeating mistakes", "lack of observation", "carelessness", "inattention"],
        "emotional_state": "failure to learn from mistakes",
        "remedy_for": "Those who repeat the same mistakes",
        "category": "insufficient_interest",
        "combinations": ["honeysuckle", "clematis", "wild_rose"],
        "summary": "For those who fail to learn from experience and keep making the same mistakes",
        "composition": "Aesculus hippocastanum - Horse Chestnut bud essence",
        "effects": "Improves learning ability, increases awareness, helps break negative patterns",
        "dosage_notes": "Combines well with Clematis for better focus and attention"
    },
    "chicory": {
        "name": "Chicory",
        "symptoms": ["possessiveness", "selfishness", "manipulation", "self-pity", "attention seeking", "controlling", "conditional love"],
        "emotional_state": "selfish possessive love",
        "remedy_for": "Possessive love and self-centered care",
        "category": "overcare",
        "combinations": ["heather", "willow", "beech"],
        "summary": "For possessive and manipulative behavior disguised as love and care for others",
        "composition": "Cichorium intybus - Wild Chicory flower essence",
        "effects": "Promotes unconditional love, reduces possessiveness, encourages selfless service",
        "dosage_notes": "Often paired with Heather for those seeking constant attention"
    },
    "clematis": {
        "name": "Clematis",
        "symptoms": ["dreamy", "absent-minded", "lack of interest in present", "escapism", "drowsiness", "inattention", "living in future"],
        "emotional_state": "dreamy inattention to present",
        "remedy_for": "Dreaminess and lack of interest in present",
        "category": "insufficient_interest",
        "combinations": ["wild_rose", "chestnut_bud", "honeysuckle"],
        "summary": "For dreamers and escapists who live in their imagination rather than reality, a Rescue Remedy ingredient",
        "composition": "Clematis vitalba - Wild Clematis flower essence",
        "effects": "Brings grounding and practical focus, increases interest in life, improves concentration",
        "dosage_notes": "Key ingredient in Rescue Remedy for shock-induced withdrawal"
    },
    "crab_apple": {
        "name": "Crab Apple",
        "symptoms": ["self-disgust", "feeling unclean", "shame", "poor self-image", "obsession with details", "perfectionism"],
        "emotional_state": "self-hatred and disgust",
        "remedy_for": "Self-disgust and feeling unclean",
        "category": "despondency",
        "combinations": ["pine", "larch", "elm"],
        "summary": "The cleansing remedy for those who feel contaminated or obsessed with imperfection",
        "composition": "Malus pumila - Wild Crab Apple flower essence",
        "effects": "Promotes self-acceptance, cleanses negative self-perception, reduces obsessive behavior",
        "dosage_notes": "Excellent with Pine for guilt-related self-hatred"
    },
    "elm": {
        "name": "Elm",
        "symptoms": ["overwhelm", "temporary inadequacy", "responsibility burden", "momentary loss of confidence", "feeling inadequate"],
        "emotional_state": "overwhelmed by responsibility",
        "remedy_for": "Temporary feelings of being overwhelmed",
        "category": "despondency",
        "combinations": ["oak", "olive", "hornbeam"],
        "summary": "For capable people temporarily overwhelmed by responsibilities and duties",
        "composition": "Ulmus procera - English Elm flower essence",
        "effects": "Restores confidence in abilities, provides strength during challenging periods",
        "dosage_notes": "Often combined with Oak for chronic overwork patterns"
    },
    "gentian": {
        "name": "Gentian",
        "symptoms": ["discouragement", "doubt", "setbacks affect easily", "pessimism", "depression from known cause"],
        "emotional_state": "discouragement from setbacks",
        "remedy_for": "Discouragement and doubt from known causes",
        "category": "uncertainty",
        "combinations": ["gorse", "mustard", "cerato"],
        "summary": "For discouragement after setbacks, doubt when progress is slow",
        "composition": "Gentianella amarella - Autumn Gentian flower essence",
        "effects": "Restores faith and perseverance, helps overcome temporary setbacks",
        "dosage_notes": "Works well with Gorse for deeper depression"
    },
    "gorse": {
        "name": "Gorse",
        "symptoms": ["hopelessness", "despair", "giving up", "no faith in recovery", "pessimism", "lost hope"],
        "emotional_state": "hopelessness and despair",
        "remedy_for": "Great hopelessness and despair",
        "category": "uncertainty",
        "combinations": ["sweet_chestnut", "gentian", "wild_rose"],
        "summary": "For deep hopelessness when all seems lost, bringing light into darkness",
        "composition": "Ulex europaeus - Gorse flower essence",
        "effects": "Rekindles hope and faith, brings light to dark periods",
        "dosage_notes": "Essential in depression support combinations"
    },
    "heather": {
        "name": "Heather",
        "symptoms": ["self-centered", "talkative", "attention seeking", "loneliness", "poor listener", "self-obsessed"],
        "emotional_state": "self-centered talkativeness",
        "remedy_for": "Self-centeredness and constant need for attention",
        "category": "loneliness",
        "combinations": ["chicory", "impatiens", "water_violet"],
        "summary": "For those who constantly talk about themselves and seek attention",
        "composition": "Calluna vulgaris - Heather flower essence",
        "effects": "Promotes genuine interest in others, reduces self-obsession",
        "dosage_notes": "Often paired with Water Violet for social balance"
    },
    "holly": {
        "name": "Holly",
        "symptoms": ["hatred", "jealousy", "envy", "revenge", "suspicion", "anger", "vexation"],
        "emotional_state": "hatred and jealousy",
        "remedy_for": "Hatred, envy, jealousy and revenge",
        "category": "oversensitive",
        "combinations": ["willow", "beech", "vine"],
        "summary": "For negative emotions like hatred, jealousy, and envy, opening the heart to love",
        "composition": "Ilex aquifolium - Holly flower essence",
        "effects": "Opens heart to love, dissolves negative emotions, promotes compassion",
        "dosage_notes": "Powerful remedy often used alone or with Willow"
    },
    "honeysuckle": {
        "name": "Honeysuckle",
        "symptoms": ["living in past", "nostalgia", "regret", "homesickness", "dwelling on past", "loss of interest in present"],
        "emotional_state": "living in the past",
        "remedy_for": "Living in the past and nostalgia",
        "category": "insufficient_interest",
        "combinations": ["clematis", "wild_rose", "chestnut_bud"],
        "summary": "For those stuck in the past, unable to move forward with their lives",
        "composition": "Lonicera caprifolium - Honeysuckle flower essence",
        "effects": "Helps release the past, brings focus to present opportunities",
        "dosage_notes": "Often combined with Clematis for time-related issues"
    },
    "hornbeam": {
        "name": "Hornbeam",
        "symptoms": ["mental fatigue", "procrastination", "tiredness before starting", "doubt in ability to cope", "weariness"],
        "emotional_state": "mental weariness",
        "remedy_for": "Mental fatigue and procrastination",
        "category": "uncertainty",
        "combinations": ["olive", "elm", "oak"],
        "summary": "For mental tiredness and the Monday morning feeling",
        "composition": "Carpinus betulus - Hornbeam flower essence",
        "effects": "Restores mental energy and enthusiasm, overcomes procrastination",
        "dosage_notes": "Excellent with Olive for complete exhaustion"
    },
    "impatiens": {
        "name": "Impatiens",
        "symptoms": ["impatience", "irritability", "hasty", "tension", "intolerance of slow pace", "quick thinking"],
        "emotional_state": "impatience and irritability",
        "remedy_for": "Impatience and irritability with others",
        "category": "loneliness",
        "combinations": ["beech", "heather", "vine"],
        "summary": "For quick-thinking people who are impatient with slower minds, a Rescue Remedy ingredient",
        "composition": "Impatiens glandulifera - Impatiens flower essence",
        "effects": "Promotes patience and gentleness, reduces tension and irritability",
        "dosage_notes": "Core ingredient in Rescue Remedy for tension relief"
    },
    "larch": {
        "name": "Larch",
        "symptoms": ["lack of confidence", "expects failure", "inferiority complex", "hesitation", "despondency"],
        "emotional_state": "lack of confidence",
        "remedy_for": "Lack of confidence and expectation of failure",
        "category": "despondency",
        "combinations": ["cerato", "centaury", "pine"],
        "summary": "For those who expect to fail and lack confidence in their abilities",
        "composition": "Larix decidua - Larch flower essence",
        "effects": "Builds self-confidence, encourages taking risks, promotes self-belief",
        "dosage_notes": "Essential in confidence-building combinations"
    },
    "mimulus": {
        "name": "Mimulus",
        "symptoms": ["fear of known things", "shyness", "timidity", "nervousness", "anxiety about specific things", "phobias"],
        "emotional_state": "fear of known things",
        "remedy_for": "Fear of known things and shyness",
        "category": "fear",
        "combinations": ["aspen", "larch", "agrimony"],
        "summary": "For everyday fears and anxieties about known things",
        "composition": "Mimulus guttatus - Monkey Flower essence",
        "effects": "Promotes courage and confidence, reduces specific fears and phobias",
        "dosage_notes": "Often paired with Aspen for comprehensive fear treatment"
    },
    "mustard": {
        "name": "Mustard",
        "symptoms": ["depression without cause", "gloom", "melancholy", "sadness", "dark cloud feeling"],
        "emotional_state": "deep depression without reason",
        "remedy_for": "Deep depression that comes and goes without reason",
        "category": "insufficient_interest",
        "combinations": ["gentian", "gorse", "sweet_chestnut"],
        "summary": "For deep gloom and depression that descends like a dark cloud",
        "composition": "Sinapis arvensis - Wild Mustard flower essence",
        "effects": "Brings joy and light, lifts depression and melancholy",
        "dosage_notes": "Key remedy in depression support blends"
    },
    "oak": {
        "name": "Oak",
        "symptoms": ["exhaustion but keeps going", "never gives up", "duty bound", "stubborn persistence", "overwork"],
        "emotional_state": "exhausted but struggling on",
        "remedy_for": "Those who struggle on despite exhaustion",
        "category": "despondency",
        "combinations": ["elm", "olive", "hornbeam"],
        "summary": "For strong, reliable people who never give up but are reaching their limits",
        "composition": "Quercus robur - Oak flower essence",
        "effects": "Restores strength and flexibility, helps recognize limits",
        "dosage_notes": "Essential for stress and overwhelm combinations"
    },
    "olive": {
        "name": "Olive",
        "symptoms": ["complete exhaustion", "drained", "no reserves left", "worn out", "fatigue"],
        "emotional_state": "complete mental and physical exhaustion",
        "remedy_for": "Complete exhaustion of mind and body",
        "category": "insufficient_interest",
        "combinations": ["oak", "elm", "hornbeam"],
        "summary": "For complete physical and mental exhaustion after long struggle",
        "composition": "Olea europaea - Olive flower essence",
        "effects": "Restores vitality and energy, promotes peaceful recovery",
        "dosage_notes": "Often used with Oak for chronic exhaustion patterns"
    },
    "pine": {
        "name": "Pine",
        "symptoms": ["guilt", "self-reproach", "blame self for others' mistakes", "never satisfied with efforts", "apologetic"],
        "emotional_state": "guilt and self-reproach",
        "remedy_for": "Guilt and self-reproach",
        "category": "despondency",
        "combinations": ["crab_apple", "larch", "centaury"],
        "summary": "For guilt, self-blame, and those who are never satisfied with their efforts",
        "composition": "Pinus sylvestris - Scots Pine flower essence",
        "effects": "Promotes self-forgiveness and realistic self-assessment",
        "dosage_notes": "Excellent with Crab Apple for self-criticism"
    },
    "red_chestnut": {
        "name": "Red Chestnut",
        "symptoms": ["excessive worry for others", "fearful for loved ones", "anxiety for others' wellbeing", "over-concern"],
        "emotional_state": "excessive concern for others",
        "remedy_for": "Excessive worry and fear for others",
        "category": "overcare",
        "combinations": ["chicory", "vine", "beech"],
        "summary": "For anxious over-concern for the welfare of loved ones",
        "composition": "Aesculus carnea - Red Chestnut flower essence",
        "effects": "Promotes calm concern without anxiety, sends positive thoughts",
        "dosage_notes": "Often needed by parents and caregivers"
    },
    "rescue_remedy": {
        "name": "Rescue Remedy",
        "symptoms": ["emergency", "trauma", "shock", "panic", "crisis", "stress", "accident"],
        "emotional_state": "emergency and crisis situations",
        "remedy_for": "Emergency situations, trauma, shock and crisis",
        "category": "emergency",
        "combinations": ["rock_rose", "impatiens", "cherry_plum", "star_of_bethlehem", "clematis"],
        "summary": "The famous five-flower emergency blend for crisis and trauma situations",
        "composition": "Rock Rose + Impatiens + Cherry Plum + Star of Bethlehem + Clematis",
        "effects": "Provides immediate comfort and stability during crisis",
        "dosage_notes": "Can be used frequently during emergency situations"
    },
    "rock_rose": {
        "name": "Rock Rose",
        "symptoms": ["terror", "panic", "nightmare", "extreme fear", "helplessness", "emergency"],
        "emotional_state": "extreme terror and panic",
        "remedy_for": "Terror, panic and extreme fear",
        "category": "fear",
        "combinations": ["cherry_plum", "aspen", "mimulus"],
        "summary": "For extreme fear, terror and panic states, a Rescue Remedy ingredient",
        "composition": "Helianthemum nummularium - Rock Rose flower essence",
        "effects": "Provides courage in extreme fear, brings calm to panic",
        "dosage_notes": "Core ingredient in Rescue Remedy for emergency situations"
    },
    "rock_water": {
        "name": "Rock Water",
        "symptoms": ["self-denial", "rigidity", "self-discipline", "hard on self", "strict principles", "inflexibility"],
        "emotional_state": "rigid self-discipline",
        "remedy_for": "Self-denial and rigid adherence to principles",
        "category": "overcare",
        "combinations": ["vine", "beech", "oak"],
        "summary": "For those who are hard on themselves with rigid self-discipline",
        "composition": "Natural spring water from healing wells",
        "effects": "Promotes flexibility and self-compassion, maintains ideals without rigidity",
        "dosage_notes": "Unique non-flower remedy made from natural spring water"
    },
    "scleranthus": {
        "name": "Scleranthus",
        "symptoms": ["indecision", "uncertainty between choices", "mood swings", "hesitation", "vacillation"],
        "emotional_state": "indecision between alternatives",
        "remedy_for": "Indecision and uncertainty between two choices",
        "category": "uncertainty",
        "combinations": ["cerato", "wild_oat", "gentian"],
        "summary": "For indecision and uncertainty when torn between two choices",
        "composition": "Scleranthus annuus - Scleranthus flower essence",
        "effects": "Brings clarity and determination, stabilizes mood swings",
        "dosage_notes": "Essential for decision-making difficulties"
    },
    "star_of_bethlehem": {
        "name": "Star of Bethlehem",
        "symptoms": ["shock", "trauma", "grief", "distress", "after-effects of shock", "comfort"],
        "emotional_state": "shock and trauma",
        "remedy_for": "Shock, trauma and grief",
        "category": "despondency",
        "combinations": ["sweet_chestnut", "willow", "pine"],
        "summary": "The great comforter for shock and trauma, a Rescue Remedy ingredient",
        "composition": "Ornithogalum umbellatum - Star of Bethlehem flower essence",
        "effects": "Heals effects of shock and trauma, provides comfort and healing",
        "dosage_notes": "Core ingredient in Rescue Remedy and grief support blends"
    },
    "sweet_chestnut": {
        "name": "Sweet Chestnut",
        "symptoms": ["extreme mental anguish", "despair", "limit of endurance", "dark night of soul", "hopelessness"],
        "emotional_state": "extreme mental anguish",
        "remedy_for": "Extreme mental anguish and despair",
        "category": "despondency",
        "combinations": ["gorse", "cherry_plum", "star_of_bethlehem"],
        "summary": "For extreme mental anguish when all seems hopeless",
        "composition": "Castanea sativa - Sweet Chestnut flower essence",
        "effects": "Brings hope in darkest moments, provides strength to endure",
        "dosage_notes": "Used in severe depression and crisis support"
    },
    "vervain": {
        "name": "Vervain",
        "symptoms": ["over-enthusiasm", "fanaticism", "strain", "tension", "fixed ideas", "missionary zeal"],
        "emotional_state": "over-enthusiasm and strain",
        "remedy_for": "Over-enthusiasm and fixed ideas",
        "category": "overcare",
        "combinations": ["vine", "impatiens", "beech"],
        "summary": "For over-enthusiastic people who strain themselves with their convictions",
        "composition": "Verbena officinalis - Vervain flower essence",
        "effects": "Promotes relaxation and tolerance, moderates excessive enthusiasm",
        "dosage_notes": "Often needed by activists and passionate individuals"
    },
    "vine": {
        "name": "Vine",
        "symptoms": ["dominating", "inflexible", "tyrannical", "arrogant", "ruthless", "ambitious", "leadership"],
        "emotional_state": "domination and inflexibility",
        "remedy_for": "Dominating behavior and inflexibility",
        "category": "overcare",
        "combinations": ["beech", "vervain", "impatiens"],
        "summary": "For natural leaders who become dominating and inflexible",
        "composition": "Vitis vinifera - Vine flower essence",
        "effects": "Promotes wise leadership without domination, increases flexibility",
        "dosage_notes": "Important for authority figures and leaders"
    },
    "walnut": {
        "name": "Walnut",
        "symptoms": ["influenced by others", "life changes", "transition", "protection from change", "easily led"],
        "emotional_state": "influenced by change and others",
        "remedy_for": "Protection during change and transition",
        "category": "oversensitive",
        "combinations": ["centaury", "cerato", "agrimony"],
        "summary": "The link-breaker for protection during major life changes",
        "composition": "Juglans regia - English Walnut flower essence",
        "effects": "Provides protection from outside influences, supports transitions",
        "dosage_notes": "Essential during major life changes and transitions"
    },
    "water_violet": {
        "name": "Water Violet",
        "symptoms": ["pride", "aloofness", "superiority", "independence", "withdrawn", "self-reliant"],
        "emotional_state": "proud aloofness",
        "remedy_for": "Pride and aloof superiority",
        "category": "loneliness",
        "combinations": ["impatiens", "heather", "vine"],
        "summary": "For proud, aloof people who prefer their own company",
        "composition": "Hottonia palustris - Water Violet flower essence",
        "effects": "Promotes sharing and connection while maintaining dignity",
        "dosage_notes": "Helps balance independence with social connection"
    },
    "white_chestnut": {
        "name": "White Chestnut",
        "symptoms": ["persistent thoughts", "mental arguments", "worrying thoughts", "insomnia", "racing mind"],
        "emotional_state": "persistent unwanted thoughts",
        "remedy_for": "Persistent unwanted thoughts and mental arguments",
        "category": "insufficient_interest",
        "combinations": ["agrimony", "clematis", "mustard"],
        "summary": "For persistent unwanted thoughts and mental chatter",
        "composition": "Aesculus hippocastanum - White Chestnut flower essence",
        "effects": "Brings mental peace and clarity, stops repetitive thoughts",
        "dosage_notes": "Essential in sleep support and anxiety blends"
    },
    "wild_oat": {
        "name": "Wild Oat",
        "symptoms": ["uncertainty about life path", "ambition without direction", "dissatisfaction", "unclear goals"],
        "emotional_state": "uncertainty about life direction",
        "remedy_for": "Uncertainty about life direction and goals",
        "category": "uncertainty",
        "combinations": ["scleranthus", "cerato", "gentian"],
        "summary": "For those who are uncertain about their life direction and calling",
        "composition": "Bromus ramosus - Wild Oat flower essence",
        "effects": "Brings clarity about life purpose and direction",
        "dosage_notes": "Important for career and life direction decisions"
    },
    "wild_rose": {
        "name": "Wild Rose",
        "symptoms": ["apathy", "resignation", "lack of interest", "drift through life", "no effort", "acceptance of fate"],
        "emotional_state": "resignation and apathy",
        "remedy_for": "Apathy and resignation to circumstances",
        "category": "insufficient_interest",
        "combinations": ["clematis", "honeysuckle", "gorse"],
        "summary": "For apathy and resignation when interest in life is lost",
        "composition": "Rosa canina - Wild Rose flower essence",
        "effects": "Rekindles interest and vitality, motivates positive action",
        "dosage_notes": "Important in depression support combinations"
    },
    "willow": {
        "name": "Willow",
        "symptoms": ["resentment", "bitterness", "self-pity", "victim mentality", "blame others", "grudges"],
        "emotional_state": "resentment and bitterness",
        "remedy_for": "Resentment and bitter thoughts",
        "category": "despondency",
        "combinations": ["holly", "beech", "chicory"],
        "summary": "For resentment, bitterness and the 'poor me' attitude",
        "composition": "Salix vitellina - Golden Willow flower essence",
        "effects": "Promotes forgiveness and personal responsibility, releases resentment",
        "dosage_notes": "Often paired with Holly for negative emotions"
    }
}

# Popular Bach Flower Combinations for Specific Conditions
REMEDY_COMBINATIONS = {
    "anxiety_relief": {
        "name": "Anxiety Relief Blend",
        "remedies": ["cherry_plum", "rock_rose", "white_chestnut", "aspen", "mimulus"],
        "concentrations": {"cherry_plum": 2, "rock_rose": 2, "white_chestnut": 2, "aspen": 2, "mimulus": 2},
        "total_drops": 10,
        "bottle_size": "30ml",
        "dosage": "4 drops, 4 times daily",
        "purpose": "Comprehensive anxiety management covering panic, worry, and unknown fears",
        "suitable_for": ["panic attacks", "general anxiety", "worry", "fear", "nervous tension"]
    },
    "depression_support": {
        "name": "Depression Support Blend",
        "remedies": ["gentian", "gorse", "mustard", "sweet_chestnut", "wild_rose"],
        "concentrations": {"gentian": 2, "gorse": 2, "mustard": 2, "sweet_chestnut": 2, "wild_rose": 2},
        "total_drops": 10,
        "bottle_size": "30ml",
        "dosage": "4 drops, 4 times daily",
        "purpose": "Support for various types of depression and despair",
        "suitable_for": ["hopelessness", "discouragement", "deep sadness", "despair", "apathy"]
    },
    "stress_overwhelm": {
        "name": "Stress & Overwhelm Blend",
        "remedies": ["elm", "oak", "agrimony", "white_chestnut", "olive"],
        "concentrations": {"elm": 2, "oak": 2, "agrimony": 2, "white_chestnut": 2, "olive": 2},
        "total_drops": 10,
        "bottle_size": "30ml", 
        "dosage": "4 drops, 4 times daily",
        "purpose": "For overwhelmed, overworked, and exhausted individuals",
        "suitable_for": ["work stress", "overwhelm", "exhaustion", "responsibility burden", "mental fatigue"]
    },
    "sleep_support": {
        "name": "Sleep Support Blend",
        "remedies": ["white_chestnut", "agrimony", "aspen", "rock_rose"],
        "concentrations": {"white_chestnut": 2, "agrimony": 2, "aspen": 2, "rock_rose": 2},
        "total_drops": 8,
        "bottle_size": "30ml",
        "dosage": "4 drops before bed, repeat if needed",
        "purpose": "Calming the mind for better sleep",
        "suitable_for": ["insomnia", "racing thoughts", "nighttime anxiety", "restless sleep"]
    },
    "confidence_building": {
        "name": "Confidence Building Blend",
        "remedies": ["larch", "cerato", "centaury", "pine", "walnut"],
        "concentrations": {"larch": 2, "cerato": 2, "centaury": 2, "pine": 2, "walnut": 2},
        "total_drops": 10,
        "bottle_size": "30ml",
        "dosage": "4 drops, 4 times daily",
        "purpose": "Building self-confidence and inner strength",
        "suitable_for": ["low self-esteem", "lack of confidence", "self-doubt", "people-pleasing"]
    },
    "grief_healing": {
        "name": "Grief Healing Blend", 
        "remedies": ["star_of_bethlehem", "sweet_chestnut", "willow", "honeysuckle"],
        "concentrations": {"star_of_bethlehem": 2, "sweet_chestnut": 2, "willow": 2, "honeysuckle": 2},
        "total_drops": 8,
        "bottle_size": "30ml",
        "dosage": "4 drops, 4 times daily",
        "purpose": "Support during grief and loss",
        "suitable_for": ["loss", "bereavement", "trauma", "shock", "emotional pain"]
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
    recommendations: Dict[str, Any]  # Changed from List to Dict
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
    """Find matches using vector similarity with 1-10 relevance scoring"""
    
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
        
        # Convert similarity to 1-10 relevance score
        relevance_score = min(10, max(1, round(similarities[idx] * 10)))
        
        # Get related remedies from combinations
        related_remedies = []
        for combo_id in remedy_data.get('combinations', []):
            if combo_id in BACH_REMEDIES:
                related_remedies.append({
                    'id': combo_id,
                    'name': BACH_REMEDIES[combo_id]['name'],
                    'summary': BACH_REMEDIES[combo_id]['summary']
                })
        
        matches.append({
            'remedy_id': remedy_id,
            'remedy_name': remedy_data['name'],
            'similarity_score': float(similarities[idx]),
            'relevance_score': relevance_score,
            'symptoms': remedy_data['symptoms'],
            'remedy_for': remedy_data['remedy_for'],
            'category': remedy_data['category'],
            'summary': remedy_data['summary'],
            'composition': remedy_data['composition'],
            'effects': remedy_data['effects'],
            'related_remedies': related_remedies,
            'method': 'vector_similarity'
        })
    
    return matches

def find_knowledge_graph_matches(symptoms: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Find matches using knowledge graph analysis with 1-10 relevance scoring"""
    
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
    for remedy_id, raw_score in top_matches:
        if raw_score > 0:  # Only include remedies with some relevance
            remedy_data = BACH_REMEDIES[remedy_id]
            
            # Convert raw score to 1-10 relevance scale
            relevance_score = min(10, max(1, round(raw_score / 2)))
            
            # Get connected remedies for combination suggestions
            connected_remedies = []
            if knowledge_graph.has_node(remedy_id):
                neighbors = list(knowledge_graph.neighbors(remedy_id))
                connected_remedies = [
                    {
                        'id': neighbor,
                        'name': BACH_REMEDIES[neighbor]['name'],
                        'summary': BACH_REMEDIES[neighbor]['summary']
                    }
                    for neighbor in neighbors[:3]
                ]
            
            matches.append({
                'remedy_id': remedy_id,
                'remedy_name': remedy_data['name'],
                'raw_score': raw_score,
                'relevance_score': relevance_score,
                'symptoms': remedy_data['symptoms'],
                'remedy_for': remedy_data['remedy_for'],
                'category': remedy_data['category'],
                'summary': remedy_data['summary'],
                'composition': remedy_data['composition'],
                'effects': remedy_data['effects'],
                'connected_remedies': connected_remedies,
                'method': 'knowledge_graph'
            })
    
    return matches

def suggest_remedy_combinations(symptoms: str, primary_remedies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Suggest remedy combinations based on symptoms and analysis"""
    
    symptom_words = set(symptoms.lower().split())
    suggestions = []
    
    # Check for matching predefined combinations
    for combo_id, combo_data in REMEDY_COMBINATIONS.items():
        combo_score = 0
        
        # Check if symptoms match the combination's purpose
        suitable_for_words = set(' '.join(combo_data['suitable_for']).lower().split())
        combo_score += len(symptom_words.intersection(suitable_for_words)) * 3
        
        # Check if any primary remedies are in this combination
        primary_remedy_ids = [r['remedy_id'] for r in primary_remedies]
        matching_remedies = set(combo_data['remedies']).intersection(set(primary_remedy_ids))
        combo_score += len(matching_remedies) * 5
        
        if combo_score > 0:
            # Build remedy details for the combination
            remedy_details = []
            for remedy_id in combo_data['remedies']:
                if remedy_id in BACH_REMEDIES:
                    remedy_details.append({
                        'id': remedy_id,
                        'name': BACH_REMEDIES[remedy_id]['name'],
                        'drops': combo_data['concentrations'].get(remedy_id, 2),
                        'summary': BACH_REMEDIES[remedy_id]['summary']
                    })
            
            suggestions.append({
                'combination_id': combo_id,
                'name': combo_data['name'],
                'remedies': remedy_details,
                'total_drops': combo_data['total_drops'],
                'bottle_size': combo_data['bottle_size'],
                'dosage': combo_data['dosage'],
                'purpose': combo_data['purpose'],
                'suitable_for': combo_data['suitable_for'],
                'relevance_score': min(10, max(1, combo_score)),
                'matching_primary': list(matching_remedies)
            })
    
    # Sort by relevance and return top 2
    suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
    return suggestions[:2]

# API Routes
@api_router.post("/recommendations", response_model=Dict[str, Any])
async def get_recommendations(request: RecommendationRequest):
    """Get Bach flower remedy recommendations with combinations"""
    
    try:
        symptoms_text = request.symptoms
        
        # If NLP mode, analyze the text first
        if request.nlp_mode:
            nlp_analysis = await analyze_text_sentiment(symptoms_text)
            symptoms_text = nlp_analysis['extracted_symptoms']
        
        # Get recommendations from both methods
        vector_matches = find_vector_matches(symptoms_text, top_k=1)
        graph_matches = find_knowledge_graph_matches(symptoms_text, top_k=1)
        
        # Get combination suggestions
        all_matches = vector_matches + graph_matches
        combination_suggestions = suggest_remedy_combinations(symptoms_text, all_matches)
        
        # Combine and format results
        recommendations = {
            'vector_recommendation': vector_matches[0] if vector_matches else None,
            'knowledge_graph_recommendation': graph_matches[0] if graph_matches else None,
            'combination_suggestions': combination_suggestions,
            'symptoms_analyzed': symptoms_text,
            'nlp_mode': request.nlp_mode,
            'scoring_info': {
                'relevance_scale': '1-10 (10 = extremely relevant)',
                'vector_similarity_range': '0.0-1.0 (higher = more similar)',
                'combination_matching': 'Based on symptom overlap and remedy inclusion'
            }
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

@api_router.get("/remedies/{remedy_id}/details", response_model=Dict[str, Any])
async def get_remedy_details_full(remedy_id: str):
    """Get comprehensive details for a specific remedy"""
    
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
                'category': BACH_REMEDIES[neighbor]['category'],
                'summary': BACH_REMEDIES[neighbor]['summary']
            }
            for neighbor in neighbors
        ]
    
    # Find combinations containing this remedy
    containing_combinations = []
    for combo_id, combo_data in REMEDY_COMBINATIONS.items():
        if remedy_id in combo_data['remedies']:
            containing_combinations.append({
                'id': combo_id,
                'name': combo_data['name'],
                'purpose': combo_data['purpose'],
                'dosage': combo_data['dosage']
            })
    
    return {
        'remedy': remedy_data,
        'connected_remedies': connected_remedies,
        'containing_combinations': containing_combinations,
        'usage_guidelines': {
            'standard_dose': '2 drops in 30ml mixing bottle',
            'frequency': '4 drops, 4 times daily from mixing bottle',
            'emergency_use': 'Can be increased to every 20-30 minutes for first 6 doses',
            'children': 'Reduce frequency for sensitive individuals'
        }
    }

# Protected Admin Routes
@api_router.get("/admin/vector-database", dependencies=[Depends(verify_admin_credentials)])
async def get_vector_database_data():
    """Get vector database visualization data for admin"""
    
    try:
        # Create embeddings for all remedies
        remedy_data = []
        for remedy_id, remedy_info in BACH_REMEDIES.items():
            text = f"{' '.join(remedy_info['symptoms'])} {remedy_info['emotional_state']}"
            embedding = embedding_model.encode([text])[0]
            
            remedy_data.append({
                'id': remedy_id,
                'name': remedy_info['name'],
                'category': remedy_info['category'],
                'embedding_preview': embedding[:5].tolist(),  # First 5 dimensions for preview
                'vector_length': len(embedding),
                'symptoms_count': len(remedy_info['symptoms'])
            })
        
        return {
            'total_remedies': len(remedy_data),
            'embedding_dimensions': len(embedding_model.encode(['test'])[0]),
            'remedies': remedy_data,
            'model_info': {
                'name': 'all-MiniLM-L6-v2',
                'description': 'Sentence transformer model for semantic similarity'
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving vector database: {str(e)}")

@api_router.get("/admin/knowledge-graph", dependencies=[Depends(verify_admin_credentials)])
async def get_knowledge_graph_data():
    """Get knowledge graph visualization data for admin"""
    
    try:
        # Prepare nodes and edges data
        nodes = []
        edges = []
        
        for remedy_id, remedy_data in BACH_REMEDIES.items():
            nodes.append({
                'id': remedy_id,
                'name': remedy_data['name'],
                'category': remedy_data['category'],
                'symptoms_count': len(remedy_data['symptoms']),
                'connections': len(remedy_data.get('combinations', []))
            })
        
        # Create edges from combinations
        for remedy_id, remedy_data in BACH_REMEDIES.items():
            for connected_id in remedy_data.get('combinations', []):
                if connected_id in BACH_REMEDIES:
                    edges.append({
                        'source': remedy_id,
                        'target': connected_id,
                        'weight': 0.8,
                        'type': 'combination'
                    })
        
        # Add category connections
        categories = {}
        for remedy_id, remedy_data in BACH_REMEDIES.items():
            category = remedy_data['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(remedy_id)
        
        # Add category edges (lighter weight)
        for category, remedy_ids in categories.items():
            for i, remedy1 in enumerate(remedy_ids):
                for remedy2 in remedy_ids[i+1:]:
                    edges.append({
                        'source': remedy1,
                        'target': remedy2,
                        'weight': 0.3,
                        'type': 'category'
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'categories': list(categories.keys()),
            'statistics': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'categories_count': len(categories),
                'average_connections': sum(len(r.get('combinations', [])) for r in BACH_REMEDIES.values()) / len(BACH_REMEDIES)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving knowledge graph: {str(e)}")

@api_router.get("/combinations", response_model=Dict[str, Any])
async def get_all_combinations():
    """Get all available remedy combinations"""
    
    combinations_with_details = {}
    for combo_id, combo_data in REMEDY_COMBINATIONS.items():
        # Add remedy details to each combination
        remedy_details = []
        for remedy_id in combo_data['remedies']:
            if remedy_id in BACH_REMEDIES:
                remedy_details.append({
                    'id': remedy_id,
                    'name': BACH_REMEDIES[remedy_id]['name'],
                    'drops': combo_data['concentrations'].get(remedy_id, 2),
                    'summary': BACH_REMEDIES[remedy_id]['summary']
                })
        
        combinations_with_details[combo_id] = {
            **combo_data,
            'remedy_details': remedy_details
        }
    
    return {
        'combinations': combinations_with_details,
        'usage_guidelines': {
            'mixing_instructions': 'Add specified drops of each remedy to 30ml mixing bottle with spring water',
            'preservation': 'Add 1-2 teaspoons of brandy, apple cider vinegar, or glycerin as preservative',
            'standard_dosage': '4 drops from mixing bottle, 4 times daily',
            'emergency_dosage': 'Can increase frequency to every 20-30 minutes for first 6 doses'
        }
    }

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
        recommendations=recommendations_response  # Now it's a Dict as expected
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

@api_router.post("/admin/login")
async def admin_login(credentials: HTTPBasicCredentials = Depends(security)):
    """Admin login endpoint"""
    
    try:
        # Verify credentials
        verify_admin_credentials(credentials)
        return {
            "message": "Login successful",
            "username": credentials.username,
            "access_level": "admin"
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Admin Routes
@api_router.post("/admin/knowledge-sources", dependencies=[Depends(verify_admin_credentials)], response_model=AdminKnowledgeSource)
async def add_knowledge_source(source: AdminKnowledgeSourceCreate):
    """Add a new knowledge source for admin"""
    
    knowledge_source = AdminKnowledgeSource(**source.dict())
    source_dict = knowledge_source.dict()
    source_dict['timestamp'] = source_dict['timestamp'].isoformat()
    
    await db.knowledge_sources.insert_one(source_dict)
    
    return knowledge_source

@api_router.get("/admin/knowledge-sources", dependencies=[Depends(verify_admin_credentials)], response_model=List[AdminKnowledgeSource])
async def get_knowledge_sources():
    """Get all knowledge sources"""
    
    sources = await db.knowledge_sources.find().to_list(100)
    
    for source in sources:
        if isinstance(source.get('timestamp'), str):
            source['timestamp'] = datetime.fromisoformat(source['timestamp'])
    
    return [AdminKnowledgeSource(**source) for source in sources]

@api_router.post("/admin/rebuild-knowledge-base", dependencies=[Depends(verify_admin_credentials)])
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