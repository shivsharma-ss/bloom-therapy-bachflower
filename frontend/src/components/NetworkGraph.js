import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { ZoomIn, ZoomOut, RotateCcw, Info } from 'lucide-react';

const NetworkGraph = ({ graphData, title, type = 'knowledge' }) => {
  const fgRef = useRef();
  const [selectedNode, setSelectedNode] = useState(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState(null);

  const categoryColors = {
    'fear': '#ef4444',
    'uncertainty': '#f59e0b', 
    'insufficient_interest': '#8b5cf6',
    'loneliness': '#06b6d4',
    'oversensitive': '#10b981',
    'despondency': '#6366f1',
    'overcare': '#f97316',
    'emergency': '#dc2626'
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    
    // Highlight connected nodes
    const connectedNodes = new Set();
    const connectedLinks = new Set();
    
    if (graphData && graphData.edges) {
      graphData.edges.forEach(link => {
        if (link.source === node.id || link.target === node.id) {
          connectedLinks.add(link);
          connectedNodes.add(link.source === node.id ? link.target : link.source);
        }
      });
    }
    
    connectedNodes.add(node.id);
    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);
  };

  const handleNodeHover = (node) => {
    setHoverNode(node);
    
    if (node) {
      const connectedNodes = new Set();
      const connectedLinks = new Set();
      
      if (graphData && graphData.edges) {
        graphData.edges.forEach(link => {
          if (link.source === node.id || link.target === node.id) {
            connectedLinks.add(link);
            connectedNodes.add(link.source === node.id ? link.target : link.source);
          }
        });
      }
      
      connectedNodes.add(node.id);
      setHighlightNodes(connectedNodes);
      setHighlightLinks(connectedLinks);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  const resetView = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  };

  const zoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() * 1.5);
    }
  };

  const zoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() / 1.5);
    }
  };

  useEffect(() => {
    if (fgRef.current && graphData) {
      // Auto-fit graph on load
      setTimeout(() => {
        fgRef.current.zoomToFit(400);
      }, 100);
    }
  }, [graphData]);

  if (!graphData) {
    return (
      <Card className="bg-slate-800/40 border-purple-500/20">
        <CardHeader>
          <CardTitle className="text-purple-200">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-slate-400">
            <Info className="w-8 h-8 mr-2" />
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/40 border-purple-500/20">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-purple-200">{title}</CardTitle>
            <div className="flex gap-2 mt-2">
              {graphData.statistics && (
                <>
                  <Badge variant="outline" className="text-xs border-purple-400/30 text-purple-200">
                    {graphData.statistics.total_nodes} Nodes
                  </Badge>
                  <Badge variant="outline" className="text-xs border-purple-400/30 text-purple-200">
                    {graphData.statistics.total_edges} Edges
                  </Badge>
                </>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={zoomIn} className="border-purple-400/30 text-purple-200">
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={zoomOut} className="border-purple-400/30 text-purple-200">
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={resetView} className="border-purple-400/30 text-purple-200">
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <ForceGraph2D
            ref={fgRef}
            graphData={{
              nodes: graphData.nodes || [],
              links: graphData.edges || []
            }}
            width={800}
            height={600}
            backgroundColor="rgba(15, 23, 42, 0.8)"
            nodeAutoColorBy="category"
            nodeColor={node => {
              if (selectedNode && node.id === selectedNode.id) return '#fbbf24';
              if (hoverNode && node.id === hoverNode.id) return '#f59e0b';
              if (highlightNodes.has(node.id)) return categoryColors[node.category] || '#8b5cf6';
              return categoryColors[node.category] || '#64748b';
            }}
            nodeRelSize={4}
            nodeVal={node => {
              if (selectedNode && node.id === selectedNode.id) return 8;
              if (hoverNode && node.id === hoverNode.id) return 6;
              return Math.max(3, node.connections || 1);
            }}
            nodeLabel={node => `
              <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px; max-width: 200px;">
                <strong>${node.name}</strong><br/>
                Category: ${node.category}<br/>
                Symptoms: ${node.symptoms_count}<br/>
                Connections: ${node.connections}
              </div>
            `}
            nodeCanvasObject={(node, ctx, globalScale) => {
              // Draw node
              const label = node.name;
              const fontSize = 10 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              
              // Node circle
              ctx.beginPath();
              const nodeSize = Math.max(3, node.connections || 1) * (selectedNode && node.id === selectedNode.id ? 2 : 1);
              ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI, false);
              
              // Node color
              let nodeColor = categoryColors[node.category] || '#64748b';
              if (selectedNode && node.id === selectedNode.id) nodeColor = '#fbbf24';
              else if (hoverNode && node.id === hoverNode.id) nodeColor = '#f59e0b';
              else if (highlightNodes.has(node.id)) nodeColor = categoryColors[node.category] || '#8b5cf6';
              else if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) nodeColor = '#374151';
              
              ctx.fillStyle = nodeColor;
              ctx.fill();
              
              // Node border
              ctx.strokeStyle = highlightNodes.has(node.id) ? '#ffffff' : 'rgba(255,255,255,0.3)';
              ctx.lineWidth = highlightNodes.has(node.id) ? 2 : 1;
              ctx.stroke();
              
              // Label for larger nodes
              if (nodeSize > 4 || selectedNode?.id === node.id) {
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#ffffff';
                ctx.fillText(label, node.x, node.y + nodeSize + fontSize + 2);
              }
            }}
            linkColor={link => {
              if (highlightLinks.has(link)) return '#8b5cf6';
              if (highlightLinks.size > 0) return 'rgba(100, 116, 139, 0.2)';
              return link.type === 'combination' ? 'rgba(139, 92, 246, 0.6)' : 'rgba(100, 116, 139, 0.4)';
            }}
            linkWidth={link => highlightLinks.has(link) ? 3 : (link.weight > 0.5 ? 2 : 1)}
            linkDirectionalParticles={0}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            onBackgroundClick={() => {
              setSelectedNode(null);
              setHighlightNodes(new Set());
              setHighlightLinks(new Set());
            }}
            cooldownTicks={100}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.08}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            enablePanInteraction={true}
          />
          
          {/* Legend */}
          <div className="absolute top-4 right-4 bg-slate-800/90 p-3 rounded-lg border border-purple-500/20">
            <h4 className="text-xs font-medium text-purple-200 mb-2">Categories</h4>
            <div className="space-y-1">
              {Object.entries(categoryColors).map(([category, color]) => (
                <div key={category} className="flex items-center gap-2 text-xs">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: color }}
                  ></div>
                  <span className="text-slate-300 capitalize">{category.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Selected Node Info */}
          {selectedNode && (
            <div className="absolute bottom-4 left-4 bg-slate-800/90 p-3 rounded-lg border border-purple-500/20 max-w-xs">
              <h4 className="font-medium text-purple-200 mb-1">{selectedNode.name}</h4>
              <p className="text-xs text-slate-300 mb-1">
                <strong>Category:</strong> {selectedNode.category}
              </p>
              <p className="text-xs text-slate-300 mb-1">
                <strong>Symptoms:</strong> {selectedNode.symptoms_count}
              </p>
              <p className="text-xs text-slate-300">
                <strong>Connections:</strong> {selectedNode.connections}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default NetworkGraph;