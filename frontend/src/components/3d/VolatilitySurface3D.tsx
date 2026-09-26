import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { WebGLFallback2D } from './WebGLFallback2D';
import { RotateCcw, Layers, Eye, ShieldAlert } from 'lucide-react';

interface VolatilitySurface3DProps {
  isLowPerf?: boolean;
}

export const VolatilitySurface3D: React.FC<VolatilitySurface3DProps> = ({ isLowPerf = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [wireframe, setWireframe] = useState<boolean>(false);
  const [optionType, setOptionType] = useState<'CALL' | 'PUT'>('CALL');
  const [hoveredPoint, setHoveredPoint] = useState<{
    strike: number;
    expiry: string;
    iv: number;
  } | null>(null);

  if (isLowPerf) {
    return <WebGLFallback2D title="3D VOLATILITY SURFACE — 2D FALLBACK" />;
  }

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 450;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    scene.fog = new THREE.FogExp2(0x060911, 0.02);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(16, 14, 22);
    camera.lookAt(0, 2, 0);

    let renderer: THREE.WebGLRenderer | null = null;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);
    } catch {
      return;
    }

    // Grid Floor
    const grid = new THREE.GridHelper(30, 20, 0xd4af37, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);

    // Surface Geometry
    // X = Strike (-10 to 10), Z = Expiry (-8 to 8), Y = IV height
    const xSegments = 24;
    const zSegments = 16;
    const geometry = new THREE.PlaneGeometry(24, 16, xSegments, zSegments);
    geometry.rotateX(-Math.PI / 2);

    const pos = geometry.attributes.position;
    // Calculate heights representing real implied volatility smile
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);

      // Strike moneyness factor: smile curvature
      const moneyness = x / 8.0;
      const skew = optionType === 'CALL' ? -0.15 * moneyness : 0.25 * moneyness;
      const curvature = (moneyness * moneyness) * 1.8;
      // Term structure: slight upward tilt with expiry
      const termSlope = (z + 8) * 0.12;

      // Base height
      const y = 1.8 + curvature + skew + termSlope;
      pos.setY(i, y);
    }
    geometry.computeVertexNormals();

    // Material with subtle gold-to-cyan gradient look
    const material = new THREE.MeshStandardMaterial({
      color: 0xd4af37,
      roughness: 0.35,
      metalness: 0.6,
      wireframe: wireframe,
      side: THREE.DoubleSide,
    });

    const surfaceMesh = new THREE.Mesh(geometry, material);
    scene.add(surfaceMesh);

    // Coordinate Axes representation
    const axisGroup = new THREE.Group();
    // Strike axis line
    const strikeLineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-12, 0, 8),
      new THREE.Vector3(12, 0, 8),
    ]);
    const axisMat = new THREE.LineBasicMaterial({ color: 0x94a3b8 });
    axisGroup.add(new THREE.Line(strikeLineGeo, axisMat));
    scene.add(axisGroup);

    // Lighting
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x0f172a, 0.6);
    scene.add(hemiLight);

    const dirLight = new THREE.DirectionalLight(0xd4af37, 1.2);
    dirLight.position.set(10, 20, 15);
    scene.add(dirLight);

    const blueLight = new THREE.PointLight(0x38bdf8, 1.5, 40);
    blueLight.position.set(-10, 8, -5);
    scene.add(blueLight);

    // Mouse drag rotation controls
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotationY = 0;
    let targetRotationX = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        targetRotationY += deltaX * 0.008;
        targetRotationX += deltaY * 0.008;
        targetRotationX = Math.max(-0.6, Math.min(0.6, targetRotationX));
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // Animation Loop
    let animId: number;
    const animate = () => {
      if (document.hidden) {
        animId = requestAnimationFrame(animate);
        return;
      }

      // Smooth camera interpolation
      surfaceMesh.rotation.y += (targetRotationY - surfaceMesh.rotation.y) * 0.1;
      surfaceMesh.rotation.x += (targetRotationX - surfaceMesh.rotation.x) * 0.1;
      grid.rotation.y = surfaceMesh.rotation.y;

      renderer?.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      if (!container || !renderer) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('resize', handleResize);

      geometry.dispose();
      material.dispose();
      strikeLineGeo.dispose();
      axisMat.dispose();
      grid.dispose();

      if (renderer) {
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [isLowPerf, wireframe, optionType]);

  return (
    <div className="w-full bg-[#070b16] border border-white/[0.08] rounded-xl overflow-hidden relative">
      {/* Surface Header & Controls */}
      <div className="flex flex-wrap items-center justify-between p-4 border-b border-white/[0.06] bg-[#090e1c]/80 backdrop-blur-sm z-10">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
              3D Implied Volatility Surface
            </h3>
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            X = Strike Price • Y = Implied Volatility (IV%) • Z = Expiry Term
          </p>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <div className="flex items-center bg-slate-900/80 p-0.5 rounded border border-slate-800">
            <button
              onClick={() => setOptionType('CALL')}
              className={`px-3 py-1 rounded text-xs transition-all ${
                optionType === 'CALL'
                  ? 'bg-amber-400/20 text-amber-300 font-semibold border border-amber-400/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              CALL IV
            </button>
            <button
              onClick={() => setOptionType('PUT')}
              className={`px-3 py-1 rounded text-xs transition-all ${
                optionType === 'PUT'
                  ? 'bg-amber-400/20 text-amber-300 font-semibold border border-amber-400/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              PUT IV
            </button>
          </div>

          <button
            onClick={() => setWireframe(!wireframe)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded border text-xs transition-all ${
              wireframe
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{wireframe ? 'WIREFRAME' : 'SURFACE'}</span>
          </button>
        </div>
      </div>

      {/* 3D Canvas Container */}
      <div
        ref={containerRef}
        className="w-full h-[460px] relative cursor-grab active:cursor-grabbing"
      />

      {/* Mandatory Quantitative Truth Callout */}
      <div className="p-3 bg-[#05070c] border-t border-white/[0.06] flex flex-wrap items-center justify-between text-[11px] font-mono gap-2">
        <div className="flex items-center gap-2 text-rose-300">
          <ShieldAlert className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
          <span>
            DATA FIDELITY AUDIT: 0.68% PAIRED BID/ASK COVERAGE • CONTINUOUS EXECUTABLE SURFACE: 0.0%
          </span>
        </div>
        <div className="text-slate-500">
          VALUATION MARKS ONLY • EXECUTION BACKTESTING BLOCKED
        </div>
      </div>
    </div>
  );
};
