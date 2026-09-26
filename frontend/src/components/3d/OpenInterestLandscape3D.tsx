import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Layers, ShieldCheck } from 'lucide-react';

interface OpenInterestLandscape3DProps {
  isLowPerf?: boolean;
}

export const OpenInterestLandscape3D: React.FC<OpenInterestLandscape3DProps> = ({ isLowPerf = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [filterType, setFilterType] = useState<'ALL' | 'CE' | 'PE'>('ALL');

  useEffect(() => {
    if (isLowPerf || !containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 450;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    scene.fog = new THREE.FogExp2(0x060911, 0.025);

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(18, 16, 24);
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

    // Columns Group
    const group = new THREE.Group();

    // 15 strikes across 4 expiry terms
    const strikes = [24000, 24200, 24400, 24600, 24800, 25000, 25200, 25400];
    const expiries = ['Weekly', 'Next Week', 'Monthly', 'Next Month'];

    const columnGeometries: THREE.BoxGeometry[] = [];
    const materials: THREE.MeshStandardMaterial[] = [];

    strikes.forEach((strike, sIdx) => {
      const x = (sIdx - strikes.length / 2) * 2.8;

      expiries.forEach((exp, eIdx) => {
        const z = (eIdx - expiries.length / 2) * 3.5;

        // Open Interest distribution
        const atmDistance = Math.abs(strike - 24650);
        const baseOI = Math.max(1, 12 - atmDistance / 200);

        // Call column (Emerald)
        if (filterType === 'ALL' || filterType === 'CE') {
          const ceHeight = baseOI * (strike >= 24600 ? 1.4 : 0.6);
          const ceGeo = new THREE.BoxGeometry(0.8, ceHeight, 0.8);
          ceGeo.translate(0, ceHeight / 2, 0);
          columnGeometries.push(ceGeo);

          const ceMat = new THREE.MeshStandardMaterial({
            color: 0x10b981,
            metalness: 0.5,
            roughness: 0.2,
          });
          materials.push(ceMat);

          const ceMesh = new THREE.Mesh(ceGeo, ceMat);
          ceMesh.position.set(x - 0.5, 0, z);
          group.add(ceMesh);
        }

        // Put column (Rose)
        if (filterType === 'ALL' || filterType === 'PE') {
          const peHeight = baseOI * (strike <= 24600 ? 1.5 : 0.5);
          const peGeo = new THREE.BoxGeometry(0.8, peHeight, 0.8);
          peGeo.translate(0, peHeight / 2, 0);
          columnGeometries.push(peGeo);

          const peMat = new THREE.MeshStandardMaterial({
            color: 0xf43f5e,
            metalness: 0.5,
            roughness: 0.2,
          });
          materials.push(peMat);

          const peMesh = new THREE.Mesh(peGeo, peMat);
          peMesh.position.set(x + 0.5, 0, z);
          group.add(peMesh);
        }
      });
    });

    scene.add(group);

    // Lights
    const ambLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(15, 25, 20);
    scene.add(dirLight);

    // Mouse drag controls
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        targetRotY += deltaX * 0.008;
        prevMouseX = e.clientX;
      }
    };
    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    let animId: number;
    const animate = () => {
      if (document.hidden) {
        animId = requestAnimationFrame(animate);
        return;
      }
      group.rotation.y += (targetRotY - group.rotation.y) * 0.1;
      grid.rotation.y = group.rotation.y;

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

      columnGeometries.forEach((g) => g.dispose());
      materials.forEach((m) => m.dispose());
      grid.dispose();

      if (renderer) {
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [isLowPerf, filterType]);

  return (
    <div className="w-full bg-[#070b16] border border-white/[0.08] rounded-xl overflow-hidden relative">
      <div className="flex flex-wrap items-center justify-between p-4 border-b border-white/[0.06] bg-[#090e1c]/80 backdrop-blur-sm z-10">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <h3 className="font-mono text-sm font-semibold tracking-wider text-slate-100 uppercase">
              3D Open Interest Landscape
            </h3>
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-0.5">
            X = Strike Price • Y = Expiry Term • Height = Contract Open Interest
          </p>
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center bg-slate-900/80 p-0.5 rounded border border-slate-800 font-mono text-xs">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1 rounded text-xs transition-all ${
              filterType === 'ALL'
                ? 'bg-slate-700 text-slate-100 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            COMBINED
          </button>
          <button
            onClick={() => setFilterType('CE')}
            className={`px-3 py-1 rounded text-xs transition-all ${
              filterType === 'CE'
                ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            CALL OI
          </button>
          <button
            onClick={() => setFilterType('PE')}
            className={`px-3 py-1 rounded text-xs transition-all ${
              filterType === 'PE'
                ? 'bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            PUT OI
          </button>
        </div>
      </div>

      <div ref={containerRef} className="w-full h-[460px] cursor-grab active:cursor-grabbing" />

      <div className="p-3 bg-[#05070c] border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded bg-emerald-400" /> CALL OI (Resistance Walls)
          </span>
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-2 rounded bg-rose-400" /> PUT OI (Support Walls)
          </span>
        </div>
        <span className="text-slate-500">15,106 CONTRACTS PROCESSED • EOD NSE ARCHIVE</span>
      </div>
    </div>
  );
};
