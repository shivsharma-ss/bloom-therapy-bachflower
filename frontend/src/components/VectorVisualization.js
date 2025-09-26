import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Database, Zap } from 'lucide-react';

const VectorVisualization = ({ vectorData, title }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!vectorData || !vectorData.remedies) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 120, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Prepare data - using embedding preview for visualization
    const remedies = vectorData.remedies.map(remedy => ({
      ...remedy,
      // Use first two dimensions for 2D projection
      x: remedy.embedding_preview[0],
      y: remedy.embedding_preview[1],
      // Use third dimension for size/color intensity
      intensity: Math.abs(remedy.embedding_preview[2])
    }));

    // Create scales
    const xExtent = d3.extent(remedies, d => d.x);
    const yExtent = d3.extent(remedies, d => d.y);
    const intensityExtent = d3.extent(remedies, d => d.intensity);

    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain(yExtent)
      .range([innerHeight, 0]);

    const radiusScale = d3.scaleSqrt()
      .domain([0, d3.max(remedies, d => d.symptoms_count)])
      .range([4, 16]);

    const colorScale = d3.scaleSequential(d3.interpolatePurples)
      .domain(intensityExtent);

    // Create tooltip
    const tooltip = d3.select("body")
      .append("div")
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "rgba(15, 23, 42, 0.95)")
      .style("color", "#e2e8f0")
      .style("padding", "8px 12px")
      .style("border-radius", "6px")
      .style("border", "1px solid rgba(139, 92, 246, 0.3)")
      .style("font-size", "12px")
      .style("z-index", "1000");

    // Add background grid
    const xAxis = d3.axisBottom(xScale).ticks(8);
    const yAxis = d3.axisLeft(yScale).ticks(8);

    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(xAxis
        .tickSize(-innerHeight)
        .tickFormat("")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.2);

    g.append("g")
      .attr("class", "grid")
      .call(yAxis
        .tickSize(-innerWidth)
        .tickFormat("")
      )
      .style("stroke-dasharray", "3,3")
      .style("opacity", 0.2);

    // Add axes
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .style("color", "#94a3b8");

    g.append("g")
      .call(d3.axisLeft(yScale))
      .style("color", "#94a3b8");

    // Add axis labels
    g.append("text")
      .attr("transform", `translate(${innerWidth / 2}, ${innerHeight + 35})`)
      .style("text-anchor", "middle")
      .style("fill", "#cbd5e1")
      .style("font-size", "12px")
      .text("Embedding Dimension 1");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0 - margin.left + 15)
      .attr("x", 0 - (innerHeight / 2))
      .style("text-anchor", "middle")
      .style("fill", "#cbd5e1")
      .style("font-size", "12px")
      .text("Embedding Dimension 2");

    // Create circles for remedies
    const circles = g.selectAll("circle")
      .data(remedies)
      .enter()
      .append("circle")
      .attr("cx", d => xScale(d.x))
      .attr("cy", d => yScale(d.y))
      .attr("r", d => radiusScale(d.symptoms_count))
      .style("fill", d => colorScale(d.intensity))
      .style("stroke", "#8b5cf6")
      .style("stroke-width", 1.5)
      .style("opacity", 0.8)
      .style("cursor", "pointer");

    // Add category color coding
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

    circles
      .style("stroke", d => categoryColors[d.category] || "#8b5cf6")
      .style("stroke-width", 2);

    // Add interactivity
    circles
      .on("mouseover", function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", d => radiusScale(d.symptoms_count) * 1.5)
          .style("stroke-width", 3);

        tooltip
          .style("visibility", "visible")
          .html(`
            <strong>${d.name}</strong><br/>
            Category: ${d.category}<br/>
            Symptoms: ${d.symptoms_count}<br/>
            Vector Length: ${d.vector_length}<br/>
            Embedding Preview: [${d.embedding_preview.slice(0, 3).map(x => x.toFixed(3)).join(', ')}...]
          `);
      })
      .on("mousemove", function(event) {
        tooltip
          .style("top", (event.pageY - 10) + "px")
          .style("left", (event.pageX + 10) + "px");
      })
      .on("mouseout", function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", d => radiusScale(d.symptoms_count))
          .style("stroke-width", 2);

        tooltip.style("visibility", "hidden");
      });

    // Add labels for larger nodes
    g.selectAll("text.node-label")
      .data(remedies.filter(d => d.symptoms_count > 5))
      .enter()
      .append("text")
      .attr("class", "node-label")
      .attr("x", d => xScale(d.x))
      .attr("y", d => yScale(d.y) + radiusScale(d.symptoms_count) + 12)
      .style("text-anchor", "middle")
      .style("fill", "#e2e8f0")
      .style("font-size", "10px")
      .style("font-weight", "500")
      .text(d => d.name);

    // Cleanup tooltip on component unmount
    return () => {
      d3.select("body").selectAll("div").filter(function() {
        return this.style.position === "absolute" && 
               this.style.visibility === "hidden";
      }).remove();
    };

  }, [vectorData]);

  if (!vectorData) {
    return (
      <Card className="bg-slate-800/40 border-teal-500/20">
        <CardHeader>
          <CardTitle className="text-teal-200 flex items-center gap-2">
            <Database className="w-5 h-5" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-slate-400">
            <Zap className="w-8 h-8 mr-2" />
            No vector data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/40 border-teal-500/20">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-teal-200 flex items-center gap-2">
              <Database className="w-5 h-5" />
              {title}
            </CardTitle>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline" className="text-xs border-teal-400/30 text-teal-200">
                {vectorData.total_remedies} Remedies
              </Badge>
              <Badge variant="outline" className="text-xs border-teal-400/30 text-teal-200">
                {vectorData.embedding_dimensions}D Embeddings
              </Badge>
              <Badge variant="outline" className="text-xs border-teal-400/30 text-teal-200">
                {vectorData.model_info.name}
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <svg ref={svgRef}></svg>
          
          {/* Legend */}
          <div className="absolute top-4 right-4 bg-slate-800/90 p-3 rounded-lg border border-teal-500/20">
            <h4 className="text-xs font-medium text-teal-200 mb-2">Legend</h4>
            <div className="space-y-1 text-xs text-slate-300">
              <div>• Circle size = Symptom count</div>
              <div>• Color intensity = Embedding strength</div>
              <div>• Border color = Category</div>
              <div>• Position = 2D projection</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VectorVisualization;