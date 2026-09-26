import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface MarketStateOrb3DProps {
  regime: string;
  confidence: number;
}

export const MarketStateOrb3D: React.FC<MarketStateOrb3DProps> = ({ regime, confidence }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 220;
    const height = container.clientHeight || 220;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0, 8);

    let renderer: THREE.WebGLRenderer | null = null;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);
    } catch {
      return;
    }

    // Colors according to regime
    let primaryColor = 0xd4af37; // Gold for RANGE
    if (regime === 'TREND') primaryColor = 0x10b981; // Emerald
    if (regime === 'BREAKOUT') primaryColor = 0x38bdf8; // Sky
    if (regime === 'HIGH_VOLATILITY') primaryColor = 0xf43f5e; // Rose
    if (regime === 'TRANSITION') primaryColor = 0xa855f7; // Purple

    // Concentric orbital rings
    const group = new THREE.Group();

    // Outer Torus
    const torusGeo1 = new THREE.TorusGeometry(2.2, 0.04, 16, 64);
    const torusMat1 = new THREE.MeshBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: 0.8,
      wireframe: true,
    });
    const ring1 = new THREE.Mesh(torusGeo1, torusMat1);
    group.add(ring1);

    // Inner Angled Torus
    const torusGeo2 = new THREE.TorusGeometry(1.6, 0.03, 16, 64);
    const torusMat2 = new THREE.MeshBasicMaterial({
      color: 0x94a3b8,
      transparent: true,
      opacity: 0.5,
    });
    const ring2 = new THREE.Mesh(torusGeo2, torusMat2);
    ring2.rotation.x = Math.PI / 3;
    group.add(ring2);

    // Core Icosahedron
    const coreGeo = new THREE.IcosahedronGeometry(0.8, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: primaryColor,
      wireframe: true,
      transparent: true,
      opacity: 0.6 + confidence * 0.3,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    group.add(core);

    scene.add(group);

    let animId: number;
    const animate = () => {
      if (document.hidden) {
        animId = requestAnimationFrame(animate);
        return;
      }

      // Speeds based on volatility or regime
      const speedMultiplier = regime === 'HIGH_VOLATILITY' ? 2.5 : regime === 'BREAKOUT' ? 1.8 : 0.9;

      ring1.rotation.x += 0.008 * speedMultiplier;
      ring1.rotation.y += 0.012 * speedMultiplier;

      ring2.rotation.y -= 0.015 * speedMultiplier;
      ring2.rotation.z += 0.009 * speedMultiplier;

      core.rotation.y += 0.005 * speedMultiplier;
      core.rotation.x += 0.005 * speedMultiplier;

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
      window.removeEventListener('resize', handleResize);
      torusGeo1.dispose();
      torusMat1.dispose();
      torusGeo2.dispose();
      torusMat2.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      if (renderer) {
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [regime, confidence]);

  return (
    <div
      ref={containerRef}
      className="w-full h-44 relative flex items-center justify-center overflow-hidden"
    />
  );
};
