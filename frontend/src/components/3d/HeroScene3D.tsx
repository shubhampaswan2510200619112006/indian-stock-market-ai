import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface HeroScene3DProps {
  isLowPerf?: boolean;
}

export const HeroScene3D: React.FC<HeroScene3DProps> = ({ isLowPerf = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLowPerf || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x05070a, 0.035);

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(0, 12, 28);
    camera.lookAt(0, 0, 0);

    let renderer: THREE.WebGLRenderer | null = null;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn('WebGL not supported or failed to initialize:', e);
      return;
    }

    // Grid Floor
    const gridHelper = new THREE.GridHelper(60, 40, 0xd4af37, 0x1e293b);
    gridHelper.position.y = -2;
    if (Array.isArray(gridHelper.material)) {
      gridHelper.material.forEach((m) => {
        m.transparent = true;
        m.opacity = 0.25;
      });
    } else {
      gridHelper.material.transparent = true;
      gridHelper.material.opacity = 0.25;
    }
    scene.add(gridHelper);

    // Dynamic Financial Trajectory Ribbon
    const curvePoints: THREE.Vector3[] = [];
    const numPoints = 25;
    for (let i = 0; i < numPoints; i++) {
      const x = (i - numPoints / 2) * 1.8;
      // Synthesize realistic subtle wave trajectory
      const y = Math.sin(i * 0.4) * 2.5 + Math.cos(i * 0.2) * 1.2 + 2;
      const z = Math.sin(i * 0.3) * 6;
      curvePoints.push(new THREE.Vector3(x, y, z));
    }
    const curve = new THREE.CatmullRomCurve3(curvePoints);
    const tubeGeometry = new THREE.TubeGeometry(curve, 70, 0.18, 8, false);
    const tubeMaterial = new THREE.MeshBasicMaterial({
      color: 0xd4af37,
      transparent: true,
      opacity: 0.85,
    });
    const trajectoryMesh = new THREE.Mesh(tubeGeometry, tubeMaterial);
    scene.add(trajectoryMesh);

    // Glowing Data Nodes along the trajectory
    const nodesGroup = new THREE.Group();
    const nodeGeometry = new THREE.SphereGeometry(0.28, 12, 12);
    const nodeMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.9,
    });
    for (let i = 0; i < numPoints; i += 3) {
      const pt = curvePoints[i];
      const nodeMesh = new THREE.Mesh(nodeGeometry, nodeMaterial);
      nodeMesh.position.copy(pt);
      nodesGroup.add(nodeMesh);
    }
    scene.add(nodesGroup);

    // Ambient floating particles
    const particleCount = 200;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 50;
      positions[i + 1] = Math.random() * 20 - 2;
      positions[i + 2] = (Math.random() - 0.5) * 50;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x64748b,
      size: 0.18,
      transparent: true,
      opacity: 0.6,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // Subtle volumetric lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xd4af37, 2, 50);
    pointLight.position.set(0, 10, 10);
    scene.add(pointLight);

    // Mouse movement parallax
    let mouseX = 0;
    let mouseY = 0;
    const handleMouseMove = (event: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((event.clientX - rect.left) / width - 0.5) * 2;
      mouseY = ((event.clientY - rect.top) / height - 0.5) * 2;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Resize handler
    const handleResize = () => {
      if (!container || !renderer) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop with tab visibility check
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      if (document.hidden) {
        animationFrameId = requestAnimationFrame(animate);
        return;
      }

      const elapsedTime = clock.getElapsedTime();

      // Gentle camera sway
      camera.position.x += (mouseX * 4 - camera.position.x) * 0.03;
      camera.position.y += (-mouseY * 2 + 12 - camera.position.y) * 0.03;
      camera.lookAt(0, 0, 0);

      // Trajectory subtle breathing
      trajectoryMesh.rotation.y = Math.sin(elapsedTime * 0.15) * 0.05;
      nodesGroup.rotation.y = Math.sin(elapsedTime * 0.15) * 0.05;

      // Slowly rotate particles
      particles.rotation.y = elapsedTime * 0.02;

      renderer?.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    // Cleanup resources
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);

      tubeGeometry.dispose();
      tubeMaterial.dispose();
      nodeGeometry.dispose();
      nodeMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
      gridHelper.dispose();

      if (renderer) {
        renderer.dispose();
        if (container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [isLowPerf]);

  if (isLowPerf) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-[#0b0f19] to-[#05070a] border border-white/[0.05] rounded-xl overflow-hidden relative">
        <div className="absolute inset-0 grid-bg opacity-30" />
        <div className="text-center z-10 p-6">
          <div className="font-mono text-xs text-amber-400/80 uppercase tracking-widest mb-1">
            2D PERFORMANCE MODE ACTIVE
          </div>
          <div className="text-slate-400 text-sm">
            High-efficiency low-power layout engaged for maximum battery and responsiveness.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[360px] relative overflow-hidden rounded-xl bg-gradient-to-b from-[#070b14] via-[#05070a] to-[#05070a]"
    >
      {/* Decorative gradient overlay */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#05070a] via-transparent to-transparent opacity-80" />
      <div className="absolute top-4 left-4 z-10 font-mono text-[11px] text-slate-500 tracking-wider flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span>3D CINEMATIC FINANCIAL LANDSCAPE • 60 FPS</span>
      </div>
    </div>
  );
};
