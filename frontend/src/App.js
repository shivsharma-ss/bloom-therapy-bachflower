import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Import Shadcn components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Switch } from './components/ui/switch';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './components/ui/tooltip';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';

// Import custom components
import NetworkGraph from './components/NetworkGraph';
import VectorVisualization from './components/VectorVisualization';

// Import icons from Lucide React
import { 
  Flower2, 
  Brain, 
  Sparkles, 
  Heart, 
  Zap, 
  Leaf, 
  Droplets, 
  Moon, 
  Sun, 
  Shield, 
  Lightbulb,
  User,
  Lock,
  Eye,
  EyeOff,
  RefreshCw,
  Plus,
  Save,
  Settings,
  Database,
  Network,
  FlaskConical,
  Beaker,
  Waves,
  Wind,
  Star,
  Gem,
  Palette,
  Wand2,
  TrendingUp,
  Activity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [symptoms, setSymptoms] = useState('');
  const [nlpMode, setNlpMode] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userSelections, setUserSelections] = useState([]);
  const [loadingSelections, setLoadingSelections] = useState(false);
  const [userId] = useState(() => {
    // Get existing user ID from localStorage or create new one
    let storedUserId = localStorage.getItem('bach_flower_user_id');
    if (!storedUserId) {
      storedUserId = `user_${Date.now()}_${Math.random().toString(36).substring(2)}`;
      localStorage.setItem('bach_flower_user_id', storedUserId);
    }
    return storedUserId;
  });
  const [activeTab, setActiveTab] = useState('analyze');
  
  // Admin state
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminCredentials, setAdminCredentials] = useState({ username: '', password: '' });
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [adminSources, setAdminSources] = useState([]);
  const [newSource, setNewSource] = useState({ type: 'text', content: '', url: '' });
  const [vectorData, setVectorData] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [combinations, setCombinations] = useState({});
  const [selectedRemedyDetails, setSelectedRemedyDetails] = useState(null);
  const [showRemedyDialog, setShowRemedyDialog] = useState(false);

  // Load user selections on component mount
  useEffect(() => {
    loadUserSelections();
    loadCombinations();
  }, []);

  const loadUserSelections = async () => {
    try {
      setLoadingSelections(true);
      const response = await axios.get(`${API}/remedy-selections/${userId}`);
      setUserSelections(response.data);
      console.log('Loaded selections for user:', userId, 'Count:', response.data.length);
    } catch (error) {
      console.error('Error loading selections:', error);
      if (error.response?.status !== 404) {
        toast.error('Error loading your saved selections');
      }
    } finally {
      setLoadingSelections(false);
    }
  };

  const loadCombinations = async () => {
    try {
      const response = await axios.get(`${API}/combinations`);
      setCombinations(response.data.combinations);
    } catch (error) {
      console.error('Error loading combinations:', error);
    }
  };

  const loadAdminSources = async () => {
    if (!isAdmin) return;
    try {
      const response = await axios.get(`${API}/admin/knowledge-sources`, {
        auth: adminCredentials
      });
      setAdminSources(response.data);
    } catch (error) {
      console.error('Error loading admin sources:', error);
      toast.error('Error loading knowledge sources');
    }
  };

  const loadVectorData = async () => {
    if (!isAdmin) return;
    try {
      const response = await axios.get(`${API}/admin/vector-database`, {
        auth: adminCredentials
      });
      setVectorData(response.data);
    } catch (error) {
      console.error('Error loading vector data:', error);
      toast.error('Error loading vector database');
    }
  };

  const loadGraphData = async () => {
    if (!isAdmin) return;
    try {
      const response = await axios.get(`${API}/admin/knowledge-graph`, {
        auth: adminCredentials
      });
      setGraphData(response.data);
    } catch (error) {
      console.error('Error loading graph data:', error);
      toast.error('Error loading knowledge graph');
    }
  };

  const handleAdminLogin = async () => {
    try {
      const response = await axios.post(`${API}/admin/login`, {}, {
        auth: adminCredentials
      });
      
      setIsAdmin(true);
      setShowAdminLogin(false);
      toast.success('Admin login successful!');
      
      // Load admin data
      loadAdminSources();
      loadVectorData();
      loadGraphData();
    } catch (error) {
      console.error('Admin login failed:', error);
      toast.error('Invalid admin credentials');
    }
  };

  const analyzeSymptoms = async () => {
    if (!symptoms.trim()) {
      toast.error('Please enter symptoms to analyze');
      return;
    }

    // Additional validation for meaningful input
    if (symptoms.trim().length < 3) {
      toast.error('Please enter more detailed symptoms');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/recommendations`, {
        symptoms: symptoms,
        nlp_mode: nlpMode
      });

      setRecommendations(response.data);
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Error analyzing symptoms:', error);
      toast.error('Error analyzing symptoms. Please try again.');
    }
    setLoading(false);
  };

  const saveSelection = async () => {
    if (!recommendations) {
      toast.error('Please analyze symptoms first');
      return;
    }

    try {
      await axios.post(`${API}/remedy-selections`, {
        user_id: userId,
        symptoms: symptoms,
        nlp_mode: nlpMode
      });

      toast.success('Selection saved successfully!');
      loadUserSelections();
      
      // Clear current analysis
      setSymptoms('');
      setRecommendations(null);
    } catch (error) {
      console.error('Error saving selection:', error);
      toast.error('Error saving selection. Please try again.');
    }
  };

  const addKnowledgeSource = async () => {
    if (!newSource.content.trim()) {
      toast.error('Please enter content for the knowledge source');
      return;
    }

    try {
      await axios.post(`${API}/admin/knowledge-sources`, {
        source_type: newSource.type,
        content: newSource.content,
        source_url: newSource.url || null
      }, {
        auth: adminCredentials
      });

      toast.success('Knowledge source added successfully!');
      setNewSource({ type: 'text', content: '', url: '' });
      loadAdminSources();
    } catch (error) {
      console.error('Error adding knowledge source:', error);
      toast.error('Error adding knowledge source. Please try again.');
    }
  };

  const rebuildKnowledgeBase = async () => {
    try {
      const response = await axios.post(`${API}/admin/rebuild-knowledge-base`, {}, {
        auth: adminCredentials
      });
      toast.success(response.data.message);
    } catch (error) {
      console.error('Error rebuilding knowledge base:', error);
      toast.error('Error rebuilding knowledge base. Please try again.');
    }
  };

  const fetchRemedyDetails = async (remedyId) => {
    try {
      const response = await axios.get(`${API}/remedies/${remedyId}/details`);
      setSelectedRemedyDetails(response.data);
      setShowRemedyDialog(true);
    } catch (error) {
      console.error('Error fetching remedy details:', error);
      toast.error('Error loading remedy details');
    }
  };

  const RecommendationCard = ({ recommendation, type }) => (
    <Card className="h-full bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-purple-500/20 backdrop-blur-sm hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-500 hover:scale-105 card-hover">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button 
                  onClick={() => fetchRemedyDetails(recommendation.remedy_id)}
                  className="text-purple-200 hover:text-purple-100 font-bold text-lg transition-all duration-300 hover:scale-110"
                >
                  {recommendation.remedy_name}
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-sm">{recommendation.summary}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <Badge variant={type === 'vector_recommendation' ? 'default' : 'secondary'} 
                 className={`${type === 'vector_recommendation' 
                   ? 'bg-teal-600 text-white animate-pulse-color' 
                   : 'bg-orange-600 text-white animate-pulse-color'} transition-all duration-300`}>
            {type === 'vector_recommendation' ? (
              <><Database className="w-3 h-3 mr-1" /> Vector Analysis</>
            ) : (
              <><Network className="w-3 h-3 mr-1" /> Knowledge Graph</>
            )}
          </Badge>
        </CardTitle>
        <CardDescription className="text-slate-300 animate-fadeInUp">{recommendation.category}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="animate-fadeInUp" style={{animationDelay: '0.1s'}}>
            <h4 className="font-medium text-sm text-purple-200 mb-1 flex items-center gap-1">
              <Heart className="w-3 h-3" /> Remedy For:
            </h4>
            <p className="text-sm text-slate-300">{recommendation.remedy_for}</p>
          </div>
          
          <div className="animate-fadeInUp" style={{animationDelay: '0.2s'}}>
            <h4 className="font-medium text-sm text-purple-200 mb-1 flex items-center gap-1">
              <Flower2 className="w-3 h-3" /> Key Symptoms:
            </h4>
            <div className="flex flex-wrap gap-1">
              {recommendation.symptoms.slice(0, 4).map((symptom, idx) => (
                <Badge 
                  key={idx} 
                  variant="outline" 
                  className="text-xs border-purple-400/30 text-purple-200 hover:bg-purple-600/20 transition-all duration-300 badge-animate"
                  style={{animationDelay: `${idx * 0.1}s`}}
                >
                  {symptom}
                </Badge>
              ))}
              {recommendation.symptoms.length > 4 && (
                <Badge variant="outline" className="text-xs border-purple-400/30 text-purple-200">
                  +{recommendation.symptoms.length - 4} more
                </Badge>
              )}
            </div>
          </div>

          {/* Enhanced Scoring Information */}
          <div className="grid grid-cols-2 gap-3 animate-fadeInUp" style={{animationDelay: '0.3s'}}>
            <div className="bg-slate-800/50 p-2 rounded hover:bg-slate-700/50 transition-all duration-300">
              <h5 className="text-xs text-teal-200 font-medium flex items-center gap-1">
                <Zap className="w-3 h-3" /> Similarity Score
              </h5>
              <p className="text-sm text-white font-bold">
                {recommendation.similarity_score ? 
                  `${(recommendation.similarity_score * 100).toFixed(1)}%` : 
                  'N/A'
                }
              </p>
            </div>
            <div className="bg-slate-800/50 p-2 rounded hover:bg-slate-700/50 transition-all duration-300">
              <h5 className="text-xs text-orange-200 font-medium flex items-center gap-1">
                <Star className="w-3 h-3" /> Relevance Score
              </h5>
              <p className="text-sm text-white font-bold">
                {recommendation.relevance_score || 'N/A'}/10
              </p>
            </div>
          </div>

          {/* Related/Connected Remedies */}
          {(recommendation.related_remedies || recommendation.connected_remedies) && (
            <div className="animate-fadeInUp" style={{animationDelay: '0.4s'}}>
              <h4 className="font-medium text-sm text-purple-200 mb-2 flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Related Remedies:
              </h4>
              <div className="flex flex-wrap gap-1">
                {(recommendation.related_remedies || recommendation.connected_remedies)?.map((remedy, idx) => (
                  <TooltipProvider key={idx}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Badge 
                          variant="secondary" 
                          className="text-xs bg-purple-700/30 text-purple-100 hover:bg-purple-600/40 cursor-pointer transition-all duration-300 interactive-element"
                          onClick={() => fetchRemedyDetails(remedy.id || remedy)}
                          style={{animationDelay: `${idx * 0.05}s`}}
                        >
                          {remedy.name || remedy}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-sm">{remedy.summary || 'Click for details'}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const CombinationCard = ({ combination }) => (
    <Card className="bg-gradient-to-br from-emerald-800/50 to-teal-900/50 border-emerald-500/20 hover:shadow-lg hover:shadow-emerald-500/20 transition-all duration-500 combination-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-emerald-200">
          <FlaskConical className="w-5 h-5 animate-pulse" />
          {combination.name}
        </CardTitle>
        <CardDescription className="text-emerald-300">{combination.purpose}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-emerald-200 animate-fadeInUp">
            <Droplets className="w-4 h-4" />
            <span>{combination.total_drops} drops in {combination.bottle_size}</span>
            <Badge variant="outline" className="text-xs border-emerald-400/30 text-emerald-200">
              + {combination.preservative}
            </Badge>
          </div>
          
          <div className="animate-fadeInUp" style={{animationDelay: '0.1s'}}>
            <h5 className="font-medium text-emerald-200 mb-2 flex items-center gap-1">
              <Beaker className="w-4 h-4" /> 
              Remedies in this blend:
            </h5>
            <div className="space-y-1">
              {combination.remedies.map((remedy, idx) => (
                <div 
                  key={idx} 
                  className="flex justify-between items-center text-sm bg-emerald-800/20 p-2 rounded hover:bg-emerald-700/30 transition-all duration-300"
                  style={{animationDelay: `${idx * 0.05}s`}}
                >
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button 
                          onClick={() => fetchRemedyDetails(remedy.id)}
                          className="text-emerald-100 hover:text-emerald-50 transition-colors"
                        >
                          {remedy.name}
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-sm max-w-xs">{remedy.summary}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <Badge variant="outline" className="text-xs border-emerald-400/30 text-emerald-200">
                    {remedy.drops} drops
                  </Badge>
                </div>
              ))}
            </div>
          </div>
          
          <div className="text-xs text-emerald-300 bg-emerald-800/30 p-3 rounded animate-fadeInUp" style={{animationDelay: '0.3s'}}>
            <div className="space-y-1">
              <div><strong>Dosage:</strong> {combination.dosage}</div>
              <div><strong>Bottle:</strong> {combination.bottle_size} with {combination.preservative}</div>
              <div><strong>Total:</strong> {combination.total_drops} drops of remedies</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <Toaster />
      
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      {/* Header */}
      <header className="bg-slate-800/80 backdrop-blur-sm border-b border-purple-500/20 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-teal-500 rounded-full flex items-center justify-center">
                  <Flower2 className="w-6 h-6 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                  <Sparkles className="w-2 h-2 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-200 to-teal-200 bg-clip-text text-transparent">
                  Bach Flower Remedies
                </h1>
                <p className="text-sm text-slate-400 flex items-center gap-1">
                  <Brain className="w-3 h-3" />
                  AI-Powered Natural Healing Recommendations
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {!isAdmin && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setShowAdminLogin(true)}
                  className="border-purple-400/30 text-purple-200 hover:bg-purple-600/20"
                >
                  <Lock className="w-4 h-4 mr-1" />
                  Admin
                </Button>
              )}
              {isAdmin && (
                <Badge className="bg-green-600 text-white">
                  <Shield className="w-3 h-3 mr-1" />
                  Admin Active
                </Badge>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 relative z-10">
        <Tabs value={activeTab} onValueChange={(newTab) => {
          setActiveTab(newTab);
          // Reload selections when switching to selections tab
          if (newTab === 'selections') {
            loadUserSelections();
          }
          // Load admin sources when switching to admin tab
          if (newTab === 'admin' && isAdmin) {
            loadAdminSources();
          }
        }} className="space-y-8">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800/60 backdrop-blur-sm border border-purple-500/20">
            <TabsTrigger value="analyze" data-testid="analyze-tab" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Brain className="w-4 h-4 mr-2" />
              Analyze Symptoms
            </TabsTrigger>
            <TabsTrigger value="selections" data-testid="selections-tab" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Heart className="w-4 h-4 mr-2" />
              My Selections
            </TabsTrigger>
            <TabsTrigger value="admin" data-testid="admin-tab" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white" disabled={!isAdmin}>
              <Settings className="w-4 h-4 mr-2" />
              Admin Panel
            </TabsTrigger>
          </TabsList>

          {/* Symptom Analysis Tab */}
          <TabsContent value="analyze" className="space-y-6">
            <Card className="bg-slate-800/40 backdrop-blur-sm border-purple-500/20">
              <CardHeader>
                <CardTitle className="text-purple-200 flex items-center gap-2">
                  <Brain className="w-5 h-5" />
                  Symptom Analysis
                </CardTitle>
                <CardDescription className="text-slate-300">
                  Enter your symptoms to get personalized Bach flower remedy recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* NLP Toggle */}
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-800/30 to-teal-800/30 rounded-lg border border-purple-500/20">
                  <div className="flex-1">
                    <h3 className="font-medium text-purple-200 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4" />
                      Natural Language Processing
                    </h3>
                    <p className="text-sm text-slate-300">
                      {nlpMode 
                        ? 'Describe your feelings in natural language - AI will extract symptoms'
                        : 'Enter specific symptoms separated by commas or "+"'
                      }
                    </p>
                  </div>
                  <Switch 
                    checked={nlpMode} 
                    onCheckedChange={setNlpMode}
                    data-testid="nlp-toggle"
                    className="data-[state=checked]:bg-purple-600"
                  />
                </div>

                {/* Symptom Input */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-purple-200 flex items-center gap-1">
                    <Flower2 className="w-4 h-4" />
                    {nlpMode ? 'Describe how you\'re feeling:' : 'Enter symptoms:'}
                  </label>
                  {nlpMode ? (
                    <Textarea 
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      placeholder="I've been feeling overwhelmed at work, constantly worried about everything, and having trouble sleeping. I feel like I'm always anxious and can't relax..."
                      className="min-h-24 bg-slate-900/50 border-purple-400/30 text-white placeholder-slate-400 focus:border-purple-400"
                      data-testid="symptoms-textarea"
                    />
                  ) : (
                    <Input 
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      placeholder="anxiety, worry, insomnia, restlessness, fear"
                      className="bg-slate-900/50 border-purple-400/30 text-white placeholder-slate-400 focus:border-purple-400"
                      data-testid="symptoms-input"
                    />
                  )}
                </div>

                <Button 
                  onClick={analyzeSymptoms} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-600 to-teal-600 hover:from-purple-700 hover:to-teal-700 text-white"
                  data-testid="analyze-button"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      Analyze Symptoms
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Recommendations Display */}
            {recommendations && (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-200 to-teal-200 bg-clip-text text-transparent mb-2">
                    Your Recommendations
                  </h2>
                  <p className="text-slate-300">
                    Dual analysis methods for comprehensive remedy selection
                  </p>
                </div>

                {/* Scoring Information */}
                <Alert className="bg-slate-800/40 border-purple-500/20">
                  <Lightbulb className="w-4 h-4" />
                  <AlertDescription className="text-slate-300">
                    <div className="grid md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <strong className="text-purple-200">Relevance Scale:</strong> {recommendations.scoring_info?.relevance_scale}
                      </div>
                      <div>
                        <strong className="text-teal-200">Similarity Range:</strong> {recommendations.scoring_info?.vector_similarity_range}
                      </div>
                      <div>
                        <strong className="text-orange-200">Combination Matching:</strong> {recommendations.scoring_info?.combination_matching}
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>

                {/* NLP Analysis Results */}
                {nlpMode && recommendations.nlp_analysis && (
                  <Alert className="bg-blue-900/40 border-blue-500/20">
                    <Brain className="w-4 h-4" />
                    <AlertDescription className="text-blue-100">
                      <div className="space-y-2">
                        <p><strong>Sentiment Analysis:</strong> 
                          {recommendations.nlp_analysis.sentiment_polarity > 0 ? 'Positive' : 
                           recommendations.nlp_analysis.sentiment_polarity < -0.1 ? 'Negative' : 'Neutral'} 
                          ({(recommendations.nlp_analysis.sentiment_polarity * 100).toFixed(1)}%)
                        </p>
                        <p><strong>Extracted Symptoms:</strong> {recommendations.symptoms_analyzed}</p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Dual Recommendations */}
                <div className="grid md:grid-cols-2 gap-6">
                  {recommendations.vector_recommendation && (
                    <RecommendationCard 
                      recommendation={recommendations.vector_recommendation}
                      type="vector_recommendation"
                    />
                  )}
                  
                  {recommendations.knowledge_graph_recommendation && (
                    <RecommendationCard 
                      recommendation={recommendations.knowledge_graph_recommendation}
                      type="knowledge_graph_recommendation"
                    />
                  )}
                </div>

                {/* Combination Suggestions */}
                {recommendations.combination_suggestions && recommendations.combination_suggestions.length > 0 && (
                  <div>
                    <h3 className="text-xl font-bold text-purple-200 mb-4 flex items-center gap-2">
                      <Beaker className="w-5 h-5" />
                      Recommended Combinations
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      {recommendations.combination_suggestions.map((combination, idx) => (
                        <CombinationCard key={idx} combination={combination} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Save Button */}
                <div className="text-center">
                  <Button 
                    onClick={saveSelection}
                    variant="outline"
                    className="bg-slate-800/40 border-purple-400/30 text-purple-200 hover:bg-purple-600/20"
                    data-testid="save-selection-button"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save This Selection
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* My Selections Tab */}
          <TabsContent value="selections" className="space-y-6">
            <Card className="bg-slate-800/40 backdrop-blur-sm border-purple-500/20">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="text-purple-200 flex items-center gap-2">
                      <Heart className="w-5 h-5" />
                      Your Remedy Selections
                    </CardTitle>
                    <CardDescription className="text-slate-300">
                      View and edit your saved Bach flower remedy recommendations
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={loadUserSelections}
                    variant="outline"
                    size="sm"
                    disabled={loadingSelections}
                    data-testid="refresh-selections-button"
                    className="border-purple-400/30 text-purple-200 hover:bg-purple-600/20"
                  >
                    <RefreshCw className={`w-4 h-4 mr-1 ${loadingSelections ? 'animate-spin' : ''}`} />
                    {loadingSelections ? 'Loading...' : 'Refresh'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {loadingSelections ? (
                  <div className="text-center py-8">
                    <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin text-purple-400" />
                    <p className="text-slate-300">Loading your selections...</p>
                  </div>
                ) : userSelections.length === 0 ? (
                  <div className="text-center py-8">
                    <Flower2 className="w-16 h-16 mx-auto mb-4 text-purple-400" />
                    <p className="text-slate-300 mb-2">No selections saved yet.</p>
                    <p className="text-sm text-slate-400">Analyze some symptoms to get started!</p>
                    <Button 
                      onClick={() => setActiveTab('analyze')}
                      variant="outline"
                      className="mt-4 border-purple-400/30 text-purple-200 hover:bg-purple-600/20"
                    >
                      <Brain className="w-4 h-4 mr-2" />
                      Start Analysis
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {userSelections.map((selection, index) => (
                      <Card key={selection.id} className="bg-slate-900/50 border-slate-700/50">
                        <CardContent className="pt-4">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <p className="text-sm text-slate-400 mb-1 flex items-center gap-1">
                                <Moon className="w-3 h-3" />
                                {new Date(selection.timestamp).toLocaleDateString()} at{' '}
                                {new Date(selection.timestamp).toLocaleTimeString()}
                              </p>
                              <p className="font-medium text-slate-200">{selection.symptoms}</p>
                              {selection.nlp_mode && (
                                <Badge variant="secondary" className="mt-1 bg-blue-600 text-white">
                                  <Brain className="w-3 h-3 mr-1" />
                                  NLP Mode
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          <Separator className="my-3 bg-slate-700" />
                          
                          <div className="grid md:grid-cols-2 gap-4">
                            {selection.recommendations.vector_recommendation && (
                              <div className="space-y-2">
                                <h4 className="font-medium text-sm text-teal-200 flex items-center gap-1">
                                  <Database className="w-3 h-3" />
                                  Vector Analysis
                                </h4>
                                <button 
                                  onClick={() => fetchRemedyDetails(selection.recommendations.vector_recommendation.remedy_id)}
                                  className="text-sm font-medium text-white hover:text-teal-200 transition-colors"
                                >
                                  {selection.recommendations.vector_recommendation.remedy_name}
                                </button>
                                <p className="text-xs text-slate-400">
                                  {selection.recommendations.vector_recommendation.remedy_for}
                                </p>
                              </div>
                            )}
                            
                            {selection.recommendations.knowledge_graph_recommendation && (
                              <div className="space-y-2">
                                <h4 className="font-medium text-sm text-orange-200 flex items-center gap-1">
                                  <Network className="w-3 h-3" />
                                  Knowledge Graph
                                </h4>
                                <button 
                                  onClick={() => fetchRemedyDetails(selection.recommendations.knowledge_graph_recommendation.remedy_id)}
                                  className="text-sm font-medium text-white hover:text-orange-200 transition-colors"
                                >
                                  {selection.recommendations.knowledge_graph_recommendation.remedy_name}
                                </button>
                                <p className="text-xs text-slate-400">
                                  {selection.recommendations.knowledge_graph_recommendation.remedy_for}
                                </p>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Admin Panel Tab */}
          {isAdmin && (
            <TabsContent value="admin" className="space-y-6">
              <Card className="bg-slate-800/40 backdrop-blur-sm border-purple-500/20">
                <CardHeader>
                  <CardTitle className="text-purple-200 flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    Admin Dashboard
                  </CardTitle>
                  <CardDescription className="text-slate-300">
                    Manage knowledge base and view system analytics
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Analytics Cards */}
              <div className="grid md:grid-cols-3 gap-6">
                <Card className="bg-gradient-to-br from-teal-800/40 to-teal-900/40 border-teal-500/20 hover:shadow-lg hover:shadow-teal-500/20 transition-all duration-500">
                  <CardHeader>
                    <CardTitle className="text-teal-200 flex items-center gap-2">
                      <Database className="w-5 h-5" />
                      Vector Database
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {vectorData ? (
                      <div className="space-y-2 text-sm">
                        <p className="text-teal-100">Total Remedies: <strong>{vectorData.total_remedies}</strong></p>
                        <p className="text-teal-100">Embedding Dimensions: <strong>{vectorData.embedding_dimensions}</strong></p>
                        <p className="text-teal-100">Model: <strong>{vectorData.model_info.name}</strong></p>
                      </div>
                    ) : (
                      <Button onClick={loadVectorData} variant="outline" size="sm" className="border-teal-400/30 text-teal-200">
                        <Eye className="w-4 h-4 mr-1" />
                        Load Data
                      </Button>
                    )}
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-orange-800/40 to-orange-900/40 border-orange-500/20 hover:shadow-lg hover:shadow-orange-500/20 transition-all duration-500">
                  <CardHeader>
                    <CardTitle className="text-orange-200 flex items-center gap-2">
                      <Network className="w-5 h-5" />
                      Knowledge Graph
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {graphData ? (
                      <div className="space-y-2 text-sm">
                        <p className="text-orange-100">Nodes: <strong>{graphData.statistics.total_nodes}</strong></p>
                        <p className="text-orange-100">Edges: <strong>{graphData.statistics.total_edges}</strong></p>
                        <p className="text-orange-100">Categories: <strong>{graphData.statistics.categories_count}</strong></p>
                      </div>
                    ) : (
                      <Button onClick={loadGraphData} variant="outline" size="sm" className="border-orange-400/30 text-orange-200">
                        <Eye className="w-4 h-4 mr-1" />
                        Load Data
                      </Button>
                    )}
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-purple-800/40 to-purple-900/40 border-purple-500/20 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-500">
                  <CardHeader>
                    <CardTitle className="text-purple-200 flex items-center gap-2">
                      <FlaskConical className="w-5 h-5" />
                      Combinations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <p className="text-purple-100">Available Blends: <strong>{Object.keys(combinations).length}</strong></p>
                      <p className="text-purple-100">Traditional Formulas: <strong>Dr. Bach + Practitioner</strong></p>
                      <p className="text-purple-100">Concentration: <strong>Variable drops per remedy</strong></p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Network Visualizations */}
              <div className="grid lg:grid-cols-2 gap-6">
                <NetworkGraph 
                  graphData={graphData}
                  title="Bach Flower Knowledge Graph"
                  type="knowledge"
                />
                
                <VectorVisualization 
                  vectorData={vectorData}
                  title="Vector Database Visualization"
                />
              </div>

              {/* Knowledge Source Management */}
              <Card className="bg-slate-800/40 backdrop-blur-sm border-purple-500/20">
                <CardHeader>
                  <CardTitle className="text-purple-200 flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    Knowledge Base Management
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Add Knowledge Source Form */}
                  <div className="space-y-4 p-4 bg-slate-900/50 rounded-lg border border-purple-500/20">
                    <h3 className="font-medium text-purple-200 flex items-center gap-2">
                      <Plus className="w-4 h-4" />
                      Add Knowledge Source
                    </h3>
                    
                    <div className="grid md:grid-cols-3 gap-4">
                      <div>
                        <label className="text-sm font-medium text-slate-300 mb-2 block">Source Type</label>
                        <select 
                          value={newSource.type}
                          onChange={(e) => setNewSource({...newSource, type: e.target.value})}
                          className="w-full p-2 border border-purple-400/30 rounded-md bg-slate-900/50 text-white"
                        >
                          <option value="text">Text</option>
                          <option value="web">Web URL</option>
                          <option value="pdf">PDF Document</option>
                          <option value="image">Image</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium text-slate-300 mb-2 block">Source URL (optional)</label>
                        <Input 
                          value={newSource.url}
                          onChange={(e) => setNewSource({...newSource, url: e.target.value})}
                          placeholder="https://example.com/resource"
                          className="bg-slate-900/50 border-purple-400/30 text-white"
                        />
                      </div>
                      
                      <div className="md:col-span-1">
                        <label className="text-sm font-medium text-slate-300 mb-2 block">Actions</label>
                        <Button 
                          onClick={addKnowledgeSource}
                          className="w-full bg-purple-600 hover:bg-purple-700"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Add Source
                        </Button>
                      </div>
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium text-slate-300 mb-2 block">Content</label>
                      <Textarea 
                        value={newSource.content}
                        onChange={(e) => setNewSource({...newSource, content: e.target.value})}
                        placeholder="Enter the content or description of the knowledge source..."
                        className="min-h-24 bg-slate-900/50 border-purple-400/30 text-white"
                      />
                    </div>
                  </div>

                  {/* Rebuild Knowledge Base */}
                  <div className="p-4 bg-orange-900/30 rounded-lg border border-orange-500/20">
                    <h3 className="font-medium text-orange-200 mb-2 flex items-center gap-2">
                      <RefreshCw className="w-4 h-4" />
                      Rebuild Knowledge Base
                    </h3>
                    <p className="text-sm text-orange-300 mb-3">
                      Process all knowledge sources and rebuild the knowledge graphs and vector database.
                    </p>
                    <Button 
                      onClick={rebuildKnowledgeBase}
                      variant="outline"
                      className="border-orange-400/30 text-orange-200 hover:bg-orange-600/20"
                    >
                      <RefreshCw className="w-4 h-4 mr-1" />
                      Rebuild Knowledge Base
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>

      {/* Admin Login Dialog */}
      <Dialog open={showAdminLogin} onOpenChange={setShowAdminLogin}>
        <DialogContent className="bg-slate-800 border-purple-500/20">
          <DialogHeader>
            <DialogTitle className="text-purple-200 flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Admin Login
            </DialogTitle>
            <DialogDescription className="text-slate-300">
              Enter admin credentials to access the management panel
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              placeholder="Username"
              type="text"
              value={adminCredentials.username}
              onChange={(e) => setAdminCredentials({...adminCredentials, username: e.target.value})}
              className="bg-slate-900/50 border-purple-400/30 text-white"
            />
            <Input
              placeholder="Password"
              type="password"
              value={adminCredentials.password}
              onChange={(e) => setAdminCredentials({...adminCredentials, password: e.target.value})}
              className="bg-slate-900/50 border-purple-400/30 text-white"
            />
            <Button onClick={handleAdminLogin} className="w-full bg-purple-600 hover:bg-purple-700">
              <Shield className="w-4 h-4 mr-2" />
              Login
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Remedy Details Dialog */}
      <Dialog open={showRemedyDialog} onOpenChange={setShowRemedyDialog}>
        <DialogContent className="bg-slate-800 border-purple-500/20 max-w-2xl">
          {selectedRemedyDetails && (
            <>
              <DialogHeader>
                <DialogTitle className="text-purple-200 flex items-center gap-2">
                  <Flower2 className="w-5 h-5" />
                  {selectedRemedyDetails.remedy.name}
                </DialogTitle>
                <DialogDescription className="text-slate-300">
                  {selectedRemedyDetails.remedy.remedy_for}
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <div>
                  <h4 className="font-medium text-purple-200 mb-2 flex items-center gap-1">
                    <Leaf className="w-4 h-4" />
                    Composition
                  </h4>
                  <p className="text-sm text-slate-300">{selectedRemedyDetails.remedy.composition}</p>
                </div>

                <div>
                  <h4 className="font-medium text-purple-200 mb-2 flex items-center gap-1">
                    <Sparkles className="w-4 h-4" />
                    Effects
                  </h4>
                  <p className="text-sm text-slate-300">{selectedRemedyDetails.remedy.effects}</p>
                </div>

                <div>
                  <h4 className="font-medium text-purple-200 mb-2 flex items-center gap-1">
                    <Droplets className="w-4 h-4" />
                    Usage Guidelines
                  </h4>
                  <div className="text-sm text-slate-300 space-y-1">
                    <p><strong>Standard Dose:</strong> {selectedRemedyDetails.usage_guidelines.standard_dose}</p>
                    <p><strong>Frequency:</strong> {selectedRemedyDetails.usage_guidelines.frequency}</p>
                    <p><strong>Emergency Use:</strong> {selectedRemedyDetails.usage_guidelines.emergency_use}</p>
                  </div>
                </div>

                {selectedRemedyDetails.connected_remedies.length > 0 && (
                  <div>
                    <h4 className="font-medium text-purple-200 mb-2 flex items-center gap-1">
                      <Network className="w-4 h-4" />
                      Connected Remedies
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedRemedyDetails.connected_remedies.map((remedy, idx) => (
                        <Badge 
                          key={idx} 
                          variant="outline" 
                          className="cursor-pointer border-purple-400/30 text-purple-200 hover:bg-purple-600/20"
                          onClick={() => fetchRemedyDetails(remedy.id)}
                        >
                          {remedy.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedRemedyDetails.containing_combinations.length > 0 && (
                  <div>
                    <h4 className="font-medium text-purple-200 mb-2 flex items-center gap-1">
                      <FlaskConical className="w-4 h-4" />
                      Available in Combinations
                    </h4>
                    <div className="space-y-2">
                      {selectedRemedyDetails.containing_combinations.map((combo, idx) => (
                        <div key={idx} className="bg-slate-900/50 p-2 rounded">
                          <p className="text-sm font-medium text-slate-200">{combo.name}</p>
                          <p className="text-xs text-slate-400">{combo.purpose}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;