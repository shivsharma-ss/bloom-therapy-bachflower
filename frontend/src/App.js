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
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';

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
  const [adminSources, setAdminSources] = useState([]);
  const [newSource, setNewSource] = useState({ type: 'text', content: '', url: '' });

  // Load user selections on component mount
  useEffect(() => {
    loadUserSelections();
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

  const loadAdminSources = async () => {
    try {
      const response = await axios.get(`${API}/admin/knowledge-sources`);
      setAdminSources(response.data);
    } catch (error) {
      console.error('Error loading admin sources:', error);
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

  const updateSelection = async (selectionId, newSymptoms) => {
    try {
      await axios.put(`${API}/remedy-selections/${selectionId}`, 
        { symptoms: newSymptoms },
        { headers: { 'Content-Type': 'application/json' }}
      );

      toast.success('Selection updated successfully!');
      loadUserSelections();
    } catch (error) {
      console.error('Error updating selection:', error);
      toast.error('Error updating selection. Please try again.');
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
      const response = await axios.post(`${API}/admin/rebuild-knowledge-base`);
      toast.success(response.data.message);
    } catch (error) {
      console.error('Error rebuilding knowledge base:', error);
      toast.error('Error rebuilding knowledge base. Please try again.');
    }
  };

  const RecommendationCard = ({ recommendation, type }) => (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {recommendation.remedy_name}
          <Badge variant={type === 'vector_recommendation' ? 'default' : 'secondary'}>
            {type === 'vector_recommendation' ? 'Vector Analysis' : 'Knowledge Graph'}
          </Badge>
        </CardTitle>
        <CardDescription>{recommendation.category}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <h4 className="font-medium text-sm text-slate-700 mb-1">Remedy For:</h4>
            <p className="text-sm">{recommendation.remedy_for}</p>
          </div>
          <div>
            <h4 className="font-medium text-sm text-slate-700 mb-1">Key Symptoms:</h4>
            <div className="flex flex-wrap gap-1">
              {recommendation.symptoms.slice(0, 4).map((symptom, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {symptom}
                </Badge>
              ))}
              {recommendation.symptoms.length > 4 && (
                <Badge variant="outline" className="text-xs">
                  +{recommendation.symptoms.length - 4} more
                </Badge>
              )}
            </div>
          </div>
          {recommendation.similarity_score && (
            <div>
              <span className="text-xs text-slate-600">
                Similarity: {(recommendation.similarity_score * 100).toFixed(1)}%
              </span>
            </div>
          )}
          {recommendation.relevance_score && (
            <div>
              <span className="text-xs text-slate-600">
                Relevance Score: {recommendation.relevance_score}
              </span>
            </div>
          )}
          {recommendation.connected_remedies && recommendation.connected_remedies.length > 0 && (
            <div>
              <h4 className="font-medium text-sm text-slate-700 mb-1">Related Remedies:</h4>
              <div className="flex flex-wrap gap-1">
                {recommendation.connected_remedies.map((remedy, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {remedy}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      <Toaster />
      
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">🌸</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-700 to-teal-700 bg-clip-text text-transparent">
                  Bach Flower Remedies
                </h1>
                <p className="text-sm text-slate-600">AI-Powered Natural Healing Recommendations</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <TabsList className="grid w-full grid-cols-3 bg-white/60 backdrop-blur-sm">
            <TabsTrigger value="analyze" data-testid="analyze-tab">Analyze Symptoms</TabsTrigger>
            <TabsTrigger value="selections" data-testid="selections-tab">My Selections</TabsTrigger>
            <TabsTrigger value="admin" data-testid="admin-tab">Admin Panel</TabsTrigger>
          </TabsList>

          {/* Symptom Analysis Tab */}
          <TabsContent value="analyze" className="space-y-6">
            <Card className="bg-white/60 backdrop-blur-sm border-emerald-200">
              <CardHeader>
                <CardTitle className="text-emerald-800">Symptom Analysis</CardTitle>
                <CardDescription>
                  Enter your symptoms to get personalized Bach flower remedy recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* NLP Toggle */}
                <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                  <div className="flex-1">
                    <h3 className="font-medium text-emerald-800">Natural Language Processing</h3>
                    <p className="text-sm text-emerald-600">
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
                  />
                </div>

                {/* Symptom Input */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    {nlpMode ? 'Describe how you\'re feeling:' : 'Enter symptoms:'}
                  </label>
                  {nlpMode ? (
                    <Textarea 
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      placeholder="I've been feeling overwhelmed at work, constantly worried about everything, and having trouble sleeping. I feel like I'm always anxious and can't relax..."
                      className="min-h-24 bg-white border-emerald-200 focus:border-emerald-400"
                      data-testid="symptoms-textarea"
                    />
                  ) : (
                    <Input 
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      placeholder="anxiety, worry, insomnia, restlessness, fear"
                      className="bg-white border-emerald-200 focus:border-emerald-400"
                      data-testid="symptoms-input"
                    />
                  )}
                </div>

                <Button 
                  onClick={analyzeSymptoms} 
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                  data-testid="analyze-button"
                >
                  {loading ? 'Analyzing...' : 'Analyze Symptoms'}
                </Button>
              </CardContent>
            </Card>

            {/* Recommendations Display */}
            {recommendations && (
              <div className="space-y-6">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-emerald-800 mb-2">Your Recommendations</h2>
                  <p className="text-slate-600">
                    Two complementary analysis methods for comprehensive remedy selection
                  </p>
                </div>

                {/* NLP Analysis Results */}
                {nlpMode && recommendations.nlp_analysis && (
                  <Alert className="bg-blue-50 border-blue-200">
                    <AlertDescription>
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

                {/* Save Button */}
                <div className="text-center">
                  <Button 
                    onClick={saveSelection}
                    variant="outline"
                    className="bg-white border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                    data-testid="save-selection-button"
                  >
                    Save This Selection
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          {/* My Selections Tab */}
          <TabsContent value="selections" className="space-y-6">
            <Card className="bg-white/60 backdrop-blur-sm border-emerald-200">
              <CardHeader>
                <CardTitle className="text-emerald-800">Your Remedy Selections</CardTitle>
                <CardDescription>
                  View and edit your saved Bach flower remedy recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                {userSelections.length === 0 ? (
                  <p className="text-center text-slate-500 py-8">
                    No selections saved yet. Analyze some symptoms to get started!
                  </p>
                ) : (
                  <div className="space-y-4">
                    {userSelections.map((selection, index) => (
                      <Card key={selection.id} className="bg-white border-slate-200">
                        <CardContent className="pt-4">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <p className="text-sm text-slate-600 mb-1">
                                {new Date(selection.timestamp).toLocaleDateString()} at{' '}
                                {new Date(selection.timestamp).toLocaleTimeString()}
                              </p>
                              <p className="font-medium">{selection.symptoms}</p>
                              {selection.nlp_mode && (
                                <Badge variant="secondary" className="mt-1">NLP Mode</Badge>
                              )}
                            </div>
                          </div>
                          
                          <Separator className="my-3" />
                          
                          <div className="grid md:grid-cols-2 gap-4">
                            {selection.recommendations.vector_recommendation && (
                              <div className="space-y-2">
                                <h4 className="font-medium text-sm text-emerald-700">Vector Analysis</h4>
                                <p className="text-sm font-medium">
                                  {selection.recommendations.vector_recommendation.remedy_name}
                                </p>
                                <p className="text-xs text-slate-600">
                                  {selection.recommendations.vector_recommendation.remedy_for}
                                </p>
                              </div>
                            )}
                            
                            {selection.recommendations.knowledge_graph_recommendation && (
                              <div className="space-y-2">
                                <h4 className="font-medium text-sm text-teal-700">Knowledge Graph</h4>
                                <p className="text-sm font-medium">
                                  {selection.recommendations.knowledge_graph_recommendation.remedy_name}
                                </p>
                                <p className="text-xs text-slate-600">
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
          <TabsContent value="admin" className="space-y-6">
            <Card className="bg-white/60 backdrop-blur-sm border-emerald-200">
              <CardHeader>
                <CardTitle className="text-emerald-800">Knowledge Base Management</CardTitle>
                <CardDescription>
                  Add new sources and manage the Bach flower remedy knowledge base
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Add Knowledge Source */}
                <div className="space-y-4 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                  <h3 className="font-medium text-emerald-800">Add Knowledge Source</h3>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium text-slate-700 mb-2 block">Source Type</label>
                      <select 
                        value={newSource.type}
                        onChange={(e) => setNewSource({...newSource, type: e.target.value})}
                        className="w-full p-2 border border-emerald-200 rounded-md bg-white"
                        data-testid="source-type-select"
                      >
                        <option value="text">Text</option>
                        <option value="web">Web URL</option>
                        <option value="pdf">PDF Document</option>
                        <option value="image">Image</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium text-slate-700 mb-2 block">Source URL (optional)</label>
                      <Input 
                        value={newSource.url}
                        onChange={(e) => setNewSource({...newSource, url: e.target.value})}
                        placeholder="https://example.com/resource"
                        className="bg-white border-emerald-200"
                        data-testid="source-url-input"
                      />
                    </div>
                    
                    <div className="md:col-span-1">
                      <label className="text-sm font-medium text-slate-700 mb-2 block">Actions</label>
                      <Button 
                        onClick={addKnowledgeSource}
                        className="w-full bg-emerald-600 hover:bg-emerald-700"
                        data-testid="add-source-button"
                      >
                        Add Source
                      </Button>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-slate-700 mb-2 block">Content</label>
                    <Textarea 
                      value={newSource.content}
                      onChange={(e) => setNewSource({...newSource, content: e.target.value})}
                      placeholder="Enter the content or description of the knowledge source..."
                      className="min-h-24 bg-white border-emerald-200"
                      data-testid="source-content-textarea"
                    />
                  </div>
                </div>

                {/* Rebuild Knowledge Base */}
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <h3 className="font-medium text-orange-800 mb-2">Rebuild Knowledge Base</h3>
                  <p className="text-sm text-orange-700 mb-3">
                    Process all knowledge sources and rebuild the knowledge graphs and vector database.
                  </p>
                  <Button 
                    onClick={rebuildKnowledgeBase}
                    variant="outline"
                    className="border-orange-300 text-orange-700 hover:bg-orange-100"
                    data-testid="rebuild-kb-button"
                  >
                    Rebuild Knowledge Base
                  </Button>
                </div>

                {/* Load Sources on Tab Active */}
                {activeTab === 'admin' && (
                  <div className="pt-4">
                    <Button 
                      onClick={loadAdminSources}
                      variant="outline"
                      className="mb-4"
                      data-testid="load-sources-button"
                    >
                      Load Knowledge Sources
                    </Button>
                    
                    {adminSources.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-medium text-slate-700">Current Sources ({adminSources.length})</h4>
                        {adminSources.slice(0, 5).map((source, index) => (
                          <Card key={source.id} className="bg-white border-slate-200">
                            <CardContent className="pt-3 pb-3">
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <div className="flex gap-2 items-center mb-1">
                                    <Badge variant="outline">{source.source_type}</Badge>
                                    <Badge variant={source.processed ? 'default' : 'secondary'}>
                                      {source.processed ? 'Processed' : 'Pending'}
                                    </Badge>
                                  </div>
                                  <p className="text-sm text-slate-600 truncate">
                                    {source.content.length > 100 
                                      ? `${source.content.substring(0, 100)}...` 
                                      : source.content}
                                  </p>
                                  {source.source_url && (
                                    <p className="text-xs text-blue-600 mt-1">{source.source_url}</p>
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                        {adminSources.length > 5 && (
                          <p className="text-sm text-slate-500 text-center">
                            ... and {adminSources.length - 5} more sources
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;