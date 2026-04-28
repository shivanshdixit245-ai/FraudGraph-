import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function ForceGraph({ 
  nodes = [], 
  edges = [], 
  onNodeClick, 
  selectedNodeId 
}) {
  const containerRef = useRef(null);
  // Keeps track of the D3 graph data so we don't lose velocity and positions across re-renders
  const graphDataRef = useRef({ nodes: [], links: [] });
  const simulationRef = useRef(null);
  const svgElementsRef = useRef({ svg: null, g: null, linkGroup: null, nodeGroup: null });

  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    // 1. Initial SVG & Simulation Setup (runs only once)
    if (!simulationRef.current) {
      const svg = d3.select(containerRef.current)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .style('background-color', '#0D1117');

      // Setup Glow Filter for high-risk nodes
      const defs = svg.append('defs');
      const filter = defs.append('filter')
        .attr('id', 'glow')
        .attr('x', '-50%')
        .attr('y', '-50%')
        .attr('width', '200%')
        .attr('height', '200%');
      filter.append('feGaussianBlur')
        .attr('stdDeviation', '4')
        .attr('result', 'coloredBlur');
      const feMerge = filter.append('feMerge');
      feMerge.append('feMergeNode').attr('in', 'coloredBlur');
      feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

      // Main container for zooming/panning
      const g = svg.append('g').attr('class', 'main-group');
      const linkGroup = g.append('g').attr('class', 'links');
      const nodeGroup = g.append('g').attr('class', 'nodes');

      // Enable Zoom & Pan
      const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      svg.call(zoom);

      // Initialize Force Simulation
      const simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(65))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('collide', d3.forceCollide().radius(20))
        .force('x', d3.forceX(width / 2).strength(0.003))
        .force('y', d3.forceY(height / 2).strength(0.003));

      simulationRef.current = simulation;
      svgElementsRef.current = { svg, g, linkGroup, nodeGroup };

      // Handle Resize to keep center gravity updated
      const handleResize = () => {
        if (!containerRef.current) return;
        const w = containerRef.current.clientWidth;
        const h = containerRef.current.clientHeight;
        simulation.force('x', d3.forceX(w / 2).strength(0.003))
                  .force('y', d3.forceY(h / 2).strength(0.003));
        simulation.alpha(0.1).restart();
      };
      window.addEventListener('resize', handleResize);
      containerRef.current._handleResize = handleResize;
    }

    const { linkGroup, nodeGroup } = svgElementsRef.current;
    const simulation = simulationRef.current;

    console.log(`[ForceGraph] Rendering with ${nodes.length} nodes, ${edges.length} edges. selectedNodeId: ${selectedNodeId}`);

    // 2. Reconcile Data to preserve D3 physics state (x, y, vx, vy, fx, fy)
    let isTopologyChanged = false;
    const oldNodesMap = new Map(graphDataRef.current.nodes.map(n => [n.id, n]));

    const newNodes = nodes.map(n => {
      const old = oldNodesMap.get(n.id);
      if (!old) {
        isTopologyChanged = true;
        return { ...n }; // Purely new node
      }
      return { ...old, ...n, x: old.x, y: old.y, vx: old.vx, vy: old.vy, fx: old.fx, fy: old.fy };
    });

    const newEdges = edges.map(e => {
      const sourceId = e.source?.id || e.source;
      const targetId = e.target?.id || e.target;
      const oldLink = graphDataRef.current.links.find(l => 
        (l.source.id || l.source) === sourceId && 
        (l.target.id || l.target) === targetId
      );
      
      if (oldLink) {
        return { ...oldLink, ...e, source: oldLink.source, target: oldLink.target };
      }
      
      isTopologyChanged = true;
      return { ...e, source: sourceId, target: targetId };
    });

    graphDataRef.current = { nodes: newNodes, links: newEdges };
    const nodesMap = new Map(newNodes.map(n => [n.id, n]));

    // 3. Render Links
    const link = linkGroup.selectAll('.edge')
      .data(newEdges, d => d.id || `${d.source.id || d.source}-${d.target.id || d.target}`);

    link.exit().remove();

    const linkEnter = link.enter()
      .append('line')
      .attr('class', 'edge')
      .style('stroke-opacity', 0.4)
      .style('stroke-width', 2);

    const mergedLinks = linkEnter.merge(link);

    // Apply color logic to edges using native CSS transitions
    mergedLinks
      .style('transition', 'stroke 0.5s ease')
      .style('stroke', d => {
        const sourceId = d.source.id || d.source;
        const targetId = d.target.id || d.target;
        const srcNode = nodesMap.get(sourceId) || {};
        const tgtNode = nodesMap.get(targetId) || {};
        const maxRisk = Math.max(srcNode.risk || 0, tgtNode.risk || 0);
        
        if (maxRisk > 0.7) return '#E24B4A'; // High Risk
        if (maxRisk >= 0.3) return '#EF9F27'; // Med Risk
        return '#1D9E75'; // Safe
      });

    // 4. Render Nodes
    const node = nodeGroup.selectAll('.node-group')
      .data(newNodes, d => d.id);

    node.exit().remove();

    const nodeEnter = node.enter()
      .append('g')
      .attr('class', 'node-group')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          // By leaving d.fx and d.fy set, the node remains pinned
        })
      )
      .on('dblclick', (event, d) => {
        // Double click unpins the node
        d.fx = null;
        d.fy = null;
        simulation.alpha(0.1).restart();
      })
      .on('click', (event, d) => {
        if (onNodeClick) onNodeClick(d);
      })
      .on('mouseenter', function (event, d) {
        if (d.risk <= 0.7) {
          d3.select(this).select('.node-label').style('opacity', 1);
        }
      })
      .on('mouseleave', function (event, d) {
        if (d.risk <= 0.7) {
          d3.select(this).select('.node-label').style('opacity', 0);
        }
      });

    // Selection ring (Blue)
    nodeEnter.append('circle')
      .attr('class', 'node-ring')
      .style('fill', 'none')
      .style('stroke', '#388ADD')
      .style('stroke-width', 2)
      .style('transition', 'r 0.5s ease, opacity 0.3s ease');

    // Main Node Circle
    nodeEnter.append('circle')
      .attr('class', 'node-circle')
      .style('transition', 'fill 0.5s ease, r 0.5s ease, filter 0.5s ease');

    // Node Label
    nodeEnter.append('text')
      .attr('class', 'node-label')
      .attr('dy', 22)
      .attr('text-anchor', 'middle')
      .style('fill', '#E6EDF3')
      .style('font-family', 'Inter')
      .style('font-size', '11px')
      .style('pointer-events', 'none')
      .style('transition', 'opacity 0.3s ease');

    const mergedNodes = nodeEnter.merge(node);

    // Apply data-driven dynamic styles
    mergedNodes.select('.node-circle')
      .attr('r', d => d.risk > 0.7 ? 10 : d.risk >= 0.3 ? 8 : 7)
      .style('fill', d => d.risk > 0.7 ? '#FF3B30' : d.risk >= 0.3 ? '#EF9F27' : '#1D9E75')
      .style('filter', d => d.risk > 0.7 ? 'url(#glow)' : 'none');

    mergedNodes.select('.node-ring')
      .attr('r', d => (d.risk > 0.7 ? 10 : d.risk >= 0.3 ? 8 : 7) + 4)
      .style('opacity', d => d.id === selectedNodeId ? 1 : 0);

    mergedNodes.select('.node-label')
      .text(d => d.label || d.id)
      .style('opacity', d => d.risk > 0.7 ? 1 : 0);

    // 5. Restart Simulation safely
    simulation.nodes(newNodes);
    simulation.force('link').links(newEdges);

    if (isTopologyChanged) {
      simulation.alpha(0.3).restart();
    }

    // Tick handler for physical layout updates
    simulation.on('tick', () => {
      mergedLinks
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      mergedNodes
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

  }, [nodes, edges, selectedNodeId, onNodeClick]);

  // Cleanup resize listener on unmount
  useEffect(() => {
    return () => {
      if (containerRef.current && containerRef.current._handleResize) {
        window.removeEventListener('resize', containerRef.current._handleResize);
      }
    };
  }, []);

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full cursor-grab active:cursor-grabbing"
    />
  );
}
